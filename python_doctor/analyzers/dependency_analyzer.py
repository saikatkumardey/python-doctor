"""Dependency hygiene analyzer."""

import json
import os
import shutil
import subprocess  # nosec B404 — required for running CLI tools
import sys

from ..rules import (
    CATEGORIES,
    MIXED_BUILD_SYSTEM_COST,
    NO_BUILD_FILE_COST,
    VULNERABLE_DEP_COST,
    AnalyzerResult,
    Finding,
)


def _check_build_files(path: str) -> tuple[bool, bool, bool, bool]:
    """Check which build/dependency files exist in the project."""
    has_pyproject = os.path.isfile(os.path.join(path, "pyproject.toml"))
    has_setup_py = os.path.isfile(os.path.join(path, "setup.py"))
    has_setup_cfg = os.path.isfile(os.path.join(path, "setup.cfg"))
    has_requirements = os.path.isfile(os.path.join(path, "requirements.txt"))
    return has_pyproject, has_setup_py, has_setup_cfg, has_requirements


def _check_build_system(path: str, result: AnalyzerResult) -> None:
    """Check for missing or mixed build system files."""
    has_pyproject, has_setup_py, has_setup_cfg, has_requirements = _check_build_files(path)

    if not (has_pyproject or has_setup_py or has_setup_cfg):
        result.findings.append(Finding(
            category="dependencies", rule="deps/no-build-file",
            message="No pyproject.toml, setup.py, or setup.cfg found",
            cost=NO_BUILD_FILE_COST,
        ))

    if has_pyproject and has_requirements:
        result.findings.append(Finding(
            category="dependencies", rule="deps/mixed-build",
            message="Both pyproject.toml and requirements.txt found (consider consolidating)",
            cost=MIXED_BUILD_SYSTEM_COST,
        ))


def _run_pip_audit(path: str) -> list:
    """Run pip-audit and return vulnerability list."""
    if shutil.which("pip-audit"):
        cmd = ["pip-audit", "--format", "json", "--path", path]
    else:
        cmd = [sys.executable, "-m", "pip_audit", "--format", "json", "--path", path]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)  # nosec B603
        vulns = json.loads(proc.stdout) if proc.stdout.strip() else []
        if isinstance(vulns, dict):
            vulns = vulns.get("dependencies", [])
        return vulns
    except (FileNotFoundError, json.JSONDecodeError, subprocess.TimeoutExpired, OSError):
        return []


def _check_vulnerabilities(path: str, result: AnalyzerResult) -> None:
    """Run pip-audit to check for known vulnerabilities."""
    vulns = _run_pip_audit(path)
    for v in vulns:
        if not isinstance(v, dict) or not v.get("vulns"):
            continue
        for vuln in v["vulns"]:
            vid = vuln.get("id", "?") if isinstance(vuln, dict) else str(vuln)
            result.findings.append(Finding(
                category="dependencies", rule=f"deps/vuln/{vid}",
                message=f"Vulnerable: {v.get('name', '?')} {v.get('version', '')}",
                cost=VULNERABLE_DEP_COST,
            ))


def analyze(path: str, **_kw) -> AnalyzerResult:
    """Analyze dependency hygiene: build files, mixed systems, and vulnerabilities."""
    result = AnalyzerResult(category="dependencies")
    max_ded = CATEGORIES["dependencies"]["max_deduction"]

    _check_build_system(path, result)
    _check_vulnerabilities(path, result)

    result.deduction = min(sum(f.cost for f in result.findings), max_ded)
    return result
