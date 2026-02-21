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

Setting up linting, security scanning, dead code detection, and complexity analysis means configuring 5+ tools, reading 5 different output formats, and deciding what matters. Python Doctor wraps them all into a single command with a single score.

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

9 categories, 5 external tools + 4 custom AST analyzers:

| Category | Max | What |
|----------|-----|------|
| 🔒 Security | -30 | Bandit (SQLi, hardcoded secrets, unsafe calls). Auto-skips `assert` in test files. |
| 🧹 Lint | -25 | Ruff (unused imports, undefined names, style) |
| 💀 Dead Code | -15 | Vulture (unused functions, variables, imports) |
| 🔄 Complexity | -15 | Radon (cyclomatic complexity > 10) |
| 🏗 Structure | -15 | File sizes, test ratio, type hints, README, LICENSE, linter/type-checker config |
| 📦 Dependencies | -15 | Build file exists, no mixed systems, pip-audit vulnerabilities |
| 📝 Docstrings | -10 | Public function/class docstring coverage |
| 🔗 Imports | -10 | Star imports, circular import detection |
| ⚡ Exceptions | -10 | Bare `except:`, silently swallowed exceptions |

Score = `max(0, 100 - total_deductions)`. Each category is capped at its max.

## The Loop

This is how an agent uses it:

1. `python-doctor . --json` → read the report
2. Fix the findings (auto-fix with `--fix`, manual fixes for the rest)
3. `python-doctor . --score` → verify improvement
4. Repeat until score target met

We built Python Doctor, then ran it on itself. Score: 47. Fixed everything it flagged. Score: 98. The tool eats its own dogfood.

## License

MIT — Saikat Kumar Dey, 2026
