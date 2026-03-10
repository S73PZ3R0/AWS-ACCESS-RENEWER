# Patch Notes

## [1.8.0] - 2026-03-10

### Added
- **Surgical Login Interface**: Implemented an automated fallback UI that triggers when AWS authentication fails or configuration is missing.
- **Secure Credential Input**: Added interactive prompts for AWS Access Key, Secret Key, and Default Region using `questionary` (password masking enabled).
- **Headless Batch Mode**: Implemented full UI suppression when the `--batch` flag is used.
- **JSON Output**: The tool now returns a structured JSON object in batch mode, providing the source IP, operation summary, and detailed per-instance results.
- **Enhanced Interactive Selection**: Standardized keyboard-driven multiselect styling for a more consistent feel.

### Changed
- **Entry Point Refactoring**: Restored a minimalist `main.py` at the project root to ensure standard `uv run` and `python main.py` execution paths are preserved alongside modular packaging.
- **Modular Refinement**: Integrated custom exception classes (`AWSAuthError`, `AWSConfigError`) for precise control flow between the core and UI layers.

### Fixed
- **Authentication Resilience**: The tool now automatically retries operations after valid credentials are provided in the new login interface.
- **Import Resolution**: Fixed a `NameError` and `ModuleNotFoundError` related to `questionary` in modular environments.
- **UI Flickering**: Resolved an issue where UI elements were still rendering in batch mode when executed as a global tool.


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
