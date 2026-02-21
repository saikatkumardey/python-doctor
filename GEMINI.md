# GEMINI.md - Python Doctor 🐍

This document provides foundational context and mandates for Gemini CLI interaction within the `python-doctor` repository.

## Project Overview

**Python Doctor** is a CLI tool designed to scan Python codebases and return a 0-100 health score with structured, actionable output. It's specifically optimized for AI agents to enable an autonomous "scan-fix-verify" loop.

### Key Technologies
- **Python 3.10+**: Core implementation.
- **uv**: Primary package manager and runner.
- **Ruff**: Linting and formatting (supports auto-fix).
- **Bandit**: Security scanning.
- **Vulture**: Dead code detection.
- **Radon**: Cyclomatic complexity analysis.
- **Custom Analyzers**: AST-based checks for structure, dependencies, docstrings, imports, and exceptions.
- **Hatchling**: Build backend.
- **Pytest**: Testing framework.

### Architecture
The project follows a modular analyzer-based architecture:
- `python_doctor/cli.py`: Entry point and report formatting.
- `python_doctor/scorer.py`: Score aggregation logic (100 - total deductions).
- `python_doctor/rules.py`: Category definitions, weights, and max deductions.
- `python_doctor/analyzers/`: Individual modules for different health categories (e.g., `bandit_analyzer.py`, `complexity.py`).

## Building and Running

### Development Environment
The project uses `uv` for dependency management.
```bash
# Sync dependencies (including dev)
uv sync --extra dev

# Run the tool on the current directory
uv run python-doctor .

# Run the tool on a specific path with JSON output
uv run python-doctor /path/to/project --json
```

### Testing
Use `pytest` to run the test suite.
```bash
uv run pytest tests/ -v
```

### Versioning and Releases
Versioning is managed via `bumpver`.
```bash
# Example: Bump patch version (0.1.0 -> 0.1.1)
bumpver update --patch
```

## Development Conventions

### Coding Standards
- **Dogfooding**: Always run `python-doctor .` on your changes. A score below 50 is considered a failure; target 80+.
- **Analyzer Pattern**: Every analyzer must implement an `analyze(path: str, **kwargs) -> AnalyzerResult` function that returns `Finding` objects.
- **Category Weights**: New rules or analyzers must be registered in `python_doctor/rules.py` with appropriate cost/max deduction.
- **Type Safety**: Use type hints extensively (checked via `mypy`).

### Testing Practices
- Every analyzer should have a corresponding test file in `tests/`.
- Verify both the presence of findings and the correctness of the deduction calculation.

### Contribution Workflow
1. Create/Modify analyzers in `python_doctor/analyzers/`.
2. Register the analyzer in `python_doctor/cli.py` (`ANALYZERS` list).
3. Update `python_doctor/rules.py` with relevant categories and costs.
4. Add tests in `tests/`.
5. Run `uv run python-doctor .` to ensure the project maintains its health score.
