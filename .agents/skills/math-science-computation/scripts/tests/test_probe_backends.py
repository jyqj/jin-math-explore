from __future__ import annotations

import json
import importlib.util
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "probe_backends.py"
POWERSHELL_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "probe_backends.ps1"


class ProbeBackendsTests(unittest.TestCase):
    def test_probe_returns_stable_json_shape_without_implicit_wsl(self) -> None:
        process = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
            ],
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        data = json.loads(process.stdout)
        self.assertEqual(data["schema_version"], "1.0")
        self.assertEqual(data["mathematica"]["mcp"]["status"], "requires_agent_probe")
        self.assertIn(data["primecount"]["status"], {"available", "unavailable", "probe_failed"})
        self.assertEqual(data["sagemath"]["wsl"]["status"], "not_requested")
        self.assertIn(data["python"]["status"], {"available", "unavailable", "probe_failed"})
        self.assertIn("native", data["sagemath"])
        self.assertIn(data["host"]["system"], {"Windows", "Darwin", "Linux"})
        self.assertTrue(data["host"]["architecture"])

    def test_explicit_primecount_probe_success(self) -> None:
        process = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--primecount-command", sys.executable],
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        data = json.loads(process.stdout)
        self.assertEqual(data["primecount"]["status"], "available")
        self.assertEqual(data["primecount"]["discovery_source"], "explicit")
        self.assertIn("Python", data["primecount"]["version_output"])

    def test_explicit_missing_primecount_does_not_fall_through(self) -> None:
        missing = Path(__file__).resolve().parent / "definitely-missing-primecount.exe"
        process = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--primecount-command",
                str(missing),
            ],
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        data = json.loads(process.stdout)
        self.assertEqual(data["primecount"]["status"], "unavailable")
        self.assertEqual(data["primecount"]["discovery_source"], "explicit")
        self.assertIsNone(data["primecount"]["path"])

    def test_wsl_request_is_rejected_as_unsupported_off_windows(self) -> None:
        spec = importlib.util.spec_from_file_location("probe_backends_module", SCRIPT_PATH)
        self.assertIsNotNone(spec and spec.loader)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        data = module.probe_sage("definitely-missing-sage", "Example", "sage", "Darwin")
        self.assertEqual(data["wsl"]["status"], "unsupported_platform")


@unittest.skipUnless(shutil.which("pwsh"), "PowerShell 7 is unavailable")
class PowerShellCompatibilityTests(unittest.TestCase):
    def test_powershell_entry_keeps_the_same_shape(self) -> None:
        process = subprocess.run(
            ["pwsh", "-NoLogo", "-NoProfile", "-File", str(POWERSHELL_SCRIPT_PATH)],
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        data = json.loads(process.stdout)
        self.assertEqual(data["schema_version"], "1.0")
        self.assertIn(data["host"]["system"], {"Windows", "Darwin", "Linux"})


if __name__ == "__main__":
    unittest.main()
