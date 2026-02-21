"""Structure analyzer: file sizes, tests, type hints, project health."""

import ast
import os

from ..rules import (
    CATEGORIES,
    LARGE_FILE_COST,
    LARGE_FILE_THRESHOLD,
    LOW_TEST_RATIO_COST,
    LOW_TYPE_HINTS_COST,
    NO_GITIGNORE_COST,
    NO_LICENSE_COST,
    NO_LINTER_CONFIG_COST,
    NO_PY_TYPED_COST,
    NO_README_COST,
    NO_TESTS_COST,
    NO_TYPE_CHECKER_COST,
    TYPE_HINT_THRESHOLD,
    VERY_LOW_TEST_RATIO_COST,
    AnalyzerResult,
    Finding,
)

_SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv", ".tox", ".mypy_cache", ".ruff_cache"}


def _count_lines(filepath: str) -> int:
    """Count total lines in a file."""
    try:
        with open(filepath, "r", errors="ignore") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def _count_code_lines(filepath: str) -> int:
    """Count non-blank, non-comment lines."""
    count = 0
    try:
        with open(filepath, "r", errors="ignore") as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    count += 1
    except OSError:
        pass
    return count


def _has_type_hints(filepath: str) -> bool:
    """Check if a file contains any type annotations."""
    try:
        with open(filepath, "r", errors="ignore") as f:
            tree = ast.parse(f.read(), filename=filepath)
    except (SyntaxError, OSError):
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if node.returns is not None:
                return True
            for arg in node.args.args + node.args.kwonlyargs:
                if arg.annotation is not None:
                    return True
        if isinstance(node, ast.AnnAssign):
            return True
    return False


def _is_test_file(filepath: str) -> bool:
    """Check if a file is a test file."""
    parts = os.path.normpath(filepath).split(os.sep)
    if any(p in ("tests", "test") for p in parts):
        return True
    basename = os.path.basename(filepath)
    return basename.startswith("test_") or basename.endswith("_test.py")


def _collect_py_files(path: str) -> tuple[list[str], list[str], list[str], bool]:
    """Walk the project and classify Python files into source and test files."""
    py_files = []
    test_files = []
    source_files = []
    has_tests = False
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        if any(d in ("tests", "test") for d in dirs):
            has_tests = True
        for f in files:
            if f.endswith(".py"):
                fp = os.path.join(root, f)
                py_files.append(fp)
                if _is_test_file(fp):
                    has_tests = True
                    test_files.append(fp)
                else:
                    source_files.append(fp)
    return py_files, test_files, source_files, has_tests


def _check_large_files(py_files: list[str], result: AnalyzerResult) -> None:
    """Flag files exceeding the line threshold."""
    for fp in py_files:
        lines = _count_lines(fp)
        if lines > LARGE_FILE_THRESHOLD:
            result.findings.append(Finding(
                category="structure", rule="structure/large-file",
                message=f"{lines} lines (consider splitting)",
                file=fp, cost=LARGE_FILE_COST,
            ))


def _check_tests(has_tests: bool, test_files: list[str], source_files: list[str], result: AnalyzerResult) -> None:
    """Check for test existence and test-to-source ratio."""
    if not has_tests:
        result.findings.append(Finding(
            category="structure", rule="structure/no-tests",
            message="No tests directory or test files found",
            cost=NO_TESTS_COST,
        ))
        return

    test_lines = sum(_count_code_lines(f) for f in test_files)
    source_lines = sum(_count_code_lines(f) for f in source_files)
    if source_lines <= 0:
        return

    ratio = test_lines / source_lines
    if ratio < 0.1:
        result.findings.append(Finding(
            category="structure", rule="structure/low-test-ratio",
            message=f"Test-to-source ratio is {ratio:.2f} (very low, <0.1)",
            cost=VERY_LOW_TEST_RATIO_COST,
        ))
    elif ratio < 0.3:
        result.findings.append(Finding(
            category="structure", rule="structure/low-test-ratio",
            message=f"Test-to-source ratio is {ratio:.2f} (low, <0.3)",
            cost=LOW_TEST_RATIO_COST,
        ))


