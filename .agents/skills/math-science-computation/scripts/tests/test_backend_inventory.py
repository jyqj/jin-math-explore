from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "backend_inventory.py"
POWERSHELL_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "backend_inventory.ps1"
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "references" / "backend-inventory.schema.json"


def _probe_data(primecount_path: str | None = None, primecount_status: str = "unavailable") -> dict:
    return {
        "schema_version": "1.0",
        "probed_at_utc": datetime.now(timezone.utc).isoformat(),
        "host": {
            "system": __import__("platform").system(),
            "architecture": {
                "amd64": "x86_64",
                "x64": "x86_64",
                "aarch64": "arm64",
                "i386": "x86",
                "i686": "x86",
            }.get(__import__("platform").machine().lower(), __import__("platform").machine().lower()),
        },
        "mathematica": {
            "installations": [],
            "wolframscript": {"status": "unavailable", "path": None},
            "mcp": {"status": "requires_agent_probe"},
        },
        "primecount": {
            "status": primecount_status,
            "requested_command": "primecount",
            "discovery_source": "test",
            "path": primecount_path,
            "version_output": "test",
            "exit_code": 0 if primecount_status == "available" else None,
            "error": "",
        },
        "sagemath": {
            "native": {"status": "unavailable", "path": None},
            "wsl": {"status": "not_requested"},
        },
        "python": {
            "status": "available",
            "requested_command": "python",
            "path": sys.executable,
            "version": sys.version.split()[0],
            "libraries": {},
            "exit_code": 0,
            "error": "",
        },
    }


