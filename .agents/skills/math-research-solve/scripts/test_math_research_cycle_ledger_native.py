#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from MathResearchCycleLedgerV2 import CycleLedgerError, initialize, invoke_action, verify
from math_research_control_primitives import ControlIntegrityError


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")


class CycleLedgerNativeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name); self.run = self.root / "run"; self.run.mkdir()
        self.old_home = os.environ.get("MATH_RESEARCH_CONTROL_HOME"); control = self.root / "control"; control.mkdir(mode=0o700); os.chmod(control, 0o700); os.environ["MATH_RESEARCH_CONTROL_HOME"] = str(control)
        self.policy = {"schema_version":1,"protocol":"math-research-cycle-policy/v1","total_round_budget":8,"attempt_budget":5,"audit_interval_attempts":2,"max_route_family_attempts_per_cycle":2,"max_repair_batches_per_attempt":1,"audit_roles":["skeptic_quantifiers","skeptic_strategy","theory_tool_scout"]}
        dump(self.run / "cycle-policy.json", self.policy); self.write_tickets("cycle-1", ["t1", "t2", "t3"])
        initialize(self.run, "run-1", "1" * 64, Path("cycle-policy.json"), Path("cycle-tickets-000.json"))

    def tearDown(self) -> None:
        if self.old_home is None: os.environ.pop("MATH_RESEARCH_CONTROL_HOME", None)
        else: os.environ["MATH_RESEARCH_CONTROL_HOME"] = self.old_home
        self.temp.cleanup()

    def ticket(self, ticket_id: str, route: str = "route-family-a") -> dict[str, object]:
        return {"ticket_id":ticket_id,"route_family_id":route,"mechanism_id":"m1","bottleneck_id":"b1","decision_question":"q?","search_domain":"domain","success_signal":"yes","stop_signal":"no","resource_caps":{"minutes":1},"reopen_condition":"new evidence"}

    def write_tickets(self, cycle: str, ids: list[str], name: str = "cycle-tickets-000.json", source: str | None = None) -> Path:
        value: dict[str, object] = {"schema_version":1,"cycle_id":cycle,"tickets":[self.ticket(x) for x in ids]}
        if source is not None: value["source_audit_id"] = source
        path = self.run / name; dump(path, value); return path

    def start_end(self, ticket: str, outcome: str = "proved_subclaim") -> None:
        invoke_action("AttemptStart", self.run, ticket_id=ticket)
        artifact = self.run / f"{ticket}.txt"; artifact.write_text("result", encoding="utf-8")
        invoke_action("AttemptEnd", self.run, outcome=outcome, artifact_file=artifact)

    def audit(self, action: str = "pause", next_tickets: bool = False, completion: bool = False) -> None:
        state = verify(self.run); audit_id = f"audit-{state['AuditCount'] + 1}"
        ticket = self.run / f"{audit_id}-ticket.json"
        dump(ticket, {"schema_version":1,"audit_id":audit_id,"trigger":"completion" if completion else "scheduled","snapshot_head_sha256":state["HeadPayloadSha256"],"contract_binding_sha256":"1"*64,"read_only":True,"roles":["skeptic_quantifiers","skeptic_strategy","theory_tool_scout"],"resource_caps":{"minutes":1}})
        invoke_action("AuditStart", self.run, audit_ticket_file=ticket)
        reports = []
        for role in ("skeptic_quantifiers","skeptic_strategy","theory_tool_scout"):
            path = self.run / f"{audit_id}-{role}.txt"; path.write_text(role, encoding="utf-8")
            import hashlib
            reports.append({"role":role,"verdict":"PASS" if completion else "INCONCLUSIVE","artifact_file":path.name,"artifact_sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
        result = self.run / f"{audit_id}-result.json"
        dump(result, {"schema_version":1,"audit_id":audit_id,"snapshot_head_sha256":state["HeadPayloadSha256"],"contract_binding_sha256":"1"*64,"new_math_performed":False,"reports":reports,"synthesis":{"action":action,"blocking_findings":[],"quarantined_leads":[]}})
        nxt = None
        if next_tickets: nxt = self.write_tickets(f"cycle-{state['AuditCount'] + 2}", [f"n{state['AuditCount'] + 1}"], f"cycle-tickets-{state['AuditCount'] + 1:03d}.json", audit_id)
        invoke_action("AuditEnd", self.run, audit_result_file=result, next_tickets_file=nxt)

    def test_genesis_is_clean_and_zeroed(self) -> None:
        state = verify(self.run)
        self.assertEqual((0, 0, 0), (state["AttemptCount"], state["AuditCount"], state["TotalRoundCount"]))
        self.assertTrue(state["CleanReturn"])

    def test_interval_forces_audit_and_blocks_third_attempt(self) -> None:
        self.start_end("t1"); self.start_end("t2")
        self.assertTrue(verify(self.run)["AuditDue"])
        with self.assertRaises(CycleLedgerError): invoke_action("AttemptStart", self.run, ticket_id="t3")

    def test_audit_resets_cycle_and_return_check(self) -> None:
        self.start_end("t1"); self.audit("continue", next_tickets=True)
        state = invoke_action("ReturnCheck", self.run)
        self.assertTrue(state["CleanReturn"]); self.assertEqual("cycle-2", state["CurrentCycleId"])

    def test_bound_artifact_tamper_is_blocked(self) -> None:
        self.start_end("t1"); (self.run / "t1.txt").write_text("tampered", encoding="utf-8")
        with self.assertRaises(CycleLedgerError): verify(self.run)

    def test_ticket_manifest_tamper_is_blocked(self) -> None:
        invoke_action("AttemptStart", self.run, ticket_id="t1")
        value = json.loads((self.run / "cycle-tickets-000.json").read_text(encoding="utf-8")); value["tickets"][0]["decision_question"] = "changed"; dump(self.run / "cycle-tickets-000.json", value)
        with self.assertRaises(CycleLedgerError): verify(self.run)

    def test_frozen_policy_tamper_is_fail_closed(self) -> None:
        self.policy["audit_interval_attempts"] = 3; dump(self.run / "cycle-policy.json", self.policy)
        # The frozen policy itself may not be edited after genesis.
        with self.assertRaises(CycleLedgerError): verify(self.run)

    def test_completion_requires_candidate_and_unanimous_audit(self) -> None:
        self.start_end("t1", "candidate_found"); self.audit("approve-completion", completion=True)
        state = invoke_action("ReturnCheck", self.run, completion=True)
        self.assertTrue(state["CompletionAuthorized"])

    def test_dirty_return_and_ledger_tamper_are_blocked(self) -> None:
        self.start_end("t1")
        with self.assertRaises(CycleLedgerError): invoke_action("ReturnCheck", self.run)
        event = self.run / "cycle-ledger" / "00000001.json"; value = json.loads(event.read_text(encoding="utf-8")); value["payload"]["data"]["ticket_id"] = "evil"; dump(event, value)
        with self.assertRaises(ControlIntegrityError): verify(self.run)

    def test_cli_status_and_blocked_exit_codes(self) -> None:
        cli = Path(__file__).with_name("invoke_math_research_cycle_v2.py")
        env = os.environ.copy()
        good = subprocess.run([sys.executable, "-B", str(cli), "--action", "Status", "--run-directory", str(self.run)], text=True, capture_output=True, env=env)
        self.assertEqual(0, good.returncode); self.assertEqual("run-1", json.loads(good.stdout)["RunId"])
        invoke_action("AttemptStart", self.run, ticket_id="t1")
        bad = subprocess.run([sys.executable, "-B", str(cli), "--action", "ReturnCheck", "--run-directory", str(self.run)], text=True, capture_output=True, env=env)
        self.assertEqual(2, bad.returncode); self.assertFalse(json.loads(bad.stderr)["ok"])


if __name__ == "__main__":
    unittest.main()
