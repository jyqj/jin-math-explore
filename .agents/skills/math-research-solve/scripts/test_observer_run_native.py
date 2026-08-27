#!/usr/bin/env python3
"""Success and blocked-path checks for the native observer command runner."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
RUNNER = HERE / "observer_run.py"


class ObserverNativeTests(unittest.TestCase):
    def run_child(self, code: int) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(RUNNER),
                "--skill",
                "fixture",
                "--catalog",
                "fixture/v1",
                "--phase",
                "fixture.run",
                "--",
                sys.executable,
                "-c",
                f"raise SystemExit({code})",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_success_exit_is_preserved(self) -> None:
        self.assertEqual(0, self.run_child(0).returncode)

    def test_blocked_exit_is_preserved(self) -> None:
        self.assertEqual(7, self.run_child(7).returncode)

    def test_missing_command_fails_closed(self) -> None:
        result = subprocess.run(
            [sys.executable, "-B", str(RUNNER), "--skill", "x", "--catalog", "x/v1", "--phase", "x.run"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(0, result.returncode)


if __name__ == "__main__":
    unittest.main()
