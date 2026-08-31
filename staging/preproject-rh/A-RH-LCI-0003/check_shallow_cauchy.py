#!/usr/bin/env python3
"""Deterministic checks for the arbitrary-period shallow Cauchy checkpoint.

The script verifies:
1. the exact projection matrix from shallow divided-difference pair columns
   to the missing Fourier residues;
2. the finite-period Cauchy determinant formula;
3. the phase-separated period-6m collapse of the column-average gap and
   smallest principal angle;
4. the bounded matching lower bound for the column-average gap;
5. the separated-arc low-rank approximation used in the exponential angle
   upper bound.

It does not prove a statement about actual zeta zeros.
"""

from __future__ import annotations

import argparse
import math
from typing import Iterable

import numpy as np


def normalized_dft(period: int) -> np.ndarray:
    j = np.arange(period, dtype=float)
    residues = np.arange(period, dtype=float)
    return np.exp(2j * math.pi * np.outer(j, residues) / period) / math.sqrt(period)


def fiber_points(period: int, phase: float | None = None) -> np.ndarray:
    if phase is None:
        phase = -0.5 + 0.5 / period
    if not (-0.5 <= phase < -0.5 + 1.0 / period):
        raise ValueError("phase must lie in the standard fundamental interval")
    return phase + np.arange(period, dtype=float) / period


def shallow_negative_matrix(
    period: int,
    pairs: Iterable[int],
    phase: float | None = None,
) -> np.ndarray:
    pair_list = tuple(pairs)
    points = fiber_points(period, phase)
    j = np.arange(period, dtype=float)
    return np.column_stack(
        [
            points * np.exp(2j * math.pi * pair * j / period)
            for pair in pair_list
        ]
    )


def exact_projection_matrix(
    period: int,
    pairs: Iterable[int],
    empties: Iterable[int],
) -> np.ndarray:
    omega = np.exp(2j * math.pi / period)
    pair_list = tuple(pairs)
    empty_list = tuple(empties)
    return np.array(
        [
            [
                -1.0
                / (
                    math.sqrt(period)
                    * (1.0 - omega ** ((pair - empty) % period))
                )
                for pair in pair_list
            ]
            for empty in empty_list
        ],
        dtype=complex,
    )


def direct_projection_matrix(
    period: int,
    pairs: Iterable[int],
    empties: Iterable[int],
    phase: float | None = None,
) -> np.ndarray:
    dft = normalized_dft(period)
    empty_columns = dft[:, tuple(empties)]
    negative = shallow_negative_matrix(period, pairs, phase)
    return empty_columns.conj().T @ negative


def cauchy_determinant_formula(
    period: int,
    pairs: Iterable[int],
    empties: Iterable[int],
) -> complex:
    pair_list = tuple(pairs)
    empty_list = tuple(empties)
    if len(pair_list) != len(empty_list):
        raise ValueError("pair and empty sets must have the same cardinality")
    omega = np.exp(2j * math.pi / period)
    xs = [omega**empty for empty in empty_list]
    ys = [omega**pair for pair in pair_list]
    count = len(pair_list)

    numerator = complex((-1) ** count) * np.prod(xs)
    for left in range(count):
        for right in range(left + 1, count):
            numerator *= xs[right] - xs[left]
            numerator *= ys[left] - ys[right]

    denominator = 1.0 + 0.0j
    for x_value in xs:
        for y_value in ys:
            denominator *= x_value - y_value

    return period ** (-count / 2.0) * numerator / denominator


def principal_angle_squares(
    period: int,
    pairs: Iterable[int],
    empties: Iterable[int],
    phase: float | None = None,
) -> np.ndarray:
    negative = shallow_negative_matrix(period, pairs, phase)
    residual = direct_projection_matrix(period, pairs, empties, phase)
    gram = negative.conj().T @ negative
    schur = residual.conj().T @ residual

    eigenvalues, eigenvectors = np.linalg.eigh((gram + gram.conj().T) / 2.0)
    if eigenvalues[0] <= 0.0:
        raise AssertionError("negative synthesis Gram matrix is not positive definite")
    inverse_sqrt = (
        eigenvectors
        @ np.diag(1.0 / np.sqrt(eigenvalues))
        @ eigenvectors.conj().T
    )
    normalized = inverse_sqrt @ schur @ inverse_sqrt
    answer = np.linalg.eigvalsh((normalized + normalized.conj().T) / 2.0)
    return np.maximum(answer, 0.0)


