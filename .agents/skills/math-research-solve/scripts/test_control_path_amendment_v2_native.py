#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
from pathlib import Path

from MathResearchLegacyV1CompatMigration import invoke as invoke_prior, sha256_file
from MathResearchLegacyV1ControlPathAmendmentV2 import ControlPathAmendmentError, invoke
from math_research_control_primitives import read_signed_json
from test_legacy_v1_compat_migration_native import LegacyCompatibilityMigrationTests


class ControlPathAmendmentTests(LegacyCompatibilityMigrationTests):
    def control_fixture(self) -> tuple[dict[str, Path], Path]:
        invoke_prior("Apply", self.run, self.receipt_path, self.paths)
        paths = {
            "prior_launcher_entry": self.paths["launcher_entry"],
            "launcher_module": self.paths["launcher_module"],
            "prior_canary_host": self.paths["canary_host"],
            "canary_entry": self.paths["canary_entry"],
            "cycle_module": self.paths["cycle_module"],
            "cycle_cli": self.paths["cycle_cli"],
            "project_module": self.paths["project_module"],
        }
        for name in ("launcher_entry", "argv_compat_module", "canary_host", "canary_module", "amendment_module", "amendment_cli"):
            path = self.root / f"control-{name}.bin"; path.write_bytes(f"control:{name}".encode()); paths[name] = path
        manifest = read_signed_json(self.manifest_path)["payload"]
        receipt = {
            "schema_version": 1, "protocol": "math-research-legacy-v1-control-path-amendment/v2",
            "amendment_id": "fixture-control-path-v2", "action": "omit_explicit_sandbox_with_approve_for_me",
            "archive_directory_name": "compat-control-path-v2",
            "project": {"project_id": "project-1", "directory": str(self.root)},
            "run": {"id": "run-1", "directory": str(self.run), "thread_id": "thread-1"},
            "contract": {"version": "v1", "binding_sha256": "a" * 64},
            "goal": {"objective_sha256": "b" * 64},
            "prior_migration": {"receipt_sha256": sha256_file(self.receipt_path)},
            "source": {
                "status": manifest["status"], "manifest_primary_sha256": sha256_file(self.manifest_path),
                "manifest_backup_sha256": sha256_file(Path(f"{self.manifest_path}.bak")),
                "counters": manifest["cycle_ledger"]["checkpoint"],
            },
            "target": {
                name: self.binding(paths[name]) for name in (
                    "launcher_entry", "launcher_module", "argv_compat_module", "canary_host", "canary_module",
                    "canary_entry", "cycle_cli", "amendment_module", "amendment_cli"
                )
            },
            "authorization": {
                "approval_mode": "approve_for_me", "effective_sandbox": "workspace-write",
                "explicit_sandbox_argument_omitted": True, "objective_changed": False,
                "quantifiers_changed": False, "counters_reset": False, "permission_scope_expanded": False,
            },
        }
        path = self.root / "control-receipt.json"; self.write_receipt(path, receipt)
        return paths, path

    def test_control_analyze_apply_verify_preserves_authority(self) -> None:
        paths, receipt = self.control_fixture()
        before = read_signed_json(self.manifest_path)["payload"]
        self.assertEqual("ready_to_apply", invoke("Analyze", self.run, receipt, self.receipt_path, paths)["Status"])
        self.assertEqual("applied", invoke("Apply", self.run, receipt, self.receipt_path, paths)["Status"])
        self.assertEqual("already_applied", invoke("Verify", self.run, receipt, self.receipt_path, paths)["Status"])
        after = read_signed_json(self.manifest_path)["payload"]
        self.assertEqual(before["thread_id"], after["thread_id"])
        self.assertEqual(before["goal"], after["goal"])
        self.assertEqual(before["cycle_ledger"]["checkpoint"], after["cycle_ledger"]["checkpoint"])
        self.assertFalse(after["control_path_amendment_v2"]["permission_scope_expanded"])

    def test_control_target_tamper_is_blocked_without_write(self) -> None:
        paths, receipt_path = self.control_fixture(); before = sha256_file(self.manifest_path)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8")); receipt["target"]["argv_compat_module"]["sha256"] = "0" * 64
        bad = self.root / "bad-control.json"; self.write_receipt(bad, receipt)
        with self.assertRaises(ControlPathAmendmentError): invoke("Analyze", self.run, bad, self.receipt_path, paths)
        self.assertEqual(before, sha256_file(self.manifest_path))

    def test_control_verify_before_apply_is_blocked(self) -> None:
        paths, receipt = self.control_fixture()
        with self.assertRaises(ControlPathAmendmentError): invoke("Verify", self.run, receipt, self.receipt_path, paths)


if __name__ == "__main__":
    import unittest
    unittest.main()
