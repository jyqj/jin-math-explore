#!/usr/bin/env python3
"""Prove worker write and publisher readback reachability for Math Research v10.

This helper is deliberately Goal-agnostic.  It is a data-plane probe, not an
authorization token.  Run ``access-prepare`` in the exact future worker
topology and ``validate-readback`` in the exact future ingest/publisher
topology before ATTEMPT_START.  The ready receipt is short-lived and bound to
the current project head and planned ticket.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path
from typing import Any


HEX64 = re.compile(r"^[0-9a-f]{64}$")
RFC3339_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")


class TopologyError(Exception):
    def __init__(self, code: str, message: str, recovery: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.recovery = recovery


def fail(condition: bool, code: str, message: str, recovery: str) -> None:
    if condition:
        raise TopologyError(code, message, recovery)


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def principal_identity() -> str:
    if os.name == "nt":
        try:
            completed = subprocess.run(["whoami.exe"], capture_output=True, text=True, encoding="utf-8", check=True)
        except (OSError, subprocess.SubprocessError, UnicodeError) as exc:
            raise TopologyError("consumer_identity_unavailable", f"Cannot resolve the current Windows principal: {exc}", "Run the official helper in the exact desktop-consumer process.") from exc
        value = completed.stdout.strip()
    else:
        value = f"uid:{os.geteuid()}"
    fail(not value, "consumer_identity_unavailable", "Consumer principal is empty.", "Run the helper in a process with a stable OS identity.")
    return value


def same_principal(actual: str, expected: str) -> bool:
    return actual.casefold() == expected.casefold() if os.name == "nt" else actual == expected


def recursive_readback(root: Path) -> dict[str, Any]:
    records: list[dict[str, str]] = []
    directory_count = 0
    file_count = 0

    def visit(directory: Path) -> None:
        nonlocal directory_count, file_count
        directory_count += 1
        try:
            entries = sorted(os.scandir(directory), key=lambda item: item.name.casefold())
        except OSError as exc:
            raise TopologyError("consumer_scandir_unavailable", f"Consumer cannot scandir {directory}: {exc}", "Preserve bytes; restore the long-lived consumer's inherited access before any further publication.") from exc
        for entry in entries:
            path = Path(entry.path)
            target = real(path, strict=True, code="consumer_path_unreadable")
            fail(not under(target, root), "consumer_path_escape", f"Consumer readback escaped the project root: {path}", "Remove the reparse indirection before publication.")
            try:
                if entry.is_dir(follow_symlinks=False):
                    visit(path)
                elif entry.is_file(follow_symlinks=False):
                    digest = sha_file(path)
                    file_count += 1
                    records.append({"path": path.relative_to(root).as_posix(), "sha256": digest})
                else:
                    raise TopologyError("consumer_path_unsupported", f"Unsupported reparse or special entry: {path}", "Use ordinary project-local files and directories.")
            except OSError as exc:
                raise TopologyError("consumer_file_unreadable", f"Consumer cannot read {path}: {exc}", "Preserve bytes; restore consumer access from the object's owner topology.") from exc
    visit(root)
    return {"project_tree_sha256": sha_bytes(canonical_bytes(records)), "directory_count": directory_count, "file_count": file_count}


def load_json(path: Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TopologyError(code, f"Cannot read valid UTF-8 JSON at {path}: {exc}", "Use the exact file in the selected execution topology and retry once.") from exc
    fail(not isinstance(value, dict), code, f"Expected a JSON object at {path}.", "Repair the structured artifact without changing its scope.")
    return value


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def stamp(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_stamp(value: Any, label: str) -> dt.datetime:
    fail(not isinstance(value, str) or not RFC3339_Z.fullmatch(value), "receipt_invalid", f"{label} is not RFC3339-Z.", "Regenerate the topology receipt.")
    return dt.datetime.fromisoformat(value[:-1] + "+00:00")


def real(path: Path, *, strict: bool, code: str) -> Path:
    try:
        return path.resolve(strict=strict)
    except OSError as exc:
        raise TopologyError(code, f"Cannot resolve {path}: {exc}", "Use an existing canonical path without a broken reparse target.") from exc


def under(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def project_root(value: str) -> Path:
    root = real(Path(value), strict=True, code="project_unreadable")
    fail(not root.is_dir() or root == Path(root.anchor), "project_root_unsafe", "Project root must be an existing non-filesystem-root directory.", "Use the exact long-lived Math Research project directory.")
    return root


def relative_file(root: Path, value: str, code: str) -> tuple[str, Path]:
    raw = Path(value)
    target = real(raw if raw.is_absolute() else root / raw, strict=True, code=code)
    fail(not target.is_file() or not under(target, root), code, f"File is absent or escapes the project root: {value}", "Use the immutable project-bound file without copying or rebinding it.")
    return target.relative_to(root).as_posix(), target


def relative_staging(root: Path, value: str) -> tuple[str, Path]:
    raw = Path(value)
    lexical = Path(os.path.abspath(str(raw if raw.is_absolute() else root / raw)))
    try:
        lexical.relative_to(root)
    except ValueError as exc:
        raise TopologyError("worker_staging_escape", "Ticket staging path escapes the project root.", "Use the exact ticket-local staging path.") from exc
    lexical.mkdir(parents=True, exist_ok=True)
    target = real(lexical, strict=True, code="worker_staging_unwritable")
    fail(not target.is_dir() or not under(target, root), "worker_staging_escape", "Resolved staging path escapes through a reparse target.", "Remove the reparse indirection and use a real project-local directory.")
    return target.relative_to(root).as_posix(), target


def topology(path: Path, expected_role: set[str], root: Path) -> tuple[dict[str, Any], str]:
    value = load_json(path, "topology_descriptor_invalid")
    expected = {"schema", "role", "transport", "execution_workspace_root", "runner", "sandbox_mode", "runner_arguments"}
    fail(set(value) != expected, "topology_descriptor_invalid", "Topology descriptor has an unexpected key set.", "Use the exact descriptor schema from the Skill template.")
    fail(value["schema"] != "math-research-execution-topology-descriptor/v1" or value["role"] not in expected_role, "topology_descriptor_invalid", "Topology descriptor schema or role is invalid.", "Use worker for access-prepare and ingest or publisher for validate-readback.")
    descriptor_root = real(Path(value["execution_workspace_root"]), strict=True, code="execution_workspace_mismatch")
    fail(descriptor_root != root, "execution_workspace_mismatch", "Execution workspace must resolve exactly to the project root.", "Run from a project-root topology; do not bind only staging.")
    fail(Path.cwd().resolve() != root, "execution_workspace_mismatch", "Current working directory is not the declared project root.", "Start the actual data-plane process with cwd equal to the project root.")
    fail(not isinstance(value["runner_arguments"], list) or any(not isinstance(item, str) for item in value["runner_arguments"]), "topology_descriptor_invalid", "runner_arguments must be an array of strings.", "Freeze the exact runner flags in the descriptor.")
    return value, sha_bytes(canonical_bytes(value))


def ticket_bindings(root: Path, ticket_arg: str) -> tuple[dict[str, Any], dict[str, str], list[dict[str, str]], str, Path]:
    ticket_rel, ticket_path = relative_file(root, ticket_arg, "worker_input_unreadable")
    ticket = load_json(ticket_path, "ticket_invalid")
    fail(ticket.get("schema") != "math-research-ticket/v10", "ticket_invalid", "Ticket schema is not math-research-ticket/v10.", "Use the exact planned v10 ticket.")
    artifacts = ticket.get("input_artifacts")
    fail(not isinstance(artifacts, list) or not artifacts, "ticket_invalid", "Ticket input_artifacts must be a nonempty array.", "Bind every immutable input before topology proof.")
    inputs: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in artifacts:
        fail(not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("sha256"), str), "ticket_invalid", "Ticket input artifact is malformed.", "Use complete path and SHA-256 bindings.")
        rel, path = relative_file(root, item["path"], "worker_input_unreadable")
        fail(rel in seen, "ticket_invalid", f"Duplicate input path: {rel}", "Deduplicate ticket inputs.")
        fail(not HEX64.fullmatch(item["sha256"]) or sha_file(path) != item["sha256"], "worker_input_hash_mismatch", f"Input hash mismatch: {rel}", "Stop dispatch and rebuild the ticket from current immutable bytes.")
        seen.add(rel)
        inputs.append({"path": rel, "sha256": item["sha256"]})
    staging_value = ticket.get("writable_staging_path")
    fail(not isinstance(staging_value, str), "ticket_invalid", "Ticket writable_staging_path is missing.", "Bind one ticket-local staging directory.")
    staging_rel, staging = relative_staging(root, staging_value)
    return ticket, {"path": ticket_rel, "sha256": sha_file(ticket_path)}, inputs, staging_rel, staging


def project_binding(root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    head_path = root / "project.json"
    fail(not head_path.is_file(), "project_unreadable", "project.json is absent.", "Run startup and use a valid v10 project root.")
    head = load_json(head_path, "project_unreadable")
    fail(head.get("schema") != "math-research-project/v10", "project_invalid", "Execution topology receipts are required only for v10 projects.", "Use the frozen protocol for older projects.")
    return head, {"path": "project.json", "sha256": sha_file(head_path)}


def exclusive_json(path: Path, value: dict[str, Any], code: str) -> None:
    data = canonical_bytes(value)
    try:
        with path.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise TopologyError(code, f"Cannot create {path}: {exc}", "Use a fresh ticket-local output path in a writable execution topology.") from exc
    fail(path.read_bytes() != data, code, f"Immediate readback mismatch for {path}.", "Stop and select a topology with stable staging access.")


def access_prepare(args: argparse.Namespace) -> dict[str, Any]:
    root = project_root(args.project)
    worker, worker_sha = topology(Path(args.worker_topology), {"worker"}, root)
    publisher, publisher_sha = topology(Path(args.publisher_topology), {"ingest", "publisher"}, root)
    consumer, consumer_sha = topology(Path(args.consumer_topology), {"consumer"}, root)
    head, head_ptr = project_binding(root)
    ticket, ticket_ptr, inputs, staging_rel, staging = ticket_bindings(root, args.ticket)
    receipt_path = real(Path(args.receipt) if Path(args.receipt).is_absolute() else root / args.receipt, strict=False, code="worker_staging_unwritable")
    fail(receipt_path.exists() or not under(receipt_path.parent.resolve(), staging), "worker_staging_escape", "Worker receipt must be a fresh file directly inside ticket staging.", "Choose a new receipt filename under writable_staging_path.")
    issued = now_utc()
    expires = issued + dt.timedelta(seconds=args.ttl_seconds)
    nonce = secrets.token_hex(32)
    probe_path = staging / f".topology-probe-{nonce}.json"
    probe = {"schema": "math-research-topology-probe/v1", "nonce": nonce, "ticket_sha256": ticket_ptr["sha256"], "issued_at_utc": stamp(issued)}
    exclusive_json(probe_path, probe, "worker_staging_unwritable")
    probe_sha = sha_file(probe_path)
    ticket_parts = ticket_ptr["path"].split("/")
    fail(len(ticket_parts) < 3 or ticket_parts[0] != "runs", "ticket_invalid", "Ticket path does not bind a run directory.", "Keep v10 tickets under runs/<run-id>/tickets/.")
    receipt = {
        "schema": "math-research-execution-topology-worker-receipt/v1",
        "status": "worker_ready",
        "receipt_id": f"topology-{secrets.token_hex(16)}",
        "project_id": head["project_id"],
        "run_id": ticket_parts[1],
        "control_generation": head["control_generation"],
        "project_head": head_ptr,
        "ticket": {**ticket_ptr, "ticket_id": ticket["ticket_id"]},
        "inputs": inputs,
        "staging_root": staging_rel,
        "probe_relative_path": probe_path.relative_to(root).as_posix(),
        "probe_sha256": probe_sha,
        "nonce_sha256": sha_bytes(nonce.encode("ascii")),
        "worker_topology": {"descriptor": worker, "sha256": worker_sha},
        "publisher_topology": {"descriptor": publisher, "sha256": publisher_sha},
        "consumer_topology": {"descriptor": consumer, "sha256": consumer_sha},
        "consumer_principal": args.expected_consumer_principal,
        "issued_at_utc": stamp(issued),
        "expires_at_utc": stamp(expires),
    }
    exclusive_json(receipt_path, receipt, "worker_staging_unwritable")
    return {"ready": True, "phase": "ACCESS_PREPARE", "receipt_path": receipt_path.relative_to(root).as_posix(), "receipt_sha256": sha_file(receipt_path), "expires_at_utc": receipt["expires_at_utc"]}


def validate_readback(args: argparse.Namespace) -> dict[str, Any]:
    root = project_root(args.project)
    publisher, publisher_sha = topology(Path(args.publisher_topology), {"ingest", "publisher"}, root)
    receipt_rel, receipt_path = relative_file(root, args.receipt, "host_or_ingest_readback_unavailable")
    worker_bytes = receipt_path.read_bytes()
    worker_sha = sha_bytes(worker_bytes)
    worker = load_json(receipt_path, "receipt_invalid")
    fail(worker.get("schema") != "math-research-execution-topology-worker-receipt/v1" or worker.get("status") != "worker_ready", "receipt_invalid", "Worker receipt is not in worker_ready state.", "Rerun ACCESS_PREPARE once in the exact worker topology.")
    fail(parse_stamp(worker.get("expires_at_utc"), "expires_at_utc") <= now_utc(), "receipt_stale", "Worker topology receipt expired.", "Regenerate it immediately before ATTEMPT_START.")
    fail(worker.get("publisher_topology", {}).get("sha256") != publisher_sha, "topology_changed", "Publisher topology differs from the frozen descriptor.", "Regenerate the receipt after any runner, cwd, sandbox, or root change.")
    head, head_ptr = project_binding(root)
    ticket, ticket_ptr, inputs, staging_rel, staging = ticket_bindings(root, worker["ticket"]["path"])
    fail(worker["project_id"] != head["project_id"] or worker["control_generation"] != head["control_generation"] or worker["project_head"] != head_ptr, "receipt_mismatch", "Project head changed after worker readiness.", "Regenerate the receipt against the current head.")
    fail(worker["ticket"] != {**ticket_ptr, "ticket_id": ticket["ticket_id"]} or worker["inputs"] != inputs or worker["staging_root"] != staging_rel, "receipt_mismatch", "Ticket or input bindings changed after worker readiness.", "Regenerate the receipt from the current planned ticket.")
    probe_rel, probe_path = relative_file(root, worker["probe_relative_path"], "host_or_ingest_readback_unavailable")
    fail(not under(probe_path, staging) or sha_file(probe_path) != worker["probe_sha256"], "host_or_ingest_readback_unavailable", "Publisher cannot independently reopen the worker probe with the expected hash.", "Reroute once to a project-root ingest/publisher topology.")
    checked = now_utc()
    publisher_probe_dir = root / f".math-research-consumer-probe-{secrets.token_hex(16)}"
    try:
        publisher_probe_dir.mkdir()
    except OSError as exc:
        raise TopologyError("publisher_consumer_probe_unwritable", f"Publisher cannot create a root inheritance probe: {exc}", "Use a publisher topology that can create ordinary project-root descendants.") from exc
    publisher_probe_path = publisher_probe_dir / "probe.json"
    publisher_probe = {"schema": "math-research-consumer-probe/v1", "receipt_id": worker["receipt_id"], "probe_sha256": worker["probe_sha256"], "created_at_utc": stamp(checked)}
    exclusive_json(publisher_probe_path, publisher_probe, "publisher_consumer_probe_unwritable")
    ready = {
        "schema": "math-research-execution-topology-receipt/v1",
        "status": "publisher_ready_for_consumer",
        "receipt_id": worker["receipt_id"],
        "project_id": worker["project_id"],
        "run_id": worker["run_id"],
        "control_generation": worker["control_generation"],
        "project_head": worker["project_head"],
        "ticket": worker["ticket"],
        "inputs": worker["inputs"],
        "staging_root": worker["staging_root"],
        "worker_observation": {"topology": worker["worker_topology"], "probe_relative_path": probe_rel, "probe_sha256": worker["probe_sha256"], "nonce_sha256": worker["nonce_sha256"], "worker_receipt_sha256": worker_sha},
        "readback_observation": {"topology": worker["publisher_topology"], "independent_reopen": True, "project_head_sha256": head_ptr["sha256"], "ticket_sha256": ticket_ptr["sha256"], "probe_sha256": worker["probe_sha256"], "checked_at_utc": stamp(checked)},
        "consumer_topology": worker["consumer_topology"],
        "consumer_principal": worker["consumer_principal"],
        "publisher_probe_relative_path": publisher_probe_path.relative_to(root).as_posix(),
        "publisher_probe_sha256": sha_file(publisher_probe_path),
        "issued_at_utc": worker["issued_at_utc"],
        "expires_at_utc": worker["expires_at_utc"],
    }
    temp = receipt_path.with_name(receipt_path.name + f".ready-{secrets.token_hex(8)}")
    exclusive_json(temp, ready, "host_or_ingest_readback_unavailable")
    os.replace(temp, receipt_path)
    fail(load_json(receipt_path, "host_or_ingest_readback_unavailable") != ready, "host_or_ingest_readback_unavailable", "Ready receipt atomic readback failed.", "Preserve staging and reroute to a stable project-root publisher.")
    return {"ready": False, "consumer_check_required": True, "phase": "READBACK_VALIDATE", "receipt_path": receipt_rel, "receipt_sha256": sha_file(receipt_path), "expires_at_utc": ready["expires_at_utc"]}


def validate_consumer(args: argparse.Namespace) -> dict[str, Any]:
    root = project_root(args.project)
    consumer, consumer_sha = topology(Path(args.consumer_topology), {"consumer"}, root)
    receipt_rel, receipt_path = relative_file(root, args.receipt, "consumer_readback_unavailable")
    intermediate = load_json(receipt_path, "receipt_invalid")
    fail(intermediate.get("schema") != "math-research-execution-topology-receipt/v1" or intermediate.get("status") != "publisher_ready_for_consumer", "consumer_receipt_not_ready", "Consumer validation requires the publisher-ready receipt.", "Run publisher validate-readback exactly once before consumer validation.")
    fail(parse_stamp(intermediate.get("expires_at_utc"), "expires_at_utc") <= now_utc(), "receipt_stale", "Topology receipt expired before consumer validation.", "Regenerate the three-boundary receipt.")
    fail(intermediate.get("consumer_topology", {}).get("sha256") != consumer_sha, "topology_changed", "Consumer topology differs from the frozen descriptor.", "Regenerate after any consumer runner, cwd, sandbox, or root change.")
    actual_principal = principal_identity()
    expected_principal = intermediate.get("consumer_principal")
    fail(not isinstance(expected_principal, str) or not same_principal(actual_principal, expected_principal), "consumer_principal_mismatch", f"Consumer process principal {actual_principal!r} does not match {expected_principal!r}.", "Run in the actual long-lived desktop/application user boundary; never substitute the sandbox owner.")
    head, head_ptr = project_binding(root)
    fail(intermediate.get("project_id") != head["project_id"] or intermediate.get("control_generation") != head["control_generation"] or intermediate.get("project_head") != head_ptr, "receipt_mismatch", "Project head changed before consumer validation.", "Regenerate the receipt against the current head.")
    worker_probe_rel, worker_probe_path = relative_file(root, intermediate["worker_observation"]["probe_relative_path"], "consumer_readback_unavailable")
    fail(sha_file(worker_probe_path) != intermediate["worker_observation"]["probe_sha256"], "consumer_readback_unavailable", "Consumer cannot reopen the worker-owned probe with its expected hash.", "Restore consumer access from the worker-owner topology before dispatch.")
    publisher_probe_rel, publisher_probe_path = relative_file(root, intermediate["publisher_probe_relative_path"], "consumer_readback_unavailable")
    fail(sha_file(publisher_probe_path) != intermediate["publisher_probe_sha256"], "consumer_readback_unavailable", "Consumer cannot reopen the publisher-owned inheritance probe.", "Restore an inheritable consumer ACE on the project root before dispatch.")
    tree = recursive_readback(root)
    checked = now_utc()
    ready = {key: intermediate[key] for key in ("schema", "receipt_id", "project_id", "run_id", "control_generation", "project_head", "ticket", "inputs", "staging_root", "worker_observation", "readback_observation", "consumer_principal", "issued_at_utc", "expires_at_utc")}
    ready["status"] = "ready_for_attempt_start"
    ready["consumer_observation"] = {
        "topology": intermediate["consumer_topology"],
        "principal": actual_principal,
        "independent_recursive_reopen": True,
        **tree,
        "publisher_probe_relative_path": publisher_probe_rel,
        "publisher_probe_sha256": intermediate["publisher_probe_sha256"],
        "checked_at_utc": stamp(checked),
    }
    temp = receipt_path.with_name(receipt_path.name + f".consumer-{secrets.token_hex(8)}")
    exclusive_json(temp, ready, "consumer_readback_unavailable")
    os.replace(temp, receipt_path)
    try:
        worker_probe_path.unlink()
        publisher_probe_path.unlink()
        publisher_probe_path.parent.rmdir()
    except OSError as exc:
        raise TopologyError("probe_cleanup_failed", f"Consumer-ready receipt exists but named probe cleanup failed: {exc}", "Keep the ready receipt and remove only the two named probes before publication.") from exc
    return {"ready": True, "phase": "CONSUMER_VALIDATE", "receipt_path": receipt_rel, "receipt_sha256": sha_file(receipt_path), "consumer_principal": actual_principal, **tree, "expires_at_utc": ready["expires_at_utc"]}


def validate_project_consumer(args: argparse.Namespace) -> dict[str, Any]:
    root = project_root(args.project)
    topology(Path(args.consumer_topology), {"consumer"}, root)
    actual_principal = principal_identity()
    fail(not same_principal(actual_principal, args.expected_consumer_principal), "consumer_principal_mismatch", f"Consumer process principal {actual_principal!r} does not match {args.expected_consumer_principal!r}.", "Run the post-publication check as the long-lived desktop/application user.")
    head_sha = sha_file(root / "project.json")
    fail(head_sha != args.expected_project_head_sha256, "consumer_head_mismatch", "Consumer sees a different project.json hash after publication.", "Do not report success; rerun official startup and bind the exact published head.")
    tree = recursive_readback(root)
    return {"schema": "math-research-consumer-readback-result/v1", "readable": True, "phase": "POST_PUBLICATION_CONSUMER_VALIDATE", "consumer_principal": actual_principal, "project_head_sha256": head_sha, **tree, "checked_at_utc": stamp(now_utc())}


def go_check(args: argparse.Namespace) -> dict[str, Any]:
    root = project_root(args.project)
    receipt_rel, receipt_path = relative_file(root, args.receipt, "receipt_invalid")
    fail(sha_file(receipt_path) != args.expected_receipt_sha256, "receipt_mismatch", "GO receipt hash differs from ATTEMPT_START binding.", "Do not start research; ask the Goal Host for the exact committed receipt pointer.")
    receipt = load_json(receipt_path, "receipt_invalid")
    fail(receipt.get("schema") != "math-research-execution-topology-receipt/v1" or receipt.get("status") != "ready_for_attempt_start", "receipt_invalid", "GO requires a ready topology receipt.", "Complete worker and publisher topology phases first.")
    head, _ = project_binding(root)
    fail(head["control_generation"] != receipt["control_generation"] + 1, "go_generation_mismatch", "ATTEMPT_START generation has not been committed exactly once.", "Wait for Goal Host commit/readback; never infer authority from READY alone.")
    state_rel, state_path = relative_file(root, head["state"]["path"], "go_state_unreadable")
    fail(sha_file(state_path) != head["state"]["sha256"], "go_state_unreadable", "Active state hash mismatch.", "Stop and rerun official startup readback.")
    state = load_json(state_path, "go_state_unreadable")
    current = state.get("current_ticket") or {}
    refs = state.get("typed_references") or []
    bound = any(item.get("kind") == "execution_topology_receipt" and item.get("path") == receipt_rel and item.get("sha256") == args.expected_receipt_sha256 for item in refs if isinstance(item, dict))
    fail(current.get("id") != receipt["ticket"]["ticket_id"] or current.get("lifecycle") != "active" or not bound, "go_not_authorized", "Committed state does not activate the receipt-bound ticket.", "Do not perform mathematics; return the structured mismatch to the Goal Host.")
    return {"go": True, "phase": "GO", "ticket_id": current["id"], "control_generation": head["control_generation"], "state_path": state_rel}


def parser() -> argparse.ArgumentParser:
    main = argparse.ArgumentParser(description="Math Research v10 worker, publisher, and consumer topology proof.")
    sub = main.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("access-prepare")
    prepare.add_argument("--project", required=True)
    prepare.add_argument("--ticket", required=True)
    prepare.add_argument("--worker-topology", required=True)
    prepare.add_argument("--publisher-topology", required=True)
    prepare.add_argument("--consumer-topology", required=True)
    prepare.add_argument("--expected-consumer-principal", required=True)
    prepare.add_argument("--receipt", required=True)
    prepare.add_argument("--ttl-seconds", type=int, default=300, choices=range(30, 1801), metavar="30..1800")
    readback = sub.add_parser("validate-readback")
    readback.add_argument("--project", required=True)
    readback.add_argument("--receipt", required=True)
    readback.add_argument("--publisher-topology", required=True)
    consumer = sub.add_parser("validate-consumer")
    consumer.add_argument("--project", required=True)
    consumer.add_argument("--receipt", required=True)
    consumer.add_argument("--consumer-topology", required=True)
    project_check = sub.add_parser("validate-project-consumer")
    project_check.add_argument("--project", required=True)
    project_check.add_argument("--consumer-topology", required=True)
    project_check.add_argument("--expected-consumer-principal", required=True)
    project_check.add_argument("--expected-project-head-sha256", required=True)
    go = sub.add_parser("go-check")
    go.add_argument("--project", required=True)
    go.add_argument("--receipt", required=True)
    go.add_argument("--expected-receipt-sha256", required=True)
    return main


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "access-prepare":
            result = access_prepare(args)
        elif args.command == "validate-readback":
            result = validate_readback(args)
        elif args.command == "validate-consumer":
            result = validate_consumer(args)
        elif args.command == "validate-project-consumer":
            fail(not HEX64.fullmatch(args.expected_project_head_sha256), "consumer_head_mismatch", "Expected project head SHA-256 is invalid.", "Use the exact post-publication project.json hash.")
            result = validate_project_consumer(args)
        else:
            fail(not HEX64.fullmatch(args.expected_receipt_sha256), "receipt_invalid", "Expected receipt SHA-256 is invalid.", "Use the exact pointer returned by ATTEMPT_START preparation.")
            result = go_check(args)
        print(json.dumps({"ok": True, "data": result, "warnings": []}, ensure_ascii=False, sort_keys=True))
        return 0
    except TopologyError as exc:
        print(json.dumps({"ok": False, "error": {"code": exc.code, "message": exc.message, "recovery": exc.recovery}}, ensure_ascii=False, sort_keys=True))
        return 2
    except OSError as exc:
        print(json.dumps({"ok": False, "error": {"code": "filesystem_topology_unavailable", "message": str(exc), "recovery": "Preserve project/staging bytes and reroute once to an exact project-root process."}}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
