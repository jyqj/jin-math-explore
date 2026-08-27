#!/usr/bin/env python3
"""Receipt-gated native compatibility canary host v2."""
import argparse, json, sys
from pathlib import Path
from MathResearchLegacyV1CompatMigration import read_receipt
from MathResearchLegacyV1ControlPathAmendmentV2 import validate_state
from invoke_math_research_legacy_v1_compat_canary_host import invoke
from math_research_control_primitives import read_signed_json

def main(argv=None)->int:
    p=argparse.ArgumentParser(); p.add_argument("--run-directory","-RunDirectory",required=True,type=Path); p.add_argument("--manifest-path","-ManifestPath",required=True,type=Path); p.add_argument("--migration-receipt-file","-MigrationReceiptFile",required=True,type=Path); p.add_argument("--control-path-receipt-file","-ControlPathReceiptFile",required=True,type=Path); a=p.parse_args(argv)
    try:
        scripts=Path(__file__).resolve().parent; manifest=read_signed_json(a.manifest_path)["payload"]; prior=read_receipt(a.migration_receipt_file); amendment=read_receipt(a.control_path_receipt_file); paths={"prior_launcher_entry":scripts/"launch_math_research_legacy_v1_compat.py","launcher_entry":scripts/"launch_math_research_legacy_v1_compat_v2.py","launcher_module":scripts/"MathResearchLauncherV2.py","argv_compat_module":scripts/"MathResearchApproveForMeArgvCompatV2.py","prior_canary_host":scripts/"invoke_math_research_legacy_v1_compat_canary_host.py","canary_host":Path(__file__).resolve(),"canary_module":scripts/"MathResearchLauncherV2.py","canary_entry":scripts/"invoke_math_research_canary_v2.py","cycle_module":scripts/"MathResearchCycleLedgerV2.py","cycle_cli":scripts/"invoke_math_research_cycle_legacy_v1_compat.py","project_module":scripts/"MathResearchProjectArchiveV2.py","amendment_module":scripts/"MathResearchLegacyV1ControlPathAmendmentV2.py","amendment_cli":scripts/"invoke_math_research_legacy_v1_control_path_amendment_v2.py"}; validate_state(manifest,a.run_directory,amendment,prior,paths,require_applied=True); print(json.dumps(invoke(a.run_directory,a.manifest_path,entry_name="launch_math_research_legacy_v1_compat_v2.py"),separators=(",",":"))); return 0
    except Exception as exc: print(json.dumps({"ok":False,"error":str(exc)},separators=(",",":")),file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
