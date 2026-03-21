"""Main CLI entry point for Python Doctor."""

import argparse
import fnmatch
import json
import os
import sys

from . import __version__
from .analyzers import (
    bandit_analyzer,
    complexity,
    dependency_analyzer,
    docstring_analyzer,
    exceptions_analyzer,
    imports_analyzer,
    ruff_analyzer,
    structure,
    vulture_analyzer,
    zen_analyzer,
)
from .config import load_config
from .profile import detect_profile, profile_for_kind
from .rules import CATEGORIES
from .scorer import category_score, compute_score, score_label

ANALYZERS = [
    ("security", bandit_analyzer),
    ("lint", ruff_analyzer),
    ("dead_code", vulture_analyzer),
    ("complexity", complexity),
    ("structure", structure),
    ("dependencies", dependency_analyzer),
    ("docs", docstring_analyzer),
    ("imports", imports_analyzer),
    ("exceptions", exceptions_analyzer),
    ("zen", zen_analyzer),
]

MAX_FINDINGS_DISPLAY = 5

BADGE_CI_WORKFLOW = """\
name: Python Doctor

on:
  push:
    branches: [main]

permissions:
  contents: write

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install python-doctor
        run: pipx install python-doctor

      - name: Run python-doctor
        id: doctor
        run: |
          score=$(python-doctor . --score 2>/dev/null || echo "0")
          echo "score=$score" >> "$GITHUB_OUTPUT"
          echo "Python Doctor score: $score/100"

      - name: Determine badge color
        id: color
        run: |
          score=${{ steps.doctor.outputs.score }}
          if [ "$score" -ge 90 ]; then
            echo "color=brightgreen" >> "$GITHUB_OUTPUT"
          elif [ "$score" -ge 75 ]; then
            echo "color=green" >> "$GITHUB_OUTPUT"
          elif [ "$score" -ge 50 ]; then
            echo "color=yellow" >> "$GITHUB_OUTPUT"
          else
            echo "color=red" >> "$GITHUB_OUTPUT"
          fi

      - name: Update badge in README
        run: |
          score=${{ steps.doctor.outputs.score }}
          color=${{ steps.color.outputs.color }}
          encoded_score=$(echo "${score}/100" | sed 's|/|%2F|g')
          sed -i "s|python--doctor-[0-9]*%2F100-[a-z]*|python--doctor-${encoded_score}-${color}|" README.md

      - name: Commit if changed
        run: |
          git diff --quiet README.md && exit 0
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add README.md
          git commit -m "ci: update python-doctor badge to ${{ steps.doctor.outputs.score }}/100"
          git push
"""


def run_analyzers(path: str, fix: bool = False, profile_name: str | None = None):
    """Run all analyzers on the given path and return results."""
    config = load_config(path)

    # Determine profile: CLI flag > config file > auto-detect
    if profile_name:
        profile = profile_for_kind(profile_name)
    elif config.profile_override:
        profile = profile_for_kind(config.profile_override)
    else:
        profile = detect_profile(path)

    # Merge overrides (config wins over profile defaults)
    merged_max_deduction = {**profile.max_deduction_overrides, **config.max_deduction_overrides}
    merged_suppressed = profile.suppressed_rules | config.suppress_rules

    results = []
    for cat_name, mod in ANALYZERS:
        kwargs = {"path": path}
        if cat_name == "lint":
            kwargs["fix"] = fix
        if cat_name in merged_max_deduction:
            kwargs["max_deduction"] = merged_max_deduction[cat_name]
        result = mod.analyze(**kwargs)

        # Filter findings matching suppressed rules (global and per-file)
        original_findings = result.findings
        if merged_suppressed or config.per_file_suppress:
            result.findings = [
                f for f in original_findings
                if not (
                    (merged_suppressed and f.rule in merged_suppressed)
                    or (
                        f.file
                        and config.per_file_suppress
                        and any(
                            fnmatch.fnmatch(os.path.relpath(f.file, path), pat)
                            and f.rule in rules
                            for pat, rules in config.per_file_suppress.items()
                        )
                    )
                )
            ]
            if len(result.findings) != len(original_findings):
                max_ded = kwargs.get("max_deduction", CATEGORIES[cat_name]["max_deduction"])
                result.deduction = min(sum(f.cost for f in result.findings), max_ded)

        results.append(result)
    return results


