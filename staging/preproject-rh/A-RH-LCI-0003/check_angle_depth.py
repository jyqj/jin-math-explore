#!/usr/bin/env python3
"""Deterministic checks for the quantitative angle/depth checkpoint.

The script checks exact rank-one sharpness of the principal-angle operator
bound, a finite Gram expansion for the collapsed negative matrix, and the
centered frequency-square identities by numerical quadrature.

It does not prove a uniform Riesz bound, a prime-side weighted trace estimate,
or a theorem about zeta zeros.
"""

from __future__ import annotations

import argparse
import math
from fractions import Fraction
from typing import Callable


def simpson(function: Callable[[float], float], left: float, right: float, steps: int) -> float:
    if steps < 2:
        raise ValueError("steps must be at least two")
    if steps % 2:
        steps += 1
    width = (right - left) / steps
    total = function(left) + function(right)
    for index in range(1, steps):
        total += (4.0 if index % 2 else 2.0) * function(left + index * width)
    return total * width / 3.0


def dot(left: tuple[Fraction, ...], right: tuple[Fraction, ...]) -> Fraction:
    return sum((a * b for a, b in zip(left, right)), Fraction(0, 1))


def outer(vector: tuple[Fraction, ...]) -> list[list[Fraction]]:
    return [[a * b for b in vector] for a in vector]


def add_scaled(
    target: list[list[Fraction]],
    matrix: list[list[Fraction]],
    scale: Fraction,
) -> None:
    for row in range(len(target)):
        for column in range(len(target)):
            target[row][column] += scale * matrix[row][column]


def frobenius_sq(matrix: list[list[Fraction]]) -> Fraction:
    return sum((value * value for row in matrix for value in row), Fraction(0, 1))


def check_rank_one_angle_sharpness() -> None:
    for cosine in (Fraction(0, 1), Fraction(1, 4), Fraction(1, 2), Fraction(3, 4)):
        radius = Fraction(7, 3)
        eta_exact = 1 - cosine * cosine
        exact_coefficient = 2 * eta_exact - eta_exact * eta_exact
        assert exact_coefficient == 1 - cosine**4

        # The best supported positive operator is S = radius*cosine^2 uu*.
        optimum = radius * cosine * cosine
        distance_sq = radius * radius + optimum * optimum - 2 * radius * optimum * cosine * cosine
        assert distance_sq == radius * radius * exact_coefficient

        # The two-column Gram matrix has lower eigenvalue 1-cosine.
        gamma = 1 - cosine
        riesz_coefficient = 2 * gamma - gamma * gamma
        assert riesz_coefficient == eta_exact
        assert distance_sq >= radius * radius * riesz_coefficient

    print("PASS rank-one sharpness of principal-angle operator bound")
    print("  exact coefficient 2*eta-eta^2 is attained for two lines")
    print("  the coarser combined-Riesz coefficient remains valid")


def check_negative_gram_expansion() -> None:
    vectors = (
        (Fraction(1, 1), Fraction(0, 1), Fraction(1, 2)),
        (Fraction(1, 2), Fraction(1, 1), Fraction(-1, 3)),
        (Fraction(0, 1), Fraction(2, 3), Fraction(1, 1)),
    )
    multiplicities = (1, 2, 3)
    dimension = len(vectors[0])
    matrix = [[Fraction(0, 1) for _ in range(dimension)] for _ in range(dimension)]

    for multiplicity, vector in zip(multiplicities, vectors):
        add_scaled(matrix, outer(vector), Fraction(2 * multiplicity, 1))

    direct = frobenius_sq(matrix)
    gram_expansion = Fraction(0, 1)
    diagonal_part = Fraction(0, 1)
    for p, (mp, vp) in enumerate(zip(multiplicities, vectors)):
        for q, (mq, vq) in enumerate(zip(multiplicities, vectors)):
            term = Fraction(4 * mp * mq, 1) * dot(vp, vq) ** 2
            gram_expansion += term
            if p == q:
                diagonal_part += term

    assert direct == gram_expansion
    assert direct >= diagonal_part

    print("PASS collapsed-negative Gram expansion")
    print(f"  ||R||_F^2 = {direct}")
    print(f"  diagonal depth-safe contribution = {diagonal_part}")


def phi(u: float) -> float:
    return 1.0 - u * u if abs(u) <= 1.0 else 0.0


def phi_deriv(u: float) -> float:
    return -2.0 * u if abs(u) <= 1.0 else 0.0


def taper_constants() -> tuple[Fraction, Fraction, Fraction]:
    # For phi(u)=1-u^2 on [-1,1].
    return Fraction(16, 15), Fraction(8, 3), Fraction(16, 105)


