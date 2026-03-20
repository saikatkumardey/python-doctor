"""Project profile auto-detection."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]


@dataclass
class Profile:
    kind: str = "unknown"  # cli, web, library, script, unknown
    max_deduction_overrides: dict[str, int] = field(default_factory=dict)
    suppressed_rules: set[str] = field(default_factory=set)


_WEB_PACKAGES = {"flask", "django", "fastapi", "starlette", "tornado", "aiohttp", "sanic", "bottle"}
_CLI_PACKAGES = {"click", "typer", "fire", "cement", "cliff"}


def _parse_pyproject(path: str) -> dict:
    """Parse pyproject.toml and return the data dict, or empty dict on failure."""
    pyproject = os.path.join(path, "pyproject.toml")
    if not os.path.isfile(pyproject) or tomllib is None:
        return {}
    try:
        with open(pyproject, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def _read_dependencies(data: dict) -> set[str]:
    """Extract dependency names from parsed pyproject.toml data."""
    deps: set[str] = set()
    for raw in data.get("project", {}).get("dependencies", []):
        # Extract package name before version specifier
        name = raw.split(">=")[0].split("<=")[0].split("==")[0].split(">")[0].split("<")[0].split("[")[0].split(";")[0].strip()
        if name:
            deps.add(name.lower())
    return deps


def _has_scripts(data: dict) -> bool:
    """Check if the parsed pyproject.toml data has project scripts."""
    return bool(data.get("project", {}).get("scripts", {}))


def detect_profile_from_data(path: str, data: dict) -> Profile:
    """Detect the project profile from pre-parsed pyproject.toml data."""
    deps = _read_dependencies(data)

    # Web app
    if deps & _WEB_PACKAGES:
        return profile_for_kind("web")

    # CLI tool
    if (deps & _CLI_PACKAGES) or _has_scripts(data):
        return profile_for_kind("cli")

    # Library (has build-system but no scripts)
    if data.get("build-system"):
        return profile_for_kind("library")

    # Script (few .py files, no package)
    if os.path.isdir(path):
        py_files = [f for f in os.listdir(path) if f.endswith(".py")]
        has_package = any(
            os.path.isdir(os.path.join(path, d)) and os.path.isfile(os.path.join(path, d, "__init__.py"))
            for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))
        )
        if not has_package and len(py_files) <= 5:
            return profile_for_kind("script")

    return Profile()


def detect_profile(path: str) -> Profile:
    """Detect the project profile by parsing pyproject.toml."""
    data = _parse_pyproject(path)
    return detect_profile_from_data(path, data)


def profile_for_kind(kind: str) -> Profile:
    """Create a Profile with defaults for a given kind string."""
    p = Profile(kind=kind)
    if kind == "cli":
        p.suppressed_rules = {"bandit/B404"}
        p.max_deduction_overrides = {"security": 15}
    elif kind == "library":
        p.max_deduction_overrides = {"docs": 15}
    elif kind == "script":
        p.max_deduction_overrides = {"structure": 5}
        p.suppressed_rules = {"structure/no-tests", "structure/no-license"}
    return p
