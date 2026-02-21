#!/usr/bin/env python3
"""Entry point wrapper for PyInstaller."""

import sys

from python_doctor.cli import main

if __name__ == "__main__":
    sys.exit(main())
