#!/usr/bin/env python3
"""Build script to create standalone binary with PyInstaller."""

import shutil
import subprocess
import sys
from pathlib import Path

DIST_DIR = Path("dist")
BUILD_DIR = Path("build")


def build() -> None:
    """Build the binary using PyInstaller."""
    if shutil.which("pyinstaller") is None:
        print("Error: pyinstaller not found. Install with: pip install pyinstaller")
        sys.exit(1)

    print("Building python-doctor binary...")

    args = [
        "pyinstaller",
        "--name=python-doctor",
        "--onefile",
        "--console",
        "--collect-all=bandit",
        "--collect-all=vulture",
        "--collect-all=radon",
        "--hidden-import=pygments",
        "--hidden-import=colorama",
        "--hidden-import=toml",
        "--hidden-import=tomllib",
        "--hidden-import=sarif_om",
        "--clean",
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
        "--specpath",
        ".",
        "--add-data",
        "python_doctor:python_doctor",
        "run.py",
    ]

    result = subprocess.run(args)
    if result.returncode != 0:
        print("Build failed!")
        sys.exit(1)

    print(f"Binary created at: {DIST_DIR / 'python-doctor'}")


if __name__ == "__main__":
    build()
