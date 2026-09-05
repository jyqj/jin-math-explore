#!/usr/bin/env python3
"""Reproducible finite checks for A-RH-CTP-0005; not a zeta theorem."""
from __future__ import annotations

import argparse
import json
import math
import platform
from fractions import Fraction as F
from pathlib import Path

import mpmath as mp
import numpy as np


def norm2(a: np.ndarray) -> float:
    return float(np.vdot(a, a).real)


def operator(loads: np.ndarray, depths: np.ndarray,
             shifts: np.ndarray | None = None) -> np.ndarray:
    p = len(loads)
    if shifts is None:
        shifts = np.zeros(p)
    rows = (np.arange(p) - (p - 1) / 2.0) / p
    difference = rows[:, None] - rows[None, :]
    out = np.zeros((p, p), dtype=complex)
    for j, mass in enumerate(loads):
        out += (mass / p) * np.exp(2j * np.pi * (j + shifts[j]) * difference) * np.cosh(depths[j] * difference)
    return out


def toeplitz(coefficients: np.ndarray) -> np.ndarray:
    p = len(coefficients)
    out = np.zeros((p, p), dtype=complex)
    for j in range(p):
        for k in range(p):
            out[j, k] = coefficients[j-k] if j >= k else np.conj(coefficients[k-j])
    return out


def tangent_energy(loads: np.ndarray, d: int) -> float:
    p = len(loads)
    alpha = d / p
    h = np.fft.fft(loads) / p
    total = 1.0 / alpha
    for n in range(1, p):
        t = n / p
        symbol = (max(alpha-t, 0.0) + max(alpha-(1-t), 0.0)) / alpha**2
        total += symbol * abs(h[n])**2
    return float(total)


def exact_and_scalar() -> dict:
    alpha = F(3, 4)
    floor = (2*alpha-1)/alpha**2
    gap = (floor-alpha)/3
    coefficient = floor+1/alpha
    assert (floor, gap, coefficient) == (F(8, 9), F(5, 108), F(20, 9))
    mp.mp.dps = 70
    eps = (mp.sqrt(106)-9)**2/1200
    lhs = mp.mpf(20)/9*eps + 2/mp.sqrt(3)*mp.sqrt(eps)
    assert abs(lhs-mp.mpf(5)/108) < mp.mpf('1e-65')
    old = (mp.sqrt(mp.mpf(119)/72)-mp.sqrt(mp.mpf(19)/12))**2/4
    # An exact rational certificate: eps > 1398/10^6.
    q = F(1398, 10**6)
    z = F(187, 1)-1200*q
    assert z > 0 and z*z > 18**2*106
    # Exact rational 3-block projection-defect identity.
    aa, bb, cc, pp, qq, rr = F(1,3), F(-7,4), F(2,5), F(3,7), F(-2,3), F(5,9)
    n_simple = 4
    norm_a = (2+aa)**2+(1+bb)**2+cc**2+2*(pp**2+qq**2+rr**2)
    norm_r = aa**2+bb**2+cc**2+2*(pp**2+qq**2+rr**2)
    assert n_simple+norm_a-2*(3+aa+bb-cc) == norm_r+2*aa+2*cc+(n_simple-1)
    for p in range(2, 100):
        for d in range(1, p+1):
            for n in range(1, d):
                assert F(d-n, p-n) <= F(d-1, p-1) <= F(d, p)
    return {"status": "PASS", "rational_scope": "all p=2..99,d=1..p,n=1..d-1 plus analytic proof in README",
            "epsilon": str(eps), "simple_floor": str(mp.mpf(2)/3+eps),
            "gain_ratio_to_parent": str(eps/old), "rational_epsilon_lower": str(q),
            "scalar_residual": str(abs(lhs-mp.mpf(5)/108))}


