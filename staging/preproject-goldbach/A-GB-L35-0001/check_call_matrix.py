#!/usr/bin/env python3
"""Deterministic structural checks for A-GB-L35-0001 CP-0004.

PASS establishes frozen-package consistency only.  It does not independently
verify the solver lemmas, the Li-Liu theorem, or binary Goldbach.
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
        require(value["checkpoint"] == "CP-0004", "checkpoint mismatch")
    require(source["baseline_commit"] == BASELINE, "source baseline mismatch")
    require(matrix["baseline_commit"] == BASELINE, "matrix baseline mismatch")
    require(attempt["base_commit"] == BASELINE, "attempt baseline mismatch")

    require(source["paper"]["identifier"] == "arXiv:2606.05224v2",
            "wrong Li-Liu source version")
    require(source["paper"]["silent_version_substitution_allowed"] is False,
            "silent source substitution must be forbidden")
    primary = source["primary_mean_value_source"]
    require(primary["doi"] == "10.24033/asens.1547",
            "wrong primary mean-value source")
    require(primary["normalization"]["source_scale"] ==
            "x=4*M*N for supports [M,2M] and [N,2N]",
            "primary scale normalization missing")

    catalog = matrix["requirement_catalog"]
    by_id = {item["id"]: item for item in catalog}
    require(len(by_id) == len(catalog), "duplicate requirement")
    require(set(by_id) == REQUIRED_REQUIREMENTS, "requirement set differs")
    require(all(item["status"] == "PASS" for item in catalog),
            "frozen solver candidate has a non-PASS requirement")

    calls = matrix["calls"]
    call_ids = [item["call_id"] for item in calls]
    require(set(call_ids) == REQUIRED_CALLS and len(call_ids) == 3,
            "call inventory differs")
    require(all(item["status"] == "SOLVER_PASS" for item in calls),
            "not every call has a solver PASS")

    boundary = matrix["boundary_compiler"]
    require(boundary["status"] == "SOLVER_PASS",
            "boundary compiler not frozen")
    require(boundary["mesh"]["fixed_J"] == "J>=4", "mesh threshold differs")
    require("A-GB-ERR-0001" in
            (by_id["nu_range"].get("handoff", ""),
             by_id["sieve_coefficient_transfer"].get("handoff", "")),
            "common-error handoff missing")

    binding = matrix["sieve_binding"]
    require(binding["status"] == "SOLVER_PASS",
            "sieve binding not frozen")
    require(binding["remainder"]["identity"] ==
            "r_C(q)=E_C(q)-H_C(q)",
            "remainder identity differs")
    require(binding["handoff"] ==
            "A-GB-ERR-0001",
            "coprimality correction handoff missing")

    rough = matrix["rough_residual"]
    require(rough["status"] == "SOLVER_PASS_FOR_LEMMA_3_5_INTERFACE",
            "rough residual compiler status differs")
    require(rough["alpha"] == "<=tau_4",
            "rough residual order bound differs")

    findings = {item["id"] for item in matrix["findings"]}
    require({"F-L35-016", "F-L35-017", "F-L35-018",
             "F-L35-019", "F-L35-020"} <= findings,
            "CP-0004 findings incomplete")

    nu = Fraction(1, 10)
    theta = Fraction(5) * (1 - nu) / 9
    require(Fraction(4) / theta == 8,
            "coefficient boundary identity failed")
    require(Fraction(4, 53) < nu, "low-p1 interval is empty")
    require(3 * Fraction(4, 33) + Fraction(3, 11) ==
            Fraction(7, 11), "G12 exponent sum differs")
    require(Fraction(7, 11) < 1, "G12 +1 boundary count is not power-saving")

    require(matrix["overall_status"] == "FROZEN_SOLVER_CANDIDATE",
            "matrix is not frozen")
    require(matrix["provisional_verdict"] == "PASS",
            "matrix verdict differs")
    require(attempt["status"] == "frozen_candidate",
            "attempt is not frozen")
    require(attempt["verdict"] == "PASS", "attempt verdict differs")
    require(attempt["authority"]["mathematical_claim_upgrade"] is False,
            "attempt must not upgrade authority")
    require(attempt["authority"]["project_authority_changed"] is False,
            "attempt must not alter Project authority")
    require(attempt["authority"]["independent_verification"] is False,
            "attempt must not claim independent verification")
    require(attempt["verification_required"] is True,
            "frozen candidate must require verification")

    for name, expected in attempt["artifact_sha256"].items():
        require(name != "attempt.json", "self hash is forbidden")
        require(sha256(name) == expected,
                f"artifact hash mismatch: {name}")

    print(
        "PASS: A-GB-L35-0001 CP-0004 frozen solver candidate is "
        "structurally consistent; mathematical truth was not assessed."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
