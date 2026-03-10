# AWS-ACCESS-RENEWER

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A high-performance asynchronous Python utility to automatically update AWS EC2 security group SSH ingress rules. It detects your current public IP address and synchronizes your AWS access rules to ensure uninterrupted connectivity.

## Features

- **Multi-Region Support**: Scan and update rules across multiple AWS regions simultaneously.
- **Dry-Run Mode**: Preview changes without applying them using the `--dry-run` flag.
- **AWS Profile Support**: Specify custom AWS CLI profiles with the `--profile` flag.
- **Stale Rule Cleanup**: Remove old SSH access rules from other IPs using the `--cleanup` flag.
- **Rule Descriptions**: Automatically adds descriptions to managed rules for easier identification.
- **Auto IP Detection**: Automatically fetches your current public IPv4/IPv6 address.
- **Asynchronous Execution**: Uses `asyncio` and `aiohttp` for non-blocking operations.
- **Target Filtering**: Update rules by Instance ID, Name tag, or across all instances.
- **Multi-Port Support**: Sync multiple ports simultaneously (e.g., SSH, HTTPs, custom apps).
- **Interactive Port Selection**: Discovers and targets active ingress rules automatically.
- **Batch Mode**: Non-interactive execution suitable for automated workflows or cron jobs.
- **Safety First**: Structured exception handling and clear error reporting.

## Prerequisites

- **Python**: 3.12 or higher.
- **AWS CLI**: Installed and configured with valid credentials (`aws configure`).
- **Permissions**: IAM user must have permissions to `ec2:DescribeInstances`, `ec2:DescribeSecurityGroupRules`, and `ec2:ModifySecurityGroupRules`.

## Installation

This project uses `uv` for lightning-fast dependency management.

```bash
# Clone the repository
git clone https://github.com/youruser/aws-access-renewer.git
cd aws-access-renewer

# Install dependencies
uv sync
```

## Usage

### Interactive Mode
Lists all instances and prompts for confirmation before making changes.
```bash
python main.py
```

### Targeted Updates
Update a specific instance by name or ID.
```bash
# By Name tag
python main.py -n "prod-web-server"

# By Instance ID
python main.py -i i-0123456789abcdef0
```

### Advanced Options
```bash
# Multiple ports (comma-separated)
python main.py -p 22,443,8080

# Provide a specific source IP/CIDR manually
python main.py --source-ip 1.2.3.4

# Batch mode (non-interactive, updates all matches)
python main.py -b
```

## Development

### Running Tests
The project uses the standard `unittest` framework for core logic validation.
```bash
python3 -m unittest tests/test_logic.py
```

### Project Structure
- `main.py`: Core application entry point and CLI logic.
- `tests/`: Unit tests for critical functions.
- `pyproject.toml`: Dependency and metadata configuration.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
