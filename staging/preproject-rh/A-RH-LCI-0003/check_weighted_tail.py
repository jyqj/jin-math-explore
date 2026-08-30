#!/usr/bin/env python3
"""Deterministic checks for the weighted finite-section tail estimate."""

from __future__ import annotations

import argparse
import math


def sum_bounds(distance: float, spacing: float) -> tuple[float, float]:
    if distance < 2.0 * spacing:
        raise ValueError("require D >= 2q")
    sigma2 = 8.0 / distance**2 + 4.0 / (spacing * distance)
    sigma4 = 32.0 / distance**4 + 16.0 / (3.0 * spacing * distance**3)
    return sigma2, sigma4


def weighted_tail_bound(
    distance: float,
    spacing: float,
    block_radius: float,
    decay_constant: float,
) -> float:
    sigma2, sigma4 = sum_bounds(distance, spacing)
    return 2.0 * decay_constant**2 * (sigma2 + block_radius**2 * sigma4)


def partial_two_sided_sum(
    distance: float,
    spacing: float,
    block_radius: float,
    decay_constant: float,
    terms: int,
) -> float:
    start = distance / 2.0
    total = 0.0
    for index in range(terms):
        radius = start + index * spacing
        total += 2.0 * decay_constant**2 * (
            1.0 / radius**2 + block_radius**2 / radius**4
        )
    return 2.0 * total


def zeta_scale_bound(T: float, lam: float, block_radius: float = 1.0) -> float:
    ell = math.log(T / (2.0 * math.pi))
    length = lam * ell
    spacing = 2.0 * math.pi / length
    distance = math.sqrt(T)
    decay_constant = math.exp(length / 4.0)
    return weighted_tail_bound(distance, spacing, block_radius, decay_constant)


def online_scale_bound(T: float, lam: float, block_radius: float = 1.0) -> float:
    ell = math.log(T / (2.0 * math.pi))
    length = lam * ell
    spacing = 2.0 * math.pi / length
    return weighted_tail_bound(math.sqrt(T), spacing, block_radius, 1.0)


def check_grid_sum(terms: int) -> None:
    distance = 50.0
    spacing = 0.2
    block_radius = 1.5
    decay_constant = 3.0
    partial = partial_two_sided_sum(
        distance, spacing, block_radius, decay_constant, terms
    )
    bound = weighted_tail_bound(
        distance, spacing, block_radius, decay_constant
    )
    if partial > bound + 1.0e-12:
        raise AssertionError((partial, bound))
    print("PASS two-sided grid-tail bound")
    print(f"  partial sum ({terms} terms/side)={partial:.12f}")
    print(f"  analytic upper bound={bound:.12f}")


def check_scale_transition() -> None:
    sizes = (1.0e6, 1.0e8, 1.0e10, 1.0e12)
    short = [zeta_scale_bound(T, 0.75) for T in sizes]
    endpoint = [zeta_scale_bound(T, 1.0) for T in sizes]
    online = [online_scale_bound(T, 1.0) for T in sizes]

    if not all(b < a for a, b in zip(short, short[1:])):
        raise AssertionError("lambda=3/4 complex weighted tail should decrease")
    if not all(b > a for a, b in zip(endpoint, endpoint[1:])):
        raise AssertionError("endpoint worst-case bound should grow logarithmically")
    if not all(b < a for a, b in zip(online, online[1:])):
        raise AssertionError("real-argument endpoint tail should decrease")

    print("PASS scale transition")
    for T, a, b, c in zip(sizes, short, endpoint, online):
        print(
            f"  T={T:.0e}: complex lambda=3/4 {a:.6e}; "
            f"complex lambda=1 {b:.6e}; real lambda=1 {c:.6e}"
        )
    print("  predicted exponents: -1/8, 0 (logarithmic), and -1/2")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--terms", type=int, default=200_000)
    args = parser.parse_args()
    check_grid_sum(args.terms)
    check_scale_transition()
    print(
        "BOUNDARY: this checks the single-vector tail estimate and scale law only; "
        "it does not prove the prime-side weighted trace theorem."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
