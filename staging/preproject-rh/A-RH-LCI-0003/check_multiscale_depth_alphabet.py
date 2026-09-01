#!/usr/bin/env python3
"""Deterministic checks for finite-alphabet aligned multiscale depth rigidity.

The checker verifies ideal finite-period Fourier identities, generalized-cosh
Vandermonde nondegeneracy, the finite-channel rank barrier, the low-frequency
interface-coercivity barrier, and a three-depth/two-scale coercive example.
It does not prove an aligned-scale transfer for actual Zeta23 matrices.
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


def pair_atom(period: int, residue: int, depth: float, scale: float) -> np.ndarray:
    fourier = fourier_matrix(period)
    vector = fourier[:, residue : residue + 1]
    projection = vector @ vector.conj().T
    points = centered_points(period)
    c = np.diag(np.cosh(scale * depth * points))
    s = np.diag(np.sinh(scale * depth * points))
    return 2.0 * (c @ projection @ c - s @ projection @ s)


def direct_defect(labels: np.ndarray, depths: np.ndarray, scale: float) -> float:
    period = len(labels)
    matrix = np.zeros((period, period), dtype=complex)
    for residue, label in enumerate(labels):
        matrix += pair_atom(period, residue, float(depths[label]), scale)
    matrix = (matrix + matrix.conj().T) / 2.0
    return float(np.linalg.norm(matrix - 2.0 * np.eye(period), "fro") ** 2)


def indicator_fourier(labels: np.ndarray, classes: int, frequency: int) -> np.ndarray:
    period = len(labels)
    residues = np.arange(period, dtype=float)
    phase = np.exp(2j * math.pi * residues * frequency / period)
    return np.array(
        [np.mean((labels == label) * phase) for label in range(classes)],
        dtype=complex,
    )


def channel_quadratic(
    z: np.ndarray,
    depths: np.ndarray,
    scales: np.ndarray,
    theta: float,
    weights: np.ndarray | None = None,
) -> float:
    if weights is None:
        weights = np.ones(len(scales), dtype=float)
    total = 0.0
    for scale, weight in zip(scales, weights):
        first = np.dot(z, np.cosh(scale * theta * depths))
        second = np.dot(z, np.cosh(scale * (1.0 - theta) * depths))
        total += 4.0 * weight * (
            (1.0 - theta) * abs(first) ** 2 + theta * abs(second) ** 2
        )
    return float(total)


def symbol_defect(labels: np.ndarray, depths: np.ndarray, scale: float) -> float:
    period = len(labels)
    total = 0.0
    for frequency in range(1, period):
        theta = frequency / period
        z = indicator_fourier(labels, len(depths), frequency)
        total += channel_quadratic(
            z,
            depths,
            np.array([scale], dtype=float),
            theta,
        )
    return period * total


def tangent_basis(classes: int) -> np.ndarray:
    projector = np.eye(classes) - np.ones((classes, classes)) / classes
    eigenvalues, eigenvectors = np.linalg.eigh(projector)
    return eigenvectors[:, eigenvalues > 0.5]


def restricted_symbol(
    depths: np.ndarray,
    scales: np.ndarray,
    theta: float,
    weights: np.ndarray | None = None,
) -> np.ndarray:
    classes = len(depths)
    if weights is None:
        weights = np.ones(len(scales), dtype=float)
    matrix = np.zeros((classes, classes), dtype=float)
    for scale, weight in zip(scales, weights):
        first = np.cosh(scale * theta * depths)
        second = np.cosh(scale * (1.0 - theta) * depths)
        matrix += 4.0 * weight * (
            (1.0 - theta) * np.outer(first, first)
            + theta * np.outer(second, second)
        )
    basis = tangent_basis(classes)
    return basis.T @ matrix @ basis


def cosh_vandermonde(depths: np.ndarray, scales: np.ndarray) -> np.ndarray:
    parameters = np.concatenate(([0.0], scales))
    return np.cosh(np.outer(parameters, depths))


def boundary_energy(labels: np.ndarray, classes: int) -> float:
    vectors = np.eye(classes)[labels]
    return float(np.sum((np.roll(vectors, -1, axis=0) - vectors) ** 2))


def combined_symbol_defect(
    labels: np.ndarray,
    depths: np.ndarray,
    scales: np.ndarray,
    weights: np.ndarray | None = None,
) -> float:
    period = len(labels)
    total = 0.0
    for frequency in range(1, period):
        z = indicator_fourier(labels, len(depths), frequency)
        total += channel_quadratic(
            z,
            depths,
            scales,
            frequency / period,
            weights,
        )
    return period * total


def check_exact_symbol(samples: int) -> None:
    rng = np.random.default_rng(20260907)
    maximum_residual = 0.0
    for _ in range(samples):
        period = int(rng.integers(3, 11))
        classes = int(rng.integers(2, min(6, period + 1)))
        depths = np.sort(rng.uniform(0.0, 4.0, size=classes))
        labels = rng.integers(0, classes, size=period)
        scale = float(rng.uniform(0.2, 1.0))
        direct = direct_defect(labels, depths, scale)
        spectral = symbol_defect(labels, depths, scale)
        maximum_residual = max(maximum_residual, abs(direct - spectral))
    if maximum_residual > 2.0e-9:
        raise AssertionError(maximum_residual)
    print("PASS arbitrary finite-alphabet one-scale symbol identity")
    print(f"  random configurations={samples}")
    print(f"  maximum direct/spectral residual={maximum_residual:.3e}")


def check_cosh_total_positivity(samples: int) -> None:
    rng = np.random.default_rng(20260908)
    smallest_scaled_det = math.inf
    for _ in range(samples):
        classes = int(rng.integers(2, 6))
        depths = np.sort(rng.uniform(0.0, 3.0, size=classes))
        depths += np.arange(classes) * 0.25
        scales = np.sort(rng.uniform(0.15, 1.0, size=classes - 1))
        scales += np.arange(classes - 1) * 0.08
        matrix = cosh_vandermonde(depths, scales)
        sign, logabs = np.linalg.slogdet(matrix)
        if sign <= 0.0 or not np.isfinite(logabs):
            raise AssertionError((depths, scales, sign, logabs))
        row_norms = np.linalg.norm(matrix, axis=1)
        scaled_det = math.exp(logabs - float(np.sum(np.log(row_norms))))
        smallest_scaled_det = min(smallest_scaled_det, scaled_det)
    print("PASS generalized cosh-Vandermonde positivity samples")
    print(f"  random matrices={samples}")
    print(f"  smallest row-normalized determinant={smallest_scaled_det:.3e}")


def check_pointwise_rank_barrier() -> None:
    depths = np.array([0.0, 0.8, 1.9, 3.7], dtype=float)
    scales = np.array([0.73], dtype=float)
    theta = 0.37
    channel = np.vstack(
        [
            np.ones(len(depths)),
            np.cosh(scales[0] * theta * depths),
            np.cosh(scales[0] * (1.0 - theta) * depths),
        ]
    )
    _, _, vh = np.linalg.svd(channel)
    z = vh[-1].conj()
    z /= np.linalg.norm(z)
    residual = np.linalg.norm(channel @ z)
    energy = channel_quadratic(z, depths, scales, theta)
    if residual > 2.0e-12 or energy > 2.0e-22:
        raise AssertionError((residual, energy))
    print("PASS exact finite-channel rank barrier")
    print("  one scale, four depth classes: a nonzero invisible tangent direction exists")
    print(f"  channel residual={residual:.3e}; quadratic energy={energy:.3e}")


def check_low_frequency_barrier() -> None:
    depths = np.array([0.0, 0.7, 1.8, 3.2], dtype=float)
    scales = np.array([0.55, 0.9], dtype=float)
    endpoint = np.vstack(
        [np.ones(len(depths))]
        + [np.cosh(scale * depths) for scale in scales]
    )
    _, _, vh = np.linalg.svd(endpoint)
    z = vh[-1].conj()
    z /= np.linalg.norm(z)
    if np.linalg.norm(endpoint @ z) > 2.0e-12:
        raise AssertionError("failed to construct endpoint-null tangent direction")

    thetas = np.array([1.0e-2, 3.0e-3, 1.0e-3, 3.0e-4, 1.0e-4])
    ratios = np.array(
        [channel_quadratic(z, depths, scales, theta) / theta for theta in thetas]
    )
    if not np.all(ratios[1:] < ratios[:-1]) or ratios[-1] > 1.0e-5:
        raise AssertionError((thetas, ratios))
    print("PASS low-frequency first-order coercivity barrier")
    print("  two scales, four depths: Q_theta(z)/theta -> 0 along an endpoint-null direction")
    for theta, ratio in zip(thetas, ratios):
        print(f"  theta={theta:.1e}: Q/theta={ratio:.3e}")


def check_three_depth_two_scale_coercivity(theta_grid: int, samples: int) -> None:
    depths = np.array([0.0, 1.5, 3.0], dtype=float)
    scales = np.array([0.35, 1.0], dtype=float)
    weights = np.array([1.0, 1.0], dtype=float)

    thetas = np.unique(
        np.concatenate(
            (
                np.geomspace(1.0e-8, 0.1, theta_grid // 3),
                np.linspace(0.1, 0.9, theta_grid),
                1.0 - np.geomspace(1.0e-8, 0.1, theta_grid // 3),
            )
        )
    )
    minimum_ratio = math.inf
    argmin = None
    for theta in thetas:
        restricted = restricted_symbol(depths, scales, float(theta), weights)
        eigenvalue = float(np.linalg.eigvalsh((restricted + restricted.T) / 2.0)[0])
        ratio = eigenvalue / min(theta, 1.0 - theta)
        if ratio < minimum_ratio:
            minimum_ratio = ratio
            argmin = float(theta)
    if minimum_ratio <= 1.0e-7:
        raise AssertionError((minimum_ratio, argmin))

    coercivity = 0.45 * minimum_ratio
    rng = np.random.default_rng(20260909)
    smallest_slack = math.inf
    for _ in range(samples):
        period = int(rng.integers(4, 80))
        labels = rng.integers(0, len(depths), size=period)
        defect = combined_symbol_defect(labels, depths, scales, weights)
        boundary = boundary_energy(labels, len(depths))
        lower = coercivity * boundary / (4.0 * math.pi)
        smallest_slack = min(smallest_slack, defect - lower)
        if defect + 2.0e-9 < lower:
            raise AssertionError((period, defect, lower))

    print("PASS three-depth/two-scale first-order coercivity regression")
    print(f"  sampled inf Q_theta/(d(theta)||z||^2)={minimum_ratio:.6e} at theta={argmin:.6f}")
    print(f"  conservative interface coefficient={coercivity/(4*math.pi):.6e}")
    print(f"  random label configurations={samples}; minimum slack={smallest_slack:.3e}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=120)
    parser.add_argument("--theta-grid", type=int, default=1200)
    args = parser.parse_args()

    check_exact_symbol(args.samples)
    check_cosh_total_positivity(args.samples)
    check_pointwise_rank_barrier()
    check_low_frequency_barrier()
    check_three_depth_two_scale_coercivity(args.theta_grid, args.samples)
    print(
        "BOUNDARY: aligned ideal pair-lattice scales and finite depth alphabets only; "
        "no actual Zeta23 cross-scale transfer or unconditional zeta theorem is proved."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