def column_average_gap(
    period: int,
    pairs: Iterable[int],
    empties: Iterable[int],
    phase: float | None = None,
) -> float:
    negative = shallow_negative_matrix(period, pairs, phase)
    residual = direct_projection_matrix(period, pairs, empties, phase)
    return float(np.linalg.norm(residual, "fro") ** 2 / np.linalg.norm(negative, "fro") ** 2)


def circular_distance(period: int, left: int, right: int) -> int:
    raw = abs(left - right) % period
    return min(raw, period - raw)


def matched_average_lower_bound(period: int, maximum_distance: int) -> float:
    if not (1 <= maximum_distance < period / 2):
        raise ValueError("matching distance must lie in [1,P/2)")
    return 3.0 / (
        (period * period + 2.0)
        * math.sin(math.pi * maximum_distance / period) ** 2
    )


def phase_separated_sets(blocks: int) -> tuple[int, tuple[int, ...], tuple[int, ...]]:
    if blocks < 1:
        raise ValueError("blocks must be positive")
    period = 6 * blocks
    pairs = tuple(range(blocks))
    empties = tuple(range(3 * blocks, 4 * blocks))
    return period, pairs, empties


def phase_separated_average_upper_bound(blocks: int) -> float:
    return 4.0 * blocks / (36.0 * blocks * blocks - 1.0)


def separated_arc_radius() -> float:
    return 2.0 * math.sin(math.pi / 12.0)


def exponential_angle_upper_bound(blocks: int) -> float:
    radius = separated_arc_radius()
    return (
        6.0
        * blocks
        * blocks
        / (5.0 * (1.0 - radius) ** 2)
        * radius ** (2 * blocks - 2)
    )


