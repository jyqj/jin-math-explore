#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("math_research_state_v10.py")
SPEC = importlib.util.spec_from_file_location("math_research_state_v10", MODULE_PATH)
mr = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mr)


def write_json(path: Path, value: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(mr.canonical_bytes(value))
    return mr.sha_file(path)


def write_text(path: Path, value: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")
    return mr.sha_file(path)


def ptr(path: Path, root: Path) -> dict[str, str]:
    return {"path": path.relative_to(root).as_posix(), "sha256": mr.sha_file(path)}


class V10Fixture:
    def __init__(self, base: Path):
        self.base = base
        self.predecessor = base / "predecessor"
        self.project = base / "successor"
        self.stage = base / "stage-successor"
        self.predecessor.mkdir()
        self.project.mkdir()
        write_json(self.predecessor / "project.json", {"schema": "math-research-project/v8", "project_id": "proj-1", "control_generation": 7})
        problem = self.project / "inputs/problem.md"
        contract = self.project / "contracts/contract-v10.md"
        write_text(problem, "Synthetic mathematical problem.\n")
        write_text(contract, "Synthetic frozen contract.\n")
        self.route_path = self.project / "runs/run-new/routes/route-1.json"
        self.route = {
            "schema": "math-research-route-card/v10",
            "route_id": "route-1",
            "status": "active",
            "core_proof_object": "synthetic primal object",
            "proof_direction": "explicit_construction",
            "quantifier_strategy": "construct one witness for every frozen parameter",
            "mechanism_family_id": "family-1",
            "ancestor_route_ids": [],
            "coverage_bridge": {"status": "verified", "statement": "The route covers the frozen domain.", "test": "Check every quantified parameter."},
            "forbidden_family_relationship": "No forbidden family is reused.",
            "non_renaming_reason": "The proof object and quantifier mechanism are explicit.",
            "special_family": False,
            "created_at_utc": "2026-08-10T12:00:00Z",
        }
        write_json(self.route_path, self.route)
        self.capsule_path = self.project / "runs/run-new/continuity/capsule-g0001.json"
        self.capsule = {
            "schema": "math-research-continuity-capsule/v1",
            "project_id": "proj-1",
            "run_id": "run-new",
            "generation": 1,
            "target_sha256": "1" * 64,
            "proof_spine": [],
            "open_bottlenecks": ["Build the frozen witness."],
            "live_routes": ["route-1"],
            "rejected_routes": [],
            "quarantined_routes": [],
            "forbidden_families": [],
            "synthesis_candidates": [],
            "required_full_artifacts": [ptr(problem, self.project), ptr(contract, self.project)],
            "route_reset_directive": {"required": False, "trigger": "none", "forbidden_mechanism_family_ids": [], "minimum_distinct_cards": 2, "same_family_ceiling": 2},
            "updated_at_utc": "2026-08-10T12:00:00Z",
        }
        write_json(self.capsule_path, self.capsule)
        self.ticket = self.make_ticket("ticket-1", problem, contract)
        h = "1" * 64
        self.spec = {
            "schema": "math-research-successor-spec/v10",
            "predecessor": {
                "project_id": "proj-1",
                "run_id": "run-old",
                "head_sha256": mr.sha_file(self.predecessor / "project.json"),
                "final_status": "budget_exhausted",
                "envelope_sha256": h,
                "permission_envelope_sha256": "2" * 64,
                "resource_envelope_sha256": "3" * 64,
                "remaining_attempt_budget": 4,
                "remaining_total_round_budget": 8,
            },
            "successor": {
                "project_id": "proj-1",
                "run_id": "run-new",
                "envelope_sha256": h,
                "permission_envelope_sha256": "2" * 64,
                "resource_envelope_sha256": "3" * 64,
                "budgets": {"attempt_budget": 4, "total_round_budget": 8},
            },
            "reason": "schema_upgrade",
            "cumulative_counters": {"attempt_count": 3, "audit_count": 1, "total_round_count": 4, "attempts_since_last_audit": 1},
            "initial_ticket": self.ticket,
            "initial_capsule": ptr(self.capsule_path, self.project),
            "initial_route_card": ptr(self.route_path, self.project),
            "occurred_at_utc": "2026-08-10T12:00:00.000000Z",
        }
        self.spec_path = self.base / "successor-spec.json"
        write_json(self.spec_path, self.spec)

    def make_ticket(self, ticket_id: str, problem: Path | None = None, contract: Path | None = None) -> dict:
        problem = problem or self.project / "inputs/problem.md"
        contract = contract or self.project / "contracts/contract-v10.md"
        return {
            "schema": "math-research-ticket/v10",
            "ticket_id": ticket_id,
            "role": "attempt",
            "initial_lifecycle": "planned",
            "source_requirements": [
                {"id": "problem", "role": "task_contract", "required": True},
                {"id": "contract", "role": "task_contract", "required": True},
                {"id": "capsule", "role": "continuity_capsule", "required": True},
                {"id": "route", "role": "route_card", "required": True},
            ],
            "input_artifacts": [
                {"id": "problem", "role": "task_contract", **ptr(problem, self.project)},
                {"id": "contract", "role": "task_contract", **ptr(contract, self.project)},
                {"id": "capsule", "role": "continuity_capsule", **ptr(self.capsule_path, self.project)},
                {"id": "route", "role": "route_card", **ptr(self.route_path, self.project)},
            ],
            "allowed_reads": [problem.relative_to(self.project).as_posix(), contract.relative_to(self.project).as_posix(), self.capsule_path.relative_to(self.project).as_posix(), self.route_path.relative_to(self.project).as_posix()],
            "writable_staging_path": f"runs/run-new/staging/{ticket_id}/solver",
            "decision_question": "Does the synthetic route meet its frozen signal?",
            "allowed_tools": ["shell_command"],
            "resource_caps": {"child_agents": 1, "tool_calls": 4, "runtime_minutes": 10, "max_output_bytes": 4096},
            "required_outputs": ["solver_report"],
            "failure_return": {"schema": "math-research-ticket-failure/v1", "required_fields": ["status", "failed_step", "reason", "partial_artifact_hashes", "reopen_condition"]},
            "continuity_capsule": ptr(self.capsule_path, self.project),
            "route_card": ptr(self.route_path, self.project),
            "persistent_lead": {"lead_id": "lead-1", "mode": "new", "previous_ticket_id": None},
            "attempt_scope": {"attempt_kind": "route_execution", "target_sha256": "1" * 64, "route_family_id": "family-1", "proof_object": "synthetic primal object", "quantifier_strategy": "construct one witness for every frozen parameter", "evidence_standard": "independent exact verification", "resource_envelope_sha256": "3" * 64},
        }

    def create(self) -> dict:
        prepared = mr.prepare_successor(self.predecessor, self.project, self.spec_path, self.stage)
        committed = mr.commit_plan(Path(prepared["plan_path"]), "active")
        assert committed["committed"]
        return prepared

    def payload(self, name: str, value: dict) -> Path:
        path = self.base / f"{name}.json"
        write_json(path, value)
        return path

    def topology_receipt(self, ticket_pointer: dict[str, str]) -> dict[str, str]:
        head = json.loads((self.project / "project.json").read_text(encoding="utf-8"))
        state_path = self.project / head["state"]["path"]
        state = json.loads(state_path.read_text(encoding="utf-8"))
        ticket_path = self.project / ticket_pointer["path"]
        ticket = json.loads(ticket_path.read_text(encoding="utf-8"))
        descriptor_worker = {
            "schema": "math-research-execution-topology-descriptor/v1",
            "role": "worker",
            "transport": "synthetic-direct",
            "execution_workspace_root": str(self.project.resolve()),
            "runner": "unit-test",
            "sandbox_mode": "workspace-write",
            "runner_arguments": ["-C", str(self.project.resolve())],
        }
        descriptor_publisher = {**descriptor_worker, "role": "publisher"}
        descriptor_consumer = {**descriptor_worker, "role": "consumer", "transport": "synthetic-desktop-consumer"}
        topology = lambda value: {"descriptor": value, "sha256": mr.sha_bytes(mr.canonical_bytes(value))}
        staging = ticket["writable_staging_path"]
        receipt_path = self.project / staging / f"topology-{time.time_ns()}.json"
        receipt = {
            "schema": "math-research-execution-topology-receipt/v1",
            "status": "ready_for_attempt_start",
            "receipt_id": f"topology-{time.time_ns()}",
            "project_id": state["project_id"],
            "run_id": state["active_run"]["id"],
            "control_generation": state["control_generation"],
            "project_head": {"path": "project.json", "sha256": mr.sha_file(self.project / "project.json")},
            "ticket": {**ticket_pointer, "ticket_id": ticket["ticket_id"]},
            "inputs": [{"path": item["path"], "sha256": item["sha256"]} for item in ticket["input_artifacts"]],
            "staging_root": staging,
            "worker_observation": {"topology": topology(descriptor_worker), "probe_relative_path": staging + "/synthetic-probe.json", "probe_sha256": "4" * 64, "nonce_sha256": "5" * 64, "worker_receipt_sha256": "6" * 64},
            "readback_observation": {"topology": topology(descriptor_publisher), "independent_reopen": True, "project_head_sha256": mr.sha_file(self.project / "project.json"), "ticket_sha256": ticket_pointer["sha256"], "probe_sha256": "4" * 64, "checked_at_utc": "2098-01-01T00:00:00Z"},
            "consumer_principal": "synthetic-consumer",
            "consumer_observation": {"topology": topology(descriptor_consumer), "principal": "synthetic-consumer", "independent_recursive_reopen": True, "project_tree_sha256": "7" * 64, "directory_count": 2, "file_count": 3, "publisher_probe_relative_path": ".math-research-consumer-probe-synthetic/probe.json", "publisher_probe_sha256": "8" * 64, "checked_at_utc": "2098-01-01T00:00:00Z"},
            "issued_at_utc": "2026-01-01T00:00:00Z",
            "expires_at_utc": "2099-01-01T00:00:00Z",
        }
        write_json(receipt_path, receipt)
        return ptr(receipt_path, self.project)

    def transition(self, name: str, payload: dict, stage_name: str | None = None) -> dict:
        if name == "ATTEMPT_START" and "execution_topology_receipt" not in payload:
            payload = copy.deepcopy(payload)
            payload["execution_topology_receipt"] = self.topology_receipt(payload["ticket"])
        payload_path = self.payload(f"payload-{name.lower()}-{time.time_ns()}", payload)
        out = self.base / (stage_name or f"stage-{name.lower()}-{time.time_ns()}")
        result = mr.prepare_transition(self.project, name, payload_path, out, "Auto")
        mr.commit_plan(Path(result["plan_path"]), "active")
        return result


class MathResearchV10Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.fx = V10Fixture(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def assertCode(self, code: str, func, *args, **kwargs):
        with self.assertRaises(mr.ResearchError) as ctx:
            func(*args, **kwargs)
        self.assertEqual(code, ctx.exception.code)

    def test_successor_preserves_predecessor_bytes(self):
        before = (self.fx.predecessor / "project.json").read_bytes()
        self.fx.create()
        self.assertEqual(before, (self.fx.predecessor / "project.json").read_bytes())
        self.assertEqual("v10_ready", mr.startup(self.fx.project, "Auto", None)["classification"])

    def test_successor_rejects_envelope_change(self):
        spec = copy.deepcopy(self.fx.spec)
        spec["successor"]["permission_envelope_sha256"] = "9" * 64
        path = self.fx.payload("bad-successor", spec)
        self.assertCode("successor_envelope_expanded", mr.prepare_successor, self.fx.predecessor, self.fx.project, path, self.root / "bad-stage")

    def test_successor_rejects_budget_expansion(self):
        spec = copy.deepcopy(self.fx.spec)
        spec["successor"]["budgets"]["attempt_budget"] = 5
        path = self.fx.payload("bad-budget", spec)
        self.assertCode("successor_envelope_expanded", mr.prepare_successor, self.fx.predecessor, self.fx.project, path, self.root / "bad-stage")

    def test_commit_requires_active_goal(self):
        prepared = mr.prepare_successor(self.fx.predecessor, self.fx.project, self.fx.spec_path, self.fx.stage)
        self.assertCode("goal_not_active", mr.commit_plan, Path(prepared["plan_path"]), "paused")

    def test_commit_is_idempotent(self):
        prepared = mr.prepare_successor(self.fx.predecessor, self.fx.project, self.fx.spec_path, self.fx.stage)
        first = mr.commit_plan(Path(prepared["plan_path"]), "active")
        second = mr.commit_plan(Path(prepared["plan_path"]), "active")
        self.assertFalse(first["reused"])
        self.assertTrue(second["reused"])

    def test_startup_delegates_v8(self):
        result = mr.startup(self.fx.predecessor, "Auto", "active")
        self.assertEqual("delegate_startup_v4", result["classification"])

    def test_startup_v5_delegates_to_v4_with_legacy_parameter_name(self):
        pwsh = shutil.which("pwsh")
        if not pwsh:
            self.skipTest("pwsh is unavailable")
        shim_dir = Path(self.temp.name) / "startup-v5-shim"
        shim_dir.mkdir()
        shutil.copy2(MODULE_PATH.with_name("invoke_math_research_startup_v5.ps1"), shim_dir)
        (shim_dir / "math_research_state_v10.py").write_text(
            "import json\nprint(json.dumps({'ok': True, 'data': {'classification': 'delegate_startup_v4'}}))\n",
            encoding="utf-8",
        )
        (shim_dir / "invoke_math_research_startup_v4.ps1").write_text(
            "param([Parameter(Mandatory=$true)][string]$ProjectPath,"
            "[Parameter(Mandatory=$true)][string]$AuditMode,"
            "[Parameter(Mandatory=$true)][string]$GoalStatus)\n"
            "[ordered]@{project_directory=$ProjectPath;goal_status=$GoalStatus}|ConvertTo-Json\n",
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                pwsh,
                "-NoProfile",
                "-File",
                str(shim_dir / "invoke_math_research_startup_v5.ps1"),
                "-ProjectPath",
                str(self.fx.predecessor),
                "-AuditMode",
                "Auto",
                "-GoalStatus",
                "active",
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(str(self.fx.predecessor), payload["project_directory"])
        self.assertEqual("active", payload["goal_status"])

    def test_v10_ticket_missing_required_input(self):
        ticket = copy.deepcopy(self.fx.ticket)
        ticket["input_artifacts"] = ticket["input_artifacts"][:1]
        ticket["allowed_reads"] = ticket["allowed_reads"][:1]
        self.assertCode("ticket_input_incomplete", mr.validate_v10_ticket, ticket, self.fx.project)

    def test_v10_ticket_rejects_read_path_gap(self):
        ticket = copy.deepcopy(self.fx.ticket)
        ticket["allowed_reads"].append("inputs/unbound.md")
        self.assertCode("ticket_read_closure_failed", mr.validate_v10_ticket, ticket, self.fx.project)

    def _v8_ticket(self):
        problem = self.fx.project / "inputs/problem.md"
        req = self.fx.project / "inputs/source-requirements.json"
        requirements = {"schema": "math-research-source-requirements/v1", "requirements": [{"id": "problem", "role": "task_contract", "path": "inputs/problem.md", "sha256": mr.sha_file(problem), "required": True}]}
        write_json(req, requirements)
        wrapper = {
            "contract": {"path": "contracts/contract-v10.md", "version": 8, "binding_sha256": "4" * 64},
            "ticket": {
                "ticket_id": "legacy-ticket",
                "input_artifacts": [ptr(problem, self.fx.project), ptr(req, self.fx.project)],
                "filesystem_scope": {"read_paths": ["inputs/problem.md", "inputs/source-requirements.json", "contracts/contract-v10.md"], "writable_staging_path": "runs/run-old/staging/legacy-ticket/solver"},
            },
        }
        path = self.fx.project / "legacy-ticket.json"
        write_json(path, wrapper)
        return path, req

    def test_v8_preflight_passes_closed_inputs(self):
        ticket, req = self._v8_ticket()
        result = mr.preflight_v8(self.fx.project, ticket, req, None)
        self.assertEqual("none", result["worker_capsule"]["required_fork_turns"])

    def test_v8_preflight_missing_source_manifest_binding(self):
        ticket, req = self._v8_ticket()
        wrapper = mr.load_json(ticket)
        wrapper["ticket"]["input_artifacts"] = wrapper["ticket"]["input_artifacts"][:1]
        write_json(ticket, wrapper)
        self.assertCode("ticket_read_closure_failed", mr.preflight_v8, self.fx.project, ticket, req, None)

    def test_v8_access_log_out_of_scope_invalidates_return(self):
        ticket, req = self._v8_ticket()
        log = self.fx.project / "worker-access.json"
        write_json(log, {"schema": "math-research-worker-access-log/v1", "reads": ["inputs/secret.md"]})
        self.assertCode("worker_access_out_of_scope", mr.preflight_v8, self.fx.project, ticket, req, log)

    def test_attempt_start_increments_local_and_cumulative(self):
        self.fx.create()
        payload = {"schema": "math-research-transition-payload/v10", "attempt_id": "attempt-1", "attempt_kind": "route_execution", "ticket": {"path": "runs/run-new/tickets/ticket-1.json", "sha256": mr.sha_file(self.fx.project / "runs/run-new/tickets/ticket-1.json")}, "occurred_at_utc": "2026-08-10T12:01:00Z"}
        self.fx.transition("ATTEMPT_START", payload)
        _, state, _, _, _ = mr.load_v10_project(self.fx.project)
        self.assertEqual(1, state["counters"]["run_local"]["attempt_count"])
        self.assertEqual(4, state["counters"]["cumulative"]["attempt_count"])
        self.assertEqual("active", state["current_ticket"]["lifecycle"])

    def test_attempt_start_reserves_audit_round(self):
        self.fx.spec["successor"]["budgets"] = {"attempt_budget": 4, "total_round_budget": 1}
        write_json(self.fx.spec_path, self.fx.spec)
        self.fx.create()
        payload = {"schema": "math-research-transition-payload/v10", "attempt_id": "attempt-1", "attempt_kind": "route_execution", "ticket": {"path": "runs/run-new/tickets/ticket-1.json", "sha256": mr.sha_file(self.fx.project / "runs/run-new/tickets/ticket-1.json")}, "occurred_at_utc": "2026-08-10T12:01:00Z"}
        path = self.fx.payload("attempt-budget", payload)
        self.assertCode("budget_exhausted", mr.prepare_transition, self.fx.project, "ATTEMPT_START", path, self.root / "budget-stage", "Auto")

    def test_attempt_start_requires_topology_receipt_without_consuming_attempt(self):
        self.fx.create()
        before = (self.fx.project / "project.json").read_bytes()
        ticket = ptr(self.fx.project / "runs/run-new/tickets/ticket-1.json", self.fx.project)
        payload = {"schema": "math-research-transition-payload/v10", "attempt_id": "attempt-1", "attempt_kind": "route_execution", "ticket": ticket, "occurred_at_utc": "2026-08-10T12:01:00Z"}
        path = self.fx.payload("missing-topology", payload)
        self.assertCode("topology_receipt_required", mr.prepare_transition, self.fx.project, "ATTEMPT_START", path, self.root / "missing-topology-stage", "Auto")

    def test_attempt_start_rejects_receipt_without_consumer_observation(self):
        self.fx.create()
        before = (self.fx.project / "project.json").read_bytes()
        ticket = ptr(self.fx.project / "runs/run-new/tickets/ticket-1.json", self.fx.project)
        receipt_ptr = self.fx.topology_receipt(ticket)
        receipt_path = self.fx.project / receipt_ptr["path"]
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        del receipt["consumer_principal"]
        del receipt["consumer_observation"]
        write_json(receipt_path, receipt)
        payload = {"schema": "math-research-transition-payload/v10", "attempt_id": "attempt-1", "attempt_kind": "route_execution", "ticket": ticket, "execution_topology_receipt": ptr(receipt_path, self.fx.project), "occurred_at_utc": "2026-08-10T12:01:00Z"}
        path = self.fx.payload("missing-consumer-observation", payload)
        self.assertCode("schema_invalid", mr.prepare_transition, self.fx.project, "ATTEMPT_START", path, self.root / "missing-consumer-stage", "Auto")
        self.assertEqual(before, (self.fx.project / "project.json").read_bytes())

    def test_stale_topology_receipt_does_not_consume_attempt(self):
        self.fx.create()
        before = (self.fx.project / "project.json").read_bytes()
        ticket = ptr(self.fx.project / "runs/run-new/tickets/ticket-1.json", self.fx.project)
        receipt_ptr = self.fx.topology_receipt(ticket)
        receipt_path = self.fx.project / receipt_ptr["path"]
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["expires_at_utc"] = "2026-01-02T00:00:00Z"
        write_json(receipt_path, receipt)
        payload = {"schema": "math-research-transition-payload/v10", "attempt_id": "attempt-1", "attempt_kind": "route_execution", "ticket": ticket, "execution_topology_receipt": ptr(receipt_path, self.fx.project), "occurred_at_utc": "2026-08-10T12:01:00Z"}
        path = self.fx.payload("stale-topology", payload)
        self.assertCode("topology_receipt_stale", mr.prepare_transition, self.fx.project, "ATTEMPT_START", path, self.root / "stale-topology-stage", "Auto")
        self.assertEqual(before, (self.fx.project / "project.json").read_bytes())

    def test_attempt_start_kind_must_match_ticket_scope(self):
        self.fx.create()
        payload = {"schema": "math-research-transition-payload/v10", "attempt_id": "attempt-1", "attempt_kind": "candidate_revision", "ticket": {"path": "runs/run-new/tickets/ticket-1.json", "sha256": mr.sha_file(self.fx.project / "runs/run-new/tickets/ticket-1.json")}, "occurred_at_utc": "2026-08-10T12:01:00Z"}
        path = self.fx.payload("kind-mismatch", payload)
        self.assertCode("transition_invalid", mr.prepare_transition, self.fx.project, "ATTEMPT_START", path, self.root / "kind-mismatch-stage", "Auto")

    def _run_to_verifier(self):
        self.fx.create()
        ticket_pointer = {"path": "runs/run-new/tickets/ticket-1.json", "sha256": mr.sha_file(self.fx.project / "runs/run-new/tickets/ticket-1.json")}
        self.fx.transition("ATTEMPT_START", {"schema": "math-research-transition-payload/v10", "attempt_id": "attempt-1", "attempt_kind": "route_execution", "ticket": ticket_pointer, "occurred_at_utc": "2026-08-10T12:01:00Z"})
        solver = self.fx.project / "runs/run-new/attempts/attempt-1/solver-result.json"
        write_json(solver, {"schema": "synthetic-solver-result/v1", "status": "partial"})
        self.fx.transition("SOLVER_COMPLETE", {"schema": "math-research-transition-payload/v10", "solver_result": ptr(solver, self.fx.project), "occurred_at_utc": "2026-08-10T12:02:00Z"})
        partial = self.fx.project / "evidence/partial-1.md"
        write_text(partial, "Verified synthetic partial result.\n")
        completion = self.fx.project / "runs/run-new/attempts/attempt-1/verifier-completion.json"
        write_json(completion, {"schema": "math-research-verifier-completion/v10", "project_id": "proj-1", "run_id": "run-new", "attempt_id": "attempt-1", "ticket_id": "ticket-1", "verdict": "PASS", "candidate": None, "completed_at_utc": "2026-08-10T12:03:00Z"})
        evidence = [{"kind": "verified_partial", **ptr(partial, self.fx.project), "ticket_id": "ticket-1", "attempt_id": "attempt-1"}]
        self.fx.transition("VERIFIER_COMPLETE", {"schema": "math-research-transition-payload/v10", "verifier_completion": ptr(completion, self.fx.project), "evidence_items": evidence, "occurred_at_utc": "2026-08-10T12:03:00Z"})
        return evidence

    def test_verified_partial_survives_attempt_end(self):
        evidence = self._run_to_verifier()
        _, active_state, _, _, _ = mr.load_v10_project(self.fx.project)
        next_ticket = self.fx.make_ticket("ticket-2")
        next_ticket["attempt_scope"]["attempt_kind"] = "candidate_synthesis"
        next_path = self.fx.project / "runs/run-new/tickets/ticket-2.json"
        write_json(next_path, next_ticket)
        record = self.fx.project / "runs/run-new/attempts/attempt-1/attempt-record.json"
        write_json(record, {"schema": "math-research-attempt-record/v10", "project_id": "proj-1", "run_id": "run-new", "attempt_id": "attempt-1", "ticket_id": "ticket-1", "disposition": "no_candidate_with_evidence", "evidence": evidence, "verifier_completion": active_state["current_attempt"]["verifier_completion"], "completed_at_utc": "2026-08-10T12:04:00Z"})
        self.fx.transition("ATTEMPT_END", {"schema": "math-research-transition-payload/v10", "disposition": "no_candidate_with_evidence", "attempt_record": ptr(record, self.fx.project), "evidence_items": evidence, "next_ticket": ptr(next_path, self.fx.project), "occurred_at_utc": "2026-08-10T12:04:00Z"})
        _, state, _, _, _ = mr.load_v10_project(self.fx.project)
        self.assertIsNone(state["current_attempt"])
        self.assertEqual("ticket-2", state["current_ticket"]["id"])
        self.assertIn("verified_partial", {item["kind"] for item in state["evidence_items"]})

    def test_no_candidate_with_evidence_requires_partial(self):
        evidence = self._run_to_verifier()
        record = self.fx.project / "runs/run-new/attempts/attempt-1/attempt-record.json"
        _, active_state, _, _, _ = mr.load_v10_project(self.fx.project)
        write_json(record, {"schema": "math-research-attempt-record/v10", "project_id": "proj-1", "run_id": "run-new", "attempt_id": "attempt-1", "ticket_id": "ticket-1", "disposition": "no_candidate_with_evidence", "evidence": [], "verifier_completion": active_state["current_attempt"]["verifier_completion"], "completed_at_utc": "2026-08-10T12:04:00Z"})
        payload = {"schema": "math-research-transition-payload/v10", "disposition": "no_candidate_with_evidence", "attempt_record": ptr(record, self.fx.project), "evidence_items": [], "next_ticket": None, "occurred_at_utc": "2026-08-10T12:04:00Z"}
        path = self.fx.payload("bad-end", payload)
        self.assertCode("transition_invalid", mr.prepare_transition, self.fx.project, "ATTEMPT_END", path, self.root / "bad-end-stage", "Auto")

    def test_fail_verdict_cannot_publish_failure_boundary_evidence(self):
        self._start_active_attempt()
        solver = self.fx.project / "runs/run-new/attempts/attempt-1/solver-result.json"
        write_json(solver, {"schema": "synthetic-solver-result/v1", "status": "failed"})
        self.fx.transition("SOLVER_COMPLETE", {"schema": "math-research-transition-payload/v10", "solver_result": ptr(solver, self.fx.project), "occurred_at_utc": "2026-08-10T12:02:00Z"})
        boundary = self.fx.project / "evidence/unverified-boundary.md"
        write_text(boundary, "Unverified boundary.\n")
        completion = self.fx.project / "runs/run-new/attempts/attempt-1/fail-completion.json"
        write_json(completion, {"schema": "math-research-verifier-completion/v10", "project_id": "proj-1", "run_id": "run-new", "attempt_id": "attempt-1", "ticket_id": "ticket-1", "verdict": "FAIL", "candidate": None, "completed_at_utc": "2026-08-10T12:03:00Z"})
        evidence = [{"kind": "failure_boundary", **ptr(boundary, self.fx.project), "ticket_id": "ticket-1", "attempt_id": "attempt-1"}]
        payload = {"schema": "math-research-transition-payload/v10", "verifier_completion": ptr(completion, self.fx.project), "evidence_items": evidence, "occurred_at_utc": "2026-08-10T12:03:00Z"}
        path = self.fx.payload("fail-evidence", payload)
        self.assertCode("verification_required", mr.prepare_transition, self.fx.project, "VERIFIER_COMPLETE", path, self.root / "fail-evidence-stage", "Auto")

    def test_checkpoint_rejects_untyped_reference(self):
        self.fx.create()
        artifact = self.fx.project / "evidence/x.md"
        write_text(artifact, "x\n")
        payload = {"schema": "math-research-transition-payload/v10", "references": [{"kind": "arbitrary_blob", **ptr(artifact, self.fx.project), "attempt_id": None, "ticket_id": None}], "occurred_at_utc": "2026-08-10T12:05:00Z"}
        path = self.fx.payload("bad-checkpoint", payload)
        self.assertCode("reference_invalid", mr.prepare_transition, self.fx.project, "CHECKPOINT_COMMIT", path, self.root / "bad-checkpoint-stage", "Auto")

    def test_cas_conflict_rejects_second_plan(self):
        self.fx.create()
        payload1 = self.fx.payload("cp1", {"schema": "math-research-transition-payload/v10", "references": [], "occurred_at_utc": "2026-08-10T12:05:00Z"})
        payload2 = self.fx.payload("cp2", {"schema": "math-research-transition-payload/v10", "references": [], "occurred_at_utc": "2026-08-10T12:06:00Z"})
        p1 = mr.prepare_transition(self.fx.project, "CHECKPOINT_COMMIT", payload1, self.root / "stage-cp1", "Auto")
        p2 = mr.prepare_transition(self.fx.project, "CHECKPOINT_COMMIT", payload2, self.root / "stage-cp2", "Auto")
        mr.commit_plan(Path(p1["plan_path"]), "active")
        self.assertCode("cas_conflict", mr.commit_plan, Path(p2["plan_path"]), "active")

    def test_metadata_drift_escalates_to_full(self):
        self.fx.create()
        path = self.fx.project / "inputs/problem.md"
        stat = path.stat()
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))
        result = mr.startup(self.fx.project, "Auto", None)
        self.assertEqual("Full", result["audit_mode_used"])
        self.assertIn("metadata_drift_escalated_to_full", result["audit_notes"])

    def test_historical_hash_corruption_fails_full(self):
        self.fx.create()
        path = self.fx.project / "inputs/problem.md"
        path.write_text("tampered\n", encoding="utf-8")
        self.assertCode("artifact_hash_mismatch", mr.startup, self.fx.project, "Full", None)

    def test_unmanifested_authoritative_file_fails(self):
        self.fx.create()
        write_text(self.fx.project / "evidence/unbound.md", "unbound\n")
        self.assertCode("manifest_unexpected_file", mr.startup, self.fx.project, "Auto", None)

    def test_capsule_required_full_artifact_cannot_be_replaced_by_summary(self):
        ticket = copy.deepcopy(self.fx.ticket)
        ticket["source_requirements"][1]["required"] = False
        ticket["input_artifacts"] = [item for item in ticket["input_artifacts"] if item["id"] != "contract"]
        ticket["allowed_reads"] = [item for item in ticket["allowed_reads"] if item != "contracts/contract-v10.md"]
        self.assertCode("ticket_full_context_missing", mr.validate_v10_ticket, ticket, self.fx.project)

    def test_access_log_v2_allows_rechecking_own_staging_output(self):
        ticket_path = self.fx.project / "runs/run-new/tickets/preflight.json"
        write_json(ticket_path, self.fx.ticket)
        log = self.fx.project / "worker-access-v2.json"
        write_json(log, {
            "schema": "math-research-worker-access-log/v2",
            "input_reads": ["inputs/problem.md"],
            "staging_reads": ["runs/run-new/staging/ticket-1/solver/solver-report.md"],
        })
        result = mr.preflight_v10(self.fx.project, ticket_path, log)
        self.assertEqual(1, result["staging_read_count"])

    def test_access_log_v2_rejects_unbound_input(self):
        ticket_path = self.fx.project / "runs/run-new/tickets/preflight.json"
        write_json(ticket_path, self.fx.ticket)
        log = self.fx.project / "worker-access-v2.json"
        write_json(log, {"schema": "math-research-worker-access-log/v2", "input_reads": ["inputs/secret.md"], "staging_reads": []})
        self.assertCode("worker_access_out_of_scope", mr.preflight_v10, self.fx.project, ticket_path, log)

    def test_access_log_v2_rejects_staging_escape(self):
        ticket_path = self.fx.project / "runs/run-new/tickets/preflight.json"
        write_json(ticket_path, self.fx.ticket)
        log = self.fx.project / "worker-access-v2.json"
        write_json(log, {"schema": "math-research-worker-access-log/v2", "input_reads": [], "staging_reads": ["runs/run-new/staging/other-ticket/output.md"]})
        self.assertCode("worker_staging_escape", mr.preflight_v10, self.fx.project, ticket_path, log)

    def test_route_reset_assessment_triggers_on_user_ban(self):
        result = mr.assess_route_reset({
            "schema": "math-research-route-reset-assessment-input/v1",
            "explicit_user_ban": True,
            "consecutive_same_family_negative_attempts": 0,
            "consecutive_special_family_successes_without_bridge": 0,
            "strategy_overlap_detected": False,
            "same_family_attempt_count": 0,
            "same_family_ceiling": 2,
        })
        self.assertTrue(result["reset_required"])
        self.assertIn("explicit_user_ban", result["triggers"])

    def test_route_reset_assessment_triggers_after_two_same_family_failures(self):
        result = mr.assess_route_reset({
            "schema": "math-research-route-reset-assessment-input/v1",
            "explicit_user_ban": False,
            "consecutive_same_family_negative_attempts": 2,
            "consecutive_special_family_successes_without_bridge": 0,
            "strategy_overlap_detected": False,
            "same_family_attempt_count": 1,
            "same_family_ceiling": 3,
        })
        self.assertEqual(["same_family_negative_ceiling"], result["triggers"])

    def _trigger_active_reset(self):
        self._start_active_attempt()
        reset_capsule = copy.deepcopy(self.fx.capsule)
        reset_capsule["generation"] = 3
        reset_capsule["route_reset_directive"] = {"required": True, "trigger": "explicit_user_ban", "forbidden_mechanism_family_ids": ["family-1"], "minimum_distinct_cards": 2, "same_family_ceiling": 2}
        reset_capsule["updated_at_utc"] = "2026-08-10T12:04:00Z"
        reset_capsule_path = self.fx.project / "runs/run-new/continuity/capsule-g0003.json"
        write_json(reset_capsule_path, reset_capsule)
        self.fx.transition("RESEARCH_CHECKPOINT", {"schema": "math-research-transition-payload/v10", "capsule": ptr(reset_capsule_path, self.fx.project), "references": [], "checkpoint_reason": "route_internal_revision", "occurred_at_utc": "2026-08-10T12:04:00Z"})
        self.reset_capsule = reset_capsule
        self.reset_capsule_path = reset_capsule_path
        self.fx.transition("ROUTE_RESET_TRIGGER", {
            "schema": "math-research-transition-payload/v10",
            "assessment": {
                "schema": "math-research-route-reset-assessment-input/v1",
                "explicit_user_ban": True,
                "consecutive_same_family_negative_attempts": 0,
                "consecutive_special_family_successes_without_bridge": 0,
                "strategy_overlap_detected": False,
                "same_family_attempt_count": 1,
                "same_family_ceiling": 2,
            },
            "occurred_at_utc": "2026-08-10T12:05:00Z",
        })

    def test_route_reset_trigger_records_earliest_generation(self):
        self._trigger_active_reset()
        result = mr.startup(self.fx.project, "Auto", None)
        self.assertEqual(4, result["route_reset"]["trigger_generation"])
        self.assertEqual(["explicit_user_ban"], result["route_reset"]["triggers"])
        self.assertEqual("attempt-1", result["current_attempt_id"])
        self.assertEqual("ticket-1", result["current_ticket_id"])
        self.assertEqual("lead-1", result["lead_id"])
        self.assertEqual(1, result["checkpoint_count"])

    def test_route_reset_rejects_a_second_trigger_record(self):
        self._trigger_active_reset()
        payload = {
            "schema": "math-research-transition-payload/v10",
            "assessment": {
                "schema": "math-research-route-reset-assessment-input/v1",
                "explicit_user_ban": True,
                "consecutive_same_family_negative_attempts": 0,
                "consecutive_special_family_successes_without_bridge": 0,
                "strategy_overlap_detected": False,
                "same_family_attempt_count": 1,
                "same_family_ceiling": 2,
            },
            "occurred_at_utc": "2026-08-10T12:06:00Z",
        }
        path = self.fx.payload("duplicate-reset-trigger", payload)
        self.assertCode("route_reset_sequence_invalid", mr.prepare_transition, self.fx.project, "ROUTE_RESET_TRIGGER", path, self.root / "duplicate-reset-stage", "Auto")

    def test_route_reset_trigger_must_match_active_directive(self):
        self._start_active_attempt()
        reset_capsule = copy.deepcopy(self.fx.capsule)
        reset_capsule["generation"] = 3
        reset_capsule["route_reset_directive"] = {"required": True, "trigger": "explicit_user_ban", "forbidden_mechanism_family_ids": ["family-1"], "minimum_distinct_cards": 2, "same_family_ceiling": 2}
        reset_capsule["updated_at_utc"] = "2026-08-10T12:04:00Z"
        reset_capsule_path = self.fx.project / "runs/run-new/continuity/capsule-trigger-mismatch.json"
        write_json(reset_capsule_path, reset_capsule)
        self.fx.transition("RESEARCH_CHECKPOINT", {"schema": "math-research-transition-payload/v10", "capsule": ptr(reset_capsule_path, self.fx.project), "references": [], "checkpoint_reason": "route_internal_revision", "occurred_at_utc": "2026-08-10T12:04:00Z"})
        payload = {
            "schema": "math-research-transition-payload/v10",
            "assessment": {"schema": "math-research-route-reset-assessment-input/v1", "explicit_user_ban": False, "consecutive_same_family_negative_attempts": 2, "consecutive_special_family_successes_without_bridge": 0, "strategy_overlap_detected": False, "same_family_attempt_count": 1, "same_family_ceiling": 3},
            "occurred_at_utc": "2026-08-10T12:05:00Z",
        }
        path = self.fx.payload("trigger-directive-mismatch", payload)
        self.assertCode("route_reset_sequence_invalid", mr.prepare_transition, self.fx.project, "ROUTE_RESET_TRIGGER", path, self.root / "trigger-directive-mismatch-stage", "Auto")

    def test_triggered_attempt_cannot_close_before_portfolio_acceptance(self):
        self._trigger_active_reset()
        record = self.fx.project / "runs/run-new/attempts/attempt-1/reset-attempt-record.json"
        write_json(record, {"schema": "math-research-attempt-record/v10", "project_id": "proj-1", "run_id": "run-new", "attempt_id": "attempt-1", "ticket_id": "ticket-1", "disposition": "no_candidate", "evidence": [], "verifier_completion": None, "completed_at_utc": "2026-08-10T12:06:00Z"})
        payload = {"schema": "math-research-transition-payload/v10", "disposition": "no_candidate", "attempt_record": ptr(record, self.fx.project), "evidence_items": [], "next_ticket": None, "occurred_at_utc": "2026-08-10T12:06:00Z"}
        path = self.fx.payload("end-before-portfolio", payload)
        self.assertCode("route_reset_sequence_invalid", mr.prepare_transition, self.fx.project, "ATTEMPT_END", path, self.root / "end-before-portfolio-stage", "Auto")

    def test_portfolio_acceptance_binds_exactly_one_successor(self):
        self._trigger_active_reset()
        reset_capsule = self.reset_capsule
        route_a = self._route_variant("route-a", "family-a", "object-alpha", "quantifier-plan-alpha")
        route_a["status"] = "active"
        route_b = self._route_variant("route-b", "family-b", "object-beta", "quantifier-plan-beta")
        route_a_path = self.fx.project / "runs/run-new/routes/route-a.json"
        write_json(route_a_path, route_a)
        portfolio_path = self.fx.project / "runs/run-new/routes/portfolio-1.json"
        write_json(portfolio_path, {"schema": "math-research-route-portfolio/v10", "routes": [route_a, route_b], "created_at_utc": "2026-08-10T12:08:00Z"})
        successor_capsule = copy.deepcopy(reset_capsule)
        successor_capsule["generation"] = 5
        successor_capsule["live_routes"] = ["route-a"]
        successor_capsule["quarantined_routes"] = ["route-1"]
        successor_capsule["forbidden_families"] = ["family-1"]
        successor_capsule["route_reset_directive"] = {"required": False, "trigger": "none", "forbidden_mechanism_family_ids": [], "minimum_distinct_cards": 2, "same_family_ceiling": 2}
        successor_capsule["updated_at_utc"] = "2026-08-10T12:08:00Z"
        successor_capsule_path = self.fx.project / "runs/run-new/continuity/capsule-g0005.json"
        write_json(successor_capsule_path, successor_capsule)
        self.fx.transition("ROUTE_PORTFOLIO_ACCEPT", {"schema": "math-research-transition-payload/v10", "portfolio": ptr(portfolio_path, self.fx.project), "selected_route": ptr(route_a_path, self.fx.project), "successor_capsule": ptr(successor_capsule_path, self.fx.project), "occurred_at_utc": "2026-08-10T12:08:00Z"})
        _, accepted, _, _, _ = mr.load_v10_project(self.fx.project)
        self.assertEqual("portfolio_accepted", accepted["route_reset"]["status"])
        self.assertEqual(4, accepted["route_reset"]["trigger_generation"])
        self.assertEqual(5, accepted["route_reset"]["portfolio_generation"])
        payload_path = self.fx.payload("checkpoint-after-portfolio", {"schema": "math-research-transition-payload/v10", "references": [], "occurred_at_utc": "2026-08-10T12:08:30Z"})
        self.assertCode("route_reset_sequence_invalid", mr.prepare_transition, self.fx.project, "CHECKPOINT_COMMIT", payload_path, self.root / "checkpoint-after-portfolio-stage", "Auto")

        next_ticket = self.fx.make_ticket("ticket-2")
        next_ticket["continuity_capsule"] = ptr(successor_capsule_path, self.fx.project)
        next_ticket["route_card"] = ptr(route_a_path, self.fx.project)
        for item in next_ticket["input_artifacts"]:
            if item["id"] == "capsule":
                item.update(next_ticket["continuity_capsule"])
            if item["id"] == "route":
                item.update(next_ticket["route_card"])
        next_ticket["allowed_reads"] = [item["path"] for item in next_ticket["input_artifacts"]]
        next_ticket["persistent_lead"] = {"lead_id": "lead-2", "mode": "new", "previous_ticket_id": None}
        next_ticket["attempt_scope"].update({"route_family_id": "family-a", "proof_object": "object-alpha", "quantifier_strategy": "quantifier-plan-alpha"})
        next_ticket_path = self.fx.project / "runs/run-new/tickets/ticket-2.json"
        record = self.fx.project / "runs/run-new/attempts/attempt-1/reset-complete.json"
        write_json(record, {"schema": "math-research-attempt-record/v10", "project_id": "proj-1", "run_id": "run-new", "attempt_id": "attempt-1", "ticket_id": "ticket-1", "disposition": "no_candidate", "evidence": [], "verifier_completion": None, "completed_at_utc": "2026-08-10T12:09:00Z"})
        wrong_ticket = self.fx.make_ticket("ticket-2")
        write_json(next_ticket_path, wrong_ticket)
        wrong_payload = {"schema": "math-research-transition-payload/v10", "disposition": "no_candidate", "attempt_record": ptr(record, self.fx.project), "evidence_items": [], "next_ticket": ptr(next_ticket_path, self.fx.project), "occurred_at_utc": "2026-08-10T12:09:00Z"}
        wrong_path = self.fx.payload("wrong-reset-successor-ticket", wrong_payload)
        self.assertCode("route_reset_sequence_invalid", mr.prepare_transition, self.fx.project, "ATTEMPT_END", wrong_path, self.root / "wrong-reset-successor-ticket-stage", "Auto")
        partial_identity_ticket = copy.deepcopy(next_ticket)
        partial_identity_ticket["persistent_lead"] = {"lead_id": "lead-1", "mode": "resume", "previous_ticket_id": "ticket-1"}
        write_json(next_ticket_path, partial_identity_ticket)
        partial_identity_payload = {"schema": "math-research-transition-payload/v10", "disposition": "no_candidate", "attempt_record": ptr(record, self.fx.project), "evidence_items": [], "next_ticket": ptr(next_ticket_path, self.fx.project), "occurred_at_utc": "2026-08-10T12:09:00Z"}
        partial_identity_path = self.fx.payload("partial-reset-identity", partial_identity_payload)
        self.assertCode("partial_reset_identity", mr.prepare_transition, self.fx.project, "ATTEMPT_END", partial_identity_path, self.root / "partial-reset-identity-stage", "Auto")
        write_json(next_ticket_path, next_ticket)
        self.fx.transition("ATTEMPT_END", {"schema": "math-research-transition-payload/v10", "disposition": "no_candidate", "attempt_record": ptr(record, self.fx.project), "evidence_items": [], "next_ticket": ptr(next_ticket_path, self.fx.project), "occurred_at_utc": "2026-08-10T12:09:00Z"})
        self.fx.transition("ATTEMPT_START", {"schema": "math-research-transition-payload/v10", "attempt_id": "attempt-2", "attempt_kind": "route_execution", "ticket": ptr(next_ticket_path, self.fx.project), "occurred_at_utc": "2026-08-10T12:10:00Z"})
        _, started, _, _, _ = mr.load_v10_project(self.fx.project)
        self.assertEqual("successor_started", started["route_reset"]["status"])
        self.assertEqual("attempt-2", started["route_reset"]["successor_attempt_id"])
        self.assertEqual("route-a", mr.load_json(self.fx.project / started["active_route_card"]["path"])["route_id"])
        self.assertEqual("lead-2", started["current_attempt"]["lead_id"])

    def _route_variant(self, route_id: str, family: str, proof_object: str, quantifier: str) -> dict:
        card = copy.deepcopy(self.fx.route)
        card["route_id"] = route_id
        card["mechanism_family_id"] = family
        card["core_proof_object"] = proof_object
        card["quantifier_strategy"] = quantifier
        card["status"] = "proposed"
        return card

    def test_semantic_reset_portfolio_rejects_forbidden_family(self):
        directive = {"required": True, "trigger": "explicit_user_ban", "forbidden_mechanism_family_ids": ["family-1"], "minimum_distinct_cards": 2, "same_family_ceiling": 2}
        portfolio = {"schema": "math-research-route-portfolio/v10", "routes": [
            self._route_variant("route-a", "family-1", "object-a", "strategy-a"),
            self._route_variant("route-b", "family-2", "object-b", "strategy-b"),
        ], "created_at_utc": "2026-08-10T12:10:00Z"}
        self.assertCode("surface_route_reset", mr.validate_route_portfolio, portfolio, reset_directive=directive)

    def test_semantic_reset_portfolio_requires_distinct_fingerprint(self):
        directive = {"required": True, "trigger": "same_family_negative_ceiling", "forbidden_mechanism_family_ids": [], "minimum_distinct_cards": 2, "same_family_ceiling": 2}
        portfolio = {"schema": "math-research-route-portfolio/v10", "routes": [
            self._route_variant("route-a", "family-a", "same-object", "same-strategy"),
            self._route_variant("route-b", "family-b", "same-object", "same-strategy"),
        ], "created_at_utc": "2026-08-10T12:10:00Z"}
        self.assertCode("surface_route_reset", mr.validate_route_portfolio, portfolio, reset_directive=directive)

    def test_reset_successor_capsule_preserves_continuity_spine(self):
        old = copy.deepcopy(self.fx.capsule)
        old["proof_spine"] = [{"claim_id": "claim-terminal", "status": "verified", "statement": "Frozen theorem.", "dependencies": [], "artifact": ptr(self.fx.project / "inputs/problem.md", self.fx.project)}]
        directive = {"required": True, "trigger": "explicit_user_ban", "forbidden_mechanism_family_ids": ["family-1"], "minimum_distinct_cards": 2, "same_family_ceiling": 2}
        selected = self._route_variant("route-a", "family-a", "object-alpha", "quantifier-plan-alpha")
        selected["status"] = "active"
        successor = copy.deepcopy(old)
        successor["generation"] = 7
        successor["live_routes"] = ["route-a"]
        successor["quarantined_routes"] = ["route-1"]
        successor["forbidden_families"] = ["family-1"]
        mr.validate_reset_successor_capsule(old, successor, selected, directive, 7)
        dropped_claim = copy.deepcopy(successor)
        dropped_claim["proof_spine"] = []
        self.assertCode("terminal_claim_regression", mr.validate_reset_successor_capsule, old, dropped_claim, selected, directive, 7)
        changed_target = copy.deepcopy(successor)
        changed_target["target_sha256"] = "9" * 64
        self.assertCode("ticket_scope_changed", mr.validate_reset_successor_capsule, old, changed_target, selected, directive, 7)
        dropped_artifact = copy.deepcopy(successor)
        dropped_artifact["required_full_artifacts"] = []
        self.assertCode("ticket_full_context_missing", mr.validate_reset_successor_capsule, old, dropped_artifact, selected, directive, 7)
        stale_route = copy.deepcopy(successor)
        stale_route["quarantined_routes"] = []
        self.assertCode("route_reset_sequence_invalid", mr.validate_reset_successor_capsule, old, stale_route, selected, directive, 7)
        proposed = copy.deepcopy(selected)
        proposed["status"] = "proposed"
        self.assertCode("route_reset_sequence_invalid", mr.validate_reset_successor_capsule, old, successor, proposed, directive, 7)
        added_terminal = copy.deepcopy(successor)
        added_terminal["proof_spine"].append({"claim_id": "claim-new-terminal", "status": "verified", "statement": "Unverified addition.", "dependencies": [], "artifact": ptr(self.fx.project / "inputs/contract-v10.md", self.fx.project) if (self.fx.project / "inputs/contract-v10.md").is_file() else ptr(self.fx.project / "contracts/contract-v10.md", self.fx.project)})
        self.assertCode("unverified_claim_promotion", mr.validate_reset_successor_capsule, old, added_terminal, selected, directive, 7)
        overlapping = copy.deepcopy(successor)
        overlapping["live_routes"].append("route-1")
        self.assertCode("route_reset_sequence_invalid", mr.validate_reset_successor_capsule, old, overlapping, selected, directive, 7)
        still_active = copy.deepcopy(successor)
        still_active["route_reset_directive"] = copy.deepcopy(directive)
        self.assertCode("route_reset_sequence_invalid", mr.validate_reset_successor_capsule, old, still_active, selected, directive, 7)
        reused = copy.deepcopy(selected)
        reused["route_id"] = "route-1"
        reused_successor = copy.deepcopy(successor)
        reused_successor["live_routes"] = ["route-1"]
        reused_successor["quarantined_routes"] = []
        self.assertCode("route_reset_sequence_invalid", mr.validate_reset_successor_capsule, old, reused_successor, reused, directive, 7)

    def test_continuity_capsule_route_registries_are_disjoint(self):
        capsule = copy.deepcopy(self.fx.capsule)
        capsule["quarantined_routes"] = ["route-1"]
        self.assertCode("capsule_invalid", mr.validate_continuity_capsule, capsule, self.fx.project)

    def test_active_special_family_route_needs_coverage_bridge(self):
        card = copy.deepcopy(self.fx.route)
        card["special_family"] = True
        card["coverage_bridge"] = {"status": "none", "statement": None, "test": None}
        self.assertCode("coverage_bridge_missing", mr.validate_route_card, card)

    def test_strategy_audit_cannot_hide_new_math(self):
        action = {
            "schema": "math-research-strategy-action/v1",
            "action": "synthesize",
            "bottleneck_progress": "Two old claims may combine.",
            "surface_reset_risk": "none",
            "missing_full_artifacts": [],
            "synthesis_map": [{"claim_ids": ["claim-1"], "reason": "Possible bridge."}],
            "ranked_route_portfolio": [],
            "required_next_inputs": [],
            "new_math_performed": True,
            "created_at_utc": "2026-08-10T12:10:00Z",
        }
        self.assertCode("strategy_audit_new_math", mr.validate_strategy_action, action, self.fx.project)

    def _start_active_attempt(self):
        self.fx.create()
        ticket_pointer = {"path": "runs/run-new/tickets/ticket-1.json", "sha256": mr.sha_file(self.fx.project / "runs/run-new/tickets/ticket-1.json")}
        self.fx.transition("ATTEMPT_START", {"schema": "math-research-transition-payload/v10", "attempt_id": "attempt-1", "attempt_kind": "route_execution", "ticket": ticket_pointer, "occurred_at_utc": "2026-08-10T12:01:00Z"})

    def test_research_checkpoint_preserves_attempt_and_counters(self):
        self._start_active_attempt()
        capsule = copy.deepcopy(self.fx.capsule)
        capsule["generation"] = 3
        capsule["open_bottlenecks"] = ["Finish the auxiliary bridge."]
        capsule["updated_at_utc"] = "2026-08-10T12:30:00Z"
        capsule_path = self.fx.project / "runs/run-new/continuity/capsule-g0003.json"
        write_json(capsule_path, capsule)
        self.fx.transition("RESEARCH_CHECKPOINT", {"schema": "math-research-transition-payload/v10", "capsule": ptr(capsule_path, self.fx.project), "references": [], "checkpoint_reason": "cadence_30m", "occurred_at_utc": "2026-08-10T12:30:00Z"})
        _, state, _, _, _ = mr.load_v10_project(self.fx.project)
        self.assertEqual(1, state["counters"]["run_local"]["attempt_count"])
        self.assertEqual(1, state["current_attempt"]["checkpoint_count"])
        self.assertEqual("ticket-1", state["current_ticket"]["id"])

    def test_research_checkpoint_cannot_promote_working_claim(self):
        self._start_active_attempt()
        capsule = copy.deepcopy(self.fx.capsule)
        capsule["generation"] = 3
        capsule["proof_spine"] = [{"claim_id": "claim-1", "status": "verified", "statement": "Unverified synthetic claim.", "dependencies": [], "artifact": ptr(self.fx.project / "inputs/problem.md", self.fx.project)}]
        capsule["updated_at_utc"] = "2026-08-10T12:30:00Z"
        capsule_path = self.fx.project / "runs/run-new/continuity/capsule-g0003.json"
        write_json(capsule_path, capsule)
        payload = {"schema": "math-research-transition-payload/v10", "capsule": ptr(capsule_path, self.fx.project), "references": [], "checkpoint_reason": "material_result", "occurred_at_utc": "2026-08-10T12:30:00Z"}
        path = self.fx.payload("bad-research-checkpoint", payload)
        self.assertCode("unverified_claim_promotion", mr.prepare_transition, self.fx.project, "RESEARCH_CHECKPOINT", path, self.root / "bad-research-checkpoint-stage", "Auto")

    def _start_with_terminal_claim(self):
        terminal = {"claim_id": "claim-terminal", "status": "verified", "statement": "Frozen terminal statement.", "dependencies": [], "artifact": ptr(self.fx.project / "inputs/problem.md", self.fx.project)}
        self.fx.capsule["proof_spine"] = [terminal]
        write_json(self.fx.capsule_path, self.fx.capsule)
        capsule_pointer = ptr(self.fx.capsule_path, self.fx.project)
        self.fx.ticket["continuity_capsule"] = capsule_pointer
        for item in self.fx.ticket["input_artifacts"]:
            if item["id"] == "capsule":
                item.update(capsule_pointer)
        self.fx.spec["initial_ticket"] = self.fx.ticket
        self.fx.spec["initial_capsule"] = capsule_pointer
        write_json(self.fx.spec_path, self.fx.spec)
        self._start_active_attempt()
        return terminal

    def test_research_checkpoint_preserves_terminal_claim_bytes(self):
        terminal = self._start_with_terminal_claim()
        variants = []
        downgraded = copy.deepcopy(self.fx.capsule)
        downgraded["proof_spine"][0]["status"] = "working"
        downgraded["proof_spine"][0]["artifact"] = None
        variants.append(downgraded)
        deleted = copy.deepcopy(self.fx.capsule)
        deleted["proof_spine"] = []
        variants.append(deleted)
        rewritten = copy.deepcopy(self.fx.capsule)
        rewritten["proof_spine"][0]["statement"] = "Different terminal statement."
        variants.append(rewritten)
        for index, capsule in enumerate(variants, start=1):
            capsule["generation"] = 3
            capsule["updated_at_utc"] = f"2026-08-10T12:3{index}:00Z"
            capsule_path = self.fx.project / "runs/run-new/continuity/capsule-terminal-bad.json"
            write_json(capsule_path, capsule)
            payload = {"schema": "math-research-transition-payload/v10", "capsule": ptr(capsule_path, self.fx.project), "references": [], "checkpoint_reason": "material_result", "occurred_at_utc": f"2026-08-10T12:3{index}:00Z"}
            path = self.fx.payload(f"terminal-regression-{index}", payload)
            self.assertCode("terminal_claim_regression", mr.prepare_transition, self.fx.project, "RESEARCH_CHECKPOINT", path, self.root / f"terminal-regression-stage-{index}", "Auto")
        self.assertEqual("verified", terminal["status"])

    def test_unchanged_scope_cannot_be_split_into_new_attempt(self):
        self._start_active_attempt()
        next_ticket = self.fx.make_ticket("ticket-2")
        next_ticket_path = self.fx.project / "runs/run-new/tickets/ticket-2-same-scope.json"
        write_json(next_ticket_path, next_ticket)
        record = self.fx.project / "runs/run-new/attempts/attempt-1/same-scope-end.json"
        write_json(record, {"schema": "math-research-attempt-record/v10", "project_id": "proj-1", "run_id": "run-new", "attempt_id": "attempt-1", "ticket_id": "ticket-1", "disposition": "no_candidate", "evidence": [], "verifier_completion": None, "completed_at_utc": "2026-08-10T12:40:00Z"})
        payload = {"schema": "math-research-transition-payload/v10", "disposition": "no_candidate", "attempt_record": ptr(record, self.fx.project), "evidence_items": [], "next_ticket": ptr(next_ticket_path, self.fx.project), "occurred_at_utc": "2026-08-10T12:40:00Z"}
        path = self.fx.payload("same-scope-split", payload)
        self.assertCode("attempt_continuity_violation", mr.prepare_transition, self.fx.project, "ATTEMPT_END", path, self.root / "same-scope-split-stage", "Auto")

    def test_no_candidate_can_end_without_verifier(self):
        self._start_active_attempt()
        record = self.fx.project / "runs/run-new/attempts/attempt-1/attempt-record.json"
        write_json(record, {"schema": "math-research-attempt-record/v10", "project_id": "proj-1", "run_id": "run-new", "attempt_id": "attempt-1", "ticket_id": "ticket-1", "disposition": "no_candidate", "evidence": [], "verifier_completion": None, "completed_at_utc": "2026-08-10T12:40:00Z"})
        self.fx.transition("ATTEMPT_END", {"schema": "math-research-transition-payload/v10", "disposition": "no_candidate", "attempt_record": ptr(record, self.fx.project), "evidence_items": [], "next_ticket": None, "occurred_at_utc": "2026-08-10T12:40:00Z"})
        _, state, _, _, _ = mr.load_v10_project(self.fx.project)
        self.assertIsNone(state["current_attempt"])
        self.assertEqual("awaiting_input", state["active_run"]["status"])

    def test_ticket_scope_change_requires_new_route(self):
        ticket = copy.deepcopy(self.fx.ticket)
        ticket["attempt_scope"]["proof_object"] = "renamed old object"
        self.assertCode("ticket_scope_changed", mr.validate_v10_ticket, ticket, self.fx.project)

    def test_duplicate_json_keys_fail_closed(self):
        path = self.root / "duplicate.json"
        path.write_text('{"x":1,"x":2}', encoding="utf-8")
        self.assertCode("duplicate_json_key", mr.load_json, path)

    def test_asset_registry_update_preserves_research_counters(self):
        self.fx.create()
        _, before, _, _, _ = mr.load_v10_project(self.fx.project)
        problem = self.fx.project / "inputs/problem.md"
        asset_dir = self.fx.project / "state/assets"
        registry = {
            "schema": "math-research-asset-registry/v1", "project_id": "proj-1", "registry_id": "registry-1", "created_at_utc": "2026-08-10T12:20:00Z",
            "assets": [{
                "asset_id": "problem-source", "kind": "source_record", "title": "Frozen problem source", "origin": "project",
                "creators": [{"type": "user", "name": "project user", "role": "problem owner"}],
                "source": {"locator": None, "identifier": "problem-source-v1", "version": "v1", "upstream_commit": None, "acquired_at_utc": "2026-08-10T12:20:00Z"},
                "local_artifacts": [{"role": "problem", "path": "inputs/problem.md", "sha256": mr.sha_file(problem), "bytes": problem.stat().st_size}],
                "license": {"status": "unknown", "identifier": None, "license_artifact": None, "redistribution": "private_only"},
                "citation": {"required": False, "key": "", "text": "", "bibtex": ""},
                "supported_claims": ["Frozen problem statement."], "usage": {"entrypoints": [], "environment": "Markdown", "verification": "Hash-bound in the v10 archive."},
                "limitations": [], "export": {"mother_bundle": True, "paper_support_bundle": True}
            }]
        }
        ledger = {"schema": "math-research-contribution-ledger/v1", "project_id": "proj-1", "ledger_id": "ledger-1", "contributions": [], "created_at_utc": "2026-08-10T12:20:00Z"}
        policy = {"schema": "math-research-export-policy/v1", "project_id": "proj-1", "default_visibility": "private", "scan_roots": ["assets"], "scan_exclusions": [], "profiles": {"mother_bundle": {"visibility": "private", "description": "Full private archive."}, "paper_support_bundle": {"visibility": "private", "description": "Private paper support."}}, "created_at_utc": "2026-08-10T12:20:00Z"}
        registry_path = asset_dir / "registry.json"; ledger_path = asset_dir / "ledger.json"; policy_path = asset_dir / "policy.json"
        write_json(registry_path, registry); write_json(ledger_path, ledger); write_json(policy_path, policy)
        index = {"schema": "math-research-asset-index/v1", "project_id": "proj-1", "authority": "authoritative", "asset_registry": ptr(registry_path, self.fx.project), "contribution_ledger": ptr(ledger_path, self.fx.project), "export_policy": ptr(policy_path, self.fx.project), "created_at_utc": "2026-08-10T12:20:00Z"}
        index_path = asset_dir / "index.json"; write_json(index_path, index)
        payload = self.fx.payload("asset-update", {"schema": "math-research-transition-payload/v10", "asset_index": ptr(index_path, self.fx.project), "occurred_at_utc": "2026-08-10T12:20:00Z"})
        stage = self.root / "asset-update-stage"
        prepared = mr.prepare_transition(self.fx.project, "ASSET_REGISTRY_UPDATE", payload, stage, "Auto")
        mr.commit_plan(Path(prepared["plan_path"]), "active")
        _, after, manifest, _, _ = mr.load_v10_project(self.fx.project, "Full")
        self.assertEqual(before["counters"], after["counters"])
        self.assertEqual(ptr(index_path, self.fx.project), after["asset_index"])
        manifested = {entry["path"] for entry in manifest["entries"]}
        self.assertTrue({"state/assets/index.json", "state/assets/registry.json", "state/assets/ledger.json", "state/assets/policy.json"}.issubset(manifested))


if __name__ == "__main__":
    unittest.main(verbosity=2)
