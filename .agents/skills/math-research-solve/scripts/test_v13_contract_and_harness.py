from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import math_research_commit_v13 as commit_harness
from attempt_package_preflight_v13 import finalize_package
from math_research_commit_v13 import commit, validate_plan
from math_research_migrate_v12_to_v13 import MigrationError, invoke_adapter
from math_research_state_v13 import AUDIT_KINDS, prepare_transition, validate_project
from map_semantic_review_v1 import build_test_closure
from v13_common import V13Error, canonical_json, inventory, load_json_bytes, objective_bytes, sha256_bytes, sha256_file

SCRIPTS = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPTS.parent
H = "a" * 64


def objective():
    return {"statement": "证明参数 μ 满足目标性质 T。", "domain": "D", "quantifier_order": "Q", "assumptions": ["A", "B"], "evidence_standard": "E", "completion_standard": "C"}


def pointer(path: str, root: Path):
    return {"path": path, "sha256": sha256_file(root / path)}


def preflight_ref(attempt_id: str):
    return {"path": f".research/staging/{attempt_id}/attempt-package-preflight.json", "sha256": "f" * 64}


def counters():
    return {"attempts_since_route_review": 0, "internal_attempts_completed": 0, "internal_attempts_started": 0, "route_review_due": False, "route_reviews": 0, "terminal_audits": 0}


def execution_head():
    return {"schema": "math-research-execution-head/v13", "generation": 1, "phase": "window_idle", "migrated_project": False, "window_source_binding": None, "active_window": None, "queue": [], "active_attempts": [], "route_decisions": [], "route_portfolio": None, "cognition": None, "capsules": [], "verification_queue": [], "review_required": [], "counters": counters(), "legacy_unfinished_work": [], "source_invalidations": [], "terminal_audits": [], "repair_count": 0, "last_transition": "GENESIS"}


def make_project(root: Path, *, legacy_review: bool = False) -> None:
    for rel in ("研究地图/.research", "研究地图/桥梁", ".research/identity", ".research/heads", ".research/authority", ".research/memory/items", ".research/migration"):
        (root / rel).mkdir(parents=True, exist_ok=True)
    (root / "README.md").write_text("# test\n", encoding="utf-8", newline="\n")
    raw = objective_bytes(objective()); (root / ".research/identity/objective-core.json").write_bytes(raw); commitment = sha256_bytes(raw)
    manifest = {"schema": "math-research-authority-manifest/v13", "objective_commitment_sha256": commitment}
    (root / ".research/authority/candidate-manifest.json").write_bytes(canonical_json(manifest)); manifest_sha = sha256_file(root / ".research/authority/candidate-manifest.json")
    memory = {"schema": "math-research-memory-item/v2", "memory_id": "m", "method_overview": {"method_family": "f"}, "method_spine": "specific spine", "reusable_structures": ["r"], "cannot_imply": ["x"], "evidence_refs": ["e"]}
    (root / ".research/memory/items/m.json").write_bytes(canonical_json(memory))
    review = {"schema": "math-research-route-review/v2", "review_id": "review-1", "new_math_performed": False, "routes": [{"route_id": "r"}]}
    (root / ".research/memory/route-review-v2.json").write_bytes(canonical_json(review))
    map_control = {"schema": "math-research-map/v1", "project_id": "p", "project_objective_sha256": commitment, "authority_manifest_sha256": manifest_sha, "status": "current", "routes": [{"route_id": "r", "evidence_refs": ["route-review:review-1"]}]}
    (root / "研究地图/.research/research-map.json").write_bytes(canonical_json(map_control))
    assets = {"schema": "math-research-map-asset-references/v3", "objective_commitment_sha256": commitment, "authority_manifest_sha256": manifest_sha, "asset_count": 0, "assets": [], "memory_ids": ["m"], "project_records": [".research/authority/candidate-manifest.json", ".research/memory/route-review-v2.json"]}
    (root / "研究地图/.research/asset-references.json").write_bytes(canonical_json(assets))
    (root / ".research/migration/review.json").write_bytes(canonical_json({"verdict": "PASS"}))
    (root / "研究地图/.research/validation-receipt.json").write_bytes(canonical_json({"schema": "math-research-map-validation/v13", "status": "PASS", "semantic_review": "PASS"}))
    authority = {"schema": "math-research-authority-head/v13", "generation": 1, "candidate_manifest": pointer(".research/authority/candidate-manifest.json", root), "memory_index": {"items": [{"path": ".research/memory/items/m.json", "sha256": sha256_file(root / ".research/memory/items/m.json"), "memory_id": "m"}]}, "route_review": pointer(".research/memory/route-review-v2.json", root), "research_map": pointer("研究地图/.research/research-map.json", root), "map_validation_receipt": pointer("研究地图/.research/validation-receipt.json", root), "independent_semantic_review": pointer(".research/migration/review.json", root)}
    (root / ".research/heads/research.json").write_bytes(canonical_json(authority))
    (root / ".research/heads/execution.json").write_bytes(canonical_json(execution_head()))
    project = {"schema": "math-research-project/v13", "project_id": "p", "created_at_utc": "2026-01-01T00:00:00Z", "objective": pointer(".research/identity/objective-core.json", root), "objective_commitment_sha256": commitment, "research_authority_head": pointer(".research/heads/research.json", root), "execution_state_head": pointer(".research/heads/execution.json", root), "generation": 1, "project_complete": False, "pending_goal_update": False}
    (root / "project.json").write_bytes(canonical_json(project))
    for rel in ("研究地图/00-研究地图契约.md", "研究地图/01-主研究地图.md", "研究地图/40-路线景观与重排条件.md", "研究地图/桥梁/权威状态与地图绑定.md"):
        (root / rel).write_text("v13 current\n", encoding="utf-8", newline="\n")
    if not legacy_review:
        build_test_closure(root)
        authority = json.loads((root / ".research/heads/research.json").read_text(encoding="utf-8"))
        authority["map_validation_receipt"] = pointer("研究地图/.research/validation-receipt.json", root)
        authority["independent_semantic_review"] = pointer(".research/map-review/closure.json", root)
        (root / ".research/heads/research.json").write_bytes(canonical_json(authority))
        project = load_project(root); project["research_authority_head"] = pointer(".research/heads/research.json", root)
        project = {key: project[key] for key in ("schema", "project_id", "created_at_utc", "objective", "objective_commitment_sha256", "research_authority_head", "execution_state_head", "generation", "project_complete", "pending_goal_update")}
        (root / "project.json").write_bytes(canonical_json(project))


def make_genesis_project(root: Path) -> None:
    make_project(root)
    project = load_project(root)
    authority = json.loads((root / project["research_authority_head"]["path"]).read_text(encoding="utf-8"))
    authority.update({"memory_index": {"items": []}, "route_review": None, "research_map": None, "map_validation_receipt": None, "independent_semantic_review": None, "genesis_eligibility": pointer(".research/authority/candidate-manifest.json", root), "map_never_created": True})
    (root / ".research/heads/genesis-research.json").write_bytes(canonical_json(authority)); project["research_authority_head"] = pointer(".research/heads/genesis-research.json", root); project["generation"] += 1; (root / "project.json").write_bytes(canonical_json(project))
    for rel in ("研究地图/.research/research-map.json", "研究地图/.research/validation-receipt.json", "研究地图/.research/asset-references.json", "研究地图/00-研究地图契约.md", "研究地图/01-主研究地图.md", "研究地图/40-路线景观与重排条件.md", "研究地图/桥梁/权威状态与地图绑定.md"):
        (root / rel).unlink(missing_ok=True)