def format_finding(f, path: str) -> str:
    """Format a single finding for display."""
    rel = os.path.relpath(f.file, path) if f.file else ""
    loc = f"{rel}:{f.line}" if f.line else rel
    icon = "⚠" if f.severity in ("warning", "low", "medium") else "✗"
    return f"  {icon} {f.rule}: {f.message}" + (f" ({loc})" if loc else "")


def print_report(results, path: str, verbose: bool = False):
    """Print the full health report to stdout."""
    print(f"\n🐍 Python Doctor v{__version__}")
    print(f"Scanning: {path}\n")

    score = compute_score(results)
    label = score_label(score)
    print(f"📊 Score: {score}/100 ({label})\n")

    for result in results:
        cat = CATEGORIES[result.category]
        cat_sc = category_score(result)
        emoji = cat["emoji"]
        name = cat["label"]
        max_d = cat["max_deduction"]

        if result.error:
            print(f"{emoji} {name} — ⚠ {result.error}")
            continue

        check = " ✓" if not result.findings else ""
        print(f"{emoji} {name} ({cat_sc}/{max_d}){check}")

        if not result.findings:
            print("  ✓ All clear.")
        else:
            limit = None if verbose else MAX_FINDINGS_DISPLAY
            shown = result.findings[:limit]
            for f in shown:
                print(format_finding(f, path))
            remaining = len(result.findings) - len(shown)
            if remaining > 0:
                print(f"  ... and {remaining} more")
        print()


def _badge_color(score: int) -> str:
    """Return shields.io color for a given score."""
    if score >= 90:
        return "brightgreen"
    if score >= 75:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"


def _print_badge(score: int):
    """Print a shields.io badge markdown snippet."""
    color = _badge_color(score)
    encoded = f"{score}%2F100"
    url = f"https://img.shields.io/badge/python--doctor-{encoded}-{color}"
    print(f"[![python-doctor]({url})](https://github.com/saikatkumardey/python-doctor)")
    print()
    print("Add this to your README.md. To auto-update the score on every push,")
    print("run: python-doctor --ci > .github/workflows/python-doctor.yml")


def main():
    """CLI entry point for python-doctor."""
    parser = argparse.ArgumentParser(
        prog="python-doctor",
        description="Scan Python codebases and get a 0-100 health score.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Directory to scan")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all findings")
    parser.add_argument("--score", action="store_true", help="Output only the score number")
    parser.add_argument("--json", dest="json_out", action="store_true", help="JSON output")
    parser.add_argument("--fix", action="store_true", help="Auto-fix what's possible (ruff --fix)")
    parser.add_argument(
        "--profile",
        choices=["cli", "web", "library", "script"],
        default=None,
        help="Override auto-detected project profile",
    )
    parser.add_argument("--badge", action="store_true", help="Output a shields.io badge markdown for your README")
    parser.add_argument("--ci", action="store_true", help="Output a GitHub Actions workflow for auto-updating the badge")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    args = parser.parse_args()

    if args.ci:
        print(BADGE_CI_WORKFLOW)
        return

    path = os.path.abspath(args.path)

    if not os.path.isdir(path):
        print(f"Error: '{path}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    results = run_analyzers(path, fix=args.fix, profile_name=args.profile)
    score = compute_score(results)

    if args.badge:
        _print_badge(score)
        return

    if args.score:
        print(score)
        return

    if args.json_out:
        output = {
            "version": __version__,
            "path": path,
            "score": score,
            "label": score_label(score),
            "categories": {},
        }
        for r in results:
            cat = CATEGORIES[r.category]
            output["categories"][r.category] = {
                "score": category_score(r),
                "max": cat["max_deduction"],
                "deduction": r.deduction,
                "error": r.error,
                "findings": [
                    {"rule": f.rule, "message": f.message, "file": f.file, "line": f.line, "severity": f.severity}
                    for f in r.findings
                ],
            }
        print(json.dumps(output, indent=2))
        return

    print_report(results, path, verbose=args.verbose)
    sys.exit(0 if score >= 50 else 1)


if __name__ == "__main__":
    main()
