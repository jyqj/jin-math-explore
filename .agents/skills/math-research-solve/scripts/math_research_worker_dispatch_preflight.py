from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


class DispatchError(Exception):
    def __init__(self, code: str, message: str, recovery: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.recovery = recovery


def _path(value: str) -> Path:
    return Path(os.path.abspath(os.path.expandvars(value)))


def _same(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left)) == os.path.normcase(str(right))


def _under(child: Path, parent: Path) -> bool:
    try:
        return os.path.commonpath([os.path.normcase(str(child)), os.path.normcase(str(parent))]) == os.path.normcase(str(parent))
    except ValueError:
        return False


def _display(value: Path) -> str:
    return value.as_posix()


def classify(
    *,
    project_raw: str,
    ticket_raw: str,
    host_roots_raw: list[str],
    transport: str,
    execution_root_raw: str | None,
) -> dict[str, Any]:
    project = _path(project_raw)
    if _same(project, Path(project.anchor)):
        raise DispatchError(
            "project_root_unsafe",
            "The project workspace cannot be a filesystem root.",
            "Supply the exact long-lived math-research project directory.",
        )
    ticket_input = Path(ticket_raw)
    ticket = _path(str(ticket_input if ticket_input.is_absolute() else project / ticket_input))
    if _same(ticket, project) or not _under(ticket, project):
        raise DispatchError(
            "ticket_path_escape",
            "The immutable ticket path must be a file path under the project root.",
            "Use the project-bound ticket path without copying it to another workspace.",
        )
    if not host_roots_raw:
        raise DispatchError(
            "host_workspace_missing",
            "At least one current Host workspace root is required.",
            "Pass every workspace root exposed by the current runtime before dispatch.",
        )
    host_roots = [_path(item) for item in host_roots_raw]
    shared = any(_under(project, root) for root in host_roots)
    execution_root = _path(execution_root_raw) if execution_root_raw else None

    if transport == "collaboration":
        if execution_root is not None and not _same(execution_root, project):
            raise DispatchError(
                "execution_workspace_mismatch",
                "A collaboration transport cannot declare a different execution workspace.",
                "Omit the execution workspace or use the exact project root.",
            )
        if not shared:
            raise DispatchError(
                "worker_workspace_mismatch",
                "The project is outside every Host workspace root, so a context-free collaboration worker cannot rely on the Host authorization context.",
                "Use project-root-exec, let the Goal Host request approval, and set the execution workspace exactly to the project root.",
            )
        classification = "host_workspace_shared"
        approval_owner = "host_context"
        next_action = "dispatch_context_free_collaboration_worker"
    elif transport == "project-root-exec":
        if execution_root is None or not _same(execution_root, project):
            raise DispatchError(
                "execution_workspace_mismatch",
                "project-root-exec requires an execution workspace exactly equal to the project root.",
                "Do not use a staging-only add-dir; set the worker working root to the complete project directory.",
            )
        classification = "project_root_rebind_required" if not shared else "project_root_exec_allowed"
        approval_owner = "goal_host_parent"
        next_action = "goal_host_approves_then_dispatches_context_free_project_root_process"
    else:
        raise DispatchError(
            "transport_invalid",
            f"Unsupported worker transport: {transport}",
            "Use collaboration or project-root-exec.",
        )

    return {
        "classification": classification,
        "project_workspace_root": _display(project),
        "ticket_path": _display(ticket),
        "project_inside_host_workspace": shared,
        "transport": transport,
        "execution_workspace_root": _display(execution_root) if execution_root else None,
        "required_fork_turns": "none",
        "worker_context": "ticket_only",
        "approval_owner": approval_owner,
        "authorization_relay_forbidden": True,
        "staging_only_workspace_forbidden": True,
        "validation_boundary": "same_project_root_process" if transport == "project-root-exec" else "shared_host_workspace",
        "next_action": next_action,
        "trust": "path_topology_only_not_filesystem_access_or_goal_authorization",
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Fail-closed worker dispatch topology preflight.")
    result.add_argument("--project", required=True)
    result.add_argument("--ticket", required=True)
    result.add_argument("--host-workspace-root", action="append", required=True)
    result.add_argument("--transport", choices=("collaboration", "project-root-exec"), required=True)
    result.add_argument("--execution-workspace-root")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        data = classify(
            project_raw=args.project,
            ticket_raw=args.ticket,
            host_roots_raw=args.host_workspace_root,
            transport=args.transport,
            execution_root_raw=args.execution_workspace_root,
        )
        print(json.dumps({"ok": True, "data": data, "warnings": []}, ensure_ascii=False, sort_keys=True))
        return 0
    except DispatchError as exc:
        print(
            json.dumps(
                {"ok": False, "error": {"code": exc.code, "message": exc.message, "recovery": exc.recovery}},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