def downgrade_to_thin_review(root: Path) -> None:
    thin_path = root / ".research/migration/review.json"
    thin_path.write_bytes(canonical_json({"verdict": "PASS"}))
    project = load_project(root)
    authority_path = root / project["research_authority_head"]["path"]
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    authority["independent_semantic_review"] = pointer(".research/migration/review.json", root)
    authority_path.write_bytes(canonical_json(authority))
    project["research_authority_head"] = {"path": project["research_authority_head"]["path"], "sha256": sha256_file(authority_path)}
    (root / "project.json").write_bytes(canonical_json(project))


def load_project(root: Path):
    return json.loads((root / "project.json").read_text(encoding="utf-8"))


def load_execution(root: Path):
    project = load_project(root)
    return json.loads((root / project["execution_state_head"]["path"]).read_text(encoding="utf-8"))


def publish_execution(root: Path, value: dict) -> None:
    project = load_project(root); rel = f".research/heads/execution-test-g{value['generation']:04d}-{value['last_transition']}.json"; path = root / rel
    path.write_bytes(canonical_json(value)); project["execution_state_head"] = {"path": rel, "sha256": sha256_file(path)}; project["generation"] += 1; (root / "project.json").write_bytes(canonical_json(project))


def budget(n: int = 5):
    return {"runtime_seconds": n, "tool_calls": n, "tickets": n, "checkpoints": n, "computations": n, "output_bytes": n, "no_progress_checkpoints": n}


def source_binding(root: Path, *, genesis: bool = False):
    project = load_project(root)
    if genesis:
        return {"kind": "genesis_objective", "objective_commitment_sha256": project["objective_commitment_sha256"], "genesis_head_sha256": project["research_authority_head"]["sha256"], "eligibility_receipt": pointer(".research/authority/candidate-manifest.json", root), "never_created_marker": True, "consumed": False}
    authority = json.loads((root / project["research_authority_head"]["path"]).read_text(encoding="utf-8"))
    return {"kind": "validated_map", "map": pointer("研究地图/.research/research-map.json", root), "validation_receipt": pointer("研究地图/.research/validation-receipt.json", root), "research_authority_head_sha256": project["research_authority_head"]["sha256"], "objective_commitment_sha256": project["objective_commitment_sha256"], "promoted_memory_index_sha256": sha256_bytes(canonical_json(authority["memory_index"])), "route_review_sha256": authority["route_review"]["sha256"]}


def portfolio(source: dict):
    members = []
    for i in range(3):
        members.append({"member_id": f"m{i}", "route_id": f"r{i}", "kind": "route_discovery" if i == 2 else "research", "semantic_fingerprint": {"proof_object": f"P{i}", "mechanism_family": f"M{i}", "quantifier_strategy": f"Q{i}"}, "bounded_question": f"b{i}", "required_outputs": [f"o{i}"], "stop_rule": f"s{i}", "failure_boundary": f"f{i}", "budget": budget(i + 1)})
    return {"schema": "math-research-route-portfolio/v13", "window_id": "w1", "source_binding_sha256": sha256_bytes(canonical_json(source)), "members": members, "window_budget": budget(20), "budget_transfer_policy": "frozen-policy"}


def window_plan(root: Path, *, genesis: bool = False):
    source = source_binding(root, genesis=genesis); port = portfolio(source)
    return {"schema": "math-research-window-plan/v13", "window_id": "w1", "planning_owner": "host", "source_binding": source, "route_portfolio": port, "proposed_attempt_ids": ["a0", "a1", "a2"], "counter_snapshot": load_execution(root)["counters"], "budget_reservation": budget(20)}


def prepare_records(root: Path):
    execution = load_execution(root); project = load_project(root); source_sha = sha256_bytes(canonical_json(execution["window_source_binding"])); portfolio_sha = sha256_bytes(canonical_json(execution["route_portfolio"])); base_pointer = pointer(".research/authority/candidate-manifest.json", root)
    rows = []
    for i in range(3):
        route_card_contract = {"schema": "math-research-route-card/v13", "project_id": project["project_id"], "window_id": "w1", "proposed_attempt_id": f"a{i}", "objective_commitment_sha256": project["objective_commitment_sha256"], "window_source_binding_sha256": source_sha, "route_decision_sha256": base_pointer["sha256"], "evidence_standard_sha256": sha256_bytes(objective()["evidence_standard"].encode("utf-8")), "semantic_fingerprint": execution["route_portfolio"]["members"][i]["semantic_fingerprint"], "success_gate": f"success-{i}", "candidate_failure_gate": f"failure-{i}"}
        route_card = {"path": f".research/staging/route-card-{i}.json", "sha256": sha256_bytes(canonical_json(route_card_contract))}
        capsule_contract = {"schema": "math-research-continuity-capsule/v13", "project_id": project["project_id"], "window_id": "w1", "proposed_attempt_id": f"a{i}", "objective_commitment_sha256": project["objective_commitment_sha256"], "cognition_sha256": base_pointer["sha256"], "selected_rendering_sha256": base_pointer["sha256"], "route_card_sha256": route_card["sha256"], "semantic_fingerprint": route_card_contract["semantic_fingerprint"], "local_position": "start", "open_questions": [], "generation": 0, "previous_capsule_sha256": None}
        capsule = {"path": f".research/staging/capsule-{i}.json", "sha256": sha256_bytes(canonical_json(capsule_contract))}
        queue_contract = {"schema": "math-research-window-queue-item/v13", "window_id": "w1", "proposed_attempt_id": f"a{i}", "solver_ticket_sha256": base_pointer["sha256"], "status": "prepared", "candidate_sha256": None, "dependency_sha256s": [], "verdict": None, "package_sha256": None}
        queue_item = {"path": f".research/staging/queue-{i}.json", "sha256": sha256_bytes(canonical_json(queue_contract))}
        rows.append({"schema": "math-research-attempt-start-prepare/v13", "project_id": project["project_id"], "window_id": "w1", "proposed_attempt_id": f"a{i}", "portfolio_member_id": f"m{i}", "objective_commitment_sha256": project["objective_commitment_sha256"], "source_binding_sha256": source_sha, "portfolio_sha256": portfolio_sha, "route_decision": base_pointer, "ticket": base_pointer, "cognition": base_pointer, "selected_rendering": base_pointer, "route_card": route_card, "route_card_contract": route_card_contract, "capsule": capsule, "capsule_contract": capsule_contract, "budget": budget(i + 1), "queue_item": queue_item, "queue_item_contract": queue_contract, "access_check": True, "input_check": True, "staging_check": True})
    return rows


def activation_payload(root: Path):
    execution = load_execution(root); project = load_project(root); rows = prepare_records(root); hashes = [sha256_bytes(canonical_json(x)) for x in rows]; source_sha = sha256_bytes(canonical_json(execution["window_source_binding"])); portfolio_sha = sha256_bytes(canonical_json(execution["route_portfolio"])); after = copy.deepcopy(execution["counters"]); after["internal_attempts_started"] += 3
    manifest = {"schema": "math-research-window-activation-manifest/v13", "expected_execution_head_sha256": project["execution_state_head"]["sha256"], "source_binding_sha256": source_sha, "portfolio_sha256": portfolio_sha, "prepare_sha256s": hashes, "counter_after": after}
    receipt = {"schema": "math-research-window-activation-receipt/v13", "window_id": "w1", "expected_project_head_sha256": sha256_file(root / "project.json"), "expected_execution_head_sha256": project["execution_state_head"]["sha256"], "source_binding_sha256": source_sha, "portfolio_sha256": portfolio_sha, "prepare_sha256s": hashes, "counter_before": execution["counters"], "counter_after": after, "candidate_execution_manifest_sha256": sha256_bytes(canonical_json(manifest))}
    return {"schema": "math-research-window-activate/v13", "prepare_records": rows, "activation_receipt": receipt}


def activate(root: Path, *, genesis: bool = False):
    plan = prepare_transition(root, "WINDOW_PLAN", window_plan(root, genesis=genesis)); publish_execution(root, plan["candidate_execution_head"])
    plan = prepare_transition(root, "WINDOW_ACTIVATE", activation_payload(root)); publish_execution(root, plan["candidate_execution_head"]); return plan


