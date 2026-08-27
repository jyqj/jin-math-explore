#!/usr/bin/env python3
"""Shared fail-closed primitives for Math Research Solve v13."""
from __future__ import annotations
import hashlib, json, os, stat, sys
from pathlib import Path, PurePosixPath
from typing import Any

OBJECTIVE_FIELDS = ("statement", "domain", "quantifier_order", "assumptions", "evidence_standard", "completion_standard")
HEX64 = set("0123456789abcdef")

class V13Error(RuntimeError):
    def __init__(self, code: str, message: str, path: str | None = None):
        super().__init__(message); self.code, self.message, self.path = code, message, path

def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"): stream.reconfigure(encoding="utf-8", errors="strict", newline="\n")

def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out: raise V13Error("duplicate_json_key", f"Duplicate JSON key: {key}", key)
        out[key] = value
    return out

def load_json_bytes(raw: bytes, *, canonical_required: bool = False) -> Any:
    if raw.startswith(b"\xef\xbb\xbf"): raise V13Error("utf8_bom_forbidden", "UTF-8 BOM is forbidden")
    if b"\r" in raw: raise V13Error("crlf_forbidden", "Only LF newlines are allowed")
    try: value = json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_pairs_no_duplicates)
    except V13Error: raise
    except Exception as exc: raise V13Error("invalid_json", str(exc)) from exc
    if canonical_required and raw != canonical_json(value): raise V13Error("noncanonical_json", "JSON bytes are not canonical")
    return value

def load_json(path: Path, *, canonical_required: bool = False) -> Any: return load_json_bytes(path.read_bytes(), canonical_required=canonical_required)
def canonical_json(value: Any) -> bytes: return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")

def objective_bytes(value: Any) -> bytes:
    if not isinstance(value, dict) or tuple(value.keys()) != OBJECTIVE_FIELDS: raise V13Error("objective_fields_invalid", "objective-core.json must contain exactly the six ordered fields")
    for field in OBJECTIVE_FIELDS:
        if field == "assumptions":
            if not isinstance(value[field], list) or not all(isinstance(x, str) for x in value[field]): raise V13Error("objective_assumptions_invalid", "assumptions must be an ordered string array", field)
        elif not isinstance(value[field], str): raise V13Error("objective_field_invalid", f"{field} must be a string", field)
    return canonical_json(value)

def sha256_bytes(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest()
def is_sha256(value: Any) -> bool: return isinstance(value, str) and len(value) == 64 and set(value) <= HEX64

def safe_relative(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value: raise V13Error("unsafe_path", "Path must be a nonempty POSIX relative path", str(value))
    rel = PurePosixPath(value)
    if rel.is_absolute() or any(p in ("", ".", "..") for p in rel.parts) or ":" in rel.parts[0]: raise V13Error("unsafe_path", "Absolute and traversal paths are forbidden", value)
    return rel

def resolved_child(root: Path, rel_text: str, *, require_existing: bool = False) -> Path:
    rel = safe_relative(rel_text); root_resolved = root.resolve(strict=True); target = root.joinpath(*rel.parts); cursor = root_resolved
    for part in rel.parts:
        cursor = cursor / part
        if cursor.exists() or cursor.is_symlink():
            info = os.lstat(cursor)
            if stat.S_ISLNK(info.st_mode): raise V13Error("reparse_point_forbidden", "Symlink/reparse traversal is forbidden", rel_text)
            resolved = cursor.resolve(strict=True)
            if root_resolved != resolved and root_resolved not in resolved.parents: raise V13Error("path_escape", "Resolved path escapes root", rel_text)
    if require_existing and not target.exists(): raise V13Error("missing_path", "Required path does not exist", rel_text)
    existing_parent = target.parent
    while not existing_parent.exists():
        existing_parent = existing_parent.parent
    parent = existing_parent.resolve(strict=True)
    if root_resolved != parent and root_resolved not in parent.parents: raise V13Error("path_escape", "Existing parent escapes root", rel_text)
    return target

def inventory(root: Path) -> list[dict[str, Any]]:
    root = root.resolve(strict=True); rows: list[dict[str, Any]] = []; seen_case: set[str] = set()
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix().casefold()):
        rel = path.relative_to(root).as_posix(); folded = rel.casefold()
        if folded in seen_case: raise V13Error("case_collision", "Case-insensitive path collision", rel)
        seen_case.add(folded); info = os.lstat(path)
        if stat.S_ISLNK(info.st_mode): raise V13Error("reparse_point_forbidden", "Symlink/reparse item is forbidden", rel)
        if path.is_file(): rows.append({"path": rel, "size": info.st_size, "sha256": sha256_file(path)})
        elif not path.is_dir(): raise V13Error("unknown_file_type", "Unsupported filesystem item", rel)
    return rows

def emit(value: Any, code: int = 0) -> int: print(json.dumps(value, ensure_ascii=False, separators=(",", ":"))); return code
def error_result(exc: BaseException) -> tuple[dict[str, Any], int]:
    if isinstance(exc, V13Error): return {"ok": False, "error": {"code": exc.code, "message": exc.message, "path": exc.path}}, 2
    return {"ok": False, "error": {"code": "internal_error", "message": f"{type(exc).__name__}: {exc}"}}, 3
