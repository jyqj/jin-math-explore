#!/usr/bin/env python3
"""Deterministic checks for the all-depth and two-depth rigidity checkpoint.

The script checks finite ideal Fourier identities and inequalities. It does
not prove the analytic lemmas, transfer them to Zeta23, or prove a theorem about
zeta zeros.
"""

from __future__ import annotations

import argparse
import math

import numpy as np


def fourier_matrix(period: int) -> np.ndarray:
    rows = np.arange(period, dtype=float)
    residues = np.arange(period, dtype=float)
    return np.exp(2j * math.pi * np.outer(rows, residues) / period) / math.sqrt(period)


def centered_points(period: int) -> np.ndarray:
    return (np.arange(period, dtype=float) - (period - 1) / 2.0) / period


def k2(load: int) -> int:
    return 4 - max(2 - load, 0) ** 2


def pair_atom(period: int, residue: int, depth: float) -> np.ndarray:
    fourier = fourier_matrix(period)
    vector = fourier[:, residue : residue + 1]
    projection = vector @ vector.conj().T
    points = centered_points(period)
    cosh = np.diag(np.cosh(depth * points))
    sinh = np.diag(np.sinh(depth * points))
    return 2.0 * (cosh @ projection @ cosh - sinh @ projection @ sinh)


def mixed_defect(
    period: int,
    pairs: tuple[int, ...],
    tangent_loads: np.ndarray,
    depth: float,
) -> float:
    pair_set = set(pairs)
    fourier = fourier_matrix(period)
    matrix = np.zeros((period, period), dtype=complex)
    budget = 0.0

    for residue in range(period):
        vector = fourier[:, residue : residue + 1]
        projection = vector @ vector.conj().T
        if residue in pair_set:
            matrix += pair_atom(period, residue, depth)
            budget += 4.0
        else:
            load = int(tangent_loads[residue])
            matrix += load * projection
            budget += k2(load)

    matrix = (matrix + matrix.conj().T) / 2.0
    return float(
        budget
        - (4.0 * float(np.trace(matrix).real) - float(np.linalg.norm(matrix, "fro") ** 2))
    )


def pair_cross_kernel(period: int, offset: int, depth: float) -> float:
    residue = offset % period
    if residue == 0:
        raise ValueError("a nonzero residue is required")
    rho = math.exp(depth / period)
    theta = 2.0 * math.pi * residue / period
    scale = rho ** (-(period - 1) / 2.0) * (rho**period - 1.0) / period
    denominator = 1.0 + rho * rho - 2.0 * rho * math.cos(theta)
    numerator = (1.0 + rho * rho) * math.cos(theta) - 2.0 * rho
    return 2.0 * scale * scale * numerator / (denominator * denominator)


def pair_cross_kernel_simplified(period: int, offset: int, depth: float) -> float:
    residue = offset % period
    if residue == 0:
        raise ValueError("a nonzero residue is required")
    x = depth / period
    theta = 2.0 * math.pi * residue / period
    numerator = math.cosh(x) * math.cos(theta) - 1.0
    denominator = (math.cosh(x) - math.cos(theta)) ** 2
    return 4.0 * math.sinh(depth / 2.0) ** 2 * numerator / (period * period * denominator)


def same_depth_symbol(theta: float, depth: float) -> float:
    theta %= 1.0
    return 4.0 * (
        theta * (math.cosh(depth * (1.0 - theta)) - 1.0) ** 2
        + (1.0 - theta) * (math.cosh(depth * theta) - 1.0) ** 2
    )


def two_depth_symbol(theta: float, first: float, second: float) -> float:
    theta %= 1.0
    return 4.0 * (
        theta
        * (math.cosh(first * (1.0 - theta)) - math.cosh(second * (1.0 - theta))) ** 2
        + (1.0 - theta)
        * (math.cosh(first * theta) - math.cosh(second * theta)) ** 2
    )


def indicator_hat(mask: np.ndarray) -> np.ndarray:
    return np.fft.fft(mask.astype(float)) / len(mask)


def boundary_count(mask: np.ndarray) -> int:
    return int(np.sum(np.roll(mask, -1) != mask))


