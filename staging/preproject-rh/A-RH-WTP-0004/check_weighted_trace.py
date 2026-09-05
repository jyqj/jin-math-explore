#!/usr/bin/env python3
"""Deterministic checks for A-RH-WTP-0004 (not an RH proof).

Run with Python >=3.11, NumPy, SciPy and SymPy. Exact symbolic checks,
finite numerical identities and convergence diagnostics are reported separately.
No network access, zeta-zero computation, Lean replay or source audit is done.
"""
from __future__ import annotations

import argparse
import math
import platform
import sys
from fractions import Fraction

import numpy as np
import scipy
from scipy.integrate import quad
import sympy as sp

SEED = 20260905


def close(actual: float | complex, expected: float | complex, *, rtol: float = 2e-9,
          atol: float = 2e-10) -> float:
    residual = float(abs(actual - expected))
    if residual > atol + rtol * abs(expected):
        raise AssertionError((actual, expected, residual))
    return residual


def von_mangoldt(limit: int) -> np.ndarray:
    if limit < 1:
        raise ValueError("limit must be positive")
    values = np.zeros(limit + 1)
    prime = np.ones(limit + 1, dtype=bool)
    prime[:2] = False
    for p in range(2, limit + 1):
        if prime[p]:
            prime[2 * p::p] = False
            power = p
            while power <= limit:
                values[power] = math.log(p)
                power *= p
    return values


def weight_variation(weights: np.ndarray) -> float:
    if weights.ndim != 1 or weights.size == 0 or not np.all(np.isfinite(weights)):
        raise ValueError("finite nonempty one-dimensional weights required")
    return float(abs(weights[-1]) + np.abs(np.diff(weights)).sum())


def cosine_hat_real(r: float, length: float) -> float:
    """FT of cos(pi*u/L) on [-L/2,L/2], continuous at both removable poles."""
    b = math.pi / length
    return float(length / 2 * (np.sinc((r + b) * length / (2 * math.pi))
                              + np.sinc((r - b) * length / (2 * math.pi))))


def cosine_autocorrelation(y: np.ndarray, length: float) -> np.ndarray:
    y = np.abs(y)
    return np.where(y < length, (length - y) / 2 * np.cos(math.pi * y / length)
                    + length / (2 * math.pi) * np.sin(math.pi * y / length), 0.0)


def check_exact_polynomials() -> None:
    z, c, t, h = sp.symbols("z c t h", real=True)
    # exp(i*t*y) has been factored out; -i*d/dy acts as t+h*z*d/dz.
    for d in range(1, 9):
        base = sum(z**k for k in range(d))
        first = (t - c) * base + h * z * sp.diff(base, z)
        twice = (t - c) * first + h * z * sp.diff(first, z)
        direct = sum((t + h * k - c)**2 * z**k for k in range(d))
        assert sp.expand(twice - direct) == 0
        weights = [sp.Rational((k % 3) - 1, k + 1) for k in range(d)]
        abel = weights[-1] * base + sum(
            (weights[k] - weights[k + 1]) * sum(z**j for j in range(k + 1))
            for k in range(d - 1))
        assert sp.expand(abel - sum(weights[k] * z**k for k in range(d))) == 0
    a, b, v = sp.symbols("a b v", real=True)
    x, y = a * sp.cosh(v) + b * sp.sinh(v), a * sp.sinh(v) + b * sp.cosh(v)
    assert sp.simplify(x*x - y*y - (a*a - b*b)) == 0
    assert Fraction(44, 27) - Fraction(19, 12) == Fraction(5, 108)
    y = (sp.sqrt(sp.Rational(119, 72))-sp.sqrt(sp.Rational(19, 12)))/2
    assert sp.simplify(y*y+sp.sqrt(sp.Rational(19, 12))*y-sp.Rational(5, 288)) == 0
    print("PASS exact symbolic quadratic-weight, Abel and hyperbolic identities (d=1..8)")


