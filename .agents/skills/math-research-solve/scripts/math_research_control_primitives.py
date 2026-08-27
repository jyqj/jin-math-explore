#!/usr/bin/env python3
"""Cross-platform integrity, atomic-file, and lease primitives.

The module is standard-library only.  POSIX keys are protected by owner-only
directory/file modes; Windows keys use CurrentUser DPAPI.  Integrity envelopes
keep the historical HMAC-SHA256 and primary/backup recovery semantics.
"""

from __future__ import annotations

import base64
import ctypes
import hashlib
import hmac
import json
import os
import secrets
import shutil
import stat
import sys
import tempfile
from contextlib import AbstractContextManager
from ctypes import wintypes
from pathlib import Path
from typing import Any, Callable


class ControlIntegrityError(RuntimeError):
    """A fail-closed control-state validation error."""


def _reject_duplicate(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ControlIntegrityError(f"duplicate JSON property: {key}")
        result[key] = value
    return result


def strict_json_loads(text: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_reject_duplicate, parse_constant=lambda value: (_ for _ in ()).throw(ControlIntegrityError(f"invalid JSON constant: {value}")))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ControlIntegrityError("invalid strict JSON") from exc


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _existing_chain(path: Path) -> list[Path]:
    absolute = Path(os.path.abspath(path))
    parts = absolute.parts
    cursor = Path(parts[0])
    result = [cursor]
    for part in parts[1:]:
        cursor /= part
        if cursor.exists() or cursor.is_symlink():
            result.append(cursor)
        else:
            break
    return result


def assert_no_symlink_chain(path: Path) -> Path:
    absolute = Path(os.path.abspath(path))
    for item in _existing_chain(absolute):
        try:
            if stat.S_ISLNK(item.lstat().st_mode):
                raise ControlIntegrityError(f"symbolic link is forbidden in control path: {item}")
        except FileNotFoundError:
            break
    return absolute


def _fsync_directory(directory: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write(path: Path, data: bytes, *, mode: int = 0o600) -> None:
    path = assert_no_symlink_chain(path)
    parent = assert_no_symlink_chain(path.parent)
    if not parent.is_dir():
        raise ControlIntegrityError(f"output parent is missing: {parent}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=parent)
    temporary = Path(temporary_name)
    try:
        if os.name != "nt":
            os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = -1
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            backup_temp = temporary.with_suffix(".bak.tmp")
            try:
                shutil.copyfile(path, backup_temp)
                if os.name != "nt":
                    os.chmod(backup_temp, mode)
                with backup_temp.open("r+b") as stream:
                    os.fsync(stream.fileno())
                os.replace(backup_temp, Path(f"{path}.bak"))
            finally:
                backup_temp.unlink(missing_ok=True)
        os.replace(temporary, path)
        _fsync_directory(parent)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def _default_state_root() -> Path:
    override = os.environ.get("MATH_RESEARCH_CONTROL_HOME")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA")
        if not base:
            raise ControlIntegrityError("LOCALAPPDATA is unavailable")
        return Path(base) / "OpenAI" / "Codex" / "MathResearchLauncher"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "OpenAI" / "Codex" / "MathResearchLauncher"
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "openai" / "codex" / "math-research-launcher"


def _secure_directory(path: Path) -> Path:
    path = assert_no_symlink_chain(path)
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    assert_no_symlink_chain(path)
    if os.name != "nt":
        metadata = path.stat()
        if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
            raise ControlIntegrityError("control directory is not owner-private")
    return path


if os.name == "nt":
    class _DataBlob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _windows_dpapi(data: bytes, *, protect: bool) -> bytes:
    if os.name != "nt":
        raise ControlIntegrityError("DPAPI is available only on Windows")
    source_buffer = ctypes.create_string_buffer(data)
    source = _DataBlob(len(data), ctypes.cast(source_buffer, ctypes.POINTER(ctypes.c_byte)))
    destination = _DataBlob()
    function = ctypes.windll.crypt32.CryptProtectData if protect else ctypes.windll.crypt32.CryptUnprotectData
    if protect:
        ok = function(ctypes.byref(source), None, None, None, None, 0, ctypes.byref(destination))
    else:
        ok = function(ctypes.byref(source), None, None, None, None, 0, ctypes.byref(destination))
    if not ok:
        raise ControlIntegrityError("CurrentUser DPAPI operation failed")
    try:
        return ctypes.string_at(destination.pbData, destination.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(destination.pbData)


def manifest_key(*, create: bool = False) -> tuple[bytes, str]:
    root = _secure_directory(_default_state_root())
    path = assert_no_symlink_chain(root / "manifest-key.v2")
    if not path.exists():
        if not create:
            raise ControlIntegrityError("manifest key is missing")
        plain = secrets.token_bytes(32)
        stored = _windows_dpapi(plain, protect=True) if os.name == "nt" else plain
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(stored)
                stream.flush()
                os.fsync(stream.fileno())
            _fsync_directory(root)
        except FileExistsError:
            pass
    assert_no_symlink_chain(path)
    if os.name != "nt":
        metadata = path.stat()
        if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
            raise ControlIntegrityError("manifest key is not owner-private")
    stored = path.read_bytes()
    key = _windows_dpapi(stored, protect=False) if os.name == "nt" else stored
    if len(key) != 32:
        raise ControlIntegrityError("manifest key has an invalid length")
    return key, "Windows-DPAPI-CurrentUser" if os.name == "nt" else "OwnerOnly-0600"


def current_user_scope_id() -> str:
    """Return a stable pseudonymous per-key user scope without exposing names."""
    key, _ = manifest_key(create=False)
    return "hmac-sha256:" + hmac.new(key, b"math-research-user-scope/v1", hashlib.sha256).hexdigest()


def _envelope(payload: Any, key: bytes, protection: str) -> dict[str, Any]:
    raw = canonical_json(payload).encode("utf-8")
    return {
        "integrity_schema": 2,
        "payload": payload,
        "integrity": {
            "algorithm": "HMAC-SHA256",
            "key_protection": protection,
            "payload_sha256": hashlib.sha256(raw).hexdigest(),
            "hmac_sha256": hmac.new(key, raw, hashlib.sha256).hexdigest(),
        },
    }


def write_signed_json(path: Path, payload: Any, *, create_key: bool = False) -> None:
    key, protection = manifest_key(create=create_key)
    normalized = strict_json_loads(canonical_json(payload))
    atomic_write(path, (json.dumps(_envelope(normalized, key, protection), ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    read = read_signed_json(path)
    if read["recovered_from_backup"] or canonical_json(read["payload"]) != canonical_json(normalized):
        raise ControlIntegrityError("signed JSON primary read-back failed")


def _verify_envelope(path: Path, key: bytes, protection: str) -> Any:
    text = path.read_text(encoding="utf-8", errors="strict")
    value = strict_json_loads(text)
    if not isinstance(value, dict) or set(value) != {"integrity_schema", "payload", "integrity"}:
        raise ControlIntegrityError("signed JSON envelope shape is invalid")
    integrity = value["integrity"]
    if value["integrity_schema"] != 2 or not isinstance(integrity, dict):
        raise ControlIntegrityError("signed JSON envelope version is invalid")
    if set(integrity) != {"algorithm", "key_protection", "payload_sha256", "hmac_sha256"}:
        raise ControlIntegrityError("signed JSON integrity shape is invalid")
    if integrity["algorithm"] != "HMAC-SHA256" or integrity["key_protection"] != protection:
        raise ControlIntegrityError("signed JSON integrity policy is invalid")
    raw = canonical_json(value["payload"]).encode("utf-8")
    if not hmac.compare_digest(hashlib.sha256(raw).hexdigest(), str(integrity["payload_sha256"])):
        raise ControlIntegrityError("signed JSON payload hash mismatches")
    expected = hmac.new(key, raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, str(integrity["hmac_sha256"])):
        raise ControlIntegrityError("signed JSON authentication mismatches")
    return value["payload"]


def read_signed_json(path: Path) -> dict[str, Any]:
    path = assert_no_symlink_chain(path)
    key, protection = manifest_key(create=False)
    failures: list[str] = []
    for candidate in (path, Path(f"{path}.bak")):
        if not candidate.is_file():
            continue
        try:
            payload = _verify_envelope(assert_no_symlink_chain(candidate), key, protection)
            return {"payload": payload, "recovered_from_backup": candidate != path, "source_path": str(candidate)}
        except (ControlIntegrityError, OSError, UnicodeError) as exc:
            failures.append(type(exc).__name__)
    raise ControlIntegrityError("no valid signed JSON primary or backup payload")


class FileLease(AbstractContextManager["FileLease"]):
    """Non-blocking per-user file lease with OS-native advisory locking."""

    def __init__(self, kind: str, value: str):
        if kind not in {"run", "thread"} or not value:
            raise ValueError("invalid lease identity")
        digest = hashlib.sha256(f"{kind}:{value.casefold()}".encode()).hexdigest()
        self.path = _secure_directory(_default_state_root() / "leases") / f"{kind}-{digest}.lock"
        self._stream: Any = None

    def __enter__(self) -> "FileLease":
        self._stream = self.path.open("a+b")
        try:
            if os.name == "nt":
                import msvcrt
                self._stream.seek(0)
                if self._stream.tell() == 0:
                    self._stream.write(b"0"); self._stream.flush()
                self._stream.seek(0)
                msvcrt.locking(self._stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self._stream.close(); self._stream = None
            raise ControlIntegrityError("lease is already held") from exc
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if self._stream is None:
            return
        try:
            if os.name == "nt":
                import msvcrt
                self._stream.seek(0); msvcrt.locking(self._stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._stream.fileno(), fcntl.LOCK_UN)
        finally:
            self._stream.close(); self._stream = None
