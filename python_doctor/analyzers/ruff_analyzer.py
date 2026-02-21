"""Ruff linter analyzer."""

import json
import shutil
import subprocess  # nosec B404 — required for running CLI tools
import sys

from ..rules import CATEGORIES, RUFF_ERROR_COST, RUFF_WARNING_COST, AnalyzerResult, Finding


def analyze(path: str, fix: bool = False) -> AnalyzerResult:
    """Run ruff linting analysis, optionally auto-fixing issues."""
    result = AnalyzerResult(category="lint")
    max_ded = CATEGORIES["lint"]["max_deduction"]

    if shutil.which("ruff"):
        cmd = ["ruff", "check"]
    else:
        cmd = [sys.executable, "-m", "ruff", "check"]

    try:
        if fix:
            fix_cmd = cmd + ["--fix",
                 "--exclude", ".venv,node_modules,__pycache__,.git,.tox",
                 path]
            subprocess.run(fix_cmd, capture_output=True, text=True, timeout=120)  # nosec B603

        proc = subprocess.run(cmd + ["--output-format", "json",  # nosec B603
             "--exclude", ".venv,node_modules,__pycache__,.git,.tox",
             path],
            capture_output=True, text=True, timeout=120)
        items = json.loads(proc.stdout) if proc.stdout.strip() else []
    except FileNotFoundError:
        result.error = "ruff not found (skipped)"
        return result
    except Exception as e:
        result.error = str(e)
        return result

    for item in items:
        code = item.get("code", "?")
        msg = item.get("message", "")
        filename = item.get("filename", "")
        line = item.get("location", {}).get("row", 0)
        # E/W prefixes are warnings, others are errors
        is_warning = code.startswith(("W", "D"))
        cost = RUFF_WARNING_COST if is_warning else RUFF_ERROR_COST

        result.findings.append(Finding(
            category="lint", rule=f"ruff/{code}", message=msg,
            file=filename, line=line,
            severity="warning" if is_warning else "error", cost=cost,
        ))

    result.deduction = min(sum(f.cost for f in result.findings), max_ded)
    return result
