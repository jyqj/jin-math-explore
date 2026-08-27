"""Fail-closed validator for native non-PowerShell platform parity."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path


SCHEMA = "pika-platform-parity/v2"
POWERSHELL_SUFFIXES = {".ps1", ".psm1"}
FORBIDDEN_RUNTIME = re.compile(r"(?i)(?:\bpwsh\b|\bpowershell(?:\.exe)?\b)")
REQUIRED_RECEIPT_FIELDS = {
    "same_inputs",
    "same_outputs",
    "same_side_effects",
    "same_exit_codes",
    "reviewed",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside(root: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    # Rebuild with platform separators without accepting absolute or parent paths.
    parts = Path(value.replace("\\", "/")).parts
    if Path(value).is_absolute() or ".." in parts:
        return None
    resolved = (root / Path(*parts)).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None
    return resolved


def inventory(payload_root: Path) -> dict[tuple[str, str], Path]:
    found: dict[tuple[str, str], Path] = {}
    for skill in sorted(path for path in payload_root.iterdir() if path.is_dir()):
        for path in sorted(skill.rglob("*")):
            if path.is_file() and path.suffix.casefold() in POWERSHELL_SUFFIXES:
                found[(skill.name, path.relative_to(skill).as_posix())] = path
    return found


def validate(payload_root: Path, manifest_path: Path) -> dict[str, object]:
    errors: list[dict[str, str]] = []
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {"ok": False, "code": "manifest_unreadable", "errors": [{"kind": type(exc).__name__}]}
    if data.get("schema") != SCHEMA:
        errors.append({"kind": "schema", "entry": "manifest"})
    entries = data.get("entries")
    if not isinstance(entries, list):
        return {"ok": False, "code": "entries_invalid", "errors": [{"kind": "entries", "entry": "manifest"}]}

    actual = inventory(payload_root)
    declared: dict[tuple[str, str], dict[str, object]] = {}
    for raw in entries:
        if not isinstance(raw, dict):
            errors.append({"kind": "entry_type", "entry": "unknown"})
            continue
        key = (str(raw.get("skill", "")), str(raw.get("powershell_path", "")))
        label = "/".join(key)
        if key in declared:
            errors.append({"kind": "duplicate", "entry": label})
            continue
        declared[key] = raw
        source = actual.get(key)
        if source is None:
            errors.append({"kind": "declared_source_missing", "entry": label})
            continue
        if raw.get("powershell_sha256") != digest(source):
            errors.append({"kind": "source_hash_mismatch", "entry": label})
        if raw.get("implementation_status") != "complete":
            errors.append({"kind": "implementation_incomplete", "entry": label})
        platforms = raw.get("platform_status")
        if not isinstance(platforms, dict):
            errors.append({"kind": "platform_status_missing", "entry": label})
        else:
            linux = platforms.get("linux")
            if not isinstance(linux, dict) or linux.get("status") != "verified" or not isinstance(linux.get("evidence"), str):
                errors.append({"kind": "linux_not_verified", "entry": label})
            darwin = platforms.get("darwin")
            if not isinstance(darwin, dict) or darwin.get("status") not in {"verified", "implemented-unverified"}:
                errors.append({"kind": "darwin_not_implemented", "entry": label})
            elif darwin.get("status") == "implemented-unverified" and not isinstance(darwin.get("reason"), str):
                errors.append({"kind": "darwin_unverified_reason_missing", "entry": label})

        skill_root = payload_root / key[0]
        equivalent = inside(skill_root, raw.get("equivalent_entrypoint"))
        if equivalent is None or not equivalent.is_file() or equivalent.suffix.casefold() not in {".py", ".sh"}:
            errors.append({"kind": "equivalent_missing_or_unsafe", "entry": label})
        else:
            text = equivalent.read_text(encoding="utf-8-sig", errors="replace")
            if FORBIDDEN_RUNTIME.search(text):
                errors.append({"kind": "equivalent_depends_on_powershell", "entry": label})

        for field in ("success_test", "blocked_test"):
            test_path = inside(skill_root, raw.get(field))
            if test_path is None or not test_path.is_file() or test_path.suffix.casefold() != ".py":
                errors.append({"kind": f"{field}_missing_or_unsafe", "entry": label})
            else:
                test_text = test_path.read_text(encoding="utf-8-sig", errors="replace")
                if FORBIDDEN_RUNTIME.search(test_text):
                    errors.append({"kind": f"{field}_depends_on_powershell", "entry": label})

        receipt = raw.get("semantic_parity_receipt")
        if not isinstance(receipt, dict) or set(receipt) != REQUIRED_RECEIPT_FIELDS or not all(
            receipt.get(field) is True for field in REQUIRED_RECEIPT_FIELDS
        ):
            errors.append({"kind": "semantic_parity_receipt_incomplete", "entry": label})

    for key in sorted(set(actual) - set(declared)):
        errors.append({"kind": "undeclared_powershell_file", "entry": "/".join(key)})
    for key in sorted(set(declared) - set(actual)):
        errors.append({"kind": "stale_manifest_entry", "entry": "/".join(key)})

    result = {
        "ok": not errors,
        "code": "platform_parity_valid" if not errors else "platform_parity_incomplete",
        "powershell_files": len(actual),
        "declared_entries": len(declared),
        "error_count": len(errors),
        "errors": errors,
    }
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "references" / "platform-parity-manifest.json",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--full-json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate(args.payload_root.resolve(), args.manifest.resolve())
    if args.full_json:
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    elif args.json:
        summary = {key: value for key, value in result.items() if key != "errors"}
        summary["error_kinds"] = dict(
            sorted(collections.Counter(item["kind"] for item in result.get("errors", [])).items())
        )
        print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
    elif result["ok"]:
        print(f"Platform parity valid: {result['powershell_files']} PowerShell files covered.")
    else:
        print(f"Platform parity incomplete: {result['error_count']} error(s).", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
