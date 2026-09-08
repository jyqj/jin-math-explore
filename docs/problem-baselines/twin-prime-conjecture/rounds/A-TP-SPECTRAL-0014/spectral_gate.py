#!/usr/bin/env python3
"""Exact finite-measure projection certificates, not prime-gap verification."""
from __future__ import annotations
import argparse
from fractions import Fraction as Q
from itertools import product
from math import comb, prod
from pathlib import Path
import json

INPUTS = {
    "schema": "twin-spectral-input/v1", "attempt": "A-TP-SPECTRAL-0014",
    "k": 40, "rho": "2624989/10000000", "gamma": "2742997/10000000",
    "mesh": "2742997/258046918656", "cap_cells": 68225,
    "I_upper": "23685317890/1000000000000000000000000",
    "J_lower": "90248755123/1000000000000000000000000",
    "annulus_amplification": "516335400854406779784975039/381184015251729692278295039",
    "coupled_cutoff": "9/40", "mass_upper": "3/2", "spectral_tangent": 2,
    "a_h": "2479900401/2500000000", "b_h": "-843183/1000000000",
    "input_brackets_independently_verified": False
}


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def encode(value):
    if isinstance(value, Q):
        return str(value)
    if isinstance(value, dict):
        return {str(k): encode(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [encode(v) for v in value]
    return value


def margin_certificate(inp: dict) -> dict:
    need(inp == INPUTS, "fixed input identity changed")
    k = inp["k"]; rho = Q(inp["rho"]); T = Q(inp["mass_upper"])
    I = Q(inp["I_upper"]); J = Q(inp["J_lower"])
    zeta = inp["cap_cells"] * Q(inp["mesh"])
    harmonic5 = sum((Q(1, j) for j in range(1, 6)), Q(0))
    log10_lower = 2 * sum((Q(9, 11) ** (2*j+1) / (2*j+1) for j in range(7)), Q(0))
    need(log10_lower > harmonic5, "Euler constant upper witness")
    need(Q(1, 2) < zeta < Q(3, 4), "ambient cap bounds")
    kappa = 2 * rho*rho / Q(inp["coupled_cutoff"])**2
    adaptive_floor = 8 * rho*rho
    need(kappa*zeta > rho and adaptive_floor*zeta > rho, "penalty floor")
    lossless = rho*J-I
    lower = rho*(4*J-6*T*I) / (k*(k-1))
    amplification = Q(inp["annulus_amplification"])
    need(lower > Q(637,125)*lossless > 0, "strict finite feasibility exclusion")
    threshold = (k*(k-1)-6*T*rho) / (rho*(k*(k-1)-4))
    robust_threshold = (k*(k-1)-6*T*amplification*rho) / (rho*(k*(k-1)-4*amplification))
    S = Q(inp["gamma"])/rho
    pair_at_endpoints = [(4*t*J-6*t*t*I)/(k*(k-1)) for t in (zeta,2*zeta)]
    pair_uniform = min(pair_at_endpoints)
    correction_lower = 2*pair_uniform/(S*S)
    need(correction_lower/I > Q(927,100000), "nontrivial trace-null perturbation cost")
    return {
        "outer_radius": S, "pair_norm_lower_with_mass_interval": pair_uniform,
        "supported_trace_null_distance_lower": correction_lower,
        "supported_trace_null_relative_squared_distance_lower": correction_lower/I,
        "ambient_cap": zeta, "harmonic5": harmonic5, "log10_lower_7_terms": log10_lower,
        "log_gap": log10_lower-harmonic5, "mass_lower_strict": zeta, "mass_upper_strict": T,
        "coupled_penalty": kappa, "adaptive_penalty_lower_strict": adaptive_floor,
        "adaptive_floor_times_cap_minus_rho": adaptive_floor*zeta-rho,
        "signed_weights": [Q(1), Q(inp["a_h"])+Q(inp["b_h"]), Q(inp["b_h"])],
        "cost_lower": lower, "lossless_frozen_margin": lossless,
        "cost_over_I_upper": lower/I, "margin_over_I_upper": lossless/I,
        "cost_to_margin_ratio": lower/lossless, "gap_above_five_margins": lower-5*lossless,
        "amplified_cost_lower": amplification*lower,
        "necessary_actual_J_over_I": threshold,
        "necessary_actual_J_over_I_with_annulus_factor": robust_threshold,
        "frozen_J_lower_over_I_upper": J/I,
        "unknown_true_margin_has_been_upper_bounded": False,
        "source_brackets_are_premises": True
    }


def orbit_forms(k: int, p: Q, mass: Q, values: list[Q]) -> dict:
    need(k >= 2 and 0 < p < 1 and mass > 0 and len(values) == k+1, "orbit domain")
    def integrate(n, f):
        return sum((comb(n, j)*p**j*(1-p)**(n-j)*f(j) for j in range(n+1)), Q(0))
    I = mass**k * integrate(k, lambda j: values[j]**2)
    J = k*mass**(k+1)*integrate(k-1, lambda j: ((1-p)*values[j]+p*values[j+1])**2)
    K = mass**(k+2)*integrate(k-2, lambda j:
        ((1-p)**2*values[j]+2*p*(1-p)*values[j+1]+p*p*values[j+2])**2)
    lower = (4*mass*J-6*mass*mass*I)/(k*(k-1))
    need(K >= lower, "symmetric pair inequality")
    return {"I": I, "J_all": J, "K_pair": K, "pair_lower": lower}


def projected_energies(k: int, p: Q, values: dict[tuple[int, ...], Q]) -> tuple[list[Q], list[Q]]:
    """All normalized conditional projections, then Boolean Mobius inversion."""
    points = list(product((0, 1), repeat=k))
    need(set(points) == set(values) and 0 < p < 1, "cube input coverage")
    weights = {x: p**sum(x)*(1-p)**(k-sum(x)) for x in points}
    projected = []
    for mask in range(1 << k):
        totals, masses = {}, {}
        for x in points:
            key = tuple(x[j] for j in range(k) if not (mask >> j) & 1)
            totals[key] = totals.get(key, Q(0)) + weights[x]*values[x]
            masses[key] = masses.get(key, Q(0)) + weights[x]
        projected.append(sum((totals[y]**2/masses[y] for y in totals), Q(0)))
    energies = projected[:]
    for j in range(k):
        for mask in range(1 << k):
            if not (mask >> j) & 1:
                energies[mask] -= energies[mask | (1 << j)]
    need(min(energies) >= 0, "orthogonal energies must be nonnegative")
    need(sum(energies) == projected[0], "energy partition")
    return projected, energies


def projection_certificate(weights: list[Q], values: list[Q]) -> dict:
    need(len(weights) == len(values) and all(w > 0 for w in weights), "fibre input")
    n = sum(weights, Q(0)); trace = sum((w*v for w, v in zip(weights, values)), Q(0))
    if not weights:
        return {"capacity": Q(0), "trace": Q(0), "correction": Q(0), "distance_squared": Q(0), "projected": []}
    correction = trace/n
    flat = [v-correction for v in values]
    need(sum((w*v for w, v in zip(weights, flat)), Q(0)) == 0, "null trace")
    need(sum((w*(v-f)**2 for w, v, f in zip(weights, values, flat)), Q(0)) == trace*trace/n, "projection distance")
    return {"capacity": n, "trace": trace, "correction": correction,
            "distance_squared": trace*trace/n, "projected": flat}


def build(inp: dict) -> tuple[dict, dict]:
    constants = margin_certificate(inp)
    k = inp["k"]; mass = Q(3, 2)
    # Walsh sums with exactly 2 or 3 constant coordinates saturate the tangent.
    E = {2: comb(k, 2), 3: comb(k, 3)}
    I = sum(E.values()); first = sum(s*e for s, e in E.items()); second = sum(s*(s-1)*e for s, e in E.items())
    need(second == 4*first-6*I, "sharp spectral model")
    sharp = {"k": k, "mass": mass, "level_energies": E, "J_over_I": mass*Q(first, I),
             "K_pair_over_I": mass*mass*Q(second, k*(k-1)*I), "tangent_equality": True}
    p = Q(1, 3); cube = {x: Q(-1 if x[0] == 0 else 2) for x in product((0, 1), repeat=4)}
    norms, energies = projected_energies(4, p, cube)
    need(norms[3] == 0, "asymmetric chosen pair must vanish")
    first = sum(norms[1 << j] for j in range(4))
    second = sum(norms[(1 << i)|(1 << j)] for i in range(4) for j in range(i+1, 4))
    asymmetric = {"k": 4, "p": p, "mass": mass, "J_over_I": mass*first/norms[0],
                  "chosen_K_over_I": mass*mass*norms[3]/norms[0],
                  "average_K_over_I": mass*mass*second/(6*norms[0]),
                  "false_symmetric_pair_lower_over_I": (4*mass*mass*first/norms[0]-6*mass*mass)/12}
    cert = {"schema": "twin-spectral-certificate/v1", "constants": constants,
            "spectrum40": [[s, (s-2)*(s-3)] for s in range(41)], "sharp_model": sharp,
            "asymmetry_counterexample": asymmetric,
            "supported_projection_example": projection_certificate([Q(1,3), Q(2,5), Q(3,7)], [Q(-2,3), Q(5,7), Q(-11,13)]),
            "zero_fibre": projection_certificate([], []),
            "deletion_noncommutation": {"values": [1,-1], "weights": ["1/2","1/2"],
                                       "trace_before": "0", "trace_after_keep_first": "1/2"}}
    res = {"schema": "twin-spectral-results/v1", "status": "conditional_solver_candidate_and_exact_check",
           "cost_lower": constants["cost_lower"], "lossless_frozen_margin": constants["lossless_frozen_margin"],
           "ratio": constants["cost_to_margin_ratio"], "ratio_exceeds_five": True,
           "excluded": "closing the un-restored symmetric-trace sufficient test with the frozen I+/J- certificate",
           "all_helpers_and_young_parameters": "within 0<=capacity<=ambient mass and penalty>=rho/ambient mass",
           "actual_true_margin_upper_bound": False, "input_brackets_independently_verified": False,
           "independently_verified": False, "new_prime_gap_bound": False,
           "cannot_imply": ["a lower bound on actual prime gaps", "failure of all asymmetric trials",
                            "failure after obtaining a stronger true margin", "an independent receipt or twin-prime proof"]}
    return encode(cert), encode(res)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    cert, results = build(INPUTS)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, value in (("inputs.json", INPUTS), ("certificates.json", cert), ("results.json", results)):
        (args.output_dir/name).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"ok": True, "cost_lower": results["cost_lower"], "margin": results["lossless_frozen_margin"],
                      "ratio": results["ratio"], "conditional": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
