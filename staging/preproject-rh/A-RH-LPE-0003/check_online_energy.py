#!/usr/bin/env python3
"""Deterministic checks for the A-RH-LPE-0003 on-line energy reduction.

The checker samples finite complex atom systems and Hermitian pair forms. It
checks algebraic identities already derived in the accompanying note. Random
finite testing is not proof and says nothing about asymptotic zeta matrices.
"""

from __future__ import annotations

import argparse
import math

import numpy as np


TOL = 2e-8


def frobenius_sq(matrix: np.ndarray) -> float:
    return float(np.vdot(matrix, matrix).real)


def jordan_parts(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    values, vectors = np.linalg.eigh(matrix)
    positive = (vectors * np.maximum(values, 0.0)) @ vectors.conj().T
    negative = (vectors * np.maximum(-values, 0.0)) @ vectors.conj().T
    return positive, negative, values


def g2(value: float) -> float:
    return value * value - 2.0 * value - max(value - 2.0, 0.0) ** 2


def k2(value: float) -> float:
    return 4.0 - max(2.0 - value, 0.0) ** 2


def one_trial(rng: np.random.Generator, dimension: int, atoms: int) -> tuple[float, bool]:
    vectors = rng.normal(size=(dimension, atoms)) + 1j * rng.normal(
        size=(dimension, atoms)
    )
    vectors /= math.sqrt(dimension)
    multiplicities = rng.integers(1, 5, size=atoms)

    p_matrix = np.zeros((dimension, dimension), dtype=complex)
    loads = []
    for index in range(atoms):
        vector = vectors[:, index]
        multiplicity = int(multiplicities[index])
        p_matrix += multiplicity * np.outer(vector, vector.conj())
        loads.append(float(multiplicity * np.vdot(vector, vector).real))
    loads = np.asarray(loads)

    random_matrix = rng.normal(size=(dimension, dimension)) + 1j * rng.normal(
        size=(dimension, dimension)
    )
    q_matrix = (random_matrix + random_matrix.conj().T) / (3.0 * math.sqrt(dimension))

    q_positive, q_negative, q_values = jordan_parts(q_matrix)
    positive_projection = np.zeros_like(q_matrix)
    positive_values, positive_vectors = np.linalg.eigh(q_matrix)
    mask = positive_values > 1e-10
    if np.any(mask):
        positive_projection = positive_vectors[:, mask] @ positive_vectors[:, mask].conj().T
    positive_rank = int(np.count_nonzero(mask))
    budget = positive_rank

    shifted_positive, shifted_negative, _ = jordan_parts(
        p_matrix - 2.0 * np.eye(dimension)
    )
    # shifted_negative = (2I-P)_+
    a_matrix = shifted_positive
    b_matrix = shifted_negative

    p_values = np.linalg.eigvalsh(p_matrix)
    off_diagonal = frobenius_sq(p_matrix) - float(np.sum(loads**2))
    schur_defect = float(np.sum([g2(value) for value in p_values])) - float(
        np.sum([g2(value) for value in loads])
    )
    load_leakage = float(np.sum(np.maximum(loads - 2.0, 0.0) ** 2))

    identity_rhs = schur_defect + frobenius_sq(a_matrix) - load_leakage
    identity_error = abs(off_diagonal - identity_rhs)
    if identity_error > TOL * max(1.0, abs(off_diagonal), abs(identity_rhs)):
        raise AssertionError((off_diagonal, identity_rhs, identity_error))

    combined = p_matrix + q_matrix
    total_defect = (
        float(np.sum([k2(value) for value in loads]))
        + 4.0 * budget
        - (4.0 * float(np.trace(combined).real) - frobenius_sq(combined))
    )

    decomposition = (
        schur_defect
        + 2.0 * float(np.trace(p_matrix @ q_positive).real)
        + frobenius_sq(q_negative - a_matrix)
        + 2.0 * float(np.trace(b_matrix @ q_negative).real)
        + frobenius_sq(q_positive - 2.0 * positive_projection)
        + 4.0 * (budget - positive_rank)
    )
    decomposition_error = abs(total_defect - decomposition)
    if decomposition_error > TOL * max(1.0, abs(total_defect), abs(decomposition)):
        raise AssertionError((total_defect, decomposition, decomposition_error))
    if min(schur_defect, total_defect, decomposition) < -TOL:
        raise AssertionError((schur_defect, total_defect, decomposition))

    sharp_upper = total_defect + (
        math.sqrt(frobenius_sq(q_negative)) + math.sqrt(max(total_defect, 0.0))
    ) ** 2
    coarse_upper = 2.0 * frobenius_sq(q_negative) + 3.0 * total_defect
    if off_diagonal > sharp_upper + TOL * max(1.0, sharp_upper):
        raise AssertionError((off_diagonal, sharp_upper))
    if off_diagonal > coarse_upper + TOL * max(1.0, coarse_upper):
        raise AssertionError((off_diagonal, coarse_upper))

    converse = 0.5 * max(off_diagonal - 3.0 * total_defect, 0.0)
    if frobenius_sq(q_negative) + TOL < converse:
        raise AssertionError((frobenius_sq(q_negative), converse))

    return max(identity_error, decomposition_error, off_diagonal - coarse_upper), bool(
        np.any(loads > 2.0 + 1e-8)
    )


def exact_orthogonal_model() -> None:
    # Four simple atoms and one double atom in five orthogonal directions.
    p_matrix = np.diag([1.0, 1.0, 1.0, 1.0, 2.0])
    loads = np.asarray([1.0, 1.0, 1.0, 1.0, 2.0])
    off_diagonal = frobenius_sq(p_matrix) - float(np.sum(loads**2))
    total_defect = float(np.sum([k2(value) for value in loads])) - (
        4.0 * float(np.trace(p_matrix).real) - frobenius_sq(p_matrix)
    )
    if abs(off_diagonal) > TOL or abs(total_defect) > TOL:
        raise AssertionError((off_diagonal, total_defect))
    print("PASS exact 4-simple/1-double orthogonal saturation model")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=1000)
    parser.add_argument("--dimension", type=int, default=6)
    parser.add_argument("--atoms", type=int, default=9)
    parser.add_argument("--seed", type=int, default=20260829)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    worst = 0.0
    saw_large_load = False
    for _ in range(args.trials):
        error, large_load = one_trial(rng, args.dimension, args.atoms)
        worst = max(worst, error)
        saw_large_load = saw_large_load or large_load
    if not saw_large_load:
        raise AssertionError("test suite did not exercise atom loads above two")

    exact_orthogonal_model()
    print("PASS on-line energy identity and parent defect decomposition")
    print("PASS E_off <= Delta+(||Q_-||+sqrt(Delta))^2")
    print("PASS E_off <= 2||Q_-||^2+3 Delta and converse lower bound")
    print(
        f"  trials={args.trials}; dimension={args.dimension}; atoms={args.atoms}; "
        f"seed={args.seed}; worst checked residual={worst:.3e}"
    )
    print(
        "BOUNDARY: finite random regression tests only; the parent theorem, "
        "asymptotic near-saturation, and all zeta applications remain unverified."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
