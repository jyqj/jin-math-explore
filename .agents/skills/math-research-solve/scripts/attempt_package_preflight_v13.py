#!/usr/bin/env python3
"""Deterministic attempt-package finalization and validation for v13."""
from __future__ import annotations

import copy
import json
import os
import re
import shutil
import stat
import uuid
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable

from v13_common import V13Error, canonical_json, inventory, is_sha256, load_json_bytes, sha256_bytes, sha256_file

MANIFEST_NAME = "artifact-manifest.json"
RECEIPT_NAME = "attempt-package-preflight.json"
MANIFEST_SCHEMA = "math-research-attempt-artifact-manifest/v1"
RECEIPT_SCHEMA = "math-research-attempt-package-preflight/v1"
FINALIZER_VERSION = 1
HEX64_RE = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{64}(?![0-9A-Fa-f])")
RECEIPT_FIELDS = {
    "schema", "attempt_id", "status", "package_root", "candidate", "dependencies",
    "artifact_refs_sha256", "package_inventory_sha256", "artifact_manifest",
    "file_count_excluding_receipt", "total_bytes_excluding_receipt",
    "max_total_bytes", "finalizer_version",
}
MANIFEST_FIELDS = {"schema", "attempt_id", "artifacts", "artifact_count", "total_bytes"}


def require(condition: bool, code: str, message: str, path: str | None = None) -> None:
    if not condition:
        raise V13Error(code, message, path)


def safe_rel(value: str) -> str:
    require(isinstance(value, str) and value and "\\" not in value and "\x00" not in value, "unsafe_package_path", "Package paths must be nonempty POSIX-relative strings", str(value))
    rel = PurePosixPath(value)
    require(not rel.is_absolute() and all(part not in {"", ".", ".."} for part in rel.parts) and ":" not in rel.parts[0], "unsafe_package_path", "Package path traversal/absolute paths are forbidden", value)
    return rel.as_posix()


def pointer(value: Any, name: str = "pointer") -> dict[str, str]:
    require(isinstance(value, dict) and set(value) == {"path", "sha256"}, "package_pointer_invalid", f"{name} must contain exactly path and sha256")
    path = safe_rel(value["path"])
    require(is_sha256(value["sha256"]), "package_pointer_invalid", f"{name}.sha256 must be lowercase SHA-256", path)
    return {"path": path, "sha256": value["sha256"]}


def _assert_plain_tree(root: Path) -> None:
    root = root.resolve(strict=True)
    seen: set[str] = set()
    for item in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix().casefold()):
        rel = item.relative_to(root).as_posix()
        folded = rel.casefold()
        require(folded not in seen, "package_case_collision", "Case-insensitive package path collision", rel)
        seen.add(folded)
        info = os.lstat(item)
        attrs = getattr(info, "st_file_attributes", 0)
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        require(not stat.S_ISLNK(info.st_mode) and not (attrs & reparse_flag), "package_reparse_forbidden", "Symlink/reparse items are forbidden", rel)
        require(item.is_dir() or item.is_file(), "package_file_type_invalid", "Only regular files and directories are allowed", rel)


def _join_prefix(prefix: str, rel: str) -> str:
    return PurePosixPath(safe_rel(prefix), safe_rel(rel)).as_posix()


def _local_target(path_text: str, prefix: str, files: set[str]) -> str | None:
    path_text = safe_rel(path_text)
    prefix = safe_rel(prefix)
    prefix_marker = prefix + "/"
    if path_text.startswith(prefix_marker):
        rel = path_text[len(prefix_marker):]
        require(rel in files, "package_local_pointer_missing", "Package-local pointer target is missing", path_text)
        return rel
    return path_text if path_text in files else None


def _walk_pointer_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if "path" in value and "sha256" in value:
            yield value
        for child in value.values():
            yield from _walk_pointer_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_pointer_dicts(child)


