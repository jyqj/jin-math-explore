#!/usr/bin/env python3
"""Native argument construction for the approve-for-me compatibility contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence


def toml_basic_string(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("TOML value must be a string")
    return json.dumps(value, ensure_ascii=False)


def _common(run_directory: str, model: str, reasoning_effort: str) -> list[str]:
    if not run_directory or not model or not reasoning_effort:
        raise ValueError("run directory, model, and reasoning effort are required")
    return [
        "--strict-config", "-C", str(Path(run_directory)), "-m", model,
        "-c", f"model_reasoning_effort={toml_basic_string(reasoning_effort)}",
        "-c", "sandbox_workspace_write.network_access=false",
        "--enable", "goals",
        "--disable", "plugins",
        "--disable", "apps",
        "--disable", "enable_mcp_apps",
        "--disable", "multi_agent_v2",
    ]


def new_global_arguments(
    *,
    flavor: str,
    run_directory: str,
    model: str,
    reasoning_effort: str,
    sandbox: str,
    allow_web_search: bool,
    enable_multi_agent: bool,
    max_child_agents: int = 1,
    approval_mode: str = "approve_for_me",
) -> list[str]:
    if flavor not in {"launcher-v2", "legacy-v1-compat"}:
        raise ValueError("unsupported compatibility flavor")
    if sandbox not in {"read-only", "workspace-write"}:
        raise ValueError("unsupported sandbox")
    if approval_mode not in {"approve_for_me", "never"}:
        raise ValueError("unsupported approval mode")
    if not 1 <= max_child_agents <= 16:
        raise ValueError("max_child_agents must be in [1, 16]")
    if flavor == "legacy-v1-compat" and sandbox != "workspace-write":
        raise ValueError("legacy compatibility approve_for_me requires workspace-write")
    if approval_mode == "approve_for_me" and sandbox != "workspace-write":
        raise ValueError("approve_for_me requires workspace-write")

    arguments = _common(run_directory, model, reasoning_effort)
    insertion = 5
    approval = ["--approve-for-me"] if approval_mode == "approve_for_me" else ["-s", sandbox, "-a", "never"]
    arguments[insertion:insertion] = approval
    arguments.extend(["--enable", "multi_agent", "-c", f"agents.max_threads={max_child_agents}"] if enable_multi_agent else ["--disable", "multi_agent"])
    if allow_web_search:
        arguments.append("--search")
    return arguments


def new_features_arguments(*, run_directory: str, max_child_agents: int, approval_mode: str) -> list[str]:
    if not run_directory or not 1 <= max_child_agents <= 16:
        raise ValueError("invalid feature probe arguments")
    if approval_mode not in {"approve_for_me", "never"}:
        raise ValueError("unsupported approval mode")
    result = ["--strict-config", "-C", str(Path(run_directory))]
    result.extend(["--approve-for-me"] if approval_mode == "approve_for_me" else ["-s", "workspace-write", "-a", "never"])
    result.extend([
        "--enable", "goals", "--enable", "multi_agent", "--disable", "multi_agent_v2",
        "--disable", "plugins", "--disable", "apps", "--disable", "enable_mcp_apps",
        "-c", f"agents.max_threads={max_child_agents}", "features", "list",
    ])
    return result


def assert_approve_for_me_arguments(arguments: Sequence[str]) -> bool:
    values = list(arguments)
    if values.count("--approve-for-me") != 1:
        raise ValueError("approve_for_me argv must contain exactly one literal option")
    if "-s" in values or "--sandbox" in values:
        raise ValueError("approve_for_me argv must omit explicit sandbox options")
    if values.count("sandbox_workspace_write.network_access=false") != 1:
        raise ValueError("approve_for_me argv must keep shell network disabled")
    return True
