"""Import hygiene analyzer."""

import ast
import os

from ..rules import CATEGORIES, CIRCULAR_IMPORT_COST, STAR_IMPORT_COST, AnalyzerResult, Finding

_SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv", ".tox", ".mypy_cache", ".ruff_cache"}


def _get_module_name(filepath: str, base_path: str) -> str | None:
    """Convert filepath to dotted module name relative to base."""
    rel = os.path.relpath(filepath, base_path)
    if rel.endswith(".py"):
        rel = rel[:-3]
    parts = rel.replace(os.sep, ".").split(".")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) if parts else None


def _collect_py_files(path: str) -> list[str]:
    """Collect all Python files in the project, skipping excluded dirs."""
    py_files = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))
    return py_files


def _check_star_imports(node: ast.ImportFrom, fp: str, result: AnalyzerResult) -> None:
    """Flag wildcard imports like 'from X import *'."""
    if node.names:
        for alias in node.names:
            if alias.name == "*":
                result.findings.append(Finding(
                    category="imports", rule="imports/star",
                    message=f"from {node.module or '?'} import *",
                    file=fp, line=node.lineno, cost=STAR_IMPORT_COST,
                ))


def _process_file_imports(
    fp: str, path: str, imports_graph: dict[str, set[str]], result: AnalyzerResult
) -> None:
    """Parse a single file and update the import graph, flagging star imports."""
    try:
        with open(fp, "r", errors="ignore") as f:
            tree = ast.parse(f.read(), filename=fp)
    except (SyntaxError, OSError):
        return

    mod_name = _get_module_name(fp, path)
    if mod_name:
        imports_graph.setdefault(mod_name, set())

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            _check_star_imports(node, fp, result)
            if mod_name and node.module:
                imports_graph.setdefault(mod_name, set()).add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if mod_name:
                    imports_graph.setdefault(mod_name, set()).add(alias.name)


def _build_import_graph(py_files: list[str], path: str, result: AnalyzerResult) -> dict[str, set[str]]:
    """Parse all files and build an import dependency graph, flagging star imports."""
    imports_graph: dict[str, set[str]] = {}
    for fp in py_files:
        _process_file_imports(fp, path, imports_graph, result)
    return imports_graph


def _detect_circular_imports(imports_graph: dict[str, set[str]], result: AnalyzerResult) -> None:
    """Detect direct circular imports (A->B and B->A)."""
    seen_cycles: set[tuple[str, str]] = set()
    for mod_a, deps_a in imports_graph.items():
        for dep in deps_a:
            if dep in imports_graph and mod_a in imports_graph[dep]:
                cycle_key = tuple(sorted([mod_a, dep]))
                if cycle_key not in seen_cycles:
                    seen_cycles.add(cycle_key)
                    result.findings.append(Finding(
                        category="imports", rule="imports/circular",
                        message=f"Circular import: {cycle_key[0]} <-> {cycle_key[1]}",
                        cost=CIRCULAR_IMPORT_COST,
                    ))


def analyze(path: str, **_kw) -> AnalyzerResult:
    """Analyze import hygiene: star imports and circular dependencies."""
    result = AnalyzerResult(category="imports")
    max_ded = CATEGORIES["imports"]["max_deduction"]

    py_files = _collect_py_files(path)
    imports_graph = _build_import_graph(py_files, path, result)
    _detect_circular_imports(imports_graph, result)

    result.deduction = min(sum(f.cost for f in result.findings), max_ded)
    return result
