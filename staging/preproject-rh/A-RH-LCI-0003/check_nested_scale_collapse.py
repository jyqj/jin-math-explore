#!/usr/bin/env python3
"""Checks for the source-compatible nested-support scale collapse.

Finite ideal partial Fourier sections only. The script verifies that changing
support length on one master critical lattice changes only nonnegative diagonal
weights and does not create new depth-moment channels at a fixed master
frequency. It does not prove a Zeta23 transfer theorem.
"""

from __future__ import annotations

import argparse
import math

import numpy as np


def partial_fourier(period: int, rows: int) -> np.ndarray:
    j = np.arange(rows, dtype=float)
    p = np.arange(period, dtype=float)
    return np.exp(2j * math.pi * np.outer(j, p) / period) / math.sqrt(period)


def centered_points(period: int, rows: int) -> np.ndarray:
    return (np.arange(rows, dtype=float) - (rows - 1) / 2.0) / period


def pair_atom(period: int, rows: int, residue: int, depth: float) -> np.ndarray:
    frame = partial_fourier(period, rows)
    vector = frame[:, residue : residue + 1]
    projection = vector @ vector.conj().T
    points = centered_points(period, rows)
    c = np.diag(np.cosh(depth * points))
    s = np.diag(np.sinh(depth * points))
    return 2.0 * (c @ projection @ c - s @ projection @ s)


def direct_excess(labels: np.ndarray, depths: np.ndarray, rows: int) -> float:
    period = len(labels)
    matrix = np.zeros((rows, rows), dtype=complex)
    for residue, label in enumerate(labels):
        matrix += pair_atom(period, rows, residue, float(depths[label]))
    matrix = (matrix + matrix.conj().T) / 2.0
    return float(np.linalg.norm(matrix - 2.0 * np.eye(rows), "fro") ** 2)


def indicator_fourier(labels: np.ndarray, classes: int, frequency: int) -> np.ndarray:
    period = len(labels)
    p = np.arange(period, dtype=float)
    phase = np.exp(2j * math.pi * p * frequency / period)
    return np.array(
        [np.mean((labels == label) * phase) for label in range(classes)],
        dtype=complex,
    )


def moment(labels: np.ndarray, depths: np.ndarray, frequency: int) -> complex:
    period = len(labels)
    theta = frequency / period
    z = indicator_fourier(labels, len(depths), frequency)
    return complex(np.dot(z, np.cosh(theta * depths)))


def symbol_excess(labels: np.ndarray, depths: np.ndarray, rows: int) -> float:
    total = 0.0
    for frequency in range(1, rows):
        total += 8.0 * (rows - frequency) * abs(moment(labels, depths, frequency)) ** 2
    return float(total)


def bank_direct(
    labels: np.ndarray,
    depths: np.ndarray,
    row_counts: np.ndarray,
    weights: np.ndarray,
) -> float:
    return float(
        sum(
            weight * direct_excess(labels, depths, int(rows))
            for rows, weight in zip(row_counts, weights)
        )
    )


def bank_collapsed(
    labels: np.ndarray,
    depths: np.ndarray,
    row_counts: np.ndarray,
    weights: np.ndarray,
) -> float:
    maximum = int(np.max(row_counts))
    total = 0.0
    for frequency in range(1, maximum):
        coefficient = float(
            sum(
                weight * max(int(rows) - frequency, 0)
                for rows, weight in zip(row_counts, weights)
            )
        )
        total += 8.0 * coefficient * abs(moment(labels, depths, frequency)) ** 2
    return total


def endpoint_null(depths: np.ndarray) -> np.ndarray:
    matrix = np.vstack([np.ones(len(depths)), np.cosh(depths)])
    _, _, vh = np.linalg.svd(matrix)
    vector = vh[-1].conj()
    return vector / np.linalg.norm(vector)


def channel_energy_for_vector(
    z: np.ndarray,
    depths: np.ndarray,
    theta: float,
    ratios: np.ndarray,
    weights: np.ndarray,
) -> float:
    first = np.dot(z, np.cosh(theta * depths))
    second = np.dot(z, np.cosh((1.0 - theta) * depths))
    total = 4.0 * weights[0] * (
        (1.0 - theta) * abs(first) ** 2 + theta * abs(second) ** 2
    )

    for ratio, weight in zip(ratios[1:], weights[1:]):
        if theta < ratio:
            total += 8.0 * weight * (ratio - theta) * abs(first) ** 2
    return float(total)


