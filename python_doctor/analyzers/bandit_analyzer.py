"""Bandit security analyzer."""

import ast
import json
import os
import shutil
import subprocess  # nosec B404 — required for running CLI tools
import sys

from ..rules import BANDIT_SEVERITY_COST, CATEGORIES, AnalyzerResult, Finding
from ._util import SKIP_DIRS, diminishing_deduction, is_example_file, is_test_file


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


def _build_bandit_cmd(abs_path: str, excludes: str) -> list[str]:
    """Build the bandit command, preferring the standalone binary."""
    if shutil.which("bandit"):
        return ["bandit", "-r", "-f", "json", "-q", "--exclude", excludes, abs_path]
    return [sys.executable, "-m", "bandit", "-r", "-f", "json", "-q", "--exclude", excludes, abs_path]


def _run_bandit(cmd: list[str], result: AnalyzerResult) -> list[dict] | None:
    """Run bandit and return its result list, or None if it failed."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)  # nosec B603
        data = json.loads(proc.stdout) if proc.stdout.strip() else {}
        return data.get("results", [])
    except FileNotFoundError:
        result.error = "bandit not found (skipped)"
        return None
    except Exception as e:
        result.error = str(e)
        return None


# Test IDs that are noise in test files (test code legitimately uses them).
_TEST_NOISE_IDS = frozenset({
    "B108", "B110", "B201", "B301", "B403", "B404", "B603", "B607", "B704",
})
# Test IDs for subprocess use that are fine in example/script directories.
_EXAMPLE_SUBPROCESS_IDS = frozenset({"B603", "B607", "B404"})


def _should_skip(item: dict, in_test: bool, in_example: bool) -> bool:
    """Return True when a bandit finding should be filtered out by context."""
    test_id = item.get("test_id", "?")

    # B101 (assert) is a standard Python pattern for internal invariants.
    if test_id == "B101":
        return True
    # Hardcoded passwords in test/example files are fake credentials.
    if test_id in ("B105", "B106", "B107") and (in_test or in_example):
        return True
    # No-timeout requests in test files are test code.
    if test_id == "B113" and in_test:
        return True
    # General test-file noise.
    if test_id in _TEST_NOISE_IDS and in_test:
        return True
    # Subprocess use in example/script dirs.
    if test_id in _EXAMPLE_SUBPROCESS_IDS and in_example:
        return True
    # Subprocess calls with only string literal args are safe.
    if test_id in ("B603", "B607") and _is_literal_subprocess(item):
        return True
    return False


def _finding_from_item(item: dict) -> Finding:
    """Build a Finding from a raw bandit result item."""
    sev = item.get("issue_severity", "LOW").upper()
    cost = BANDIT_SEVERITY_COST.get(sev, 1)
    test_id = item.get("test_id", "?")
    return Finding(
        category="security",
        rule=f"bandit/{test_id}",
        message=item.get("issue_text", ""),
        file=item.get("filename", ""),
        line=item.get("line_number", 0),
        severity=sev.lower(),
        cost=cost,
    )


def _items_to_findings(items: list[dict]) -> list[Finding]:
    """Convert raw bandit items into Findings, applying context filters."""
    findings: list[Finding] = []
    for item in items:
        filename = item.get("filename", "")
        if _should_skip(item, is_test_file(filename), is_example_file(filename)):
            continue
        findings.append(_finding_from_item(item))
    return findings


def analyze(path: str, **_kw) -> AnalyzerResult:
    """Run bandit security analysis on the project."""
    result = AnalyzerResult(category="security")
    max_ded = _kw.get("max_deduction", CATEGORIES["security"]["max_deduction"])
    abs_path = os.path.abspath(path)
    excludes = ",".join(os.path.join(abs_path, d) for d in SKIP_DIRS)

    cmd = _build_bandit_cmd(abs_path, excludes)
    items = _run_bandit(cmd, result)
    if items is None:
        return result

    result.findings = _items_to_findings(items)
    result.deduction = diminishing_deduction(
        [f.cost for f in result.findings], top_n=5, tail_rate=0.1, cap=max_ded
    )
    return result
