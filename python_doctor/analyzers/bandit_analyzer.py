"""Bandit security analyzer."""

import ast
import json
import os
import shutil
import subprocess  # nosec B404 — required for running CLI tools
import sys

from ..rules import BANDIT_SEVERITY_COST, CATEGORIES, AnalyzerResult, Finding
from ._util import SKIP_DIRS, is_example_file, is_test_file


def _is_literal_subprocess(finding: dict) -> bool:
    """Return True if the subprocess call uses only string literal arguments."""
    code = finding.get("code", "")
    try:
        tree = ast.parse(code.strip())
    except SyntaxError:
        return False

    def _is_str_literal(node: ast.expr) -> bool:
        """Check if a node is a string constant or a list of string constants."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return True
        if isinstance(node, ast.List):
            return all(
                isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                for elt in node.elts
            )
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if all(_is_str_literal(arg) for arg in node.args):
                return True
    return False


def analyze(path: str, **_kw) -> AnalyzerResult:
    """Run bandit security analysis on the project."""
    result = AnalyzerResult(category="security")
    max_ded = _kw.get("max_deduction", CATEGORIES["security"]["max_deduction"])
    abs_path = os.path.abspath(path)
    excludes = ",".join(os.path.join(abs_path, d) for d in SKIP_DIRS)

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

        in_test = is_test_file(filename)
        in_example = is_example_file(filename)

        # Skip B101 (assert) everywhere — asserts are a standard Python pattern
        # for internal invariants, not a security issue
        if test_id == "B101":
            continue

        # Skip B105/B106/B107 (hardcoded passwords) in test/example files — fake credentials
        if test_id in ("B105", "B106", "B107") and (in_test or in_example):
            continue

        # Skip B113 (no timeout on requests) in test files — test code
        if test_id == "B113" and in_test:
            continue

        # Skip noise rules in test files — test code legitimately uses these patterns
        if test_id in ("B110", "B201", "B301", "B403", "B404", "B603", "B607", "B704") and in_test:
            continue

        # Skip B603/B607/B404 (subprocess) in scripts/example dirs — build/CI scripts
        if test_id in ("B603", "B607", "B404") and in_example:
            continue

        # Skip B603/B607 when subprocess uses only string literal arguments
        if test_id in ("B603", "B607") and _is_literal_subprocess(item):
            continue

        result.findings.append(Finding(
            category="security", rule=f"bandit/{test_id}", message=msg,
            file=filename, line=line, severity=sev.lower(), cost=cost,
        ))

    result.deduction = min(sum(f.cost for f in result.findings), max_ded)
    return result
