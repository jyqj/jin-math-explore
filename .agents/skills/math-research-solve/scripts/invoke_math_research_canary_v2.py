#!/usr/bin/env python3
"""Native run-local control-path canary. It performs no research mutation."""

import argparse, json, os, subprocess, sys
from pathlib import Path
from MathResearchLauncherV2 import LauncherError, read_json_file, sha_file, sha_text
from math_research_control_primitives import assert_no_symlink_chain


def require(value: bool,message: str) -> None:
    if not value: raise LauncherError(message)


def tree_digest(root: Path) -> str:
    require(root.is_dir(),"cycle ledger is missing"); records=[]
    for item in sorted(root.rglob("*"),key=str):
        if item.is_file(): assert_no_symlink_chain(item); records.append(f"{item.relative_to(root).as_posix()}\0{item.stat().st_size}\0{sha_file(item)}")
    return sha_text("\n".join(records))


def invoke(run_directory: Path,challenge_file: Path,expected_challenge_sha256: str) -> dict:
    run=assert_no_symlink_chain(run_directory); challenge_path=assert_no_symlink_chain(challenge_file); require(challenge_path.parent.resolve()==run.resolve() and challenge_path.name=="launcher-canary-challenge-v2.json","challenge location is invalid"); require(sha_file(challenge_path)==expected_challenge_sha256,"challenge hash differs"); challenge=read_json_file(challenge_path); require(challenge.get("schema_version")==2 and challenge.get("protocol")=="math-research-launcher-canary/v2" and Path(challenge["run_directory"]).resolve()==run.resolve(),"challenge protocol/run mismatches")
    self_path=Path(__file__).resolve(); require(Path(challenge["canary_entry_path"]).resolve()==self_path and challenge["canary_entry_sha256"]==sha_file(self_path),"canary entry attestation mismatches"); manifest=Path(challenge["manifest_path"]); require(manifest.parent.resolve()==run.resolve() and manifest.name=="run.json" and sha_file(manifest)==challenge["manifest_sha256"],"manifest binding mismatches"); cycle=Path(challenge["cycle_cli_path"]); require(sha_file(cycle)==challenge["cycle_cli_sha256"],"cycle CLI binding mismatches")
    before=tree_digest(run/"cycle-ledger"); completed=subprocess.run([sys.executable,"-B",str(cycle),"--action","Status","--run-directory",str(run)],capture_output=True,text=True,env=os.environ.copy()); require(completed.returncode==0 and completed.stdout.strip(),"cycle Status failed"); status=json.loads(completed.stdout); after=tree_digest(run/"cycle-ledger"); require(before==after,"cycle Status changed ledger")
    scratch=run/"launcher-canary-scratch-v2.tmp"; created=False
    try:
        with scratch.open("x",encoding="utf-8") as stream: stream.write(challenge["nonce"]); stream.flush(); os.fsync(stream.fileno())
        created=sha_file(scratch)==sha_text(challenge["nonce"]); require(created,"scratch read-back failed")
    finally: scratch.unlink(missing_ok=True)
    evidence={"schema_version":2,"protocol":"math-research-launcher-canary/v2","challenge_nonce":challenge["nonce"],"run_manifest_sha256":challenge["manifest_sha256"],"challenge_sha256":expected_challenge_sha256,"ledger_before_sha256":before,"ledger_after_sha256":after,"cycle_status_sha256":sha_text(completed.stdout.strip()),"cycle_status_exit_code":0,"attempt_count":status["AttemptCount"],"total_round_count":status["TotalRoundCount"],"scratch_created":created,"scratch_removed":not scratch.exists()}; path=run/"launcher-canary-evidence-v2.json"; require(not path.exists(),"canary evidence already exists"); path.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding="utf-8"); require(read_json_file(path)["challenge_nonce"]==challenge["nonce"],"evidence read-back failed"); return evidence


def main(argv=None) -> int:
    p=argparse.ArgumentParser(); p.add_argument("--run-directory","-RunDirectory",required=True,type=Path); p.add_argument("--challenge-file","-ChallengeFile",required=True,type=Path); p.add_argument("--expected-challenge-sha256","-ExpectedChallengeSha256",required=True); a=p.parse_args(argv)
    try: print(json.dumps(invoke(a.run_directory,a.challenge_file,a.expected_challenge_sha256),ensure_ascii=False,separators=(",",":"))); return 0
    except (LauncherError,OSError,ValueError,KeyError,json.JSONDecodeError) as exc: print(json.dumps({"ok":False,"error":str(exc)},ensure_ascii=False,separators=(",",":")),file=sys.stderr); return 2


if __name__=="__main__": raise SystemExit(main())
