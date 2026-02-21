---
name: python-doctor
description: Run python-doctor to check Python codebase health. Use after modifying Python files to catch issues before committing.
---

# Python Doctor Health Check

You are running a Python codebase health check using `python-doctor`.

All commands below use `uvx` to run python-doctor without requiring prior installation. If `uvx` is not available, fall back to `python-doctor` directly (requires `pip install python-doctor` or `uv tool install python-doctor`).

## Step 1: Auto-fix first

Run Ruff auto-fixes to handle trivially fixable issues (unused imports, formatting, etc.):

```bash
uvx python-doctor . --fix
```

This fixes what it can and reports remaining issues.

## Step 2: Get the full report

Run a structured scan to see everything:

```bash
uvx python-doctor . --json
```

The JSON output contains:
- **score**: 0-100 health score
- **categories**: breakdown by category (security, lint, dead_code, complexity, structure, dependencies, docstrings, imports, exceptions)
- **findings**: list of individual issues with file, line, severity, message, and category

## Step 3: Fix by severity

Work through findings in this order:
1. **error** severity first — these are bugs, security issues, or critical problems
2. **warning** severity next — code quality, dead code, complexity
3. **info** severity last — style, documentation gaps

For each finding, read the file, understand the context, and fix the root cause. Do not just suppress warnings.

## Step 4: Verify improvement

After fixing, re-run:

```bash
uvx python-doctor . --score
```

## Score targets

- **80+**: Good to commit
- **50-79**: Needs work, fix warnings before committing
- **Below 50**: Do not commit. Fix errors and re-run until score is above 50.

## Tips

- Use `--verbose` to see all findings with line numbers in human-readable format
- The exit code is 1 when score < 50, useful for CI gating
- Each category has a max deduction cap, so fixing one category fully can recover significant points
- Security findings (Bandit) and lint findings (Ruff) typically have the highest impact on score
