#!/usr/bin/env python3
"""Native legacy-v1 compatibility migration with immutable source archive."""

from __future__ import annotations

import hashlib
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from math_research_control_primitives import (
    ControlIntegrityError,
    FileLease,
    assert_no_symlink_chain,
    read_signed_json,
    strict_json_loads,
    write_signed_json,
)
from math_research_process_identity import process_identity_matches


HASH_KEYS = ("head_sequence", "head_payload_sha256", "attempt_count", "audit_count", "total_round_count", "attempts_since_last_audit", "audit_due")
MONOTONE_KEYS = ("head_sequence", "attempt_count", "audit_count", "total_round_count")
TARGET_BINDINGS = {
    "launcher_entry": "launcher_entry",
    "launcher_module": "launcher_module",
    "cycle_module": "cycle_module",
    "cycle_cli": "cycle_cli",
    "project_module": "project_module",
    "canary_host": "canary_host",
    "canary_entry": "canary_entry",
}


class CompatibilityMigrationError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def require_hash(value: Any, label: str) -> str:
    text = str(value)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise CompatibilityMigrationError(f"{label} must be a lowercase SHA-256")
    return text


def read_receipt(path: Path) -> dict[str, Any]:
    path = assert_no_symlink_chain(path)
    if not path.is_file():
        raise CompatibilityMigrationError("compatibility migration receipt is missing")
    try:
        raw = path.read_bytes(); text = raw.decode("utf-8", errors="strict")
        value = strict_json_loads(text)
    except (OSError, UnicodeError, ControlIntegrityError) as exc:
        raise CompatibilityMigrationError("compatibility migration receipt is not strict JSON") from exc
    if not isinstance(value, dict):
        raise CompatibilityMigrationError("compatibility migration receipt must be an object")
    return {"path": path, "value": value, "raw_sha256": hashlib.sha256(raw).hexdigest()}


def _same_path(left: Any, right: Any) -> bool:
    return os.path.normcase(os.path.abspath(str(left))) == os.path.normcase(os.path.abspath(str(right)))


def assert_file_binding(binding: Any, expected: Path, label: str) -> None:
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
        raise CompatibilityMigrationError(f"{label} binding is invalid")
    expected = assert_no_symlink_chain(expected)
    if not _same_path(binding["path"], expected):
        raise CompatibilityMigrationError(f"{label} path differs from the receipt")
    digest = require_hash(binding["sha256"], f"{label} sha256")
    if not expected.is_file() or sha256_file(expected) != digest:
        raise CompatibilityMigrationError(f"{label} bytes differ from the receipt")


def assert_counters(snapshot: Any, checkpoint: Any, *, allow_advance: bool) -> None:
    if not isinstance(snapshot, dict) or not isinstance(checkpoint, dict) or not all(key in snapshot and key in checkpoint for key in HASH_KEYS):
        raise CompatibilityMigrationError("compatibility counter snapshot is incomplete")
    require_hash(snapshot["head_payload_sha256"], "source counters head hash")
    if allow_advance:
        for key in MONOTONE_KEYS:
            if not isinstance(snapshot[key], int) or isinstance(snapshot[key], bool) or not isinstance(checkpoint[key], int) or isinstance(checkpoint[key], bool) or checkpoint[key] < snapshot[key]:
                raise CompatibilityMigrationError(f"compatibility migration detected counter rollback at {key}")
    else:
        for key in HASH_KEYS:
            if checkpoint[key] != snapshot[key]:
                raise CompatibilityMigrationError(f"compatibility migration source counter mismatch at {key}")


