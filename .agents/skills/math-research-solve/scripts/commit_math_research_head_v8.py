#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
from math_research_head_v8 import HeadV8Error,commit_head
p=argparse.ArgumentParser();p.add_argument("--project-directory",required=True);p.add_argument("--candidate-head-file",required=True);p.add_argument("--expected-old-sha256",required=True);p.add_argument("--expected-old-control-generation",required=True);p.add_argument("--expected-new-control-generation",required=True,type=int);a=p.parse_args()
try:r=commit_head(Path(a.project_directory),Path(a.candidate_head_file),a.expected_old_sha256,a.expected_old_control_generation,a.expected_new_control_generation);code=0
except HeadV8Error as e:r={"schema":"math-research-head-commit-result/v8","committed":False,"reason":e.code,"detail":str(e)};code=1
print(json.dumps(r,ensure_ascii=False,separators=(",",":")));sys.exit(code)
