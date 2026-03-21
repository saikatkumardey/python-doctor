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
