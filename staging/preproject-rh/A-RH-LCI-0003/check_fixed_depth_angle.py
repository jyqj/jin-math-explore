#!/usr/bin/env python3
"""Checks for fixed-depth block-angle collapse.

Finite ideal polyphase calculations only; no zeta-zero theorem.
"""

from __future__ import annotations

import argparse
import math
from typing import Iterable

import numpy as np


def fourier_matrix(period: int) -> np.ndarray:
    rows = np.arange(period, dtype=float)
    residues = np.arange(period, dtype=float)
    return np.exp(2j * math.pi * np.outer(rows, residues) / period) / math.sqrt(period)


def phase_points(period: int, phase: float | None = None) -> np.ndarray:
    if phase is None:
        phase = -0.5 + 0.5 / period
    return phase + np.arange(period, dtype=float) / period


def multiplier_values(period: int, depth: float, phase: float | None = None):
    points = phase_points(period, phase)
    c = np.cosh(depth * points)
    if abs(depth) < 1.0e-14:
        d = points.copy()
        q = points.copy()
        qmax = 0.5
    else:
        d = np.sinh(depth * points) / depth
        q = np.tanh(depth * points) / depth
        qmax = math.tanh(depth / 2.0) / depth
    return points, c, d, q, qmax


def sets_for_blocks(blocks: int):
    period = 6 * blocks
    pairs = tuple(range(blocks))
    empties = tuple(range(3 * blocks, 4 * blocks))
    simples = tuple(r for r in range(period) if r not in pairs and r not in empties)
    return period, pairs, empties, simples


def spaces(period, pairs, empties, depth, phase=None):
    F = fourier_matrix(period)
    simples = tuple(r for r in range(period) if r not in pairs and r not in empties)
    _, c, d, _, _ = multiplier_values(period, depth, phase)
    FA = F[:, pairs]
    FS = F[:, simples]
    positive = np.column_stack((FS, c[:, None] * FA))
    negative = d[:, None] * FA
    return F, FA, FS, positive, negative


def actual_angle_data(period, pairs, empties, depth, phase=None):
    _, _, _, positive, negative = spaces(period, pairs, empties, depth, phase)
    qpos, _ = np.linalg.qr(positive)
    residual = negative - qpos @ (qpos.conj().T @ negative)
    gram = negative.conj().T @ negative
    schur = residual.conj().T @ residual
    eigenvalues, eigenvectors = np.linalg.eigh((gram + gram.conj().T) / 2.0)
    inverse_sqrt = (
        eigenvectors
        @ np.diag(1.0 / np.sqrt(eigenvalues))
        @ eigenvectors.conj().T
    )
    normalized = inverse_sqrt @ schur @ inverse_sqrt
    angles = np.linalg.eigvalsh((normalized + normalized.conj().T) / 2.0)
    angles = np.maximum(angles, 0.0)
    average = float(np.linalg.norm(residual, "fro") ** 2 / np.linalg.norm(negative, "fro") ** 2)
    return angles, average


def cyclic_variation(values: np.ndarray) -> float:
    return float(sum(abs(values[(j + 1) % len(values)] - values[j]) for j in range(len(values))))


def leakage_and_constructed(period, pairs, empties, depth, phase=None):
    F, FA, FS, _, negative = spaces(period, pairs, empties, depth, phase)
    _, c, _, q, qmax = multiplier_values(period, depth, phase)
    projection_a = FA @ FA.conj().T

    H = FA.conj().T @ (q[:, None] * FA)
    pair_approximation = c[:, None] * (FA @ H)
    raw = negative - pair_approximation
    constructed = raw - FS @ (FS.conj().T @ raw)

    leakage = (np.eye(period) - projection_a) @ (q[:, None] * FA)
    variation = cyclic_variation(q)
    count = len(pairs)
    leakage_bound = variation**2 * (math.log(count) + 2.0) / 8.0

    denominator_bound = count * (period * period - 1.0) / (12.0 * period * period)
    cmax = math.cosh(depth / 2.0)
    theorem_bound = (
        3.0
        * cmax**2
        * (4.0 * qmax) ** 2
        * period**2
        * (math.log(count) + 2.0)
        / (2.0 * count * (period * period - 1.0))
    )
    constructed_ratio = float(
        np.linalg.norm(constructed, "fro") ** 2 / np.linalg.norm(negative, "fro") ** 2
    )

    return {
        "variation": variation,
        "variation_bound": 4.0 * qmax,
        "leakage_sq": float(np.linalg.norm(leakage, "fro") ** 2),
        "leakage_bound": leakage_bound,
        "negative_sq": float(np.linalg.norm(negative, "fro") ** 2),
        "negative_lower": denominator_bound,
        "constructed_ratio": constructed_ratio,
        "theorem_bound": theorem_bound,
    }


