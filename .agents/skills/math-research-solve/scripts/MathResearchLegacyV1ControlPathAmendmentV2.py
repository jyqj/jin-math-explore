#!/usr/bin/env python3
"""Native approve-for-me control-path amendment layered on compat migration."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from MathResearchLegacyV1CompatMigration import (
    CompatibilityMigrationError,
    _archive_copy,
    _same_path,
    assert_counters,
    assert_file_binding,
    read_receipt,
    require_hash,
    sha256_file,
    validate_state as validate_prior_state,
)
from math_research_control_primitives import FileLease, assert_no_symlink_chain, read_signed_json, write_signed_json
from math_research_process_identity import process_identity_matches


class ControlPathAmendmentError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ControlPathAmendmentError(message)


def _prior_paths(paths: dict[str, Path]) -> dict[str, Path]:
    return {
        "launcher_entry": paths["prior_launcher_entry"], "launcher_module": paths["launcher_module"],
        "cycle_module": paths["cycle_module"], "cycle_cli": paths["cycle_cli"],
        "project_module": paths["project_module"], "canary_host": paths["prior_canary_host"],
        "canary_entry": paths["canary_entry"],
    }


def validate_state(
    manifest: dict[str, Any], run: Path, receipt_read: dict[str, Any], prior_read: dict[str, Any], paths: dict[str, Path], *, require_applied: bool
) -> None:
    receipt = receipt_read["value"]
    _require(receipt.get("schema_version") == 1 and receipt.get("protocol") == "math-research-legacy-v1-control-path-amendment/v2", "unsupported control-path amendment receipt protocol")
    for section in ("project", "run", "contract", "goal", "prior_migration", "source", "target", "authorization"):
        _require(isinstance(receipt.get(section), dict), f"control-path receipt is missing {section}")
    _require(receipt.get("action") == "omit_explicit_sandbox_with_approve_for_me" and isinstance(receipt.get("amendment_id"), str) and bool(receipt["amendment_id"]), "control-path amendment action or ID is invalid")
    _require(_same_path(receipt["run"].get("directory"), run) and manifest.get("run_id") == receipt["run"].get("id") and manifest.get("thread_id") == receipt["run"].get("thread_id"), "control-path run identity mismatches")
    _require(isinstance(manifest.get("project"), dict) and manifest["project"].get("project_id") == receipt["project"].get("project_id") and _same_path(manifest["project"].get("directory"), receipt["project"].get("directory")), "control-path project identity mismatches")
    _require(isinstance(manifest.get("cycle_ledger"), dict) and manifest.get("contract_version") == receipt["contract"].get("version") and manifest["cycle_ledger"].get("contract_binding_sha256") == receipt["contract"].get("binding_sha256"), "control-path contract binding mismatches")
    _require(isinstance(manifest.get("goal"), dict) and manifest["goal"].get("objective_sha256") == receipt["goal"].get("objective_sha256"), "control-path Goal objective mismatches")
    _require(prior_read["raw_sha256"] == receipt["prior_migration"].get("receipt_sha256") and manifest.get("compatibility_migration", {}).get("receipt_sha256") == prior_read["raw_sha256"], "control-path prior migration binding mismatches")
    auth = receipt["authorization"]
    _require(auth.get("approval_mode") == "approve_for_me" and auth.get("effective_sandbox") == "workspace-write" and auth.get("explicit_sandbox_argument_omitted") is True and all(auth.get(key) is False for key in ("objective_changed", "quantifiers_changed", "counters_reset", "permission_scope_expanded")), "control-path authorization envelope is invalid")
    validate_prior_state(manifest, run, prior_read, _prior_paths(paths), require_applied=True)
    target_names = {
        "launcher_entry": "launcher_entry", "launcher_module": "launcher_module", "argv_compat_module": "argv_compat_module",
        "canary_host": "canary_host", "canary_module": "canary_module", "canary_entry": "canary_entry",
        "cycle_cli": "cycle_cli", "amendment_module": "amendment_module", "amendment_cli": "amendment_cli",
    }
    try:
        for receipt_name, path_name in target_names.items():
            assert_file_binding(receipt["target"].get(receipt_name), paths[path_name], f"control-path {receipt_name}")
        assert_counters(receipt["source"].get("counters"), manifest["cycle_ledger"].get("checkpoint"), allow_advance=require_applied)
    except CompatibilityMigrationError as exc:
        raise ControlPathAmendmentError(str(exc)) from exc
    if not require_applied:
        return
    record = manifest.get("control_path_amendment_v2")
    _require(isinstance(record, dict) and record.get("protocol") == receipt["protocol"] and record.get("amendment_id") == receipt["amendment_id"] and record.get("receipt_sha256") == receipt_read["raw_sha256"], "signed manifest is not bound to this control-path amendment")
    archive = run / str(receipt.get("archive_directory_name", ""))
    for name, digest in (
        ("pre-amendment-run.json", receipt["source"].get("manifest_primary_sha256")),
        ("pre-amendment-run.json.bak", receipt["source"].get("manifest_backup_sha256")),
        ("control-path-receipt.json", receipt_read["raw_sha256"]),
    ):
        try: digest = require_hash(digest, f"archive {name}")
        except CompatibilityMigrationError as exc: raise ControlPathAmendmentError(str(exc)) from exc
        item = archive / name
        _require(item.is_file() and sha256_file(item) == digest, f"control-path source archive mismatches: {name}")


def _result(action: str, status: str, manifest: dict[str, Any], receipt_hash: str) -> dict[str, Any]:
    checkpoint = manifest["cycle_ledger"]["checkpoint"]
    return {"Ok": True, "Action": action, "Status": status, "RunId": manifest["run_id"], "ThreadId": manifest["thread_id"], "ReceiptSha256": receipt_hash, "AttemptCount": checkpoint["attempt_count"], "TotalRoundCount": checkpoint["total_round_count"]}


def invoke(action: str, run_directory: Path, receipt_file: Path, prior_receipt_file: Path, paths: dict[str, Path]) -> dict[str, Any]:
    _require(action in {"Analyze", "Apply", "Verify"}, "unsupported control-path action")
    run = assert_no_symlink_chain(run_directory); manifest_path = run / "run.json"
    receipt_read = read_receipt(receipt_file); prior_read = read_receipt(prior_receipt_file)
    with FileLease("run", str(run)):
        manifest = read_signed_json(manifest_path)["payload"]
        _require(isinstance(manifest, dict), "signed run manifest is invalid")
        if "control_path_amendment_v2" in manifest:
            validate_state(manifest, run, receipt_read, prior_read, paths, require_applied=True)
            return _result(action, "already_applied", manifest, receipt_read["raw_sha256"])
        validate_state(manifest, run, receipt_read, prior_read, paths, require_applied=False)
        if action == "Verify": raise ControlPathAmendmentError("control-path amendment has not been applied")
        receipt = receipt_read["value"]; source = receipt["source"]
        _require(manifest.get("status") == source.get("status"), "control-path source status mismatches")
        process = manifest.get("process")
        if process is not None:
            identity = process.get("identity") if isinstance(process, dict) else None
            _require(isinstance(identity, dict) and not process_identity_matches(identity), "control-path amendment refuses a live or unverifiable process")
        try:
            primary_hash = require_hash(source.get("manifest_primary_sha256"), "source primary hash")
            backup_hash = require_hash(source.get("manifest_backup_sha256"), "source backup hash")
        except CompatibilityMigrationError as exc: raise ControlPathAmendmentError(str(exc)) from exc
        _require(sha256_file(manifest_path) == primary_hash and sha256_file(Path(f"{manifest_path}.bak")) == backup_hash, "control-path source manifest bytes differ from the receipt")
        if action == "Analyze": return _result(action, "ready_to_apply", manifest, receipt_read["raw_sha256"])
        archive = run / str(receipt["archive_directory_name"]); archive.mkdir(mode=0o700, exist_ok=True); assert_no_symlink_chain(archive)
        try:
            _archive_copy(manifest_path, archive / "pre-amendment-run.json", primary_hash)
            _archive_copy(Path(f"{manifest_path}.bak"), archive / "pre-amendment-run.json.bak", backup_hash)
            _archive_copy(receipt_read["path"], archive / "control-path-receipt.json", receipt_read["raw_sha256"])
        except CompatibilityMigrationError as exc: raise ControlPathAmendmentError(str(exc)) from exc
        manifest["control_path_amendment_v2"] = {
            "schema_version": 1, "protocol": receipt["protocol"], "amendment_id": receipt["amendment_id"],
            "receipt_sha256": receipt_read["raw_sha256"], "source_manifest_primary_sha256": primary_hash,
            "source_manifest_backup_sha256": backup_hash, "source_counters": source["counters"],
            "approval_mode": "approve_for_me", "effective_sandbox": "workspace-write",
            "explicit_sandbox_argument_omitted": True, "objective_changed": False, "quantifiers_changed": False,
            "counters_reset": False, "permission_scope_expanded": False, "applied_at_utc": utc_now(),
        }
        manifest["revision"] += 1; manifest["updated_at_utc"] = utc_now(); manifest["exit_reason"] = "control_path_amendment_v2_applied_ready_to_resume"
        write_signed_json(manifest_path, manifest)
        read_back = read_signed_json(manifest_path)["payload"]
        validate_state(read_back, run, receipt_read, prior_read, paths, require_applied=True)
        return _result(action, "applied", read_back, receipt_read["raw_sha256"])
