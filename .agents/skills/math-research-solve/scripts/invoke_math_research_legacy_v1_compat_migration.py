#!/usr/bin/env python3
"""Native CLI for legacy-v1 compatibility migration."""

import argparse, json, sys
from pathlib import Path
from MathResearchLegacyV1CompatMigration import CompatibilityMigrationError, invoke
from math_research_control_primitives import ControlIntegrityError


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--action","-Action",required=True,choices=["Analyze","Apply","Verify"]); parser.add_argument("--run-directory","-RunDirectory",required=True,type=Path); parser.add_argument("--receipt-file","-ReceiptFile",required=True,type=Path); args=parser.parse_args(argv); root=Path(__file__).resolve().parent
    paths={"launcher_entry":root/"launch_math_research_legacy_v1_compat.py","launcher_module":root/"MathResearchLauncherV2.py","cycle_module":root/"MathResearchCycleLedgerV2.py","cycle_cli":root/"invoke_math_research_cycle_legacy_v1_compat.py","project_module":root/"MathResearchProjectArchiveV2.py","canary_host":root/"invoke_math_research_legacy_v1_compat_canary_host.py","canary_entry":root/"invoke_math_research_canary_v2.py"}
    try: print(json.dumps(invoke(args.action,args.run_directory,args.receipt_file,paths),ensure_ascii=False,sort_keys=True,separators=(",",":"))); return 0
    except (CompatibilityMigrationError,ControlIntegrityError,OSError,ValueError) as exc: print(json.dumps({"ok":False,"error":str(exc)},ensure_ascii=False,sort_keys=True,separators=(",",":")),file=sys.stderr); return 2


if __name__=="__main__": raise SystemExit(main())
