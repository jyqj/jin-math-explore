from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent


def run(script: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPTS / script), *arguments],
        text=True,
        capture_output=True,
        check=False,
        timeout=90,
    )


class NativePlatformPathsTests(unittest.TestCase):
    def test_probe_success_and_invalid_argument_block(self) -> None:
        success = run("probe_backends.py", "--python-command", sys.executable)
        self.assertEqual(success.returncode, 0, success.stderr)
        payload = json.loads(success.stdout)
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertIn(payload["host"]["system"], {"Windows", "Darwin", "Linux"})
        blocked = run("probe_backends.py", "--not-a-real-option")
        self.assertEqual(blocked.returncode, 2)

    def test_inventory_success_and_invalid_reason_block(self) -> None:
        probe = run("probe_backends.py", "--python-command", sys.executable)
        self.assertEqual(probe.returncode, 0, probe.stderr)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            probe_file = root / "probe.json"
            state_file = root / "inventory.json"
            probe_file.write_text(probe.stdout, encoding="utf-8")
            success = run(
                "backend_inventory.py",
                "--mode",
                "ReadOrCreate",
                "--state-file",
                str(state_file),
                "--probe-json-file",
                str(probe_file),
            )
            self.assertEqual(success.returncode, 0, success.stderr)
            payload = json.loads(success.stdout)
            self.assertEqual(payload["inventory_schema_version"], "1.0")
            self.assertEqual(payload["cache"]["status"], "created")
            self.assertTrue(state_file.is_file())
            blocked = run(
                "backend_inventory.py",
                "--mode",
                "Invalidate",
                "--reason-code",
                "INVALID REASON",
                "--state-file",
                str(state_file),
                "--probe-json-file",
                str(probe_file),
            )
            self.assertNotEqual(blocked.returncode, 0)

    def test_observer_preserves_success_and_failure_exit_codes(self) -> None:
        success = run(
            "observer_run.py",
            "--skill",
            "example",
            "--catalog",
            "example/v1",
            "--phase",
            "example.run",
            "--",
            sys.executable,
            "-c",
            "raise SystemExit(0)",
        )
        self.assertEqual(success.returncode, 0, success.stderr)
        blocked = run(
            "observer_run.py",
            "--skill",
            "example",
            "--catalog",
            "example/v1",
            "--phase",
            "example.run",
            "--",
            sys.executable,
            "-c",
            "raise SystemExit(7)",
        )
        self.assertEqual(blocked.returncode, 7)


if __name__ == "__main__":
    unittest.main()
