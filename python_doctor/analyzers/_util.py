"""Shared utilities for analyzers."""

import os

# Directories to skip during analysis
SKIP_DIRS = frozenset({".venv", "venv", "node_modules", "__pycache__", ".git", ".tox", ".mypy_cache", ".ruff_cache", "docs"})


_TEST_DIRS = frozenset({"tests", "test", "testing"})
_EXAMPLE_DIRS = frozenset({"examples", "example", "docs_src", "samples", "demo", "demos", "benchmarks", "scripts"})


def is_test_file(filepath: str) -> bool:
    """Check if a file is a test file."""
    parts = os.path.normpath(filepath).split(os.sep)
    if any(p in _TEST_DIRS for p in parts):
        return True
    basename = os.path.basename(filepath)
    return basename.startswith("test_") or basename.endswith("_test.py") or basename == "conftest.py"


def is_example_file(filepath: str) -> bool:
    """Check if a file is in an example/docs directory."""
    parts = os.path.normpath(filepath).split(os.sep)
    return any(p in _EXAMPLE_DIRS for p in parts)


def diminishing_deduction(
    costs: list[float],
    top_n: int = 5,
    tail_rate: float = 0.1,
    cap: float = 100.0,
) -> float:
    """Compute a capped deduction with diminishing returns.

    The *top_n* most expensive findings are counted at full cost; every
    remaining finding is counted at *tail_rate* of its cost.  The result
    is capped at *cap*.
    """
    sorted_costs = sorted(costs, reverse=True)
    total = sum(c if i < top_n else c * tail_rate for i, c in enumerate(sorted_costs))
    return min(total, cap)
