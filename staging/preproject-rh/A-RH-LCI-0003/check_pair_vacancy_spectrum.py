#!/usr/bin/env python3
"""Checks for fixed-depth pair/vacancy spectral rigidity.

Finite ideal Fourier models only; no theorem about actual zeta zeros.
"""

from __future__ import annotations

import argparse
import math

import numpy as np


def fourier_matrix(period: int) -> np.ndarray:
    rows = np.arange(period, dtype=float)
    residues = np.arange(period, dtype=float)
    return np.exp(2j * math.pi * np.outer(rows, residues) / period) / math.sqrt(period)


def sample_points(period: int, phase: float) -> np.ndarray:
    return phase + np.arange(period, dtype=float) / period


def defect_symbol(theta: float, depth: float) -> float:
    theta = theta % 1.0
    return 2.0 * (
        theta * math.cosh(2.0 * depth * (1.0 - theta))
        + (1.0 - theta) * math.cosh(2.0 * depth * theta)
        - 1.0
    )


def indicator_hat(period: int, occupied: tuple[int, ...]) -> np.ndarray:
    indicator = np.zeros(period, dtype=float)
    indicator[list(occupied)] = 1.0
    return np.fft.fft(indicator) / period


def spectral_defect_density(period: int, occupied: tuple[int, ...], depth: float) -> float:
    transformed = indicator_hat(period, occupied)
    return float(
        sum(
            defect_symbol(index / period, depth) * abs(transformed[index]) ** 2
            for index in range(period)
        )
    )


def direct_matrix(period: int, occupied: tuple[int, ...], depth: float, phase: float) -> np.ndarray:
    fourier = fourier_matrix(period)
    projection = fourier[:, occupied] @ fourier[:, occupied].conj().T
    points = sample_points(period, phase)
    c = np.diag(np.cosh(depth * points))
    s = np.diag(np.sinh(depth * points))
    matrix = 2.0 * (c @ projection @ c - s @ projection @ s)
    return (matrix + matrix.conj().T) / 2.0


def direct_defect_density(period: int, occupied: tuple[int, ...], depth: float, phase: float) -> float:
    matrix = direct_matrix(period, occupied, depth, phase)
    count = len(occupied)
    defect = np.linalg.norm(matrix, "fro") ** 2 - 4.0 * count
    return float(defect / period)


def boundary_density(period: int, occupied: tuple[int, ...]) -> float:
    indicator = np.zeros(period, dtype=float)
    indicator[list(occupied)] = 1.0
    return float(np.mean((np.roll(indicator, -1) - indicator) ** 2))


def boundary_upper(defect_density: float, depth: float) -> float:
    if depth <= 0.0:
        return math.inf
    return 2.0 * math.pi * defect_density / (math.cosh(depth) - 1.0)


def check_symbol(samples: int) -> None:
    rng = np.random.default_rng(20260901)
    maximum_formula_error = 0.0
    maximum_phase_variation = 0.0

    for _ in range(samples):
        period = int(rng.integers(3, 31))
        count = int(rng.integers(0, period + 1))
        occupied = tuple(sorted(int(value) for value in rng.choice(period, size=count, replace=False)))
        depth = float(rng.uniform(0.05, 4.0))
        phases = np.linspace(-0.5, -0.5 + 1.0 / period, 5, endpoint=False)
        direct_values = [
            direct_defect_density(period, occupied, depth, float(phase))
            for phase in phases
        ]
        spectral = spectral_defect_density(period, occupied, depth)
        maximum_formula_error = max(
            maximum_formula_error,
            max(abs(value - spectral) for value in direct_values),
        )
        maximum_phase_variation = max(
            maximum_phase_variation,
            max(direct_values) - min(direct_values),
        )

    if maximum_formula_error > 5.0e-10:
        raise AssertionError(maximum_formula_error)
    if maximum_phase_variation > 5.0e-10:
        raise AssertionError(maximum_phase_variation)

    print("PASS exact finite pair/vacancy defect symbol")
    print(f"  random configurations={samples}")
    print(f"  maximum direct/spectral residual={maximum_formula_error:.3e}")
    print(f"  maximum fiber-phase variation={maximum_phase_variation:.3e}")


