#!/usr/bin/env python3
"""Deterministic checks for A-RH-RTD-0002.

The script checks:
1. the arbitrary-threshold simple-zero envelope numerically on a dense grid;
2. the exact Fourier symbol of the sampled sinc-squared kernel;
3. the ideal lattice two-scale bound, including the exact lambda=3/4 constants;
4. a finite Toeplitz clock-multiplicity model;
5. the fixed-width trapezoid-taper Parseval defect bound.

It does not compute zeta zeros and does not prove the analytic extraction of a
near-extremal zeta configuration into the ideal lattice model.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import math

import numpy as np


TOL = 5e-10


def k_c(c: float, m: float) -> float:
    return c * c - max(c - m, 0.0) ** 2


def beta_c(c: float) -> float:
    return k_c(c, 1.0) - c * c / 2.0


def threshold_numerator(c: float, kappa: float) -> float:
    return 2.0 * c - c * c / 2.0 - kappa


def check_threshold_envelope(kappa: float, grid: int) -> None:
    if not (1.0 <= kappa < 2.0):
        raise ValueError("the checked simple-zero regime is 1 <= kappa < 2")

    cs = np.linspace(1e-4, 6.0, grid)
    max_violation = -math.inf
    best_ratio = -math.inf
    best_c = math.nan

    for c in cs:
        beta = beta_c(float(c))
        numerator = threshold_numerator(float(c), kappa)
        max_violation = max(max_violation, numerator - (2.0 - kappa) * beta)
        if beta > 1e-12:
            ratio = numerator / beta
            if ratio > best_ratio:
                best_ratio = ratio
                best_c = float(c)

        for m in range(2, 80):
            if k_c(float(c), float(m)) > c * c * m / 2.0 + 2e-11:
                raise AssertionError(f"k_c(m) envelope failed at c={c}, m={m}")

    if max_violation > 2e-9:
        raise AssertionError(f"threshold envelope violated by {max_violation}")
    if abs(best_ratio - (2.0 - kappa)) > 2e-5:
        raise AssertionError((best_ratio, 2.0 - kappa))
    if abs(best_c - 2.0) > 3e-3:
        raise AssertionError(f"dense-grid optimizer did not locate c=2: c={best_c}")

    print("PASS arbitrary-threshold envelope")
    print(f"  kappa={kappa:.12g}")
    print(f"  dense-grid best c={best_c:.7f}")
    print(f"  best ratio={best_ratio:.12f}; target 2-kappa={2-kappa:.12f}")
    print(f"  max pointwise envelope violation={max_violation:.3e}")


def sinc_sq_symbol(lam: float, frequency: float) -> float:
    """DTFT symbol of n -> sinc(lam*n)^2, frequency in cycles."""
    centered = ((frequency + 0.5) % 1.0) - 0.5
    value = 0.0
    # For 1/2 <= lam <= 1 only the aliases -1,0,1 can contribute.
    for shift in range(-2, 3):
        distance = abs(centered + shift)
        if distance < lam:
            value += (1.0 / lam) * (1.0 - distance / lam)
    return value


def symbol_minimum(lam: float) -> float:
    if not (0.5 <= lam <= 1.0):
        raise ValueError("closed formula used only for 1/2 <= lambda <= 1")
    return (2.0 * lam - 1.0) / (lam * lam)


def ideal_simple_bound(lam: float) -> float:
    omega = symbol_minimum(lam)
    return 1.0 - lam / (3.0 * omega)


def check_symbol_and_exact_optimum(grid: int) -> None:
    lambdas = np.linspace(0.5001, 1.0, grid)
    best_bound = -math.inf
    best_lam = math.nan
    worst_symbol_error = 0.0

    for lam in lambdas:
        freqs = np.linspace(-0.5, 0.5, 2001)
        numeric_min = min(sinc_sq_symbol(float(lam), float(f)) for f in freqs)
        closed_min = symbol_minimum(float(lam))
        worst_symbol_error = max(worst_symbol_error, abs(numeric_min - closed_min))
        bound = ideal_simple_bound(float(lam))
        if bound > best_bound:
            best_bound = bound
            best_lam = float(lam)

    if worst_symbol_error > TOL:
        raise AssertionError(f"symbol minimum mismatch {worst_symbol_error}")
    if abs(best_lam - 0.75) > 2e-4:
        raise AssertionError(f"unexpected optimizer lambda={best_lam}")
    if abs(best_bound - 23.0 / 32.0) > 2e-7:
        raise AssertionError((best_bound, 23.0 / 32.0))

    lam = Fraction(3, 4)
    omega = Fraction(8, 9)
    kappa = Fraction(19, 12)
    variance_cap = Fraction(9, 32)
    simple_bound = Fraction(23, 32)
    extremal_gap = Fraction(5, 108)

    assert Fraction(1, 1) / lam + lam / 3 == kappa
    assert (2 * lam - 1) / (lam * lam) == omega
    assert (kappa - Fraction(1, 1) / lam) / omega == variance_cap
    assert 1 - variance_cap == simple_bound
    assert Fraction(1, 1) / lam + omega / 3 - kappa == extremal_gap

    print("PASS sampled-sinc symbol and ideal two-scale optimum")
    print(f"  max numeric-vs-closed symbol-min error={worst_symbol_error:.3e}")
    print("  exact lambda=3/4 constants:")
    print("    omega_lambda = 8/9")
    print("    prime-side kappa = 19/12")
    print("    variance cap = 9/32")
    print("    ideal simple lower bound = 23/32")
    print("    exact clock-extremizer second-moment gap = 5/108")


def clock_pattern(blocks: int) -> np.ndarray:
    # Four simple sites, one double/tight-pair site and one empty site.
    # Total multiplicity per six sites is six.
    return np.tile(np.asarray([1, 1, 1, 1, 2, 0], dtype=float), blocks)


def toeplitz_clock_moments(lam: float, blocks: int) -> tuple[float, float, float, float]:
    multiplicities = clock_pattern(blocks)
    occupied = np.flatnonzero(multiplicities > 0)
    weights = multiplicities[occupied]
    differences = occupied[:, None] - occupied[None, :]
    gram = np.sqrt(weights)[:, None] * np.sinc(lam * differences) * np.sqrt(weights)[None, :]

    total = float(np.sum(multiplicities))
    trace_ratio = float(np.trace(gram).real / total)
    frobenius_ratio = float(np.vdot(gram, gram).real / total)
    simple_ratio = float(np.count_nonzero(multiplicities == 1) / total)
    distinct_ratio = float(np.count_nonzero(multiplicities > 0) / total)
    return trace_ratio, frobenius_ratio, simple_ratio, distinct_ratio


def check_clock_model(blocks: int) -> None:
    trace_1, frob_1, simple, distinct = toeplitz_clock_moments(1.0, blocks)
    if abs(trace_1 - 1.0) > TOL:
        raise AssertionError(trace_1)
    if abs(frob_1 - 4.0 / 3.0) > TOL:
        raise AssertionError(frob_1)
    if abs(simple - 2.0 / 3.0) > TOL:
        raise AssertionError(simple)
    if abs(distinct - 5.0 / 6.0) > TOL:
        raise AssertionError(distinct)

    lam = 0.75
    trace_lam, frob_lam, _, _ = toeplitz_clock_moments(lam, blocks)
    kappa = 1.0 / lam + lam / 3.0
    universal_clock_lower = 1.0 / lam + symbol_minimum(lam) / 3.0
    # A finite Toeplitz block has boundary error. The periodic/infinite lower
    # bound is the target; the concrete periodic pattern is numerically above it.
    if frob_lam + 5.0 / blocks < universal_clock_lower:
        raise AssertionError((frob_lam, universal_clock_lower))
    if frob_lam <= kappa:
        raise AssertionError((frob_lam, kappa))

    print("PASS finite clock-multiplicity model")
    print(f"  blocks={blocks}; matrix atoms={5*blocks}")
    print(f"  lambda=1: trace/N={trace_1:.12f}, frob^2/N={frob_1:.12f}")
    print(f"  simple/N={simple:.12f}, distinct/N={distinct:.12f}")
    print(f"  lambda=3/4: trace/N={trace_lam:.12f}")
    print(f"  lambda=3/4: frob^2/N={frob_lam:.12f}")
    print(f"  prime-side upper constant 19/12={kappa:.12f}")
    print(f"  arrangement-free infinite-symbol lower 44/27={universal_clock_lower:.12f}")


def circulant_quadratic_form(multiplicities: np.ndarray, lam: float) -> float:
    dimension = len(multiplicities)
    spectrum = np.asarray(
        [sinc_sq_symbol(lam, k / dimension) for k in range(dimension)],
        dtype=float,
    )
    transform = np.fft.fft(multiplicities)
    return float(np.sum(spectrum * np.abs(transform) ** 2).real / dimension)


def check_arrangement_free_bound(blocks: int, permutations: int, seed: int) -> None:
    rng = np.random.default_rng(seed)
    base = clock_pattern(blocks)
    dimension = len(base)
    total = float(np.sum(base))
    variance = float(np.sum((base - 1.0) ** 2))
    lam = 0.75
    lower = dimension / lam + symbol_minimum(lam) * variance
    minimum_margin = math.inf

    for _ in range(permutations):
        sample = base.copy()
        rng.shuffle(sample)
        quadratic = circulant_quadratic_form(sample, lam)
        minimum_margin = min(minimum_margin, quadratic - lower)
        if quadratic < lower - 2e-8:
            raise AssertionError((quadratic, lower))

    assert abs(total - dimension) < TOL
    assert abs(variance / dimension - 1.0 / 3.0) < TOL

    print("PASS arrangement-free circulant lower bound")
    print(f"  seed={seed}; permutations={permutations}; dimension={dimension}")
    print(f"  minimum observed margin={minimum_margin:.3e}")


def trapezoid_parseval_energy(length: Fraction, width: Fraction) -> Fraction:
    """Exact E = L*int(phi^4)/(int(phi^2))^2 - 1 for linear edge ramps."""
    if not (2 * width < length):
        raise ValueError("need 2w < L")
    integral_phi2 = length - Fraction(4, 3) * width
    integral_phi4 = length - Fraction(8, 5) * width
    return length * integral_phi4 / (integral_phi2 * integral_phi2) - 1


def check_fixed_width_taper_scaling() -> None:
    previous = None
    for length_int in (50, 100, 200, 500, 1000):
        length = Fraction(length_int, 1)
        width = Fraction(1, 1)
        energy = trapezoid_parseval_energy(length, width)
        generic_bound = 2 * width / (length - 2 * width)
        if not (0 <= energy <= generic_bound):
            raise AssertionError((length, energy, generic_bound))
        if previous is not None and not (energy < previous):
            raise AssertionError("fixed-width Parseval energy did not decrease")
        previous = energy

    print("PASS fixed-width taper Parseval scaling")
    print("  E_phi = L*int(phi^4)/(int(phi^2))^2 - 1")
    print("  explicit linear-ramp E_phi decreases as O(1/L)")
    print("  general plateau bound E_phi <= 2w/(L-2w)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kappa", type=float, default=4.0 / 3.0)
    parser.add_argument("--grid", type=int, default=20001)
    parser.add_argument("--blocks", type=int, default=80)
    parser.add_argument("--permutations", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260829)
    args = parser.parse_args()

    check_threshold_envelope(args.kappa, args.grid)
    check_symbol_and_exact_optimum(max(5001, args.grid // 2))
    check_clock_model(args.blocks)
    check_arrangement_free_bound(args.blocks, args.permutations, args.seed)
    check_fixed_width_taper_scaling()

    print(
        "BOUNDARY: PASS checks the finite/algebraic and ideal-lattice formulas only; "
        "it does not extract an actual zeta-zero configuration into the ideal lattice model."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
