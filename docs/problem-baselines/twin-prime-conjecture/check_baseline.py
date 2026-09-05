#!/usr/bin/env python3
"""Validate this reference-only documentation package, never mathematical truth.

No dependencies beyond Python's standard library; no network, source execution,
Lean build, numerical integration or prime enumeration. Exit nonzero on failure.
"""
from __future__ import annotations
import hashlib
import json
import re
import sys
from pathlib import Path

EXPECTED = {
    "README.md", "objective-and-status.md", "progress-ledger.md",
    "methods-and-barriers.md", "latest-186-review.md", "source-audit.md",
    "frontier-and-migration.md", "claims.json", "references.bib",
    "check_baseline.py",
}

def check(directory: Path) -> dict:
    errors: list[str] = []
    present = {p.name for p in directory.iterdir() if p.is_file()}
    if present != EXPECTED:
        errors.append(f"file-set mismatch: missing={sorted(EXPECTED-present)}, extra={sorted(present-EXPECTED)}")
    data = json.loads((directory / "claims.json").read_text(encoding="utf-8"))
    if data.get("authority") != "reference_only" or data.get("mathematical_truth_verified") is not False:
        errors.append("baseline authority was promoted")
    if data.get("as_of") != "2026-09-05":
        errors.append("as-of date changed without checker refresh")
    source_ids = [s["id"] for s in data["sources"]]
    claim_ids = [c["id"] for c in data["claims"]]
    if len(set(source_ids)) != len(source_ids) or len(set(claim_ids)) != len(claim_ids):
        errors.append("duplicate source or claim ID")
    if set(claim_ids) != {f"TP-{i:04d}" for i in range(1, 25)}:
        errors.append("unexpected claim ID set")
    for source in data["sources"]:
        if not source.get("version") or not source.get("checked_locator"):
            errors.append(f"missing source scope: {source['id']}")
        digest = source.get("payload_sha256")
        if digest is not None and not re.fullmatch(r"[0-9a-f]{64}", digest):
            errors.append(f"invalid source hash: {source['id']}")
    graph = {key: [] for key in claim_ids}
    for claim in data["claims"]:
        key = claim["id"]
        if claim.get("authority") != "reference_only" or claim.get("independent_verification") != "not_performed":
            errors.append(f"claim authority changed: {key}")
        if not claim.get("cannot_imply") or not claim.get("statement") or not claim.get("source_refs"):
            errors.append(f"missing statement/sources/boundary: {key}")
        for ref in claim.get("source_refs", []):
            if ref not in source_ids:
                errors.append(f"unknown source {ref} in {key}")
        for dep in claim.get("depends_on", []):
            if dep not in graph:
                errors.append(f"unknown dependency {dep} in {key}")
            else:
                graph[key].append(dep)
    for edge in data.get("dependencies", []):
        start, end = edge["from_id"], edge["to_id"]
        if start not in graph or end not in graph:
            errors.append("unknown edge endpoint")
        else:
            graph[end].append(start)
    active, done = set(), set()
    def visit(node: str) -> None:
        if node in active:
            raise ValueError(f"cyclic dependency at {node}")
        if node in done:
            return
        active.add(node)
        for other in graph[node]:
            visit(other)
        active.remove(node)
        done.add(node)
    for node in graph:
        visit(node)
    bib = (directory / "references.bib").read_text(encoding="utf-8")
    bib_ids = re.findall(r"@\w+\{([^,]+),", bib)
    if set(bib_ids) != set(source_ids) or len(bib_ids) != len(source_ids):
        errors.append("BibTeX/source ID mismatch")
    depth = 0
    for char in bib:
        depth += (char == "{") - (char == "}")
        if depth < 0:
            errors.append("unbalanced BibTeX braces")
            break
    if depth:
        errors.append("unbalanced BibTeX braces")
    for page in directory.glob("*.md"):
        text = page.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            if not (page.parent / target.split("#", 1)[0]).is_file():
                errors.append(f"broken local link {page.name}: {target}")
    return {
        "ok": not errors,
        "scope": "documentation_structure_only",
        "mathematical_truth_verified": False,
        "claims": len(claim_ids), "sources": len(source_ids),
        "errors": errors,
        "artifact_sha256": {
            name: hashlib.sha256((directory/name).read_bytes()).hexdigest()
            for name in sorted(EXPECTED) if (directory/name).is_file()
        },
    }

def main() -> int:
    try:
        result = check(Path(__file__).resolve().parent)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = {"ok": False, "scope": "documentation_structure_only",
                  "mathematical_truth_verified": False, "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    sys.exit(main())
