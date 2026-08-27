#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ENTRY = Path(__file__).with_name("test_math_research_control_path_amendment_v2.py")


class NativeRegressionEntryTests(unittest.TestCase):
    def test_success_contract(self) -> None:
        result = subprocess.run([sys.executable, "-B", str(ENTRY)], capture_output=True, text=True, check=False)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual({"ok": True, "tests": 12, "blocked_paths": 1, "explicit_sandbox_arguments": 0, "attempt_count": 0, "total_round_count": 0}, json.loads(result.stdout))

    def test_unknown_argument_is_blocked(self) -> None:
        result = subprocess.run([sys.executable, "-B", str(ENTRY), "unexpected"], capture_output=True, text=True, check=False)
        self.assertEqual(2, result.returncode)


if __name__ == "__main__": unittest.main()
