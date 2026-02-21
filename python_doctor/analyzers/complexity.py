"""Radon cyclomatic complexity analyzer."""

import json
import shutil
import subprocess  # nosec B404 — required for running CLI tools
import sys

from ..rules import CATEGORIES, AnalyzerResult, Finding


def analyze(path: str, **_kw) -> AnalyzerResult:
    """Analyze cyclomatic complexity using radon."""
    result = AnalyzerResult(category="complexity")
    max_ded = CATEGORIES["complexity"]["max_deduction"]

    if shutil.which("radon"):
        cmd = ["radon", "cc", "-j", "-n", "C",
               "-e", ".venv/*,node_modules/*,__pycache__/*,.git/*,.tox/*", path]
    else:
        cmd = [sys.executable, "-m", "radon", "cc", "-j", "-n", "C",
               "-e", ".venv/*,node_modules/*,__pycache__/*,.git/*,.tox/*", path]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)  # nosec B603
        data = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except FileNotFoundError:
        result.error = "radon not found (skipped)"
        return result
    except Exception as e:
        result.error = str(e)
        return result

    for filename, funcs in data.items():
        for func in funcs:
            cc = func.get("complexity", 0)
            name = func.get("name", "?")
            line = func.get("lineno", 0)
            if cc > 20:
                cost = 5
            elif cc > 10:
                cost = 2
            else:
                continue

            result.findings.append(Finding(
                category="complexity",
                rule=f"radon/CC{cc}",
                message=f"Function '{name}' has complexity {cc}",
                file=filename, line=line, cost=cost,
            ))

    result.deduction = min(sum(f.cost for f in result.findings), max_ded)
    return result
