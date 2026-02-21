# Contributing

Thanks for your interest in python-doctor!

## Quick Start

```bash
git clone https://github.com/saikatkumardey/python-doctor.git
cd python-doctor
uv sync --extra dev
uv run pytest tests/ -v
uv run python-doctor .
```

## Adding a New Analyzer

1. Create `python_doctor/analyzers/your_analyzer.py`
2. Implement `analyze(path: str, **kw) -> AnalyzerResult`
3. Add the category to `rules.py` `CATEGORIES` dict
4. Register it in `cli.py` `ANALYZERS` list
5. Add tests in `tests/test_your_analyzer.py`
6. Run `python-doctor .` — the score should still be 80+

Every analyzer follows the same pattern: scan the codebase, produce `Finding` objects, cap the deduction at the category max.

## Running Tests

```bash
uv run pytest tests/ -v
```

## Code Quality

We dogfood python-doctor on itself. The CI runs it on every push and fails if the score drops below 50.

```bash
uv run python-doctor . --verbose
```

## Releases

Releases are automated via GitHub Actions. Push a version tag to trigger:
- Binary builds for macOS, Linux, Windows
- GitHub release with install script
- PyPI publication

### Using bumpver

```bash
# Install (one-time)
pip install bumpver

# Patch release (0.2.1 → 0.2.2)
bumpver update --patch

# Minor release (0.2.1 → 0.3.0)
bumpver update --minor

# Major release (0.2.1 → 1.0.0)
bumpver update --major
```

This updates `pyproject.toml`, commits, and creates a git tag. Then push:

```bash
git push && git push --tags
```

### Manual Release

```bash
# Bump version in pyproject.toml
git tag v0.3.0
git push origin v0.3.0
```

### Installing Binary

Users can install without Python:

```bash
curl -sL https://raw.githubusercontent.com/saikatkumardey/python-doctor/main/install.sh | sh
```
