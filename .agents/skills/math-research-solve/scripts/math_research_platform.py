#!/usr/bin/env python3
"""Cross-platform launcher for the current math-research-solve production entries.

Windows keeps the installed PowerShell entry points unchanged.  POSIX callers
use this launcher: v10 and v9 operations run in their versioned Python engines,
while the frozen v8 implementation runs with PowerShell 7.5+ (`pwsh`).
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path


MIN_PYTHON = (3, 12)
MIN_PWSH = (7, 5, 0)
SCRIPT_DIR = Path(__file__).resolve().parent
ENGINE_V9 = SCRIPT_DIR / "math_research_state_v9.py"
ENGINE_V10 = SCRIPT_DIR / "math_research_state_v10.py"


def child_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.setdefault("PYTHONUTF8", "1")
    return env


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def find_pwsh() -> str | None:
    override = os.environ.get("MATH_RESEARCH_PWSH")
    if override is not None:
        path = Path(override).expanduser()
        return str(path.resolve()) if path.is_file() else None
    return shutil.which("pwsh")


def pwsh_version(executable: str) -> tuple[int, int, int] | None:
    try:
        result = subprocess.run(
            [executable, "-NoLogo", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=child_env(),
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.match(r"\s*(\d+)\.(\d+)(?:\.(\d+))?", result.stdout)
    if result.returncode != 0 or not match:
        return None
    return tuple(int(value or 0) for value in match.groups())


def doctor(as_json: bool) -> int:
    os_name = platform.system()
    py_ok = sys.version_info >= MIN_PYTHON
    supported_os = os_name in {"Windows", "Linux", "Darwin"}
    engine_ok = ENGINE_V9.is_file() and ENGINE_V10.is_file()
    pwsh = find_pwsh()
    version = pwsh_version(pwsh) if pwsh else None
    pwsh_ok = version is not None and version >= MIN_PWSH
    checks = {
        "os_supported": supported_os,
        "python_3_12_or_newer": py_ok,
        "state_engine_present": engine_ok,
        "powershell_7_5_or_newer": pwsh_ok,
    }
    ok = all(checks.values())
    payload = {
        "schema": "math-research-platform-doctor/v1",
        "ok": ok,
        "os": os_name,
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "powershell": ".".join(map(str, version)) if version else None,
        "checks": checks,
        "network_used": False,
        "privileged_change_performed": False,
    }
    if as_json:
        emit(payload)
    else:
        for name, passed in checks.items():
            print(f"{'PASS' if passed else 'FAIL'} {name}")
        if not pwsh_ok:
            print("PowerShell 7.5+ is required for the frozen v8 entries; no installation was attempted.", file=sys.stderr)
    if not supported_os:
        return 31
    if not py_ok or (pwsh and version and version < MIN_PWSH):
        return 11
    if not pwsh:
        return 10
    return 0 if ok else 50


def run_passthrough(command: list[str]) -> int:
    try:
        completed = subprocess.run(command, env=child_env(), check=False)
    except OSError as exc:
        print(f"Unable to start required runtime: {type(exc).__name__}", file=sys.stderr)
        return 40
    return int(completed.returncode)


def run_engine(arguments: list[str], *, version: int, capture: bool = False) -> subprocess.CompletedProcess[str] | int:
    engine = ENGINE_V10 if version == 10 else ENGINE_V9
    command = [sys.executable, "-B", str(engine), *arguments]
    if not capture:
        return run_passthrough(command)
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=child_env(),
        check=False,
    )


def require_pwsh() -> str | None:
    executable = find_pwsh()
    version = pwsh_version(executable) if executable else None
    if executable is None:
        print("PowerShell 7.5+ (pwsh) is required for this v8 operation; no installation was attempted.", file=sys.stderr)
        return None
    if version is None or version < MIN_PWSH:
        print("The available pwsh is older than PowerShell 7.5 or could not be verified.", file=sys.stderr)
        return None
    return executable


def run_ps1(script: str, arguments: list[str]) -> int:
    pwsh = require_pwsh()
    if not pwsh:
        return 10
    return run_passthrough([pwsh, "-NoLogo", "-NoProfile", "-File", str(SCRIPT_DIR / script), *arguments])


def command_startup(args: argparse.Namespace) -> int:
    result = run_engine(
        ["startup", "--project", args.project, "--audit-mode", args.audit_mode,
         "--legacy-goal-status", args.goal_status],
        version=10,
        capture=True,
    )
    assert isinstance(result, subprocess.CompletedProcess)
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        return int(result.returncode)
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        sys.stdout.write(result.stdout)
        return 50
    if parsed.get("ok") and parsed.get("data", {}).get("classification") == "delegate_startup_v4":
        return run_ps1(
            "invoke_math_research_startup_v4.ps1",
            ["-ProjectPath", args.project, "-AuditMode", args.audit_mode, "-GoalStatus", args.goal_status],
        )
    sys.stdout.write(result.stdout.rstrip("\r\n") + "\n")
    return 0


def command_ticket_preflight(args: argparse.Namespace) -> int:
    argv = ["ticket-preflight-v8", "--project", args.project, "--ticket", args.ticket,
            "--source-requirements", args.source_requirements]
    if args.access_log:
        argv.extend(["--access-log", args.access_log])
    result = run_engine(argv, version=9)
    assert isinstance(result, int)
    return result


def command_prepare_successor(args: argparse.Namespace) -> int:
    result = run_engine(["prepare-successor", "--predecessor-project", args.predecessor_project,
                         "--successor-project", args.successor_project, "--spec", args.spec,
                         "--output", args.output], version=args.engine_version)
    assert isinstance(result, int)
    return result


def command_prepare_transition(args: argparse.Namespace) -> int:
    result = run_engine(["prepare", "--project", args.project, "--transition", args.transition,
                         "--payload", args.payload, "--output", args.output,
                         "--audit-mode", args.audit_mode], version=args.engine_version)
    assert isinstance(result, int)
    return result


def command_commit_transition(args: argparse.Namespace) -> int:
    result = run_engine(["commit", "--plan", args.plan, "--goal-status", args.goal_status], version=args.engine_version)
    assert isinstance(result, int)
    return result


def command_migrate_v8(args: argparse.Namespace) -> int:
    command = [sys.executable, "-B", str(SCRIPT_DIR / "math_research_migrate_v8_to_v10.py"), args.migration_action, "--predecessor", args.predecessor]
    if args.migration_action == "prepare":
        if not all((args.successor, args.bootstrap, args.output)):
            print("migrate-v8-to-v10 prepare requires --successor, --bootstrap, and --output.", file=sys.stderr)
            return 2
        command.extend(["--successor", args.successor, "--bootstrap", args.bootstrap, "--output", args.output])
    elif args.migration_action == "freeze":
        if not args.plan:
            print("migrate-v8-to-v10 freeze requires --plan.", file=sys.stderr)
            return 2
        command.extend(["--plan", args.plan])
    elif args.migration_action == "verify":
        if not args.successor or not args.plan:
            print("migrate-v8-to-v10 verify requires --successor and --plan.", file=sys.stderr)
            return 2
        command.extend(["--successor", args.successor, "--plan", args.plan])
    return run_passthrough(command)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("doctor")
    p.add_argument("--json", action="store_true")
    p.set_defaults(handler=lambda a: doctor(a.json))

    p = sub.add_parser("startup")
    p.add_argument("--project", required=True)
    p.add_argument("--audit-mode", choices=("Auto", "Full"), default="Auto")
    p.add_argument("--goal-status", choices=("none", "active", "paused", "complete", "blocked"), default="none")
    p.set_defaults(handler=command_startup)

    p = sub.add_parser("ticket-preflight-v8")
    p.add_argument("--project", required=True); p.add_argument("--ticket", required=True)
    p.add_argument("--source-requirements", required=True); p.add_argument("--access-log")
    p.set_defaults(handler=command_ticket_preflight)

    p = sub.add_parser("ticket-preflight-v10")
    p.add_argument("--project", required=True); p.add_argument("--ticket", required=True); p.add_argument("--access-log")
    p.set_defaults(handler=lambda a: run_engine(["ticket-preflight-v10", "--project", a.project, "--ticket", a.ticket] + (["--access-log", a.access_log] if a.access_log else []), version=10))

    p = sub.add_parser("build-legacy-successor-v8")
    p.add_argument("--project-directory", required=True); p.add_argument("--goal-objective-raw", required=True)
    p.add_argument("--goal-objective-sha256", required=True); p.add_argument("--goal-thread-id")
    p.add_argument("--output-directory"); p.add_argument("--dry-run", action="store_true")
    p.set_defaults(handler=lambda a: run_ps1("build_math_research_legacy_successor_v8.ps1",
        ["-ProjectDirectory", a.project_directory, "-GoalObjectiveRaw", a.goal_objective_raw,
         "-GoalObjectiveSha256", a.goal_objective_sha256]
        + (["-GoalThreadId", a.goal_thread_id] if a.goal_thread_id else [])
        + (["-OutputDirectory", a.output_directory] if a.output_directory else [])
        + (["-DryRun"] if a.dry_run else [])))

    p = sub.add_parser("commit-head-v8")
    p.add_argument("--project-directory", required=True); p.add_argument("--candidate-head-file", required=True)
    p.add_argument("--expected-old-sha256", required=True); p.add_argument("--expected-old-control-generation", required=True)
    p.add_argument("--expected-new-control-generation", required=True, type=int)
    p.set_defaults(handler=lambda a: run_ps1("commit_math_research_head_v8.ps1",
        ["-ProjectDirectory", a.project_directory, "-CandidateHeadFile", a.candidate_head_file,
         "-ExpectedOldSha256", a.expected_old_sha256,
         "-ExpectedOldControlGeneration", a.expected_old_control_generation,
         "-ExpectedNewControlGeneration", str(a.expected_new_control_generation)]))

    p = sub.add_parser("migrate-v8-to-v10")
    p.add_argument("migration_action", choices=("inspect", "prepare", "freeze", "verify"))
    p.add_argument("--predecessor", required=True); p.add_argument("--successor")
    p.add_argument("--bootstrap"); p.add_argument("--output"); p.add_argument("--plan")
    p.set_defaults(handler=command_migrate_v8)

    p = sub.add_parser("prepare-successor-v9")
    p.add_argument("--predecessor-project", required=True); p.add_argument("--successor-project", required=True)
    p.add_argument("--spec", required=True); p.add_argument("--output", required=True)
    p.set_defaults(handler=command_prepare_successor, engine_version=9)

    p = sub.add_parser("prepare-successor-v10")
    p.add_argument("--predecessor-project", required=True); p.add_argument("--successor-project", required=True)
    p.add_argument("--spec", required=True); p.add_argument("--output", required=True)
    p.set_defaults(handler=command_prepare_successor, engine_version=10)

    p = sub.add_parser("prepare-transition-v9")
    p.add_argument("--project", required=True)
    p.add_argument("--transition", required=True, choices=("ATTEMPT_START", "SOLVER_COMPLETE", "VERIFIER_COMPLETE", "ATTEMPT_END", "CHECKPOINT_COMMIT"))
    p.add_argument("--payload", required=True); p.add_argument("--output", required=True)
    p.add_argument("--audit-mode", choices=("Auto", "Full"), default="Auto")
    p.set_defaults(handler=command_prepare_transition, engine_version=9)

    p = sub.add_parser("prepare-transition-v10")
    p.add_argument("--project", required=True)
    p.add_argument("--transition", required=True, choices=("ATTEMPT_START", "SOLVER_COMPLETE", "VERIFIER_COMPLETE", "ATTEMPT_END", "CHECKPOINT_COMMIT", "RESEARCH_CHECKPOINT"))
    p.add_argument("--payload", required=True); p.add_argument("--output", required=True)
    p.add_argument("--audit-mode", choices=("Auto", "Full"), default="Auto")
    p.set_defaults(handler=command_prepare_transition, engine_version=10)

    p = sub.add_parser("commit-transition-v9")
    p.add_argument("--plan", required=True)
    p.add_argument("--goal-status", required=True, choices=("none", "active", "paused", "complete", "blocked"))
    p.set_defaults(handler=command_commit_transition, engine_version=9)

    p = sub.add_parser("commit-transition-v10")
    p.add_argument("--plan", required=True)
    p.add_argument("--goal-status", required=True, choices=("none", "active", "paused", "complete", "blocked"))
    p.set_defaults(handler=command_commit_transition, engine_version=10)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if sys.version_info < MIN_PYTHON:
        print("Python 3.12 or newer is required; no installation was attempted.", file=sys.stderr)
        return 11
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