def check_partial_symbol(samples: int) -> None:
    rng = np.random.default_rng(20260910)
    maximum_residual = 0.0
    for _ in range(samples):
        period = int(rng.integers(4, 14))
        rows = int(rng.integers(2, period + 1))
        classes = int(rng.integers(2, min(6, period + 1)))
        depths = np.sort(rng.uniform(0.0, 4.0, size=classes))
        labels = rng.integers(0, classes, size=period)
        direct = direct_excess(labels, depths, rows)
        spectral = symbol_excess(labels, depths, rows)
        maximum_residual = max(maximum_residual, abs(direct - spectral))
    if maximum_residual > 3.0e-9:
        raise AssertionError(maximum_residual)
    print("PASS partial-frame depth symbol identity")
    print(f"  random configurations={samples}")
    print(f"  maximum direct/spectral residual={maximum_residual:.3e}")


def check_bank_collapse(samples: int) -> None:
    rng = np.random.default_rng(20260911)
    maximum_residual = 0.0
    for _ in range(samples):
        period = int(rng.integers(8, 30))
        classes = int(rng.integers(2, 6))
        depths = np.sort(rng.uniform(0.0, 5.0, size=classes))
        labels = rng.integers(0, classes, size=period)
        ratios = np.sort(rng.uniform(0.35, 1.0, size=4))[::-1]
        ratios[0] = 1.0
        row_counts = np.maximum(2, np.floor(ratios * period).astype(int))
        row_counts[0] = period
        weights = rng.uniform(0.2, 2.0, size=len(row_counts))
        direct = bank_direct(labels, depths, row_counts, weights)
        collapsed = bank_collapsed(labels, depths, row_counts, weights)
        maximum_residual = max(maximum_residual, abs(direct - collapsed))
    if maximum_residual > 1.0e-8:
        raise AssertionError(maximum_residual)
    print("PASS nested-support bank collapse to one moment channel per frequency")
    print(f"  random scale banks={samples}")
    print(f"  maximum direct/collapsed residual={maximum_residual:.3e}")


def check_low_frequency_three_depth_barrier() -> None:
    depths = np.array([0.0, 1.4, 3.0], dtype=float)
    ratios = np.array([1.0, 0.75, 0.6, 0.45], dtype=float)
    weights = np.ones(len(ratios), dtype=float)
    z = endpoint_null(depths)
    endpoint_residual = np.linalg.norm(
        np.vstack([np.ones(len(depths)), np.cosh(depths)]) @ z
    )
    if endpoint_residual > 2.0e-12:
        raise AssertionError(endpoint_residual)

    thetas = np.array([1.0e-2, 3.0e-3, 1.0e-3, 3.0e-4, 1.0e-4])
    ratios_out = np.array(
        [
            channel_energy_for_vector(z, depths, theta, ratios, weights) / theta
            for theta in thetas
        ]
    )
    if not np.all(ratios_out[1:] < ratios_out[:-1]) or ratios_out[-1] > 1.0e-5:
        raise AssertionError((thetas, ratios_out))
    print("PASS source-compatible low-frequency three-depth barrier")
    print("  one full support plus any fixed proper nested supports still has one endpoint moment")
    for theta, value in zip(thetas, ratios_out):
        print(f"  theta={theta:.1e}: combined Q/theta={value:.3e}")


def check_channel_collinearity() -> None:
    period = 120
    frequency = 3
    theta = frequency / period
    depths = np.array([0.0, 0.7, 1.9, 4.0], dtype=float)
    row_counts = np.array([120, 90, 72, 54])
    channel = np.cosh(theta * depths)
    rows = []
    for count in row_counts:
        if frequency < count:
            rows.append(math.sqrt(count - frequency) * channel)
    matrix = np.vstack(rows)
    singular = np.linalg.svd(matrix, compute_uv=False)
    numerical_rank = int(np.sum(singular > 1.0e-11 * singular[0]))
    if numerical_rank != 1:
        raise AssertionError((singular, numerical_rank))
    print("PASS nested-scale channel collinearity")
    print(f"  master frequency={frequency}/{period}; numerical channel rank={numerical_rank}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=100)
    args = parser.parse_args()

    check_partial_symbol(args.samples)
    check_bank_collapse(args.samples)
    check_channel_collinearity()
    check_low_frequency_three_depth_barrier()
    print(
        "BOUNDARY: ideal nested partial Fourier frames only; smooth taper, tails, "
        "prime-side simultaneous bounds, and actual zeta-zero transfer remain open."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
