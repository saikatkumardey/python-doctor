"""Radon cyclomatic complexity analyzer."""

import json
import shutil
import subprocess  # nosec B404 — required for running CLI tools
import sys

from ..rules import CATEGORIES, AnalyzerResult, Finding
from ._util import is_example_file, is_test_file


def analyze(path: str, **_kw) -> AnalyzerResult:
    """Analyze cyclomatic complexity using radon."""
    result = AnalyzerResult(category="complexity")
    max_ded = _kw.get("max_deduction", CATEGORIES["complexity"]["max_deduction"])

    excludes = ".venv/*,node_modules/*,__pycache__/*,.git/*,.tox/*,tests/*,test/*,scripts/*,docs/*"
    if shutil.which("radon"):
        cmd = ["radon", "cc", "-j", "-n", "C", "-e", excludes, path]
    else:
        cmd = [sys.executable, "-m", "radon", "cc", "-j", "-n", "C", "-e", excludes, path]
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
        if is_test_file(filename) or is_example_file(filename):
            continue
        for func in funcs:
            cc = func.get("complexity", 0)
            name = func.get("name", "?")
            line = func.get("lineno", 0)
            if cc > 25:
                cost = 2
            elif cc > 15:
                cost = 1
            else:
                continue

            result.findings.append(Finding(
                category="complexity",
                rule=f"radon/CC{cc}",
                message=f"Function '{name}' has complexity {cc}",
                file=filename, line=line, cost=cost,
            ))

    # Diminishing returns: top 3 findings at full cost, rest at 10%
    sorted_costs = sorted((f.cost for f in result.findings), reverse=True)
    total = sum(c if i < 3 else c * 0.1 for i, c in enumerate(sorted_costs))
    result.deduction = min(total, max_ded)
    return result