def all_two_defect_spectral(period: int, mask: np.ndarray, depth: float) -> float:
    transformed = indicator_hat(mask)
    return period * sum(
        same_depth_symbol(index / period, depth) * abs(transformed[index]) ** 2
        for index in range(period)
    )


def positive_kernel_moment(period: int, depth: float) -> float:
    return sum(
        min(offset, period - offset) * max(pair_cross_kernel(period, offset, depth), 0.0)
        for offset in range(1, period)
    )


def gamma_high(depth: float) -> float:
    c = math.cosh(depth / 2.0) - 1.0
    s = math.sinh(depth / 2.0)
    return 0.5 * c * c - 4.0 * s * s / (math.pi * math.pi)


def overlap_threshold() -> float:
    value = math.pi / (2.0 * math.sqrt(2.0))
    return 2.0 * math.log((value + 1.0) / (value - 1.0))


def two_depth_direct(period: int, mask: np.ndarray, first: float, second: float) -> float:
    matrix = np.zeros((period, period), dtype=complex)
    for residue in range(period):
        matrix += pair_atom(period, residue, first if mask[residue] else second)
    matrix = (matrix + matrix.conj().T) / 2.0
    return float(np.linalg.norm(matrix - 2.0 * np.eye(period), "fro") ** 2)


def two_depth_spectral(period: int, mask: np.ndarray, first: float, second: float) -> float:
    transformed = indicator_hat(mask)
    return period * sum(
        two_depth_symbol(index / period, first, second) * abs(transformed[index]) ** 2
        for index in range(period)
    )


def check_symbol_lower(theta_grid: int, depth_grid: int) -> None:
    minimum_same_slack = math.inf
    minimum_two_slack = math.inf
    for depth in np.linspace(0.02, 20.0, depth_grid):
        c = math.cosh(float(depth) / 2.0) - 1.0
        for index in range(1, theta_grid):
            theta = index / theta_grid
            lower = 2.0 * c * c * math.sin(math.pi * theta) ** 2
            minimum_same_slack = min(
                minimum_same_slack,
                same_depth_symbol(theta, float(depth)) - lower,
            )

    rng = np.random.default_rng(20260909)
    for _ in range(depth_grid * 4):
        first = float(rng.uniform(0.02, 20.0))
        second = float(rng.uniform(0.0, first))
        c = math.cosh(first / 2.0) - math.cosh(second / 2.0)
        for theta in rng.uniform(0.001, 0.999, 20):
            lower = 2.0 * c * c * math.sin(math.pi * float(theta)) ** 2
            minimum_two_slack = min(
                minimum_two_slack,
                two_depth_symbol(float(theta), first, second) - lower,
            )

    if minimum_same_slack < -2.0e-10 or minimum_two_slack < -2.0e-10:
        raise AssertionError((minimum_same_slack, minimum_two_slack))
    print("PASS same-depth and two-depth symbol lower bounds")
    print(f"  minimum same-depth slack={minimum_same_slack:.3e}")
    print(f"  minimum two-depth slack={minimum_two_slack:.3e}")


def check_kernel_moment(max_period: int, depth_grid: int) -> None:
    maximum_formula_residual = 0.0
    maximum_ratio = 0.0
    for period in range(2, max_period + 1):
        for depth in np.linspace(0.05, 25.0, depth_grid):
            depth = float(depth)
            for offset in range(1, period):
                direct = pair_cross_kernel(period, offset, depth)
                simplified = pair_cross_kernel_simplified(period, offset, depth)
                maximum_formula_residual = max(
                    maximum_formula_residual,
                    abs(direct - simplified) / max(1.0, abs(direct), abs(simplified)),
                )
            moment = positive_kernel_moment(period, depth)
            upper = 2.0 * math.sinh(depth / 2.0) ** 2 / (math.pi * math.pi)
            if moment > upper * (1.0 + 2.0e-11) + 2.0e-11:
                raise AssertionError((period, depth, moment, upper))
            if upper > 0.0:
                maximum_ratio = max(maximum_ratio, moment / upper)

    print("PASS simplified interaction kernel and positive-moment bound")
    print(f"  maximum relative formula residual={maximum_formula_residual:.3e}")
    print(f"  maximum tested moment/upper ratio={maximum_ratio:.9f}")


