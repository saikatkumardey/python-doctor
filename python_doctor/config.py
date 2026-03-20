"""Optional configuration from pyproject.toml [tool.python-doctor]."""
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
class Config:
    profile_override: str | None = None
    suppress_rules: set[str] = field(default_factory=set)
    per_file_suppress: dict[str, set[str]] = field(default_factory=dict)
    max_deduction_overrides: dict[str, int] = field(default_factory=dict)


def load_config(path: str) -> Config:
    config = Config()
    pyproject = os.path.join(path, "pyproject.toml")
    if not os.path.isfile(pyproject) or tomllib is None:
        return config
    try:
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
    except Exception:
        return config

    tc = data.get("tool", {}).get("python-doctor", {})
    if not tc:
        return config

    if "profile" in tc:
        config.profile_override = tc["profile"]
    if "suppress" in tc:
        config.suppress_rules = set(tc["suppress"])
    for pat, rules in tc.get("per-file-suppress", {}).items():
        config.per_file_suppress[pat] = set(rules) if isinstance(rules, list) else {rules}
    for cat, val in tc.get("max-deduction", {}).items():
        if isinstance(val, int):
            config.max_deduction_overrides[cat] = val
    return config
