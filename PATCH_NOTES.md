# Patch Notes

## [1.1.0] - 2026-03-09

### Added
- **AWS API Pagination**: Implemented `NextToken` handling in `EC2Service.list_instances` and `SecurityGroupService.list_rules`. This ensures all resources are retrieved in large AWS environments.
- **Structured Exception Handling**: Refined the main execution loop to catch specific errors (`aiohttp.ClientError`, `json.JSONDecodeError`, `ValueError`) with clear messaging, while maintaining a broad fallback for unexpected critical failures.
- **Unit Testing Suite**: Added `tests/test_logic.py` to verify core IP normalization and instance tagging logic using the `unittest` framework.
- **Graceful Termination**: Added explicit handling for `EOFError` during interactive input and improved `KeyboardInterrupt` cleanup.

### Changed
- **Project Renaming**: Unified the project name to `aws-access-renewer` across `pyproject.toml`, `README.md`, and the CLI's internal version string.
- **Version Bump**: Updated version from `1.0.2` (legacy internal) / `0.1.0` (legacy meta) to `1.1.0`.
- **IP Normalization**: Enhanced safety in `normalize_ip` to better handle malformed input strings.
- **Documentation**: Completely overhauled `README.md` and created `GEMINI.md` for AI-assisted development context.

