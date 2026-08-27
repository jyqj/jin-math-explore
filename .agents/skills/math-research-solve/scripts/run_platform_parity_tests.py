#!/usr/bin/env python3
"""Run every declared native parity Harness for one concrete platform."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path(__file__).resolve().parents[1] / "references" / "platform-parity-manifest.json")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    payload = args.manifest.resolve().parents[2]
    tests: dict[tuple[str, str], None] = {}
    for entry in manifest["entries"]:
        if entry.get("implementation_status") != "complete":
            continue
        tests[(entry["skill"], entry["success_test"])] = None
        tests[(entry["skill"], entry["blocked_test"])] = None
    env = os.environ.copy(); env["PYTHONDONTWRITEBYTECODE"] = "1"; env.setdefault("PYTHONUTF8", "1")
    results = []
    for skill, relative in sorted(tests):
        path = payload / skill / relative
        completed = subprocess.run(
            [sys.executable, "-B", str(path)], cwd=path.parent,
            capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, check=False,
        )
        combined = completed.stdout + "\n" + completed.stderr
        skipped = "skipped=" in combined or " (skipped" in combined
        results.append({
            "skill": skill, "test": relative, "exit_code": completed.returncode,
            "skips_detected": skipped,
            "status": "passed" if completed.returncode == 0 and not skipped else "passed-with-skips" if completed.returncode == 0 else "failed",
            "tail": combined.strip().splitlines()[-8:],
        })
    ok = all(item["status"] == "passed" for item in results)
    receipt = {
        "schema": "pika-platform-parity-test-run/v1", "ok": ok,
        "system": platform.system(), "release": platform.release(), "machine": platform.machine(),
        "python": platform.python_version(), "tests": results,
    }
    print(json.dumps(receipt, ensure_ascii=False, separators=(",", ":")))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
