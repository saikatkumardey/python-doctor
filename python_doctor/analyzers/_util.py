"""Shared utilities for analyzers."""

import os

# Directories to skip during analysis
SKIP_DIRS = frozenset({".venv", "venv", "node_modules", "__pycache__", ".git", ".tox", ".mypy_cache", ".ruff_cache"})


def is_test_file(filepath: str) -> bool:
    """Check if a file is a test file."""
    parts = os.path.normpath(filepath).split(os.sep)
    if any(p in ("tests", "test") for p in parts):
        return True
    basename = os.path.basename(filepath)
    return basename.startswith("test_") or basename.endswith("_test.py")
