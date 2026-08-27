#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
from math_research_head_v8 import HeadV8Error,build_legacy_successor
p=argparse.ArgumentParser();p.add_argument("--project-directory",required=True);p.add_argument("--goal-objective-raw",required=True);p.add_argument("--goal-objective-sha256",required=True);p.add_argument("--goal-thread-id");p.add_argument("--dry-run",action="store_true");a=p.parse_args()
try:r=build_legacy_successor(Path(a.project_directory),a.goal_objective_raw,a.goal_objective_sha256,a.goal_thread_id,a.dry_run);code=0
except HeadV8Error as e:r={"schema":"math-research-legacy-successor-build-result/v8","built":False,"reason":e.code,"detail":str(e)};code=1
print(json.dumps(r,ensure_ascii=False,separators=(",",":")));sys.exit(code)