def validate_state(
    manifest: dict[str, Any], run: Path, receipt_read: dict[str, Any], paths: dict[str, Path], *, require_applied: bool
) -> None:
    receipt = receipt_read["value"]
    if receipt.get("schema_version") != 1 or receipt.get("protocol") != "math-research-legacy-v1-compat-migration/v1":
        raise CompatibilityMigrationError("unsupported compatibility migration receipt protocol")
    for section in ("project", "run", "contract", "goal", "source", "target", "authorization"):
        if not isinstance(receipt.get(section), dict):
            raise CompatibilityMigrationError(f"compatibility migration receipt is missing {section}")
    if receipt.get("action") != "resume_prompt_v6_with_compat_bundle" or not isinstance(receipt.get("migration_id"), str) or not receipt["migration_id"]:
        raise CompatibilityMigrationError("compatibility migration action or ID is invalid")
    if not _same_path(receipt["run"].get("directory"), run) or manifest.get("run_id") != receipt["run"].get("id") or manifest.get("thread_id") != receipt["run"].get("thread_id"):
        raise CompatibilityMigrationError("compatibility run identity mismatches")
    if not isinstance(manifest.get("project"), dict) or manifest["project"].get("project_id") != receipt["project"].get("project_id") or not _same_path(manifest["project"].get("directory"), receipt["project"].get("directory")):
        raise CompatibilityMigrationError("compatibility project identity mismatches")
    if not isinstance(manifest.get("cycle_ledger"), dict) or manifest.get("contract_version") != receipt["contract"].get("version") or manifest["cycle_ledger"].get("contract_binding_sha256") != receipt["contract"].get("binding_sha256"):
        raise CompatibilityMigrationError("compatibility contract binding mismatches")
    require_hash(receipt["contract"].get("binding_sha256"), "contract binding")
    if not isinstance(manifest.get("goal"), dict) or manifest["goal"].get("objective_sha256") != receipt["goal"].get("objective_sha256"):
        raise CompatibilityMigrationError("compatibility Goal objective mismatches")
    if manifest.get("prompt_version") != "v6" or manifest.get("schema_version") != 1:
        raise CompatibilityMigrationError("compatibility migration accepts only schema-1 Prompt v6")
    authorization = receipt["authorization"]
    if authorization.get("approval_mode_from") != "never" or authorization.get("approval_mode_to") != "approve_for_me" or any(authorization.get(key) is not False for key in ("objective_changed", "quantifiers_changed", "counters_reset")):
        raise CompatibilityMigrationError("compatibility authorization envelope is invalid")
    for receipt_name, path_name in TARGET_BINDINGS.items():
        assert_file_binding(receipt["target"].get(receipt_name), paths[path_name], f"target {receipt_name}")
    for name in ("launcher_entry", "launcher_module", "cycle_module", "cycle_cli", "project_module"):
        binding = receipt["source"].get(name)
        if not isinstance(binding, dict):
            raise CompatibilityMigrationError(f"source binding {name} is missing")
        assert_file_binding(binding, Path(str(binding.get("path"))), f"source {name}")
    checkpoint = manifest["cycle_ledger"].get("checkpoint")
    assert_counters(receipt["source"].get("counters"), checkpoint, allow_advance=require_applied)
    if not require_applied:
        return
    record = manifest.get("compatibility_migration")
    if not isinstance(record, dict) or record.get("protocol") != receipt["protocol"] or record.get("migration_id") != receipt["migration_id"] or record.get("receipt_sha256") != receipt_read["raw_sha256"]:
        raise CompatibilityMigrationError("signed manifest is not bound to the compatibility receipt")
    config = manifest.get("config")
    if not isinstance(config, dict) or config.get("approval_policy") != "approve_for_me" or config.get("approval_mode") != "approve_for_me":
        raise CompatibilityMigrationError("signed manifest did not apply approval mode")
    for name in ("cycle_module", "cycle_cli", "project_module"):
        actual = manifest["cycle_ledger"].get(name.removeprefix("cycle_")) if name.startswith("cycle_") else manifest["cycle_ledger"].get(name)
        expected = receipt["target"][name]
        if not isinstance(actual, dict) or not _same_path(actual.get("path"), expected.get("path")) or actual.get("sha256") != expected.get("sha256"):
            raise CompatibilityMigrationError(f"signed manifest {name} binding mismatches")
    archive = run / str(receipt.get("archive_directory_name", ""))
    for name, digest in (
        ("original-run.json", receipt["source"].get("manifest_primary_sha256")),
        ("original-run.json.bak", receipt["source"].get("manifest_backup_sha256")),
        ("migration-receipt.json", receipt_read["raw_sha256"]),
    ):
        digest = require_hash(digest, f"archive {name}")
        item = archive / name
        if not item.is_file() or sha256_file(item) != digest:
            raise CompatibilityMigrationError(f"compatibility source archive mismatches: {name}")


def _archive_copy(source: Path, destination: Path, digest: str) -> None:
    digest = require_hash(digest, "archive expected hash")
    if destination.exists():
        if not destination.is_file() or sha256_file(destination) != digest:
            raise CompatibilityMigrationError(f"compatibility archive conflict: {destination}")
        return
    with source.open("rb") as reader:
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as writer:
            shutil.copyfileobj(reader, writer); writer.flush(); os.fsync(writer.fileno())
    if sha256_file(destination) != digest:
        raise CompatibilityMigrationError("compatibility archive write verification failed")


