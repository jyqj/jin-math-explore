#!/usr/bin/env python3
"""Invoke a hash-pinned, project-local v12-to-v13 migration adapter.

Migration semantics depend on the source project's own frozen evidence and
cannot live as a project example inside a reusable Skill.  This launcher keeps
the common trust boundary: the adapter is explicit, absolute, regular,
non-symlinked, SHA-256 pinned, and its stdout must be one JSON object.  The
adapter remains responsible for the current migration protocol's staging,
semantic review, same-volume exchange, rollback, and recovery contracts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ACTIONS = {"prepare", "finalize-review", "exchange", "recovery-status"}


class MigrationError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def invoke_adapter(adapter: Path, expected_sha256: str, action: str, adapter_args: list[str]) -> dict[str, Any]:
    adapter = adapter.expanduser().resolve()
    if not adapter.is_absolute() or not adapter.is_file() or adapter.is_symlink():
        raise MigrationError("adapter_invalid", "Migration adapter must be an absolute regular non-symlink file.")
    if len(expected_sha256) != 64 or any(char not in "0123456789abcdef" for char in expected_sha256):
        raise MigrationError("adapter_hash_invalid", "Migration adapter SHA-256 must be lowercase hexadecimal.")
    if sha256_file(adapter) != expected_sha256:
        raise MigrationError("adapter_hash_mismatch", "Migration adapter bytes differ from the pinned SHA-256.")
    if action not in ACTIONS:
        raise MigrationError("action_invalid", f"Unsupported migration action: {action}")
    if any("\x00" in item for item in adapter_args):
        raise MigrationError("adapter_argument_invalid", "Migration adapter arguments cannot contain NUL bytes.")
    completed = subprocess.run(
        [sys.executable, "-B", str(adapter), action, *adapter_args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise MigrationError("adapter_failed", f"Pinned migration adapter exited {completed.returncode}: {completed.stderr.strip()}")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise MigrationError("adapter_output_invalid", "Pinned migration adapter did not emit one JSON object.") from exc
    if not isinstance(result, dict):
        raise MigrationError("adapter_output_invalid", "Pinned migration adapter output must be a JSON object.")
    return {
        "schema": "math-research-v12-to-v13-adapter-receipt/v1",
        "adapter": {"path": str(adapter), "sha256": expected_sha256},
        "action": action,
        "result": result,
    }


def parser() -> argparse.ArgumentParser:
    out = argparse.ArgumentParser(description=__doc__)
    out.add_argument("action", choices=sorted(ACTIONS))
    out.add_argument("--adapter", type=Path, required=True)
    out.add_argument("--adapter-sha256", required=True)
    out.add_argument("adapter_args", nargs=argparse.REMAINDER)
    return out


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    forwarded = args.adapter_args[1:] if args.adapter_args[:1] == ["--"] else args.adapter_args
    try:
        result = invoke_adapter(args.adapter, args.adapter_sha256, args.action, forwarded)
        print(json.dumps({"ok": True, **result}, ensure_ascii=False, separators=(",", ":")))
        return 0
    except MigrationError as exc:
        print(json.dumps({"ok": False, "error": {"code": exc.code, "message": str(exc)}}, ensure_ascii=False, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
