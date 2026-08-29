#!/usr/bin/env python3
"""Deterministic model checks for A-RH-LCI-0003.

This standard-library script verifies finite formulas and asymptotic model
signals only. It does not compute zeta zeros and does not prove the compactness
or smooth-taper transfer theorems.
"""

from __future__ import annotations

import argparse
import math
from fractions import Fraction
from typing import Sequence


def sinc_sq(lam: float, x: float) -> float:
    """(sin(pi*lam*x)/(pi*lam*x))^2 with the continuous value at zero."""
    y = math.pi * lam * x
    if abs(y) < 1.0e-15:
        return 1.0
    value = math.sin(y) / y
    return value * value


def slow_strain_defect(size: int, alpha: float) -> float:
    """Exact open-interval first-scale defect for x_n=n+alpha*n/size."""
    if size < 2 or not (0.0 < alpha < 0.25):
        raise ValueError("require size >= 2 and 0 < alpha < 1/4")
    scale = 1.0 + alpha / size
    total = 0.0
    for offset in range(1, size):
        numerator = math.sin(math.pi * alpha * offset / size)
        kernel = numerator / (math.pi * offset * scale)
        total += 2.0 * (size - offset) * kernel * kernel
    return total


def slow_strain_limit(alpha: float, steps: int = 200_000) -> float:
    """Midpoint quadrature for the exact limiting integral."""
    if not (0.0 < alpha < 0.25) or steps < 100:
        raise ValueError("invalid alpha or quadrature size")
    step = 1.0 / steps
    total = 0.0
    for index in range(steps):
        t = (index + 0.5) * step
        total += (1.0 - t) * math.sin(math.pi * alpha * t) ** 2 / (t * t)
    return 2.0 * step * total / (math.pi * math.pi)


def global_coset_displacement(size: int, alpha: float) -> float:
    """Exact best fixed-coset squared displacement for alpha<1/4."""
    return alpha * alpha * (size * size - 1.0) / (12.0 * size)


def phase_separated_marks(size: int) -> tuple[int, ...]:
    """Simple density 2/3: alternating 2,0 on one third, then all ones."""
    if size % 6:
        raise ValueError("size must be divisible by six")
    active = size // 3
    return tuple(
        (2 if index % 2 == 0 else 0) if index < active else 1
        for index in range(size)
    )


def cyclic_autocorrelation(marks: Sequence[int]) -> list[int]:
    size = len(marks)
    return [
        sum(marks[index] * marks[(index + offset) % size] for index in range(size))
        for offset in range(size)
    ]


def periodized_kernel(
    lam: float,
    residue: int,
    size: int,
    strain_scale: float,
    image_radius: int,
) -> float:
    return sum(
        sinc_sq(lam, (residue + image * size) * strain_scale)
        for image in range(-image_radius, image_radius + 1)
    )


def periodic_energy(
    marks: Sequence[int],
    lam: float,
    *,
    alpha: float = 0.0,
    image_radius: int = 40,
) -> float:
    """Full periodic Gram energy, normalized by total multiplicity.

    Positions are x_n=(1+alpha/N)n on a circle of length N+alpha.
    """
    size = len(marks)
    total_mass = sum(marks)
    if size < 2 or total_mass <= 0:
        raise ValueError("nonempty positive-mass pattern required")
    strain_scale = 1.0 + alpha / size
    correlation = cyclic_autocorrelation(marks)
    numerator = 0.0
    for residue, coefficient in enumerate(correlation):
        numerator += coefficient * periodized_kernel(
            lam, residue, size, strain_scale, image_radius
        )
    return numerator / total_mass


def diagonal_energy(marks: Sequence[int]) -> float:
    return sum(value * value for value in marks) / sum(marks)


def kappa(lam: float) -> float:
    return 1.0 / lam + lam / 3.0


def exact_fraction_checks() -> None:
    assert Fraction(44, 27) - Fraction(19, 12) == Fraction(5, 108)
    assert Fraction(1, 1) - Fraction(9, 32) == Fraction(23, 32)
    assert Fraction(1, 1) - Fraction(9, 64) == Fraction(55, 64)
    size = 97
    alpha = Fraction(1, 5)
    exact = alpha * alpha * (size * size - 1) / (12 * size)
    numerical = global_coset_displacement(size, float(alpha))
    assert abs(float(exact) - numerical) < 1.0e-14


