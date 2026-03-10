import argparse
from .core.constants import VERSION, DEFAULT_SSH_PORT, DEFAULT_MANAGED_DESCRIPTION

def parse_args():
    parser = argparse.ArgumentParser(
        prog="aws-access-renewer",
        description="Automatically update AWS EC2 security group SSH rules to allow access from your current IP address.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python main.py --regions all --profile my-aws-profile"
    )
    parser.add_argument("-i", "--instance-id", help="EC2 instance ID")
    parser.add_argument("-n", "--instance-name", help="EC2 instance Name tag")
    parser.add_argument("-p", "--ssh-port", help=f"Target ports, comma-separated (default: {DEFAULT_SSH_PORT})")
    parser.add_argument("--source-ip", help="Override public IP detection")
    parser.add_argument("--regions", help="Comma-separated regions or 'all'")
    parser.add_argument("--profile", help="AWS CLI profile")
    parser.add_argument("-d", "--dry-run", action="store_true", help="Preview changes without applying them")
    parser.add_argument("--cleanup", action="store_true", help="Remove redundant rules instead of updating them")
    parser.add_argument("-b", "--batch", action="store_true", help="No interactive prompts")
    parser.add_argument("--rule-description", help="Description for updated rules", default=DEFAULT_MANAGED_DESCRIPTION)
    parser.add_argument("--version", action="version", version=f"AWS-ACCESS-RENEWER {VERSION}")
    return parser.parse_args()