def _result(action: str, status: str, manifest: dict[str, Any], receipt_hash: str) -> dict[str, Any]:
    checkpoint = manifest["cycle_ledger"]["checkpoint"]
    return {"Ok": True, "Action": action, "Status": status, "RunId": manifest["run_id"], "ThreadId": manifest["thread_id"], "ReceiptSha256": receipt_hash, "AttemptCount": checkpoint["attempt_count"], "TotalRoundCount": checkpoint["total_round_count"]}


def invoke(action: str, run_directory: Path, receipt_file: Path, paths: dict[str, Path]) -> dict[str, Any]:
    if action not in {"Analyze", "Apply", "Verify"}:
        raise CompatibilityMigrationError("unsupported migration action")
    run = assert_no_symlink_chain(run_directory)
    manifest_path = run / "run.json"; receipt_read = read_receipt(receipt_file)
    with FileLease("run", str(run)):
        manifest = read_signed_json(manifest_path)["payload"]
        if not isinstance(manifest, dict):
            raise CompatibilityMigrationError("signed run manifest is invalid")
        if "compatibility_migration" in manifest:
            validate_state(manifest, run, receipt_read, paths, require_applied=True)
            return _result(action, "already_applied", manifest, receipt_read["raw_sha256"])
        validate_state(manifest, run, receipt_read, paths, require_applied=False)
        if action == "Verify":
            raise CompatibilityMigrationError("compatibility migration has not been applied")
        if manifest.get("config", {}).get("approval_policy") != "never" or manifest.get("status") != receipt_read["value"]["source"].get("status"):
            raise CompatibilityMigrationError("source approval policy or status mismatches")
        process = manifest.get("process")
        if process is not None:
            identity = process.get("identity") if isinstance(process, dict) else None
            if not isinstance(identity, dict) or process_identity_matches(identity):
                raise CompatibilityMigrationError("migration refuses a live or unverifiable process")
        source = receipt_read["value"]["source"]
        primary_hash = require_hash(source.get("manifest_primary_sha256"), "source primary hash")
        backup_hash = require_hash(source.get("manifest_backup_sha256"), "source backup hash")
        if sha256_file(manifest_path) != primary_hash or sha256_file(Path(f"{manifest_path}.bak")) != backup_hash:
            raise CompatibilityMigrationError("source manifest bytes differ from the receipt")
        if action == "Analyze":
            return _result(action, "ready_to_apply", manifest, receipt_read["raw_sha256"])
        receipt = receipt_read["value"]; archive = run / str(receipt["archive_directory_name"])
        archive.mkdir(mode=0o700, exist_ok=True); assert_no_symlink_chain(archive)
        _archive_copy(manifest_path, archive / "original-run.json", primary_hash)
        _archive_copy(Path(f"{manifest_path}.bak"), archive / "original-run.json.bak", backup_hash)
        _archive_copy(receipt_read["path"], archive / "migration-receipt.json", receipt_read["raw_sha256"])
        manifest["config"]["approval_policy"] = "approve_for_me"; manifest["config"]["approval_mode"] = "approve_for_me"
        manifest["cycle_ledger"]["module"] = receipt["target"]["cycle_module"]
        manifest["cycle_ledger"]["cli"] = receipt["target"]["cycle_cli"]
        manifest["cycle_ledger"]["project_module"] = receipt["target"]["project_module"]
        manifest["compatibility_migration"] = {
            "schema_version": 1, "protocol": receipt["protocol"], "migration_id": receipt["migration_id"],
            "receipt_sha256": receipt_read["raw_sha256"], "source_manifest_primary_sha256": primary_hash,
            "source_manifest_backup_sha256": backup_hash, "source_thread_id": receipt["run"]["thread_id"],
            "source_contract_binding_sha256": receipt["contract"]["binding_sha256"], "source_counters": source["counters"],
            "objective_changed": False, "quantifiers_changed": False, "counters_reset": False,
            "approval_mode_from": "never", "approval_mode_to": "approve_for_me", "applied_at_utc": utc_now(),
        }
        manifest["revision"] += 1; manifest["updated_at_utc"] = utc_now(); manifest["exit_reason"] = "compatibility_migration_applied_ready_to_resume"
        write_signed_json(manifest_path, manifest)
        read_back = read_signed_json(manifest_path)["payload"]
        validate_state(read_back, run, receipt_read, paths, require_applied=True)
        return _result(action, "applied", read_back, receipt_read["raw_sha256"])
