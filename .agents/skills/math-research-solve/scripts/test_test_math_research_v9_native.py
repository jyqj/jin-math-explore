#!/usr/bin/env python3
"""Harness checks for the native v9 test orchestrator."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ENTRY = HERE / "test_math_research_v9.py"


class NativeV9OrchestratorTests(unittest.TestCase):
    def test_success(self) -> None:
        result = subprocess.run([sys.executable, "-B", str(ENTRY)], check=False)
        self.assertEqual(0, result.returncode)

    def test_success_with_benchmark(self) -> None:
        result = subprocess.run([sys.executable, "-B", str(ENTRY), "--include-benchmark"], check=False)
        self.assertEqual(0, result.returncode)

    def test_unknown_option_is_blocked(self) -> None:
        result = subprocess.run(
            [sys.executable, "-B", str(ENTRY), "--unknown"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(0, result.returncode)


if __name__ == "__main__":
    unittest.main()
