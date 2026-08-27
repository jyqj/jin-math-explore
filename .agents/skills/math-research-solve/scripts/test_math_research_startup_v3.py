#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=subprocess.run([sys.executable,"-B",str(Path(__file__).with_name("test_math_research_startup_v3_native.py"))]);print(f"RESULT passed={4 if r.returncode==0 else 0} failed={0 if r.returncode==0 else 1}");raise SystemExit(r.returncode)
