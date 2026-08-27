#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from MathResearchLegacyV1CompatMigration import CompatibilityMigrationError, invoke, read_receipt, sha256_file
from math_research_control_primitives import read_signed_json, write_signed_json


class LegacyCompatibilityMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.old = os.environ.get("MATH_RESEARCH_CONTROL_HOME")
        os.environ["MATH_RESEARCH_CONTROL_HOME"] = str(self.root / "control")
        self.run = self.root / "run"; self.run.mkdir()
        self.paths = {}
        for name in ("launcher_entry", "launcher_module", "cycle_module", "cycle_cli", "project_module", "canary_host", "canary_entry"):
            path = self.root / f"target-{name}.bin"; path.write_bytes(f"target:{name}".encode()); self.paths[name] = path
        self.sources = {}
        for name in ("launcher_entry", "launcher_module", "cycle_module", "cycle_cli", "project_module"):
            path = self.root / f"source-{name}.bin"; path.write_bytes(f"source:{name}".encode()); self.sources[name] = path
        self.checkpoint = {
            "head_sequence": 0, "head_payload_sha256": "c" * 64, "attempt_count": 0,
            "audit_count": 0, "total_round_count": 0, "attempts_since_last_audit": 0, "audit_due": False,
        }
        self.manifest = {
            "schema_version": 1, "run_id": "run-1", "revision": 3,
            "created_at_utc": "2026-01-01T00:00:00Z", "updated_at_utc": "2026-01-01T00:00:01Z",
            "prompt_version": "v6", "contract_version": "v1", "run_directory": str(self.run),
            "status": "failed", "exit_reason": "fixture", "thread_id": "thread-1",
            "project": {"project_id": "project-1", "directory": str(self.root)},
            "config": {"approval_policy": "never"}, "goal": {"objective_sha256": "b" * 64},
            "cycle_ledger": {"contract_binding_sha256": "a" * 64, "checkpoint": self.checkpoint,
                             "module": self.binding(self.sources["cycle_module"]), "cli": self.binding(self.sources["cycle_cli"]),
                             "project_module": self.binding(self.sources["project_module"])},
            "process": None,
        }
        self.manifest_path = self.run / "run.json"
        write_signed_json(self.manifest_path, self.manifest, create_key=True)
        shutil.copy2(self.manifest_path, Path(f"{self.manifest_path}.bak"))
        self.receipt = self.make_receipt()
        self.receipt_path = self.root / "receipt.json"; self.write_receipt(self.receipt_path, self.receipt)

    def tearDown(self) -> None:
        if self.old is None: os.environ.pop("MATH_RESEARCH_CONTROL_HOME", None)
        else: os.environ["MATH_RESEARCH_CONTROL_HOME"] = self.old
        self.temp.cleanup()

    @staticmethod
    def binding(path: Path) -> dict[str, str]:
        return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    @staticmethod
    def write_receipt(path: Path, value: dict) -> None:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def make_receipt(self) -> dict:
        return {
            "schema_version": 1, "protocol": "math-research-legacy-v1-compat-migration/v1",
            "migration_id": "fixture-migration", "action": "resume_prompt_v6_with_compat_bundle",
            "archive_directory_name": "compat-migration-v1",
            "project": {"project_id": "project-1", "directory": str(self.root)},
            "run": {"id": "run-1", "directory": str(self.run), "thread_id": "thread-1"},
            "contract": {"version": "v1", "binding_sha256": "a" * 64},
            "goal": {"objective_sha256": "b" * 64},
            "source": {
                "status": "failed", "manifest_primary_sha256": sha256_file(self.manifest_path),
                "manifest_backup_sha256": sha256_file(Path(f"{self.manifest_path}.bak")),
                **{name: self.binding(path) for name, path in self.sources.items()}, "counters": self.checkpoint,
            },
            "target": {name: self.binding(path) for name, path in self.paths.items()},
            "authorization": {"approval_mode_from": "never", "approval_mode_to": "approve_for_me",
                              "objective_changed": False, "quantifiers_changed": False, "counters_reset": False},
        }

    def test_analyze_apply_verify_and_archive(self) -> None:
        self.assertEqual("ready_to_apply", invoke("Analyze", self.run, self.receipt_path, self.paths)["Status"])
        self.assertEqual("applied", invoke("Apply", self.run, self.receipt_path, self.paths)["Status"])
        self.assertEqual("already_applied", invoke("Verify", self.run, self.receipt_path, self.paths)["Status"])
        manifest = read_signed_json(self.manifest_path)["payload"]
        self.assertEqual("approve_for_me", manifest["config"]["approval_mode"])
        self.assertEqual(self.checkpoint, manifest["cycle_ledger"]["checkpoint"])
        archive = self.run / "compat-migration-v1"
        self.assertEqual(sha256_file(self.receipt_path), sha256_file(archive / "migration-receipt.json"))

    def test_verify_before_apply_is_blocked(self) -> None:
        with self.assertRaises(CompatibilityMigrationError): invoke("Verify", self.run, self.receipt_path, self.paths)

    def test_target_hash_mismatch_is_blocked_without_write(self) -> None:
        before = sha256_file(self.manifest_path); bad = copy.deepcopy(self.receipt)
        bad["target"]["cycle_cli"]["sha256"] = "0" * 64
        path = self.root / "bad.json"; self.write_receipt(path, bad)
        with self.assertRaises(CompatibilityMigrationError): invoke("Analyze", self.run, path, self.paths)
        self.assertEqual(before, sha256_file(self.manifest_path))

    def test_duplicate_receipt_property_is_blocked(self) -> None:
        path = self.root / "duplicate.json"; path.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
        with self.assertRaises(CompatibilityMigrationError): read_receipt(path)

    def test_counter_rollback_after_apply_is_blocked(self) -> None:
        invoke("Apply", self.run, self.receipt_path, self.paths)
        manifest = read_signed_json(self.manifest_path)["payload"]
        manifest["cycle_ledger"]["checkpoint"]["head_sequence"] = -1
        write_signed_json(self.manifest_path, manifest)
        with self.assertRaises(CompatibilityMigrationError): invoke("Verify", self.run, self.receipt_path, self.paths)


if __name__ == "__main__": unittest.main()
