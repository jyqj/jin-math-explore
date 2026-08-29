#!/usr/bin/env python3
"""Deterministic exploration for A-RH-XSR-0002.

The exact parts check:
  * arbitrary-threshold c=2 optimality in the first/second-moment model;
  * the universal cyclic critical-lattice Fourier-symbol bound;
  * the ideal rectangular lambda=3/4 consequences
      simple proportion >= 23/32 and distinct proportion >= 55/64;
  * asymptotic sharpness of the continuum of rectangular second moments;
  * the closed-form rectangular cross-scale defect for the period-six
    [2,0,1,1,1,1] (equivalently [1,1,1,1,2,0]) extremal pattern;
  * an explicit period-twelve counterexample to treating the period-six
    optimum as arrangement-universal below lambda=5/6;
  * the three circular period-six arrangements and their stationary point;
  * the ideal single off-line-pair depth penalty.

The optional jitter search is a deterministic finite-period numerical
experiment. It is not a proof and does not model all zeta configurations.
"""

from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence


def kappa(lam: float) -> float:
    return 1.0 / lam + lam / 3.0


def baseline_h(lam: float) -> float:
    return 2.0 - kappa(lam)


def threshold_A(c: float) -> float:
    return 2.0 * c - 1.0 - 0.5 * c * c


def threshold_bound(c: float, kap: float) -> float:
    a = threshold_A(c)
    if a <= 0:
        raise ValueError("threshold coefficient must be positive")
    return 1.0 - (kap - 1.0) / a


def overlap_symbol(lam: float, x: float) -> float:
    """F_lambda(x) for the sampled sinc-squared kernel.

    x is reduced to its distance from the nearest integer, in [0,1/2].
    """
    if not (0.0 < lam <= 1.0):
        raise ValueError("lambda must lie in (0,1]")
    x = abs(x - round(x))
    x = min(x, 1.0 - x)
    return (max(lam - x, 0.0) + max(lam - (1.0 - x), 0.0)) / (lam * lam)


def overlap_symbol_min(lam: float) -> float:
    """Minimum of F_lambda on the nonzero torus for lambda >= 1/2."""
    if not (0.5 <= lam <= 1.0):
        raise ValueError("symbol minimum formula requires lambda in [1/2,1]")
    return (2.0 * lam - 1.0) / (lam * lam)


def universal_variance_cap(lam: float) -> float:
    """Variance cap from the ideal prime-side moment at one scale."""
    fmin = overlap_symbol_min(lam)
    if fmin <= 0:
        return math.inf
    return lam / (3.0 * fmin)


def universal_simple_bound(lam: float) -> float:
    """Integer-occupancy simple proportion forced by one ideal scale."""
    return 1.0 - universal_variance_cap(lam)


def universal_distinct_bound(lam: float) -> float:
    """Integer-occupancy distinct proportion forced by one ideal scale."""
    return 1.0 - 0.5 * universal_variance_cap(lam)


def universal_lattice_gap(lam: float) -> float:
    """Moment contradiction for a putative simple proportion <= 2/3."""
    return overlap_symbol_min(lam) / 3.0 - lam / 3.0


def periodic_spectral_energy(pattern: Sequence[int], lam: float) -> float:
    """Full normalized Frobenius energy for a periodic integer lattice.

    The normalization is by total multiplicity. The DFT convention is
    unnormalized, and the symbol is the exact periodization of sinc^2.
    """
    p = len(pattern)
    total = sum(pattern)
    if total <= 0:
        raise ValueError("pattern must have positive total multiplicity")
    energy = 0.0
    for q in range(p):
        z = sum(
            pattern[n] * complex(
                math.cos(-2.0 * math.pi * q * n / p),
                math.sin(-2.0 * math.pi * q * n / p),
            )
            for n in range(p)
        )
        energy += abs(z) ** 2 * overlap_symbol(lam, q / p)
    return energy / (p * total)


def periodic_spectral_defect(pattern: Sequence[int], lam: float) -> float:
    """Off-diagonal c=2 defect for loads <= 2."""
    total = sum(pattern)
    diagonal = sum(value * value for value in pattern) / total
    return periodic_spectral_energy(pattern, lam) - diagonal


