# ⚡ AWS-ACCESS-RENEWER ⚡

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.8.0-gold.svg)](PATCH_NOTES.md)

**A high-fidelity, asynchronous DevOps utility to automatically synchronize AWS EC2 security group rules with your current public IP address.**

Built for professional terminal environments, featuring a modern "Orchestrator" UI, automated authentication fallback, and headless JSON output for CI/CD automation.

---

## 🚀 Installation (System-Wide)

To use the `aws-access-renewer` command from **anywhere** on your system, install it using `uv tool`. This is the recommended method.

```bash
# 1. Install via uv (Automatic packaging and linking)
uv tool install git+https://github.com/S73PZ3R0/AWS-ACCESS-RENEWER.git

# OR from local source
uv tool install . --force
```

*The binary will be linked to your path (typically `~/.local/bin/aws-access-renewer`).*

---

## 🛠 Usage

Once installed, simply type the command from any directory:

### 1. Interactive Orchestrator (Default)
Launch the full UI to discover resources, select targets via keyboard, and monitor real-time synchronization.
```bash
aws-access-renewer
```

### 2. Automation (Headless Batch Mode)
Suppresses all UI elements and returns a structured **JSON** response. Ideal for cron jobs, scripts, and CI/CD pipelines.
```bash
aws-access-renewer --batch --cleanup
```

### 3. Advanced Commands
```bash
# Update specific region with Dry-Run (No changes made)
aws-access-renewer --regions us-east-1 --dry-run

# Target a specific instance and multiple ports
aws-access-renewer -n "prod-api" -p 22,80,443

# Use a specific AWS Profile
aws-access-renewer --profile staging
```

---

## 🔐 Key Features

- **Modern Orchestrator UI**: Scrolling high-signal CLI flow with hierarchical resource trees.
- **Surgical Login Interface**: Automated fallback UI that securely prompts for credentials only when AWS authentication fails.
- **Headless JSON Output**: Pure data output in batch mode for professional tool-chaining.
- **Smart Conflict Handling**: Proactively detects existing rules to avoid AWS `DuplicatePermission` errors.
- **Multi-Region Support**: Synchronize rules across the entire AWS global infrastructure in one pass.

---

## 🧪 Development

If you wish to contribute or modify the source:

```bash
# Clone and sync local virtual environment
git clone https://github.com/S73PZ3R0/AWS-ACCESS-RENEWER.git
cd AWS-ACCESS-RENEWER
uv sync

# Run tests
uv run python -m unittest tests/test_logic.py
```

## 📜 License
Licensed under the MIT License. See [LICENSE](LICENSE) for details.
