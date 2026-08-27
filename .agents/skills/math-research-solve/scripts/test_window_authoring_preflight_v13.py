#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("window_authoring_preflight_v13.py")


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def document_sha(value: object) -> str:
    import hashlib
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class WindowAuthoringPreflightTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, dict]:
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), *args], capture_output=True, text=True, encoding="utf-8")
        return result.returncode, json.loads(result.stdout)

    def test_review_digest_distinguishes_document_and_raw_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            packet = {"z": 1, "a": {"y": 2, "b": 3}}
            (root / "packet.json").write_bytes(canonical(packet))
            ticket = {"packet_sha256": document_sha(packet), "schema": "fixture-ticket/v1"}
            (root / "ticket.json").write_bytes(canonical(ticket))
            code, result = self.run_cli("review-digests", "--packet", str(root / "packet.json"), "--ticket", str(root / "ticket.json"))
            self.assertEqual(0, code)
            self.assertFalse(result["raw_equals_document"])
            ticket["packet_sha256"] = "0" * 64
            (root / "ticket.json").write_bytes(canonical(ticket))
            code, result = self.run_cli("review-digests", "--packet", str(root / "packet.json"), "--ticket", str(root / "ticket.json"))
            self.assertEqual(2, code)
            self.assertEqual("packet_document_digest_mismatch", result["error"]["code"])

    def test_output_scope_accepts_workspace_and_blocks_project_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            project = root / "project"
            workspace.mkdir()
            project.mkdir()
            code, _ = self.run_cli("output-scope", "--workspace-root", str(workspace), "--project-root", str(project), "--output-root", str(workspace / "worker"))
            self.assertEqual(0, code)
            code, result = self.run_cli("output-scope", "--workspace-root", str(root), "--project-root", str(project), "--output-root", str(project / "work"))
            self.assertEqual(2, code)
            self.assertEqual("output_inside_project", result["error"]["code"])

    def test_tree_uses_artifact_class_budget_and_blocks_cr(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            closure = {"schema": "math-research-map-review-closure/v1", "payload": "x" * 700}
            (root / "closure.json").write_bytes(canonical(closure))
            code, result = self.run_cli("authoring-tree", "--root", str(root), "--ordinary-max-bytes", "500", "--closure-max-bytes", "2000", "--tree-max-bytes", "3000")
            self.assertEqual(0, code)
            self.assertEqual(1, result["closure_count"])
            (root / "bad.txt").write_bytes(b"a\r\n")
            code, result = self.run_cli("authoring-tree", "--root", str(root), "--ordinary-max-bytes", "500", "--closure-max-bytes", "2000", "--tree-max-bytes", "3000")
            self.assertEqual(2, code)
            self.assertEqual("tree_cr_forbidden", result["error"]["code"])

    def test_close_manifests_separate_planning_and_commit_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            md = {"target": "map/main.md", "source": "stage/main.md", "immutable": False, "expected_old_sha256": "1" * 64}
            control = {"target": "map/control.json", "source": "stage/control.json", "immutable": False, "expected_old_sha256": "2" * 64}
            planning = {"schema": "local-v13-artifact-manifest/v1", "writes": [md]}
            commit = {"schema": "local-v13-artifact-manifest/v1", "writes": [md, control]}
            (root / "planning.json").write_bytes(canonical(planning))
            (root / "commit.json").write_bytes(canonical(commit))
            code, result = self.run_cli("window-close-manifests", "--planning-manifest", str(root / "planning.json"), "--commit-manifest", str(root / "commit.json"))
            self.assertEqual(0, code)
            self.assertTrue(result["planning_is_strict_subset"])
            planning["writes"].append(control)
            (root / "planning.json").write_bytes(canonical(planning))
            code, result = self.run_cli("window-close-manifests", "--planning-manifest", str(root / "planning.json"), "--commit-manifest", str(root / "commit.json"))
            self.assertEqual(2, code)
            self.assertEqual("planning_manifest_control_alias", result["error"]["code"])


if __name__ == "__main__":
    unittest.main()
