#!/usr/bin/env python3
"""Deterministic structural checks for A-GB-L35-0001 CP-0003.

PASS means package consistency only.  Mathematical truth, the Fouvry extension,
the Li-Liu theorem and binary Goldbach are not verified by this script.
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
        require(value["checkpoint"] == "CP-0003", "checkpoint mismatch")
    require(source["baseline_commit"] == BASELINE, "source baseline mismatch")
    require(matrix["baseline_commit"] == BASELINE, "matrix baseline mismatch")
    require(attempt["base_commit"] == BASELINE, "attempt baseline mismatch")

    paper = source["paper"]
    require(paper["identifier"] == "arXiv:2606.05224v2",
            "wrong Li-Liu source version")
    require(paper["silent_version_substitution_allowed"] is False,
            "silent source substitution must be forbidden")

    primary = source["primary_mean_value_source"]
    require(primary["doi"] == "10.24033/asens.1547",
            "wrong primary mean-value source")
    normalization = primary["normalization"]
    require(normalization["source_scale"] ==
            "x=4*M*N for supports [M,2M] and [N,2N]",
            "primary scale normalization missing")

    catalog = matrix["requirement_catalog"]
    by_id = {item["id"]: item for item in catalog}
    require(set(by_id) == REQUIRED_REQUIREMENTS, "requirement set differs")
    require(len(by_id) == len(catalog), "duplicate requirement")
    for item in catalog:
        require(item["status"] in ALLOWED_STATUS,
                f"{item['id']}: invalid status")
        if item["status"] != "PASS":
            require(bool(item.get("next_action")),
                    f"{item['id']}: missing next_action")

    require(by_id["condition_3_2"]["status"] == "PASS",
            "prime-beta condition (3.2) not frozen")
    require(by_id["small_prime_exclusion"]["status"] == "PASS",
            "roughness condition not frozen")
    require(by_id["nu_range"]["status"] == "PASS",
            "nu range split not frozen")
    require(by_id["residue_scale_uniformity"]["status"] == "PASS",
            "fixed-multiple residue bridge not frozen")
    require(by_id["sieve_coefficient_transfer"]["status"] == "PASS",
            "coefficient bridge not frozen")

    bridge = matrix["normalization_and_residue_bridge"]
    require(bridge["status"] ==
            "DERIVED_PASS_AWAITING_INDEPENDENT_VERIFICATION",
            "residue bridge authority boundary differs")
    require(bridge["fouvry_scale"] == "x=4*M*P",
            "Fouvry cell scale differs")
    require(bridge["application"].find("epsilon0^-1") >= 0,
            "fixed-multiple application missing")

    transition = matrix["nu_transition"]
    require(transition["status"] == "DERIVED_PASS_WITH_ERROR_HANDOFF",
            "nu transition status differs")
    require(transition["handoff"] == "A-GB-ERR-0001",
            "top-slice error handoff missing")

    compiler = matrix["g9_box_compiler"]
    require(compiler["status"] == "INTERIOR_PASS_BOUNDARY_OPEN",
            "G9 compiler status differs")
    require(compiler["order_bound"] == "beta<=1, alpha<=tau_2",
            "G9 order bound differs")
    require(bool(compiler["boundary_open"]),
            "boundary obligations unexpectedly absent")

    calls = matrix["calls"]
    call_ids = [item["call_id"] for item in calls]
    require(set(call_ids) == REQUIRED_CALLS and len(call_ids) == 3,
            "call inventory differs")
    require(next(c for c in calls if c["target"] == "G9")["status"] == "PARTIAL",
            "G9 should be partial at CP-0003")
    require(all(c["status"] == "INCOMPLETE"
                for c in calls if c["target"] in {"G11", "G12"}),
            "G11/G12 should remain incomplete")

    findings = {item["id"] for item in matrix["findings"]}
    require({"F-L35-011", "F-L35-012", "F-L35-013",
             "F-L35-014", "F-L35-015"} <= findings,
            "CP-0003 findings incomplete")

    nu = Fraction(1, 10)
    theta = Fraction(5) * (1 - nu) / 9
    require(Fraction(4) / theta == 8,
            "coefficient boundary identity failed")
    require(Fraction(4, 53) < Fraction(1, 10),
            "low-p1 interval is empty")

    require(matrix["provisional_verdict"] == "INCONCLUSIVE",
            "open checkpoint must remain INCONCLUSIVE")
    require(attempt["verdict"] == "INCONCLUSIVE",
            "attempt verdict must remain INCONCLUSIVE")
    require(attempt["authority"]["mathematical_claim_upgrade"] is False,
            "checkpoint must not upgrade authority")
    require(attempt["authority"]["independent_verification"] is False,
            "checkpoint must not claim independent verification")

    for name, expected in attempt["artifact_sha256"].items():
        require(name != "attempt.json", "self hash is forbidden")
        require(sha256(name) == expected,
                f"artifact hash mismatch: {name}")

    print(
        "PASS: A-GB-L35-0001 CP-0003 is structurally consistent; "
        "mathematical truth was not assessed."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
