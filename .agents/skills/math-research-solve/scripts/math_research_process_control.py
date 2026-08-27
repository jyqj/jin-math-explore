#!/usr/bin/env python3
"""Safe termination scopes for native math-research launcher processes."""

from __future__ import annotations

import os
import signal
import time
from typing import Any

from math_research_process_identity import ProcessIdentityError, process_identity_matches


class ProcessControlError(RuntimeError):
    pass


def new_posix_termination_scope(pid: int) -> dict[str, Any]:
    if os.name == "nt":
        raise ProcessControlError("POSIX process groups are unavailable on Windows")
    try:
        group = os.getpgid(pid)
    except (ProcessLookupError, PermissionError, OSError) as exc:
        raise ProcessControlError("process group is unavailable") from exc
    if group != pid:
        raise ProcessControlError("process is not the leader of a dedicated process group")
    return {"kind": "posix-process-group", "id": group}


def _still_matches(identity: dict[str, Any]) -> bool:
    return process_identity_matches(identity)


def terminate_bound_scope(
    identity: dict[str, Any],
    scope: dict[str, Any],
    *,
    graceful_seconds: float = 5.0,
    final_seconds: float = 10.0,
) -> dict[str, Any]:
    if not process_identity_matches(identity):
        raise ProcessControlError("live process identity does not match the signed manifest")
    if os.name == "nt":
        raise ProcessControlError("native Windows Job Object termination is not implemented in this module")
    if set(scope) != {"kind", "id"} or scope.get("kind") != "posix-process-group":
        raise ProcessControlError("termination scope is invalid")
    pid = identity["pid"]
    group = scope.get("id")
    if not isinstance(group, int) or isinstance(group, bool) or group <= 0 or group != pid:
        raise ProcessControlError("termination scope is not bound to the manifest PID")
    try:
        if os.getpgid(pid) != group:
            raise ProcessControlError("live process group differs from the signed scope")
    except (ProcessLookupError, PermissionError, OSError) as exc:
        raise ProcessControlError("live process group cannot be verified") from exc

    os.killpg(group, signal.SIGTERM)
    deadline = time.monotonic() + max(0.0, graceful_seconds)
    while time.monotonic() < deadline:
        if not _still_matches(identity):
            return {"terminated": True, "escalated": False, "signal": "SIGTERM"}
        time.sleep(0.05)
    if _still_matches(identity):
        os.killpg(group, signal.SIGKILL)
    deadline = time.monotonic() + max(0.0, final_seconds)
    while time.monotonic() < deadline:
        if not _still_matches(identity):
            return {"terminated": True, "escalated": True, "signal": "SIGKILL"}
        time.sleep(0.05)
    raise ProcessControlError("bound process did not exit after final termination")
