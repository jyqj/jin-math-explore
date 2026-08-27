#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from attempt_package_preflight_v13 import finalize_package, validate_package_directory
from v13_common import V13Error, canonical_json, load_json, sha256_bytes


class AttemptPackagePreflightTests(unittest.TestCase):
    def make_source(self, root: Path) -> Path:
        source = root / "raw"
        source.mkdir()
        result_raw = b'{  "value" : 7 }\n'
        (source / "result.json").write_bytes(result_raw)
        record = {
            "schema": "synthetic-computation-record/v1",
            "result": {"path": "result.json", "sha256": "0" * 64, "bytes": 1},
        }
        (source / "computation-record.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        (source / "outcome.md").write_text("Synthetic result package.\n", encoding="utf-8")
        return source

    def finalize(self, root: Path) -> tuple[Path, dict]:
        source = self.make_source(root)
        staging = root / "final"
        result = finalize_package(
            source, staging, attempt_id="attempt-synthetic",
            package_root=".research/objects/attempt-synthetic",
            candidate_path="computation-record.json",
            dependency_paths=["result.json"],
        )
        return staging, result

    def test_finalizer_canonicalizes_and_rebinds(self):
        with tempfile.TemporaryDirectory() as td:
            staging, result = self.finalize(Path(td))
            self.assertTrue(result["ok"])
            record = load_json(staging / "computation-record.json", canonical_required=True)
            result_raw = (staging / "result.json").read_bytes()
            self.assertEqual(record["result"]["sha256"], sha256_bytes(result_raw))
            self.assertEqual(record["result"]["bytes"], len(result_raw))
            checked = validate_package_directory(staging)
            self.assertEqual(checked["status"], "PASS")

    def test_stale_markdown_hash_is_blocked_before_freeze(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = self.make_source(root)
            (source / "outcome.md").write_text("Stale digest: " + "0" * 64 + "\n", encoding="utf-8")
            with self.assertRaisesRegex(V13Error, "Markdown contains a SHA-256"):
                finalize_package(source, root / "final", attempt_id="attempt-synthetic", package_root=".research/objects/attempt-synthetic", candidate_path="computation-record.json")

    def test_hash_cycle_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "raw"; source.mkdir()
            (source / "a.json").write_bytes(canonical_json({"next": {"path": "b.json", "sha256": "0" * 64}}))
            (source / "b.json").write_bytes(canonical_json({"next": {"path": "a.json", "sha256": "0" * 64}}))
            with self.assertRaisesRegex(V13Error, "acyclic"):
                finalize_package(source, root / "final", attempt_id="attempt-synthetic", package_root=".research/objects/attempt-synthetic", candidate_path="a.json")

    def test_post_receipt_mutation_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            staging, _ = self.finalize(Path(td))
            (staging / "result.json").write_bytes(canonical_json({"value": 8}))
            with self.assertRaisesRegex(V13Error, "inventory changed"):
                validate_package_directory(staging)

    def test_manifest_omission_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            staging, _ = self.finalize(Path(td))
            manifest = load_json(staging / "artifact-manifest.json", canonical_required=True)
            manifest["artifacts"] = manifest["artifacts"][:-1]
            manifest["artifact_count"] -= 1
            (staging / "artifact-manifest.json").write_bytes(canonical_json(manifest))
            with self.assertRaises(V13Error):
                validate_package_directory(staging)


if __name__ == "__main__":
    unittest.main()