def rectangular_pair_defect(depth: float, multiplicity: int = 1) -> float:
    """Ideal c=2 defect of one orthogonal off-line reflection pair.

    `depth` is y=L*(beta-1/2). The normalized positive/negative eigenvalues
    are m*(S+1) and -m*(S-1), S=sinh(y)/y.
    """
    if multiplicity < 1:
        raise ValueError("multiplicity must be positive")
    s = 1.0 if abs(depth) < 1e-14 else math.sinh(depth) / depth
    m = float(multiplicity)
    return 4.0 * (m - 1.0) ** 2 + 2.0 * m * m * (s * s - 1.0)


def alternating_block_pattern(period: int, active: int) -> tuple[int, ...]:
    """Integer occupancy m=1+d with an alternating active block.

    `active` must be even. The deviation d has active/period variance and
    Fourier mass concentrated near frequency 1/2 as the period grows.
    """
    if period <= 0 or active < 0 or active > period or active % 2:
        raise ValueError("require 0 <= active <= period and active even")
    values = []
    for n in range(period):
        if n < active:
            values.append(2 if n % 2 == 0 else 0)
        else:
            values.append(1)
    assert sum(values) == period
    return tuple(values)


def moment_excess(pattern: Sequence[int], lam: float) -> float:
    """Ideal full energy minus the prime-side kappa(lambda) budget."""
    return periodic_spectral_energy(pattern, lam) - kappa(lam)


def maximum_all_scale_excess(
    pattern: Sequence[int],
    *,
    samples: int = 4000,
) -> tuple[float, float]:
    """Grid approximation to max_{0<lambda<=1} moment excess.

    This is deterministic numerical evidence for the asymptotic sharpness
    construction, not an exact continuum maximization.
    """
    worst = -math.inf
    worst_lam = 0.0
    for j in range(1, samples + 1):
        lam = j / samples
        value = moment_excess(pattern, lam)
        if value > worst:
            worst = value
            worst_lam = lam
    return worst, worst_lam


def stability_constant_upper(lam: float, max_load: int = 2) -> float:
    """Explicit coarse Kadec-neighborhood stability constant.

    It bounds C_{lambda,M} in
      |D_lambda(u)-D_lambda(0)| <= C sqrt(D_1(u))
    for |u_n|<=1/4 and integer loads at most M.
    """
    if not (0.0 < lam <= 1.0) or max_load < 1:
        raise ValueError("invalid lambda or max_load")
    zeta3_upper = 1.202056903159595
    series_bound = (
        9.0 * math.pi**2 / lam**2
        + 252.0 * zeta3_upper / (math.pi * lam**3)
        + 3.0 * math.pi**2 / lam**4
    )
    return math.sqrt(max_load * series_bound)


def balanced_tradeoff_gain(gap: float, constant: float) -> float:
    """min_{x>=0} max{x, gap-constant*sqrt(x)}."""
    if gap <= 0:
        return 0.0
    root = (math.sqrt(constant * constant + 4.0 * gap) - constant) / 2.0
    return root * root


def arrangement_delta(lam: float, distance: int) -> float:
    """Asymptotic c=2 defect per total multiplicity for a period-six pattern.

    There are four simple atoms, one double atom, and one vacant critical
    lattice site. `distance` is the circular distance (1,2,3) between the
    double atom and the vacancy.
    """
    f1 = overlap_symbol(lam, 1.0 / 6.0)
    f2 = overlap_symbol(lam, 1.0 / 3.0)
    f3 = overlap_symbol(lam, 1.0 / 2.0)
    if distance == 1:
        energy = 1.0 / lam + f1 / 18.0 + f2 / 6.0 + f3 / 9.0
    elif distance == 2:
        energy = 1.0 / lam + f1 / 6.0 + f2 / 6.0
    elif distance == 3:
        energy = 1.0 / lam + 2.0 * f1 / 9.0 + f3 / 9.0
    else:
        raise ValueError("distance must be 1, 2, or 3")
    return energy - 4.0 / 3.0


def ideal_gain(lam: float, distance: int = 1) -> float:
    """Idealized improvement over 2/3 in the rectangular period-six model."""
    return baseline_h(lam) + arrangement_delta(lam, distance) - 2.0 / 3.0


def ideal_gain_piecewise(lam: float) -> float:
    """Closed form for the worst period-six circular arrangement."""
    if not (0.5 <= lam <= 1.0):
        raise ValueError("piecewise formula is recorded only on [1/2,1]")
    if lam >= 5.0 / 6.0:
        return (-lam**3 + 2.0 * lam - 1.0) / (3.0 * lam**2)
    if lam >= 2.0 / 3.0:
        return (-36.0 * lam**3 + 66.0 * lam - 31.0) / (108.0 * lam**2)
    return (-36.0 * lam**3 + 48.0 * lam - 19.0) / (108.0 * lam**2)


