"""Tests for the exceptions analyzer."""

from python_doctor.analyzers import exceptions_analyzer


def test_detects_bare_except(tmp_path):
    """Bare except clauses should be flagged."""
    code = tmp_path / "bad.py"
    code.write_text("try:\n    pass\nexcept:\n    pass\n")
    result = exceptions_analyzer.analyze(str(tmp_path))
    rules = [f.rule for f in result.findings]
    assert "exceptions/bare" in rules


def test_detects_silent_swallow(tmp_path):
    """except Exception: pass should be flagged."""
    code = tmp_path / "silent.py"
    code.write_text("try:\n    pass\nexcept Exception:\n    pass\n")
    result = exceptions_analyzer.analyze(str(tmp_path))
    rules = [f.rule for f in result.findings]
    assert "exceptions/silent" in rules


def test_clean_code_no_findings(tmp_path):
    """Proper exception handling should produce no findings."""
    code = tmp_path / "good.py"
    code.write_text("try:\n    pass\nexcept ValueError as e:\n    print(e)\n")
    result = exceptions_analyzer.analyze(str(tmp_path))
    assert len(result.findings) == 0