def _json_objects(raw_files: dict[str, bytes]) -> dict[str, Any]:
    objects: dict[str, Any] = {}
    for rel, raw in raw_files.items():
        if rel.lower().endswith(".json"):
            require(not raw.startswith(b"\xef\xbb\xbf"), "utf8_bom_forbidden", "UTF-8 BOM is forbidden", rel)
            def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
                value: dict[str, Any] = {}
                for key, item in pairs:
                    require(key not in value, "duplicate_json_key", "Duplicate JSON key in raw attempt package", rel)
                    value[key] = item
                return value
            try:
                objects[rel] = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=no_duplicates)
            except V13Error:
                raise
            except Exception as exc:
                raise V13Error("invalid_json", f"Invalid JSON in raw attempt package: {exc}", rel) from exc
    return objects


def _dependency_graph(objects: dict[str, Any], prefix: str, files: set[str]) -> dict[str, set[str]]:
    graph = {rel: set() for rel in files}
    for rel, value in objects.items():
        for ref in _walk_pointer_dicts(value):
            require(isinstance(ref.get("path"), str), "package_pointer_invalid", "Pointer path must be a string", rel)
            target = _local_target(ref["path"], prefix, files)
            if target is None:
                require(is_sha256(ref.get("sha256")), "package_external_pointer_invalid", "External pointer SHA-256 is invalid", ref["path"])
                continue
            require(target not in {MANIFEST_NAME, RECEIPT_NAME}, "package_reserved_reference", "Content files cannot reference manifest or preflight receipt", ref["path"])
            graph[rel].add(target)
    return graph


def _topological_order(graph: dict[str, set[str]]) -> list[str]:
    visiting: set[str] = set()
    done: set[str] = set()
    order: list[str] = []

    def visit(node: str, chain: list[str]) -> None:
        if node in done:
            return
        require(node not in visiting, "package_hash_cycle", "Package hash references must be acyclic", " -> ".join(chain + [node]))
        visiting.add(node)
        for child in sorted(graph[node], key=str.casefold):
            visit(child, chain + [node])
        visiting.remove(node)
        done.add(node)
        order.append(node)

    for node in sorted(graph, key=str.casefold):
        visit(node, [])
    return order


def _rewrite_local_pointers(value: Any, prefix: str, files: set[str], byte_map: dict[str, bytes]) -> Any:
    value = copy.deepcopy(value)
    for ref in _walk_pointer_dicts(value):
        target = _local_target(ref["path"], prefix, files)
        if target is None:
            continue
        raw = byte_map[target]
        ref["sha256"] = sha256_bytes(raw)
        if "bytes" in ref:
            ref["bytes"] = len(raw)
        if "size" in ref:
            ref["size"] = len(raw)
    return value


def _validate_markdown_hashes(files: dict[str, bytes]) -> None:
    current_hashes = {sha256_bytes(raw) for raw in files.values()}
    for rel, raw in files.items():
        if not rel.lower().endswith(".md"):
            continue
        try:
            text = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise V13Error("package_markdown_utf8_invalid", "Markdown must be strict UTF-8", rel) from exc
        for match in HEX64_RE.finditer(text):
            require(match.group(0).lower() in current_hashes, "package_markdown_stale_hash", "Markdown contains a SHA-256 that does not match any finalized package file; remove it or regenerate the Markdown", rel)


def _manifest(attempt_id: str, files: dict[str, bytes]) -> dict[str, Any]:
    rows = [{"path": rel, "bytes": len(files[rel]), "sha256": sha256_bytes(files[rel])} for rel in sorted(files, key=str.casefold)]
    return {"schema": MANIFEST_SCHEMA, "attempt_id": attempt_id, "artifacts": rows, "artifact_count": len(rows), "total_bytes": sum(row["bytes"] for row in rows)}


def _view_from_directory(root: Path) -> dict[str, bytes]:
    _assert_plain_tree(root)
    return {row["path"]: (root / PurePosixPath(row["path"])).read_bytes() for row in inventory(root)}


def _package_inventory(files: dict[str, bytes]) -> list[dict[str, Any]]:
    return [{"path": rel, "size": len(files[rel]), "sha256": sha256_bytes(files[rel])} for rel in sorted(files, key=str.casefold)]


def _resolve_project_pointer(ref: dict[str, str], prefix: str, files: dict[str, bytes], external_reader: Callable[[str], bytes] | None) -> bytes:
    target = _local_target(ref["path"], prefix, set(files))
    if target is not None:
        raw = files[target]
    else:
        require(external_reader is not None, "package_external_pointer_unverified", "An external pointer requires a project-root verifier", ref["path"])
        raw = external_reader(ref["path"])
    require(sha256_bytes(raw) == ref["sha256"], "package_pointer_hash_mismatch", "Pointer does not bind the final bytes", ref["path"])
    return raw


