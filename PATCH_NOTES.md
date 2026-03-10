# Patch Notes

## [1.7.0] - 2026-03-10

### Added
- **Modern Orchestrator UI**: Completely redesigned the CLI experience with a high-fidelity, scrolling flow.
- **Hierarchical Discovery**: Added a dynamic tree view for AWS resources grouped by region.
- **Interactive Multiselection**: Implemented a custom keyboard-driven multiselector for both EC2 instances and ports.
- **Port Discovery**: Added automatic detection of open ingress ports from security groups during the interactive flow.
- **Modular Architecture**: Refactored the core logic into a professional package structure (`src/aws_access_renewer/`).
- **Global Installation Support**: Added `[project.scripts]` entry point and package restructuring for system-wide use via `uv tool install`.
- **Git Integration**: Added a comprehensive `.gitignore` file to protect the repository from temporary files and virtual environments.

### Changed
- **Entry Point**: Moved `main.py` to `src/aws_access_renewer/__main__.py` to support standard Python packaging.
- **Execution Flow**: Optimized the main loop for smoother transitions between discovery, selection, and execution phases.
- **Theming**: Standardized the "Terminal Classic" (Gold/Amber) aesthetic across all UI components.

### Fixed
- **Module Resolution**: Resolved `ModuleNotFoundError` during global installation by correctly structuring the source code.
- **Event Loop Conflict**: Fixed `asyncio.run()` errors when running the tool in environments with existing loops.
- **Duplicate Permission Handling**: Improved logic to gracefully skip or handle existing AWS security group rules.
