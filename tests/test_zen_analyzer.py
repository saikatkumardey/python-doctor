"""Tests for the Zen of Python analyzer."""

from python_doctor.analyzers import zen_analyzer


def test_detects_deep_nesting(tmp_path):
    code = tmp_path / "nested.py"
    code.write_text(
        "def deep():\n"
        "    if True:\n"
        "        for x in []:\n"
        "            if True:\n"
        "                while True:\n"
        "                    if True:\n"
        "                        pass\n"
    )
    result = zen_analyzer.analyze(str(tmp_path))
    rules = [f.rule for f in result.findings]
    assert "zen/deep-nesting" in rules


def test_shallow_nesting_ok(tmp_path):
    code = tmp_path / "flat.py"
    code.write_text(
        "def flat():\n"
        "    if True:\n"
        "        for x in []:\n"
        "            pass\n"
    )
    result = zen_analyzer.analyze(str(tmp_path))
    rules = [f.rule for f in result.findings]
    assert "zen/deep-nesting" not in rules


def test_detects_long_function(tmp_path):
    code = tmp_path / "long.py"
    lines = ["def long_func():\n"]
    lines.extend(["    x = 1\n"] * 55)
    code.write_text("".join(lines))
    result = zen_analyzer.analyze(str(tmp_path))
    rules = [f.rule for f in result.findings]
    assert "zen/long-function" in rules


def test_short_function_ok(tmp_path):
    code = tmp_path / "short.py"
    lines = ["def short_func():\n"]
    lines.extend(["    x = 1\n"] * 10)
    code.write_text("".join(lines))
    result = zen_analyzer.analyze(str(tmp_path))
    rules = [f.rule for f in result.findings]
    assert "zen/long-function" not in rules


def test_detects_too_many_params(tmp_path):
    code = tmp_path / "params.py"
    code.write_text("def many(a, b, c, d, e, f, g):\n    pass\n")
    result = zen_analyzer.analyze(str(tmp_path))
    rules = [f.rule for f in result.findings]
    assert "zen/too-many-params" in rules


def test_self_not_counted_as_param(tmp_path):
    code = tmp_path / "method.py"
    code.write_text(
        "class Foo:\n"
        "    def method(self, a, b, c, d, e):\n"
        "        pass\n"
    )
    result = zen_analyzer.analyze(str(tmp_path))
    rules = [f.rule for f in result.findings]
    assert "zen/too-many-params" not in rules


def test_detects_large_class(tmp_path):
    code = tmp_path / "big.py"
    methods = "\n".join(f"    def method_{i}(self):\n        pass\n" for i in range(12))
    code.write_text(f"class Big:\n{methods}")
    result = zen_analyzer.analyze(str(tmp_path))
    rules = [f.rule for f in result.findings]
    assert "zen/large-class" in rules


def test_small_class_ok(tmp_path):
    code = tmp_path / "small.py"
    code.write_text("class Small:\n    def one(self):\n        pass\n")
    result = zen_analyzer.analyze(str(tmp_path))
    rules = [f.rule for f in result.findings]
    assert "zen/large-class" not in rules


def test_detects_dense_code(tmp_path):
    code = tmp_path / "dense.py"
    code.write_text("x = 1; y = 2; z = 3\n")
    result = zen_analyzer.analyze(str(tmp_path))
    rules = [f.rule for f in result.findings]
    assert "zen/dense-code" in rules


def test_single_statement_ok(tmp_path):
    code = tmp_path / "clean.py"
    code.write_text("x = 1\ny = 2\n")
    result = zen_analyzer.analyze(str(tmp_path))
    rules = [f.rule for f in result.findings]
    assert "zen/dense-code" not in rules


def test_skips_test_files(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    code = tests_dir / "test_big.py"
    lines = ["def test_long():\n"]
    lines.extend(["    x = 1\n"] * 55)
    code.write_text("".join(lines))
    result = zen_analyzer.analyze(str(tmp_path))
    assert len(result.findings) == 0


def test_deduction_capped(tmp_path):
    code = tmp_path / "many_issues.py"
    # Generate many deeply nested functions to exceed max_deduction
    funcs = []
    for i in range(20):
        funcs.append(
            f"def f{i}():\n"
            "    if True:\n"
            "        for x in []:\n"
            "            if True:\n"
            "                while True:\n"
            "                    if True:\n"
            "                        pass\n\n"
        )
    code.write_text("".join(funcs))
    result = zen_analyzer.analyze(str(tmp_path))
    assert result.deduction <= 15  # max_deduction for zen category


def test_clean_code_no_findings(tmp_path):
    code = tmp_path / "clean.py"
    code.write_text(
        "def greet(name: str) -> str:\n"
        "    return f'Hello, {name}'\n"
    )
    result = zen_analyzer.analyze(str(tmp_path))
    assert len(result.findings) == 0
    assert result.deduction == 0
