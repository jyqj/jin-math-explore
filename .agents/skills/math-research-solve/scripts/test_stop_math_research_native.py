#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from math_research_control_primitives import read_signed_json, write_signed_json
from math_research_process_control import new_posix_termination_scope
from math_research_process_identity import snapshot_process


HERE = Path(__file__).resolve().parent
ENTRY = HERE / "stop_math_research.py"


@unittest.skipIf(os.name == "nt", "POSIX native stop path")
class NativeStopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.control = self.root / "control"
        self.old = os.environ.get("MATH_RESEARCH_CONTROL_HOME")
        os.environ["MATH_RESEARCH_CONTROL_HOME"] = str(self.control)
        self.children: list[subprocess.Popen[bytes]] = []

    def tearDown(self) -> None:
        for child in self.children:
            if child.poll() is None:
                os.killpg(child.pid, 9)
            child.wait(timeout=5)
        if self.old is None:
            os.environ.pop("MATH_RESEARCH_CONTROL_HOME", None)
        else:
            os.environ["MATH_RESEARCH_CONTROL_HOME"] = self.old
        self.temp.cleanup()

    def fixture(self) -> tuple[Path, subprocess.Popen[bytes]]:
        run = self.root / "run-001"; run.mkdir()
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
        self.children.append(child); time.sleep(0.05)
        identity = snapshot_process(child.pid)
        manifest = {
            "schema": "math-research-run/v2", "schema_version": 2,
            "run_id": "run-001", "thread_id": "thread-fixture", "run_directory": str(run),
            "process": {"identity": identity, "termination_scope": new_posix_termination_scope(child.pid)},
        }
        write_signed_json(run / "run.json", manifest, create_key=True)
        return run, child

    def invoke(self, run: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "-B", str(ENTRY), "--run-directory", str(run)], capture_output=True, text=True, check=False, env=os.environ.copy())

    def test_success_writes_request_then_stops_group(self) -> None:
        run, child = self.fixture(); result = self.invoke(run)
        self.assertEqual(0, result.returncode, result.stderr)
        child.wait(timeout=5)
        request = read_signed_json(run / "stop-request.json")["payload"]
        self.assertEqual(child.pid, request["target_identity"]["pid"])
        self.assertTrue(json.loads(result.stdout)["ok"])

    def test_tampered_manifest_is_blocked_without_signal(self) -> None:
        run, child = self.fixture()
        envelope = json.loads((run / "run.json").read_text(encoding="utf-8"))
        envelope["payload"]["process"]["identity"]["start_token"] += "-tampered"
        (run / "run.json").write_text(json.dumps(envelope), encoding="utf-8")
        result = self.invoke(run)
        self.assertEqual(1, result.returncode)
        self.assertIsNone(child.poll())

    def test_wrong_group_is_blocked_without_signal(self) -> None:
        run, child = self.fixture()
        manifest = read_signed_json(run / "run.json")["payload"]
        manifest["process"]["termination_scope"]["id"] += 1
        write_signed_json(run / "run.json", manifest)
        result = self.invoke(run)
        self.assertEqual(1, result.returncode)
        self.assertIsNone(child.poll())


if __name__ == "__main__":
    unittest.main()
