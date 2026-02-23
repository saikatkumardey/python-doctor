# AGENTS.md — Agent Guidelines for python-doctor

This file provides guidance for AI agents working on the python-doctor codebase.

## Project Overview

python-doctor is a CLI tool that scans Python codebases and returns a 0-100 health score. It uses multiple analyzers (ruff, bandit, vulture, etc.) to check code quality, security, complexity, and structure.

## Build, Lint, and Test Commands

### Installation
```bash
uv sync --extra dev  # Install with dev dependencies
```

### Linting
```bash
ruff check .              # Run ruff linter on entire project
ruff check path/to/file.py  # Lint specific file
```

### Type Checking
```bash
mypy .                   # Run mypy type checker
```

### Running Tests
```bash
pytest                   # Run all tests
pytest tests/            # Run tests in specific directory
pytest tests/test_scorer.py  # Run specific test file
pytest tests/test_scorer.py::test_compute_score_no_deductions  # Run single test
pytest -v                # Verbose output
pytest -k "test_name"    # Run tests matching pattern
```

### Running the CLI
```bash
python -m python_doctor.cli <path>   # Scan a directory
python-doctor <path>    # After pip install
python-doctor <path> --fix  # Auto-fix issues
python-doctor <path> --json  # JSON output
python-doctor <path> --verbose  # Show all findings
```

## Code Style Guidelines

### General Principles
- Python 3.10+ (use built-in types like `list[str]` not `List[str]`)
- Maximum line length: 120 characters
- No comments unless explaining complex logic
- Keep functions small and focused

### Imports
- Group in order: stdlib, third-party, local
- Use explicit relative imports for internal modules
- Example from cli.py:
```python
import argparse
import json
import os
import sys

from . import __version__
from .analyzers import (
    bandit_analyzer,
    complexity,
    # ...
)
from .rules import CATEGORIES
from .scorer import category_score, compute_score, score_label
```

### Type Hints
- Always use type hints for function arguments and return values
- Use `| None` instead of `Optional`
- Example:
```python
def run_analyzers(path: str, fix: bool = False) -> list[AnalyzerResult]:
    ...
```

### Naming Conventions
- `snake_case` for functions, variables, and modules
- `PascalCase` for classes and dataclasses
- `SCREAMING_SNAKE_CASE` for constants
- Prefix private functions with underscore: `_private_function()`

### Dataclasses
Use `@dataclass` for simple data containers:
```python
@dataclass
class Finding:
    category: str
    rule: str
    message: str
    file: str = ""
    line: int = 0
    severity: str = "medium"
    cost: float = 0.0
```

### Error Handling
- Use specific exception types first, then general
- Catch and handle gracefully — don't let exceptions crash the tool
- Store errors in `AnalyzerResult.error` field rather than raising
```python
try:
    proc = subprocess.run(...)
    items = json.loads(proc.stdout) if proc.stdout.strip() else []
except FileNotFoundError:
    result.error = "ruff not found (skipped)"
    return result
except Exception as e:
    result.error = str(e)
    return result
```

### String Formatting
- Use f-strings for all string formatting
```python
score_label = f"Score: {score}/100"
```

### File Structure
```
python_doctor/
├── __init__.py       # Version only
├── cli.py            # CLI entry point
├── scorer.py         # Score calculation logic
├── rules.py          # Constants and dataclasses
└── analyzers/
    ├── __init__.py
    ├── bandit_analyzer.py
    ├── complexity.py
    ├── dependency_analyzer.py
    ├── docstring_analyzer.py
    ├── exceptions_analyzer.py
    ├── imports_analyzer.py
    ├── ruff_analyzer.py
    ├── structure.py
    └── vulture_analyzer.py

tests/
├── test_scorer.py
├── test_rules.py
└── test_*_analyzer.py
```

### Running Quality Checks
Before submitting code, run:
```bash
ruff check .
mypy .
pytest
```

### Adding New Analyzers
1. Create new file in `python_doctor/analyzers/`
2. Implement `analyze(path: str, **kwargs) -> AnalyzerResult` function
3. Add to ANALYZERS list in `cli.py`
4. Add category in `rules.py` CATEGORIES dict
5. Add tests in `tests/`

### Analyzer Result Format
Each analyzer returns:
```python
result = AnalyzerResult(category="category_name")
result.findings.append(Finding(
    category="lint",
    rule="ruff/E501",
    message="Line too long",
    file="path/to/file.py",
    line=42,
    severity="warning",
    cost=0.5,
))
result.deduction = min(sum(f.cost for f in result.findings), max_ded)
return result
```

## Configuration Files

- `pyproject.toml` — Project metadata, dependencies, ruff/mypy config
- Tests use pytest (no pytest.ini needed)