def direct_pair_difference(t: float, delta: float, center: float, steps: int) -> float:
    def integrand(u: float) -> float:
        ph = phi(u)
        derivative = phi_deriv(u)
        ch = math.cosh(delta * u)
        sh = math.sinh(delta * u)

        x_norm = ((t - center) * ph * ch) ** 2 + (derivative * ch + delta * ph * sh) ** 2
        y_norm = ((t - center) * ph * sh) ** 2 + (derivative * sh + delta * ph * ch) ** 2
        return x_norm - y_norm

    return simpson(integrand, -1.0, 1.0, steps)


def direct_online_norm(s: float, center: float, steps: int) -> float:
    return simpson(
        lambda u: ((s - center) * phi(u)) ** 2 + phi_deriv(u) ** 2,
        -1.0,
        1.0,
        steps,
    )


def check_centered_derivative_identity(steps: int) -> None:
    a_exact, b_exact, m2_exact = taper_constants()
    a_numeric = simpson(lambda u: phi(u) ** 2, -1.0, 1.0, steps)
    b_numeric = simpson(lambda u: phi_deriv(u) ** 2, -1.0, 1.0, steps)
    m2_numeric = simpson(lambda u: u * u * phi(u) ** 2, -1.0, 1.0, steps)

    for observed, expected in (
        (a_numeric, float(a_exact)),
        (b_numeric, float(b_exact)),
        (m2_numeric, float(m2_exact)),
    ):
        if abs(observed - expected) > 5.0e-11:
            raise AssertionError((observed, expected))

    cases = (
        (2.3, 0.4, 2.0),
        (0.0, 0.7, 0.2),
        (5.0, 1.2, 4.8),
    )
    maximum_error = 0.0
    for t, delta, center in cases:
        direct = direct_pair_difference(t, delta, center, steps)
        predicted = float(a_exact) * ((t - center) ** 2 - delta**2) + float(b_exact)
        maximum_error = max(maximum_error, abs(direct - predicted))

    if maximum_error > 2.0e-9:
        raise AssertionError(maximum_error)

    print("PASS centered derivative identity for individual pairs")
    print("  A_phi=16/15, B_phi=8/3, M2_phi=16/105")
    print(f"  maximum quadrature residual={maximum_error:.3e}")


def check_aggregate_depth_identity(steps: int) -> None:
    on_line = ((2, -0.10), (1, 0.15))
    pairs = ((1, 0.05, 0.20), (2, -0.12, 0.10))
    center = 0.0
    a_exact, b_exact, _ = taper_constants()
    a_value = float(a_exact)
    b_value = float(b_exact)

    total_multiplicity = sum(m for m, _ in on_line) + 2 * sum(n for n, _, _ in pairs)
    direct_moment = sum(
        m * direct_online_norm(s, center, steps) for m, s in on_line
    ) + 2.0 * sum(
        n * direct_pair_difference(t, delta, center, steps)
        for n, t, delta in pairs
    )

    horizontal = sum(m * (s - center) ** 2 for m, s in on_line) + 2.0 * sum(
        n * (t - center) ** 2 for n, t, _ in pairs
    )
    depth = sum(n * delta**2 for n, _, delta in pairs)
    predicted = b_value * total_multiplicity + a_value * (horizontal - 2.0 * depth)

    if abs(direct_moment - predicted) > 4.0e-9:
        raise AssertionError((direct_moment, predicted))

    block_radius = max(
        max(abs(s - center) for _, s in on_line),
        max(abs(t - center) for _, t, _ in pairs),
    )
    epsilon = (b_value * total_multiplicity - direct_moment) / (
        a_value * total_multiplicity
    )
    extracted_bound = (block_radius * block_radius + epsilon) / 2.0
    observed_depth_density = depth / total_multiplicity

    if observed_depth_density > extracted_bound + 2.0e-12:
        raise AssertionError((observed_depth_density, extracted_bound))

    print("PASS aggregate centered-moment and local depth extraction")
    print(f"  total multiplicity={total_multiplicity}")
    print(f"  block radius h={block_radius:.6f}")
    print(f"  implied epsilon={epsilon:.12f}")
    print(f"  depth density={observed_depth_density:.12f}")
    print(f"  conditional bound=(h^2+epsilon)/2={extracted_bound:.12f}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quadrature-steps", type=int, default=20_000)
    args = parser.parse_args()

    check_rank_one_angle_sharpness()
    check_negative_gram_expansion()
    check_centered_derivative_identity(args.quadrature_steps)
    check_aggregate_depth_identity(args.quadrature_steps)
    print(
        "BOUNDARY: exact finite-dimensional identities and numerical quadrature only; "
        "no uniform angle bound, prime-side trace estimate, or zeta theorem is proved."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