def run(samples: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    metrics = {"max_defect_residual": 0.0, "max_tangent_symbol_residual": 0.0,
               "min_coercivity_slack": math.inf, "max_toeplitz_contraction_ratio": 0.0,
               "max_displacement_ratio": 0.0, "max_taper_loss_ratio": 0.0,
               "max_normalized_taper_ratio": 0.0, "max_taper_center_residual": 0.0,
               "max_projection_identity_residual": 0.0, "min_perturbed_budget_slack": math.inf,
               "accepted_zero_error_models": 0}
    for trial in range(samples):
        p = 4*int(rng.integers(2, 17))
        d = 3*p//4
        alpha = d/p
        sigma = (d-1)/(p-1)
        # Equal double/vacancy counts force exact mean mass one.
        loads = np.ones(p, dtype=int)
        count = int(rng.integers(0, p//3+1))
        perm = rng.permutation(p)
        loads[perm[:count]] = 2
        loads[perm[count:2*count]] = 0
        depths = np.zeros(p)
        is_pair = (loads == 2) & (rng.random(p) < 0.8)
        depths[is_pair] = rng.uniform(0.0, 2*np.pi, np.count_nonzero(is_pair))
        g = operator(loads, depths)
        g0 = operator(loads, np.zeros(p))
        k = g-g0
        budget = float(np.sum(4*loads-loads**2))
        defect = budget-4*float(np.trace(g).real)+norm2(g)
        identity = norm2(k)-2*float(np.trace((2*np.eye(p)-g0)@k).real)
        metrics["max_defect_residual"] = max(metrics["max_defect_residual"], abs(defect-identity))
        slack = defect-norm2(k)
        metrics["min_coercivity_slack"] = min(metrics["min_coercivity_slack"], slack)
        assert slack >= -2e-9*max(1.0, norm2(k))
        assert np.max(np.abs(np.diag(k))) < 1e-12
        assert norm2(k[:d, :d]) <= sigma*norm2(k)+2e-9
        g_short, g0_short = g[:d, :d]/alpha, g0[:d, :d]/alpha
        spectral = tangent_energy(loads, d)
        metrics["max_tangent_symbol_residual"] = max(metrics["max_tangent_symbol_residual"], abs(norm2(g0_short)/p-spectral))
        s = float(np.mean(loads == 1))
        x = s-2/3
        delta = defect/p
        left = math.sqrt(max(0.0, (8/9)*(1-s)))
        right = math.sqrt(max(0.0, norm2(g_short)/p-1/alpha)) + math.sqrt(max(0.0, delta/alpha))
        assert left <= right+2e-9
        if norm2(g)/p <= 4/3+1e-12 and norm2(g_short)/p <= 19/12+1e-12:
            metrics["accepted_zero_error_models"] += 1
            assert s >= 2/3+float((mp.sqrt(106)-9)**2/1200)-2e-9

        # Exact Toeplitz contraction, independent of pair realizability.
        c = rng.normal(size=p)+1j*rng.normal(size=p)
        c[0] = 0
        t = toeplitz(c)
        contracted = norm2(t[:d, :d])
        metrics["max_toeplitz_contraction_ratio"] = max(metrics["max_toeplitz_contraction_ratio"], contracted/(sigma*norm2(t)))
        assert contracted <= sigma*norm2(t)+1e-10
        sharp = toeplitz(np.array([0, 1]+[0]*(p-2), dtype=complex))
        assert abs(norm2(sharp[:d, :d])/norm2(sharp)-sigma) < 1e-14

        # Displacements: no common depth or depth alphabet is assumed.
        shifts = rng.uniform(-0.08, 0.08, p)
        gp = operator(loads, depths, shifts)
        amax = float(max(depths))
        emax = float(max(abs(shifts)))
        weighted_rms = math.sqrt(float(np.sum(loads*shifts**2))/p)
        analytic_r = math.sqrt(2)*np.pi*math.exp(amax)*(math.exp(np.pi*emax)+1)*weighted_rms
        actual_r = math.sqrt(norm2(gp-g)/p)
        assert actual_r <= analytic_r+1e-10
        if analytic_r > 0:
            metrics["max_displacement_ratio"] = max(metrics["max_displacement_ratio"], actual_r/analytic_r)
        u1 = max(0.0, norm2(gp-np.eye(p))/p-1/3)
        u2 = max(0.0, norm2(gp[:d, :d]/alpha-np.eye(d)/alpha)/p-alpha/3)
        lifted_u1 = u1+2*actual_r*math.sqrt(1/3+u1)+actual_r**2
        radicand = x+lifted_u1
        assert radicand >= -2e-9
        rhs = math.sqrt(alpha/3+u2)+(actual_r+math.sqrt(max(0.0, radicand)))/math.sqrt(alpha)
        metrics["min_perturbed_budget_slack"] = min(metrics["min_perturbed_budget_slack"], rhs-left)
        assert rhs >= left-2e-9

        # Smoothing on r rows, with a strictly positive common normalization.
        psi = np.ones(d)
        r = max(1, d//8)
        changed = np.r_[np.arange((r+1)//2), np.arange(d-r//2, d)]
        psi[changed] = rng.uniform(0.0, 0.8, r)
        local = t[:d, :d]
        smoothed = psi[:, None]*local*psi[None, :]
        ratio_bound = 2*r/(p-d+1)
        loss = norm2(local-smoothed)
        assert loss <= ratio_bound*norm2(t)+1e-9
        metrics["max_taper_loss_ratio"] = max(metrics["max_taper_loss_ratio"], loss/(ratio_bound*norm2(t)))
        kappa = float(np.sum(psi**2))/p
        actual = math.sqrt(norm2(smoothed/kappa-local/alpha)/p)
        upper = (math.sqrt(ratio_bound)/kappa + (1/kappa-1/alpha)*math.sqrt(sigma))*math.sqrt(norm2(t)/p)
        assert actual <= upper+1e-9
        metrics["max_normalized_taper_ratio"] = max(metrics["max_normalized_taper_ratio"], actual/upper)
        tapered_g = psi[:, None]*g[:d, :d]*psi[None, :]/kappa
        diagonal = np.diag(psi**2/kappa)
        cpsi = float(np.sum(psi**4))/(p*kappa*kappa)
        center_residual = abs((norm2(tapered_g)-norm2(tapered_g-diagonal))/p-cpsi)
        metrics["max_taper_center_residual"] = max(metrics["max_taper_center_residual"], center_residual)
        assert center_residual <= 2e-9

        # General Hilbert-space projection template, without a grid hypothesis.
        du, de, df = 2, 2, 2
        qdim = du+de+df
        z = rng.normal(size=(qdim, qdim))+1j*rng.normal(size=(qdim, qdim))
        a = (z+z.conj().T)/2
        margin = float(rng.uniform(0.0, 3.0))
        a[:du, :du] += np.eye(du)*(2+(margin-float(np.trace(a[:du, :du]).real))/du)
        neg = rng.normal(size=(df, df))+1j*rng.normal(size=(df, df))
        a[-df:, -df:] = -neg@neg.conj().T
        n_simple = de+int(rng.integers(0, 4))
        normal = np.diag([2]*du+[1]*de+[0]*df)
        delta = n_simple+norm2(a)-2*float(np.trace(a).real)
        rhs = norm2(a-normal)+2*(float(np.trace(a[:du, :du]).real)-2*du)-2*float(np.trace(a[-df:, -df:]).real)+n_simple-de
        residual = abs(delta-rhs)
        metrics["max_projection_identity_residual"] = max(metrics["max_projection_identity_residual"], residual)
        assert residual <= 2e-9 and delta >= norm2(a-normal)-2e-9

    # Counterexamples to deleting hypotheses or inventing stronger factors.
    p, d = 100, 75
    sharp_ratio = (d-1)/(p-1)
    assert sharp_ratio > (d/p)**2
    arbitrary = np.zeros((p, p))
    arbitrary[0, 1] = arbitrary[1, 0] = 1
    psi = np.ones(d)
    psi[0] = 0
    local = arbitrary[:d, :d]
    lost_fraction = norm2(local-psi[:, None]*local*psi[None, :])/norm2(arbitrary)
    assert lost_fraction == 1 and 2/(p-d+1) < 1
    return {"status": "PASS", "samples": samples, "seed": seed,
            "periods": "multiples of 4 in [8,64]", "depths": "site dependent in [0,2*pi]",
            "displacements": "[-0.08,0.08]", "metrics": metrics,
            "scope_guards": {"alpha_squared_contraction_false": {"observed_ratio": sharp_ratio, "false_bound": (d/p)**2},
                             "small_edge_count_without_toeplitz_false": {"lost_fraction": lost_fraction, "false_bound": 2/(p-d+1)}}}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=int, default=160)
    parser.add_argument('--seed', type=int, default=2026090505)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.samples < 1:
        parser.error('--samples must be positive')
    result = {"backend": {"python": platform.python_version(), "numpy": np.__version__, "mpmath": mp.__version__},
              "exact_and_scalar": exact_and_scalar(), "finite_regression": run(args.samples, args.seed),
              "boundary": "Exact rational subchecks and seeded floating-point finite tests. Analytic lemmas are proof candidates, not independently verified. No zeta-zero bound or full source transfer is asserted."}
    text = json.dumps(result, indent=2, allow_nan=False)+'\n'
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    print(text, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
