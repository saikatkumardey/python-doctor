# Python Doctor 🐍

[![Tests](https://github.com/saikatkumardey/python-doctor/actions/workflows/test.yml/badge.svg)](https://github.com/saikatkumardey/python-doctor/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/python-doctor)](https://pypi.org/project/python-doctor/)
[![Python](https://img.shields.io/pypi/pyversions/python-doctor)](https://pypi.org/project/python-doctor/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**One command. One score. Built for AI agents.**

Python Doctor scans a Python codebase and returns a 0-100 health score with structured, actionable output. It's designed so an AI agent can run it, read the results, fix the issues, and verify the fix — in a loop, without human intervention.

```bash
python-doctor .
# 📊 Score: 98/100 (Excellent)
```

## Why?

Setting up linting, security scanning, and complexity analysis means configuring multiple tools, reading different output formats, and deciding what matters. Python Doctor wraps them into a single command with a single score.

An agent doesn't need to know what Bandit is. It just needs to know the score dropped and which lines to fix.

## Install the CLI

```bash
# Recommended - curl (no Python required, works on macOS/Linux)
curl -sL https://raw.githubusercontent.com/saikatkumardey/python-doctor/main/install.sh | sh

# Using pipx (isolated environment, macOS/Linux)
brew install pipx
pipx install python-doctor

# Using pip (may require --user on macOS/Linux)
pip install python-doctor

# Using uv (fast, modern)
uv tool install python-doctor

# Or clone and run directly (for development)
git clone https://github.com/saikatkumardey/python-doctor.git
cd python-doctor
uv run python-doctor /path/to/project
```

## Add to Your Coding Agent

Python Doctor works with any agent that can run shell commands. Install the CLI (above), then add the rule to your agent:

### Claude Code (Plugin)

Install as a Claude Code plugin to get the `/python-doctor` slash command:

```bash
/plugin marketplace add saikatkumardey/python-doctor
/plugin install python-doctor@python-doctor-plugins
```

Then use `/python-doctor` after modifying Python files. Claude will run the scan, fix issues by severity, and re-run until the score target is met.

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

### GitHub Actions (CI)

```yaml
- name: Health Check
  run: |
    pipx install python-doctor
    python-doctor . --verbose
```

Exits with code 1 if score < 50.

## Badge

Add a live score badge to your README:

```bash
# 1. Get your badge markdown (runs a scan)
python-doctor . --badge

# 2. Generate the CI workflow that auto-updates it on every push
python-doctor --ci > .github/workflows/python-doctor.yml

# 3. Commit both and push
git add README.md .github/workflows/python-doctor.yml
git commit -m "Add python-doctor badge"
git push
```

The CI workflow runs `python-doctor` on every push to `main`, updates the badge score in your README, and auto-commits the change.

## Usage

```bash
# Scan current directory
python-doctor .

# Verbose — show all findings with line numbers
python-doctor . --verbose

# Just the score (for CI or quick checks)
python-doctor . --score

# Structured JSON for agents
python-doctor . --json

# Auto-fix what Ruff can handle, then report the rest
python-doctor . --fix
```

## What It Checks

7 categories, weighted by impact and auto-scaled to 100:

| Category | Weight | Max | What |
|----------|--------|-----|------|
| 🔒 Security | 5 | -25 | Bandit (SQLi, hardcoded secrets, unsafe calls). Context-aware: skips noise in test/example/docs files. |
| 🧹 Lint | 4 | -20 | Ruff (unused imports, undefined names, style). Excludes docs/. |
| 🔄 Complexity | 3 | -15 | Radon (cyclomatic complexity > 15). Excludes test files. |
| 🧘 Zen | 3 | -15 | Deep nesting (>5), long functions (>75 lines), too many params (>10), large classes (>15 methods) |
| 🏗 Structure | 2 | -10 | File sizes (>1000 lines), test ratio, type hints, README, LICENSE, linter/type-checker config |
| ⚡ Exceptions | 2 | -10 | Bare `except:`, silently swallowed exceptions |
| 🔗 Imports | 1 | -5 | Star imports, circular import detection |

Weights are relative — add or remove a category and the max deductions automatically rebalance to sum to 100. Score = `max(0, 100 - total_deductions)`.

## Scores on Popular Projects

| Project | Stars | Score | Profile | Top Findings |
|---------|-------|-------|---------|-------------|
| [requests](https://github.com/psf/requests) | 52k+ | **81/100** (Good) | library | Weak hashes (B324), complexity (CC 21), large files, no type hints |
| [flask](https://github.com/pallets/flask) | 69k+ | **78/100** (Good) | web | Hardcoded passwords, complexity (CC 23), large files (app.py: 1625 lines) |
| [fastapi](https://github.com/fastapi/fastapi) | 82k+ | **78/100** (Good) | web | Complexity (CC 45), large files (routing.py: 4956 lines), many params |

Test and example files are excluded from security and complexity analysis. Docs directories are excluded from linting. Remaining deductions reflect real source code findings.

## The Loop

This is how an agent uses it:

1. `python-doctor . --json` → read the report
2. Fix the findings (auto-fix with `--fix`, manual fixes for the rest)
3. `python-doctor . --score` → verify improvement
4. Repeat until score target met

We built Python Doctor, then ran it on itself. Score: 47. Fixed everything it flagged. Score: 92. The tool eats its own dogfood.

## License

MIT — Saikat Kumar Dey, 2026