def legacy_queued_preflight_fixture(root: Path):
    activate(root); execution = load_execution(root); base = pointer(".research/authority/candidate-manifest.json", root)
    execution["phase"] = "window_verifying"; execution["verification_queue"] = []
    for attempt in execution["active_attempts"]:
        attempt["status"] = "verification_queued"; attempt["closing"] = {"schema": "math-research-attempt-closing/v13", "attempt_id": attempt["attempt_id"], "closing_reason": "legacy close", "outcome": "inconclusive", "candidate": base, "dependencies": [base], "artifact_refs": [base], "evidence_refs": ["legacy"], "final_capsule": base, "budget_usage": budget(1), "semantic_reset_directive": None, "cannot_imply": ["objective"], "reopen_conditions": ["preflight backfill"]}; attempt["verification"] = None; attempt["package"] = None
        execution["verification_queue"].append({"schema": "math-research-verification-queue/v13", "attempt_id": attempt["attempt_id"], "verifier_ticket": base, "candidate_sha256": base["sha256"], "dependency_sha256s": [base["sha256"]], "independence_mode": "context_isolated_single_agent", "consumer_principal": "verifier", "status": "queued"})
    execution["generation"] += 1; execution["last_transition"] = "LEGACY_QUEUED_FIXTURE"; publish_execution(root, execution)
    execution = load_execution(root); rows = []
    for attempt in execution["active_attempts"]:
        frozen = {k: attempt[k] for k in ("source_binding_sha256", "portfolio_sha256", "route_decision_sha256", "cognition_sha256", "selected_rendering_sha256", "route_card_sha256", "semantic_fingerprint", "evidence_standard_sha256")}
        rows.append({"attempt_id": attempt["attempt_id"], "old_candidate_sha256": base["sha256"], "old_dependency_sha256s": [base["sha256"]], "old_verifier_ticket_sha256": base["sha256"], "new_candidate": base, "new_dependencies": [base], "new_artifact_refs": [base, preflight_ref(attempt["attempt_id"])], "frozen_semantics": frozen})
    return {"schema": "math-research-queued-preflight-rebind/v13", "window_id": "w1", "expected_execution_head_sha256": load_project(root)["execution_state_head"]["sha256"], "compatibility_reason": "v13-attempt-package-preflight-backfill", "rebinds": rows}


def verified_attempt_end_fixture(root: Path, *, route_delta: list, result_proposals: list, promotion_eligible: bool):
    activate(root); execution = load_execution(root); base = pointer(".research/authority/candidate-manifest.json", root); attempt = execution["active_attempts"][0]
    verification = {"verdict": "PASS"}; closing = {"outcome": "inconclusive", "artifact_refs": [base, preflight_ref("a0")]}
    attempt["status"] = "verification_complete"; attempt["closing"] = closing; attempt["verification"] = verification
    execution["phase"] = "window_verifying"; execution["generation"] += 1; execution["last_transition"] = "TEST_VERIFIED_ATTEMPT"; publish_execution(root, execution)
    execution = load_execution(root); attempt = execution["active_attempts"][0]
    package = {"schema": "math-research-attempt-reconciliation-package/v13", "attempt_id": "a0", "window_id": "w1", "source_binding_sha256": attempt["source_binding_sha256"], "portfolio_member_id": attempt["portfolio_member_id"], "route_decision_sha256": attempt["route_decision_sha256"], "outcome": "inconclusive", "artifact_refs": closing["artifact_refs"], "evidence_refs": ["synthetic-evidence"], "verification": verification, "final_capsule": base, "route_delta": route_delta, "result_proposals": result_proposals, "obstacles": ["synthetic obstacle"], "cannot_imply": ["terminal objective"], "reopen_conditions": ["new evidence"], "budget_usage": budget(1), "semantic_reset_directive": None, "source_invalidated": False, "promotion_eligible": promotion_eligible}
    before = execution["counters"]["internal_attempts_completed"]; receipt = {"schema": "math-research-attempt-close-receipt/v13", "attempt_id": "a0", "package_sha256": sha256_bytes(canonical_json(package)), "completed_counter_before": before, "completed_counter_after": before + 1}
    return {"schema": "math-research-attempt-end/v13", "attempt_id": "a0", "package": package, "close_receipt": receipt}


class ObjectiveGoldenTests(unittest.TestCase):
    def test_exact_bytes_and_order(self):
        raw = objective_bytes(objective()); self.assertFalse(raw.startswith(b"\xef\xbb\xbf")); self.assertNotIn(b"\r", raw); self.assertTrue(raw.endswith(b"\n")); self.assertIn("μ".encode(), raw)

    def test_metadata_and_noncanonical_inputs_fail(self):
        changed = objective(); changed["path"] = "x"
        with self.assertRaises(V13Error): objective_bytes(changed)
        raw = objective_bytes(objective())
        for bad in (b"\xef\xbb\xbf" + raw, raw.replace(b"\n", b"\r\n"), b'{"a":1,"a":2}\n', json.dumps(objective(), ensure_ascii=True, indent=2).encode() + b"\n"):
            with self.assertRaises(V13Error): load_json_bytes(bad, canonical_required=True)

    def test_each_field_and_assumption_order_change_commitment(self):
        base = sha256_bytes(objective_bytes(objective()))
        for key in ("statement", "domain", "quantifier_order", "evidence_standard", "completion_standard"):
            value = objective(); value[key] += "x"; self.assertNotEqual(base, sha256_bytes(objective_bytes(value)))
        value = objective(); value["assumptions"].reverse(); self.assertNotEqual(base, sha256_bytes(objective_bytes(value)))


