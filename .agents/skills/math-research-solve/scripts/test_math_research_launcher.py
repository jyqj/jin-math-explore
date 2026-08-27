#!/usr/bin/env python3
"""Portable wrapper for the shared Launcher v2 semantic suite."""
import subprocess, sys
from pathlib import Path

completed=subprocess.run([sys.executable,"-B",str(Path(__file__).with_name("test_math_research_launcher_native.py"))])
print(f"RESULT passed={11 if completed.returncode == 0 else 0} failed={0 if completed.returncode == 0 else 1}")
raise SystemExit(completed.returncode)
