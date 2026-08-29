#!/usr/bin/env python3
"""Deterministic checks for the ideal aligned off-line pair model.

Assumptions checked here:
- ideal box taper on a centered interval;
- one reflection pair with the same real clock coordinate;
- normalized horizontal depth a = (beta - 1/2) L;
- c=2 rank-trace certificate.

The script does not claim that every zeta pair is aligned to the sampling clock,
or that the ideal calculation transfers without loss to the smooth finite-frame
construction used in Zeta23.
"""

from __future__ import annotations

import argparse
import math

import numpy as np


def sinhc(value: float) -> float:
    if abs(value) < 1e-8:
        square = value * value
        return 1.0 + square / 6.0 + square * square / 120.0
    return math.sinh(value) / value


def pair_eigenvalues(depth: float) -> tuple[float, float]:
    """Positive and negative eigenvalues of the normalized ideal pair block."""
    scale = sinhc(depth)
    return scale + 1.0, -(scale - 1.0)


def pair_defect(depth: float) -> float:
    """Exact c=2 defect: 2 * (sinhc(depth)^2 - 1)."""
    scale = sinhc(depth)
    return 2.0 * (scale * scale - 1.0)


def run(max_depth: float, grid: int, lam: float) -> None:
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

    tolerance = 3e-10
    if worst_eigenvalue_identity > tolerance:
        raise AssertionError(worst_eigenvalue_identity)
    if worst_depth_violation > tolerance:
        raise AssertionError(worst_depth_violation)
    if worst_scale_violation > tolerance:
        raise AssertionError(worst_scale_violation)
    if worst_defect_violation > tolerance:
        raise AssertionError(worst_defect_violation)

    print("PASS ideal aligned off-line pair depth model")
    print(f"  grid={grid}; max_depth={max_depth}; lambda={lam}")
    print("  eigenvalues: sinhc(a)+1 and -(sinhc(a)-1)")
    print("  exact c=2 defect: 2*(sinhc(a)^2-1)")
    print("  lower bound: defect >= (2/3)*a^2")
    print("  restriction: defect(lambda*a) <= lambda^2*defect(a)")
    print(f"  max checked violation={max(worst_depth_violation, worst_scale_violation, worst_defect_violation):.3e}")
    print("BOUNDARY: ideal aligned pair calculation only; no unconditional zeta conclusion.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-depth", type=float, default=5.0)
    parser.add_argument("--grid", type=int, default=10001)
    parser.add_argument("--lambda", dest="lam", type=float, default=0.75)
    args = parser.parse_args()
    run(args.max_depth, args.grid, args.lam)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
