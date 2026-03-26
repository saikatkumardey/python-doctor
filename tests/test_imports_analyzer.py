"""Tests for the imports analyzer."""

from python_doctor.analyzers import imports_analyzer


def test_star_import_detected(tmp_path):
    """Star imports should be flagged."""
    code = tmp_path / "star.py"
    code.write_text("from os.path import *\n")
    result = imports_analyzer.analyze(str(tmp_path))
    rules = [f.rule for f in result.findings]
    assert "imports/star" in rules


def test_clean_imports(tmp_path):
    """Normal imports should produce no findings."""
    code = tmp_path / "clean.py"
    code.write_text("import os\nfrom os.path import join\n")
    result = imports_analyzer.analyze(str(tmp_path))
    assert len(result.findings) == 0


def test_empty_project(tmp_path):
    """Empty project should have no findings."""
    result = imports_analyzer.analyze(str(tmp_path))
    assert result.deduction == 0


def test_star_import_in_init_skipped(tmp_path):
    """Star imports inside __init__.py are a standard re-export pattern and should not be flagged."""
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("from .core import *\n")
    (pkg / "core.py").write_text("X = 1\n")
    result = imports_analyzer.analyze(str(tmp_path))
    rules = [f.rule for f in result.findings]
    assert "imports/star" not in rules


def test_circular_import_stdlib_shadowing_skipped(tmp_path):
    """Circular import false positive caused by a local module sharing a name with a stdlib module is skipped."""
    # Simulate: project has a module named 'os' that imports from stdlib 'os',
    # which would otherwise appear as a cycle (os -> os).
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    # local 'mypkg.os' imports 'os' (stdlib) — leaf names both equal 'os'
    (pkg / "os.py").write_text("import os\n")
    result = imports_analyzer.analyze(str(tmp_path))
    rules = [f.rule for f in result.findings]
    assert "imports/circular" not in rules