class BackendInventoryTests(unittest.TestCase):
    def _run(self, state: Path, fixture: Path, *extra: str) -> tuple[dict, float]:
        command = [
            sys.executable,
            str(SCRIPT_PATH),
            "--state-file",
            str(state),
            "--probe-json-file",
            str(fixture),
            *extra,
        ]
        started = time.perf_counter()
        process = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )
        elapsed = time.perf_counter() - started
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        return json.loads(process.stdout), elapsed

    def test_create_then_cache_hit_starts_no_backend_and_meets_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state = root / "state" / "inventory.json"
            fixture = root / "probe.json"
            fixture.write_text(json.dumps(_probe_data()), encoding="utf-8")

            created, _ = self._run(state, fixture)
            self.assertEqual(created["cache"]["status"], "created")
            self.assertTrue(created["cache"]["backend_started"])
            self.assertNotIn("mcp", created["local"]["mathematica"])

            fixture.write_text("this must not be read on a cache hit", encoding="utf-8")
            hit, wall_seconds = self._run(state, fixture)
            self.assertEqual(hit["cache"]["status"], "hit")
            self.assertFalse(hit["cache"]["backend_started"])
            self.assertLessEqual(hit["cache"]["elapsed_ms"], 250)
            self.assertLess(wall_seconds, 2.0)

    def test_missing_recorded_path_refreshes_only_affected_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            executable = root / "primecount.exe"
            executable.write_bytes(b"test")
            state = root / "inventory.json"
            fixture = root / "probe.json"
            fixture.write_text(
                json.dumps(_probe_data(str(executable), "available")),
                encoding="utf-8",
            )
            self._run(state, fixture)

            executable.unlink()
            fixture.write_text(json.dumps(_probe_data()), encoding="utf-8")
            refreshed, _ = self._run(state, fixture)
            self.assertEqual(refreshed["cache"]["status"], "refreshed")
            self.assertEqual(refreshed["cache"]["invalid_path_backends"], ["primecount"])
            self.assertEqual(refreshed["cache"]["refreshed_backends"], ["primecount"])
            self.assertEqual(refreshed["local"]["primecount"]["status"], "unavailable")

    def test_explicit_invalidation_records_reason_then_refreshes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state = root / "inventory.json"
            fixture = root / "probe.json"
            fixture.write_text(json.dumps(_probe_data()), encoding="utf-8")
            self._run(state, fixture)

            refreshed, _ = self._run(
                state,
                fixture,
                "--mode",
                "Invalidate",
                "--backend",
                "python",
                "--reason-code",
                "execution_failed",
            )
            self.assertEqual(refreshed["cache"]["refreshed_backends"], ["python"])
            stored = json.loads(state.read_text(encoding="utf-8"))
            self.assertEqual(stored["invalidations"][-1]["backend"], "python")
            self.assertEqual(stored["invalidations"][-1]["reason"], "execution_failed")

    def test_schema_declares_session_mcp_as_historical(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        mcp = schema["properties"]["mcp"]["properties"]
        self.assertEqual(mcp["persisted_status"]["const"], "historical_only")
        self.assertEqual(
            mcp["authority"]["const"],
            "current_session_tool_discovery_and_call",
        )
        self.assertIn("host", schema["properties"]["local"]["required"])
        self.assertIn("protocol_version", mcp["mathematica"]["properties"])

    def test_record_mcp_persists_protocol_and_distinct_versions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state = root / "inventory.json"
            fixture = root / "probe.json"
            fixture.write_text(json.dumps(_probe_data()), encoding="utf-8")
            self._run(state, fixture)
            recorded, _ = self._run(
                state,
                fixture,
                "--mode", "RecordMcp",
                "--mcp-server-name", "WolframLanguage",
                "--mcp-protocol-version", "2025-06-18",
                "--mcp-server-version", "2.2.0",
                "--mcp-wolfram-language-version", "15.0.1",
            )
            observation = recorded["mcp"]["recorded_mathematica_observation"]
            self.assertEqual(recorded["cache"]["status"], "mcp_recorded")
            self.assertFalse(recorded["cache"]["backend_started"])
            self.assertEqual(observation["protocol_version"], "2025-06-18")
            self.assertEqual(observation["server_version"], "2.2.0")
            self.assertEqual(observation["wolfram_language_version"], "15.0.1")
            stored = json.loads(state.read_text(encoding="utf-8"))
            self.assertEqual(stored["mcp"]["persisted_status"], "historical_only")

    def test_record_mcp_rejects_partial_or_non_protocol_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state = root / "inventory.json"
            fixture = root / "probe.json"
            fixture.write_text(json.dumps(_probe_data()), encoding="utf-8")
            self._run(state, fixture)
            for extra in (
                ["--mcp-server-name", "WolframLanguage"],
                ["--mcp-server-name", "WolframLanguage", "--mcp-protocol-version", "2.2.0", "--mcp-server-version", "2.2.0", "--mcp-wolfram-language-version", "15.0.1"],
            ):
                process = subprocess.run(
                    [sys.executable, str(SCRIPT_PATH), "--state-file", str(state), "--probe-json-file", str(fixture), "--mode", "RecordMcp", *extra],
                    text=True, capture_output=True, check=False, timeout=15,
                )
                self.assertNotEqual(process.returncode, 0)

    def test_snapshot_from_another_host_is_refreshed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state = root / "inventory.json"
            fixture = root / "probe.json"
            probe = _probe_data()
            fixture.write_text(json.dumps(probe), encoding="utf-8")
            self._run(state, fixture)

            stored = json.loads(state.read_text(encoding="utf-8"))
            stored["local"]["host"]["system"] = "Darwin" if probe["host"]["system"] != "Darwin" else "Linux"
            state.write_text(json.dumps(stored), encoding="utf-8")
            refreshed, _ = self._run(state, fixture)
            self.assertEqual(refreshed["cache"]["status"], "refreshed")
            self.assertEqual(refreshed["cache"]["refreshed_backends"], ["mathematica", "primecount", "sagemath", "python"])


@unittest.skipUnless(shutil.which("pwsh"), "PowerShell 7 is unavailable")
class PowerShellInventoryCompatibilityTests(unittest.TestCase):
    def test_powershell_reads_python_created_snapshot_without_starting_backends(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state = root / "inventory.json"
            fixture = root / "probe.json"
            fixture.write_text(json.dumps(_probe_data()), encoding="utf-8")
            create = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--state-file", str(state), "--probe-json-file", str(fixture)],
                text=True,
                capture_output=True,
                check=False,
                timeout=15,
            )
            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)
            fixture.write_text("cache hit must not read this", encoding="utf-8")
            hit = subprocess.run(
                ["pwsh", "-NoLogo", "-NoProfile", "-File", str(POWERSHELL_SCRIPT_PATH), "-StateFile", str(state), "-ProbeJsonFile", str(fixture)],
                text=True,
                capture_output=True,
                check=False,
                timeout=15,
            )
            self.assertEqual(hit.returncode, 0, hit.stdout + hit.stderr)
            data = json.loads(hit.stdout)
            self.assertEqual(data["cache"]["status"], "hit")
            self.assertFalse(data["cache"]["backend_started"])

    def test_powershell_records_negotiated_mcp_protocol_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            state = root / "inventory.json"
            fixture = root / "probe.json"
            fixture.write_text(json.dumps(_probe_data()), encoding="utf-8")
            create = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--state-file", str(state), "--probe-json-file", str(fixture)],
                text=True, capture_output=True, check=False, timeout=15,
            )
            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)
            record = subprocess.run(
                [
                    "pwsh", "-NoLogo", "-NoProfile", "-File", str(POWERSHELL_SCRIPT_PATH),
                    "-Mode", "RecordMcp", "-StateFile", str(state),
                    "-McpServerName", "WolframLanguage",
                    "-McpProtocolVersion", "2025-06-18",
                    "-McpServerVersion", "2.2.0",
                    "-McpWolframLanguageVersion", "15.0.1",
                ],
                text=True, capture_output=True, check=False, timeout=15,
            )
            self.assertEqual(record.returncode, 0, record.stdout + record.stderr)
            data = json.loads(record.stdout)
            observation = data["mcp"]["recorded_mathematica_observation"]
            self.assertEqual(observation["protocol_version"], "2025-06-18")
            self.assertEqual(observation["server_version"], "2.2.0")


if __name__ == "__main__":
    unittest.main()
