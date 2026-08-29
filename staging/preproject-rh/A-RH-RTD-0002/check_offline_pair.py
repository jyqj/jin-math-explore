#!/usr/bin/env python3
"""Deterministic checks for ideal off-line pair models.

The isolated-pair calculation assumes:
- ideal box taper on a centered interval;
- one reflection pair aligned to one real clock coordinate;
- normalized horizontal depth a = (beta - 1/2) L;
- the c=2 rank-trace certificate.

The collective countermodel is deliberately more abstract. It shows that the
aggregate rank-trace data of several hyperbolic pair blocks cannot, by itself,
control each pair's negative component: different pairs can cancel one
another's negative directions exactly.

Nothing here proves a statement about all zeta pairs or transfers the ideal
calculation without loss to the smooth finite-frame construction in Zeta23.
"""

from __future__ import annotations

import argparse
import math

import numpy as np


TOL = 3e-10


def sinhc(value: float) -> float:
    if abs(value) < 1e-8:
        square = value * value
        return 1.0 + square / 6.0 + square * square / 120.0
    return math.sinh(value) / value


def pair_eigenvalues(depth: float) -> tuple[float, float]:
    """Positive and negative eigenvalues of the normalized isolated pair block."""
    scale = sinhc(depth)
    return scale + 1.0, -(scale - 1.0)


def pair_defect(depth: float) -> float:
    """Exact isolated c=2 defect: 2 * (sinhc(depth)^2 - 1)."""
    scale = sinhc(depth)
    return 2.0 * (scale * scale - 1.0)


def check_isolated_pair(max_depth: float, grid: int, lam: float) -> None:
    if not (0.0 < lam <= 1.0):
        raise ValueError("need 0 < lambda <= 1")

    worst_depth_violation = 0.0
    worst_scale_violation = 0.0
    worst_defect_violation = 0.0
    worst_eigenvalue_identity = 0.0

    for depth in np.linspace(0.0, max_depth, grid):
        depth = float(depth)
        scale = sinhc(depth)
        short_scale = sinhc(lam * depth)
        defect = pair_defect(depth)
        short_defect = pair_defect(lam * depth)
        positive, negative = pair_eigenvalues(depth)

        worst_eigenvalue_identity = max(
            worst_eigenvalue_identity,
            abs(positive + negative - 2.0),
            abs(positive * positive + negative * negative - 2.0 * (scale * scale + 1.0)),
        )
        worst_depth_violation = max(
            worst_depth_violation,
            (2.0 / 3.0) * depth * depth - defect,
        )
        worst_scale_violation = max(
            worst_scale_violation,
            (short_scale - 1.0) - lam * lam * (scale - 1.0),
        )
        worst_defect_violation = max(
            worst_defect_violation,
            short_defect - lam * lam * defect,
        )

    if worst_eigenvalue_identity > TOL:
        raise AssertionError(worst_eigenvalue_identity)
    if worst_depth_violation > TOL:
        raise AssertionError(worst_depth_violation)
    if worst_scale_violation > TOL:
        raise AssertionError(worst_scale_violation)
    if worst_defect_violation > TOL:
        raise AssertionError(worst_defect_violation)

    print("PASS ideal aligned isolated-pair depth model")
    print(f"  grid={grid}; max_depth={max_depth}; lambda={lam}")
    print("  eigenvalues: sinhc(a)+1 and -(sinhc(a)-1)")
    print("  exact c=2 defect: 2*(sinhc(a)^2-1)")
    print("  lower bound: defect >= (2/3)*a^2")
    print("  restriction: defect(lambda*a) <= lambda^2*defect(a)")
    print(f"  max checked violation={max(worst_depth_violation, worst_scale_violation, worst_defect_violation):.3e}")


def aggregate_c2_defect(matrix: np.ndarray, budget: int) -> float:
    trace = float(np.trace(matrix).real)
    frobenius_sq = float(np.vdot(matrix, matrix).real)
    return 4.0 * budget - (4.0 * trace - frobenius_sq)


def check_collective_cancellation(max_depth: float, grid: int, lam: float) -> None:
    """Two nontrivial hyperbolic pairs can sum to 2I exactly.

    For each scale choose alpha^2=(S+1)/2 and beta^2=(S-1)/2,
    where S=sinhc(scale*depth). Pair one uses positive direction e1 and
    negative direction e2; pair two swaps them. Their sum is 2I because
    alpha^2-beta^2=1, even though beta>0 for every nonzero depth.
    """

    identity = np.eye(2)
    worst_matrix_error = 0.0
    worst_defect = 0.0
    largest_hidden_negative_mass = 0.0

    for depth in np.linspace(0.0, max_depth, grid):
        for scale_factor in (1.0, lam):
            scale = sinhc(scale_factor * float(depth))
            alpha_sq = (scale + 1.0) / 2.0
            beta_sq = (scale - 1.0) / 2.0

            pair_one = 2.0 * np.diag([alpha_sq, -beta_sq])
            pair_two = 2.0 * np.diag([-beta_sq, alpha_sq])
            aggregate = pair_one + pair_two

            worst_matrix_error = max(
                worst_matrix_error,
                float(np.linalg.norm(aggregate - 2.0 * identity, ord="fro")),
            )
            worst_defect = max(worst_defect, abs(aggregate_c2_defect(aggregate, budget=2)))
            largest_hidden_negative_mass = max(largest_hidden_negative_mass, 2.0 * beta_sq)

    if worst_matrix_error > TOL:
        raise AssertionError(worst_matrix_error)
    if worst_defect > TOL:
        raise AssertionError(worst_defect)
    if largest_hidden_negative_mass <= 0.0:
        raise AssertionError("the countermodel did not include a nonzero negative pair component")

    print("PASS collective two-pair cancellation countermodel")
    print("  Q1=2(alpha^2 e1e1* - beta^2 e2e2*)")
    print("  Q2=2(alpha^2 e2e2* - beta^2 e1e1*)")
    print("  alpha^2-beta^2=1, hence Q1+Q2=2I at both checked scales")
    print("  aggregate c=2 defect is zero despite nonzero individual negative parts")
    print(f"  largest hidden individual negative eigenvalue checked={largest_hidden_negative_mass:.6f}")
    print("  consequence: scalar per-scale trace/Frobenius data cannot recover pairwise depth")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-depth", type=float, default=5.0)
    parser.add_argument("--grid", type=int, default=10001)
    parser.add_argument("--lambda", dest="lam", type=float, default=0.75)
    args = parser.parse_args()

    check_isolated_pair(args.max_depth, args.grid, args.lam)
    check_collective_cancellation(args.max_depth, args.grid, args.lam)
    print(
        "BOUNDARY: ideal isolated and abstract aggregate pair models only; "
        "no unconditional conclusion about zeta zeros."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