def bisect_root(func, lo: float, hi: float, iterations: int = 100) -> float:
    flo = func(lo)
    fhi = func(hi)
    if flo == 0:
        return lo
    if fhi == 0:
        return hi
    if flo * fhi > 0:
        raise ValueError("root is not bracketed")
    for _ in range(iterations):
        mid = 0.5 * (lo + hi)
        fmid = func(mid)
        if flo * fmid <= 0:
            hi, fhi = mid, fmid
        else:
            lo, flo = mid, fmid
    return 0.5 * (lo + hi)


def direct_periodic_delta(
    lam: float,
    positions: Sequence[float],
    weights: Sequence[float],
    period: float = 6.0,
    periods: int = 1200,
) -> float:
    """Truncated direct sum for the off-diagonal Gram energy per multiplicity."""
    total = 0.0
    weight_sum = sum(weights)
    for j, xj in enumerate(positions):
        for ell, xell in enumerate(positions):
            coeff = weights[j] * weights[ell]
            if coeff == 0:
                continue
            for n in range(-periods, periods + 1):
                if j == ell and n == 0:
                    continue
                x = xj - xell - period * n
                y = math.pi * lam * x
                kval = 1.0 if abs(y) < 1e-15 else math.sin(y) / y
                total += coeff * kval * kval
    return total / weight_sum


@dataclass(frozen=True)
class JitterResult:
    lam: float
    objective: float
    defect_at_one: float
    second_scale_excess: float
    displacements: tuple[float, ...]


def periodic_objective(
    lam: float,
    displacements: Sequence[float],
    periods: int,
) -> tuple[float, float, float]:
    base = (0.0, 2.0, 3.0, 4.0, 5.0)
    weights = (2.0, 1.0, 1.0, 1.0, 1.0)
    positions = tuple(base[i] + displacements[i] for i in range(5))
    d1 = direct_periodic_delta(1.0, positions, weights, periods=periods)
    dl = direct_periodic_delta(lam, positions, weights, periods=periods)
    penalty = kappa(lam) - 4.0 / 3.0
    excess = dl - penalty
    return max(0.0, d1, excess), d1, excess


def jitter_search(
    lam: float,
    *,
    seed: int,
    starts: int,
    periods: int,
    initial_step: float,
    rounds: int,
) -> JitterResult:
    """Deterministic coordinate search; heuristic only.

    Translation is fixed by setting the displacement of the double atom to 0.
    The remaining four occupied sites move inside [-0.48,0.48].
    """
    rng = random.Random(seed)
    best: tuple[float, tuple[float, ...], float, float] | None = None
    for start in range(starts):
        if start == 0:
            u = [0.0] * 5
        else:
            u = [0.0] + [rng.uniform(-0.3, 0.3) for _ in range(4)]
        step = initial_step
        value, d1, excess = periodic_objective(lam, u, periods)
        for _ in range(rounds):
            improved = False
            candidate_best = (value, tuple(u), d1, excess)
            for idx in range(1, 5):
                for sign in (-1.0, 1.0):
                    v = list(u)
                    v[idx] = max(-0.48, min(0.48, v[idx] + sign * step))
                    cv, cd1, cexcess = periodic_objective(lam, v, periods)
                    if cv + 1e-14 < candidate_best[0]:
                        candidate_best = (cv, tuple(v), cd1, cexcess)
            if candidate_best[0] + 1e-14 < value:
                value, u_tuple, d1, excess = candidate_best
                u = list(u_tuple)
                improved = True
            if not improved:
                step *= 0.5
            if step < 1e-5:
                break
        record = (value, tuple(u), d1, excess)
        if best is None or record[0] < best[0]:
            best = record
    assert best is not None
    return JitterResult(lam, best[0], best[2], best[3], best[1])


def exact_fraction_checks() -> None:
    lam = Fraction(3, 4)
    fmin = Fraction(8, 9)
    variance_cap = lam / (3 * fmin)
    assert variance_cap == Fraction(9, 32)
    assert 1 - variance_cap == Fraction(23, 32)
    assert 1 - variance_cap / 2 == Fraction(55, 64)

    gain = (-36 * lam**3 + 66 * lam - 31) / (108 * lam**2)
    assert gain == Fraction(53, 972)
    assert Fraction(2, 3) + gain == Fraction(701, 972)

    lam_56 = Fraction(5, 6)
    gap_56 = (-lam_56**3 + 2 * lam_56 - 1) / (3 * lam_56**2)
    assert gap_56 == Fraction(19, 450)
    assert Fraction(2, 3) + gap_56 == Fraction(319, 450)

    vals = [arrangement_delta(5.0 / 6.0, d) for d in (1, 2, 3)]
    assert max(vals) - min(vals) < 1e-12