def check_slow_strain(alpha: float, quadrature_steps: int) -> None:
    limit = slow_strain_limit(alpha, quadrature_steps)
    sizes = (120, 480, 1_920, 7_680)
    values = [slow_strain_defect(size, alpha) for size in sizes]

    if abs(values[-1] - limit) > 1.5e-5:
        raise AssertionError("slow-strain defect did not approach the limiting integral")
    if values[-1] / sizes[-1] > 1.0e-5:
        raise AssertionError("first-scale defect per site is not small")
    expected_displacement_density = alpha * alpha / 12.0
    observed = global_coset_displacement(sizes[-1], alpha) / sizes[-1]
    if abs(observed - expected_displacement_density) > 1.0e-9:
        raise AssertionError("global displacement identity mismatch")

    print("PASS slow-strain obstruction")
    print(f"  alpha={alpha:.6f}")
    print(f"  limiting first-scale defect={limit:.12f}")
    for size, value in zip(sizes, values):
        print(
            f"  N={size:5d}: D1={value:.12f}, "
            f"D1/N={value/size:.3e}, "
            f"best-coset-L2/N={global_coset_displacement(size, alpha)/size:.12f}"
        )


def check_local_window_collapse(alpha: float) -> None:
    """Fixed-radius pair differences converge to integer differences."""
    radius = 20
    sizes = (120, 480, 1_920, 7_680)
    errors = [2.0 * radius * alpha / size for size in sizes]
    for previous, current in zip(errors, errors[1:]):
        if current >= previous:
            raise AssertionError("local strain error should decrease")
    print("PASS local-window collapse")
    for size, error in zip(sizes, errors):
        print(f"  N={size:5d}: max fixed-window difference error <= {error:.3e}")


def check_phase_separated_gap(
    alpha: float,
    image_radius: int,
) -> None:
    lam = 0.75
    target = 5.0 / 108.0
    sizes = (120, 240, 480, 960)
    second_excesses: list[float] = []
    first_defects: list[float] = []

    for size in sizes:
        marks = phase_separated_marks(size)
        diagonal = diagonal_energy(marks)
        first_defect = periodic_energy(
            marks, 1.0, alpha=alpha, image_radius=image_radius
        ) - diagonal
        second_excess = periodic_energy(
            marks, lam, alpha=alpha, image_radius=image_radius
        ) - kappa(lam)
        first_defects.append(first_defect)
        second_excesses.append(second_excess)

    if first_defects[-1] > 3.0e-4:
        raise AssertionError("strained first-scale defect did not decay per site")
    if abs(second_excesses[-1] - target) > 2.5e-4:
        raise AssertionError("second-scale excess did not approach 5/108")
    if sum(value == 1 for value in phase_separated_marks(sizes[-1])) * 3 != 2 * sizes[-1]:
        raise AssertionError("simple density is not exactly 2/3")

    print("PASS phase-separated local-limit signal")
    print(f"  strain alpha={alpha:.6f}; target second-scale gap=5/108={target:.12f}")
    for size, first, second in zip(sizes, first_defects, second_excesses):
        print(
            f"  N={size:4d}: D1/N={first:.9f}, "
            f"E_3/4-kappa={second:.9f}"
        )


def check_hyperbolic_swap() -> None:
    """Exact two-pair cancellation in the abstract real block model."""
    for r in (Fraction(1, 10), Fraction(1, 2), Fraction(2, 1)):
        # Diagonal entries of Psharp and R in the basis (e1,e2).
        psharp = (2 * (1 + r), 2 * (1 + r))
        negative = (2 * r, 2 * r)
        total_matrix = tuple(p - n for p, n in zip(psharp, negative))
        trace = sum(total_matrix)
        frobenius_sq = sum(value * value for value in total_matrix)
        count_budget = Fraction(8, 1)  # two reflection-pair budgets
        combined_defect = count_budget - (4 * trace - frobenius_sq)

        single_norm_sum = 1 + 2 * r
        isolated_each = 2 * (single_norm_sum * single_norm_sum - 1)
        isolated_sum = 2 * isolated_each

        assert total_matrix == (Fraction(2, 1), Fraction(2, 1))
        assert combined_defect == 0
        assert isolated_sum == 16 * r + 16 * r * r
        assert isolated_sum > 0
        # The collapsed-orbit negative matching term vanishes exactly.
        spectral_excess = tuple(value - 2 for value in psharp)
        assert spectral_excess == negative

    print("PASS abstract hyperbolic-swap obstruction")
    print("  two interacting deep pairs can have zero combined c=2 defect")
    print("  isolated positive depth penalties therefore do not add")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--quadrature-steps", type=int, default=100_000)
    parser.add_argument("--image-radius", type=int, default=40)
    args = parser.parse_args()

    exact_fraction_checks()
    check_slow_strain(args.alpha, args.quadrature_steps)
    check_local_window_collapse(args.alpha)
    check_phase_separated_gap(args.alpha, args.image_radius)
    check_hyperbolic_swap()
    print(
        "BOUNDARY: finite formulas and numerical asymptotics only; "
        "no compactness theorem or zeta-zero theorem is machine-proved here."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
