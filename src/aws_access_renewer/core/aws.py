import asyncio
from asyncio.subprocess import PIPE
from json import loads
from typing import Optional, List

class AWSAuthError(RuntimeError):
    """Raised when AWS authentication fails."""
    pass

class AWSConfigError(RuntimeError):
    """Raised when AWS configuration is missing (e.g. region)."""
    pass

async def run_cmd(cmd: str, profile: Optional[str] = None, region: Optional[str] = None) -> str:
    full_cmd = "aws "
    if profile: full_cmd += f"--profile {profile} "
    if region: full_cmd += f"--region {region} "
    full_cmd += cmd[4:] if cmd.startswith("aws ") else cmd
    
    process = await asyncio.create_subprocess_shell(full_cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        err = stderr.decode().strip()
        if "InvalidPermission.Duplicate" in err: 
            return "ALREADY_EXISTS"
        
        if any(token in err for token in ["AuthFailure", "InvalidClientTokenId", "SignatureDoesNotMatch", "ExpiredToken"]):
            raise AWSAuthError(err)
        
        if "You must specify a region" in err:
            raise AWSConfigError(err)
            
        raise RuntimeError(err)
    return stdout.decode()

class EC2Service:
    def __init__(self, profile: Optional[str] = None, region: Optional[str] = None):
        self.profile, self.region = profile, region

    async def list_regions(self) -> List[str]:
        raw = await run_cmd("ec2 describe-regions --output json", self.profile)
        return [r["RegionName"] for r in loads(raw)["Regions"]]

    async def list_instances(self) -> list[dict]:
        all_inst, token = [], None
        while True:
            cmd = f"ec2 describe-instances --output json" + (f" --next-token {token}" if token else "")
            data = loads(await run_cmd(cmd, self.profile, self.region))
            all_inst.extend([i for r in data.get("Reservations", []) for i in r.get("Instances", [])])
            token = data.get("NextToken")
            if not token: break
        return all_inst

    @staticmethod
    def instance_name(instance: dict) -> str:
        return next((tag["Value"] for tag in instance.get("Tags", []) if tag["Key"] == "Name"), "N/A")

class SecurityGroupService:
    def __init__(self, profile: Optional[str] = None, region: Optional[str] = None):
        self.profile, self.region = profile, region

    async def list_rules(self) -> list[dict]:
        all_rules, token = [], None
        while True:
            cmd = f"ec2 describe-security-group-rules --output json" + (f" --next-token {token}" if token else "")
            data = loads(await run_cmd(cmd, self.profile, self.region))
            all_rules.extend(data.get("SecurityGroupRules", []))
            token = data.get("NextToken")
            if not token: break
        return all_rules
