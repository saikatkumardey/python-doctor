"""Docstring coverage analyzer."""

import ast
import os

from ..rules import CATEGORIES, AnalyzerResult, Finding
from ._util import SKIP_DIRS, is_test_file


def _check_file(filepath: str) -> tuple[int, int]:
    """Return (total_public, documented) counts for public functions/classes."""
    try:
        with open(filepath, "r", errors="ignore") as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
    except (SyntaxError, OSError):
        return 0, 0

    total = 0
    documented = 0
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name.startswith("_"):
                continue
            total += 1
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)):
                documented += 1
    return total, documented


def _collect_coverage(path: str) -> tuple[int, int]:
    """Walk project files and sum up docstring coverage stats."""
    total_public = 0
    total_documented = 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if not f.endswith(".py"):
                continue
            fp = os.path.join(root, f)
            if is_test_file(fp):
                continue
            if f == "__init__.py" and os.path.getsize(fp) < 10:
                continue
            pub, doc = _check_file(fp)
            total_public += pub
            total_documented += doc
    return total_public, total_documented


def _compute_deduction(ratio: float) -> tuple[int, int]:
    """Compute cost and percentage from docstring coverage ratio."""
    pct = int(ratio * 100)
    if ratio < 0.25:
        return 10, pct
    if ratio < 0.50:
        return 5, pct
    return 0, pct


def analyze(path: str, **_kw) -> AnalyzerResult:
    """Analyze docstring coverage for public functions and classes."""
    result = AnalyzerResult(category="docs")
    max_ded = _kw.get("max_deduction", CATEGORIES["docs"]["max_deduction"])

    total_public, total_documented = _collect_coverage(path)
    if total_public == 0:
        return result

    ratio = total_documented / total_public
    cost, pct = _compute_deduction(ratio)
    if cost > 0:
        result.findings.append(Finding(
            category="docs", rule="docs/low-coverage",
            message=f"Only {pct}% of public functions/classes have docstrings",
            cost=cost,
        ))

    result.deduction = min(sum(f.cost for f in result.findings), max_ded)
    return result
