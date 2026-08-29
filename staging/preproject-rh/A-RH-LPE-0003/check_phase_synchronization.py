#!/usr/bin/env python3
"""Deterministic finite checks for A-RH-LPE-0003.

These tests cover weighted phase synchronization, complete-block extraction,
overlap stitching, finite-Toeplitz boundary corrections, random partitions,
and the disconnected/low-gap countermodels. They do not construct or verify
the analytic Zeta23 extraction hypotheses.
"""

from __future__ import annotations

import argparse
import math

import numpy as np


TOL = 2e-9


def td(value):
    """Distance to the nearest integer."""
    array = np.asarray(value, dtype=float)
    result = np.abs(array - np.round(array))
    return float(result) if np.isscalar(value) else result


def laplacian(edges):
    edges = np.asarray(edges, dtype=float).copy()
    if edges.ndim != 2 or edges.shape[0] != edges.shape[1]:
        raise ValueError("edges must be square")
    if not np.allclose(edges, edges.T, atol=1e-12):
        raise ValueError("edges must be symmetric")
    if np.min(edges) < -TOL:
        raise ValueError("edges must be nonnegative")
    np.fill_diagonal(edges, 0.0)
    return np.diag(np.sum(edges, axis=1)) - edges


def gap(weights, edges):
    """Best lambda in Var_w(f) <= Dirichlet(f)/lambda."""
    weights = np.asarray(weights, dtype=float)
    normalized = (
        np.diag(1.0 / np.sqrt(weights))
        @ laplacian(edges)
        @ np.diag(1.0 / np.sqrt(weights))
    )
    eigenvalues = np.linalg.eigvalsh(normalized)
    if np.count_nonzero(eigenvalues <= 1e-10) != 1:
        return 0.0
    return float(eigenvalues[eigenvalues > 1e-10][0])


def phase(positions, weights):
    mean = np.sum(weights * np.exp(2j * math.pi * positions))
    return 0.0 if abs(mean) <= 1e-14 else float(np.angle(mean) / (2 * math.pi))


def energy(positions, edges):
    differences = positions[:, None] - positions[None, :]
    return float(0.5 * np.sum(edges * np.square(np.sinc(differences))))


def phase_bound(positions, weights, edges):
    lam = gap(weights, edges)
    if lam <= 0:
        raise ValueError("connected graph required")
    support = np.asarray(edges) > 1e-14
    np.fill_diagonal(support, False)
    differences = np.abs(positions[:, None] - positions[None, :])
    radius = float(np.max(differences[support]))
    tau = phase(positions, weights)
    loss = float(np.sum(weights * np.square(td(positions - tau))))
    bound = math.pi**2 * radius**2 * energy(positions, edges) / (2 * lam)
    return loss, bound, lam, tau


def random_graph_checks(rng, trials, size):
    worst = -math.inf
    for _ in range(trials):
        increments = rng.integers(1, 4, size=size - 1)
        positions = np.concatenate(([0], np.cumsum(increments))).astype(float)
        positions += rng.normal(0, 0.12, size)
        weights = rng.uniform(0.4, 2.0, size)
        edges = np.zeros((size, size))
        for i in range(size - 1):
            edges[i, i + 1] = edges[i + 1, i] = rng.uniform(0.4, 1.8)
        for i in range(size):
            for j in range(i + 2, min(size, i + 5)):
                if rng.random() < 0.35:
                    edges[i, j] = edges[j, i] = rng.uniform(0.1, 1.0)
        loss, bound, _, tau = phase_bound(positions, weights, edges)
        worst = max(worst, loss - bound)
        if loss > bound + TOL * max(1.0, bound):
            raise AssertionError((loss, bound))
        eta = rng.uniform(0.05, 0.45)
        bad = np.sum(weights[td(positions - tau) > eta])
        if bad > bound / eta**2 + TOL * max(1.0, bound / eta**2):
            raise AssertionError((bad, bound / eta**2))
    print(f"PASS local phase synchronization; worst loss-bound={worst:.3e}")


def complete_block_checks(rng, trials, size):
    gap_error = 0.0
    worst = -math.inf
    for _ in range(trials):
        diameter = rng.uniform(0.5, 6.0)
        positions = rng.uniform(-diameter / 2, diameter / 2, size)
        weights = rng.uniform(0.1, 2.0, size)
        edges = np.outer(weights, weights)
        np.fill_diagonal(edges, 0.0)
        lam = gap(weights, edges)
        gap_error = max(gap_error, abs(lam - np.sum(weights)))
        loss, bound, _, _ = phase_bound(positions, weights, edges)
        worst = max(worst, loss - bound)
        if loss > bound + TOL * max(1.0, bound):
            raise AssertionError((loss, bound))
    positions = np.arange(size, dtype=float)
    weights = np.ones(size)
    edges = np.outer(weights, weights)
    np.fill_diagonal(edges, 0.0)
    loss, bound, lam, _ = phase_bound(positions, weights, edges)
    if max(abs(loss), abs(bound), abs(lam - size)) > 2e-8:
        raise AssertionError((loss, bound, lam))
    print(
        "PASS complete-block specialization; "
        f"gap error={gap_error:.3e}; worst loss-bound={worst:.3e}"
    )


