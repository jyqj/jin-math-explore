#!/usr/bin/env python3
"""Cross-platform safe-stop entry for native math-research runs."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from math_research_control_primitives import (
    ControlIntegrityError,
    FileLease,
    assert_no_symlink_chain,
    current_user_scope_id,
    read_signed_json,
    write_signed_json,
)
from math_research_process_control import ProcessControlError, terminate_bound_scope
from math_research_process_identity import process_identity_matches


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def require_manifest(value: Any, run: Path) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ControlIntegrityError("run manifest must be an object")
    required = {"schema", "schema_version", "run_id", "thread_id", "run_directory", "process"}
    if not required.issubset(value):
        raise ControlIntegrityError("run manifest is missing control fields")
    if value["schema"] != "math-research-run/v2" or value["schema_version"] != 2:
        raise ControlIntegrityError("unsupported native run manifest schema")
    if Path(str(value["run_directory"])) != run:
        raise ControlIntegrityError("run manifest directory binding mismatches")
    if not isinstance(value["run_id"], str) or not value["run_id"]:
        raise ControlIntegrityError("run manifest ID is invalid")
    process = value["process"]
    if not isinstance(process, dict) or set(process) != {"identity", "termination_scope"}:
        raise ControlIntegrityError("run manifest process record is invalid")
    if not process_identity_matches(process["identity"]):
        raise ControlIntegrityError("run manifest process identity is not live and exact")
    return value


def stop(run_directory: Path) -> dict[str, Any]:
    run = assert_no_symlink_chain(run_directory)
    if not run.is_dir():
        raise ControlIntegrityError("run directory is missing")
    with FileLease("run", str(run)):
        manifest = require_manifest(read_signed_json(run / "run.json")["payload"], run)
        process = manifest["process"]
        request_path = run / "stop-request.json"
        request = {
            "schema": "math-research-stop-request/v2",
            "run_id": manifest["run_id"],
            "thread_id": manifest["thread_id"],
            "target_identity": process["identity"],
            "target_termination_scope": process["termination_scope"],
            "requested_at_utc": utc_now(),
            "requested_by_scope": current_user_scope_id(),
        }
        write_signed_json(request_path, request)
        termination = terminate_bound_scope(process["identity"], process["termination_scope"])
        return {
            "ok": True,
            "run_directory": str(run),
            "thread_id": manifest["thread_id"],
            "stopped_pid": process["identity"]["pid"],
            "stop_request": str(request_path),
            "termination": termination,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-directory", "-RunDirectory", required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(stop(Path(args.run_directory)), ensure_ascii=False, separators=(",", ":")))
        return 0
    except (ControlIntegrityError, ProcessControlError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "code": "safe_stop_blocked", "reason": str(exc)}, ensure_ascii=False, separators=(",", ":")), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
