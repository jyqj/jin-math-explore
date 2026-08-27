#!/usr/bin/env python3
"""Native replacement for the historical v9 test orchestrator."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def run(name: str) -> int:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.setdefault("PYTHONUTF8", "1")
    return subprocess.run([sys.executable, "-B", str(HERE / name)], env=env, check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-benchmark", "-IncludeBenchmark", action="store_true")
    args = parser.parse_args()
    # The native suite excludes the historical shell-delegation assertion and
    # exercises both versioned Python state engines without platform skips.
    code = run("test_native_v9_v10_entrypoints.py")
    if code != 0:
        return code
    return run("benchmark_math_research_startup_v9.py") if args.include_benchmark else 0


if __name__ == "__main__":
    raise SystemExit(main())
