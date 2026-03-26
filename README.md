<p align="center">
  <h1 align="center">Python Doctor</h1>
  <p align="center">
    <strong>One command. One score. Built for AI agents.</strong>
  </p>
  <p align="center">
    <a href="https://github.com/saikatkumardey/python-doctor/actions/workflows/test.yml"><img src="https://github.com/saikatkumardey/python-doctor/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
    <a href="https://pypi.org/project/python-doctor/"><img src="https://img.shields.io/pypi/v/python-doctor" alt="PyPI"></a>
    <a href="https://pypi.org/project/python-doctor/"><img src="https://img.shields.io/pypi/pyversions/python-doctor" alt="Python"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  </p>
</p>

Python Doctor scans a Python codebase and returns a **0-100 health score** with structured, actionable output. It wraps security scanning, linting, complexity analysis, and more into a single command — so an AI agent can run it, read the results, fix the issues, and verify the fix in a loop without human intervention.

```
$ python-doctor .

🐍 Python Doctor v2026.3.21
Scanning: /home/user/myproject

📊 Score: 82/100 (Good)

🔒 Security (25/25) ✓
  ✓ All clear.

🧹 Lint (16/20)
  ✗ F841: unused variable 'x' (api/views.py:45)
  ✗ F401: unused import 'os' (utils/helpers.py:1)
  ⚠ W291: trailing whitespace (models/user.py:12)
  ... and 2 more

🔄 Complexity (15/15) ✓
  ✓ All clear.

🧘 Zen (12/15)
  ⚠ deep-nesting: 6 levels deep (core/engine.py:88)
  ⚠ long-function: 92 lines (core/engine.py:45)

🏗 Structure (8/10)
  ⚠ low-test-ratio: test:source ratio is 0.3 (< 0.5)

⚡ Exceptions (10/10) ✓
  ✓ All clear.

🔗 Imports (5/5) ✓
  ✓ All clear.
```

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Agent Integration](#agent-integration)
- [CLI Reference](#cli-reference)
- [What It Checks](#what-it-checks)
- [Scoring](#scoring)
- [Configuration](#configuration)
- [Profiles](#profiles)
- [Pre-commit Hook](#pre-commit-hook)
- [CI/CD](#cicd)
- [Benchmarks](#benchmarks)
- [Contributing](#contributing)
- [License](#license)

## Installation

```bash
# Recommended (isolated environment)
pipx install python-doctor

# Using uv
uv tool install python-doctor

# Using pip
pip install python-doctor

# Or install the binary (no Python required)
curl -sL https://raw.githubusercontent.com/saikatkumardey/python-doctor/main/install.sh | sh
```

Requires **Python 3.10+**. Dependencies (`ruff`, `bandit`, `radon`, `vulture`) are installed automatically.

<details>
<summary>Install from source</summary>

```bash
git clone https://github.com/saikatkumardey/python-doctor.git
cd python-doctor
uv sync
uv run python-doctor /path/to/project
```
</details>

## Quick Start

```bash
# Scan a project
python-doctor .

# See all findings with line numbers
python-doctor . --verbose

# Auto-fix what can be fixed (via ruff --fix)
python-doctor . --fix

# Just the score (for scripts and CI)
python-doctor . --score
# → 82

# Structured JSON output (for agents)
python-doctor . --json
```

### JSON Output

The `--json` flag returns machine-readable output that agents can parse directly:

```json
{
  "version": "2026.3.21",
  "path": "/home/user/myproject",
  "score": 82,
  "label": "Good",
  "categories": {
    "security": {
      "score": 25,
      "max": 25,
      "deduction": 0,
      "error": null,
      "findings": []
    },
    "lint": {
      "score": 16,
      "max": 20,
      "deduction": 4,
      "error": null,
      "findings": [
        {
          "rule": "F841",
          "message": "Local variable `x` is assigned to but never used",
          "file": "/home/user/myproject/api/views.py",
          "line": 45,
          "severity": "error"
        }
      ]
    }
  }
}
```

## Agent Integration

Python Doctor works with any agent that can run shell commands. Install the CLI, then add the appropriate rule for your agent.

### Claude Code

Install as a plugin for the `/python-doctor` slash command:

```bash
/plugin marketplace add saikatkumardey/python-doctor
/plugin install python-doctor@python-doctor-plugins
```

<details>
<summary>Manual setup (without plugin)</summary>

Add to your `CLAUDE.md`:

```markdown
## Python Health Check

Before finishing work on Python files, run:
  python-doctor . --json

Fix any findings with severity "error". Target score: 80+.
If score drops below 50, do not commit — fix the issues first.
```
</details>

### Cursor

Add to `.cursor/rules/python-doctor.mdc`:

```markdown
---
description: Python codebase health check
globs: "**/*.py"
alwaysApply: false
---

Run `python-doctor . --json` after modifying Python files.
Fix findings. Target score: 80+. Do not commit below 50.
```

### OpenAI Codex

Add to `AGENTS.md`:

```markdown
## Python Health Check

After modifying Python files, run `python-doctor . --json` to check codebase health.
Fix any findings. Target score: 80+. Exit code 1 means score < 50 — fix before committing.
```

### Windsurf / Cline / Aider

Add to your project rules or system prompt:

```
After modifying Python files, run: python-doctor . --json
Read the output. Fix findings with severity "error" first, then warnings.
Re-run to verify the score improved. Target: 80+.
```

### The Agent Loop

This is the intended workflow:

```
1. python-doctor . --json  → read the report
2. Fix findings (--fix for auto-fixable, manual for the rest)
3. python-doctor . --score → verify improvement
4. Repeat until score target met
```

We built Python Doctor, then ran it on itself. Score: 47. Fixed everything it flagged. Score: 92. The tool eats its own dogfood.

## CLI Reference

```
python-doctor [PATH] [OPTIONS]

Arguments:
  PATH                   Directory to scan (default: .)

Options:
  -v, --verbose          Show all findings with line numbers
  --score                Output only the numeric score
  --json                 Structured JSON output for agents
  --fix                  Auto-fix issues via ruff --fix, then report the rest
  --badge                Output a shields.io badge markdown snippet
  --ci                   Output a GitHub Actions workflow for badge auto-update
  --pre-commit           Install as a git pre-commit hook
  --min-score N          Minimum score threshold (exit 1 if below). Default: 50
  --profile TYPE         Override auto-detected profile (cli|web|library|script)
  --version              Show version and exit
  -h, --help             Show help and exit
```

### Exit Codes

| Code | Meaning |
|------|---------|
| `0`  | Score >= 50 |
| `1`  | Score < 50 (critical health) |

## What It Checks

7 categories, weighted by impact:

| Category | Weight | Max Deduction | What it catches |
|----------|--------|---------------|-----------------|
| **Security** | 5 | 25 | Bandit findings: SQL injection, hardcoded secrets, unsafe calls. Context-aware: skips test/example/docs files. |
| **Lint** | 4 | 20 | Ruff: unused imports, undefined names, style violations. Excludes docs/. |
| **Complexity** | 3 | 15 | Radon: cyclomatic complexity > 15. Excludes test files. |
| **Zen** | 3 | 15 | Deep nesting (>5 levels), long functions (>75 lines), too many params (>10), large classes (>15 methods) |
| **Structure** | 2 | 10 | Large files (>1000 lines), test ratio, type hints, README, LICENSE, linter config |
| **Exceptions** | 2 | 10 | Bare `except:`, silently swallowed exceptions |
| **Imports** | 1 | 5 | Star imports (`from x import *`), circular dependency detection |

## Scoring

Score = `max(0, 100 - total_deductions)`

- Weights are relative. Max deductions auto-scale so they always sum to exactly 100.
- Adding or removing a category automatically rebalances the weights.
- Deductions are capped per category (a single category can't tank the whole score).

| Score | Label | Meaning |
|-------|-------|---------|
| 90-100 | Excellent | Clean codebase, ready for production |
| 75-89 | Good | Minor issues, nothing blocking |
| 50-74 | Needs Work | Significant issues to address |
| 0-49 | Critical | Major problems, CI will fail (exit code 1) |

## Configuration

Configure via `[tool.python-doctor]` in your `pyproject.toml`:

```toml
[tool.python-doctor]
# Override the auto-detected project profile
profile = "web"

# Suppress specific rules globally
suppress = ["bandit/B101", "structure/no-py-typed"]

# Suppress rules for specific files (glob patterns)
[tool.python-doctor.per-file-suppress]
"tests/**" = ["bandit/B101"]
"scripts/*" = ["structure/large-file"]

# Override max deduction for a category
[tool.python-doctor.max-deduction]
security = 15
structure = 5
```

## Profiles

Python Doctor auto-detects your project type and adjusts rules accordingly:

| Profile | Detection | Adjustments |
|---------|-----------|-------------|
| **web** | `flask`, `django`, `fastapi`, etc. in dependencies | Default rules |
| **cli** | `click`, `typer`, etc. in deps, or `[project.scripts]` defined | Suppresses subprocess-related Bandit rules (B404, B603, B607), caps security at 15 |
| **library** | Has `[build-system]` but no scripts | Default rules |
| **script** | Few `.py` files, no package directory | Relaxed structure checks, no tests/license requirement |

Override with `--profile <type>` or set `profile` in `pyproject.toml`.

## Pre-commit Hook

Block commits when the health score drops too low.

### Quick install (git hook)

```bash
# Install with default threshold (score < 50 blocks commit)
python-doctor --pre-commit

# Or set a custom threshold
python-doctor --pre-commit --min-score 80
```

### Using the pre-commit framework

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/saikatkumardey/python-doctor
    rev: v2026.03.22
    hooks:
      - id: python-doctor
```

## CI/CD

### GitHub Actions

Add a health check step to any workflow:

```yaml
- name: Health Check
  run: |
    pipx install python-doctor
    python-doctor . --verbose
```

Exits with code 1 if score drops below 50.

### Auto-Updating Badge

Add a live score badge to your README:

```bash
# 1. Get your badge markdown (runs a scan)
python-doctor . --badge

# 2. Generate the CI workflow
python-doctor --ci > .github/workflows/python-doctor.yml

# 3. Commit and push
git add README.md .github/workflows/python-doctor.yml
git commit -m "Add python-doctor badge"
git push
```

The workflow runs on every push to `main`, updates the badge score in your README, and auto-commits the change.

## Benchmarks

Scores on popular open-source projects:

| Project | Stars | Score | Profile | Top Findings |
|---------|-------|-------|---------|-------------|
| [requests](https://github.com/psf/requests) | 52k+ | **81/100** (Good) | library | Weak hashes (B324), complexity (CC 21), large files, no type hints |
| [flask](https://github.com/pallets/flask) | 69k+ | **78/100** (Good) | web | Hardcoded passwords, complexity (CC 23), large files (app.py: 1625 lines) |
| [fastapi](https://github.com/fastapi/fastapi) | 82k+ | **78/100** (Good) | web | Complexity (CC 45), large files (routing.py: 4956 lines), many params |

Test and example files are excluded from security and complexity analysis. Docs directories are excluded from linting.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, how to add analyzers, and release process.

```bash
# Quick start
git clone https://github.com/saikatkumardey/python-doctor.git
cd python-doctor
uv sync --extra dev
uv run pytest tests/ -v
```

## License

[MIT](LICENSE) - Saikat Kumar Dey, 2026
