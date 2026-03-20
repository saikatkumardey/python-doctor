"""Exception handling analyzer."""

import ast
import os

from ..rules import BARE_EXCEPT_COST, CATEGORIES, SILENT_EXCEPTION_COST, AnalyzerResult, Finding
from ._util import SKIP_DIRS, is_test_file


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


def _is_pass_or_continue(handler: ast.ExceptHandler) -> bool:
    """Check if an except handler body is just ``pass`` or ``continue``."""
    return (
        len(handler.body) == 1
        and isinstance(handler.body[0], (ast.Pass, ast.Continue))
    )


def _find_fallback_chains(tree: ast.Module) -> set[int]:
    """Return handler line numbers that belong to fallback chains.

    A fallback chain is two or more consecutive ``try`` nodes in the same
    block where every handler body is just ``pass`` or ``continue``.  These
    represent intentional "try method A, then method B" patterns and should
    not be flagged.
    """
    suppressed: set[int] = set()

    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list):
            continue

        # Scan for runs of consecutive Try nodes whose handlers are all
        # pass/continue.
        run: list[ast.Try] = []
        for stmt in body:
            is_try = isinstance(stmt, ast.Try)
            if is_try and all(_is_pass_or_continue(h) for h in stmt.handlers):
                run.append(stmt)
            else:
                if len(run) >= 2:
                    for try_node in run:
                        for handler in try_node.handlers:
                            suppressed.add(handler.lineno)
                run = []
        # Flush any remaining run at the end of the body.
        if len(run) >= 2:
            for try_node in run:
                for handler in try_node.handlers:
                    suppressed.add(handler.lineno)

    return suppressed


def _check_file(fp: str, result: AnalyzerResult) -> None:
    """Analyze exception handlers in a single file."""
    try:
        with open(fp, "r", errors="ignore") as fh:
            tree = ast.parse(fh.read(), filename=fp)
    except (SyntaxError, OSError):
        return

    suppressed = _find_fallback_chains(tree)

    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if node.lineno in suppressed:
            continue
        _check_bare_except(node, fp, result)
        _check_silent_swallow(node, fp, result)


def analyze(path: str, **_kw) -> AnalyzerResult:
    """Analyze exception handling patterns across the project."""
    result = AnalyzerResult(category="exceptions")
    max_ded = _kw.get("max_deduction", CATEGORIES["exceptions"]["max_deduction"])

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if not f.endswith(".py"):
                continue
            fp = os.path.join(root, f)
            if is_test_file(fp):
                continue
            _check_file(fp, result)

    result.deduction = min(sum(f.cost for f in result.findings), max_ded)
    return result