def overlap_checks(rng, trials, points):
    worst = -math.inf
    for _ in range(trials):
        weights = rng.uniform(0.1, 2.0, points)
        positions = rng.normal(0, 3, points)
        tau, sigma = rng.uniform(-0.5, 0.5, 2)
        e1 = np.sum(weights * np.square(td(positions - tau)))
        e2 = np.sum(weights * np.square(td(positions - sigma)))
        lhs = np.sum(weights) * td(tau - sigma) ** 2
        rhs = 2 * (e1 + e2)
        worst = max(worst, lhs - rhs)
        if lhs > rhs + TOL * max(1.0, rhs):
            raise AssertionError((lhs, rhs))
    print(f"PASS overlap phase stitching; worst lhs-rhs={worst:.3e}")


def toeplitz_checks(rng, trials, size, alpha=0.75):
    omega = (2 * alpha - 1) / alpha**2
    rho = omega / 2
    worst = -math.inf
    for _ in range(trials):
        d = int(rng.integers(max(4, size // 2), max(5, 3 * size)))
        m = rng.integers(0, 4, d).astype(float)
        if np.sum(m) == 0:
            m[0] = 1
        indices = np.arange(d)
        matrix = np.square(np.sinc(alpha * (indices[:, None] - indices[None, :])))
        total = float(np.sum(m))
        mean = total / d
        variance = float(np.sum(np.square(m - mean)))
        form = float(m @ matrix @ m)
        missing = 1 / alpha - np.sum(matrix, axis=1)
        B = float(np.sum(missing))
        C = float(np.dot(missing, missing))
        lower = (
            (omega - rho) * variance
            + total**2 / (alpha * d)
            - mean**2 * (B + C / rho)
        )
        worst = max(worst, lower - form)
        if lower > form + TOL * max(1.0, form):
            raise AssertionError((lower, form))
        Bmax = 2 / (math.pi**2 * alpha**2) * (3 + math.log(max(1, d - 1)))
        Cmax = 1 / (9 * alpha**4) + 2 / (3 * math.pi**2 * alpha**4)
        if B > Bmax + 1e-8 or C > Cmax + 1e-8:
            raise AssertionError((B, Bmax, C, Cmax))
    print(f"PASS Toeplitz boundary correction; worst lower-form={worst:.3e}")


def kernel_stability_checks(rng, trials, size, alpha=0.75):
    c = math.pi * alpha
    hnorm = (
        3 * c
        + 16 / c * (math.pi**2 / 6 - 1)
        + 32 / c**2 * (1.2020569031595942 - 1)
    )
    coefficient = 2 * hnorm
    if coefficient >= 25.226:
        raise AssertionError(coefficient)
    worst = -math.inf
    for _ in range(trials):
        eta = rng.uniform(1e-4, 0.24)
        cells = np.sort(rng.choice(np.arange(4 * size), size, replace=False))
        occupancies = rng.integers(0, 4, size)
        if np.sum(occupancies) == 0:
            occupancies[0] = 1
        atom_cells = np.repeat(cells, occupancies)
        deviations = rng.uniform(-eta, eta, len(atom_cells))
        positions = atom_cells.astype(float) + deviations
        actual = float(np.sum(np.square(np.sinc(alpha * (
            positions[:, None] - positions[None, :]
        )))))
        lattice = float(np.sum(np.square(np.sinc(alpha * (
            atom_cells[:, None] - atom_cells[None, :]
        )))))
        second_moment = float(np.sum(np.square(occupancies)))
        bound = coefficient * eta * second_moment
        violation = abs(actual - lattice) - bound
        worst = max(worst, violation)
        if violation > TOL * max(1.0, bound):
            raise AssertionError((actual, lattice, bound))
    print(
        "PASS approximate-cell kernel stability; "
        f"C={coefficient:.9f}; worst |delta Q|-bound={worst:.3e}"
    )


def partition_loss(positions, weights, length, shift, eta):
    all_edges = np.outer(weights, weights)
    np.fill_diagonal(all_edges, 0.0)
    total_energy = energy(positions, all_edges)
    block_ids = np.floor((positions - shift) / length).astype(int)
    loss = bad = 0.0
    for block_id in np.unique(block_ids):
        mask = block_ids == block_id
        xp, wp = positions[mask], weights[mask]
        if len(xp) == 1:
            local_loss, tau = 0.0, float(xp[0])
        else:
            edges = np.outer(wp, wp)
            np.fill_diagonal(edges, 0.0)
            local_loss, _, _, tau = phase_bound(xp, wp, edges)
        loss += local_loss
        bad += float(np.sum(wp[td(xp - tau) > eta]))
    return loss, bad, math.pi**2 * length**2 * total_energy / 2


def boundary_mass(positions, weights, length, shift, radius):
    residue = np.mod(positions - shift, length)
    distance = np.minimum(residue, length - residue)
    return float(np.sum(weights[distance < radius]))


def partition_checks(rng, trials, size):
    worst_loss = worst_bad = -math.inf
    for _ in range(trials):
        labels = np.sort(rng.choice(np.arange(8 * size), size, replace=False))
        positions = labels.astype(float) + rng.normal(0, 0.04, size)
        weights = rng.integers(1, 4, size).astype(float)
        length = rng.uniform(6, 14)
        shift = rng.uniform(0, length)
        eta = rng.uniform(0.08, 0.22)
        loss, bad, bound = partition_loss(positions, weights, length, shift, eta)
        worst_loss = max(worst_loss, loss - bound)
        worst_bad = max(worst_bad, bad - bound / eta**2)
        if loss > bound + TOL * max(1.0, bound):
            raise AssertionError((loss, bound))
        if bad > bound / eta**2 + TOL * max(1.0, bound / eta**2):
            raise AssertionError((bad, bound / eta**2))
        radius = min(rng.uniform(0.2, 1.5), length / 4)
        shifts = np.linspace(0, length, 2001, endpoint=False)
        minimum = min(boundary_mass(positions, weights, length, u, radius) for u in shifts)
        average_bound = 2 * radius * np.sum(weights) / length
        if minimum > average_bound + max(2 * np.max(weights), 0.01 * np.sum(weights)):
            raise AssertionError((minimum, average_bound))
    print(
        "PASS random-partition extraction; "
        f"worst loss={worst_loss:.3e}; worst bad-mass={worst_bad:.3e}"
    )


def countermodels(max_power):
    positions = np.array([0.0, 1.0, 0.5, 1.5])
    weights = np.ones(4)
    edges = np.zeros((4, 4))
    edges[0, 1] = edges[1, 0] = 1
    edges[2, 3] = edges[3, 2] = 1
    if abs(energy(positions, edges)) > TOL or gap(weights, edges) != 0:
        raise AssertionError("disconnected model failed")
    phases = np.linspace(0, 1, 20001, endpoint=False)
    best = min(np.sum(np.square(td(positions - tau))) for tau in phases)
    if abs(best - 0.25) > 2e-4:
        raise AssertionError(best)
    print(f"PASS disconnected two-coset model; best global loss={best:.12f}")

    rows = []
    for power in range(4, max_power + 1):
        n = 2**power
        positions = np.array([j + j / n for j in range(n)], dtype=float)
        weights = np.ones(n)
        edges = np.zeros((n, n))
        for j in range(n - 1):
            edges[j, j + 1] = edges[j + 1, j] = 1
        loss, bound, lam, _ = phase_bound(positions, weights, edges)
        rows.append((n, lam, energy(positions, edges), loss, bound))
    for first, second in zip(rows, rows[1:]):
        if not (
            second[1] < 0.35 * first[1]
            and second[2] < 0.65 * first[2]
            and second[3] > 1.7 * first[3]
        ):
            raise AssertionError((first, second))
    n, lam, e, loss, bound = rows[-1]
    print(
        "PASS low-gap path scaling; "
        f"n={n}; gap={lam:.3e}; energy={e:.3e}; "
        f"loss={loss:.3e}; bound={bound:.3e}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=250)
    parser.add_argument("--size", type=int, default=24)
    parser.add_argument("--overlap-points", type=int, default=16)
    parser.add_argument("--seed", type=int, default=20260829)
    parser.add_argument("--max-power", type=int, default=9)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    random_graph_checks(rng, args.trials, args.size)
    complete_block_checks(rng, args.trials, args.size)
    overlap_checks(rng, args.trials, args.overlap_points)
    toeplitz_checks(rng, args.trials, args.size)
    kernel_stability_checks(rng, args.trials, args.size)
    partition_checks(rng, args.trials, args.size)
    countermodels(args.max_power)
    print(
        "BOUNDARY: finite graph, phase, ideal-sinc and Toeplitz checks only; "
        "no Zeta23 extraction hypothesis or zeta-zero theorem is verified."
    )


if __name__ == "__main__":
    main()
