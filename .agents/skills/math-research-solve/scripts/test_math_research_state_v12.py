#!/usr/bin/env python3
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("math_research_state_v12.py")
SPEC = importlib.util.spec_from_file_location("mrs12", MODULE)
m = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(m)


def objective(pid):
    return {
        "schema": m.OBJECTIVE_SCHEMA,
        "project_id": pid,
        "statement": "Prove or disprove P.",
        "domain": "Integers",
        "quantifier_order": "For every n there exists m.",
        "assumptions": [],
        "evidence_standard": "Exact proof, independent verification, terminal audit.",
        "completion_standard": "P is settled under all frozen quantifiers.",
        "created_at_utc": "2026-08-14T00:00:00Z",
    }


def memory(mid="fact", cls="verified_fact", trust="promoted"):
    exclusion = cls in m.FAILURE_CLASSES or cls == "bounded_negative"
    return {
        "memory_id": mid,
        "classification": cls,
        "statement": "Scoped statement.",
        "scope": "Exactly n=1.",
        "origin": {"kind": "legacy_project_import", "source_id": "old"},
        "trust_state": trust,
        "evidence": ([{"role": "verifier", "locator": "legacy/report.json", "sha256": "1" * 64, "verifier_verdict": "PASS"}] if exclusion else []),
        "permits": ["Use the scoped statement."],
        "does_not_imply": ["No claim outside the scope."],
        "reopen_condition": "Reopen with stronger evidence.",
        "tool_requirements": [],
        "exclusion_authorized": exclusion,
        "exclusion_scope": "Exactly n=1." if exclusion else None,
        "created_at_utc": "2026-08-14T00:00:00Z",
    }


def project_spec(pid, source):
    return {
        "project_id": pid,
        "display_name": pid,
        "objective": objective(pid),
        "sources": [{"source_id": "old", "path": str(source)}],
        "memory_items": [memory()],
        "route_review": {"review_number": 1, "new_math_performed": False, "ranked_routes": []},
        "counters": {"internal_attempts_started": 2, "internal_attempts_completed": 2, "terminal_audits": 0, "route_reviews": 1, "attempts_since_route_review": 0, "route_review_due": False},
        "project_complete": False,
        "terminal_evidence": [],
        "legacy_resume_capsules": [],
        "intakes": [],
    }


class V12Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "old"
        self.source.mkdir()
        (self.source / "a.txt").write_bytes(b"same")
        (self.source / "b.txt").write_bytes(b"same")

    def tearDown(self):
        self.temp.cleanup()

    def build(self, pid="p"):
        target = self.root / (pid + "-v12")
        m.build_project(target, project_spec(pid, self.source), "2026-08-14T00:00:00Z")
        return target

    def assert_code(self, code, fn, *args, **kwargs):
        with self.assertRaises(m.ResearchError) as cm:
            fn(*args, **kwargs)
        self.assertEqual(cm.exception.code, code)

    def test_layout_startup_dedupe_restore_and_views(self):
        project = self.build()
        result = m.startup(project, full=True)
        self.assertEqual(result["classification"], "v12_ready")
        self.assertEqual({p.name for p in project.iterdir()}, m.ROOT_ENTRIES)
        objects = [p for p in (project / ".research/objects/sha256").rglob("*") if p.is_file()]
        self.assertEqual(len(objects), 1)
        restored = self.root / "restored"
        m.restore_tree(project, "old", restored)
        self.assertEqual((restored / "a.txt").read_bytes(), b"same")
        (project / "当前状态.md").write_text("drift", encoding="utf-8")
        self.assertEqual(m.startup(project, full=True)["classification"], "v12_view_drift")
        self.assert_code("goal_gate", m.repair_views, project, "none")
        m.repair_views(project, "active")
        self.assertEqual(m.startup(project, full=True)["classification"], "v12_ready")

    def test_failure_taxonomy_fail_closed(self):
        pid = "p"
        obj_sha = "2" * 64
        raw = memory("o", "unresolved_obstacle", "recorded")
        raw.update({"schema": m.MEMORY_ITEM_SCHEMA, "project_id": pid, "project_objective_sha256": obj_sha})
        raw["exclusion_authorized"] = True
        raw["exclusion_scope"] = "all n"
        self.assert_code("memory_scope_invalid", m.validate_memory_item, raw, pid, obj_sha)
        raw = memory("f", "verified_refutation", "promoted")
        raw.update({"schema": m.MEMORY_ITEM_SCHEMA, "project_id": pid, "project_objective_sha256": obj_sha})
        raw["evidence"][0]["verifier_verdict"] = "INCONCLUSIVE"
        self.assert_code("verification_required", m.validate_memory_item, raw, pid, obj_sha)

    def test_goal_objective_and_three_attempt_gate(self):
        project = self.build()
        head = m.load_json(project / "project.json")
        state = m.load_json(m.ptr(project, head["state"], "state"))
        self.assert_code("objective_changed", m.simulate_transition, state, "TASK_START", {"task_id": "t", "task_kind": "research", "project_objective_sha256": "0" * 64})
        state = m.simulate_transition(state, "TASK_START", {"task_id": "t", "task_kind": "research", "project_objective_sha256": head["project_objective"]["sha256"]})
        state = m.simulate_transition(state, "RUN_START", {"run_id": "r"})
        for i in range(3):
            state = m.simulate_transition(state, "ATTEMPT_START", {"attempt_id": f"a{i}"})
            state = m.simulate_transition(state, "ATTEMPT_END", {})
        self.assertTrue(state["counters"]["route_review_due"])
        self.assert_code("route_review_required", m.simulate_transition, state, "ATTEMPT_START", {"attempt_id": "a4"})
        state = m.simulate_transition(state, "ROUTE_REVIEW_COMPLETE", {"new_math_performed": False})
        state = m.simulate_transition(state, "ATTEMPT_START", {"attempt_id": "a4"})
        self.assertEqual(state["current_attempt"], "a4")

    def test_exports(self):
        project = self.build()
        self.assert_code("project_not_complete", m.export_project, project, "final", self.root / "final")
        m.export_project(project, "intermediate", self.root / "intermediate")
        m.export_project(project, "full-private", self.root / "private")
        self.assertTrue((self.root / "private/project/.research/state/objective.json").is_file())

    def test_batch_prepare_and_goal_gate(self):
        spec = project_spec("p", self.source)
        spec.update({
            "current_root": str(self.source),
            "target_root": str(self.root / "new"),
            "expected_current_tree_sha256": m.tree_hash(m.tree_inventory(self.source)),
        })
        batch = {"schema": "math-research-batch-migration-spec/v12", "projects": [spec], "created_at_utc": "2026-08-14T00:00:00Z"}
        batch_path = self.root / "batch.json"
        m.write_json(batch_path, batch)
        prepared = m.prepare_batch(batch_path, self.root / "stage")
        self.assert_code("goal_gate", m.commit_batch, Path(prepared["plan_path"]), prepared["plan_sha256"], "none")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink unavailable")
    def test_link_rejected(self):
        target = self.root / "target.txt"
        target.write_text("x")
        link = self.source / "link.txt"
        try:
            os.symlink(target, link)
        except OSError:
            self.skipTest("symlink privilege unavailable")
        self.assert_code("reparse_point_rejected", m.tree_inventory, self.source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