class StateMachineTests(unittest.TestCase):
    def test_idle_thin_review_is_upgrade_required_and_cannot_plan(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); downgrade_to_thin_review(root)
            status = validate_project(root)
            self.assertEqual("map_review_upgrade_required", status["status"])
            self.assertEqual("legacy_map_upgrade_required", status["source_mode"])
            self.assertFalse(status["activation_eligible"])
            with self.assertRaises(V13Error) as caught:
                prepare_transition(root, "WINDOW_PLAN", window_plan(root))
            self.assertEqual("map_review_upgrade_required", caught.exception.code)

    def test_active_window_can_resume_on_frozen_legacy_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); activate(root); downgrade_to_thin_review(root)
            status = validate_project(root)
            self.assertEqual("v13_ready", status["status"])
            self.assertEqual("legacy_map_upgrade_required", status["source_mode"])
            execution = load_execution(root); frozen = copy.deepcopy(execution); frozen["generation"] = 0; frozen["last_transition"] = ""
            payload = {"schema": "math-research-window-suspend/v13", "resume_capsule": pointer(".research/authority/candidate-manifest.json", root), "frozen_state_sha256": sha256_bytes(canonical_json(frozen)), "reason": "fixture pause"}
            self.assertEqual("window_suspended", prepare_transition(root, "SUSPEND", payload)["candidate_execution_head"]["phase"])

    def test_startup_requires_full_execution_schema_and_public_utf8(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); self.assertTrue(validate_project(root)["activation_eligible"])
            cp = subprocess.run([sys.executable, str(SCRIPTS / "math_research_state_v13.py"), "startup", "--project", str(root)], capture_output=True, encoding="utf-8", check=True)
            self.assertIn("v13_ready", cp.stdout)
            execution = load_execution(root); execution.pop("queue"); publish_execution(root, execution)
            with self.assertRaises(V13Error): validate_project(root)

    def test_goal_loss_causes_no_authoritative_write(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); before = sha256_file(root / "project.json")
            with self.assertRaises(V13Error): prepare_transition(root, "WINDOW_PLAN", window_plan(root), goal_state="paused")
            self.assertEqual(before, sha256_file(root / "project.json"))

    def test_prepare_cli_writes_local_plan_but_stdout_is_minimized(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); payload_path = root.parent / "payload.json"; output_path = root.parent / "plan-output.json"; payload_path.write_bytes(canonical_json(window_plan(root)))
            cp = subprocess.run([sys.executable, str(SCRIPTS / "math_research_state_v13.py"), "prepare", "--project", str(root), "--transition", "WINDOW_PLAN", "--payload", str(payload_path), "--goal-state", "active", "--output", str(output_path)], capture_output=True, encoding="utf-8", check=True)
            public = json.loads(cp.stdout); self.assertEqual("prepared", public["status"]); self.assertTrue(output_path.is_file()); self.assertNotIn("bounded_question", cp.stdout); self.assertNotIn("证明", cp.stdout); self.assertIn("candidate_execution_head", output_path.read_text(encoding="utf-8"))

    def test_prepare_is_non_authoritative_and_third_failure_keeps_zero(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); plan = prepare_transition(root, "WINDOW_PLAN", window_plan(root)); publish_execution(root, plan["candidate_execution_head"])
            rows = prepare_records(root); pre = prepare_transition(root, "ATTEMPT_START_PREPARE", rows[0]); self.assertEqual("none", pre["authority"]); self.assertEqual(0, pre["candidate_execution_head"]["counters"]["internal_attempts_started"])
            payload = activation_payload(root); payload["prepare_records"] = payload["prepare_records"][:2]
            with self.assertRaises(V13Error): prepare_transition(root, "WINDOW_ACTIVATE", payload)
            self.assertEqual(0, load_execution(root)["counters"]["internal_attempts_started"])

    def test_activation_starts_three_with_one_receipt_and_consumes_genesis_once(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_genesis_project(root); plan = activate(root, genesis=True); execution = plan["candidate_execution_head"]
            self.assertEqual(3, execution["counters"]["internal_attempts_started"]); self.assertEqual(3, len(execution["active_attempts"])); self.assertEqual(1, len({x["activation_receipt_sha256"] for x in execution["active_attempts"]})); self.assertTrue(execution["window_source_binding"]["consumed"])
            publish_execution(root, execution); self.assertEqual("window_running", validate_project(root)["phase"])

    def test_migrated_project_can_never_plan_genesis(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_genesis_project(root); execution = load_execution(root); execution["migrated_project"] = True; execution["generation"] += 1; execution["last_transition"] = "MIGRATION"; publish_execution(root, execution)
            with self.assertRaises(V13Error): prepare_transition(root, "WINDOW_PLAN", window_plan(root, genesis=True))

    def test_existing_valid_map_refuses_genesis(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root)
            with self.assertRaises(V13Error): prepare_transition(root, "WINDOW_PLAN", window_plan(root, genesis=True))

    def test_checkpoint_cannot_change_frozen_semantics(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); activate(root); execution = load_execution(root); attempt = execution["active_attempts"][0]; base = pointer(".research/authority/candidate-manifest.json", root)
            frozen = {k: attempt[k] for k in ("source_binding_sha256", "portfolio_sha256", "route_decision_sha256", "cognition_sha256", "selected_rendering_sha256", "route_card_sha256", "semantic_fingerprint", "evidence_standard_sha256")}
            initial = execution["capsules"][0]; successor_contract = {k: v for k, v in initial.items() if k not in {"object", "attempt_id"}}; successor_contract["generation"] += 1; successor_contract["previous_capsule_sha256"] = attempt["last_capsule_sha256"]; successor_contract["local_position"] = "checkpoint"
            successor_pointer = {"path": ".research/staging/capsule-successor.json", "sha256": sha256_bytes(canonical_json(successor_contract))}
            payload = {"schema": "math-research-checkpoint/v13", "attempt_id": "a0", "frozen_bindings": frozen, "prior_capsule_sha256": attempt["last_capsule_sha256"], "successor_capsule": successor_pointer, "successor_capsule_contract": successor_contract, "last_verified_checkpoint": base}
            self.assertEqual("window_running", prepare_transition(root, "CHECKPOINT", payload)["candidate_execution_head"]["phase"])
            payload["frozen_bindings"]["semantic_fingerprint"] = {"proof_object": "changed", "mechanism_family": "M0", "quantifier_strategy": "Q0"}
            with self.assertRaises(V13Error): prepare_transition(root, "CHECKPOINT", payload)

    def test_semantic_reset_closes_without_successor(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); activate(root); base = pointer(".research/authority/candidate-manifest.json", root)
            payload = {"schema": "math-research-attempt-closing/v13", "attempt_id": "a0", "closing_reason": "semantic change", "outcome": "inconclusive", "candidate": None, "dependencies": [], "artifact_refs": [base, preflight_ref("a0")], "evidence_refs": ["e"], "final_capsule": base, "budget_usage": budget(1), "semantic_reset_directive": {"successor_attempt_forbidden_in_window": True}, "cannot_imply": ["objective"], "reopen_conditions": ["future window"]}
            plan = prepare_transition(root, "SEMANTIC_RESET", payload); self.assertEqual("attempt_closing", plan["candidate_execution_head"]["phase"]); self.assertEqual(3, len(plan["candidate_execution_head"]["active_attempts"]))

    def test_verification_principal_and_single_repair_are_enforced(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); activate(root); base = pointer(".research/authority/candidate-manifest.json", root)
            close = {"schema": "math-research-attempt-closing/v13", "attempt_id": "a0", "closing_reason": "candidate", "outcome": "candidate_found", "candidate": base, "dependencies": [base], "artifact_refs": [base, preflight_ref("a0")], "evidence_refs": ["e"], "final_capsule": base, "budget_usage": budget(1), "semantic_reset_directive": None, "cannot_imply": ["outside scope"], "reopen_conditions": ["verify"]}
            publish_execution(root, prepare_transition(root, "ATTEMPT_CLOSE", close)["candidate_execution_head"])
            queue = {"schema": "math-research-verification-queue/v13", "attempt_id": "a0", "verifier_ticket": base, "candidate_sha256": base["sha256"], "dependency_sha256s": [base["sha256"]], "independence_mode": "context_isolated_single_agent", "consumer_principal": "solver"}
            with self.assertRaises(V13Error): prepare_transition(root, "VERIFICATION_QUEUE", queue)
            queue["consumer_principal"] = "verifier"; publish_execution(root, prepare_transition(root, "VERIFICATION_QUEUE", queue)["candidate_execution_head"])
            result = {"schema": "math-research-verification-result/v13", "attempt_id": "a0", "verifier_ticket_sha256": base["sha256"], "candidate_sha256": base["sha256"], "dependency_sha256s": [base["sha256"]], "verdict": "FAIL", "checked_scope": "all", "earliest_error": "line 1", "unresolved": [], "context_isolated": True}
            publish_execution(root, prepare_transition(root, "VERIFICATION_RESULT", result)["candidate_execution_head"]); attempt = load_execution(root)["active_attempts"][0]
            frozen = {k: attempt[k] for k in ("source_binding_sha256", "portfolio_sha256", "route_decision_sha256", "semantic_fingerprint", "evidence_standard_sha256")}
            repair = {"schema": "math-research-limited-repair/v13", "attempt_id": "a0", "repair_ticket": base, "old_candidate_sha256": base["sha256"], "new_candidate": base, "new_dependencies": [base], "new_artifact_refs": [base, preflight_ref("a0-repair")], "frozen_semantics": frozen}
            publish_execution(root, prepare_transition(root, "LIMITED_REPAIR", repair)["candidate_execution_head"])
            with self.assertRaises(V13Error): prepare_transition(root, "LIMITED_REPAIR", repair)

    def test_queued_preflight_rebind_is_atomic_and_preserves_semantics_and_counters(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); payload = legacy_queued_preflight_fixture(root); before = load_execution(root)
            plan = prepare_transition(root, "QUEUED_PREFLIGHT_REBIND", payload); after = plan["candidate_execution_head"]
            self.assertEqual("attempt_closing", after["phase"]); self.assertEqual([], after["verification_queue"]); self.assertEqual(before["counters"], after["counters"]); self.assertEqual(0, after["repair_count"])
            for old, new in zip(before["active_attempts"], after["active_attempts"]):
                self.assertEqual("closing", new["status"]); self.assertEqual(0, new["repair_count"]); self.assertEqual(old["semantic_fingerprint"], new["semantic_fingerprint"]); self.assertTrue(any(x["path"].endswith("/attempt-package-preflight.json") for x in new["closing"]["artifact_refs"]))

    def test_queued_preflight_rebind_rejects_partial_repeat_and_nonlegacy_state(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); payload = legacy_queued_preflight_fixture(root)
            partial = copy.deepcopy(payload); partial["rebinds"].pop()
            with self.assertRaises(V13Error): prepare_transition(root, "QUEUED_PREFLIGHT_REBIND", partial)
            execution = load_execution(root); execution["active_attempts"][0]["closing"]["artifact_refs"].append(preflight_ref("already-bound")); execution["generation"] += 1; execution["last_transition"] = "RECEIPT_BOUND"; publish_execution(root, execution)
            payload["expected_execution_head_sha256"] = load_project(root)["execution_state_head"]["sha256"]
            with self.assertRaises(V13Error): prepare_transition(root, "QUEUED_PREFLIGHT_REBIND", payload)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); payload = legacy_queued_preflight_fixture(root); plan = prepare_transition(root, "QUEUED_PREFLIGHT_REBIND", payload); publish_execution(root, plan["candidate_execution_head"]); payload["expected_execution_head_sha256"] = load_project(root)["execution_state_head"]["sha256"]
            with self.assertRaises(V13Error): prepare_transition(root, "QUEUED_PREFLIGHT_REBIND", payload)

    def test_reconciliation_needs_three_packages_and_never_new_math(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); activate(root); execution = load_execution(root); execution["phase"] = "window_verifying"
            for i, attempt in enumerate(execution["active_attempts"]):
                attempt["status"] = "package_ready"; attempt["closing"] = {"outcome": "inconclusive"}; attempt["package"] = {"sha256": str(i + 1) * 64}
            execution["active_attempts"][2]["package"] = None; execution["generation"] += 1; execution["last_transition"] = "TEST_PACKAGES"; publish_execution(root, execution)
            payload = {"schema": "math-research-window-reconciliation/v13", "package_sha256s": ["1" * 64, "2" * 64], "new_math_performed": False, "conflict_set": [], "candidate_research_authority_head": pointer(".research/heads/research.json", root), "candidate_manifest": pointer(".research/authority/candidate-manifest.json", root), "map_validation_receipt": pointer("研究地图/.research/validation-receipt.json", root), "semantic_review_receipt": pointer(".research/migration/review.json", root), "reconciliation_receipt": pointer(".research/migration/review.json", root)}
            with self.assertRaises(V13Error): prepare_transition(root, "WINDOW_RECONCILE", payload)

    def test_window_close_publishes_both_heads_with_all_active_pointers_clear(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); activate(root); execution = load_execution(root); execution["phase"] = "window_verifying"
            package_hashes = []
            for i, attempt in enumerate(execution["active_attempts"]):
                value = str(i + 1) * 64; package_hashes.append(value); attempt["status"] = "package_ready"; attempt["closing"] = {"outcome": "inconclusive"}; attempt["package"] = {"sha256": value}
            execution["generation"] += 1; execution["last_transition"] = "TEST_PACKAGES"; publish_execution(root, execution); base = pointer(".research/authority/candidate-manifest.json", root); authority_pointer = pointer(".research/heads/research.json", root)
            reconcile = {"schema": "math-research-window-reconciliation/v13", "package_sha256s": package_hashes, "new_math_performed": False, "conflict_set": [], "candidate_research_authority_head": authority_pointer, "candidate_manifest": base, "map_validation_receipt": pointer("研究地图/.research/validation-receipt.json", root), "semantic_review_receipt": pointer(".research/migration/review.json", root), "reconciliation_receipt": pointer(".research/migration/review.json", root)}
            publish_execution(root, prepare_transition(root, "WINDOW_RECONCILE", reconcile)["candidate_execution_head"]); execution = load_execution(root)
            expected = copy.deepcopy(execution); expected["generation"] += 1; expected["last_transition"] = "WINDOW_CLOSE"; expected.update({"phase": "window_idle", "window_source_binding": None, "active_window": None, "queue": [], "active_attempts": [], "route_decisions": [], "route_portfolio": None, "cognition": None, "capsules": [], "verification_queue": [], "repair_count": 0}); expected["counters"]["route_reviews"] += 1; expected["counters"]["attempts_since_route_review"] = 0; expected["counters"]["route_review_due"] = False
            close = {"schema": "math-research-window-close/v13", "reconciliation_receipt_sha256": reconcile["reconciliation_receipt"]["sha256"], "candidate_research_authority_head": authority_pointer, "candidate_execution_state_head": {"path": ".research/heads/window-close.json", "sha256": sha256_bytes(canonical_json(expected))}, "queue_clear_proof": True, "terminal_candidate": None}
            plan = prepare_transition(root, "WINDOW_CLOSE", close); final = plan["candidate_execution_head"]; self.assertEqual("both", plan["authority"]); self.assertEqual("window_idle", final["phase"])
            for key in ("active_window", "window_source_binding", "route_portfolio", "cognition"): self.assertIsNone(final[key])
            for key in ("queue", "active_attempts", "route_decisions", "capsules", "verification_queue"): self.assertEqual([], final[key])
            self.assertEqual(close["candidate_execution_state_head"], plan["candidate_project"]["execution_state_head"])

    def test_targeted_review_gate_blocks_only_named_transition(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); execution = load_execution(root); execution["review_required"] = [{"scope": "project", "owner_lifecycle": "maintenance_reconciliation", "blocked_transition": ["WINDOW_PLAN"], "dependency_closure": [], "release_condition": "receipt", "evidence_refs": []}]; execution["generation"] += 1; execution["last_transition"] = "GATE"; publish_execution(root, execution)
            with self.assertRaises(V13Error): prepare_transition(root, "WINDOW_PLAN", window_plan(root))

    def test_planning_block_resume_and_supersede_do_not_count(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); plan = prepare_transition(root, "WINDOW_PLAN", window_plan(root)); publish_execution(root, plan["candidate_execution_head"]); execution = load_execution(root); source_sha = sha256_bytes(canonical_json(execution["window_source_binding"]))
            blocked = {"schema": "math-research-window-planning-block/v13", "reason": "not differentiated", "missing_regions": ["third method"], "reopen_condition": "new tool", "source_binding_sha256": source_sha}; publish_execution(root, prepare_transition(root, "WINDOW_PLANNING_BLOCK", blocked)["candidate_execution_head"])
            resumed = {"schema": "math-research-window-planning-resume/v13", "source_binding_sha256": source_sha, "release_evidence_refs": ["tool-ready"]}; publish_execution(root, prepare_transition(root, "WINDOW_PLANNING_RESUME", resumed)["candidate_execution_head"])
            closure = pointer(".research/authority/candidate-manifest.json", root); supersede = {"schema": "math-research-window-planning-supersede/v13", "reason": "authority changed", "superseded_proposed_attempt_ids": ["a0", "a1", "a2"], "zero_attempts_committed": True, "planning_closure": closure}
            final = prepare_transition(root, "WINDOW_PLANNING_SUPERSEDE", supersede)["candidate_execution_head"]; self.assertEqual("window_idle", final["phase"]); self.assertEqual(0, final["counters"]["internal_attempts_started"])

    def test_attempt_end_advances_execution_only_and_counts_once(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); activate(root); base = pointer(".research/authority/candidate-manifest.json", root)
            close = {"schema": "math-research-attempt-closing/v13", "attempt_id": "a0", "closing_reason": "bounded stop", "outcome": "inconclusive", "candidate": None, "dependencies": [], "artifact_refs": [base, preflight_ref("a0")], "evidence_refs": ["e"], "final_capsule": base, "budget_usage": budget(1), "semantic_reset_directive": None, "cannot_imply": ["objective"], "reopen_conditions": ["new evidence"]}; publish_execution(root, prepare_transition(root, "ATTEMPT_CLOSE", close)["candidate_execution_head"])
            execution = load_execution(root); attempt = execution["active_attempts"][0]
            package = {"schema": "math-research-attempt-reconciliation-package/v13", "attempt_id": "a0", "window_id": "w1", "source_binding_sha256": attempt["source_binding_sha256"], "portfolio_member_id": attempt["portfolio_member_id"], "route_decision_sha256": attempt["route_decision_sha256"], "outcome": "inconclusive", "artifact_refs": close["artifact_refs"], "evidence_refs": ["e"], "verification": None, "final_capsule": base, "route_delta": [], "result_proposals": [], "obstacles": ["o"], "cannot_imply": ["objective"], "reopen_conditions": ["new evidence"], "budget_usage": budget(1), "semantic_reset_directive": None, "source_invalidated": False, "promotion_eligible": False}
            before = execution["counters"]["internal_attempts_completed"]; receipt = {"schema": "math-research-attempt-close-receipt/v13", "attempt_id": "a0", "package_sha256": sha256_bytes(canonical_json(package)), "completed_counter_before": before, "completed_counter_after": before + 1}
            plan = prepare_transition(root, "ATTEMPT_END", {"schema": "math-research-attempt-end/v13", "attempt_id": "a0", "package": package, "close_receipt": receipt}); self.assertEqual("execution", plan["authority"]); self.assertIsNone(plan["candidate_research_authority_head"]); self.assertEqual(before + 1, plan["candidate_execution_head"]["counters"]["internal_attempts_completed"])

    def test_source_valid_pass_requires_explicit_reconciliation_knowledge(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); payload = verified_attempt_end_fixture(root, route_delta=[], result_proposals=[], promotion_eligible=False)
            with self.assertRaisesRegex(V13Error, "source-valid PASS package"):
                prepare_transition(root, "ATTEMPT_END", payload)

    def test_source_valid_pass_with_route_delta_is_promotion_eligible(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); payload = verified_attempt_end_fixture(root, route_delta=[{"scope": "route_local", "claim": "synthetic verified boundary"}], result_proposals=[], promotion_eligible=True)
            plan = prepare_transition(root, "ATTEMPT_END", payload)
            self.assertTrue(plan["candidate_execution_head"]["active_attempts"][0]["package"]["promotion_eligible"])

    def test_reconcile_refuses_unchanged_authority_for_promotable_knowledge(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); activate(root); execution = load_execution(root); package_hashes = []
            for i, attempt in enumerate(execution["active_attempts"]):
                value = str(i + 1) * 64; package_hashes.append(value); attempt["status"] = "package_ready"; attempt["closing"] = {"outcome": "inconclusive"}; attempt["package"] = {"sha256": value, "promotion_eligible": i == 0}
            execution["phase"] = "window_verifying"; execution["generation"] += 1; execution["last_transition"] = "TEST_PROMOTABLE_PACKAGES"; publish_execution(root, execution)
            base = pointer(".research/authority/candidate-manifest.json", root); reconcile = {"schema": "math-research-window-reconciliation/v13", "package_sha256s": package_hashes, "new_math_performed": False, "conflict_set": [], "candidate_research_authority_head": pointer(".research/heads/research.json", root), "candidate_manifest": base, "map_validation_receipt": pointer("研究地图/.research/validation-receipt.json", root), "semantic_review_receipt": pointer(".research/migration/review.json", root), "reconciliation_receipt": pointer(".research/migration/review.json", root)}
            with self.assertRaisesRegex(V13Error, "new research authority head"):
                prepare_transition(root, "WINDOW_RECONCILE", reconcile)

    def test_suspend_resume_preserves_same_window(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); activate(root); execution = load_execution(root); frozen = copy.deepcopy(execution); frozen["generation"] = 0; frozen["last_transition"] = ""; base = pointer(".research/authority/candidate-manifest.json", root)
            suspend = {"schema": "math-research-window-suspend/v13", "resume_capsule": base, "frozen_state_sha256": sha256_bytes(canonical_json(frozen)), "reason": "safe pause"}; publish_execution(root, prepare_transition(root, "SUSPEND", suspend)["candidate_execution_head"])
            resume = {"schema": "math-research-window-resume/v13", "resume_capsule_sha256": base["sha256"], "integrity_check": True, "frozen_bindings_unchanged": True}; plan = prepare_transition(root, "RESUME", resume); self.assertEqual("window_running", plan["candidate_execution_head"]["phase"]); self.assertEqual("w1", plan["candidate_execution_head"]["active_window"]["window_id"])

    def test_source_invalidation_requires_three_closing_packages(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); activate(root); base = pointer(".research/authority/candidate-manifest.json", root); source_sha = sha256_bytes(canonical_json(load_execution(root)["window_source_binding"])); gate = {"scope": "source_integrity", "owner_lifecycle": "source_integrity_review", "blocked_transition": ["WINDOW_RECONCILE"], "dependency_closure": [source_sha], "release_condition": "source receipt", "evidence_refs": []}
            start = {"schema": "math-research-source-review-start/v13", "source_binding_sha256": source_sha, "review_ticket": base, "review_gate": gate}; publish_execution(root, prepare_transition(root, "SOURCE_REVIEW_START", start)["candidate_execution_head"])
            invalid = {"schema": "math-research-source-invalidation/v13", "review_receipt": base, "source_binding_sha256": source_sha, "dependency_closure": [source_sha], "invalidation_id": "inv-1"}; publish_execution(root, prepare_transition(root, "SOURCE_INVALIDATE", invalid)["candidate_execution_head"])
            payload = {"schema": "math-research-source-integrity-reconciliation/v13", "new_math_performed": False, "candidate_research_authority_head": pointer(".research/heads/research.json", root), "candidate_execution_state_head": {"path": ".research/heads/source-close.json", "sha256": H}, "withdrawals": [], "dependency_impact": [], "queue_clear_proof": True, "semantic_review_receipt": base, "close_receipt": base}
            with self.assertRaises(V13Error): prepare_transition(root, "SOURCE_INTEGRITY_RECONCILE", payload)

    def test_maintenance_failure_keeps_old_research_head_and_owner_gate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); base = pointer(".research/authority/candidate-manifest.json", root); start = {"schema": "math-research-maintenance-start/v13", "input_records": [base], "reason": "late verification", "origin_phase": "window_idle", "new_math_performed": False}; publish_execution(root, prepare_transition(root, "MAINTENANCE_START", start)["candidate_execution_head"])
            gate = {"scope": "claim", "owner_lifecycle": "maintenance_reconciliation", "blocked_transition": ["WINDOW_PLAN"], "dependency_closure": ["claim-1"], "release_condition": "adjudication", "evidence_refs": []}
            fail = {"schema": "math-research-maintenance-reconciliation/v13", "new_math_performed": False, "candidate_research_authority_head": None, "candidate_execution_state_head": None, "promotion_or_withdrawal": [], "dependency_impact": [], "semantic_review_receipt": None, "maintenance_receipt": base, "next_phase": "maintenance", "review_gate": gate}
            plan = prepare_transition(root, "MAINTENANCE_FAIL", fail); self.assertEqual("execution", plan["authority"]); self.assertIsNone(plan["candidate_research_authority_head"]); self.assertEqual("maintenance_reconciliation", plan["candidate_execution_head"]["review_required"][-1]["owner_lifecycle"])

    def test_terminal_coverage_and_soundness_branches(self):
        for impact, expected in (("coverage", "window_idle"), ("soundness", "maintenance")):
            with self.subTest(impact=impact), tempfile.TemporaryDirectory() as td:
                root = Path(td); make_project(root); execution = load_execution(root); base = pointer(".research/authority/candidate-manifest.json", root); execution["phase"] = "completion_pending"; execution["terminal_audits"] = [{"status": "candidate_frozen", "candidate": base, "dependencies": [base], "completion_candidate_sha256": "3" * 64, "audits": {}}]; execution["generation"] += 1; execution["last_transition"] = "CANDIDATE"; publish_execution(root, execution)
                tickets = {k: {"path": base["path"], "sha256": str(i + 4) * 64} for i, k in enumerate(sorted(AUDIT_KINDS))}
                start = {"schema": "math-research-terminal-audit-start/v13", "completion_candidate_sha256": "3" * 64, "audit_tickets": tickets, "context_isolation": True}; publish_execution(root, prepare_transition(root, "TERMINAL_AUDIT_START", start)["candidate_execution_head"])
                kind = sorted(AUDIT_KINDS)[0]; result = {"schema": "math-research-terminal-audit-result/v13", "audit_kind": kind, "ticket_sha256": tickets[kind]["sha256"], "completion_candidate_sha256": "3" * 64, "verdict": "FAIL", "receipt": base, "impact_classification": impact, "new_math_performed": False}
                self.assertEqual(expected, prepare_transition(root, "TERMINAL_AUDIT_RESULT", result)["candidate_execution_head"]["phase"])

    def test_three_pass_completion_sets_permanent_pending_and_closes_engine(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); make_project(root); execution = load_execution(root); base = pointer(".research/authority/candidate-manifest.json", root); execution["phase"] = "terminal_audit"; tickets = {k: {"path": base["path"], "sha256": str(i + 4) * 64} for i, k in enumerate(sorted(AUDIT_KINDS))}; audits = {}
            for kind in AUDIT_KINDS: audits[kind] = {"schema": "math-research-terminal-audit-result/v13", "audit_kind": kind, "ticket_sha256": tickets[kind]["sha256"], "completion_candidate_sha256": "3" * 64, "verdict": "PASS", "receipt": base, "impact_classification": None, "new_math_performed": False}
            execution["terminal_audits"] = [{"status": "auditing", "candidate": base, "dependencies": [base], "completion_candidate_sha256": "3" * 64, "audits": audits, "audit_tickets": tickets}]; execution["generation"] += 1; execution["last_transition"] = "AUDITS_PASS"; publish_execution(root, execution)
            expected = copy.deepcopy(execution); expected["generation"] += 1; expected["last_transition"] = "COMPLETION_PUBLISH"; expected["phase"] = "project_complete"; expected["terminal_audits"][0]["status"] = "published"; expected["terminal_audits"][0]["terminal_summary"] = base; expected["terminal_audits"][0]["completion_plan"] = base
            payload = {"schema": "math-research-completion-publication/v13", "completion_candidate_sha256": "3" * 64, "terminal_summary": base, "completion_plan": base, "candidate_research_authority_head": pointer(".research/heads/research.json", root), "candidate_execution_state_head": {"path": ".research/heads/final-execution.json", "sha256": sha256_bytes(canonical_json(expected))}}
            plan = prepare_transition(root, "COMPLETION_PUBLISH", payload); self.assertTrue(plan["candidate_project"]["project_complete"]); self.assertTrue(plan["candidate_project"]["pending_goal_update"])
            final_exec = plan["candidate_execution_head"]; (root / ".research/heads/final-execution.json").write_bytes(canonical_json(final_exec)); project = plan["candidate_project"]; (root / "project.json").write_bytes(canonical_json(project))
            self.assertEqual("v13_complete_pending_goal_update", validate_project(root)["status"])
            with self.assertRaises(V13Error): prepare_transition(root, "WINDOW_PLAN", window_plan(root))


