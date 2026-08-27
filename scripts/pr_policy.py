#!/usr/bin/env python3
"""Mechanical PR scope policy for jin-math-explore.

This validates branch/title/path separation. It does not review mathematics.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PROJECT_TITLE = re.compile(r"^\[(P-[0-9]{4,})\]\[(window|source|verify|terminal|genesis|state)\]\s+\S", re.IGNORECASE)
SHARED_TITLE = re.compile(r"^\[shared\]\[(S-[0-9]{4,})\]\s+\S", re.IGNORECASE)
SIMPLE_TITLE = re.compile(r"^\[(infra|program)\]\s+\S", re.IGNORECASE)
PROJECT_PATH = re.compile(r"^projects/(P-[0-9]{4,})--[^/]+(?:/|$)", re.IGNORECASE)
REGISTRY_PATH = re.compile(r"^registry/projects/(P-[0-9]{4,})\.json$", re.IGNORECASE)
OBJECTIVE_SUFFIX = "/.research/identity/objective-core.json"


@dataclass(frozen=True)
class Change:
    status: str
    path: str


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    path: str = ""


@dataclass(frozen=True)
class PullRequestKind:
    family: str
    operation: str
    object_id: str | None


def classify_title(title: str) -> PullRequestKind | None:
    match = PROJECT_TITLE.match(title)
    if match:
        return PullRequestKind("project", match.group(2).lower(), match.group(1).upper())
    match = SHARED_TITLE.match(title)
    if match:
        return PullRequestKind("shared", "publish", match.group(1).upper())
    match = SIMPLE_TITLE.match(title)
    if match:
        return PullRequestKind(match.group(1).lower(), match.group(1).lower(), None)
    return None


def expected_branch(kind: PullRequestKind) -> str:
    if kind.family == "infra":
        return "infra/"
    if kind.family == "program":
        return "program/"
    if kind.family == "shared":
        return f"shared/{kind.object_id.lower()}"
    prefix = {
        "window": "research",
        "source": "source",
        "verify": "verify",
        "terminal": "terminal",
        "genesis": "genesis",
        "state": "state",
    }[kind.operation]
    return f"{prefix}/{kind.object_id.lower()}/"


def read_changes(root: Path, base: str, head: str) -> list[Change]:
    completed = subprocess.run(
        ["git", "diff", "--name-status", "--find-renames", f"{base}...{head}"],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    changes: list[Change] = []
    for line in completed.stdout.splitlines():
        fields = line.split("\t")
        status = fields[0]
        if status.startswith(("R", "C")) and len(fields) == 3:
            changes.append(Change("D", fields[1]))
            changes.append(Change("A", fields[2]))
        elif len(fields) == 2:
            changes.append(Change(status[:1], fields[1]))
    return changes


def _project_ids(changes: Iterable[Change]) -> set[str]:
    ids: set[str] = set()
    for change in changes:
        match = PROJECT_PATH.match(change.path) or REGISTRY_PATH.match(change.path)
        if match:
            ids.add(match.group(1).upper())
    return ids


def _allowed_project_path(path: str, project_id: str) -> bool:
    return (
        bool(re.match(rf"^projects/{re.escape(project_id)}--[^/]+/", path, re.IGNORECASE))
        or path.lower() == f"registry/projects/{project_id.lower()}.json"
        or path.startswith("catalog/")
    )


def _load_added_verification_candidates(root: Path, changes: Iterable[Change]) -> list[str]:
    candidates: list[str] = []
    for change in changes:
        if change.status != "A" or not change.path.endswith("jin-math-verification.json"):
            continue
        receipt_path = root / change.path
        if not receipt_path.is_file():
            continue
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            relative = receipt["candidate"]["path"]
        except (OSError, KeyError, TypeError, json.JSONDecodeError):
            continue
        project_match = PROJECT_PATH.match(change.path)
        if project_match:
            project_dir = change.path.split("/", 2)[:2]
            candidates.append("/".join(project_dir + [relative]))
    return candidates


def evaluate(root: Path, title: str, branch: str, changes: list[Change]) -> list[Finding]:
    findings: list[Finding] = []
    kind = classify_title(title)
    if kind is None:
        return [Finding("pr_title_invalid", "title must use a registered [infra], [program], [P-XXXX][type], or [shared][S-XXXX] prefix")]
    branch = branch.strip()
    if branch != branch.lower() or not branch.startswith(expected_branch(kind)):
        findings.append(Finding("branch_name_invalid", f"expected lowercase branch prefix {expected_branch(kind)}", branch))
    if not changes:
        findings.append(Finding("empty_change", "PR contains no changed files"))
        return findings

    changed_project_ids = _project_ids(changes)
    if kind.family == "project":
        if changed_project_ids - {kind.object_id}:
            findings.append(Finding("changed_project_count", f"Project PR may touch only {kind.object_id}; found {sorted(changed_project_ids)}"))
        for change in changes:
            if not _allowed_project_path(change.path, kind.object_id or ""):
                findings.append(Finding("project_scope_violation", "Project PR contains protocol/other-project files", change.path))
    elif changed_project_ids:
        findings.append(Finding("authority_scope_violation", f"{kind.family} PR cannot advance Project authority: {sorted(changed_project_ids)}"))

    objective_changes = [change for change in changes if change.path.endswith(OBJECTIVE_SUFFIX)]
    if kind.family == "project" and kind.operation == "genesis":
        project_id = kind.object_id or ""
        registry = f"registry/projects/{project_id}.json".lower()
        required_suffixes = ("/project.json", OBJECTIVE_SUFFIX)
        if not any(change.path.lower() == registry and change.status == "A" for change in changes):
            findings.append(Finding("genesis_registry_missing", "genesis must add the matching registry entry"))
        for suffix in required_suffixes:
            if not any(change.path.endswith(suffix) and change.status == "A" for change in changes):
                findings.append(Finding("genesis_project_incomplete", f"genesis must add {suffix}"))
        for change in changes:
            if PROJECT_PATH.match(change.path) and change.status != "A":
                findings.append(Finding("genesis_not_create_only", "genesis Project bytes must be newly added", change.path))
    elif objective_changes:
        for change in objective_changes:
            findings.append(Finding("objective_immutability", "objective may only be added by a genesis PR", change.path))

    if kind.family == "infra":
        forbidden = ("projects/", "registry/projects/", "registry/shared-results/", "catalog/")
        for change in changes:
            if change.path.startswith(forbidden):
                findings.append(Finding("infra_authority_violation", "infra PR cannot publish mathematical/registry authority", change.path))
    elif kind.family == "program":
        allowed = ("program/", "docs/", "PROGRAM_CHARTER.md", "README.md", "CONTRIBUTING.md")
        for change in changes:
            if not change.path.startswith(allowed):
                findings.append(Finding("program_scope_violation", "program PR is limited to governance documentation", change.path))
    elif kind.family == "shared":
        expected = f"registry/shared-results/{kind.object_id}.json".lower()
        for change in changes:
            if change.path.lower() != expected or change.status != "A":
                findings.append(Finding("shared_scope_violation", "shared-result PR must add only its matching registry object", change.path))

    if kind.family == "project" and kind.operation == "verify":
        receipt_changes = [change for change in changes if change.status == "A" and change.path.endswith("jin-math-verification.json")]
        if not receipt_changes:
            findings.append(Finding("verification_receipt_missing", "verify PR must add a jin-math-verification.json receipt"))
        changed_paths = {change.path for change in changes}
        for candidate in _load_added_verification_candidates(root, changes):
            if candidate in changed_paths:
                findings.append(Finding("verification_candidate_modified", "verify PR modifies its frozen candidate", candidate))
    return sorted(set(findings), key=lambda item: (item.code, item.path, item.message))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PR title, branch, and changed-file scope mechanically.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--title", default=os.environ.get("PR_TITLE"))
    parser.add_argument("--branch", default=os.environ.get("PR_BRANCH"))
    parser.add_argument("--base", default=os.environ.get("PR_BASE_SHA"))
    parser.add_argument("--head", default=os.environ.get("PR_HEAD_SHA", "HEAD"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not all((args.title, args.branch, args.base, args.head)):
        parser.error("title, branch, base, and head are required via arguments or PR_* environment variables")
    root = args.root.resolve()
    changes = read_changes(root, args.base, args.head)
    findings = evaluate(root, args.title, args.branch, changes)
    payload = {"ok": not findings, "scope": "pr_title_branch_and_changed_files_only", "mathematical_truth_verified": False, "findings": [item.__dict__ for item in findings]}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    elif findings:
        for item in findings:
            print(f"{item.code}: {item.path}: {item.message}")
    else:
        print("PASS: PR scope policy satisfied; mathematical truth was not assessed.")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
