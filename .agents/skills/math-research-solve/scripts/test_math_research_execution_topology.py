from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("math_research_execution_topology.py")


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def write_json(path: Path, value: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical(value)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Fixture:
    def __init__(self, root: Path) -> None:
        self.project = root / "project"
        self.project.mkdir()
        self.input = self.project / "inputs" / "problem.md"
        self.input.parent.mkdir()
        self.input.write_text("synthetic input\n", encoding="utf-8")
        self.ticket_rel = "runs/run-1/tickets/ticket-1.json"
        self.staging_rel = "runs/run-1/staging/ticket-1/solver"
        self.receipt_rel = self.staging_rel + "/execution-topology.json"
        write_json(self.project / "project.json", {
            "schema": "math-research-project/v10",
            "project_id": "synthetic-project",
            "control_generation": 1,
            "state": {"path": "state/g1.json", "sha256": "0" * 64},
        })
        self.ticket = {
            "schema": "math-research-ticket/v10",
            "ticket_id": "ticket-1",
            "input_artifacts": [{"id": "problem", "role": "task_contract", "path": "inputs/problem.md", "sha256": sha(self.input)}],
            "writable_staging_path": self.staging_rel,
            "continuity_capsule": {"path": "runs/run-1/continuity/capsule.json", "sha256": "1" * 64},
        }
        write_json(self.project / self.ticket_rel, self.ticket)
        self.worker = root / "worker.json"
        self.publisher = root / "publisher.json"
        self.consumer = root / "consumer.json"
        write_json(self.worker, self.descriptor("worker", "project-root-exec"))
        write_json(self.publisher, self.descriptor("publisher", "project-root-exec"))
        write_json(self.consumer, self.descriptor("consumer", "desktop-consumer"))
        self.consumer_principal = self.current_principal()

    @staticmethod
    def current_principal() -> str:
        if os.name == "nt":
            return subprocess.run(["whoami.exe"], capture_output=True, text=True, encoding="utf-8", check=True).stdout.strip()
        return f"uid:{os.geteuid()}"

    def descriptor(self, role: str, transport: str) -> dict:
        return {
            "schema": "math-research-execution-topology-descriptor/v1",
            "role": role,
            "transport": transport,
            "execution_workspace_root": str(self.project),
            "runner": "synthetic-runner",
            "sandbox_mode": "workspace-write",
            "runner_arguments": ["-C", str(self.project)],
        }

    def run(self, *args: str) -> tuple[int, dict]:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        completed = subprocess.run([sys.executable, "-B", str(SCRIPT), *args], cwd=self.project, capture_output=True, text=True, encoding="utf-8", check=False, env=env)
        self.assert_output(completed)
        return completed.returncode, json.loads(completed.stdout)

    @staticmethod
    def assert_output(completed: subprocess.CompletedProcess[str]) -> None:
        if not completed.stdout.strip():
            raise AssertionError(completed.stderr)

    def prepare(self) -> tuple[int, dict]:
        return self.run("access-prepare", "--project", str(self.project), "--ticket", self.ticket_rel, "--worker-topology", str(self.worker), "--publisher-topology", str(self.publisher), "--consumer-topology", str(self.consumer), "--expected-consumer-principal", self.consumer_principal, "--receipt", self.receipt_rel, "--ttl-seconds", "300")

    def readback(self) -> tuple[int, dict]:
        return self.run("validate-readback", "--project", str(self.project), "--receipt", self.receipt_rel, "--publisher-topology", str(self.publisher))

    def consumer_readback(self) -> tuple[int, dict]:
        return self.run("validate-consumer", "--project", str(self.project), "--receipt", self.receipt_rel, "--consumer-topology", str(self.consumer))


class ExecutionTopologyTests(unittest.TestCase):
    def test_round_trip_success(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fx = Fixture(Path(raw))
            code, prepared = fx.prepare()
            self.assertEqual(0, code)
            self.assertTrue(prepared["data"]["ready"])
            code, ready = fx.readback()
            self.assertEqual(0, code)
            self.assertFalse(ready["data"]["ready"])
            receipt = json.loads((fx.project / fx.receipt_rel).read_text(encoding="utf-8"))
            self.assertEqual("publisher_ready_for_consumer", receipt["status"])
            code, ready = fx.consumer_readback()
            self.assertEqual(0, code)
            receipt = json.loads((fx.project / fx.receipt_rel).read_text(encoding="utf-8"))
            self.assertEqual("ready_for_attempt_start", receipt["status"])
            self.assertTrue(receipt["readback_observation"]["independent_reopen"])
            self.assertTrue(receipt["consumer_observation"]["independent_recursive_reopen"])
            self.assertEqual(fx.consumer_principal, receipt["consumer_observation"]["principal"])
            self.assertFalse(any((fx.project / fx.staging_rel).glob(".topology-probe-*")))
            self.assertFalse(any(fx.project.glob(".math-research-consumer-probe-*")))
            self.assertEqual(sha(fx.project / fx.receipt_rel), ready["data"]["receipt_sha256"])

    def test_missing_worker_input_fails_before_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fx = Fixture(Path(raw))
            fx.input.unlink()
            code, payload = fx.prepare()
            self.assertEqual(2, code)
            self.assertEqual("worker_input_unreadable", payload["error"]["code"])
            self.assertFalse((fx.project / fx.receipt_rel).exists())

    def test_staging_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fx = Fixture(Path(raw))
            fx.ticket["writable_staging_path"] = "../outside"
            write_json(fx.project / fx.ticket_rel, fx.ticket)
            code, payload = fx.prepare()
            self.assertEqual(2, code)
            self.assertEqual("worker_staging_escape", payload["error"]["code"])

    def test_publisher_detects_probe_change(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fx = Fixture(Path(raw))
            self.assertEqual(0, fx.prepare()[0])
            receipt = json.loads((fx.project / fx.receipt_rel).read_text(encoding="utf-8"))
            (fx.project / receipt["probe_relative_path"]).write_text("changed\n", encoding="utf-8")
            code, payload = fx.readback()
            self.assertEqual(2, code)
            self.assertEqual("host_or_ingest_readback_unavailable", payload["error"]["code"])

    def test_topology_change_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fx = Fixture(Path(raw))
            self.assertEqual(0, fx.prepare()[0])
            changed = fx.descriptor("publisher", "different-runner")
            write_json(fx.publisher, changed)
            code, payload = fx.readback()
            self.assertEqual(2, code)
            self.assertEqual("topology_changed", payload["error"]["code"])

    def test_missing_publisher_probe_blocks_consumer_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fx = Fixture(Path(raw))
            self.assertEqual(0, fx.prepare()[0])
            self.assertEqual(0, fx.readback()[0])
            receipt = json.loads((fx.project / fx.receipt_rel).read_text(encoding="utf-8"))
            (fx.project / receipt["publisher_probe_relative_path"]).unlink()
            code, payload = fx.consumer_readback()
            self.assertEqual(2, code)
            self.assertEqual("consumer_readback_unavailable", payload["error"]["code"])

    def test_wrong_consumer_principal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fx = Fixture(Path(raw))
            fx.consumer_principal = "synthetic\\not-the-current-principal"
            self.assertEqual(0, fx.prepare()[0])
            self.assertEqual(0, fx.readback()[0])
            code, payload = fx.consumer_readback()
            self.assertEqual(2, code)
            self.assertEqual("consumer_principal_mismatch", payload["error"]["code"])

    def test_post_publication_consumer_validation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fx = Fixture(Path(raw))
            head_sha = sha(fx.project / "project.json")
            code, payload = fx.run("validate-project-consumer", "--project", str(fx.project), "--consumer-topology", str(fx.consumer), "--expected-consumer-principal", fx.consumer_principal, "--expected-project-head-sha256", head_sha)
            self.assertEqual(0, code)
            self.assertTrue(payload["data"]["readable"])
            code, payload = fx.run("validate-project-consumer", "--project", str(fx.project), "--consumer-topology", str(fx.consumer), "--expected-consumer-principal", fx.consumer_principal, "--expected-project-head-sha256", "0" * 64)
            self.assertEqual(2, code)
            self.assertEqual("consumer_head_mismatch", payload["error"]["code"])

    def test_go_requires_committed_generation_and_receipt_reference(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fx = Fixture(Path(raw))
            self.assertEqual(0, fx.prepare()[0])
            code, ready = fx.readback()
            self.assertEqual(0, code)
            code, ready = fx.consumer_readback()
            self.assertEqual(0, code)
            receipt_sha = ready["data"]["receipt_sha256"]
            state = {
                "current_ticket": {"id": "ticket-1", "lifecycle": "active"},
                "typed_references": [{"kind": "execution_topology_receipt", "path": fx.receipt_rel, "sha256": receipt_sha, "attempt_id": "attempt-1", "ticket_id": "ticket-1"}],
            }
            state_sha = write_json(fx.project / "state/g2.json", state)
            write_json(fx.project / "project.json", {"schema": "math-research-project/v10", "project_id": "synthetic-project", "control_generation": 2, "state": {"path": "state/g2.json", "sha256": state_sha}})
            code, payload = fx.run("go-check", "--project", str(fx.project), "--receipt", fx.receipt_rel, "--expected-receipt-sha256", receipt_sha)
            self.assertEqual(0, code)
            self.assertTrue(payload["data"]["go"])


if __name__ == "__main__":
    unittest.main()
