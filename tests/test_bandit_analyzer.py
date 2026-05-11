"""Tests for the bandit security analyzer helpers."""

from python_doctor.analyzers import bandit_analyzer
from python_doctor.analyzers.bandit_analyzer import (
    _build_bandit_cmd,
    _finding_from_item,
    _is_literal_subprocess,
    _items_to_findings,
    _should_skip,
)


def test_build_cmd_uses_module_when_binary_missing(monkeypatch):
    """Falls back to ``python -m bandit`` when the binary is not on PATH."""
    monkeypatch.setattr(bandit_analyzer.shutil, "which", lambda _: None)
    cmd = _build_bandit_cmd("/tmp/x", "/tmp/x/.venv")
    assert cmd[1] == "-m"
    assert cmd[2] == "bandit"
    assert cmd[-1] == "/tmp/x"


def test_build_cmd_uses_binary_when_available(monkeypatch):
    """Prefers the standalone bandit binary when present."""
    monkeypatch.setattr(bandit_analyzer.shutil, "which", lambda _: "/usr/bin/bandit")
    cmd = _build_bandit_cmd("/tmp/x", "")
    assert cmd[0] == "bandit"
    assert "-r" in cmd
    assert "json" in cmd


def test_is_literal_subprocess_true_for_string_args():
    """A call with all string literal arguments is recognized as literal."""
    finding = {"code": 'subprocess.run("ls -la")'}
    assert _is_literal_subprocess(finding) is True


def test_is_literal_subprocess_true_for_string_list():
    """A list of string literals counts as literal subprocess args."""
    finding = {"code": 'subprocess.run(["ls", "-la"])'}
    assert _is_literal_subprocess(finding) is True


def test_is_literal_subprocess_false_for_variable():
    """Variable arguments are not literal."""
    finding = {"code": "subprocess.run(user_cmd)"}
    assert _is_literal_subprocess(finding) is False


def test_is_literal_subprocess_false_on_syntax_error():
    """Unparseable code returns False rather than raising."""
    finding = {"code": "not valid python !!!"}
    assert _is_literal_subprocess(finding) is False


def test_should_skip_b101_always():
    """B101 (assert) is always skipped — it's a standard Python pattern."""
    item = {"test_id": "B101", "code": "assert x"}
    assert _should_skip(item, in_test=False, in_example=False) is True


def test_should_skip_b105_in_tests():
    """Hardcoded password in test files is fake — skip."""
    assert _should_skip({"test_id": "B105"}, in_test=True, in_example=False) is True


def test_should_skip_b105_not_in_source():
    """Hardcoded password in real source must be reported."""
    assert _should_skip({"test_id": "B105"}, in_test=False, in_example=False) is False


def test_should_skip_b113_in_test():
    """Missing request timeout in tests is fine."""
    assert _should_skip({"test_id": "B113"}, in_test=True, in_example=False) is True


def test_should_skip_b603_with_literal_args():
    """B603 with literal subprocess args is skipped."""
    item = {"test_id": "B603", "code": 'subprocess.run("echo hi")'}
    assert _should_skip(item, in_test=False, in_example=False) is True


def test_should_skip_b603_with_variable_args_not_skipped():
    """B603 with variable args is still reported in source code."""
    item = {"test_id": "B603", "code": "subprocess.run(cmd)"}
    assert _should_skip(item, in_test=False, in_example=False) is False


def test_should_skip_real_high_severity_in_source_false():
    """Real high-severity issues in source must never be skipped."""
    item = {"test_id": "B602", "code": "os.system(x)"}
    assert _should_skip(item, in_test=False, in_example=False) is False


def test_finding_from_item_copies_fields():
    """Finding fields are populated from the bandit item."""
    item = {
        "test_id": "B602",
        "issue_text": "shell=True",
        "filename": "/tmp/a.py",
        "line_number": 42,
        "issue_severity": "HIGH",
    }
    f = _finding_from_item(item)
    assert f.rule == "bandit/B602"
    assert f.file == "/tmp/a.py"
    assert f.line == 42
    assert f.severity == "high"
    assert f.cost == 2  # HIGH severity cost


def test_items_to_findings_applies_filters():
    """The filter pipeline drops B101 while keeping a real B602 finding."""
    items = [
        {"test_id": "B101", "filename": "src/a.py", "issue_severity": "LOW"},
        {
            "test_id": "B602",
            "filename": "src/b.py",
            "issue_severity": "HIGH",
            "issue_text": "x",
            "line_number": 1,
        },
    ]
    findings = _items_to_findings(items)
    assert len(findings) == 1
    assert findings[0].rule == "bandit/B602"


def test_analyze_clean_project_no_findings(tmp_path):
    """A clean Python file produces no security findings."""
    code = tmp_path / "clean.py"
    code.write_text("def add(a, b):\n    return a + b\n")
    result = bandit_analyzer.analyze(str(tmp_path))
    # No high-severity issues in trivial code.
    assert all(f.severity != "high" for f in result.findings)
