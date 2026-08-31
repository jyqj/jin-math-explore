#!/usr/bin/env python3
"""Deterministic structural checks for A-GB-L35-0001 CP-0002.

A PASS establishes package consistency only. It does not verify Lemma 3.5,
the Li-Liu proof, or the binary Goldbach conjecture.
"""
from __future__ import annotations

import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
ATTEMPT_ID = "A-GB-L35-0001"
BASELINE = "70484b065fc3b6a64f06955a5f9c895531750891"
REQUIRED_CALLS = {
    "CALL-G9-L35-LOW-P1",
    "CALL-G11-L35-LOW-P1",
    "CALL-G12-L35-LOW-P1",
}
REQUIRED_REQUIREMENTS = {
    "dyadic_support",
    "order_k_bounds",
    "condition_3_2",
    "small_prime_exclusion",
    "local_X_definition",
    "nu_definition",
    "nu_range",
    "well_factorable_weight",
    "level_Q_match",
    "residue_scale_uniformity",
    "error_uniformity",
    "block_summability",
    "sieve_coefficient_transfer",
}
ALLOWED_STATUS = {"PASS", "PARTIAL", "OPEN", "FAIL", "NA"}


def load(name: str) -> Any:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def sha256(name: str) -> str:
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    source = load("source-lock.json")
    matrix = load("call-matrix.json")
    attempt = load("attempt.json")

    for value in (source, matrix, attempt):
        require(value["attempt_id"] == ATTEMPT_ID, "attempt_id mismatch")
    require(source["baseline_commit"] == BASELINE, "source baseline mismatch")
    require(matrix["baseline_commit"] == BASELINE, "matrix baseline mismatch")
    require(attempt["base_commit"] == BASELINE, "attempt baseline mismatch")
    require(source["paper"]["identifier"] == "arXiv:2606.05224v2",
            "wrong source version")
    require(source["paper"]["silent_version_substitution_allowed"] is False,
            "silent source substitution must be forbidden")

    catalog = matrix["requirement_catalog"]
    requirement_ids = [item["id"] for item in catalog]
    require(len(requirement_ids) == len(set(requirement_ids)),
            "duplicate requirement")
    require(set(requirement_ids) == REQUIRED_REQUIREMENTS,
            "requirement set differs")
    has_nonpass = False
    for item in catalog:
        require(item["status"] in ALLOWED_STATUS,
                f"{item['id']}: invalid status")
        if item["status"] != "PASS":
            has_nonpass = True
            require(bool(item.get("next_action")),
                    f"{item['id']}: missing next_action")

    calls = matrix["calls"]
    call_ids = [item["call_id"] for item in calls]
    require(len(call_ids) == len(set(call_ids)), "duplicate call ID")
    require(set(call_ids) == REQUIRED_CALLS, "call set differs")
    for call in calls:
        require(call["status"] == "INCOMPLETE",
                f"{call['call_id']}: initial checkpoint must be incomplete")
        require(set(call["requirements_applied"]) == REQUIRED_REQUIREMENTS,
                f"{call['call_id']}: requirement coverage differs")
        require(bool(call["call_specific_open_point"]),
                f"{call['call_id']}: missing open point")

    require(has_nonpass, "checkpoint unexpectedly has no open work")
    by_id = {item["id"]: item for item in catalog}
    require(by_id["condition_3_2"]["status"] == "PASS",
            "prime-beta condition (3.2) was not frozen")
    require(by_id["sieve_coefficient_transfer"]["status"] == "PASS",
            "coefficient bridge was not frozen")
    findings = {item["id"] for item in matrix["findings"]}
    require({"F-L35-007", "F-L35-008", "F-L35-009", "F-L35-010"} <= findings,
            "CP-0002 findings are incomplete")
    require(matrix["g9_reconstruction"]["status"] == "PARTIAL",
            "G9 reconstruction status differs")
    require(matrix["provisional_verdict"] == "INCONCLUSIVE",
            "open checkpoint must remain INCONCLUSIVE")
    require(attempt["verdict"] == "INCONCLUSIVE",
            "attempt verdict must remain INCONCLUSIVE")
    require(attempt["authority"]["mathematical_claim_upgrade"] is False,
            "checkpoint must not upgrade authority")

    nu = Fraction(1, 10)
    theta = Fraction(5) * (1 - nu) / 9
    require(Fraction(4) / theta == 8,
            "coefficient boundary identity failed")
    require(matrix["coefficient_check"]["boundary_value"] == "8",
            "stored boundary value mismatch")

    for name, expected in attempt["artifact_sha256"].items():
        require(name != "attempt.json", "self hash is forbidden")
        require(sha256(name) == expected, f"artifact hash mismatch: {name}")

    print(
        "PASS: A-GB-L35-0001 CP-0002 is structurally consistent; "
        "mathematical truth was not assessed."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
