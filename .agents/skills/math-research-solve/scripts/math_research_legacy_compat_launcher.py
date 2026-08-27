#!/usr/bin/env python3
"""Receipt-gated native Resume path for migrated legacy v1 launchers."""
import argparse, json, sys
from pathlib import Path
from MathResearchLegacyV1CompatMigration import read_receipt, validate_state
from MathResearchLegacyV1ControlPathAmendmentV2 import validate_state as validate_amendment
from invoke_math_research_legacy_v1_compat_canary_host import invoke as invoke_canary_host
from math_research_control_primitives import read_signed_json
from math_research_launcher_v6_cli import launch_v6

def native_paths(root:Path,v2:bool=False)->dict:
    base={"launcher_entry":root/("launch_math_research_legacy_v1_compat_v2.py" if v2 else "launch_math_research_legacy_v1_compat.py"),"launcher_module":root/"MathResearchLauncherV2.py","cycle_module":root/"MathResearchCycleLedgerV2.py","cycle_cli":root/"invoke_math_research_cycle_legacy_v1_compat.py","project_module":root/"MathResearchProjectArchiveV2.py","canary_host":root/("invoke_math_research_legacy_v1_compat_canary_host_v2.py" if v2 else "invoke_math_research_legacy_v1_compat_canary_host.py"),"canary_entry":root/"invoke_math_research_canary_v2.py"}; return base

def main(argv=None,v2:bool=False)->int:
    p=argparse.ArgumentParser(); p.add_argument("--mode","-Mode",required=True); p.add_argument("--run-directory","-RunDirectory",required=True,type=Path); p.add_argument("--continuation-prompt-file","-ContinuationPromptFile",required=True,type=Path); p.add_argument("--migration-receipt-file","-MigrationReceiptFile",required=True,type=Path); p.add_argument("--control-path-receipt-file","-ControlPathReceiptFile",type=Path); a=p.parse_args(argv)
    try:
        if a.mode!="Resume": raise ValueError("legacy compatibility launcher is Resume-only")
        root=Path(__file__).resolve().parent; manifest=read_signed_json(a.run_directory/"run.json")["payload"]; prior=read_receipt(a.migration_receipt_file); paths=native_paths(root,False); validate_state(manifest,a.run_directory,prior,paths,require_applied=True)
        if v2:
            if a.control_path_receipt_file is None: raise ValueError("v2 requires control-path receipt")
            amended=read_receipt(a.control_path_receipt_file); all_paths={"prior_launcher_entry":paths["launcher_entry"],**native_paths(root,True),"argv_compat_module":root/"MathResearchApproveForMeArgvCompatV2.py","prior_canary_host":paths["canary_host"],"canary_module":root/"MathResearchLauncherV2.py","amendment_module":root/"MathResearchLegacyV1ControlPathAmendmentV2.py","amendment_cli":root/"invoke_math_research_legacy_v1_control_path_amendment_v2.py"}; validate_amendment(manifest,a.run_directory,amended,prior,all_paths,require_applied=True)
        def hook(current,attestation):
            result=invoke_canary_host(a.run_directory,a.run_directory/"run.json",entry_name=("launch_math_research_legacy_v1_compat_v2.py" if v2 else "launch_math_research_legacy_v1_compat.py"),attestation=attestation); current.setdefault("compatibility_migration",{})["canary"]={"passed":result["Passed"],"reused":result["Reused"],"receipt_path":result["ReceiptPath"],"binding_sha256":result["BindingSha256"]}
        result=launch_v6(mode="Resume",run_directory=a.run_directory,continuation_prompt_file=a.continuation_prompt_file,resume_hook=hook); print(json.dumps({"ok":True,"status":result["status"],"thread_id":result["thread_id"]},separators=(",",":"))); return 0
    except Exception as exc: print(json.dumps({"ok":False,"error":str(exc)},separators=(",",":")),file=sys.stderr); return 2
