#!/usr/bin/env python3
"""Checks for mixed tangent 0/1/2 states with one moderate pair depth.

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


def k2(load: int) -> int:
    return 4 - max(2 - load, 0) ** 2


def pair_cross_kernel(period: int, offset: int, depth: float) -> float:
    if offset % period == 0:
        raise ValueError("off-diagonal offset required")
    radius = math.exp(depth / period)
    angle = 2.0 * math.pi * (offset % period) / period
    scale = (
        radius ** (-(period - 1) / 2.0)
        * (radius**period - 1.0)
        / period
    )
    denominator = 1.0 + radius * radius - 2.0 * radius * math.cos(angle)
    numerator = (1.0 + radius * radius) * math.cos(angle) - 2.0 * radius
    return 2.0 * scale * scale * numerator / (denominator * denominator)


def r_symbol(theta: float, depth: float) -> float:
    theta = theta % 1.0
    return (
        theta * math.cosh(depth * (1.0 - theta))
        + (1.0 - theta) * math.cosh(depth * theta)
    )


def difference_symbol(theta: float, depth: float) -> float:
    theta = theta % 1.0
    return 4.0 * (
        theta * (math.cosh(depth * (1.0 - theta)) - 1.0) ** 2
        + (1.0 - theta) * (math.cosh(depth * theta) - 1.0) ** 2
    )


def indicator_hat(period: int, pairs: tuple[int, ...]) -> np.ndarray:
    values = np.zeros(period, dtype=float)
    values[list(pairs)] = 1.0
    return np.fft.fft(values) / period


def spectral_lower(period: int, pairs: tuple[int, ...], depth: float) -> float:
    transformed = indicator_hat(period, pairs)
    return float(
        sum(
            difference_symbol(index / period, depth) * abs(transformed[index]) ** 2
            for index in range(period)
        )
    )


def boundary_density(period: int, pairs: tuple[int, ...]) -> float:
    values = np.zeros(period, dtype=float)
    values[list(pairs)] = 1.0
    return float(np.mean((np.roll(values, -1) - values) ** 2))


def direct_defect(
    period: int,
    pairs: tuple[int, ...],
    tangent_loads: np.ndarray,
    depth: float,
    phase: float,
) -> float:
    pair_set = set(pairs)
    fourier = fourier_matrix(period)
    points = phase + np.arange(period, dtype=float) / period
    c = np.diag(np.cosh(depth * points))
    s = np.diag(np.sinh(depth * points))
    matrix = np.zeros((period, period), dtype=complex)
    budget = 0

    for residue in range(period):
        column = fourier[:, residue : residue + 1]
        atom = column @ column.conj().T
        if residue in pair_set:
            matrix += 2.0 * (c @ atom @ c - s @ atom @ s)
            budget += 4
        else:
            load = int(tangent_loads[residue])
            matrix += load * atom
            budget += k2(load)

    matrix = (matrix + matrix.conj().T) / 2.0
    defect = budget - (
        4.0 * float(np.trace(matrix).real)
        - float(np.linalg.norm(matrix, "fro") ** 2)
    )
    return defect / period


def all_two_defect(
    period: int,
    pairs: tuple[int, ...],
    depth: float,
    phase: float,
) -> float:
    loads = np.full(period, 2, dtype=int)
    return direct_defect(period, pairs, loads, depth, phase)


def check_kernel_formula(samples: int) -> None:
    rng = np.random.default_rng(20260904)
    maximum_residual = 0.0

    for _ in range(samples):
        period = int(rng.integers(4, 31))
        depth = float(rng.uniform(0.05, 6.0))
        phase = float(rng.uniform(-0.5, -0.5 + 1.0 / period))
        p, q = rng.choice(period, size=2, replace=False)
        offset = int(p) - int(q)

        fourier = fourier_matrix(period)
        points = phase + np.arange(period, dtype=float) / period
        c = np.diag(np.cosh(depth * points))
        s = np.diag(np.sinh(depth * points))
        up = fourier[:, int(p) : int(p) + 1]
        uq = fourier[:, int(q) : int(q) + 1]
        atom_p = up @ up.conj().T
        atom_q = uq @ uq.conj().T
        pair_p = 2.0 * (c @ atom_p @ c - s @ atom_p @ s)
        difference = pair_p - 2.0 * atom_p
        observed = float(np.trace(atom_q @ difference).real)
        predicted = pair_cross_kernel(period, offset, depth)
        maximum_residual = max(maximum_residual, abs(observed - predicted))

    if maximum_residual > 2.0e-10:
        raise AssertionError(maximum_residual)

    print("PASS exact pair-versus-tangent kernel")
    print(f"  random samples={samples}")
    print(f"  maximum residual={maximum_residual:.3e}")


def check_moderate_sign(grid: int) -> None:
    depths = np.linspace(0.05, 2.0 * math.pi - 1.0e-4, grid)
    largest_value = -math.inf
    for period in range(2, 81):
        for depth in depths:
            for offset in range(1, period):
                value = pair_cross_kernel(period, offset, float(depth))
                largest_value = max(largest_value, value)
                if value >= 0.0:
                    raise AssertionError((period, depth, offset, value))

    print("PASS favorable off-diagonal sign for 0<a<2pi")
    print(f"  periods=2..80; depth grid={grid}; largest tested kernel={largest_value:.3e}")


def check_mixed_lower(samples: int) -> None:
    rng = np.random.default_rng(20260905)
    smallest_slack = math.inf
    maximum_phase_variation = 0.0

    for _ in range(samples):
        period = int(rng.integers(3, 36))
        pair_mask = rng.random(period) < float(rng.uniform(0.0, 0.7))
        pairs = tuple(int(value) for value in np.where(pair_mask)[0])
        loads = rng.integers(0, 3, size=period)
        depth = float(rng.uniform(0.05, 2.0 * math.pi - 0.01))
        phases = np.linspace(-0.5, -0.5 + 1.0 / period, 4, endpoint=False)
        values = [
            direct_defect(period, pairs, loads, depth, float(phase))
            for phase in phases
        ]
        lower = spectral_lower(period, pairs, depth)
        smallest_slack = min(smallest_slack, min(values) - lower)
        maximum_phase_variation = max(
            maximum_phase_variation,
            max(values) - min(values),
        )
        if min(values) + 3.0e-10 < lower:
            raise AssertionError((period, depth, min(values), lower, loads, pairs))

        all_two = all_two_defect(period, pairs, depth, float(phases[0]))
        if abs(all_two - lower) > 3.0e-10:
            raise AssertionError(("all-two identity", all_two, lower))

    print("PASS mixed tangent-state spectral lower bound")
    print(f"  random configurations={samples}")
    print(f"  minimum defect-minus-lower slack={smallest_slack:.3e}")
    print(f"  maximum fiber-phase variation={maximum_phase_variation:.3e}")


def check_symbol(grid: int) -> None:
    depths = (0.1, 0.5, 1.0, 2.0, 4.0, 6.0)
    minimum_slack = math.inf

    for depth in depths:
        coefficient = 4.0 * (math.cosh(depth / 2.0) - 1.0) ** 2
        for index in range(1, grid):
            theta = index / grid
            distance = min(theta, 1.0 - theta)
            direct = difference_symbol(theta, depth)
            alternate = 2.0 * (
                3.0 + r_symbol(theta, 2.0 * depth) - 4.0 * r_symbol(theta, depth)
            )
            lower = coefficient * distance
            minimum_slack = min(minimum_slack, direct - lower)
            if abs(direct - alternate) > 2.0e-10:
                raise AssertionError(("symbol identity", depth, theta, direct, alternate))
            if direct <= 0.0 or direct + 3.0e-13 < lower:
                raise AssertionError(("symbol lower", depth, theta, direct, lower))

    print("PASS difference-atom symbol identity and positivity")
    print(f"  theta grid={grid}; minimum lower-bound slack={minimum_slack:.3e}")


def check_boundary(samples: int) -> None:
    rng = np.random.default_rng(20260906)
    largest_ratio = 0.0

    for _ in range(samples):
        period = int(rng.integers(4, 61))
        pair_mask = rng.random(period) < float(rng.uniform(0.0, 0.8))
        pairs = tuple(int(value) for value in np.where(pair_mask)[0])
        loads = rng.integers(0, 3, size=period)
        depth = float(rng.uniform(0.1, 2.0 * math.pi - 0.02))
        defect = direct_defect(
            period,
            pairs,
            loads,
            depth,
            -0.5 + 0.5 / period,
        )
        boundary = boundary_density(period, pairs)
        denominator = (math.cosh(depth / 2.0) - 1.0) ** 2
        upper = math.pi * defect / denominator
        if boundary > upper + 3.0e-10:
            raise AssertionError((period, depth, boundary, upper))
        if upper > 0.0:
            largest_ratio = max(largest_ratio, boundary / upper)

    print("PASS mixed-state pair-interface inequality")
    print(f"  random configurations={samples}")
    print(f"  largest observed boundary/upper ratio={largest_ratio:.6f}")


def check_high_depth_scope_guard() -> None:
    depth = 10.0
    period = 20
    positive = pair_cross_kernel(period, 1, depth)
    negative = pair_cross_kernel(period, 2, depth)
    if positive <= 0.0 or negative >= 0.0:
        raise AssertionError((positive, negative))

    print("PASS high-depth scope guard")
    print(f"  at a=10: J_a(1)={positive:.6f} > 0, J_a(2)={negative:.6f} < 0")
    print("  the uniform favorable-sign reduction is therefore not extended past 2pi")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=120)
    parser.add_argument("--depth-grid", type=int, default=600)
    parser.add_argument("--theta-grid", type=int, default=3000)
    args = parser.parse_args()

    check_kernel_formula(args.samples)
    check_moderate_sign(args.depth_grid)
    check_mixed_lower(args.samples)
    check_symbol(args.theta_grid)
    check_boundary(args.samples)
    check_high_depth_scope_guard()
    print(
        "BOUNDARY: ideal fixed common depth 0<a<2pi only; "
        "variable/high depth and actual Zeta23 transfer remain open."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