def check_weighted_prime_trace() -> None:
    # A cosine taper is H^1_0, not the source's flat C^3 taper. Used only to
    # check the Fourier normalization; no application of the zeta EF is made.
    length = 4.0
    tau = 7.0 + (2 * math.pi / length) * np.arange(5)
    center = float(tau[2])
    weights = (tau - center)**2
    limit = int(math.exp(length))
    vm = von_mangoldt(limit)
    n = np.flatnonzero(vm)
    logs, coef = np.log(n), vm[n] / np.sqrt(n)
    aphi = cosine_autocorrelation(logs, length)
    dw = np.exp(1j * np.outer(logs, tau)) @ weights
    predicted = float(-2 * np.sum(coef * aphi * dw.real))

    def integrand(t: float) -> float:
        hval = sum(float(w) * cosine_hat_real(t - float(tk), length)**2
                   for w, tk in zip(weights, tau))
        px = -float(np.dot(coef, np.cos(t * logs))) / math.pi
        return hval * px

    radius = 260.0
    measured, quad_error = quad(integrand, -radius, radius, epsabs=2e-8,
                                 epsrel=2e-10, limit=1800)
    # For |r|>=2b, |hat(phi)(r)| <= (8b/3)/r^2. This is an analytic omitted
    # integral bound; scipy's internal quadrature error is not certified.
    b = math.pi / length
    gap = radius - float(np.max(np.abs(tau)))
    assert gap >= 2*b
    tail = float(2 * np.abs(weights).sum() * (8*b/3)**2 / (3*gap**3)
                 * coef.sum() / math.pi)
    residual = abs(measured - predicted)
    if residual > tail + 10 * quad_error + 1e-8:
        raise AssertionError((measured, predicted, residual, tail, quad_error))

    variation = weight_variation(weights)
    theta = math.pi * logs / length
    geometric_bound = np.minimum(len(weights), 1 / np.abs(np.sin(theta)))
    if np.any(np.abs(dw) > variation * geometric_bound + 1e-9):
        raise AssertionError("Abel bound failed")
    # C_X is computed only on this finite interval. It is not advertised as a
    # proved global Chebyshev constant.
    cumulative = np.cumsum(vm)
    cx = float(np.max(cumulative[1:] / np.arange(1, limit + 1)))
    closed_bound = 2 * cx * variation * (
        length**2 * math.exp(length / 4) / math.log(2)
        + length * math.exp(length / 2))
    triangle = float(2 * np.sum(coef * np.abs(aphi) * np.abs(dw)))
    assert abs(predicted) <= triangle + 1e-9
    assert triangle <= closed_bound + 1e-9
    print("PASS finite weighted prime-part identity (numerical quadrature)")
    print(f"  L={length:g}, prime powers n<=floor(exp(L))={limit}, weights=(tau-c)^2")
    print(f"  prime-side finite sum={predicted:.12f}")
    print(f"  truncated direct integral={measured:.12f}")
    print(f"  residual={residual:.3e}; analytic integral tail bound={tail:.3e}")
    print(f"  scipy internal error estimate={quad_error:.3e} (not interval-certified)")
    print(f"  finite C_X={cx:.9f}, triangle bound={triangle:.6f}, coarse Abel bound={closed_bound:.6f}")


def cosine_hat_complex(z: np.ndarray) -> np.ndarray:
    # L=2pi, evaluated only at integer-real parts; no removable pole is hit.
    return -np.cos(math.pi * z) / (z*z - 0.25)


def cutoff_contrast(m: int, k: int, delta: float) -> float:
    if m < 0 or k < 0 or not 0 < delta < .5:
        raise ValueError("nonnegative cutoffs and 0<delta<1/2 required")
    p = np.arange(-m, m + 1)[:, None]
    freq = np.arange(-k, k + 1)[None, :]
    shifted = cosine_hat_complex((p - freq).astype(complex) - 1j*delta)
    tangent = cosine_hat_complex((p - freq).astype(complex))
    difference = (shifted*shifted).real - (tangent*tangent).real
    return float(np.sum(freq*freq * difference / math.pi) / (2*m + 1))


