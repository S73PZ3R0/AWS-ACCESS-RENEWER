#!/usr/bin/env python3
import asyncio
import argparse
import sys
import ipaddress
from asyncio.subprocess import PIPE
from itertools import cycle
from json import loads, dumps
from shutil import get_terminal_size
from typing import Optional, Iterable
import aiohttp

# ---------------------------
# UI / Helpers
# ---------------------------

SPINNER = cycle(["/", "-", "\\", "|"])


async def run_cmd(cmd: str, label: str) -> str:
    process = await asyncio.create_subprocess_shell(cmd, stdout=PIPE, stderr=PIPE)

    while process.returncode is None:
        print(f"\r{label} {next(SPINNER)}", end="", flush=True)
        await asyncio.sleep(0.1)

    print(f"\r{' ' * get_terminal_size().columns}", end="", flush=True)

    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError(stderr.decode().strip())

    return stdout.decode()


def normalize_ip(value: str) -> str:
    if "/" in value:
        return value
    ip = ipaddress.ip_address(value)
    return f"{value}/32" if ip.version == 4 else f"{value}/128"


async def fetch_public_ip() -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.ipify.org?format=json") as resp:
            return (await resp.json())["ip"]


def confirm(prompt: str) -> bool:
    answer = input(f"{prompt} [y/N]: ").strip().lower()
    return answer in {"y", "yes"}


# ---------------------------
# EC2
# ---------------------------


class EC2Service:
    @staticmethod
    async def list_instances() -> list[dict]:
        raw = await run_cmd(
            "aws ec2 describe-instances --output json",
            "Loading EC2 instances",
        )
        data = loads(raw)
        return [
            instance
            for reservation in data.get("Reservations", [])
            for instance in reservation.get("Instances", [])
        ]

    @staticmethod
    def instance_name(instance: dict) -> str:
        for tag in instance.get("Tags", []):
            if tag.get("Key") == "Name":
                return tag.get("Value", "")
        return ""

    @classmethod
    def resolve_many(
        cls,
        instances: list[dict],
        *,
        instance_id: Optional[str],
        instance_name: Optional[str],
    ) -> list[dict]:
        if instance_id:
            matches = [i for i in instances if i["InstanceId"] == instance_id]
        elif instance_name:
            matches = [i for i in instances if cls.instance_name(i) == instance_name]
        else:
            # no filter → all instances
            matches = instances

        if not matches:
            raise RuntimeError("No instances matched")

        return matches


# ---------------------------
# Security Groups
# ---------------------------


class SecurityGroupService:
    @staticmethod
    async def list_rules() -> list[dict]:
        raw = await run_cmd(
            "aws ec2 describe-security-group-rules --output json",
            "Loading security group rules",
        )
        return loads(raw)["SecurityGroupRules"]


# ---------------------------
# SSH Rule Logic
# ---------------------------


class SSHRuleUpdater:
    def __init__(self, instance: dict, ssh_port: int, source_ip: str):
        self.instance = instance
        self.port = ssh_port
        self.source_cidr = normalize_ip(source_ip)
        self.sg_ids = {sg["GroupId"] for sg in instance["SecurityGroups"]}

    def _is_matching_ssh_rule(self, rule: dict) -> bool:
        return (
            rule["GroupId"] in self.sg_ids
            and not rule["IsEgress"]
            and rule["IpProtocol"] == "tcp"
            and rule["FromPort"] == self.port
            and rule["ToPort"] == self.port
        )

    async def update(self, rules: list[dict]):
        ssh_rules = [r for r in rules if self._is_matching_ssh_rule(r)]

        if not ssh_rules:
            print(f"  No SSH ingress rules found for port {self.port}.")
            return

        for rule in ssh_rules:
            if rule.get("CidrIpv4") == self.source_cidr:
                print(f"  Skipping {rule['SecurityGroupRuleId']} (already correct)")
                continue

            payload = {
                "SecurityGroupRuleId": rule["SecurityGroupRuleId"],
                "SecurityGroupRule": {
                    "IpProtocol": "tcp",
                    "FromPort": self.port,
                    "ToPort": self.port,
                    "CidrIpv4": self.source_cidr,
                },
            }

            cmd = (
                "aws ec2 modify-security-group-rules "
                f"--group-id {rule['GroupId']} "
                f"--security-group-rules '{dumps([payload])}'"
            )

            await run_cmd(cmd, f"  Updating {rule['SecurityGroupRuleId']}")
            print(f"  Updated → {self.source_cidr}")


# ---------------------------
# CLI
# ---------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update EC2 SSH security group source IP"
    )
    parser.add_argument("-i", "--instance-id")
    parser.add_argument("-n", "--instance-name")
    parser.add_argument("-p", "--ssh-port", type=int, default=22)
    parser.add_argument("--source-ip", help="IP or CIDR (auto-detected if omitted)")
    return parser.parse_args()


async def main():
    args = parse_args()

    instances = await EC2Service.list_instances()
    targets = EC2Service.resolve_many(
        instances,
        instance_id=args.instance_id,
        instance_name=args.instance_name,
    )

    if not args.instance_id and not args.instance_name:
        print(f"⚠️  No instance filter provided.")
        print(f"⚠️  This will update SSH rules on {len(targets)} instances.")
        if not confirm("Continue?"):
            print("Aborted.")
            return

    source_ip = args.source_ip or await fetch_public_ip()
    print(f"Using source IP: {source_ip}\n")

    rules = await SecurityGroupService.list_rules()

    for instance in targets:
        print(
            f"Instance: {instance['InstanceId']} "
            f"({EC2Service.instance_name(instance)})"
        )

        updater = SSHRuleUpdater(
            instance=instance,
            ssh_port=args.ssh_port,
            source_ip=source_ip,
        )
        await updater.update(rules)
        print()

    print("Done.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCancelled.")
