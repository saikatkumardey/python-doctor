"""Zen of Python analyzer — checks for deep nesting, oversized functions/classes, and dense code."""

import ast
import os

from ..rules import (
    CATEGORIES,
    AnalyzerResult,
    Finding,
)
from ._util import SKIP_DIRS, is_example_file, is_test_file

# Costs
DEEP_NESTING_COST = 1
LONG_FUNCTION_COST = 1
MANY_PARAMS_COST = 0.5
LARGE_CLASS_COST = 1
DENSE_LINE_COST = 0.5

# Thresholds
NESTING_THRESHOLD = 5
LONG_FUNCTION_LINES = 75
MANY_PARAMS_THRESHOLD = 10
LARGE_CLASS_METHODS = 15
DENSE_STATEMENTS_THRESHOLD = 2  # multiple statements separated by ;


def _nesting_depth(node: ast.AST) -> int:
    """Compute maximum nesting depth of control flow inside a node."""
    _NESTING_TYPES = (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.ExceptHandler)

    max_depth = 0

    def _walk(n: ast.AST, depth: int) -> None:
        nonlocal max_depth
        if isinstance(n, _NESTING_TYPES):
            depth += 1
            if depth > max_depth:
                max_depth = depth
        for child in ast.iter_child_nodes(n):
            _walk(child, depth)

    _walk(node, 0)
    return max_depth


def _function_lines(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Count the line span of a function body."""
    if not node.body:
        return 0
    first = node.body[0].lineno
    last = node.body[-1].end_lineno or node.body[-1].lineno
    return last - first + 1


def _check_functions(tree: ast.Module, fp: str, result: AnalyzerResult) -> None:
    """Check functions for deep nesting, excessive length, and too many parameters."""
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        name = node.name

        depth = _nesting_depth(node)
        if depth > NESTING_THRESHOLD:
            result.findings.append(Finding(
                category="zen", rule="zen/deep-nesting",
                message=f"Function '{name}' has nesting depth {depth} (max {NESTING_THRESHOLD})",
                file=fp, line=node.lineno, cost=DEEP_NESTING_COST,
            ))

        lines = _function_lines(node)
        if lines > LONG_FUNCTION_LINES:
            result.findings.append(Finding(
                category="zen", rule="zen/long-function",
                message=f"Function '{name}' is {lines} lines (max {LONG_FUNCTION_LINES})",
                file=fp, line=node.lineno, cost=LONG_FUNCTION_COST,
            ))

        nparams = len(node.args.args) + len(node.args.posonlyargs) + len(node.args.kwonlyargs)
        if node.args.vararg:
            nparams += 1
        if node.args.kwarg:
            nparams += 1
        # Exclude 'self' and 'cls'
        if nparams > 0 and node.args.args and node.args.args[0].arg in ("self", "cls"):
            nparams -= 1
        # Skip constructors — they naturally have many params in frameworks
        if nparams > MANY_PARAMS_THRESHOLD and name not in ("__init__", "__init_subclass__"):
            result.findings.append(Finding(
                category="zen", rule="zen/too-many-params",
                message=f"Function '{name}' has {nparams} parameters (max {MANY_PARAMS_THRESHOLD})",
                file=fp, line=node.lineno, cost=MANY_PARAMS_COST,
            ))


def _check_classes(tree: ast.Module, fp: str, result: AnalyzerResult) -> None:
    """Check classes for too many methods."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        methods = [
            n for n in node.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        if len(methods) > LARGE_CLASS_METHODS:
            result.findings.append(Finding(
                category="zen", rule="zen/large-class",
                message=f"Class '{node.name}' has {len(methods)} methods (max {LARGE_CLASS_METHODS})",
                file=fp, line=node.lineno, cost=LARGE_CLASS_COST,
            ))


def _check_dense_lines(source: str, fp: str, result: AnalyzerResult) -> None:
    """Check for lines with multiple semicolon-separated statements."""
    for lineno, line in enumerate(source.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Skip strings that contain semicolons
        if stripped.startswith(("'", '"', "b'", 'b"', "f'", 'f"')):
            continue
        # Count semicolons outside of strings (simple heuristic)
        if stripped.count(";") >= DENSE_STATEMENTS_THRESHOLD:
            result.findings.append(Finding(
                category="zen", rule="zen/dense-code",
                message="Multiple statements on one line",
                file=fp, line=lineno, cost=DENSE_LINE_COST,
            ))


def _check_file(fp: str, result: AnalyzerResult) -> None:
    """Analyze a single file for Zen of Python violations."""
    try:
        with open(fp, "r", errors="ignore") as fh:
            source = fh.read()
        tree = ast.parse(source, filename=fp)
    except (SyntaxError, OSError):
        return

    _check_functions(tree, fp, result)
    _check_classes(tree, fp, result)
    _check_dense_lines(source, fp, result)


def analyze(path: str, **_kw) -> AnalyzerResult:
    """Analyze the project for Zen of Python violations."""
    result = AnalyzerResult(category="zen")
    max_ded = _kw.get("max_deduction", CATEGORIES["zen"]["max_deduction"])

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if not f.endswith(".py"):
                continue
            fp = os.path.join(root, f)
            if is_test_file(fp) or is_example_file(fp):
                continue
            _check_file(fp, result)

    # Diminishing returns: top 3 findings at full cost, rest at 10%
    sorted_costs = sorted((f.cost for f in result.findings), reverse=True)
    total = sum(c if i < 3 else c * 0.1 for i, c in enumerate(sorted_costs))
    result.deduction = min(total, max_ded)
    return result