def check_symbol_positivity(grid: int) -> None:
    depths = (0.1, 0.5, 1.0, 2.0, 4.0)
    smallest_slack = math.inf
    for depth in depths:
        for index in range(1, grid):
            theta = index / grid
            distance = min(theta, 1.0 - theta)
            value = defect_symbol(theta, depth)
            lower = 2.0 * (math.cosh(depth) - 1.0) * distance
            smallest_slack = min(smallest_slack, value - lower)
            if value <= 0.0 or value + 2.0e-13 < lower:
                raise AssertionError((depth, theta, value, lower))
        if abs(defect_symbol(0.0, depth)) > 1.0e-14:
            raise AssertionError("zero mode mismatch")
        if abs(defect_symbol(1.0, depth)) > 1.0e-14:
            raise AssertionError("period endpoint mismatch")

    print("PASS positivity and unique-zero lower bound")
    print(f"  grid={grid}; minimum numerical slack={smallest_slack:.3e}")


def check_boundary_control(samples: int) -> None:
    rng = np.random.default_rng(20260902)
    maximum_ratio = 0.0
    for _ in range(samples):
        period = int(rng.integers(4, 61))
        count = int(rng.integers(0, period + 1))
        occupied = tuple(sorted(int(value) for value in rng.choice(period, size=count, replace=False)))
        depth = float(rng.uniform(0.1, 4.0))
        defect = spectral_defect_density(period, occupied, depth)
        boundary = boundary_density(period, occupied)
        upper = boundary_upper(defect, depth)
        if boundary > upper + 2.0e-12:
            raise AssertionError((period, depth, boundary, upper))
        if upper > 0.0 and math.isfinite(upper):
            maximum_ratio = max(maximum_ratio, boundary / upper)

    print("PASS nearest-neighbor boundary inequality")
    print(f"  random configurations={samples}")
    print(f"  largest observed boundary/upper ratio={maximum_ratio:.6f}")


def check_homogeneous_operator_identity(samples: int) -> None:
    rng = np.random.default_rng(20260903)
    maximum_residual = 0.0

    for _ in range(samples):
        period = int(rng.integers(3, 41))
        depth = float(rng.uniform(0.0, 5.0))
        values = rng.normal(size=period)
        fourier = fourier_matrix(period)
        points = -0.5 + (np.arange(period, dtype=float) + 0.5) / period
        psi = np.diag(values)
        c = np.diag(np.cosh(depth * points))
        s = np.diag(np.sinh(depth * points))

        x_columns = psi @ c @ fourier
        y_columns = psi @ s @ fourier
        signed = 2.0 * (x_columns @ x_columns.conj().T - y_columns @ y_columns.conj().T)
        expected = 2.0 * psi @ psi
        maximum_residual = max(
            maximum_residual,
            float(np.linalg.norm(signed - expected, "fro")),
        )

    if maximum_residual > 2.0e-10:
        raise AssertionError(maximum_residual)

    print("PASS homogeneous pair/load-two operator identity")
    print(f"  random finite Fourier grids={samples}")
    print(f"  maximum Frobenius residual={maximum_residual:.3e}")


def check_macroscopic_blocks(max_period: int, depth: float) -> None:
    periods = tuple(period for period in range(24, max_period + 1, 24))
    if not periods:
        raise ValueError("max-period must be at least 24")

    previous_boundary = math.inf
    print("PASS macroscopic phase-separation scaling")
    print("  P    pair_fraction   boundary_density   defect_density")
    for period in periods:
        count = period // 4
        occupied = tuple(range(count))
        boundary = boundary_density(period, occupied)
        defect = spectral_defect_density(period, occupied, depth)
        if boundary >= previous_boundary:
            raise AssertionError("boundary density did not decrease")
        previous_boundary = boundary
        print(f"  {period:3d}  {count/period:.6f}       {boundary:.6e}       {defect:.6e}")

    if previous_boundary > 2.0 / periods[-1] + 1.0e-14:
        raise AssertionError("boundary identity regression")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=120)
    parser.add_argument("--grid", type=int, default=4000)
    parser.add_argument("--max-period", type=int, default=240)
    parser.add_argument("--depth", type=float, default=1.0)
    args = parser.parse_args()

    check_symbol(args.samples)
    check_symbol_positivity(args.grid)
    check_boundary_control(args.samples)
    check_homogeneous_operator_identity(args.samples)
    check_macroscopic_blocks(args.max_period, args.depth)
    print(
        "BOUNDARY: finite ideal fixed-depth pair/vacancy Fourier models only; "
        "mixed states, varying depths, source transfer, and zeta remain open."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
