#!/usr/bin/env python3
"""Checks for the period-six confluent clock angle theorem.

The script verifies the determinant formulas against direct 6x6 matrices,
checks the exact a=0 angle constants, and scans principal angles/singular values
for regression. It is not a proof about arbitrary stationary laws or zeta.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import math

import numpy as np


def fiber_matrix(a: float, x: float, pair: int, empty: int, normalized: bool) -> np.ndarray:
    residues = [r for r in range(6) if r not in (pair, empty)]
    points = x + np.arange(6, dtype=float) / 6.0
    columns = [np.exp(2j * math.pi * r * points) for r in residues]
    columns.append(np.exp(2j * math.pi * pair * points) * np.cosh(a * points))
    if abs(a) < 1.0e-14:
        negative = np.exp(2j * math.pi * pair * points) * points
    else:
        negative = np.exp(2j * math.pi * pair * points) * np.sinh(a * points)
        if normalized:
            negative = negative / a
    columns.append(negative)
    return np.column_stack(columns)


def delta_sq_formula(a: float, q: int) -> float:
    r = math.exp(a / 6.0)
    minus = r * r - r + 1.0
    plus = r * r + r + 1.0
    if q in (1, 5):
        return (
            (r - 1.0) ** 2
            * (r + 1.0) ** 6
            * minus**2
            * plus**4
            / (4.0 * r**10)
        )
    if q in (2, 4):
        return (
            3.0
            * (r - 1.0) ** 2
            * (r + 1.0) ** 6
            * minus**4
            * plus**2
            / (4.0 * r**10)
        )
    if q == 3:
        return (
            (r - 1.0) ** 2
            * (r + 1.0) ** 2
            * minus**4
            * plus**4
            / r**10
        )
    raise ValueError("q must be nonzero modulo 6")


def principal_angle_sq(matrix: np.ndarray) -> float:
    positive = matrix[:, :5]
    negative = matrix[:, 5]
    coefficients, *_ = np.linalg.lstsq(positive, negative, rcond=None)
    residual = negative - positive @ coefficients
    return float(np.vdot(residual, residual).real / np.vdot(negative, negative).real)


def check_determinant_formulas(samples: int) -> None:
    rng = np.random.default_rng(20260831)
    maximum_relative_error = 0.0
    maximum_phase_magnitude_variation = 0.0

    for _ in range(samples):
        a = float(rng.uniform(0.02, 6.0))
        pair = int(rng.integers(0, 6))
        empty = int(rng.integers(0, 5))
        if empty >= pair:
            empty += 1
        q = (empty - pair) % 6
        predicted_sq = 36.0 * delta_sq_formula(a, q)

        magnitudes = []
        for x in np.linspace(-0.5, -1.0 / 3.0, 11, endpoint=False):
            determinant = np.linalg.det(fiber_matrix(a, float(x), pair, empty, False))
            observed_sq = abs(determinant) ** 2
            relative = abs(observed_sq - predicted_sq) / max(1.0, predicted_sq)
            maximum_relative_error = max(maximum_relative_error, relative)
            magnitudes.append(abs(determinant))
        maximum_phase_magnitude_variation = max(
            maximum_phase_magnitude_variation, max(magnitudes) - min(magnitudes)
        )

    if maximum_relative_error > 2.0e-10:
        raise AssertionError(maximum_relative_error)
    if maximum_phase_magnitude_variation > 2.0e-10:
        raise AssertionError(maximum_phase_magnitude_variation)

    print("PASS exact determinant formulas and phase-independent magnitude")
    print(f"  random parameter samples={samples}")
    print(f"  maximum relative squared-determinant error={maximum_relative_error:.3e}")
    print(f"  maximum magnitude variation across fiber phase={maximum_phase_magnitude_variation:.3e}")


def check_confluent_limits() -> None:
    expected = {
        1: 36.0,
        2: 12.0 * math.sqrt(3.0),
        3: 18.0,
        4: 12.0 * math.sqrt(3.0),
        5: 36.0,
    }
    a = 1.0e-6
    for q, target in expected.items():
        observed = 6.0 * math.sqrt(delta_sq_formula(a, q)) / a
        if abs(observed - target) > 2.0e-4:
            raise AssertionError((q, observed, target))
    print("PASS normalized confluent determinant limits")
    print("  q=1/5 -> 36; q=2/4 -> 12*sqrt(3); q=3 -> 18")


def check_exact_shallow_angles() -> None:
    root_distances = {
        1: Fraction(1, 1),
        2: Fraction(3, 1),
        3: Fraction(4, 1),
        4: Fraction(3, 1),
        5: Fraction(1, 1),
    }
    maximum_norm = Fraction(19, 36)
    exact_bounds = {
        q: Fraction(1, 6) / distance / maximum_norm
        for q, distance in root_distances.items()
    }
    assert exact_bounds[1] == Fraction(6, 19)
    assert exact_bounds[2] == Fraction(2, 19)
    assert exact_bounds[3] == Fraction(3, 38)
    assert min(exact_bounds.values()) == Fraction(3, 38)

    scanned = math.inf
    argmin = None
    for pair in range(6):
        for empty in range(6):
            if pair == empty:
                continue
            for x in np.linspace(-0.5, -1.0 / 3.0, 1001, endpoint=False):
                eta = principal_angle_sq(fiber_matrix(0.0, float(x), pair, empty, True))
                if eta < scanned:
                    scanned = eta
                    argmin = (pair, empty, float(x))
    if scanned < float(Fraction(3, 38)) - 2.0e-11:
        raise AssertionError((scanned, argmin))

    print("PASS exact a=0 arrangement-free principal-angle bound")
    print("  adjacent pair/empty: 6/19")
    print("  distance-two pair/empty: 2/19")
    print("  opposite pair/empty: 3/38 (global minimum)")
    print(f"  scanned minimum={scanned:.12f} at {argmin}")


def check_bounded_depth_regression(max_depth: float, depth_steps: int, phase_steps: int) -> None:
    minimum_angle = math.inf
    minimum_singular = math.inf
    argmin_angle = None
    argmin_singular = None

    depths = np.linspace(0.0, max_depth, depth_steps)
    phases = np.linspace(-0.5, -1.0 / 3.0, phase_steps, endpoint=False)
    for a in depths:
        for pair in range(6):
            for empty in range(6):
                if pair == empty:
                    continue
                for x in phases:
                    matrix = fiber_matrix(float(a), float(x), pair, empty, True)
                    angle = principal_angle_sq(matrix)
                    singular = float(np.linalg.svd(matrix, compute_uv=False)[-1])
                    if angle < minimum_angle:
                        minimum_angle = angle
                        argmin_angle = (float(a), pair, empty, float(x))
                    if singular < minimum_singular:
                        minimum_singular = singular
                        argmin_singular = (float(a), pair, empty, float(x))

    if minimum_angle <= 0.0 or minimum_singular <= 0.0:
        raise AssertionError((minimum_angle, minimum_singular))

    print("PASS bounded-depth fiber regression scan")
    print(f"  depth range=[0,{max_depth}]")
    print(f"  minimum principal-angle square={minimum_angle:.12f} at {argmin_angle}")
    print(f"  minimum normalized singular value={minimum_singular:.12f} at {argmin_singular}")


def check_edge_fraction() -> None:
    for length, width in ((100.0, 1.0), (300.0, 2.0), (1000.0, 3.0)):
        phases = np.linspace(-0.5, -1.0 / 3.0, 500_000, endpoint=False)
        bad = np.zeros_like(phases, dtype=bool)
        for j in range(6):
            point = phases + j / 6.0
            bad |= np.abs(point) > 0.5 - width / length
        observed_relative = float(np.mean(bad))
        upper = min(1.0, 12.0 * width / length)
        if observed_relative > upper + 2.0e-5:
            raise AssertionError((observed_relative, upper))
    print("PASS fixed-width exceptional-fiber fraction")
    print("  relative bad phase fraction <= 12w/L")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--max-depth", type=float, default=4.0)
    parser.add_argument("--depth-steps", type=int, default=17)
    parser.add_argument("--phase-steps", type=int, default=61)
    args = parser.parse_args()

    check_determinant_formulas(args.samples)
    check_confluent_limits()
    check_exact_shallow_angles()
    check_bounded_depth_regression(args.max_depth, args.depth_steps, args.phase_steps)
    check_edge_fraction()
    print(
        "BOUNDARY: period-six ideal/confluent fibers and edge-measure regression only; "
        "no theorem for arbitrary stationary laws or actual zeta zeros is proved."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
