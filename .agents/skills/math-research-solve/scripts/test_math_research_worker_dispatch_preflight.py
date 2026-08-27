from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("math_research_worker_dispatch_preflight.py")


class WorkerDispatchPreflightTests(unittest.TestCase):
    def run_preflight(self, *args: str) -> tuple[int, dict]:
        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), *args],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertTrue(completed.stdout.strip(), completed.stderr)
        return completed.returncode, json.loads(completed.stdout)

    def test_collaboration_accepts_project_inside_host_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            host = Path(raw) / "host"
            project = host / "project"
            code, payload = self.run_preflight(
                "--project", str(project),
                "--ticket", "runs/run-1/tickets/t1.json",
                "--host-workspace-root", str(host),
                "--transport", "collaboration",
            )
            self.assertEqual(0, code)
            self.assertTrue(payload["ok"])
            self.assertEqual("host_workspace_shared", payload["data"]["classification"])

    def test_collaboration_rejects_external_project(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            code, payload = self.run_preflight(
                "--project", str(root / "external" / "project"),
                "--ticket", "runs/run-1/tickets/t1.json",
                "--host-workspace-root", str(root / "host"),
                "--transport", "collaboration",
            )
            self.assertEqual(2, code)
            self.assertEqual("worker_workspace_mismatch", payload["error"]["code"])

    def test_project_root_exec_accepts_exact_external_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project = root / "external" / "project"
            code, payload = self.run_preflight(
                "--project", str(project),
                "--ticket", "runs/run-1/tickets/t1.json",
                "--host-workspace-root", str(root / "host"),
                "--transport", "project-root-exec",
                "--execution-workspace-root", str(project),
            )
            self.assertEqual(0, code)
            self.assertEqual("project_root_rebind_required", payload["data"]["classification"])
            self.assertEqual("goal_host_parent", payload["data"]["approval_owner"])

    def test_project_root_exec_rejects_staging_only_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project = root / "external" / "project"
            code, payload = self.run_preflight(
                "--project", str(project),
                "--ticket", "runs/run-1/tickets/t1.json",
                "--host-workspace-root", str(root / "host"),
                "--transport", "project-root-exec",
                "--execution-workspace-root", str(project / "runs" / "run-1" / "staging" / "t1"),
            )
            self.assertEqual(2, code)
            self.assertEqual("execution_workspace_mismatch", payload["error"]["code"])

    def test_ticket_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            project = root / "host" / "project"
            code, payload = self.run_preflight(
                "--project", str(project),
                "--ticket", str(root / "other" / "ticket.json"),
                "--host-workspace-root", str(root / "host"),
                "--transport", "collaboration",
            )
            self.assertEqual(2, code)
            self.assertEqual("ticket_path_escape", payload["error"]["code"])


if __name__ == "__main__":
    unittest.main()
