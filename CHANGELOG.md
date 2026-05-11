# Changelog

## 2026.5.11
- Parallel analyzer execution: 3-5x faster scans via ThreadPoolExecutor.
- Score delta cache: every run shows score change from last run, with top regression callout.
- New --strict flag: exit 2 on any regression vs cached state (for CI).
- New --no-cache flag: skip state caching when desired.
- Refactor: split cli.main() into _build_parser/_emit_output/_build_json_output/_save_state_safely/_compute_exit_code helpers. Self-score 89 -> 94.
- Cleanup: fixed E501 line-length violations in _util.py, profile.py, cli.py.
- Refactor: split bandit_analyzer.analyze (CC 20 -> <=15) and exceptions_analyzer._find_fallback_chains (nesting 6 -> <=5).
- Suppressed intentional B103 chmod warnings on git hook install path.
- Added unit tests; test-to-source ratio now >=0.3.

## 2026.2.22 (2026-02-22)

### Added
- Initial consolidated release (Fresh Start).
- 9 analyzers: security (Bandit), lint (Ruff), dead code (Vulture), complexity (Radon), structure, dependencies, docstrings, imports, exceptions.
- Structure checks: test-to-source ratio, README, LICENSE, .gitignore, linter config, type checker config, py.typed.
- CLI with `--verbose`, `--score`, `--json`, `--fix` flags.
- Claude Code plugin with `/python-doctor` skill.
- Adopted CalVer (YYYY.M.D) versioning scheme.
