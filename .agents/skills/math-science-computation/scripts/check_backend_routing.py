#!/usr/bin/env python3
"""Validate the backend routing catalog and promoted evidence links."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_COLUMNS = (
    "route_id",
    "task_class",
    "conditions",
    "primary",
    "fallback",
    "decision_metrics",
    "evidence_status",
    "evidence_ids",
)
VALID_STATUSES = {"heuristic", "benchmarked"}


def parse_catalog(text: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    header_index = next(
        (i for i, line in enumerate(lines) if line.strip().startswith("| route_id |")),
        None,
    )
    if header_index is None or header_index + 1 >= len(lines):
        raise ValueError("routing catalog table is missing")

    headers = [cell.strip() for cell in lines[header_index].strip().strip("|").split("|")]
    if tuple(headers) != REQUIRED_COLUMNS:
        raise ValueError(f"routing catalog columns must be: {', '.join(REQUIRED_COLUMNS)}")

    rows: list[dict[str, str]] = []
    for line in lines[header_index + 2 :]:
        if not line.lstrip().startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != len(headers):
            raise ValueError(f"catalog row has {len(cells)} cells instead of {len(headers)}: {line}")
        rows.append(dict(zip(headers, cells)))
    if not rows:
        raise ValueError("routing catalog has no route records")
    return rows


def evidence_ids(text: str) -> set[str]:
    return set(re.findall(r"(?m)^- `evidence_id`:\s*`([^`]+)`\s*$", text))


def validate(routing_text: str, evidence_text: str) -> list[str]:
    errors: list[str] = []
    try:
        rows = parse_catalog(routing_text)
    except ValueError as exc:
        return [str(exc)]

    known_evidence = evidence_ids(evidence_text)
    seen: set[str] = set()
    for row in rows:
        route_id = row["route_id"]
        if not route_id:
            errors.append("route_id must not be empty")
            continue
        if route_id in seen:
            errors.append(f"duplicate route_id: {route_id}")
        seen.add(route_id)

        for field in REQUIRED_COLUMNS[1:6]:
            if not row[field]:
                errors.append(f"{route_id}: {field} must not be empty")

        status = row["evidence_status"]
        ids = [item.strip() for item in row["evidence_ids"].split(",") if item.strip()]
        if status not in VALID_STATUSES:
            errors.append(f"{route_id}: invalid evidence_status {status!r}")
        elif status == "heuristic" and ids != ["none"]:
            errors.append(f"{route_id}: heuristic routes must use evidence_ids 'none'")
        elif status == "benchmarked":
            if not ids or ids == ["none"]:
                errors.append(f"{route_id}: benchmarked route must cite evidence_ids")
            for item in ids:
                if item not in known_evidence:
                    errors.append(f"{route_id}: unknown evidence_id {item}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--routing-file", type=Path, required=True)
    parser.add_argument("--evidence-file", type=Path, required=True)
    args = parser.parse_args()

    errors = validate(
        args.routing_file.read_text(encoding="utf-8"),
        args.evidence_file.read_text(encoding="utf-8"),
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Backend routing policy is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
