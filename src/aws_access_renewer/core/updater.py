from json import dumps
from typing import Dict, Any, Optional
from .aws import run_cmd
from .network import normalize_ip

class SSHRuleUpdater:
    MANAGED_DESCRIPTION = "Auto-updated by aws-access-renewer"
    
    def __init__(self, instance: dict, ports: list[int], source_ip: str, 
                 profile: Optional[str] = None, region: Optional[str] = None,
                 dry_run: bool = False, cleanup: bool = False):
        self.instance, self.ports = instance, ports
        self.source_cidr = normalize_ip(source_ip)
        self.sg_ids = {sg["GroupId"] for sg in instance["SecurityGroups"]}
        self.profile, self.region, self.dry_run, self.cleanup = profile, region, dry_run, cleanup

    def _is_matching_ssh_rule(self, rule: dict) -> bool:
        return (rule["GroupId"] in self.sg_ids and not rule["IsEgress"] and 
                rule["IpProtocol"] == "tcp" and rule["FromPort"] in self.ports)

    async def update(self, rules: list[dict]) -> Dict[str, Any]:
        ssh_rules = [r for r in rules if self._is_matching_ssh_rule(r)]
        results = {"updated": 0, "skipped": 0, "revoked": 0}
        if not ssh_rules: return results

        already_allowed = any((r.get("CidrIpv4") == self.source_cidr or r.get("CidrIpv6") == self.source_cidr) for r in ssh_rules)

        for rule in ssh_rules:
            current_cidr = rule.get("CidrIpv4") or rule.get("CidrIpv6")
            if current_cidr == self.source_cidr:
                results["skipped"] += 1
                continue
            
            if already_allowed:
                if self.cleanup:
                    if not self.dry_run:
                        await run_cmd(f"ec2 revoke-security-group-ingress --group-id {rule['GroupId']} --security-group-rule-ids {rule['SecurityGroupRuleId']}", self.profile, self.region)
                    results["revoked"] += 1
                else: results["skipped"] += 1
                continue

            if self.dry_run:
                results["updated"] += 1
                continue

            payload = [{"SecurityGroupRuleId": rule["SecurityGroupRuleId"], "SecurityGroupRule": {
                "IpProtocol": "tcp", "FromPort": rule["FromPort"], "ToPort": rule["ToPort"],
                "CidrIpv4": self.source_cidr, "Description": self.MANAGED_DESCRIPTION}}]
            
            res = await run_cmd(f"ec2 modify-security-group-rules --group-id {rule['GroupId']} --security-group-rules '{dumps(payload)}'", self.profile, self.region)
            if res == "ALREADY_EXISTS": results["skipped"] += 1
            else: results["updated"] += 1
        return results