def validate_package_mapping(
    files: dict[str, bytes], *, expected_closing: dict[str, Any] | None = None,
    external_reader: Callable[[str], bytes] | None = None,
) -> dict[str, Any]:
    require(RECEIPT_NAME in files, "package_receipt_missing", f"{RECEIPT_NAME} is required")
    receipt = load_json_bytes(files[RECEIPT_NAME], canonical_required=True)
    require(isinstance(receipt, dict) and set(receipt) == RECEIPT_FIELDS and receipt.get("schema") == RECEIPT_SCHEMA, "package_receipt_invalid", "Preflight receipt schema/fields are invalid", RECEIPT_NAME)
    require(receipt["status"] == "PASS" and isinstance(receipt["attempt_id"], str) and receipt["attempt_id"] and receipt["finalizer_version"] == FINALIZER_VERSION, "package_receipt_invalid", "Preflight receipt identity/status/version is invalid", RECEIPT_NAME)
    prefix = safe_rel(receipt["package_root"])
    require(isinstance(receipt["max_total_bytes"], int) and receipt["max_total_bytes"] > 0, "package_receipt_invalid", "max_total_bytes must be positive")
    content = {rel: raw for rel, raw in files.items() if rel != RECEIPT_NAME}
    actual_inventory = _package_inventory(content)
    require(receipt["package_inventory_sha256"] == sha256_bytes(canonical_json(actual_inventory)), "package_inventory_mismatch", "Final package inventory changed after preflight")
    require(receipt["file_count_excluding_receipt"] == len(content) and receipt["total_bytes_excluding_receipt"] == sum(len(raw) for raw in content.values()), "package_inventory_mismatch", "Receipt file/byte counts differ")
    require(sum(len(raw) for raw in files.values()) <= receipt["max_total_bytes"], "package_budget_exceeded", "Final package exceeds max_total_bytes")
    require(MANIFEST_NAME in content, "package_manifest_missing", f"{MANIFEST_NAME} is required")
    manifest = load_json_bytes(content[MANIFEST_NAME], canonical_required=True)
    listed_files = {rel: raw for rel, raw in content.items() if rel != MANIFEST_NAME}
    expected_manifest = _manifest(receipt["attempt_id"], listed_files)
    require(manifest == expected_manifest and isinstance(manifest, dict) and set(manifest) == MANIFEST_FIELDS, "package_manifest_mismatch", "Artifact manifest does not exactly cover finalized package content", MANIFEST_NAME)
    manifest_pointer = pointer(receipt["artifact_manifest"], "artifact_manifest")
    require(manifest_pointer["path"] == _join_prefix(prefix, MANIFEST_NAME) and manifest_pointer["sha256"] == sha256_bytes(content[MANIFEST_NAME]), "package_manifest_pointer_mismatch", "Receipt manifest pointer differs from final bytes")
    candidate = None if receipt["candidate"] is None else pointer(receipt["candidate"], "candidate")
    require(isinstance(receipt["dependencies"], list), "package_receipt_invalid", "dependencies must be an array")
    dependencies = [pointer(ref, f"dependencies[{index}]") for index, ref in enumerate(receipt["dependencies"])]
    for ref in ([candidate] if candidate is not None else []) + dependencies + [manifest_pointer]:
        _resolve_project_pointer(ref, prefix, content, external_reader)
    json_objects = _json_objects(listed_files)
    graph = _dependency_graph(json_objects, prefix, set(listed_files))
    _topological_order(graph)
    for rel, value in json_objects.items():
        require(content[rel] == canonical_json(value), "package_json_noncanonical", "All package JSON must be canonical", rel)
        for ref in _walk_pointer_dicts(value):
            target = _local_target(ref["path"], prefix, set(listed_files))
            if target is not None:
                require(ref.get("sha256") == sha256_bytes(listed_files[target]), "package_internal_hash_mismatch", "Internal pointer hash differs from final bytes", ref["path"])
                if "bytes" in ref:
                    require(ref["bytes"] == len(listed_files[target]), "package_internal_size_mismatch", "Internal pointer bytes differ", ref["path"])
                if "size" in ref:
                    require(ref["size"] == len(listed_files[target]), "package_internal_size_mismatch", "Internal pointer size differs", ref["path"])
    _validate_markdown_hashes(listed_files)
    if expected_closing is not None:
        require(receipt["attempt_id"] == expected_closing.get("attempt_id"), "package_closing_binding_mismatch", "Receipt attempt differs from closing payload")
        require(candidate == expected_closing.get("candidate") and dependencies == expected_closing.get("dependencies"), "package_closing_binding_mismatch", "Receipt candidate/dependencies differ from closing payload")
        refs = expected_closing.get("artifact_refs")
        require(isinstance(refs, list), "package_closing_binding_mismatch", "Closing artifact_refs must be an array")
        receipt_path = _join_prefix(prefix, RECEIPT_NAME)
        receipt_refs = [pointer(ref, f"artifact_refs[{index}]") for index, ref in enumerate(refs) if isinstance(ref, dict) and ref.get("path") == receipt_path]
        require(len(receipt_refs) == 1 and receipt_refs[0]["sha256"] == sha256_bytes(files[RECEIPT_NAME]), "package_closing_binding_mismatch", "Closing payload must bind exactly one final receipt")
        other_refs = [pointer(ref, f"artifact_refs[{index}]") for index, ref in enumerate(refs) if ref.get("path") != receipt_path]
        require(receipt["artifact_refs_sha256"] == sha256_bytes(canonical_json(other_refs)), "package_artifact_refs_mismatch", "Receipt does not bind closing artifact_refs")
        require(manifest_pointer in other_refs, "package_artifact_refs_mismatch", "Artifact manifest pointer must be present in closing artifact_refs")
        for ref in other_refs:
            _resolve_project_pointer(ref, prefix, content, external_reader)
    return {
        "ok": True, "status": "PASS", "attempt_id": receipt["attempt_id"],
        "inventory_sha256": receipt["package_inventory_sha256"],
        "file_count": len(files), "total_bytes": sum(len(raw) for raw in files.values()),
        "receipt_sha256": sha256_bytes(files[RECEIPT_NAME]),
    }


