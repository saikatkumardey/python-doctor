"""Bandit security analyzer."""

import json
import os
import shutil
import subprocess  # nosec B404 — required for running CLI tools
import sys

from ..rules import BANDIT_SEVERITY_COST, CATEGORIES, AnalyzerResult, Finding

_EXCLUDE_DIRS = [".venv", "venv", "node_modules", "__pycache__", ".git", ".tox", ".mypy_cache", ".ruff_cache"]


def _is_test_file(filepath: str) -> bool:
    """Check if a file is a test file (in test dir or test-named)."""
    parts = os.path.normpath(filepath).split(os.sep)
    if any(p in ("tests", "test") for p in parts):
        return True
    basename = os.path.basename(filepath)
    return basename.startswith("test_") or basename.endswith("_test.py")


def analyze(path: str, **_kw) -> AnalyzerResult:
    """Run bandit security analysis on the project."""
    result = AnalyzerResult(category="security")
    max_ded = CATEGORIES["security"]["max_deduction"]
    abs_path = os.path.abspath(path)
    excludes = ",".join(os.path.join(abs_path, d) for d in _EXCLUDE_DIRS)

    if shutil.which("bandit"):
        cmd = ["bandit", "-r", "-f", "json", "-q", "--exclude", excludes, abs_path]
    else:
        cmd = [sys.executable, "-m", "bandit", "-r", "-f", "json", "-q", "--exclude", excludes, abs_path]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)  # nosec B603
        data = json.loads(proc.stdout) if proc.stdout.strip() else {}
        items = data.get("results", [])
    except FileNotFoundError:
        result.error = "bandit not found (skipped)"
        return result
    except Exception as e:
        result.error = str(e)
        return result

    for item in items:
        sev = item.get("issue_severity", "LOW").upper()
        cost = BANDIT_SEVERITY_COST.get(sev, 1)
        test_id = item.get("test_id", "?")
        msg = item.get("issue_text", "")
        filename = item.get("filename", "")
        line = item.get("line_number", 0)

        # Skip B101 (assert) in test files
        if test_id == "B101" and _is_test_file(filename):
            continue

        result.findings.append(Finding(
            category="security", rule=f"bandit/{test_id}", message=msg,
            file=filename, line=line, severity=sev.lower(), cost=cost,
        ))

    result.deduction = min(sum(f.cost for f in result.findings), max_ded)
    return result