def run_exact_checks() -> None:
    exact_fraction_checks()

    kap = 4.0 / 3.0
    samples = [1.0 + j / 100.0 for j in range(101)]
    bounds = [threshold_bound(c, kap) for c in samples]
    assert max(bounds) <= 2.0 / 3.0 + 1e-12
    assert abs(bounds[-1] - 2.0 / 3.0) < 1e-12

    grid = [0.5001 + j * (0.4999 / 5000) for j in range(5001)]
    best_grid = max(grid, key=universal_simple_bound)
    assert abs(best_grid - 0.75) < 2e-4
    assert abs(universal_simple_bound(0.75) - 23.0 / 32.0) < 1e-12
    assert abs(universal_distinct_bound(0.75) - 55.0 / 64.0) < 1e-12

    golden = (math.sqrt(5.0) - 1.0) / 2.0
    assert universal_lattice_gap(golden) < 2e-15
    for lam in (0.65, 0.70, 0.75, 0.90, 0.99):
        assert universal_lattice_gap(lam) > 0.0

    p12 = (2, 0, 1, 2, 0, 1, 1, 1, 1, 1, 1, 1)
    p12_delta = periodic_spectral_defect(p12, 0.75)
    exact_p12 = (76.0 - 2.0 * math.sqrt(3.0)) / 243.0
    assert abs(p12_delta - exact_p12) < 2e-12
    assert p12_delta + 1e-12 < arrangement_delta(0.75, 1)

    assert abs(rectangular_pair_defect(0.0, 1)) < 1e-15
    for y in (0.1, 0.5, 1.0):
        assert rectangular_pair_defect(y, 1) + 1e-12 >= 2.0 * y * y / 3.0
        assert rectangular_pair_defect(y, 2) >= 4.0

    p64 = alternating_block_pattern(64, 18)
    assert sum(value == 1 for value in p64) == 46
    assert abs(sum((value - 1) ** 2 for value in p64) / 64.0 - 9.0 / 32.0) < 1e-15
    excess64, lam64 = maximum_all_scale_excess(p64, samples=1600)
    assert excess64 < 0.0012
    assert 0.72 < lam64 < 0.78

    c_stab = stability_constant_upper(0.75, 2)
    eta_stab = balanced_tradeoff_gain(universal_lattice_gap(0.75), c_stab)
    assert c_stab < 31.0
    assert eta_stab > 2.0e-6

    for lam in (0.5, 0.6, 2.0 / 3.0, 0.7, 0.75, 5.0 / 6.0, 0.9, 0.95, 1.0):
        assert abs(ideal_gain(lam) - ideal_gain_piecewise(lam)) < 2e-12
        f1 = overlap_symbol(lam, 1.0 / 6.0)
        f2 = overlap_symbol(lam, 1.0 / 3.0)
        f3 = overlap_symbol(lam, 1.0 / 2.0)
        assert f1 + 1e-12 >= f2 >= f3 - 1e-12
        d1, d2, d3 = (arrangement_delta(lam, d) for d in (1, 2, 3))
        assert abs((d2 - d1) - (f1 - f3) / 9.0) < 2e-12
        assert abs((d3 - d1) - (f1 - f2) / 6.0) < 2e-12
        assert d1 <= d2 + 1e-12 and d1 <= d3 + 1e-12

    root_mid = bisect_root(lambda x: 18.0 * x**3 + 33.0 * x - 31.0, 2.0 / 3.0, 5.0 / 6.0)
    root_low = bisect_root(lambda x: 18.0 * x**3 + 24.0 * x - 19.0, 0.5, 2.0 / 3.0)
    candidates = [0.5, root_low, 2.0 / 3.0, root_mid, 5.0 / 6.0, 1.0]
    optimum = max(candidates, key=ideal_gain_piecewise)
    assert abs(optimum - root_mid) < 1e-12

    direct = direct_periodic_delta(
        0.75,
        positions=(0.0, 2.0, 3.0, 4.0, 5.0),
        weights=(2.0, 1.0, 1.0, 1.0, 1.0),
        periods=20000,
    )
    closed = arrangement_delta(0.75, 1)
    assert abs(direct - closed) < 8e-6

    print("PASS exact algebraic/closed-form checks")
    print("  threshold continuum maximum: c=2, bound=2/3 at kappa=4/3")
    print("  universal exact-lattice optimum scale: lambda=3/4")
    print(f"  universal variance cap: {universal_variance_cap(0.75):.12f} = 9/32")
    print(f"  universal simple bound: {universal_simple_bound(0.75):.12f} = 23/32")
    print(f"  universal distinct bound: {universal_distinct_bound(0.75):.12f} = 55/64")
    print("  worst period-six circular arrangement: double adjacent to vacancy")
    print(f"  period-six optimum lambda: {root_mid:.15f}")
    print(f"  period-six optimum gain over 2/3: {ideal_gain_piecewise(root_mid):.15f}")
    print(f"  period-six optimum simple proportion: {2/3 + ideal_gain_piecewise(root_mid):.15f}")
    print(f"  direct-vs-closed residual at lambda=3/4: {abs(direct-closed):.3e}")
    p64 = alternating_block_pattern(64, 18)
    excess64, lam64 = maximum_all_scale_excess(p64, samples=4000)
    print(f"  p=64 alternating-block max all-scale excess: {excess64:.9f} at lambda~{lam64:.6f}")
    c_stab = stability_constant_upper(0.75, 2)
    eta_stab = balanced_tradeoff_gain(universal_lattice_gap(0.75), c_stab)
    print(f"  coarse Kadec stability C(3/4,2): {c_stab:.9f}")
    print(f"  resulting conditional positive gap: {eta_stab:.9e}")


