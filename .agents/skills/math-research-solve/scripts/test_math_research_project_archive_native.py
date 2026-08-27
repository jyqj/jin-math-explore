#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from MathResearchProjectArchiveV2 import (
    ProjectArchiveError, failure_record, initialize_project, new_handoff,
    project_status, publish_checkpoint, read_json, register_contract, repair_event_tail,
    resume_plan, route_fingerprint, route_start, sha_bytes, sha_file, source_claims, verify_project,
)
from MathResearchCycleLedgerV2 import initialize as initialize_cycle, invoke_action
from math_research_control_primitives import write_signed_json
from MathResearchLegacyArchive import analyze as analyze_legacy, apply as apply_legacy, legacy_failure, verify as verify_legacy


class ProjectArchiveNativeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name); self.old_control=os.environ.get("MATH_RESEARCH_CONTROL_HOME"); control=self.root/"control"; control.mkdir(mode=0o700); os.chmod(control,0o700); os.environ["MATH_RESEARCH_CONTROL_HOME"]=str(control); self.vault=self.root/"vault"; self.vault.mkdir(); self.source=self.root/"source"; self.source.mkdir()
        (self.source/"AI-START-HERE.md").write_text("start",encoding="utf-8"); (self.source/"work/proof").mkdir(parents=True); (self.source/"work/proof/note.md").write_text("proof",encoding="utf-8"); (self.source/"work/proof/cache.pyc").write_bytes(b"cache"); (self.source/"work/skill-dev").mkdir(); (self.source/"work/skill-dev/private.md").write_text("private",encoding="utf-8")
        self.created=initialize_project(self.vault,"project-one","project-0001","Prove T.",source_workspace=self.source); self.project=Path(self.created["ProjectDirectory"])

    def tearDown(self) -> None:
        if self.old_control is None: os.environ.pop("MATH_RESEARCH_CONTROL_HOME",None)
        else: os.environ["MATH_RESEARCH_CONTROL_HOME"]=self.old_control
        self.temp.cleanup()

    def test_initialize_filters_nonresearch_and_verifies_imports(self) -> None:
        self.assertTrue(self.created["Ok"]); self.assertTrue((self.project/"history/imported-workspace/work/proof/note.md").is_file()); self.assertFalse((self.project/"history/imported-workspace/work/skill-dev/private.md").exists()); self.assertFalse((self.project/"history/imported-workspace/work/proof/cache.pyc").exists())
        self.assertEqual(2,verify_project(self.project)["ImportedFilesVerified"])

    def test_duplicate_and_import_tamper_fail_closed(self) -> None:
        with self.assertRaises(ProjectArchiveError): initialize_project(self.vault,"project-one","project-0001","Prove T.")
        imported=self.project/"history/imported-workspace/work/proof/note.md"; imported.write_text("tampered",encoding="utf-8")
        with self.assertRaises(ProjectArchiveError): verify_project(self.project)

    def test_resume_precedence(self) -> None:
        self.assertEqual("awaiting_contract",resume_plan(self.project)["Action"]); checkpoint=self.project/"state/checkpoint.json"; value=read_json(checkpoint,"checkpoint"); value["audit_due"]=True; checkpoint.write_text(json.dumps(value),encoding="utf-8"); self.assertEqual("audit_required",resume_plan(self.project)["Action"]); value["dirty"]=True; checkpoint.write_text(json.dumps(value),encoding="utf-8"); self.assertEqual("recovery_or_audit_only",resume_plan(self.project)["Action"])

    def test_failure_record_binds_artifact_and_nonentailment(self) -> None:
        run=self.project/"runs/r1"; run.mkdir(); artifact=run/"a.md"; artifact.write_text("a",encoding="utf-8"); record=run/"failure.json"; value={"schema":1,"attempt_id":"attempt-0001","route_id":"r1","decision_problem":"decide","failed_step":"step","failure_reason":"reason","excluded_scope":"excluded","not_excluded_scope":"remaining","retry_fingerprint_sha256":"a"*64,"reopen_conditions":["c1:new"],"artifacts":[{"file":"a.md","sha256":sha_file(artifact)}]}; record.write_text(json.dumps(value),encoding="utf-8"); self.assertTrue(failure_record(record,"attempt-0001",run)["Ok"]); value["not_excluded_scope"]=""; record.write_text(json.dumps(value),encoding="utf-8")
        with self.assertRaises(ProjectArchiveError): failure_record(record,"attempt-0001",run)

    def test_frozen_route_requires_new_registered_evidence(self) -> None:
        ticket={"route_id":"r1","route_family_id":"family","mechanism_id":"m","decision_problem":"d","frozen_domain":"x","resource_caps":{"minutes":1}}; ticket["route_fingerprint_sha256"]=route_fingerprint(ticket); registry=self.project/"state/route-registry.json"; value=read_json(registry,"registry"); value["routes"]=[{"route_id":"r1","route_family_id":"family","retry_fingerprint_sha256":ticket["route_fingerprint_sha256"],"status":"frozen","reopen_condition_ids":["c1"],"seen_evidence_sha256":[]}]; registry.write_text(json.dumps(value),encoding="utf-8")
        with self.assertRaises(ProjectArchiveError): route_start(self.project,ticket)
        ticket["reopen_evidence"]={"condition_id":"c1","evidence_sha256":"b"*64}; self.assertTrue(route_start(self.project,ticket)["Ok"])

    def test_source_claim_and_handoff_event(self) -> None:
        evidence=self.project/"evidence/verified/result.md"; evidence.write_text("verified",encoding="utf-8"); self.assertEqual([sha_file(evidence)],source_claims(self.project,[sha_file(evidence)])["VerifiedHashes"]); handoff=new_handoff(self.project,"test"); self.assertTrue(Path(handoff["Path"]).is_file()); self.assertTrue(verify_project(self.project)["Ok"])

    def test_event_tamper_and_legacy_gate(self) -> None:
        new_handoff(self.project,"test"); events=self.project/"state/project-events.jsonl"; lines=events.read_text(encoding="utf-8").splitlines(); event=json.loads(lines[-1]); event["data"]["next_action"]="changed"; lines[-1]=json.dumps(event,separators=(",",":")); events.write_text("\n".join(lines)+"\n",encoding="utf-8")
        with self.assertRaises(ProjectArchiveError): verify_project(self.project)

    def test_contract_registration_and_bounded_tail_repair(self) -> None:
        run=self.project/"runs/run-1"; run.mkdir(); contract=self.root/"contract.md"; contract.write_text("fixed\n",encoding="utf-8"); binding=sha_bytes(b"fixed\n"); registered=register_contract(self.project,contract,binding,"v1",run); self.assertEqual("CONTRACT_REGISTERED",registered["SagaState"])
        handoff=new_handoff(self.project,"repair"); events=self.project/"state/project-events.jsonl"; lines=events.read_text(encoding="utf-8").splitlines(); tail=json.loads(lines[-1]); old=tail["event_sha256"]; tail["event_sha256"]="0"*64; lines[-1]=json.dumps(tail,ensure_ascii=False,separators=(",",":")); events.write_text("\n".join(lines)+"\n",encoding="utf-8"); checkpoint=self.project/"state/checkpoint.json"; state=read_json(checkpoint,"checkpoint"); state["last_project_event_sha256"]="0"*64; checkpoint.write_text(json.dumps(state),encoding="utf-8"); repaired=repair_event_tail(self.project); self.assertTrue(repaired["Changed"]); self.assertNotEqual(old,repaired["PreviousEventSha256"]); self.assertTrue(verify_project(self.project)["Ok"])

    def test_publication_failure_recovery_and_idempotence(self) -> None:
        run=self.project/"runs/run-publish"; run.mkdir(); policy={"schema_version":1,"protocol":"math-research-cycle-policy/v1","total_round_budget":4,"attempt_budget":2,"audit_interval_attempts":1,"max_route_family_attempts_per_cycle":2,"max_repair_batches_per_attempt":1,"audit_roles":["skeptic_quantifiers","skeptic_strategy","theory_tool_scout"]}; tickets={"schema_version":1,"cycle_id":"cycle-1","tickets":[{"ticket_id":"t1","route_family_id":"r","mechanism_id":"m","bottleneck_id":"b","decision_question":"q","search_domain":"d","success_signal":"s","stop_signal":"x","resource_caps":{"minutes":1},"reopen_condition":"new"}]}; (run/"cycle-policy.json").write_text(json.dumps(policy),encoding="utf-8"); (run/"cycle-tickets-000.json").write_text(json.dumps(tickets),encoding="utf-8"); initialize_cycle(run,"run-publish","a"*64,Path("cycle-policy.json"),Path("cycle-tickets-000.json")); invoke_action("AttemptStart",run,ticket_id="t1"); result=run/"result.md"; result.write_text("proved",encoding="utf-8"); invoke_action("AttemptEnd",run,outcome="proved_subclaim",artifact_file=result); write_signed_json(run/"run.json",{"run_directory":str(run.resolve()),"project":{"project_id":"project-0001"},"goal":{"observed_status":"active","goal_id":"g1"},"thread_id":"thread-1"})
        with self.assertRaisesRegex(ProjectArchiveError,"synthetic publication"): publish_checkpoint(self.project,run,fail_after_first_commit=True)
        self.assertTrue(read_json(self.project/"state/checkpoint.json","checkpoint")["recovery_required"]); published=publish_checkpoint(self.project,run); self.assertFalse(published["AlreadyPublished"]); self.assertGreaterEqual(len(published["PublishedArtifacts"]),2); again=publish_checkpoint(self.project,run); self.assertTrue(again["AlreadyPublished"])

    def test_status_is_structural_for_migration_required(self) -> None:
        legacy=self.root/"legacy"; legacy.mkdir(); (legacy/"record.md").write_text("old",encoding="utf-8"); created=initialize_project(self.vault,"project-two","project-0002","Decide S.",legacy_run_directories=[legacy]); second=Path(created["ProjectDirectory"]); self.assertEqual("required",project_status(second)["MigrationStatus"])
        with self.assertRaisesRegex(ProjectArchiveError,"legacy_semantic_archive_incomplete"): verify_project(second)

    def test_reviewed_legacy_semantic_migration_is_complete_and_tamper_evident(self) -> None:
        legacy=self.root/"legacy-full"; (legacy/"artifacts/bounded-scan").mkdir(parents=True); (legacy/"AttemptLedger.md").write_text("# Attempts\n\n### 2030-01-01 - route-one\n- Result: incomplete\n- Boundary: finite family only\n",encoding="utf-8"); (legacy/"BlockedLedger.md").write_text("# Blocks\n\n### 2030-01-01 - missing-tool\n- Stop reason: required tool unavailable\n\n### 2030-01-02 - bounded-method\n- Stop reason: method insufficient on the frozen family\n",encoding="utf-8"); (legacy/"SourceLedger.md").write_text("| Date | Source | Status |\n|---|---|---|\n| 2030 | Paper | partial audit |\n",encoding="utf-8"); (legacy/"SandboxSignals.md").write_text("| Date | Signal | Status |\n|---|---|---|\n| 2030 | scan | exploratory |\n",encoding="utf-8"); (legacy/"artifacts/bounded-scan/metadata.json").write_text('{"artifact_type":"SandboxSearch","candidate_status":"not-candidate"}',encoding="utf-8")
        created=initialize_project(self.vault,"project-three","project-0003","Decide S.",legacy_run_directories=[legacy]); project=Path(created["ProjectDirectory"]); analysis=analyze_legacy(project); self.assertEqual(6,analysis["recognized_count"]); self.assertEqual((1,1),(analysis["disposition_counts"]["operational_blocker"],analysis["disposition_counts"]["failure"])); analysis["review_status"]="approved"; reviewed=self.root/"reviewed.json"; reviewed.write_text(json.dumps(analysis),encoding="utf-8"); result=apply_legacy(project,reviewed,"No candidate; baseline unchanged."); self.assertEqual(6,result["Recognized"]); self.assertTrue(verify_project(project)["Ok"]); failure=next((project/"failures").glob("*.legacy-failure.json")); self.assertTrue(legacy_failure(failure)["Ok"]); manifest=read_json(project/"manifests/legacy-semantic-manifest.json","manifest"); target=project/Path(manifest["records"][0]["targets"][0]["path"]); target.write_text("tampered",encoding="utf-8")
        with self.assertRaisesRegex(ProjectArchiveError,"canonical target hash mismatch"): verify_legacy(project)

    def test_project_cli_success_and_blocked_routes(self) -> None:
        cli=Path(__file__).with_name("invoke_math_research_project_v2.py"); alias=Path(__file__).with_name("invoke_math_research_project.py"); vault=self.root/"cli-vault"; vault.mkdir(); source=self.root/"source.pdf"; source.write_bytes(b"pdf"); package=self.root/"contract-package.zip"; package.write_bytes(b"zip")
        created=subprocess.run([sys.executable,"-B",str(cli),"--action","Initialize","--vault-root",str(vault),"--project-directory-name","cli-project","--project-id","cli-project-0001","--problem-statement","Decide.","--additional-source-file",str(source),"--contract-package-file",str(package)],capture_output=True,text=True,env=os.environ.copy()); self.assertEqual(0,created.returncode,created.stderr); project=Path(json.loads(created.stdout)["ProjectDirectory"]); self.assertTrue((project/"sources/originals/source.pdf").is_file()); self.assertTrue((project/"history/contract-packages/contract-package.zip").is_file())
        for entry,action in ((cli,"Status"),(cli,"ResumePlan"),(cli,"Handoff"),(alias,"Verify")):
            result=subprocess.run([sys.executable,"-B",str(entry),"--action",action,"--project-directory",str(project)],capture_output=True,text=True,env=os.environ.copy()); self.assertEqual(0,result.returncode,result.stderr); self.assertTrue(json.loads(result.stdout)["Ok"])
        blocked=subprocess.run([sys.executable,"-B",str(cli),"--action","Verify"],capture_output=True,text=True,env=os.environ.copy()); self.assertEqual(2,blocked.returncode); self.assertFalse(json.loads(blocked.stderr)["ok"])


if __name__=="__main__": unittest.main()
