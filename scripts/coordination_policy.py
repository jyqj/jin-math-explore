#!/usr/bin/env python3
"""Mechanical coordination-manifest policy for jin-math-explore.

The policy validates declared coordination metadata and changed-file scope. It
never decides mathematical truth, lease ownership, or verifier correctness.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping, Sequence


PROTOCOL = "jin-math-agent-coordination/v1"
MARKER = "jin-math-coordination:v1"
MANIFEST_RE = re.compile(
    rf"<!--\s*{re.escape(MARKER)}\s*\n(?P<payload>.*?)\n\s*-->",
    re.DOTALL,
)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/+\-]{1,127}$")
LEASE_RE = re.compile(r"^L-[A-Za-z0-9][A-Za-z0-9._:\-]{2,127}$")
VERIFY_TITLE = re.compile(r"^\[P-[0-9]{4,}\]\[verify\]\s+\S", re.IGNORECASE)

ALLOWED_ACTOR_KINDS = {"human", "agent", "automation"}
ALLOWED_ROLES = {
    "human_owner",
    "program_steward",
    "protocol_maintainer",
    "source_auditor",
    "solver",
    "compute_runner",
    "independent_verifier",
    "reconciler",
    "integrator",
    "automation",
}
ALLOWED_LEASE_MODES = {"exclusive_write", "partitioned_write"}
ALLOWED_HANDOFF_STATUS = {"none", "partial", "complete", "blocked"}
GLOBAL_SERIAL_PREFIXES = (
    ".github/",
    ".agents/skills/",
    "program/",
    "schemas/",
    "scripts/",
    "tests/",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "PROGRAM_CHARTER.md",
    "README.md",
    "skill-dependencies.json",
    "vendored-skills.lock.json",
)


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    path: str = ""


def _mapping(value: object) -> Mapping[str, object] | None:
    return value if isinstance(value, dict) else None


def _sequence(value: object) -> Sequence[object] | None:
    return value if isinstance(value, list) else None


def extract_manifest(body: str) -> tuple[Mapping[str, object] | None, list[Finding]]:
    matches = list(MANIFEST_RE.finditer(body or ""))
    if not matches:
        return None, [Finding("coordination_manifest_missing", f"PR body must contain one <!-- {MARKER} ... --> JSON block")]
    if len(matches) != 1:
        return None, [Finding("coordination_manifest_count", "PR body must contain exactly one coordination manifest")]
    try:
        payload = json.loads(matches[0].group("payload"))
    except json.JSONDecodeError as exc:
        return None, [Finding("coordination_manifest_json", f"coordination manifest is not valid JSON: {exc.msg}")]
    if not isinstance(payload, dict):
        return None, [Finding("coordination_manifest_type", "coordination manifest must be a JSON object")]
    return payload, []


def _valid_token(value: object) -> bool:
    return isinstance(value, str) and bool(TOKEN_RE.fullmatch(value))


def _normalize_scope_entry(value: object) -> tuple[str | None, str | None]:
    if not isinstance(value, str):
        return None, "scope entry must be a string"
    if not value or len(value) > 256:
        return None, "scope entry must contain 1..256 characters"
    if value.startswith("/") or "\\" in value or "//" in value:
        return None, "scope entry must be a normalized repository-relative POSIX path"
    if any(character in value for character in "*?["):
        return None, "scope entry cannot contain glob metacharacters"
    directory = value.endswith("/")
    raw = value[:-1] if directory else value
    if not raw:
        return None, "scope entry cannot be the repository root"
    parts = PurePosixPath(raw).parts
    if any(part in {"", ".", ".."} for part in parts):
        return None, "scope entry cannot contain empty, dot, or parent segments"
    if parts[0] == ".git":
        return None, "scope entry cannot address .git"
    normalized = PurePosixPath(*parts).as_posix()
    return normalized + ("/" if directory else ""), None


def _covers(scope_entry: str, path: str) -> bool:
    return path.startswith(scope_entry) if scope_entry.endswith("/") else path == scope_entry


def _parse_expiry(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc)


def _is_global_serial(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in GLOBAL_SERIAL_PREFIXES)


def _scope(
    lease: Mapping[str, object],
    field: str,
    *,
    required: bool,
) -> tuple[list[str], list[Finding]]:
    raw = _sequence(lease.get(field))
    if raw is None:
        if required:
            return [], [Finding(f"coordination_{field}_type", f"lease.{field} must be a JSON array")]
        return [], []
    if required and not raw:
        return [], [Finding(f"coordination_{field}_empty", f"lease.{field} cannot be empty")]
    if len(raw) > 128:
        return [], [Finding(f"coordination_{field}_large", f"lease.{field} may contain at most 128 entries")]
    normalized: list[str] = []
    findings: list[Finding] = []
    for index, entry in enumerate(raw):
        path, error = _normalize_scope_entry(entry)
        if error:
            findings.append(Finding(f"coordination_{field}_path", error, f"lease.{field}[{index}]"))
        elif path is not None:
            normalized.append(path)
    duplicates = sorted({entry for entry in normalized if normalized.count(entry) > 1})
    for entry in duplicates:
        findings.append(Finding(f"coordination_{field}_duplicate", "scope entry is duplicated", entry))
    return normalized, findings


def evaluate(
    body: str,
    title: str,
    base_sha: str,
    changed_paths: Iterable[str],
    *,
    now: datetime | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    manifest, extraction_findings = extract_manifest(body)
    if extraction_findings:
        return extraction_findings
    assert manifest is not None

    if manifest.get("protocol") != PROTOCOL:
        findings.append(Finding("coordination_protocol", f"protocol must be {PROTOCOL}"))

    issue = manifest.get("issue")
    if not isinstance(issue, int) or isinstance(issue, bool) or issue <= 0:
        findings.append(Finding("coordination_issue", "issue must be a positive integer"))

    actor = _mapping(manifest.get("actor"))
    if actor is None:
        findings.append(Finding("coordination_actor", "actor must be a JSON object"))
        actor = {}
    kind = actor.get("kind")
    if kind not in ALLOWED_ACTOR_KINDS:
        findings.append(Finding("coordination_actor_kind", f"actor.kind must be one of {sorted(ALLOWED_ACTOR_KINDS)}"))
    if not _valid_token(actor.get("id")):
        findings.append(Finding("coordination_actor_id", "actor.id must be a stable non-empty token"))
    if not _valid_token(actor.get("run_id")):
        findings.append(Finding("coordination_run_id", "actor.run_id must identify this execution context"))
    role = actor.get("role")
    if role not in ALLOWED_ROLES:
        findings.append(Finding("coordination_role", f"actor.role must be one of {sorted(ALLOWED_ROLES)}"))

    lease = _mapping(manifest.get("lease"))
    if lease is None:
        findings.append(Finding("coordination_lease", "lease must be a JSON object"))
        lease = {}
    lease_id = lease.get("id")
    if not isinstance(lease_id, str) or not LEASE_RE.fullmatch(lease_id):
        findings.append(Finding("coordination_lease_id", "lease.id must match L-<token>"))
    mode = lease.get("mode")
    if mode not in ALLOWED_LEASE_MODES:
        findings.append(Finding("coordination_lease_mode", f"lease.mode must be one of {sorted(ALLOWED_LEASE_MODES)}"))
    observed_base = lease.get("base_sha")
    if not isinstance(observed_base, str) or not SHA_RE.fullmatch(observed_base):
        findings.append(Finding("coordination_base_sha", "lease.base_sha must be a lowercase 40-hex commit SHA"))
    elif observed_base != base_sha.lower():
        findings.append(Finding("coordination_base_stale", "lease.base_sha must equal the PR event base SHA", observed_base))

    expiry = _parse_expiry(lease.get("expires_at"))
    if expiry is None:
        findings.append(Finding("coordination_lease_expiry", "lease.expires_at must be an ISO-8601 UTC timestamp ending in Z"))
    else:
        current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        if expiry <= current:
            findings.append(Finding("coordination_lease_expired", "lease has expired and must be renewed in the Issue and PR manifest"))

    write_set, write_findings = _scope(lease, "write_set", required=True)
    read_set, read_findings = _scope(lease, "read_set", required=False)
    findings.extend(write_findings)
    findings.extend(read_findings)
    overlap = sorted(set(write_set) & set(read_set))
    for entry in overlap:
        findings.append(Finding("coordination_scope_overlap", "an entry cannot be both read-only and writable", entry))

    normalized_changes: list[str] = []
    for raw_path in changed_paths:
        path, error = _normalize_scope_entry(raw_path)
        if error or path is None or path.endswith("/"):
            findings.append(Finding("coordination_changed_path", error or "changed path must identify a file", str(raw_path)))
        else:
            normalized_changes.append(path)
    if not normalized_changes:
        findings.append(Finding("coordination_empty_diff", "PR contains no changed files"))
    for path in normalized_changes:
        if not any(_covers(entry, path) for entry in write_set):
            findings.append(Finding("coordination_write_scope_violation", "changed file is outside the declared lease.write_set", path))
    for entry in write_set:
        if not any(_covers(entry, path) for path in normalized_changes):
            findings.append(Finding("coordination_write_scope_unused", "declared write scope does not cover any changed file", entry))

    if any(_is_global_serial(path) for path in normalized_changes) and mode != "exclusive_write":
        findings.append(Finding("coordination_global_requires_exclusive", "global protocol/automation paths require an exclusive_write lease"))

    independence = _mapping(manifest.get("independence"))
    if independence is None:
        findings.append(Finding("coordination_independence", "independence must be a JSON object"))
        independence = {}
    required = independence.get("required")
    context_access = independence.get("solver_context_access")
    candidate_frozen = independence.get("candidate_frozen")
    if not isinstance(required, bool):
        findings.append(Finding("coordination_independence_required", "independence.required must be boolean"))
    if not isinstance(context_access, bool):
        findings.append(Finding("coordination_solver_context", "independence.solver_context_access must be boolean"))
    if not isinstance(candidate_frozen, bool):
        findings.append(Finding("coordination_candidate_frozen", "independence.candidate_frozen must be boolean"))
    verification_change = bool(VERIFY_TITLE.match(title or ""))
    if verification_change or role == "independent_verifier":
        if role != "independent_verifier":
            findings.append(Finding("coordination_verifier_role", "[verify] PR requires actor.role=independent_verifier"))
        if required is not True:
            findings.append(Finding("coordination_verifier_independence", "verification requires independence.required=true"))
        if context_access is not False:
            findings.append(Finding("coordination_verifier_context", "independent verifier must declare solver_context_access=false"))
        if candidate_frozen is not True:
            findings.append(Finding("coordination_verifier_candidate", "independent verifier must declare candidate_frozen=true"))

    handoff = _mapping(manifest.get("handoff"))
    if handoff is None:
        findings.append(Finding("coordination_handoff", "handoff must be a JSON object"))
    else:
        status = handoff.get("status")
        if status not in ALLOWED_HANDOFF_STATUS:
            findings.append(Finding("coordination_handoff_status", f"handoff.status must be one of {sorted(ALLOWED_HANDOFF_STATUS)}"))
        summary = handoff.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            findings.append(Finding("coordination_handoff_summary", "handoff.summary must be a non-empty string"))

    return sorted(set(findings), key=lambda item: (item.code, item.path, item.message))


def read_changed_paths(root: Path, base: str, head: str) -> list[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-status", "--find-renames", f"{base}...{head}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    paths: list[str] = []
    for line in completed.stdout.splitlines():
        fields = line.split("\t")
        if fields and fields[0].startswith(("R", "C")) and len(fields) == 3:
            paths.extend(fields[1:])
        elif len(fields) == 2:
            paths.append(fields[1])
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PR coordination manifest and declared write scope mechanically.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--body", default=os.environ.get("PR_BODY"))
    parser.add_argument("--title", default=os.environ.get("PR_TITLE"))
    parser.add_argument("--base", default=os.environ.get("PR_BASE_SHA"))
    parser.add_argument("--head", default=os.environ.get("PR_HEAD_SHA", "HEAD"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not all((args.body, args.title, args.base, args.head)):
        parser.error("body, title, base, and head are required via arguments or PR_* environment variables")
    root = args.root.resolve()
    findings = evaluate(args.body, args.title, args.base, read_changed_paths(root, args.base, args.head))
    payload = {
        "ok": not findings,
        "scope": "coordination_manifest_and_declared_write_set_only",
        "lease_ownership_verified": False,
        "mathematical_truth_verified": False,
        "findings": [item.__dict__ for item in findings],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    elif findings:
        for item in findings:
            print(f"{item.code}: {item.path}: {item.message}")
    else:
        print("PASS: coordination manifest and declared write scope satisfied; lease ownership and mathematical truth were not assessed.")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
