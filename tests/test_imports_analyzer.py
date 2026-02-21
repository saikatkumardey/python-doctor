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