def _check_type_hints(py_files: list[str], result: AnalyzerResult) -> bool:
    """Check type hint coverage across files. Returns whether type hints are used."""
    hinted = sum(1 for fp in py_files if _has_type_hints(fp))
    uses_type_hints = hinted > 0
    ratio = hinted / len(py_files) if py_files else 1
    if ratio < TYPE_HINT_THRESHOLD:
        pct = int((1 - ratio) * 100)
        result.findings.append(Finding(
            category="structure", rule="structure/type-hints",
            message=f"No type hints found in {pct}% of files",
            cost=LOW_TYPE_HINTS_COST,
        ))
    return uses_type_hints


def _check_readme(path: str, result: AnalyzerResult) -> None:
    """Check for README file."""
    if not any(os.path.isfile(os.path.join(path, n)) for n in ("README.md", "README.rst", "README")):
        result.findings.append(Finding(
            category="structure", rule="structure/no-readme",
            message="No README found", cost=NO_README_COST,
        ))


def _check_license(path: str, result: AnalyzerResult) -> None:
    """Check for LICENSE file."""
    if not any(os.path.isfile(os.path.join(path, n)) for n in ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE")):
        result.findings.append(Finding(
            category="structure", rule="structure/no-license",
            message="No LICENSE file found", cost=NO_LICENSE_COST,
        ))


def _check_gitignore(path: str, result: AnalyzerResult) -> None:
    """Check for .gitignore file."""
    if not os.path.isfile(os.path.join(path, ".gitignore")):
        result.findings.append(Finding(
            category="structure", rule="structure/no-gitignore",
            message="No .gitignore found", cost=NO_GITIGNORE_COST,
        ))


def _check_linter_config(path: str, result: AnalyzerResult) -> None:
    """Check for linter configuration."""
    if os.path.isfile(os.path.join(path, "ruff.toml")):
        return
    pyproject = os.path.join(path, "pyproject.toml")
    if os.path.isfile(pyproject):
        try:
            with open(pyproject) as f:
                if "[tool.ruff]" in f.read():
                    return
        except OSError:
            pass
    setup_cfg = os.path.join(path, "setup.cfg")
    if os.path.isfile(setup_cfg):
        try:
            with open(setup_cfg) as f:
                if "[flake8]" in f.read():
                    return
        except OSError:
            pass
    result.findings.append(Finding(
        category="structure", rule="structure/no-linter-config",
        message="No linter configuration found", cost=NO_LINTER_CONFIG_COST,
    ))


def _check_type_checker_config(path: str, result: AnalyzerResult) -> None:
    """Check for type checker configuration."""
    if any(os.path.isfile(os.path.join(path, n)) for n in ("mypy.ini", "pyrightconfig.json", ".mypy.ini")):
        return
    pyproject = os.path.join(path, "pyproject.toml")
    if os.path.isfile(pyproject):
        try:
            with open(pyproject) as f:
                if "[tool.mypy]" in f.read():
                    return
        except OSError:
            pass
    result.findings.append(Finding(
        category="structure", rule="structure/no-type-checker",
        message="No type checker configuration found", cost=NO_TYPE_CHECKER_COST,
    ))


def _check_py_typed(path: str, uses_type_hints: bool, result: AnalyzerResult) -> None:
    """Check for py.typed marker file when type hints are used."""
    if not uses_type_hints:
        return
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        if "py.typed" in files:
            return
    result.findings.append(Finding(
        category="structure", rule="structure/no-py-typed",
        message="Type hints used but no py.typed marker found", cost=NO_PY_TYPED_COST,
    ))


def _check_project_health(path: str, result: AnalyzerResult, uses_type_hints: bool) -> None:
    """Check for README, LICENSE, .gitignore, linter config, type checker config."""
    _check_readme(path, result)
    _check_license(path, result)
    _check_gitignore(path, result)
    _check_linter_config(path, result)
    _check_type_checker_config(path, result)
    _check_py_typed(path, uses_type_hints, result)


def analyze(path: str, **_kw) -> AnalyzerResult:
    """Analyze project structure: file sizes, tests, type hints, and project health."""
    result = AnalyzerResult(category="structure")
    max_ded = CATEGORIES["structure"]["max_deduction"]

    py_files, test_files, source_files, has_tests = _collect_py_files(path)
    if not py_files:
        return result

    _check_large_files(py_files, result)
    _check_tests(has_tests, test_files, source_files, result)
    uses_type_hints = _check_type_hints(py_files, result)
    _check_project_health(path, result, uses_type_hints)

    result.deduction = min(sum(f.cost for f in result.findings), max_ded)
    return result
