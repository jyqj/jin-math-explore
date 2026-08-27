from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
LAUNCHER = SCRIPTS / "math_research_platform.py"


class PlatformTests(unittest.TestCase):
    def run_launcher(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        values = os.environ.copy(); values["PYTHONDONTWRITEBYTECODE"] = "1"; values["PYTHONUTF8"] = "1"
        if env: values.update(env)
        return subprocess.run([sys.executable, "-B", str(LAUNCHER), *args], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", env=values, check=False)

    def test_windows_production_files_are_unchanged(self) -> None:
        manifest = json.loads((ROOT / "references" / "windows-production-sha256.json").read_text(encoding="utf-8"))
        for name, expected in manifest["files"].items():
            self.assertEqual(hashlib.sha256((SCRIPTS / name).read_bytes()).hexdigest(), expected, name)

    def test_missing_pwsh_is_a_blocked_runtime(self) -> None:
        result = self.run_launcher("doctor", "--json", env={"MATH_RESEARCH_PWSH": str(ROOT / "missing-pwsh")})
        self.assertEqual(result.returncode, 10)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertFalse(payload["checks"]["powershell_7_5_or_newer"])

    def test_v9_help_and_python_entry_are_callable(self) -> None:
        result = subprocess.run([sys.executable, "-B", str(SCRIPTS / "math_research_state_v9.py"), "--help"],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertIn("ticket-preflight-v8", result.stdout)

    def test_v10_help_and_python_entry_are_callable(self) -> None:
        result = subprocess.run([sys.executable, "-B", str(SCRIPTS / "math_research_state_v10.py"), "--help"],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertIn("ticket-preflight-v10", result.stdout)
        self.assertIn("route-reset-assess", result.stdout)

    def test_launcher_help_lists_all_current_routes(self) -> None:
        result = self.run_launcher("--help")
        self.assertEqual(result.returncode, 0)
        for route in ("startup", "ticket-preflight-v8", "build-legacy-successor-v8", "commit-head-v8",
                      "prepare-successor-v9", "prepare-transition-v9", "commit-transition-v9",
                      "ticket-preflight-v10", "prepare-successor-v10", "prepare-transition-v10",
                      "commit-transition-v10"):
            self.assertIn(route, result.stdout)


if __name__ == "__main__":
    unittest.main()
