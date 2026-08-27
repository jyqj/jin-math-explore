#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("math_research_migrate_v8_to_v10", HERE / "math_research_migrate_v8_to_v10.py")
mig = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mig)
mr = mig.mr


def dump(path: Path, value: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(mr.canonical_bytes(value))
    return mr.sha_file(path)


def text(path: Path, value: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")
    return mr.sha_file(path)


def ptr(root: Path, path: Path) -> dict[str, str]:
    return {"path": path.relative_to(root).as_posix(), "sha256": mr.sha_file(path)}


class Fixture:
    def __init__(self, base: Path):
        self.base = base
        self.v8 = base / "project-v8"
        self.v10 = base / "project-v10"
        self.stage = base / "stage"
        self.v8.mkdir()
        problem = self.v8 / "state/problem.md"
        text(problem, "Synthetic problem.\n")
        policy = {
            "schema_version": 3,
            "protocol": "math-research-cycle-policy/v3",
            "total_round_budget": 12,
            "attempt_budget": 8,
            "audit_interval_attempts": 4,
            "max_route_family_attempts_per_cycle": 2,
            "max_repair_batches_per_attempt": 1,
            "allowed_worker_tools": ["shell_command"],
            "max_ticket_tool_calls": 8,
            "max_ticket_output_bytes": 4096,
            "audit_roles": ["skeptic_quantifiers", "skeptic_strategy", "theory_tool_scout"],
        }
        contract_text = "---\nprotocol_version: v8\n---\n\n<!-- math-research-cycle-policy\n" + json.dumps(policy, separators=(",", ":")) + "\n-->\n"
        contract = self.v8 / "contracts/contract-v8.md"
        text(contract, contract_text)
        contract_binding = mig._normalized_text_hash(contract)

        paper = self.v8 / "assets/paper.pdf"
        paper.parent.mkdir(parents=True)
        paper.write_bytes(b"%PDF synthetic\n")
        registry = {
            "schema": "math-research-asset-registry/v1",
            "project_id": "proj",
            "registry_id": "registry-1",
            "created_at_utc": "2026-08-13T00:00:00Z",
            "assets": [{
                "asset_id": "paper-1", "kind": "paper", "title": "Synthetic paper", "origin": "external",
                "creators": [{"type": "person", "name": "Author", "role": "author"}],
                "source": {"locator": "https://example.test/paper", "identifier": "paper-1", "version": "v1", "upstream_commit": None, "acquired_at_utc": "2026-08-13T00:00:00Z"},
                "local_artifacts": [{"role": "paper_pdf", "path": "assets/paper.pdf", "sha256": mr.sha_file(paper), "bytes": paper.stat().st_size}],
                "license": {"status": "unknown", "identifier": None, "license_artifact": None, "redistribution": "private_only"},
                "citation": {"required": True, "key": "Author2026", "text": "Author (2026)", "bibtex": "@article{Author2026,title={Synthetic paper},author={Author}}"},
                "supported_claims": ["Synthetic claim."],
                "usage": {"entrypoints": [], "environment": "PDF reader", "verification": "fixture"},
                "limitations": ["fixture"], "export": {"mother_bundle": True, "paper_support_bundle": True},
            }],
        }
        ledger = {"schema": "math-research-contribution-ledger/v1", "project_id": "proj", "ledger_id": "ledger-1", "created_at_utc": "2026-08-13T00:00:00Z", "contributions": []}
        export = {"schema": "math-research-export-policy/v1", "project_id": "proj", "default_visibility": "private", "scan_roots": ["assets"], "scan_exclusions": [], "profiles": {"mother_bundle": {"visibility": "private", "description": "full"}, "paper_support_bundle": {"visibility": "private", "description": "paper"}}, "created_at_utc": "2026-08-13T00:00:00Z"}
        registry_path = self.v8 / "state/assets/registry.json"; dump(registry_path, registry)
        ledger_path = self.v8 / "state/assets/ledger.json"; dump(ledger_path, ledger)
        export_path = self.v8 / "state/assets/export.json"; dump(export_path, export)
        index = {"schema": "math-research-asset-index/v1", "project_id": "proj", "authority": "auxiliary_non_authoritative", "asset_registry": ptr(self.v8, registry_path), "contribution_ledger": ptr(self.v8, ledger_path), "export_policy": ptr(self.v8, export_path), "created_at_utc": "2026-08-13T00:00:00Z"}
        index_path = self.v8 / "state/assets/index.json"; dump(index_path, index)

        frozen_ticket = self.v8 / "runs/run-1/tickets/seed.json"
        dump(frozen_ticket, {"schema": "synthetic-v8-ticket", "id": "seed"})
        event = self.v8 / "state/project-events/g0003.json"
        event_value = {"schema": "math-research-project-event/v8", "project_id": "proj", "control_generation": 3, "referenced_artifacts": [ptr(self.v8, index_path)]}
        dump(event, event_value)
        checkpoint = self.v8 / "state/generations/g0003/checkpoint.json"
        counters = {"attempt_count": 2, "audit_count": 1, "total_round_count": 3, "attempts_since_last_audit": 1, "audit_due": False}
        contract_pointer = {"path": "contracts/contract-v8.md", "version": "v8", "binding_sha256": contract_binding}
        run = {"id": "run-1", "path": "runs/run-1", "status": "preparing"}
        checkpoint_value = {
            "schema": "math-research-checkpoint/v8", "project_id": "proj", "control_generation": 3,
            "contract": contract_pointer, "run": run, "problem_statement_sha256": mr.sha_file(problem),
            "host_goal": {"thread_id_available": True, "thread_id": "thread", "objective_raw_sha256": "1" * 64},
            "host_binding_head": {"path": "runs/run-1/host.json", "sha256": "2" * 64},
            "counters": counters,
            "current_lifecycle": {"kind": "frozen_ticket", "id": "seed", **ptr(self.v8, frozen_ticket)},
            "successor": None, "completion_ready": False, "pending_goal_update": False,
            "last_run_event": {"id": "event", "sha256": mr.sha_file(event)}, "updated_at_utc": "2026-08-13T00:00:00Z",
        }
        dump(checkpoint, checkpoint_value)
        head = {
            "schema": "math-research-project/v8", "project_id": "proj", "project_identity_sha256": "3" * 64,
            "problem_statement_sha256": mr.sha_file(problem), "control_generation": 3,
            "active_checkpoint": {**ptr(self.v8, checkpoint), "control_generation": 3},
            "goal_host_state": {"path": "state/generations/g0003/goal.json", "sha256": "4" * 64, "control_generation": 3},
            "project_event_head": {**ptr(self.v8, event), "control_generation": 3},
            "host_binding_head": {"path": "runs/run-1/host.json", "sha256": "2" * 64, "control_generation": 2},
            "active_contract": contract_pointer, "active_run": run, "legacy_successor": None,
        }
        dump(self.v8 / "project.json", head)
        self.problem = problem
        self.contract = contract
        self.inspection = mig.inspect_v8(self.v8)
        self.bootstrap = self._bootstrap()
        self.bootstrap_path = base / "bootstrap.json"
        dump(self.bootstrap_path, self.bootstrap)

    def _bootstrap(self) -> dict:
        run = "run-2"
        route = {
            "schema": "math-research-route-card/v10", "route_id": "route-new", "status": "active",
            "core_proof_object": "new global estimate", "proof_direction": "dual_separation",
            "quantifier_strategy": "fixed-parameter signed estimate", "mechanism_family_id": "new-family",
            "ancestor_route_ids": [], "coverage_bridge": {"status": "working", "statement": "Bridge the estimate to the target.", "test": "Prove the fixed-parameter implication."},
            "forbidden_family_relationship": "Distinct from frozen predecessor families.", "non_renaming_reason": "Uses a new proof object.",
            "special_family": False, "created_at_utc": "2026-08-13T00:00:00Z",
        }
        capsule = {
            "schema": "math-research-continuity-capsule/v1", "project_id": "proj", "run_id": run, "generation": 1,
            "target_sha256": self.inspection["head_sha256"], "proof_spine": [], "open_bottlenecks": ["Bridge the estimate."],
            "live_routes": ["route-new"], "rejected_routes": [], "quarantined_routes": [], "forbidden_families": [],
            "synthesis_candidates": [], "required_full_artifacts": [ptr(self.v8, self.problem), ptr(self.v8, self.contract)],
            "route_reset_directive": {"required": False, "trigger": "none", "forbidden_mechanism_family_ids": [], "minimum_distinct_cards": 2, "same_family_ceiling": 2},
            "updated_at_utc": "2026-08-13T00:00:00Z",
        }
        ticket = {
            "schema": "math-research-ticket/v10", "ticket_id": "ticket-new", "role": "attempt", "initial_lifecycle": "planned",
            "source_requirements": [{"id": "problem", "role": "task_contract", "required": True}, {"id": "contract", "role": "task_contract", "required": True}],
            "input_artifacts": [{"id": "problem", "role": "task_contract", **ptr(self.v8, self.problem)}, {"id": "contract", "role": "task_contract", **ptr(self.v8, self.contract)}],
            "allowed_reads": ["state/problem.md", "contracts/contract-v8.md"], "writable_staging_path": "placeholder",
            "decision_question": "Can the new estimate close the inherited bottleneck?", "allowed_tools": ["shell_command"],
            "resource_caps": {"child_agents": 0, "tool_calls": 8, "runtime_minutes": 10, "max_output_bytes": 4096},
            "required_outputs": ["solver_report"],
            "failure_return": {"schema": "math-research-ticket-failure/v1", "required_fields": ["status", "failed_step", "reason", "partial_artifact_hashes", "reopen_condition"]},
            "continuity_capsule": {"path": "placeholder", "sha256": "0" * 64}, "route_card": {"path": "placeholder", "sha256": "0" * 64},
            "persistent_lead": {"lead_id": "lead-new", "mode": "new", "previous_ticket_id": None},
            "attempt_scope": {"attempt_kind": "route_discovery", "target_sha256": self.inspection["head_sha256"], "route_family_id": "new-family", "proof_object": "new global estimate", "quantifier_strategy": "fixed-parameter signed estimate", "evidence_standard": "independent exact verification", "resource_envelope_sha256": self.inspection["resource_envelope_sha256"]},
        }
        return {
            "schema": "math-research-v8-incremental-migration-bootstrap/v10", "successor_run_id": run,
            "initial_ticket": ticket, "initial_capsule": capsule, "initial_route_card": route,
            "copy_artifacts": [{"source_path": "state/problem.md", "target_path": "state/problem.md", "sha256": mr.sha_file(self.problem)}],
            "occurred_at_utc": "2026-08-13T00:00:00Z",
        }


class MigrationTests(unittest.TestCase):
    def test_additive_migration_preserves_counters_assets_and_freezes_v8(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(Path(td))
            prepared = mig.prepare(f.v8, f.v10, f.bootstrap_path, f.stage)
            frozen = mig.freeze(f.v8, Path(prepared["plan_path"]))
            self.assertTrue(frozen["frozen"])
            committed = mr.commit_plan(Path(prepared["plan_path"]), "active")
            self.assertTrue(committed["committed"])
            verified = mig.verify(f.v8, f.v10, Path(prepared["plan_path"]))
            self.assertEqual(verified["cumulative_counters"]["attempt_count"], 2)
            self.assertEqual(verified["remaining_budgets"], {"attempt_budget": 6, "total_round_budget": 9})
            self.assertIsNotNone(verified["asset_index"])
            startup = mr.startup(f.v8, "Full", "active")
            self.assertEqual(startup["classification"], "v8_migrated_frozen")
            self.assertTrue(startup["successor_ready"])

    def test_attempt_start_rejected_until_predecessor_freeze_exists(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(Path(td))
            prepared = mig.prepare(f.v8, f.v10, f.bootstrap_path, f.stage)
            mr.commit_plan(Path(prepared["plan_path"]), "active")
            head, state, _, _, _ = mr.load_v10_project(f.v10, "Full")
            ticket = state["current_ticket"]
            payload = {"schema": "math-research-transition-payload/v10", "attempt_id": "attempt-new", "attempt_kind": "route_discovery", "ticket": {"path": ticket["path"], "sha256": ticket["sha256"]}, "occurred_at_utc": "2026-08-13T00:01:00Z"}
            with self.assertRaises(mr.ResearchError) as caught:
                mr.apply_transition(f.v10, state, "ATTEMPT_START", payload, head["control_generation"] + 1)
            self.assertEqual(caught.exception.code, "predecessor_not_frozen")

    def test_freeze_rejects_changed_v8_head(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(Path(td))
            prepared = mig.prepare(f.v8, f.v10, f.bootstrap_path, f.stage)
            head = json.loads((f.v8 / "project.json").read_text(encoding="utf-8"))
            head["control_generation"] = 4
            dump(f.v8 / "project.json", head)
            with self.assertRaises(mr.ResearchError) as caught:
                mig.freeze(f.v8, Path(prepared["plan_path"]))
            self.assertIn(caught.exception.code, {"cas_conflict", "v8_head_invalid"})

    def test_prepare_rejects_existing_successor(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(Path(td))
            f.v10.mkdir()
            dump(f.v10 / "project.json", {"schema": "other"})
            with self.assertRaises(mr.ResearchError) as caught:
                mig.prepare(f.v8, f.v10, f.bootstrap_path, f.stage)
            self.assertEqual(caught.exception.code, "successor_exists")

    def test_official_v8_writer_rejects_freeze_marker(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(Path(td))
            prepared = mig.prepare(f.v8, f.v10, f.bootstrap_path, f.stage)
            mig.freeze(f.v8, Path(prepared["plan_path"]))
            result = subprocess.run([
                "pwsh", "-NoProfile", "-File", str(HERE / "commit_math_research_head_v8.ps1"),
                "-ProjectDirectory", str(f.v8), "-CandidateHeadFile", str(f.v8 / "missing.json"),
                "-ExpectedOldSha256", mr.sha_file(f.v8 / "project.json"), "-ExpectedOldControlGeneration", "3", "-ExpectedNewControlGeneration", "4",
            ], text=True, capture_output=True, encoding="utf-8")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("v8_migrated_frozen", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
