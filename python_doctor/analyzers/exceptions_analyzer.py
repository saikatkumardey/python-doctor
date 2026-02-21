"""Exception handling analyzer."""

import ast
import os

from ..rules import BARE_EXCEPT_COST, CATEGORIES, SILENT_EXCEPTION_COST, AnalyzerResult, Finding

_SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv", ".tox", ".mypy_cache", ".ruff_cache"}


def _is_test_file(filepath: str) -> bool:
    """Check if a file is a test file."""
    parts = os.path.normpath(filepath).split(os.sep)
    if any(p in ("tests", "test") for p in parts):
        return True
    basename = os.path.basename(filepath)
    return basename.startswith("test_") or basename.endswith("_test.py")


def _check_bare_except(node: ast.ExceptHandler, fp: str, result: AnalyzerResult) -> None:
    """Flag bare except: clauses without an exception type."""
    if node.type is None:
        result.findings.append(Finding(
            category="exceptions", rule="exceptions/bare",
            message="Bare except: without exception type",
            file=fp, line=node.lineno, cost=BARE_EXCEPT_COST,
        ))


def _check_silent_swallow(node: ast.ExceptHandler, fp: str, result: AnalyzerResult) -> None:
    """Flag except Exception: pass patterns."""
    if (isinstance(node.type, ast.Name) and node.type.id == "Exception"
            and len(node.body) == 1 and isinstance(node.body[0], ast.Pass)):
        result.findings.append(Finding(
            category="exceptions", rule="exceptions/silent",
            message="except Exception: pass (silently swallowed)",
            file=fp, line=node.lineno, cost=SILENT_EXCEPTION_COST,
        ))


def _check_file(fp: str, result: AnalyzerResult) -> None:
    """Analyze exception handlers in a single file."""
    try:
        with open(fp, "r", errors="ignore") as fh:
            tree = ast.parse(fh.read(), filename=fp)
    except (SyntaxError, OSError):
        return

    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        _check_bare_except(node, fp, result)
        _check_silent_swallow(node, fp, result)


def analyze(path: str, **_kw) -> AnalyzerResult:
    """Analyze exception handling patterns across the project."""
    result = AnalyzerResult(category="exceptions")
    max_ded = CATEGORIES["exceptions"]["max_deduction"]

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for f in files:
            if not f.endswith(".py"):
                continue
            fp = os.path.join(root, f)
            if _is_test_file(fp):
                continue
            _check_file(fp, result)

    result.deduction = min(sum(f.cost for f in result.findings), max_ded)
    return result