def check_high_depth_absorption(samples: int) -> None:
    threshold = overlap_threshold()
    if not threshold < 2.0 * math.pi:
        raise AssertionError(threshold)

    rng = np.random.default_rng(20260910)
    minimum_slack = math.inf
    for _ in range(samples):
        period = int(rng.integers(3, 75))
        depth = float(rng.uniform(2.0 * math.pi, 20.0))
        mask = rng.random(period) < float(rng.uniform(0.05, 0.95))
        if mask.all() or (~mask).all():
            continue
        loads = rng.integers(0, 3, size=period)
        pairs = tuple(int(value) for value in np.where(mask)[0])
        defect = mixed_defect(period, pairs, loads, depth)
        lower = gamma_high(depth) * boundary_count(mask)
        slack = defect - lower
        minimum_slack = min(minimum_slack, slack)
        if slack < -2.0e-7 * max(1.0, abs(defect), abs(lower)):
            raise AssertionError((period, depth, defect, lower))

    print("PASS high-depth arbitrary-tangent absorption regression")
    print(f"  a_*={threshold:.12f} < 2pi={2.0 * math.pi:.12f}")
    print(f"  minimum tested absolute slack={minimum_slack:.6e}")


def check_two_depth_identity(samples: int) -> None:
    rng = np.random.default_rng(20260911)
    maximum_relative_residual = 0.0
    minimum_boundary_slack = math.inf

    for _ in range(samples):
        period = int(rng.integers(3, 65))
        first = float(rng.uniform(0.02, 12.0))
        second = float(rng.uniform(0.0, first))
        mask = rng.random(period) < float(rng.uniform(0.05, 0.95))
        if mask.all() or (~mask).all():
            continue

        direct = two_depth_direct(period, mask, first, second)
        spectral = two_depth_spectral(period, mask, first, second)
        residual = abs(direct - spectral) / max(1.0, abs(direct), abs(spectral))
        maximum_relative_residual = max(maximum_relative_residual, residual)
        if residual > 2.0e-9:
            raise AssertionError((period, first, second, direct, spectral))

        c = math.cosh(first / 2.0) - math.cosh(second / 2.0)
        lower = 0.5 * c * c * boundary_count(mask)
        slack = direct - lower
        minimum_boundary_slack = min(minimum_boundary_slack, slack)
        if slack < -2.0e-8 * max(1.0, abs(direct), abs(lower)):
            raise AssertionError((period, first, second, direct, lower))

    print("PASS exact two-depth Fourier identity and interface inequality")
    print(f"  maximum relative direct/spectral residual={maximum_relative_residual:.3e}")
    print(f"  minimum tested absolute boundary slack={minimum_boundary_slack:.3e}")


def check_phase_separated_depths() -> None:
    first = 2.0
    second = 0.5
    d1 = abs(math.cosh(first) - math.cosh(second))
    d2 = abs(first - second) * math.sinh(max(first, second) / 2.0)
    coefficient = 2.0 * (d1 * d1 + d2 * d2)

    print("PASS phase-separated binary-depth upper bound")
    for period in (60, 120, 240, 480):
        mask = np.zeros(period, dtype=bool)
        mask[: period // 2] = True
        density = two_depth_spectral(period, mask, first, second) / period
        upper = coefficient * (1.0 + math.log(period / 2.0)) / period
        if density > upper + 2.0e-12:
            raise AssertionError((period, density, upper))
        print(f"  P={period:4d}: defect/P={density:.9e} <= {upper:.9e}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=220)
    parser.add_argument("--max-period", type=int, default=90)
    parser.add_argument("--depth-grid", type=int, default=40)
    parser.add_argument("--theta-grid", type=int, default=1200)
    args = parser.parse_args()

    check_symbol_lower(args.theta_grid, args.depth_grid)
    check_kernel_moment(args.max_period, args.depth_grid)
    check_high_depth_absorption(args.samples)
    check_two_depth_identity(args.samples)
    check_phase_separated_depths()
    print(
        "BOUNDARY: finite ideal common/two-depth Fourier models only; "
        "continuous variable depth and actual Zeta23 transfer remain open."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
