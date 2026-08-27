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


MODULE_PATH = Path(__file__).with_name("math_research_state_v9.py")
SPEC = importlib.util.spec_from_file_location("math_research_state_v9", MODULE_PATH)
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


class V9Fixture:
    def __init__(self, base: Path):
        self.base = base
        self.predecessor = base / "predecessor"
        self.project = base / "successor"
        self.stage = base / "stage-successor"
        self.predecessor.mkdir()
        self.project.mkdir()
        write_json(self.predecessor / "project.json", {"schema": "math-research-project/v8", "project_id": "proj-1", "control_generation": 7})
        problem = self.project / "inputs/problem.md"
        contract = self.project / "contracts/contract-v9.md"
        write_text(problem, "Synthetic mathematical problem.\n")
        write_text(contract, "Synthetic frozen contract.\n")
        self.ticket = self.make_ticket("ticket-1", problem, contract)
        h = "1" * 64
        self.spec = {
            "schema": "math-research-successor-spec/v9",
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
            "occurred_at_utc": "2026-08-10T12:00:00.000000Z",
        }
        self.spec_path = self.base / "successor-spec.json"
        write_json(self.spec_path, self.spec)

    def make_ticket(self, ticket_id: str, problem: Path | None = None, contract: Path | None = None) -> dict:
        problem = problem or self.project / "inputs/problem.md"
        contract = contract or self.project / "contracts/contract-v9.md"
        return {
            "schema": "math-research-ticket/v9",
            "ticket_id": ticket_id,
            "role": "attempt",
            "initial_lifecycle": "planned",
            "source_requirements": [
                {"id": "problem", "role": "task_contract", "required": True},
                {"id": "contract", "role": "task_contract", "required": True},
            ],
            "input_artifacts": [
                {"id": "problem", "role": "task_contract", **ptr(problem, self.project)},
                {"id": "contract", "role": "task_contract", **ptr(contract, self.project)},
            ],
            "allowed_reads": [problem.relative_to(self.project).as_posix(), contract.relative_to(self.project).as_posix()],
            "writable_staging_path": f"runs/run-new/staging/{ticket_id}/solver",
            "decision_question": "Does the synthetic route meet its frozen signal?",
            "allowed_tools": ["shell_command"],
            "resource_caps": {"child_agents": 1, "tool_calls": 4, "runtime_minutes": 10, "max_output_bytes": 4096},
            "required_outputs": [{"path": "solver-report.md", "schema": "math-research-solver-report/v1", "sha256_on_return": "required"}],
            "failure_return": {"schema": "math-research-ticket-failure/v1", "required_fields": ["status", "failed_step", "reason", "partial_artifact_hashes", "reopen_condition"]},
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

    def transition(self, name: str, payload: dict, stage_name: str | None = None) -> dict:
        payload_path = self.payload(f"payload-{name.lower()}-{time.time_ns()}", payload)
        out = self.base / (stage_name or f"stage-{name.lower()}-{time.time_ns()}")
        result = mr.prepare_transition(self.project, name, payload_path, out, "Auto")
        mr.commit_plan(Path(result["plan_path"]), "active")
        return result


class MathResearchV9Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.fx = V9Fixture(self.root)

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
        self.assertEqual("v9_ready", mr.startup(self.fx.project, "Auto", None)["classification"])

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
        self.assertEqual("delegate_startup_v3", result["classification"])

    def test_startup_v4_delegates_to_v3_with_legacy_parameter_name(self):
        pwsh = shutil.which("pwsh")
        if not pwsh:
            self.skipTest("pwsh is unavailable")
        shim_dir = Path(self.temp.name) / "startup-v4-shim"
        shim_dir.mkdir()
        shutil.copy2(MODULE_PATH.with_name("invoke_math_research_startup_v4.ps1"), shim_dir)
        (shim_dir / "math_research_state_v9.py").write_text(
            "import json\nprint(json.dumps({'ok': True, 'data': {'classification': 'delegate_startup_v3'}}))\n",
            encoding="utf-8",
        )
        (shim_dir / "invoke_math_research_startup_v3.ps1").write_text(
            "param([Parameter(Mandatory=$true)][string]$ProjectDirectory,"
            "[Parameter(Mandatory=$true)][string]$GoalStatus)\n"
            "[ordered]@{project_directory=$ProjectDirectory;goal_status=$GoalStatus}|ConvertTo-Json\n",
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                pwsh,
                "-NoProfile",
                "-File",
                str(shim_dir / "invoke_math_research_startup_v4.ps1"),
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

    def test_v9_ticket_missing_required_input(self):
        ticket = copy.deepcopy(self.fx.ticket)
        ticket["input_artifacts"] = ticket["input_artifacts"][:1]
        ticket["allowed_reads"] = ticket["allowed_reads"][:1]
        self.assertCode("ticket_input_incomplete", mr.validate_v9_ticket, ticket, self.fx.project)

    def test_v9_ticket_rejects_read_path_gap(self):
        ticket = copy.deepcopy(self.fx.ticket)
        ticket["allowed_reads"].append("inputs/unbound.md")
        self.assertCode("ticket_read_closure_failed", mr.validate_v9_ticket, ticket, self.fx.project)

    def _v8_ticket(self):
        problem = self.fx.project / "inputs/problem.md"
        req = self.fx.project / "inputs/source-requirements.json"
        requirements = {"schema": "math-research-source-requirements/v1", "requirements": [{"id": "problem", "role": "task_contract", "path": "inputs/problem.md", "sha256": mr.sha_file(problem), "required": True}]}
        write_json(req, requirements)
        wrapper = {
            "contract": {"path": "contracts/contract-v9.md", "version": 8, "binding_sha256": "4" * 64},
            "ticket": {
                "ticket_id": "legacy-ticket",
                "input_artifacts": [ptr(problem, self.fx.project), ptr(req, self.fx.project)],
                "filesystem_scope": {"read_paths": ["inputs/problem.md", "inputs/source-requirements.json", "contracts/contract-v9.md"], "writable_staging_path": "runs/run-old/staging/legacy-ticket/solver"},
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
        payload = {"schema": "math-research-transition-payload/v9", "attempt_id": "attempt-1", "attempt_kind": "route_execution", "ticket": {"path": "runs/run-new/tickets/ticket-1.json", "sha256": mr.sha_file(self.fx.project / "runs/run-new/tickets/ticket-1.json")}, "occurred_at_utc": "2026-08-10T12:01:00Z"}
        self.fx.transition("ATTEMPT_START", payload)
        _, state, _, _, _ = mr.load_v9_project(self.fx.project)
        self.assertEqual(1, state["counters"]["run_local"]["attempt_count"])
        self.assertEqual(4, state["counters"]["cumulative"]["attempt_count"])
        self.assertEqual("active", state["current_ticket"]["lifecycle"])

    def test_attempt_start_reserves_audit_round(self):
        self.fx.spec["successor"]["budgets"] = {"attempt_budget": 4, "total_round_budget": 1}
        write_json(self.fx.spec_path, self.fx.spec)
        self.fx.create()
        payload = {"schema": "math-research-transition-payload/v9", "attempt_id": "attempt-1", "attempt_kind": "route_execution", "ticket": {"path": "runs/run-new/tickets/ticket-1.json", "sha256": mr.sha_file(self.fx.project / "runs/run-new/tickets/ticket-1.json")}, "occurred_at_utc": "2026-08-10T12:01:00Z"}
        path = self.fx.payload("attempt-budget", payload)
        self.assertCode("budget_exhausted", mr.prepare_transition, self.fx.project, "ATTEMPT_START", path, self.root / "budget-stage", "Auto")

    def _run_to_verifier(self):
        self.fx.create()
        ticket_pointer = {"path": "runs/run-new/tickets/ticket-1.json", "sha256": mr.sha_file(self.fx.project / "runs/run-new/tickets/ticket-1.json")}
        self.fx.transition("ATTEMPT_START", {"schema": "math-research-transition-payload/v9", "attempt_id": "attempt-1", "attempt_kind": "route_execution", "ticket": ticket_pointer, "occurred_at_utc": "2026-08-10T12:01:00Z"})
        solver = self.fx.project / "runs/run-new/attempts/attempt-1/solver-result.json"
        write_json(solver, {"schema": "synthetic-solver-result/v1", "status": "partial"})
        self.fx.transition("SOLVER_COMPLETE", {"schema": "math-research-transition-payload/v9", "solver_result": ptr(solver, self.fx.project), "occurred_at_utc": "2026-08-10T12:02:00Z"})
        partial = self.fx.project / "evidence/partial-1.md"
        write_text(partial, "Verified synthetic partial result.\n")
        completion = self.fx.project / "runs/run-new/attempts/attempt-1/verifier-completion.json"
        write_json(completion, {"schema": "math-research-verifier-completion/v9", "project_id": "proj-1", "run_id": "run-new", "attempt_id": "attempt-1", "ticket_id": "ticket-1", "verdict": "PASS", "candidate": None, "completed_at_utc": "2026-08-10T12:03:00Z"})
        evidence = [{"kind": "verified_partial", **ptr(partial, self.fx.project), "ticket_id": "ticket-1", "attempt_id": "attempt-1"}]
        self.fx.transition("VERIFIER_COMPLETE", {"schema": "math-research-transition-payload/v9", "verifier_completion": ptr(completion, self.fx.project), "evidence_items": evidence, "occurred_at_utc": "2026-08-10T12:03:00Z"})
        return evidence

    def test_verified_partial_survives_attempt_end(self):
        evidence = self._run_to_verifier()
        next_ticket = self.fx.make_ticket("ticket-2")
        next_path = self.fx.project / "runs/run-new/tickets/ticket-2.json"
        write_json(next_path, next_ticket)
        record = self.fx.project / "runs/run-new/attempts/attempt-1/attempt-record.json"
        write_json(record, {"schema": "math-research-attempt-record/v9", "project_id": "proj-1", "run_id": "run-new", "attempt_id": "attempt-1", "ticket_id": "ticket-1", "disposition": "no_candidate_with_evidence", "evidence": evidence, "completed_at_utc": "2026-08-10T12:04:00Z"})
        self.fx.transition("ATTEMPT_END", {"schema": "math-research-transition-payload/v9", "disposition": "no_candidate_with_evidence", "attempt_record": ptr(record, self.fx.project), "evidence_items": evidence, "next_ticket": ptr(next_path, self.fx.project), "occurred_at_utc": "2026-08-10T12:04:00Z"})
        _, state, _, _, _ = mr.load_v9_project(self.fx.project)
        self.assertIsNone(state["current_attempt"])
        self.assertEqual("ticket-2", state["current_ticket"]["id"])
        self.assertIn("verified_partial", {item["kind"] for item in state["evidence_items"]})

    def test_no_candidate_with_evidence_requires_partial(self):
        evidence = self._run_to_verifier()
        record = self.fx.project / "runs/run-new/attempts/attempt-1/attempt-record.json"
        write_json(record, {"schema": "math-research-attempt-record/v9", "project_id": "proj-1", "run_id": "run-new", "attempt_id": "attempt-1", "ticket_id": "ticket-1", "disposition": "no_candidate_with_evidence", "evidence": [], "completed_at_utc": "2026-08-10T12:04:00Z"})
        payload = {"schema": "math-research-transition-payload/v9", "disposition": "no_candidate_with_evidence", "attempt_record": ptr(record, self.fx.project), "evidence_items": [], "next_ticket": None, "occurred_at_utc": "2026-08-10T12:04:00Z"}
        path = self.fx.payload("bad-end", payload)
        self.assertCode("transition_invalid", mr.prepare_transition, self.fx.project, "ATTEMPT_END", path, self.root / "bad-end-stage", "Auto")

    def test_checkpoint_rejects_untyped_reference(self):
        self.fx.create()
        artifact = self.fx.project / "evidence/x.md"
        write_text(artifact, "x\n")
        payload = {"schema": "math-research-transition-payload/v9", "references": [{"kind": "arbitrary_blob", **ptr(artifact, self.fx.project), "attempt_id": None, "ticket_id": None}], "occurred_at_utc": "2026-08-10T12:05:00Z"}
        path = self.fx.payload("bad-checkpoint", payload)
        self.assertCode("reference_invalid", mr.prepare_transition, self.fx.project, "CHECKPOINT_COMMIT", path, self.root / "bad-checkpoint-stage", "Auto")

    def test_cas_conflict_rejects_second_plan(self):
        self.fx.create()
        payload1 = self.fx.payload("cp1", {"schema": "math-research-transition-payload/v9", "references": [], "occurred_at_utc": "2026-08-10T12:05:00Z"})
        payload2 = self.fx.payload("cp2", {"schema": "math-research-transition-payload/v9", "references": [], "occurred_at_utc": "2026-08-10T12:06:00Z"})
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

    def test_duplicate_json_keys_fail_closed(self):
        path = self.root / "duplicate.json"
        path.write_text('{"x":1,"x":2}', encoding="utf-8")
        self.assertCode("duplicate_json_key", mr.load_json, path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
