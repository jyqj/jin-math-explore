from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ENTRY = Path(__file__).resolve().with_name("invoke_math_research_v13.py")


class NativeV13DispatcherTests(unittest.TestCase):
    def run_entry(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(ENTRY), *arguments],
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )

    def test_success_preserves_underlying_help(self) -> None:
        result = self.run_entry("--tool", "state", "--", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage:", result.stdout)

    def test_invalid_and_missing_tools_are_blocked(self) -> None:
        self.assertEqual(self.run_entry("--tool", "invalid").returncode, 1)
        self.assertEqual(self.run_entry().returncode, 1)


if __name__ == "__main__":
    unittest.main()
