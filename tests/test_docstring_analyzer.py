"""Tests for the docstring analyzer."""

from python_doctor.analyzers import docstring_analyzer


def test_no_docstrings_flagged(tmp_path):
    """Files with no docstrings on public functions get flagged."""
    code = tmp_path / "nodoc.py"
    code.write_text("def hello():\n    pass\n\ndef world():\n    pass\n")
    result = docstring_analyzer.analyze(str(tmp_path))
    assert result.deduction > 0


def test_full_docstrings_clean(tmp_path):
    """Files with all public functions documented should pass."""
    code = tmp_path / "doc.py"
    code.write_text('def hello():\n    """Say hello."""\n    pass\n\ndef world():\n    """Say world."""\n    pass\n')
    result = docstring_analyzer.analyze(str(tmp_path))
    assert result.deduction == 0


def test_empty_project(tmp_path):
    """Empty project should have no deductions."""
    result = docstring_analyzer.analyze(str(tmp_path))
    assert result.deduction == 0


def test_private_functions_ignored(tmp_path):
    """Private functions (starting with _) should not be checked."""
    code = tmp_path / "priv.py"
    code.write_text("def _private():\n    pass\n")
    result = docstring_analyzer.analyze(str(tmp_path))
    assert result.deduction == 0
