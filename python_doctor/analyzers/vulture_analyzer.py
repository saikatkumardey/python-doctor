"""Vulture dead code analyzer."""

import re
import shutil
import subprocess  # nosec B404 — required for running CLI tools
import sys

from ..rules import CATEGORIES, VULTURE_COST, AnalyzerResult, Finding


def analyze(path: str, **_kw) -> AnalyzerResult:
    """Analyze dead code using vulture."""
    result = AnalyzerResult(category="dead_code")
    max_ded = CATEGORIES["dead_code"]["max_deduction"]

    if shutil.which("vulture"):
        cmd = ["vulture", "--min-confidence", "80",
               "--exclude", ".venv,node_modules,__pycache__,.git,.tox", path]
    else:
        cmd = [sys.executable, "-m", "vulture", "--min-confidence", "80",
               "--exclude", ".venv,node_modules,__pycache__,.git,.tox", path]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)  # nosec B603
        lines = proc.stdout.strip().splitlines() if proc.stdout else []
    except FileNotFoundError:
        result.error = "vulture not found (skipped)"
        return result
    except Exception as e:
        result.error = str(e)
        return result

    # vulture output: filename:line: unused X 'name' (NN% confidence)
    pat = re.compile(r"^(.+?):(\d+): (.+)$")
    for line in lines:
        m = pat.match(line)
        if m:
            filename, lineno, msg = m.group(1), int(m.group(2)), m.group(3)
            result.findings.append(Finding(
                category="dead_code", rule="vulture", message=msg,
                file=filename, line=lineno, cost=VULTURE_COST,
            ))

    result.deduction = min(sum(f.cost for f in result.findings), max_ded)
    return result
