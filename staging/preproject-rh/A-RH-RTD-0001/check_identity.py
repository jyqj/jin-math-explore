#!/usr/bin/env python3
"""Deterministic numerical and exact checks for A-RH-RTD-0001.

This script checks finite-dimensional algebraic identities only. It does not
compute zeta zeros and does not verify the analytic hypotheses of Zeta23.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

import numpy as np


TOL = 2e-8


def hermitian_part(matrix: np.ndarray) -> np.ndarray:
    return (matrix + matrix.conj().T) / 2


def frob_sq(matrix: np.ndarray) -> float:
    return float(np.real(np.vdot(matrix, matrix)))


def real_trace(matrix: np.ndarray) -> float:
    return float(np.real(np.trace(matrix)))


def spectral_part(matrix: np.ndarray, positive: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    values, vectors = np.linalg.eigh(hermitian_part(matrix))
    clipped = np.maximum(values, 0.0) if positive else np.maximum(-values, 0.0)
    part = (vectors * clipped) @ vectors.conj().T
    support = clipped > 1e-10
    projection = (vectors[:, support] @ vectors[:, support].conj().T) if np.any(support) else np.zeros_like(matrix)
    return hermitian_part(part), projection, clipped


def positive_shift_part(matrix: np.ndarray, shift: float) -> np.ndarray:
    values, vectors = np.linalg.eigh(hermitian_part(matrix))
    clipped = np.maximum(values - shift, 0.0)
    return hermitian_part((vectors * clipped) @ vectors.conj().T)


def negative_shift_part(matrix: np.ndarray, shift: float) -> np.ndarray:
    values, vectors = np.linalg.eigh(hermitian_part(matrix))
    clipped = np.maximum(shift - values, 0.0)
    return hermitian_part((vectors * clipped) @ vectors.conj().T)


def scalar_g(c: float, x: float) -> float:
    return x * x - c * x - max(x - c, 0.0) ** 2


def scalar_k(c: float, x: float) -> float:
    return c * c - max(c - x, 0.0) ** 2


def trace_g(c: float, matrix: np.ndarray) -> float:
    values = np.linalg.eigvalsh(hermitian_part(matrix))
    return float(sum(scalar_g(c, float(value)) for value in values))


@dataclass(frozen=True)
class AtomicPSD:
    matrix: np.ndarray
    multiplicities: np.ndarray
    vectors: list[np.ndarray]
    loads: np.ndarray


def random_atomic_psd(rng: np.random.Generator, dimension: int, atoms: int) -> AtomicPSD:
    vectors: list[np.ndarray] = []
    multiplicities: list[int] = []
    matrix = np.zeros((dimension, dimension), dtype=np.complex128)
    loads: list[float] = []
    for _ in range(atoms):
        raw = rng.normal(size=dimension) + 1j * rng.normal(size=dimension)
        raw /= np.linalg.norm(raw)
        radius = rng.uniform(0.15, 1.0)
        vector = radius * raw
        multiplicity = int(rng.integers(1, 5))
        matrix += multiplicity * np.outer(vector, vector.conj())
        vectors.append(vector)
        multiplicities.append(multiplicity)
        loads.append(multiplicity * float(np.vdot(vector, vector).real))
    return AtomicPSD(
        matrix=hermitian_part(matrix),
        multiplicities=np.asarray(multiplicities, dtype=float),
        vectors=vectors,
        loads=np.asarray(loads, dtype=float),
    )


def random_hermitian(rng: np.random.Generator, dimension: int) -> np.ndarray:
    raw = rng.normal(size=(dimension, dimension)) + 1j * rng.normal(size=(dimension, dimension))
    return hermitian_part(raw / math.sqrt(dimension))


def defect_and_decomposition(atomic: AtomicPSD, q: np.ndarray, c: float, b_slack: int = 0) -> tuple[float, float, dict[str, float]]:
    p = atomic.matrix
    q_plus, pi_plus, plus_values = spectral_part(q, positive=True)
    q_minus, _, _ = spectral_part(q, positive=False)
    rank_plus = int(np.count_nonzero(plus_values > 1e-10))
    b = rank_plus + b_slack

    a_c = positive_shift_part(p, c)
    b_c = negative_shift_part(p, c)
    j_c = trace_g(c, p) - float(sum(scalar_g(c, float(x)) for x in atomic.loads))

    lhs = 2.0 * c * real_trace(p + q) - frob_sq(p + q)
    direct = float(sum(scalar_k(c, float(x)) for x in atomic.loads)) + c * c * b - lhs

    terms = {
        "schur_defect": j_c,
        "positive_overlap": 2.0 * real_trace(p @ q_plus),
        "negative_match": frob_sq(q_minus - a_c),
        "negative_below_threshold_overlap": 2.0 * real_trace(b_c @ q_minus),
        "positive_quantization": frob_sq(q_plus - c * pi_plus),
        "unused_positive_inertia": c * c * (b - rank_plus),
    }
    decomposed = float(sum(terms.values()))
    return direct, decomposed, terms


def check_random_identities(seed: int, trials: int) -> None:
    rng = np.random.default_rng(seed)
    worst_identity = 0.0
    worst_nonnegative = 0.0
    worst_compatibility = 0.0
    worst_two_parameter = 0.0

    for _ in range(trials):
        dimension = int(rng.integers(2, 9))
        atoms = int(rng.integers(dimension, 2 * dimension + 3))
        atomic1 = random_atomic_psd(rng, dimension, atoms)
        atomic2 = random_atomic_psd(rng, dimension, atoms)
        q1 = random_hermitian(rng, dimension)
        q2 = random_hermitian(rng, dimension)
        c = float(rng.uniform(0.6, 4.0))

        delta1, decomp1, terms1 = defect_and_decomposition(atomic1, q1, c, int(rng.integers(0, 3)))
        delta2, decomp2, terms2 = defect_and_decomposition(atomic2, q2, c, int(rng.integers(0, 3)))
        worst_identity = max(worst_identity, abs(delta1 - decomp1), abs(delta2 - decomp2))
        worst_nonnegative = min(worst_nonnegative, min(terms1.values()), min(terms2.values()))

        a1 = positive_shift_part(atomic1.matrix, c)
        a2 = positive_shift_part(atomic2.matrix, c)
        q1_minus, _, _ = spectral_part(q1, positive=False)
        q2_minus, _, _ = spectral_part(q2, positive=False)
        separation = max(math.sqrt(frob_sq(a1 - a2)) - math.sqrt(frob_sq(q1_minus - q2_minus)), 0.0)
        compatibility_rhs = 0.5 * separation * separation
        worst_compatibility = max(worst_compatibility, compatibility_rhs - (delta1 + delta2))

        c_small = float(rng.uniform(0.4, 2.0))
        c_large = c_small + float(rng.uniform(0.2, 2.0))
        _, _, plus_values = spectral_part(q1, positive=True)
        rank_plus = int(np.count_nonzero(plus_values > 1e-10))
        b = rank_plus + int(rng.integers(0, 3))
        d_small, _, _ = defect_and_decomposition(atomic1, q1, c_small, b - rank_plus)
        d_large, _, _ = defect_and_decomposition(atomic1, q1, c_large, b - rank_plus)
        ac = positive_shift_part(atomic1.matrix, c_small)
        ad = positive_shift_part(atomic1.matrix, c_large)
        two_parameter_rhs = 0.5 * frob_sq(ac - ad) + 0.5 * (c_large - c_small) ** 2 * b
        worst_two_parameter = max(worst_two_parameter, two_parameter_rhs - (d_small + d_large))

    if worst_identity > TOL:
        raise AssertionError(f"defect identity residual too large: {worst_identity}")
    if worst_nonnegative < -TOL:
        raise AssertionError(f"a purported nonnegative term was negative: {worst_nonnegative}")
    if worst_compatibility > TOL:
        raise AssertionError(f"dual-compression compatibility failed by {worst_compatibility}")
    if worst_two_parameter > TOL:
        raise AssertionError(f"two-parameter compatibility failed by {worst_two_parameter}")

    print(f"PASS random identities: seed={seed}, trials={trials}")
    print(f"  max |direct-decomposition| = {worst_identity:.3e}")
    print(f"  minimum component term     = {worst_nonnegative:.3e}")
    print(f"  max compatibility violation= {worst_compatibility:.3e}")
    print(f"  max two-parameter violation= {worst_two_parameter:.3e}")


def check_exact_no_go_model() -> None:
    eigenvalues = [1, 1, 1, 1, 2]
    total_multiplicity = sum(eigenvalues)
    simple_count = sum(value == 1 for value in eigenvalues)
    distinct_count = len(eigenvalues)
    frob = sum(value * value for value in eigenvalues)
    trace = total_multiplicity

    c2_lhs = 4 * trace - frob - 2 * total_multiplicity
    c3_lhs = 6 * trace - frob - 3 * total_multiplicity

    assert total_multiplicity == 6
    assert simple_count == 4
    assert distinct_count == 5
    assert c2_lhs == simple_count
    assert c3_lhs == 2 * distinct_count
    assert 3 * simple_count == 2 * total_multiplicity
    assert 6 * distinct_count == 5 * total_multiplicity

    print("PASS exact no-go model: diag(1,1,1,1,2), Q=0")
    print("  simple / multiplicity = 4/6 = 2/3")
    print("  distinct / multiplicity = 5/6")
    print("  c=2 and c=3 scalar certificates are simultaneously exact")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260829)
    parser.add_argument("--trials", type=int, default=500)
    args = parser.parse_args()
    check_exact_no_go_model()
    check_random_identities(args.seed, args.trials)
    print("BOUNDARY: these checks are finite-dimensional numerical/exact checks, not a proof about zeta zeros.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
