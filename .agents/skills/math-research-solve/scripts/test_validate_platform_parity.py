from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from validate_platform_parity import validate


class PlatformParityValidatorTests(unittest.TestCase):
    def make_fixture(self, *, blocked: bool = False) -> tuple[Path, Path, tempfile.TemporaryDirectory[str]]:
        temporary = tempfile.TemporaryDirectory()
        payload = Path(temporary.name) / "payload"
        skill = payload / "example"
        scripts = skill / "scripts"
        references = skill / "references"
        scripts.mkdir(parents=True)
        references.mkdir()
        source = scripts / "action.ps1"
        source.write_text("Write-Output ok\n", encoding="utf-8")
        equivalent = scripts / "action.py"
        equivalent.write_text("print('ok')\n", encoding="utf-8")
        success = scripts / "test_action_success.py"
        success.write_text("assert True\n", encoding="utf-8")
        failure = scripts / "test_action_blocked.py"
        failure.write_text("assert True\n", encoding="utf-8")
        manifest = references / "platform-parity-manifest.json"
        entry = {
            "skill": "example",
            "powershell_path": "scripts/action.ps1",
            "powershell_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "role": "production-or-maintenance",
            "python_candidates": ["scripts/action.py"],
            "equivalent_entrypoint": "scripts/action.py",
            "implementation_status": "missing" if blocked else "complete",
            "platform_status": {
                "linux": {"status": "verified", "evidence": "references/linux.json"},
                "darwin": {"status": "implemented-unverified", "reason": "No real runner."},
            },
            "success_test": "scripts/test_action_success.py",
            "blocked_test": "scripts/test_action_blocked.py",
            "semantic_parity_receipt": {
                "same_inputs": True,
                "same_outputs": True,
                "same_side_effects": True,
                "same_exit_codes": True,
                "reviewed": True,
            },
        }
        manifest.write_text(
            json.dumps({"schema": "pika-platform-parity/v2", "entries": [entry]}),
            encoding="utf-8",
        )
        return payload, manifest, temporary

    def test_success_fixture_passes(self) -> None:
        payload, manifest, temporary = self.make_fixture()
        self.addCleanup(temporary.cleanup)
        result = validate(payload, manifest)
        self.assertTrue(result["ok"], result)

    def test_unverified_entry_is_blocked(self) -> None:
        payload, manifest, temporary = self.make_fixture(blocked=True)
        self.addCleanup(temporary.cleanup)
        result = validate(payload, manifest)
        self.assertFalse(result["ok"])
        self.assertIn("implementation_incomplete", {item["kind"] for item in result["errors"]})

    def test_undeclared_script_is_blocked(self) -> None:
        payload, manifest, temporary = self.make_fixture()
        self.addCleanup(temporary.cleanup)
        extra = payload / "example" / "scripts" / "extra.psm1"
        extra.write_text("function Invoke-Extra {}\n", encoding="utf-8")
        result = validate(payload, manifest)
        self.assertFalse(result["ok"])
        self.assertIn("undeclared_powershell_file", {item["kind"] for item in result["errors"]})


if __name__ == "__main__":
    unittest.main()
