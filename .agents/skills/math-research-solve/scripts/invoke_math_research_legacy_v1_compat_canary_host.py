#!/usr/bin/env python3
"""Native compatibility canary host for migrated v3-v6 runs."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from MathResearchLauncherV2 import LauncherError, invoke_launcher_canary, select_codex_executable
from math_research_control_primitives import read_signed_json

def invoke(run:Path,manifest_path:Path,*,entry_name:str="launch_math_research_legacy_v1_compat.py",attestation=None,invoker=None)->dict:
    scripts=Path(__file__).resolve().parent; manifest=read_signed_json(manifest_path)["payload"]
    if manifest.get("prompt_version")!="v6" or manifest.get("config",{}).get("approval_mode")!="approve_for_me": raise LauncherError("compatibility canary requires applied Prompt v6 approve_for_me amendment")
    selected=attestation or select_codex_executable(); pinned=manifest.get("executable",{})
    if selected["version"]!=pinned.get("version") or selected["sha256"]!=pinned.get("sha256"): raise LauncherError("compatibility canary executable differs from signed manifest")
    return invoke_launcher_canary(attestation=selected,run_directory=run,manifest_path=manifest_path,launcher_entry_path=scripts/entry_name,launcher_module_path=scripts/"MathResearchLauncherV2.py",canary_entry_path=scripts/"invoke_math_research_canary_v2.py",cycle_cli_path=scripts/"invoke_math_research_cycle_legacy_v1_compat.py",approval_mode="approve_for_me",model=manifest["config"]["model"],reasoning_effort=manifest["config"]["reasoning_effort"],web_search=manifest["config"]["web_search"],max_child_agents=int(manifest["config"]["max_child_agents"]),invoker=invoker)

def main(argv=None)->int:
    p=argparse.ArgumentParser(); p.add_argument("--run-directory","-RunDirectory",required=True,type=Path); p.add_argument("--manifest-path","-ManifestPath",required=True,type=Path); a=p.parse_args(argv)
    try: print(json.dumps(invoke(a.run_directory,a.manifest_path),separators=(",",":"))); return 0
    except Exception as exc: print(json.dumps({"ok":False,"error":str(exc)},separators=(",",":")),file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