def full_fiber_matrix(period, pairs, empties, depth, phase=None):
    if depth <= 0.0:
        raise ValueError("positive depth required for Vandermonde formula")
    F = fourier_matrix(period)
    simples = tuple(r for r in range(period) if r not in pairs and r not in empties)
    points, c, d, _, _ = multiplier_values(period, depth, phase)
    return np.column_stack((F[:, simples], c[:, None] * F[:, pairs], d[:, None] * F[:, pairs]))


def vandermonde_logdet(period, pairs, empties, depth):
    if depth <= 0.0:
        raise ValueError("positive depth required")
    omega = np.exp(2j * math.pi / period)
    simples = tuple(r for r in range(period) if r not in pairs and r not in empties)
    nodes = [omega**r for r in simples]
    nodes.extend(math.exp(depth / period) * omega**p for p in pairs)
    nodes.extend(math.exp(-depth / period) * omega**p for p in pairs)

    result = -0.5 * period * math.log(period) - len(pairs) * math.log(2.0 * depth)
    for left in range(period):
        for right in range(left + 1, period):
            result += math.log(abs(nodes[right] - nodes[left]))
    return result


def check_vandermonde(samples: int) -> None:
    rng = np.random.default_rng(20260901)
    maximum_error = 0.0
    for _ in range(samples):
        period = int(rng.integers(6, 25))
        count = int(rng.integers(1, max(2, period // 3)))
        residues = rng.choice(period, size=2 * count, replace=False)
        pairs = tuple(int(v) for v in residues[:count])
        empties = tuple(int(v) for v in residues[count:])
        depth = float(rng.uniform(0.1, 4.0))
        observed = float(np.linalg.slogdet(full_fiber_matrix(period, pairs, empties, depth))[1])
        predicted = vandermonde_logdet(period, pairs, empties, depth)
        maximum_error = max(maximum_error, abs(observed - predicted))
    if maximum_error > 2.0e-7:
        raise AssertionError(maximum_error)
    print("PASS arbitrary-depth generalized Vandermonde determinant")
    print(f"  random configurations={samples}")
    print(f"  maximum log-determinant residual={maximum_error:.3e}")


def check_leakage_bounds(max_blocks: int, depths: Iterable[float]) -> None:
    maximum_constructed_minus_actual = 0.0
    print("PASS fixed-depth Fourier-leakage angle theorem")
    for depth in depths:
        last_actual = None
        print(f"  normalized depth a={depth:g}")
        print("    P      eta_min       actual_avg   constructed   theorem_bound")
        for blocks in range(1, max_blocks + 1):
            period, pairs, empties, _ = sets_for_blocks(blocks)
            record = leakage_and_constructed(period, pairs, empties, depth)
            angles, actual_average = actual_angle_data(period, pairs, empties, depth)

            if record["variation"] > record["variation_bound"] + 2.0e-13:
                raise AssertionError(("variation", depth, period, record))
            if record["leakage_sq"] > record["leakage_bound"] + 2.0e-12:
                raise AssertionError(("leakage", depth, period, record))
            if record["negative_sq"] + 2.0e-12 < record["negative_lower"]:
                raise AssertionError(("denominator", depth, period, record))
            if record["constructed_ratio"] > record["theorem_bound"] + 2.0e-12:
                raise AssertionError(("theorem", depth, period, record))
            if actual_average > record["constructed_ratio"] + 3.0e-11:
                raise AssertionError(("projection", depth, period, actual_average, record))
            if angles[0] > actual_average + 3.0e-11:
                raise AssertionError(("minimum/average", depth, period, angles[0], actual_average))

            maximum_constructed_minus_actual = max(
                maximum_constructed_minus_actual,
                record["constructed_ratio"] - actual_average,
            )
            last_actual = float(angles[0])
            print(
                f"    {period:3d}  {angles[0]:.3e}  {actual_average:.3e}  "
                f"{record['constructed_ratio']:.3e}  {record['theorem_bound']:.3e}"
            )
        if last_actual is None:
            raise AssertionError("no block sizes tested")

    print(f"  max constructed-average slack={maximum_constructed_minus_actual:.3e}")
    print("  theorem bound is coarse but decays as O_a(log P/P) for fixed depth")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=80)
    parser.add_argument("--max-blocks", type=int, default=8)
    parser.add_argument("--depths", type=float, nargs="*", default=(0.0, 0.5, 1.0, 2.0, 4.0))
    args = parser.parse_args()

    check_vandermonde(args.samples)
    check_leakage_bounds(args.max_blocks, args.depths)
    print(
        "BOUNDARY: finite ideal periodic fibers and deterministic checks only; "
        "no source-level weighted trace or zeta theorem is proved."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