def validate_package_directory(root: Path, *, expected_closing: dict[str, Any] | None = None, project_root: Path | None = None) -> dict[str, Any]:
    files = _view_from_directory(root)
    external_reader: Callable[[str], bytes] | None = None
    if project_root is not None:
        resolved_root = project_root.resolve(strict=True)
        def read_external(rel: str) -> bytes:
            target = resolved_root.joinpath(*PurePosixPath(safe_rel(rel)).parts)
            require(target.is_file() and resolved_root in target.resolve(strict=True).parents, "package_external_pointer_missing", "External project pointer is missing or escapes project", rel)
            return target.read_bytes()
        external_reader = read_external
    return validate_package_mapping(files, expected_closing=expected_closing, external_reader=external_reader)


def finalize_package(
    source: Path, staging: Path, *, attempt_id: str, package_root: str,
    candidate_path: str | None = None, dependency_paths: list[str] | None = None,
    external_dependencies: list[dict[str, str]] | None = None,
    external_artifacts: list[dict[str, str]] | None = None,
    max_total_bytes: int = 300_000, project_root: Path | None = None,
) -> dict[str, Any]:
    require(source.is_dir(), "package_source_missing", "Source package directory is missing")
    require(not staging.exists(), "package_staging_exists", "Staging destination must not already exist", str(staging))
    require(isinstance(attempt_id, str) and attempt_id.strip(), "package_attempt_invalid", "attempt_id must be nonempty")
    prefix = safe_rel(package_root)
    require(isinstance(max_total_bytes, int) and max_total_bytes > 0, "package_budget_invalid", "max_total_bytes must be positive")
    _assert_plain_tree(source)
    if project_root is not None:
        require(project_root.resolve(strict=True).stat().st_dev == staging.parent.resolve(strict=True).stat().st_dev, "package_cross_volume_staging", "Package staging must be on the project volume")
    temp = staging.with_name(staging.name + ".tmp-" + uuid.uuid4().hex)
    try:
        shutil.copytree(source, temp)
        _assert_plain_tree(temp)
        for reserved in (MANIFEST_NAME, RECEIPT_NAME):
            reserved_path = temp / reserved
            if reserved_path.exists():
                require(reserved_path.is_file(), "package_reserved_path_invalid", "Reserved package path must be a file", reserved)
                reserved_path.unlink()
        raw_files = _view_from_directory(temp)
        require(raw_files, "package_empty", "Attempt package has no content files")
        files_set = set(raw_files)
        objects = _json_objects(raw_files)
        graph = _dependency_graph(objects, prefix, files_set)
        order = _topological_order(graph)
        finalized = dict(raw_files)
        for rel in order:
            if rel in objects:
                value = _rewrite_local_pointers(objects[rel], prefix, files_set, finalized)
                raw = canonical_json(value)
                path = temp.joinpath(*PurePosixPath(rel).parts)
                replacement = path.with_name(path.name + ".finalize-tmp")
                replacement.write_bytes(raw)
                os.replace(replacement, path)
                finalized[rel] = raw
        _validate_markdown_hashes(finalized)
        manifest = _manifest(attempt_id, finalized)
        manifest_raw = canonical_json(manifest)
        (temp / MANIFEST_NAME).write_bytes(manifest_raw)
        content = dict(finalized)
        content[MANIFEST_NAME] = manifest_raw
        def internal_pointer(rel: str, name: str) -> dict[str, str]:
            rel = safe_rel(rel)
            require(rel in content and rel not in {MANIFEST_NAME, RECEIPT_NAME}, "package_named_file_missing", f"{name} is not a finalized package file", rel)
            return {"path": _join_prefix(prefix, rel), "sha256": sha256_bytes(content[rel])}
        candidate = internal_pointer(candidate_path, "candidate") if candidate_path is not None else None
        dependencies = [internal_pointer(rel, f"dependency[{index}]") for index, rel in enumerate(dependency_paths or [])]
        dependencies.extend(pointer(ref, f"external_dependency[{index}]") for index, ref in enumerate(external_dependencies or []))
        manifest_pointer = {"path": _join_prefix(prefix, MANIFEST_NAME), "sha256": sha256_bytes(manifest_raw)}
        artifact_refs = [manifest_pointer]
        artifact_refs.extend(pointer(ref, f"external_artifact[{index}]") for index, ref in enumerate(external_artifacts or []))
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "attempt_id": attempt_id,
            "status": "PASS",
            "package_root": prefix,
            "candidate": candidate,
            "dependencies": dependencies,
            "artifact_refs_sha256": sha256_bytes(canonical_json(artifact_refs)),
            "package_inventory_sha256": sha256_bytes(canonical_json(_package_inventory(content))),
            "artifact_manifest": manifest_pointer,
            "file_count_excluding_receipt": len(content),
            "total_bytes_excluding_receipt": sum(len(raw) for raw in content.values()),
            "max_total_bytes": max_total_bytes,
            "finalizer_version": FINALIZER_VERSION,
        }
        receipt_raw = canonical_json(receipt)
        require(sum(len(raw) for raw in content.values()) + len(receipt_raw) <= max_total_bytes, "package_budget_exceeded", "Finalized package exceeds max_total_bytes")
        (temp / RECEIPT_NAME).write_bytes(receipt_raw)
        files = dict(content); files[RECEIPT_NAME] = receipt_raw
        receipt_pointer = {"path": _join_prefix(prefix, RECEIPT_NAME), "sha256": sha256_bytes(receipt_raw)}
        closing = {"attempt_id": attempt_id, "candidate": candidate, "dependencies": dependencies, "artifact_refs": artifact_refs + [receipt_pointer]}
        validate_package_mapping(files, expected_closing=closing, external_reader=(lambda rel: (project_root / PurePosixPath(rel)).read_bytes()) if project_root is not None else None)
        os.replace(temp, staging)
        return {"ok": True, "status": "PASS", "attempt_id": attempt_id, "package_root": prefix, "candidate": candidate, "dependencies": dependencies, "artifact_refs": artifact_refs + [receipt_pointer], "receipt_sha256": receipt_pointer["sha256"], "file_count": len(files), "total_bytes": sum(len(raw) for raw in files.values())}
    except Exception:
        if temp.exists():
            shutil.rmtree(temp)
        raise