def separated_cauchy_core(
    period: int,
    pairs: Iterable[int],
    empties: Iterable[int],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    omega = np.exp(2j * math.pi / period)
    pair_roots = np.array([omega**pair for pair in pairs], dtype=complex)
    empty_roots = np.array([omega**empty for empty in empties], dtype=complex)
    core = 1.0 / (empty_roots[:, None] - pair_roots[None, :])
    return core, empty_roots, pair_roots


def separated_low_rank_approximation(
    blocks: int,
) -> tuple[np.ndarray, np.ndarray, float]:
    period, pairs, empties = phase_separated_sets(blocks)
    core, empty_roots, pair_roots = separated_cauchy_core(period, pairs, empties)
    center = np.exp(1j * math.pi / 6.0)
    empty_displacement = empty_roots + center
    pair_displacement = pair_roots - center
    ratio = (
        empty_displacement[:, None] - pair_displacement[None, :]
    ) / (2.0 * center)

    rank_target = max(0, blocks - 1)
    approximation = np.zeros_like(core)
    for power in range(rank_target):
        approximation += -(ratio**power) / (2.0 * center)

    radius = separated_arc_radius()
    entrywise_bound = 0.5 * radius**rank_target / (1.0 - radius)
    return core, approximation, entrywise_bound


def check_projection_and_cauchy(samples: int) -> None:
    rng = np.random.default_rng(20260901)
    maximum_projection_error = 0.0
    maximum_determinant_error = 0.0

    for _ in range(samples):
        period = int(rng.integers(6, 31))
        count = int(rng.integers(1, max(2, period // 3)))
        residues = rng.choice(period, size=2 * count, replace=False)
        pairs = tuple(int(value) for value in residues[:count])
        empties = tuple(int(value) for value in residues[count:])

        direct = direct_projection_matrix(period, pairs, empties)
        exact = exact_projection_matrix(period, pairs, empties)
        maximum_projection_error = max(
            maximum_projection_error,
            float(np.max(np.abs(direct - exact))),
        )

        observed = np.linalg.det(exact)
        predicted = cauchy_determinant_formula(period, pairs, empties)
        relative = abs(observed - predicted) / max(abs(observed), 1.0e-300)
        maximum_determinant_error = max(maximum_determinant_error, float(relative))

        if abs(predicted) == 0.0:
            raise AssertionError("Cauchy determinant unexpectedly vanished")

    if maximum_projection_error > 2.0e-13:
        raise AssertionError(maximum_projection_error)
    if maximum_determinant_error > 2.0e-7:
        raise AssertionError(maximum_determinant_error)

    print("PASS arbitrary-period projection and Cauchy determinant")
    print(f"  random disjoint configurations={samples}")
    print(f"  maximum projection residual={maximum_projection_error:.3e}")
    print(f"  maximum determinant relative error={maximum_determinant_error:.3e}")


def check_phase_separated_collapse(max_blocks: int) -> None:
    if max_blocks < 2:
        raise ValueError("max_blocks must be at least two")

    print("PASS phase-separated shallow-angle collapse")
    print("  P    pairs       eta_min        mean_eta      column_avg      avg_upper")
    previous_average = math.inf

    for blocks in range(1, max_blocks + 1):
        period, pairs, empties = phase_separated_sets(blocks)
        angles = principal_angle_squares(period, pairs, empties)
        average = column_average_gap(period, pairs, empties)
        upper = phase_separated_average_upper_bound(blocks)

        if average > upper + 2.0e-12:
            raise AssertionError((blocks, average, upper))
        if blocks > 1 and average >= previous_average:
            raise AssertionError("phase-separated average gap did not decrease")
        previous_average = average

        print(
            f"  {period:3d}  {blocks:5d}  {angles[0]:.3e}  "
            f"{angles.mean():.3e}  {average:.3e}  {upper:.3e}"
        )

    last_upper = phase_separated_average_upper_bound(max_blocks)
    if last_upper > 1.0 / max_blocks:
        raise AssertionError("explicit O(1/P) bound regression")


def check_bounded_matching() -> None:
    examples = (
        (12, (0, 4), (1, 5), 1),
        (18, (0, 6, 12), (1, 7, 13), 1),
        (24, (0, 6, 12, 18), (2, 8, 14, 20), 2),
        (30, (0, 5, 10, 15, 20), (2, 7, 12, 17, 22), 2),
    )

    for period, pairs, empties, distance in examples:
        actual_maximum = max(
            circular_distance(period, pair, empty)
            for pair, empty in zip(pairs, empties)
        )
        if actual_maximum > distance:
            raise AssertionError("declared matching radius is too small")
        observed = column_average_gap(period, pairs, empties)
        lower = matched_average_lower_bound(period, distance)
        if observed + 2.0e-12 < lower:
            raise AssertionError((period, observed, lower))

    print("PASS bounded pair-vacancy matching average-gap lower bound")
    print("  fixed matching radius gives a positive asymptotic column-average gap")


def check_low_rank_exponential_bound(max_blocks: int) -> None:
    radius = separated_arc_radius()
    if abs(radius * radius - (2.0 - math.sqrt(3.0))) > 1.0e-14:
        raise AssertionError("arc radius identity mismatch")

    for blocks in range(2, max_blocks + 1):
        core, approximation, entrywise_bound = separated_low_rank_approximation(blocks)
        error = core - approximation
        maximum_error = float(np.max(np.abs(error)))
        if maximum_error > entrywise_bound + 2.0e-13:
            raise AssertionError((blocks, maximum_error, entrywise_bound))

        numerical_rank = np.linalg.matrix_rank(approximation, tol=1.0e-10)
        if numerical_rank > blocks - 1:
            raise AssertionError((blocks, numerical_rank))

        period, pairs, empties = phase_separated_sets(blocks)
        eta_min = float(principal_angle_squares(period, pairs, empties)[0])
        analytic_upper = exponential_angle_upper_bound(blocks)
        if eta_min > analytic_upper + 1.0e-10:
            raise AssertionError((blocks, eta_min, analytic_upper))

    print("PASS separated-arc low-rank and exponential angle upper bound")
    print(f"  analytic radius r=sqrt(2-sqrt(3))={radius:.12f}")
    print(
        "  eta_min <= [6m^2/(5(1-r)^2)] r^(2m-2) "
        "for the P=6m phase-separated family"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--max-blocks", type=int, default=8)
    args = parser.parse_args()

    check_projection_and_cauchy(args.samples)
    check_phase_separated_collapse(args.max_blocks)
    check_bounded_matching()
    check_low_rank_exponential_bound(args.max_blocks)
    print(
        "BOUNDARY: finite ideal shallow/confluent periodic systems only; "
        "no uniform source-level angle theorem or zeta-zero theorem is proved."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