def print_table() -> None:
    print("\nuniversal ideal critical-lattice bound")
    print("lambda      variance_cap  simple_bound  distinct_bound  gap_vs_2/3")
    for lam in (0.99, 0.95, 0.90, 5.0 / 6.0, 0.80, 0.75, 0.70, (math.sqrt(5.0) - 1.0) / 2.0):
        print(
            f"{lam:0.9f}  {universal_variance_cap(lam):0.9f}  "
            f"{universal_simple_bound(lam):0.9f}  "
            f"{universal_distinct_bound(lam):0.9f}  "
            f"{universal_lattice_gap(lam):0.9f}"
        )

    print("\nideal single off-line-pair c=2 defect (multiplicity one)")
    print("depth_y     defect        quadratic_lower")
    for depth in (0.0, 0.1, 0.25, 0.5, 1.0):
        print(
            f"{depth:0.6f}  {rectangular_pair_defect(depth, 1):0.9f}  "
            f"{2.0 * depth * depth / 3.0:0.9f}"
        )

    print("\nrectangular period-six model (stronger but not arrangement-universal below 5/6)")
    print("lambda      delta_min     H(lambda)     ideal_bound   gain")
    for lam in (0.99, 0.97, 0.95, 0.90, 5.0 / 6.0, 0.80, 0.75, 0.728504383258804, 2.0 / 3.0, 0.60, 0.50):
        delta = arrangement_delta(lam, 1)
        h = baseline_h(lam)
        bound = h + delta
        print(f"{lam:0.9f}  {delta:0.9f}  {h:0.9f}  {bound:0.9f}  {bound-2/3:0.9f}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jitter-search", action="store_true")
    parser.add_argument("--jitter-lambda", type=float, default=0.90)
    parser.add_argument("--seed", type=int, default=20260829)
    parser.add_argument("--starts", type=int, default=8)
    parser.add_argument("--periods", type=int, default=180)
    parser.add_argument("--rounds", type=int, default=40)
    args = parser.parse_args()

    run_exact_checks()
    print_table()

    if args.jitter_search:
        result = jitter_search(
            args.jitter_lambda,
            seed=args.seed,
            starts=args.starts,
            periods=args.periods,
            initial_step=0.18,
            rounds=args.rounds,
        )
        print("\nHEURISTIC periodic-jitter search (not proof)")
        print(f"  lambda={result.lam:.9f}")
        print(f"  min max-gap={result.objective:.9f}")
        print(f"  first-scale defect={result.defect_at_one:.9f}")
        print(f"  second-scale excess={result.second_scale_excess:.9f}")
        print("  displacements=" + ",".join(f"{x:.7f}" for x in result.displacements))

    print("\nBOUNDARY: the universal and period-six bounds are exact only for the ideal")
    print("rectangular critical-lattice model. They are not theorems about actual zeta")
    print("zeros or the smooth finite Zeta23 taper. The jitter search is heuristic.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