class CommitHarnessTests(unittest.TestCase):
    def build_plan(self, root: Path, staging: Path, *, extra: bool = False):
        old = load_project(root); (staging / "objects").mkdir(parents=True); (staging / "objects/new.json").write_bytes(canonical_json({"schema": "test-object/v1"}))
        candidate = copy.deepcopy(old); candidate["generation"] += 1; (staging / "project.json").write_bytes(canonical_json(candidate))
        if extra: (staging / "unknown.txt").write_text("unknown\n", encoding="utf-8")
        writes = [{"path": ".research/objects/new.json", "source": "objects/new.json", "sha256": sha256_file(staging / "objects/new.json"), "immutable": True, "expected_old_sha256": None}, {"path": "project.json", "source": "project.json", "sha256": sha256_file(staging / "project.json"), "immutable": False, "expected_old_sha256": sha256_file(root / "project.json")}]
        payload = {"schema": "math-research-commit-plan/v13", "expected_project_head_sha256": sha256_file(root / "project.json"), "expected_execution_head_sha256": old["execution_state_head"]["sha256"], "expected_research_authority_head_sha256": old["research_authority_head"]["sha256"], "staging_inventory_sha256": sha256_bytes(canonical_json(inventory(staging))), "writes": writes}
        plan = {**payload, "plan_sha256": sha256_bytes(canonical_json(payload))}; ordered = {"schema": plan["schema"], "expected_project_head_sha256": plan["expected_project_head_sha256"], "expected_execution_head_sha256": plan["expected_execution_head_sha256"], "expected_research_authority_head_sha256": plan["expected_research_authority_head_sha256"], "staging_inventory_sha256": plan["staging_inventory_sha256"], "plan_sha256": plan["plan_sha256"], "writes": plan["writes"]}
        path = root.parent / "plan.json"; path.write_bytes(canonical_json(ordered)); return path

    def test_full_inventory_and_immutable_overwrite_are_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "project"; staging = Path(td) / "stage"; root.mkdir(); staging.mkdir(); make_project(root); plan = self.build_plan(root, staging, extra=True)
            with self.assertRaises(V13Error): validate_plan(root, staging, plan)

    def test_map_write_revalidates_exact_closure(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "project"; staging = Path(td) / "stage"; root.mkdir(); staging.mkdir(); make_project(root)
            map_rel = "研究地图/.research/research-map.json"; old_map_sha = sha256_file(root / map_rel)
            changed = json.loads((root / map_rel).read_text(encoding="utf-8")); changed["fixture_mutation"] = True
            (staging / "map.json").write_bytes(canonical_json(changed))
            old = load_project(root); candidate = copy.deepcopy(old); candidate["generation"] += 1; (staging / "project.json").write_bytes(canonical_json(candidate))
            writes = [
                {"path": map_rel, "source": "map.json", "sha256": sha256_file(staging / "map.json"), "immutable": False, "expected_old_sha256": old_map_sha},
                {"path": "project.json", "source": "project.json", "sha256": sha256_file(staging / "project.json"), "immutable": False, "expected_old_sha256": sha256_file(root / "project.json")},
            ]
            payload = {"schema": "math-research-commit-plan/v13", "expected_project_head_sha256": sha256_file(root / "project.json"), "expected_execution_head_sha256": old["execution_state_head"]["sha256"], "expected_research_authority_head_sha256": old["research_authority_head"]["sha256"], "staging_inventory_sha256": sha256_bytes(canonical_json(inventory(staging))), "writes": writes}
            plan = {**payload, "plan_sha256": sha256_bytes(canonical_json(payload))}; plan_path = Path(td) / "map-plan.json"; plan_path.write_bytes(canonical_json(plan))
            with self.assertRaises(V13Error) as caught:
                validate_plan(root, staging, plan_path)
            self.assertEqual("map_review_closure_invalid", caught.exception.code)

    def test_completed_project_rejects_commit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "project"; staging = Path(td) / "stage"; root.mkdir(); staging.mkdir(); make_project(root)
            project = load_project(root); project["project_complete"] = True; project["pending_goal_update"] = True; (root / "project.json").write_bytes(canonical_json(project))
            plan = self.build_plan(root, staging)
            with self.assertRaises(V13Error) as caught:
                validate_plan(root, staging, plan)
            self.assertEqual("project_closed", caught.exception.code)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "project"; staging = Path(td) / "stage"; root.mkdir(); staging.mkdir(); make_project(root); (root / ".research/objects").mkdir(); (root / ".research/objects/new.json").write_text("different\n", encoding="utf-8"); plan = self.build_plan(root, staging)
            with self.assertRaises(V13Error): validate_plan(root, staging, plan)

    def test_commit_is_journaled_and_goal_gated(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "project"; staging = Path(td) / "stage"; journal = Path(td) / "journal"; root.mkdir(); staging.mkdir(); make_project(root); plan = self.build_plan(root, staging)
            with self.assertRaises(V13Error): commit(root, staging, plan, journal, "paused")
            result = commit(root, staging, plan, journal, "active"); self.assertEqual("committed", result["status"]); self.assertTrue((root / ".research/objects/new.json").is_file())

    def test_attempt_close_commit_rechecks_preflight_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            base_dir = Path(td); root = base_dir / "project"; root.mkdir(); make_project(root); activate(root)
            raw = base_dir / "raw"; raw.mkdir(); (raw / "candidate.json").write_bytes(canonical_json({"schema": "synthetic-candidate/v1"})); (raw / "outcome.md").write_bytes(b"Synthetic package.\n")
            finalized = base_dir / "finalized"
            final_result = finalize_package(raw, finalized, attempt_id="a0", package_root=".research/objects/a0-package", candidate_path="candidate.json")
            base_pointer = pointer(".research/authority/candidate-manifest.json", root)
            close = {"schema": "math-research-attempt-closing/v13", "attempt_id": "a0", "closing_reason": "candidate", "outcome": "candidate_found", "candidate": final_result["candidate"], "dependencies": final_result["dependencies"], "artifact_refs": final_result["artifact_refs"], "evidence_refs": ["synthetic"], "final_capsule": base_pointer, "budget_usage": budget(1), "semantic_reset_directive": None, "cannot_imply": ["outside synthetic scope"], "reopen_conditions": ["new evidence"]}
            transition = prepare_transition(root, "ATTEMPT_CLOSE", close)
            staging = base_dir / "stage"; package_stage = staging / "objects/a0-package"; package_stage.parent.mkdir(parents=True); shutil.copytree(finalized, package_stage)
            execution_path = staging / "heads/close.json"; execution_path.parent.mkdir(parents=True); execution_path.write_bytes(canonical_json(transition["candidate_execution_head"]))
            old = load_project(root); candidate_project = copy.deepcopy(old); candidate_project["generation"] += 1; candidate_project["execution_state_head"] = {"path": ".research/heads/close.json", "sha256": sha256_file(execution_path)}; (staging / "project.json").write_bytes(canonical_json(candidate_project))

            def build_current_plan() -> Path:
                writes = []
                for item in sorted((staging / "objects/a0-package").rglob("*")):
                    if item.is_file():
                        source = item.relative_to(staging).as_posix(); target = ".research/" + source
                        writes.append({"path": target, "source": source, "sha256": sha256_file(item), "immutable": True, "expected_old_sha256": None})
                writes.append({"path": ".research/heads/close.json", "source": "heads/close.json", "sha256": sha256_file(execution_path), "immutable": True, "expected_old_sha256": None})
                writes.append({"path": "project.json", "source": "project.json", "sha256": sha256_file(staging / "project.json"), "immutable": False, "expected_old_sha256": sha256_file(root / "project.json")})
                payload = {"schema": "math-research-commit-plan/v13", "expected_project_head_sha256": sha256_file(root / "project.json"), "expected_execution_head_sha256": old["execution_state_head"]["sha256"], "expected_research_authority_head_sha256": old["research_authority_head"]["sha256"], "staging_inventory_sha256": sha256_bytes(canonical_json(inventory(staging))), "writes": writes}
                plan = {**payload, "plan_sha256": sha256_bytes(canonical_json(payload))}; path = base_dir / "closing-plan.json"; path.write_bytes(canonical_json(plan)); return path

            self.assertTrue(validate_plan(root, staging, build_current_plan())["ok"])
            receipt_path = package_stage / "attempt-package-preflight.json"; receipt = json.loads(receipt_path.read_text(encoding="utf-8")); receipt["status"] = "FAIL"; receipt_path.write_bytes(canonical_json(receipt))
            with self.assertRaises(V13Error):
                validate_plan(root, staging, build_current_plan())

    def test_rollback_never_overwrites_concurrent_change(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "project"; staging = Path(td) / "stage"; journal = Path(td) / "journal"; root.mkdir(); staging.mkdir(); make_project(root); plan = self.build_plan(root, staging); real_replace = commit_harness.os.replace
            def interference(src, dst):
                dst_path = Path(dst)
                if dst_path == root / "project.json" and ".v13tmp-" in Path(src).name:
                    (root / ".research/objects/new.json").write_text("external change\n", encoding="utf-8"); raise OSError("injected")
                return real_replace(src, dst)
            with mock.patch.object(commit_harness.os, "replace", side_effect=interference):
                with self.assertRaises(OSError): commit(root, staging, plan, journal, "active")
            self.assertEqual("external change\n", (root / ".research/objects/new.json").read_text(encoding="utf-8")); journals = list(journal.glob("journal-*.json")); self.assertEqual("recovery_required", json.loads(journals[0].read_text(encoding="utf-8"))["status"])


class StaticContractTests(unittest.TestCase):
    def test_active_map_contract_has_landscape_name_and_no_future_command_name(self):
        text = (SKILL_ROOT / "references/research-map-protocol-v1.md").read_text(encoding="utf-8")
        self.assertIn("40-路线景观与重排条件.md", text); self.assertNotIn("40-当前候选路线与下一步.md", text)

    def test_final_contract_has_no_post_final_acknowledgement_write(self):
        for rel in ("SKILL.md", "references/persistence-contract-v13.md", "references/state-machine-v13.md", "references/terminology.md"):
            text = (SKILL_ROOT / rel).read_text(encoding="utf-8")
            self.assertNotIn("acknowledgement may clear", text); self.assertNotIn("acknowledgement 可清", text)


class MigrationHarnessTests(unittest.TestCase):
    def test_project_local_adapter_is_hash_pinned_and_json_bound(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            adapter = root / "adapter.py"
            adapter.write_text(
                "import json,sys\nprint(json.dumps({'action':sys.argv[1],'args':sys.argv[2:]}))\n",
                encoding="utf-8",
                newline="\n",
            )
            digest = sha256_file(adapter)
            result = invoke_adapter(adapter, digest, "prepare", ["--source", "synthetic"])
            self.assertEqual("math-research-v12-to-v13-adapter-receipt/v1", result["schema"])
            self.assertEqual("prepare", result["result"]["action"])

    def test_project_local_adapter_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            adapter = Path(td) / "adapter.py"
            adapter.write_text("print('{}')\n", encoding="utf-8", newline="\n")
            with self.assertRaises(MigrationError) as caught:
                invoke_adapter(adapter, "0" * 64, "prepare", [])
            self.assertEqual("adapter_hash_mismatch", caught.exception.code)


if __name__ == "__main__":
    unittest.main()
