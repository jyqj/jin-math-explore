#!/usr/bin/env python3
"""Deterministic checks for A-RH-RTD-0002.

The script checks:
1. the arbitrary-threshold simple-zero envelope;
2. the sampled-sinc-squared Fourier symbol;
3. the normalized two-scale occupancy theorem at reference density theta;
4. the exact alpha=3/4 gain and error budget;
5. finite circulant and Toeplitz clock models;
6. the same-scale fixed-width taper collapse.

It does not compute zeta zeros and does not prove the analytic extraction of an
actual near-extremal zeta configuration into an integer occupancy model.
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
        c = float(c)
        beta = beta_c(c)
        numerator = threshold_numerator(c, kappa)
        max_violation = max(max_violation, numerator - (2.0 - kappa) * beta)
        if beta > 1e-12:
            ratio = numerator / beta
            if ratio > best_ratio:
                best_ratio = ratio
                best_c = c

        for m in range(2, 80):
            if k_c(c, float(m)) > c * c * m / 2.0 + 2e-11:
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


def sinc_sq_symbol(alpha: float, frequency: float) -> float:
    """DTFT of n -> sinc(alpha*n)^2, with frequency in cycles."""
    centered = ((frequency + 0.5) % 1.0) - 0.5
    value = 0.0
    for shift in range(-2, 3):
        distance = abs(centered + shift)
        if distance < alpha:
            value += (1.0 / alpha) * (1.0 - distance / alpha)
    return value


def symbol_minimum(alpha: float) -> float:
    if not (0.5 <= alpha <= 1.0):
        raise ValueError("closed formula used only for 1/2 <= alpha <= 1")
    return (2.0 * alpha - 1.0) / (alpha * alpha)


def same_scale_bound(theta: float) -> float:
    return 2.0 - 1.0 / theta - theta / 3.0


def two_scale_bound(theta: float, alpha: float, error: float = 0.0) -> float:
    """Normalized occupancy bound.

    theta=d/N is the reference-cell density, alpha is the relative shorter
    scale, and error is the shorter-scale quadratic-form slack per unit N.
    """
    if not (0.0 < theta <= 1.0):
        raise ValueError("need 0 < theta <= 1")
    omega = symbol_minimum(alpha)
    return (
        theta
        - (1.0 - theta) ** 2 / theta
        - alpha * theta / (3.0 * omega)
        - error / omega
    )


def theta_threshold_for_two_thirds() -> float:
    return (64.0 - 4.0 * math.sqrt(94.0)) / 27.0


def check_symbol_and_normalized_optimum(grid: int) -> None:
    alphas = np.linspace(0.5001, 1.0, grid)
    worst_symbol_error = 0.0
    best_alpha = math.nan
    best_penalty = math.inf

    for alpha in alphas:
        alpha = float(alpha)
        freqs = np.linspace(-0.5, 0.5, 2001)
        numeric_min = min(sinc_sq_symbol(alpha, float(f)) for f in freqs)
        closed_min = symbol_minimum(alpha)
        worst_symbol_error = max(worst_symbol_error, abs(numeric_min - closed_min))
        penalty = alpha / (3.0 * closed_min)
        if penalty < best_penalty:
            best_penalty = penalty
            best_alpha = alpha

    if worst_symbol_error > TOL:
        raise AssertionError(f"symbol minimum mismatch {worst_symbol_error}")
    if abs(best_alpha - 0.75) > 2e-4:
        raise AssertionError(f"unexpected optimizer alpha={best_alpha}")

    alpha = Fraction(3, 4)
    omega = Fraction(8, 9)
    assert (2 * alpha - 1) / (alpha * alpha) == omega
    assert alpha / (3 * omega) == Fraction(9, 32)

    # Exact symbolic bookkeeping with rational theta values.
    for theta in (
        Fraction(1, 1),
        Fraction(99, 100),
        Fraction(19, 20),
        Fraction(15, 16),
    ):
        b = theta - (1 - theta) ** 2 / theta - alpha * theta / (3 * omega)
        h = 2 - 1 / theta - theta / 3
        assert b - h == Fraction(5, 96) * theta
        # Every unit of quadratic-form error costs 1/omega=9/8.
        assert 1 / omega == Fraction(9, 8)
        # Error below 5 theta / 108 preserves a strict gain over H(theta).
        assert Fraction(9, 8) * Fraction(5, 108) * theta == Fraction(5, 96) * theta

    if abs(two_scale_bound(1.0, 0.75) - 23.0 / 32.0) > TOL:
        raise AssertionError("theta=1 limit must be 23/32")

    threshold = theta_threshold_for_two_thirds()
    if not two_scale_bound(threshold + 1e-7, 0.75) > 2.0 / 3.0:
        raise AssertionError("theta threshold should be sufficient")
    if not two_scale_bound(threshold - 1e-7, 0.75) < 2.0 / 3.0:
        raise AssertionError("theta threshold should be necessary in the ideal formula")

    print("PASS sampled-sinc symbol and normalized two-scale theorem")
    print(f"  max numeric-vs-closed symbol-min error={worst_symbol_error:.3e}")
    print(f"  optimizer alpha={best_alpha:.7f}; exact alpha=3/4")
    print("  omega_3/4=8/9")
    print("  B(theta,3/4,eps)=23 theta/32-(1-theta)^2/theta-(9/8)eps")
    print("  B-H(theta)=5 theta/96-(9/8)eps")
    print("  total error budget preserving the ideal gain: eps < 5 theta/108")
    print(f"  zero-error threshold for B>2/3: theta>{threshold:.12f}")
    print("  theta->1 zero-error limit: 23/32")


def circulant_quadratic_form(multiplicities: np.ndarray, alpha: float) -> float:
    dimension = len(multiplicities)
    spectrum = np.asarray(
        [sinc_sq_symbol(alpha, k / dimension) for k in range(dimension)],
        dtype=float,
    )
    transform = np.fft.fft(multiplicities)
    return float(np.sum(spectrum * np.abs(transform) ** 2).real / dimension)


def check_normalized_occupancy_random(
    trials: int, dimension: int, max_occupancy: int, seed: int
) -> None:
    rng = np.random.default_rng(seed)
    alpha = 0.75
    omega = symbol_minimum(alpha)
    min_margin = math.inf
    max_simple_violation = -math.inf

    for _ in range(trials):
        m = rng.integers(0, max_occupancy + 1, size=dimension).astype(float)
        total = float(np.sum(m))
        if total <= 0:
            continue
        theta = dimension / total
        if theta > 1.0:
            # The intended zeta regime has no more reference cells than total mass.
            continue
        mean = total / dimension
        variance = float(np.sum((m - mean) ** 2))
        quadratic = circulant_quadratic_form(m, alpha)
        lower = total / (alpha * theta) + omega * variance
        margin = quadratic - lower
        min_margin = min(min_margin, margin)
        if margin < -2e-8:
            raise AssertionError((quadratic, lower, theta))

        simple = float(np.count_nonzero(m == 1))
        simple_lower = dimension - float(np.sum((m - 1.0) ** 2))
        max_simple_violation = max(max_simple_violation, simple_lower - simple)
        if simple + TOL < simple_lower:
            raise AssertionError((simple, simple_lower))

    print("PASS finite-circulant normalized occupancy checks")
    print(
        f"  seed={seed}; trials={trials}; dimension={dimension}; "
        f"minimum spectral margin={min_margin:.3e}"
    )
    print(f"  maximum integer-simple inequality violation={max_simple_violation:.3e}")


def clock_pattern(blocks: int) -> np.ndarray:
    return np.tile(np.asarray([1, 1, 1, 1, 2, 0], dtype=float), blocks)


def toeplitz_clock_moments(alpha: float, blocks: int) -> tuple[float, float, float, float]:
    multiplicities = clock_pattern(blocks)
    occupied = np.flatnonzero(multiplicities > 0)
    weights = multiplicities[occupied]
    differences = occupied[:, None] - occupied[None, :]
    gram = (
        np.sqrt(weights)[:, None]
        * np.sinc(alpha * differences)
        * np.sqrt(weights)[None, :]
    )

    total = float(np.sum(multiplicities))
    trace_ratio = float(np.trace(gram).real / total)
    frobenius_ratio = float(np.vdot(gram, gram).real / total)
    simple_ratio = float(np.count_nonzero(multiplicities == 1) / total)
    distinct_ratio = float(np.count_nonzero(multiplicities > 0) / total)
    return trace_ratio, frobenius_ratio, simple_ratio, distinct_ratio


def check_clock_model(blocks: int, permutations: int, seed: int) -> None:
    trace_1, frob_1, simple, distinct = toeplitz_clock_moments(1.0, blocks)
    assert abs(trace_1 - 1.0) <= TOL
    assert abs(frob_1 - 4.0 / 3.0) <= TOL
    assert abs(simple - 2.0 / 3.0) <= TOL
    assert abs(distinct - 5.0 / 6.0) <= TOL

    alpha = 0.75
    _, frob_short, _, _ = toeplitz_clock_moments(alpha, blocks)
    kappa = 1.0 / alpha + alpha / 3.0
    universal_lower = 1.0 / alpha + symbol_minimum(alpha) / 3.0
    assert abs(universal_lower - 44.0 / 27.0) <= TOL
    assert abs(kappa - 19.0 / 12.0) <= TOL
    assert abs(universal_lower - kappa - 5.0 / 108.0) <= TOL
    if frob_short + 5.0 / blocks < universal_lower:
        raise AssertionError((frob_short, universal_lower))
    if frob_short <= kappa:
        raise AssertionError((frob_short, kappa))

    rng = np.random.default_rng(seed)
    base = clock_pattern(blocks)
    dimension = len(base)
    variance = float(np.sum((base - 1.0) ** 2))
    lower = dimension / alpha + symbol_minimum(alpha) * variance
    minimum_margin = math.inf
    for _ in range(permutations):
        sample = base.copy()
        rng.shuffle(sample)
        quadratic = circulant_quadratic_form(sample, alpha)
        minimum_margin = min(minimum_margin, quadratic - lower)
        if quadratic < lower - 2e-8:
            raise AssertionError((quadratic, lower))

    print("PASS Nyquist clock extremizer and sub-Nyquist exclusion")
    print(f"  lambda=1: trace/N={trace_1:.12f}, frob^2/N={frob_1:.12f}")
    print(f"  simple/N={simple:.12f}, distinct/N={distinct:.12f}")
    print(f"  alpha=3/4 Toeplitz frob^2/N={frob_short:.12f}")
    print("  exact infinite-symbol lower=44/27")
    print("  prime-side upper constant=19/12")
    print("  exact arrangement-free margin=5/108")
    print(f"  random-permutation minimum circulant margin={minimum_margin:.3e}")


def trapezoid_parseval_energy(length: Fraction, width: Fraction) -> Fraction:
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

    print("PASS same-scale fixed-width taper collapse check")
    print("  E_phi=L int(phi^4)/(int(phi^2))^2-1=O(1/L)")
    print("  generic plateau bound E_phi<=2w/(L-2w)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kappa", type=float, default=4.0 / 3.0)
    parser.add_argument("--grid", type=int, default=20001)
    parser.add_argument("--blocks", type=int, default=80)
    parser.add_argument("--permutations", type=int, default=200)
    parser.add_argument("--occupancy-trials", type=int, default=500)
    parser.add_argument("--dimension", type=int, default=96)
    parser.add_argument("--max-occupancy", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260829)
    args = parser.parse_args()

    check_threshold_envelope(args.kappa, args.grid)
    check_symbol_and_normalized_optimum(max(5001, args.grid // 2))
    check_normalized_occupancy_random(
        args.occupancy_trials, args.dimension, args.max_occupancy, args.seed
    )
    check_clock_model(args.blocks, args.permutations, args.seed)
    check_fixed_width_taper_scaling()

    print(
        "BOUNDARY: these checks certify finite algebra and ideal lattice formulas only; "
        "they do not extract actual zeta zeros into the occupancy model or control "
        "off-line, taper, grid, and tail errors."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
