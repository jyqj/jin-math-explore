#!/usr/bin/env python3
"""Native CLI for project archive operations."""

from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from MathResearchProjectArchiveV2 import *
from MathResearchLegacyArchive import analyze, apply, legacy_failure, verify as verify_semantic
from math_research_control_primitives import ControlIntegrityError

ACTIONS=("Initialize","Verify","StructuralOnly","Status","ResumePlan","AnalyzeLegacy","ApplyLegacyMigration","VerifySemanticArchive","ValidateFailure","ValidateLegacyFailure","ValidateSources","CheckRoute","RegisterContract","PublishCheckpoint","Handoff","RepairEventTail")


def build_parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(); p.add_argument("--action","-Action",required=True,choices=ACTIONS); p.add_argument("--project-directory","-ProjectDirectory",type=Path); p.add_argument("--vault-root","-VaultRoot",type=Path); p.add_argument("--project-directory-name","-ProjectDirectoryName"); p.add_argument("--project-id","-ProjectId"); p.add_argument("--problem-statement","-ProblemStatement"); p.add_argument("--seed-directory","-SeedDirectory",type=Path); p.add_argument("--source-workspace","-SourceWorkspace",type=Path); p.add_argument("--legacy-run-directory","-LegacyRunDirectories",action="append",type=Path,default=[]); p.add_argument("--additional-source-file","-AdditionalSourceFiles",action="append",type=Path,default=[]); p.add_argument("--contract-package-file","-ContractPackageFiles",action="append",type=Path,default=[]); p.add_argument("--failure-record-file","-FailureRecordFile",type=Path); p.add_argument("--manifest-file","-ManifestFile",type=Path); p.add_argument("--current-conclusion","-CurrentConclusion"); p.add_argument("--claim-sha256","-ClaimSha256",action="append",default=[]); p.add_argument("--expected-attempt-id","-ExpectedAttemptId"); p.add_argument("--artifact-root","-ArtifactRoot",type=Path); p.add_argument("--ticket-file","-TicketFile",type=Path); p.add_argument("--contract-file","-ContractFile",type=Path); p.add_argument("--contract-binding-sha256","-ContractBindingSha256"); p.add_argument("--contract-version","-ContractVersion"); p.add_argument("--run-directory","-RunDirectory",type=Path); p.add_argument("--handoff-label","-HandoffLabel",default="handoff"); return p


def required(value, label: str):
    if value is None or isinstance(value,str) and not value.strip(): raise ProjectArchiveError(f"{label} is required")
    return value


def dispatch(a) -> dict:
    if a.action=="Initialize": return initialize_project(required(a.vault_root,"VaultRoot"),required(a.project_directory_name,"ProjectDirectoryName"),required(a.project_id,"ProjectId"),required(a.problem_statement,"ProblemStatement"),seed_directory=a.seed_directory,source_workspace=a.source_workspace,legacy_run_directories=a.legacy_run_directory,additional_source_files=a.additional_source_file,contract_package_files=a.contract_package_file)
    if a.action=="Verify": return verify_project(required(a.project_directory,"ProjectDirectory"))
    if a.action=="StructuralOnly": return verify_project(required(a.project_directory,"ProjectDirectory"),structural_only=True)
    if a.action=="Status": return project_status(required(a.project_directory,"ProjectDirectory"))
    if a.action=="ResumePlan": return resume_plan(required(a.project_directory,"ProjectDirectory"))
    if a.action=="AnalyzeLegacy": return analyze(required(a.project_directory,"ProjectDirectory"))
    if a.action=="ApplyLegacyMigration": return apply(required(a.project_directory,"ProjectDirectory"),required(a.manifest_file,"ManifestFile"),a.current_conclusion or "Legacy material migrated; migration alone promotes no candidate and changes no baseline.")
    if a.action=="VerifySemanticArchive": return verify_semantic(required(a.project_directory,"ProjectDirectory"))
    if a.action=="ValidateFailure": return failure_record(required(a.failure_record_file,"FailureRecordFile"),a.expected_attempt_id,a.artifact_root)
    if a.action=="ValidateLegacyFailure": return legacy_failure(required(a.failure_record_file,"FailureRecordFile"))
    if a.action=="ValidateSources": return source_claims(required(a.project_directory,"ProjectDirectory"),a.claim_sha256)
    if a.action=="CheckRoute": return route_start(required(a.project_directory,"ProjectDirectory"),read_json(required(a.ticket_file,"TicketFile"),"route ticket"))
    if a.action=="RegisterContract": return register_contract(required(a.project_directory,"ProjectDirectory"),required(a.contract_file,"ContractFile"),required(a.contract_binding_sha256,"ContractBindingSha256"),required(a.contract_version,"ContractVersion"),required(a.run_directory,"RunDirectory"))
    if a.action=="PublishCheckpoint": return publish_checkpoint(required(a.project_directory,"ProjectDirectory"),required(a.run_directory,"RunDirectory"))
    if a.action=="Handoff": return new_handoff(required(a.project_directory,"ProjectDirectory"),a.handoff_label)
    if a.action=="RepairEventTail": return repair_event_tail(required(a.project_directory,"ProjectDirectory"))
    raise ProjectArchiveError("unsupported action")


def main(argv=None) -> int:
    try: result=dispatch(build_parser().parse_args(argv)); print(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(",",":"))); return 0
    except (ProjectArchiveError,ControlIntegrityError,OSError,UnicodeError,ValueError) as exc: print(json.dumps({"ok":False,"error":str(exc)},ensure_ascii=False,sort_keys=True,separators=(",",":")),file=sys.stderr); return 2


if __name__=="__main__": raise SystemExit(main())
