#!/usr/bin/env python3
"""Native schema router for frozen Startup v4-v8 entrypoints."""
import argparse, json, subprocess, sys
from pathlib import Path
from math_research_control_primitives import assert_no_symlink_chain, strict_json_loads

SCHEMA_ENGINE={"math-research-project/v9":"math_research_state_v9.py","math-research-project/v10":"math_research_state_v10.py","math-research-project/v11":"math_research_state_v11.py","math-research-project/v12":"math_research_state_v12.py","math-research-project/v13":"math_research_state_v13.py"}
VERSION_TARGET={4:9,5:10,6:11,7:12,8:13}

def invoke(version:int,project:Path,audit_mode:str="Auto",goal_status:str="none",runner=None)->dict:
    if version not in VERSION_TARGET or audit_mode not in {"Auto","Full"}: raise ValueError("startup version or audit mode is invalid")
    project=assert_no_symlink_chain(project); head_path=assert_no_symlink_chain(project/"project.json")
    if not head_path.is_file(): raise ValueError(f"project.json is absent: {project}")
    head=strict_json_loads(head_path.read_text(encoding="utf-8",errors="strict")); schema=head.get("schema"); target=f"math-research-project/v{VERSION_TARGET[version]}"
    if schema==target:
        engine=Path(__file__).with_name(SCHEMA_ENGINE[target]); argv=[sys.executable,"-B",str(engine),"startup","--project",str(project)];
        if audit_mode=="Full": argv.append("--full" if version>=6 else "--audit-mode=Full")
        if version<=5: argv.append(f"--legacy-goal-status={goal_status}")
        completed=(runner or subprocess.run)(argv,capture_output=True,text=True)
        if completed.returncode: raise RuntimeError(completed.stderr or f"Startup v{version} failed with {completed.returncode}")
        value=strict_json_loads(completed.stdout); return value.get("data",value) if isinstance(value,dict) else value
    if version==4:
        legacy=Path(__file__).with_name("invoke_math_research_startup_v3.py"); argv=[sys.executable,"-B",str(legacy),"--project-directory",str(project),"--goal-status",goal_status]
    else:
        return invoke(version-1,project,audit_mode,goal_status,runner)
    completed=(runner or subprocess.run)(argv,capture_output=True,text=True)
    if completed.returncode: raise RuntimeError(completed.stderr or "Startup v3 delegation failed")
    return strict_json_loads(completed.stdout)

def main(version:int,argv=None)->int:
    p=argparse.ArgumentParser(); p.add_argument("--project-path","-ProjectPath",required=True,type=Path); p.add_argument("--audit-mode","-AuditMode",choices=("Auto","Full"),default="Auto"); p.add_argument("--goal-status","-GoalStatus",default="none"); a=p.parse_args(argv)
    try: print(json.dumps(invoke(version,a.project_path,a.audit_mode,a.goal_status),ensure_ascii=False,separators=(",",":"))); return 0
    except Exception as exc: print(json.dumps({"ok":False,"error":str(exc)},ensure_ascii=False,separators=(",",":")),file=sys.stderr); return 2
