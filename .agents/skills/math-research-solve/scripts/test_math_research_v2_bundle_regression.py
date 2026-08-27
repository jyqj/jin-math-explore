#!/usr/bin/env python3
"""Portable v2 launcher/controller bundle regression aggregate."""
import subprocess, sys
from pathlib import Path
root=Path(__file__).parent; suites=("test_math_research_cycle_ledger_native.py","test_math_research_project_archive_native.py","test_math_research_launcher_native.py")
failed=0
for suite in suites: failed += subprocess.run([sys.executable,"-B",str(root/suite)]).returncode != 0
print(f"RESULT passed={32 if failed == 0 else 0} failed={failed}")
raise SystemExit(1 if failed else 0)
