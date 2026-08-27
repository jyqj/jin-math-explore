#!/usr/bin/env python3
"""Synthetic v3 success and fail-closed tests."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("research_map_v3", Path(__file__).with_name("research_map_v3.py"))
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
sha_file = MODULE.sha_file
validate_v3 = MODULE.validate_v3
write_json = MODULE.write_json


def make_fixture(base: Path) -> tuple[Path, Path]:
    project = base / "project"
    map_root = base / "map"
    (project / ".research/state").mkdir(parents=True)
    (project / ".research/memory/items").mkdir(parents=True)
    (project / ".research/objects/sha256").mkdir(parents=True)
    objective = project / ".research/state/objective.json"
    objective.write_text('{"objective":"synthetic"}\n', encoding="utf-8")
    memory = project / ".research/memory/items/memory-a.json"
    write_json(memory, {"memory_id": "memory-a"})
    index = project / ".research/memory/index.json"
    write_json(index, {"items": [{"path": ".research/memory/items/memory-a.json", "sha256": sha_file(memory)}]})
    state = project / ".research/state/current.json"
    write_json(state, {"memory_index": {"path": ".research/memory/index.json", "sha256": sha_file(index)}})
    raw = b"synthetic verifier result\n"
    digest = hashlib.sha256(raw).hexdigest()
    obj = project / ".research/objects/sha256" / digest[:2] / digest
    obj.parent.mkdir(parents=True)
    obj.write_bytes(raw)
    manifest = project / ".research/state/manifest.json"
    entries = []
    for path in (project / ".research").rglob("*"):
        if path.is_file() and path != manifest:
            entries.append({"path": path.relative_to(project).as_posix(), "sha256": sha_file(path), "size": path.stat().st_size})
    write_json(manifest, {"entries": entries})
    head = {
        "schema": "math-research-project/v12",
        "project_id": "synthetic-project",
        "project_objective": {"path": ".research/state/objective.json", "sha256": sha_file(objective)},
        "state": {"path": ".research/state/current.json", "sha256": sha_file(state)},
        "archive_manifest": {"path": ".research/state/manifest.json", "sha256": sha_file(manifest)},
    }
    write_json(project / "project.json", head)

    map_root.mkdir()
    contract = map_root / "00-contract.md"
    main = map_root / "01-main.md"
    route = map_root / "20-route.md"
    contract.write_text("## Contract\n\nSynthetic objective binding and evidence boundary for this map.\n", encoding="utf-8")
    main.write_text("## Main map\n\nRead [[20-route]] for the only synthetic route and its evidence boundary.\n", encoding="utf-8")
    route.write_text("## Route\n\nThe synthetic object connects to the objective only through the cited verifier object. The remaining test is explicit.\n", encoding="utf-8")
    aid = "asset-synthetic"
    field = {"asset_status": "supported", "source_refs": [f"asset:{aid}"], "gap": ""}
    control = {
        "schema": "math-research-map/v3",
        "map_id": "synthetic-map",
        "map_version": 1,
        "project_id": "synthetic-project",
        "project_schema": "math-research-project/v12",
        "objective_sha256": sha_file(objective),
        "source_head_sha256": sha_file(project / "project.json"),
        "status": "review_required",
        "status_reason": "synthetic",
        "control_notes": {
            "contract": {"path": "00-contract.md", "sha256": sha_file(contract)},
            "main": {"path": "01-main.md", "sha256": sha_file(main)},
        },
        "asset_references": ".research/asset-references.json",
        "active_route_ids": ["route-a"],
        "nodes": [{
            "id": "route-a", "kind": "route", "state": "active", "note": "20-route.md",
            "note_sha256": sha_file(route), "sections": {}, "memory_ids": ["memory-a"],
            "evidence_sha256s": [], "project_record_refs": [], "required_asset_ids": [aid],
            "route_entry": {"heading": "Route", "fields": {name: copy.deepcopy(field) for name in (
                "mathematical_object", "objective_mechanism", "evidence_boundary", "missing_work", "success_failure_gate")}},
        }],
    }
    refs = {
        "schema": "math-research-map-asset-references/v2", "map_id": "synthetic-map",
        "source_head_sha256": control["source_head_sha256"], "asset_count": 1,
        "assets": [{"asset_id": aid, "display_name": "verifier.json", "object_sha256": digest,
                    "size": len(raw), "role": "verifier", "node_ids": ["route-a"], "source_locator": "synthetic"}],
        "memory_ids": ["memory-a"], "project_records": [],
    }
    write_json(map_root / ".research/research-map.json", control)
    write_json(map_root / ".research/asset-references.json", refs)
    write_json(map_root / ".research/validation-receipt.json", {
        "schema": "math-research-map-validation-receipt/v1", "map_id": "synthetic-map",
        "map_version": 1, "project_id": "synthetic-project", "source_head_sha256": control["source_head_sha256"],
        "validated_at_utc": "2026-01-01T00:00:00Z", "structural_validation": {"ok": True},
        "semantic_audit": {"status": "review_required"},
    })
    return map_root, project


class ResearchMapV3Tests(unittest.TestCase):
    def run_case(self, mutate, expected_code: str) -> None:
        with tempfile.TemporaryDirectory() as temp:
            map_root, project = make_fixture(Path(temp))
            mutate(map_root, project)
            result = validate_v3(map_root, project)
            self.assertFalse(result["ok"], result)
            self.assertIn(expected_code, {x["code"] for x in result["issues"]})

    def test_success(self):
        with tempfile.TemporaryDirectory() as temp:
            map_root, project = make_fixture(Path(temp))
            self.assertTrue(validate_v3(map_root, project)["ok"])

    def test_non_markdown_link(self):
        self.run_case(lambda m, p: (m / "01-main.md").write_text("## Main\n\n[raw](x.json)\n", encoding="utf-8"), "non_markdown_local_link")

    def test_blank_note(self):
        self.run_case(lambda m, p: (m / "20-route.md").write_text("", encoding="utf-8"), "blank_markdown")

    def test_map_local_raw_asset(self):
        self.run_case(lambda m, p: (m / "data.json").write_text("{}", encoding="utf-8"), "raw_asset_in_map")

    def test_missing_project_object(self):
        def mutate(m, p):
            refs = json.loads((m / ".research/asset-references.json").read_text(encoding="utf-8"))
            digest = refs["assets"][0]["object_sha256"]
            (p / ".research/objects/sha256" / digest[:2] / digest).unlink()
        self.run_case(mutate, "project_object_missing")

    def test_tampered_object(self):
        def mutate(m, p):
            refs = json.loads((m / ".research/asset-references.json").read_text(encoding="utf-8"))
            digest = refs["assets"][0]["object_sha256"]
            (p / ".research/objects/sha256" / digest[:2] / digest).write_bytes(b"tampered")
        self.run_case(mutate, "project_object_hash_mismatch")

    def test_stale_head(self):
        self.run_case(lambda m, p: (p / "project.json").write_bytes((p / "project.json").read_bytes() + b" "), "source_head_stale")

    def test_unsupported_route_expansion(self):
        def mutate(m, p):
            control = json.loads((m / ".research/research-map.json").read_text(encoding="utf-8"))
            control["nodes"][0]["route_entry"]["fields"]["objective_mechanism"]["source_refs"] = ["asset:invented"]
            write_json(m / ".research/research-map.json", control)
        self.run_case(mutate, "route_source_unresolved")

    def test_current_without_semantic_pass(self):
        def mutate(m, p):
            control = json.loads((m / ".research/research-map.json").read_text(encoding="utf-8"))
            control["status"] = "current"
            write_json(m / ".research/research-map.json", control)
        self.run_case(mutate, "current_without_semantic_pass")


if __name__ == "__main__":
    unittest.main()
