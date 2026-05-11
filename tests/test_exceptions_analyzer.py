"""Tests for the exceptions analyzer."""

import ast

from python_doctor.analyzers import exceptions_analyzer
from python_doctor.analyzers.exceptions_analyzer import (
    _find_fallback_chains,
    _is_fallback_try,
    _is_pass_or_continue,
)


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


def test_is_pass_or_continue_pass():
    """An ExceptHandler body with just ``pass`` is recognized."""
    handler = ast.parse("try:\n    x = 1\nexcept:\n    pass\n").body[0].handlers[0]
    assert _is_pass_or_continue(handler) is True


def test_is_pass_or_continue_continue():
    """An ExceptHandler body with just ``continue`` is recognized."""
    src = "for _ in []:\n    try:\n        x = 1\n    except:\n        continue\n"
    handler = ast.parse(src).body[0].body[0].handlers[0]
    assert _is_pass_or_continue(handler) is True


def test_is_pass_or_continue_real_body():
    """A handler with real code is NOT pass/continue."""
    src = "try:\n    x = 1\nexcept:\n    print('boom')\n"
    handler = ast.parse(src).body[0].handlers[0]
    assert _is_pass_or_continue(handler) is False


def test_is_fallback_try_true():
    """A Try whose handlers are all pass/continue counts as a fallback try."""
    src = "try:\n    a = 1\nexcept Exception:\n    pass\n"
    stmt = ast.parse(src).body[0]
    assert _is_fallback_try(stmt) is True


def test_is_fallback_try_false_for_non_try():
    """Non-Try statements are never fallback tries."""
    stmt = ast.parse("x = 1\n").body[0]
    assert _is_fallback_try(stmt) is False


def test_is_fallback_try_false_with_real_handler():
    """A Try with a non-pass handler is not a fallback try."""
    src = "try:\n    a = 1\nexcept Exception:\n    log('x')\n"
    stmt = ast.parse(src).body[0]
    assert _is_fallback_try(stmt) is False


def test_find_fallback_chains_suppresses_two_in_a_row():
    """Two consecutive fallback Try blocks are suppressed."""
    src = (
        "try:\n    a = 1\nexcept Exception:\n    pass\n"
        "try:\n    b = 2\nexcept Exception:\n    pass\n"
    )
    tree = ast.parse(src)
    suppressed = _find_fallback_chains(tree)
    # Both handlers should be in the suppression set.
    assert len(suppressed) == 2


def test_find_fallback_chains_single_try_not_suppressed():
    """A lone Try block is not a fallback chain."""
    src = "try:\n    a = 1\nexcept Exception:\n    pass\n"
    tree = ast.parse(src)
    suppressed = _find_fallback_chains(tree)
    assert suppressed == set()


def test_find_fallback_chains_broken_run_not_suppressed():
    """A statement between two fallback Trys breaks the chain."""
    src = (
        "try:\n    a = 1\nexcept Exception:\n    pass\n"
        "x = 1\n"
        "try:\n    b = 2\nexcept Exception:\n    pass\n"
    )
    tree = ast.parse(src)
    suppressed = _find_fallback_chains(tree)
    assert suppressed == set()


def test_fallback_chain_skipped_in_file(tmp_path):
    """An end-to-end fallback chain produces no exception findings."""
    code = tmp_path / "fallback.py"
    code.write_text(
        "try:\n    import fastjson as json\nexcept ImportError:\n    pass\n"
        "try:\n    import ujson as json\nexcept ImportError:\n    pass\n"
    )
    result = exceptions_analyzer.analyze(str(tmp_path))
    silent = [f for f in result.findings if f.rule == "exceptions/silent"]
    assert silent == []