def check_cutoff_order() -> None:
    delta, fixed = .2, 3
    target = -2 * math.pi * delta**2
    cutoffs = (32, 128, 512, 2048)
    first = [cutoff_contrast(fixed, k, delta) for k in cutoffs]
    second = [cutoff_contrast(m, fixed, delta) for m in cutoffs]
    assert all(abs(v-target) < abs(u-target) for u, v in zip(first, first[1:]))
    assert abs(first[-1]-target) < 2e-4
    assert all(abs(v) < abs(u) for u, v in zip(second, second[1:]))
    assert abs(second[-1]) < 1e-10
    print("PASS unequal cutoff-order limits: numerical signal for the proved model formulas")
    print(f"  target at fixed zero cutoff, then full grid: -2*pi*delta^2={target:.12f}")
    for cutoff, a, b in zip(cutoffs, first, second):
        print(f"  cutoff={cutoff:4d}: fixed M=3, K growing: {a:.12f}; fixed K=3, M growing: {b:.3e}")


def mixed_model(depths: np.ndarray, pairs: np.ndarray,
                tangent_loads: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    psize = len(depths)
    j = np.arange(psize)
    fourier = np.exp(2j*math.pi*np.outer(j, j)/psize)/math.sqrt(psize)
    loads = np.where(pairs, 2, tangent_loads)
    g0 = (fourier * loads) @ fourier.conj().T
    displacement = (j[:, None] - j[None, :])/psize
    k = np.zeros((psize, psize), dtype=complex)
    for p in np.flatnonzero(pairs):
        up = np.outer(fourier[:, p], fourier[:, p].conj())
        k += 4 * np.sinh(depths[p]*displacement/2)**2 * up
    g = g0 + k
    budget = float(np.sum(4 - np.maximum(2-loads, 0)**2))
    defect = budget - 4*float(np.trace(g).real) + float(np.vdot(g, g).real)
    return g0, k, defect


def check_operator_transfer(samples: int) -> None:
    rng = np.random.default_rng(SEED)
    maximum_identity = 0.0
    minimum_transfer_slack = math.inf
    weighted_invariance_error = 0.0
    minimum_moderate_slack = math.inf
    for case in range(samples):
        period = int(rng.integers(3, 25))
        depths = rng.uniform(0.0, 5.0, size=period)
        pairs = np.ones(period, dtype=bool) if case % 3 == 0 else rng.random(period) < .55
        loads = rng.integers(0, 3, size=period)
        g0, k, defect = mixed_model(depths, pairs, loads)
        d0 = 2*np.eye(period) - g0
        cross = float(np.trace(d0 @ k).real)
        norm2 = float(np.vdot(k, k).real)
        # Site-dependent depths lie below 2*pi in this regression. The sign
        # comparison is atomwise: it does not need a common depth alphabet.
        minimum_moderate_slack = min(minimum_moderate_slack, defect - norm2)
        if defect + 3e-8 < norm2:
            raise AssertionError(("moderate-depth coercivity", defect, norm2))
        residual = close(defect + 2*cross, norm2)
        maximum_identity = max(maximum_identity, residual)
        d = max(1, (3*period)//4)
        raw = rng.standard_normal((period, d)) + 1j*rng.standard_normal((period, d))
        columns, _ = np.linalg.qr(raw)
        contraction = np.diag(rng.uniform(.1, 1, size=d)) @ columns.conj().T
        small_k = contraction @ k @ contraction.conj().T
        small_g0 = contraction @ g0 @ contraction.conj().T
        local_norm2 = float(np.vdot(small_k, small_k).real)
        if local_norm2 > norm2 + 2e-8:
            raise AssertionError("HS contraction failed")
        eps = max(cross, 0.0)/period
        eta = max(defect/period + 2*eps, 0.0)
        lhs = abs(float(np.vdot(small_g0+small_k, small_g0+small_k).real)
                  - float(np.vdot(small_g0, small_g0).real))/period
        upper = 4*math.sqrt((d/period)*eta)+eta
        minimum_transfer_slack = min(minimum_transfer_slack, upper-lhs)
        if lhs > upper + 3e-8:
            raise AssertionError(("transfer", lhs, upper))
        if np.all(pairs):
            close(defect, norm2)
        # Every common-depth full pair family has K=0, including arbitrary
        # finite diagonal weights. This directly tests the no-identification.
        all_pairs = np.ones(period, dtype=bool)
        _, homogeneous, _ = mixed_model(np.full(period, 2.3), all_pairs, loads)
        weights = rng.normal(size=period)
        weighted_invariance_error = max(weighted_invariance_error,
            float(np.linalg.norm(homogeneous, 'fro')),
            abs(float(np.dot(weights, homogeneous.diagonal().real))))
    if weighted_invariance_error > 3e-10:
        raise AssertionError(weighted_invariance_error)
    print("PASS variable-depth pure-pair contraction and conditional mixed transfer")
    print(f"  samples={samples}, seed={SEED}, periods=3..24, depths in [0,5]")
    print(f"  maximum exact-defect-identity residual={maximum_identity:.3e}")
    print(f"  minimum second-moment-bound slack={minimum_transfer_slack:.3e}")
    print(f"  minimum variable-moderate-depth D-||K||^2 slack={minimum_moderate_slack:.3e}")
    print(f"  homogeneous pair/tangent operator residual={weighted_invariance_error:.3e}")
    gain, alpha = 5/108, 3/4
    # Source-compatible unit-norm short atoms use G_alpha=R G R*/alpha.
    # Omitting alpha^-2 here would understate the second-moment error.
    raw_allowance = gain * alpha**2
    eta_star = (raw_allowance/(math.sqrt(4*alpha+raw_allowance)+2*math.sqrt(alpha)))**2
    close((4*math.sqrt(alpha*eta_star)+eta_star)/alpha**2, gain, atol=1e-15)
    critical_eta = (raw_allowance/(math.sqrt(2+raw_allowance)+math.sqrt(2)))**2
    close((2*math.sqrt(2*critical_eta)+critical_eta)/alpha**2, gain, atol=1e-15)
    print(f"  correctly normalized general eta threshold: {eta_star:.15g}")
    print(f"  critical mean-load-one eta threshold: {critical_eta:.15g}")
    print("  both reserve the entire 5/108 gap for operator error only; other source losses are not included")


def pair_cross_closed(period: int, offset: int, depth: float) -> float:
    if offset % period == 0:
        raise ValueError("off-diagonal offset required")
    u = 2*math.sinh(depth/(2*period))**2
    v = 2*math.sin(math.pi*(offset % period)/period)**2
    return 4*math.sinh(depth/2)**2/period**2 * (u-v-u*v)/(u+v)**2


def check_critical_corollary(samples: int) -> None:
    rng = np.random.default_rng(SEED + 2)
    alpha, kappa = .75, 19/12
    t = 5/288
    epsilon = (2*t/(math.sqrt(kappa+4*t)+math.sqrt(kappa)))**2
    maximum_symbol_error = 0.0
    maximum_kernel_error = 0.0
    accepted = 0
    for _ in range(samples):
        period = int(rng.choice([12,24,36]))
        order = rng.permutation(period)
        q = int(rng.integers(0,period//3+1))
        loads = np.ones(period,dtype=int)
        loads[order[:q]] = 2
        loads[order[q:2*q]] = 0
        pairs = (loads == 2) & (rng.random(period) < .8)
        depths = rng.uniform(0,2*math.pi,period)
        g0,k,defect = mixed_model(depths,pairs,loads)
        g = g0+k
        d = int(alpha*period)
        mhat = np.fft.fft(loads)/period
        th = np.arange(period)/period
        symbol = (np.maximum(alpha-th,0)+np.maximum(alpha-(1-th),0))/alpha**2
        # The constant mode has only one representative, not both endpoints.
        symbol[0] = 1/alpha
        e0 = float(np.linalg.norm(g0[:d,:d]/alpha,'fro')**2/period)
        predicted = float(np.sum(symbol*abs(mhat)**2))
        maximum_symbol_error = max(maximum_symbol_error,close(e0,predicted))
        simple = float(np.mean(loads==1))
        assert e0 + 1e-10 >= 4/3+8/9*(1-simple)
        e1 = float(np.linalg.norm(g,'fro')**2/period)
        e2 = float(np.linalg.norm(g[:d,:d]/alpha,'fro')**2/period)
        close(defect/period,e1-2+simple)
        u1,u2 = max(e1-4/3,0),max(e2-kappa,0)
        x = simple-2/3
        left = math.sqrt(44/27-8*x/9)
        right = math.sqrt(kappa+u2)+math.sqrt(max(x+u1,0))/alpha
        assert left <= right + 3e-9
        if u1 <= 1e-12 and u2 <= 1e-12:
            accepted += 1
            assert simple+1e-10 >= 2/3+epsilon
        # New proof uses the old interaction formula atom by atom.
        r0,r1 = map(int,rng.choice(period,size=2,replace=False))
        aa = float(rng.choice([0.0,.01,1.0,2*math.pi,10.0]))
        mask = np.zeros(period,dtype=bool); mask[r0] = True
        _, kk, _ = mixed_model(np.full(period,aa),mask,np.zeros(period,dtype=int))
        f = np.exp(2j*math.pi*r1*np.arange(period)/period)/math.sqrt(period)
        observed = float(np.vdot(f,kk@f).real)
        expected = pair_cross_closed(period,r0-r1,aa)
        maximum_kernel_error = max(maximum_kernel_error,close(observed,expected))
        if aa <= 2*math.pi:
            assert expected <= 1e-12
    print("PASS critical-density short-scale normalization and explicit ideal gap")
    print(f"  direct/symbol residual={maximum_symbol_error:.3e}; finite kernel residual={maximum_kernel_error:.3e}")
    print(f"  configurations satisfying both zero-error model budgets={accepted}/{samples}")
    print(f"  epsilon_ideal={epsilon:.15g}; conditional simple density >= {2/3+epsilon:.15g}")
    print("  pure ideal model, pair multiplicity one, normalized depths <=2*pi; not a zeta record")


def check_high_depth_charge(samples: int) -> None:
    rng = np.random.default_rng(SEED + 1)
    worst = math.inf
    for _ in range(samples):
        period = int(rng.integers(4, 20))
        depths = rng.uniform(.05, 10, period)
        pairs = rng.random(period) < .4
        loads = rng.integers(0, 3, period)
        g0, k, defect = mixed_model(depths, pairs, loads)
        j = np.arange(period)
        fourier = np.exp(2j*math.pi*np.outer(j, j)/period)/math.sqrt(period)
        diff = (j[:,None]-j[None,:])/period
        charge = 0.0
        for p in np.flatnonzero(pairs & (depths > 2*math.pi)):
            up = np.outer(fourier[:,p], fourier[:,p].conj())
            kp = 4*np.sinh(depths[p]*diff/2)**2*up
            entries = np.diag(fourier.conj().T @ kp @ fourier).real
            charge += float(np.sum((2-loads[~pairs])*np.maximum(entries[~pairs], 0)))
        norm2 = float(np.vdot(k,k).real)
        slack = defect + 2*charge - norm2
        worst = min(worst, slack)
        if slack < -1e-8*(1+norm2):
            raise AssertionError(("high-depth charge", slack, norm2))
    print("PASS arbitrary mixed depths with explicit positive high-depth leakage charge")
    print(f"  samples={samples}, depths in [0.05,10], minimum slack={worst:.3e}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', type=int, default=80)
    args = parser.parse_args()
    if not 1 <= args.samples <= 10000:
        parser.error('--samples must be in 1..10000')
    print(f"Python {platform.python_version()}; NumPy {np.__version__}; SciPy {scipy.__version__}; SymPy {sp.__version__}")
    check_exact_polynomials()
    check_weighted_prime_trace()
    check_cutoff_order()
    check_operator_transfer(args.samples)
    check_high_depth_charge(args.samples)
    check_critical_corollary(args.samples)
    print("BOUNDARY: exact symbolic identities plus numerical finite models; no Lean verification,")
    print("no source-level microscopic weighted-trace asymptotic, and no unconditional zeta improvement.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
