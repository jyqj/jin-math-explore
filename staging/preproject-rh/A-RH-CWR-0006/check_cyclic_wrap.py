#!/usr/bin/env python3
"""Reproducible finite checks for A-RH-CWR-0006.

Exact integer/rational checks are separate from seeded floating-point tests.
No test asserts that a matrix countermodel is a zeta-zero configuration.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
import platform

import mpmath as mp
import numpy as np


def hs2(a: np.ndarray) -> float:
    return float(np.vdot(a, a).real)


def fourier(p: int) -> np.ndarray:
    j = np.arange(p)
    return np.exp(2j * np.pi * np.outer(j, j) / p) / math.sqrt(p)


def toeplitz(lower: np.ndarray) -> np.ndarray:
    p = len(lower)
    i, j = np.indices((p, p))
    return np.where(i >= j, lower[np.abs(i-j)], lower[np.abs(i-j)].conj())


def cyclic_average(a: np.ndarray) -> np.ndarray:
    p = len(a)
    f = fourier(p)
    beta = np.diag(f.conj().T @ a @ f).real
    return (f * beta) @ f.conj().T


def wrap_formula(a: np.ndarray, phase: float = 0.0) -> float:
    p = len(a)
    lower = a[:, 0]
    return sum(n*(p-n)/p * abs(lower[n] - np.exp(2j*np.pi*phase)*lower[p-n].conjugate())**2
               for n in range(1, p))


def spectral_round(a: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = len(a)
    f = fourier(p)
    beta = np.diag(f.conj().T @ a @ f).real
    marks = np.empty(p)
    marks[np.argsort(beta)] = np.sort(target)
    return (f * marks) @ f.conj().T, marks


def far_lag(p: int) -> np.ndarray:
    if p < 6 or p % 6:
        raise ValueError('period must be a positive multiple of six')
    n = 5*p//6
    q = np.eye(p, dtype=np.int64)
    for j in range(p-n):
        q[j+n, j] = q[j, j+n] = 1
    return q


def exact_checks(max_period: int) -> dict:
    counts = 0
    for p in range(6, max_period+1, 6):
        k, n = p//6, 5*p//6
        q = far_lag(p)
        eye = np.eye(p, dtype=np.int64)
        t = q-eye
        assert np.array_equal(t @ t @ t, t)
        assert np.array_equal(q @ (q-eye) @ (q-2*eye), np.zeros_like(q))
        assert int(np.trace(q)) == p
        assert int(np.trace(q @ q)) == 4*p//3
        assert (p-2*k) + int(np.trace(q @ q)) - 2*p == 0
        for d in range(1, p+1):
            alpha = Fraction(d, p)
            short = Fraction(d + 2*max(d-n, 0), p) / alpha**2
            budget = 1/alpha + alpha/3
            assert short <= budget
            assert int(np.sum(q[:d, :d]**2)) == d + 2*max(d-n, 0)
            if d <= n:
                assert short == 1/alpha
            counts += 1
        # Exact cyclic-average entries for this sparse example.
        c = np.eye(p, dtype=object)
        for j in range(p):
            c[(j+k) % p, j] = Fraction(1, 6)
            c[(j-k) % p, j] = Fraction(1, 6)
        wrap = sum((Fraction(int(q[i,j]))-c[i,j])**2 for i in range(p) for j in range(p))
        assert wrap / p == Fraction(5, 18)
        shifted = np.roll(np.roll(q, 1, axis=0), 1, axis=1)
        assert int(np.sum((q-shifted)**2)) == 4
    # The polynomial proving all-real alpha in [5/6,1] has nonnegative factors.
    # alpha^3-6alpha+5=(1-alpha)(5-alpha-alpha^2).
    # Exact fixed P=12 single-window witness.
    q = far_lag(12)
    assert np.array_equal(q[:9,:9], np.eye(9, dtype=int))
    mp.mp.dps = 70
    omega_star = (mp.mpf(59) - 24*mp.sqrt(6))/288
    assert omega_star > 0
    return {
        'status':'PASS', 'integer_periods':f'multiples of 6 in [6,{max_period}]',
        'rational_all_row_counts_tested':counts,
        'polynomial_factorization':'alpha^3-6alpha+5=(1-alpha)(5-alpha-alpha^2)',
        'countermodel_simple_spectral_fraction':'2/3',
        'countermodel_normalized_wrap_squared':'5/18',
        'countermodel_one_step_shift_squared':'4',
        'conditional_zero_remainder_wrap_threshold':mp.nstr(omega_star,65),
        'threshold_formula':'(59-24*sqrt(6))/288',
    }


def local_match(x: np.ndarray, mass: np.ndarray, h: float) -> dict:
    if len(x) == 0 or not 0 < h < 0.25:
        raise ValueError('nonempty points and 0<h<1/4 required')
    if not np.all(np.isin(mass, [1,2])):
        raise ValueError('the lemma assumes masses 1 or 2')
    w = float(mass.sum())
    r = float(np.ptp(x))
    dif = x[:,None]-x[None,:]
    energy_kernel = np.sinc(dif)**2
    np.fill_diagonal(energy_kernel,0)
    energy = float(mass @ energy_kernel @ mass)
    torus = dif-np.rint(dif)
    costs = torus**2 @ mass
    pivot = int(np.argmin(costs))
    phase = float(x[pivot])
    labels = np.rint(x-phase).astype(np.int64)
    err = x-phase-labels
    good = np.abs(err) <= h
    bad_mass = float(mass[~good].sum())
    kept = []
    for label in np.unique(labels[good]):
        group = np.flatnonzero(good & (labels == label))
        kept.append(int(group[np.argmax(mass[group])]))
    kept = np.array(kept, dtype=int)
    collision_mass = float(mass[good].sum()-mass[kept].sum())
    phase_bound = np.pi**2*r*r*energy/(4*w)
    collision_bound = energy/(2*np.sinc(2*h)**2)
    tol = 2e-10*(1+energy+phase_bound)
    assert float(costs[pivot]) <= phase_bound+tol
    assert bad_mass <= phase_bound/h**2+tol
    assert collision_mass <= collision_bound+tol
    assert len(np.unique(labels[kept])) == len(kept)
    assert np.all(np.abs(err[kept]) <= h)
    assert float(np.sum(mass[kept]*err[kept]**2)) <= phase_bound+tol
    return {'energy':energy,'phase_cost':float(costs[pivot]),'phase_bound':float(phase_bound),
            'bad_mass':bad_mass,'collision_mass':collision_mass,'collision_bound':float(collision_bound),
            'retained':int(len(kept)), 'mass':w}


def numerical_checks(samples: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    metrics = {'max_wrap_formula_residual':0.,'max_shift_average_residual':0.,
               'max_projection_rounding_ratio':0.,'max_general_rounding_ratio':0.,
               'max_twisted_formula_residual':0.,'max_one_step_formula_residual':0.,'min_conditional_budget_slack':float('inf'),
               'max_discarded_bessel_ratio':0.}
    for trial in range(samples):
        p = int(rng.integers(3,29))
        lower = (rng.normal(size=p)+1j*rng.normal(size=p))/math.sqrt(p)
        lower[0] = 1
        a = toeplitz(lower)
        c = cyclic_average(a)
        dist = hs2(a-c)
        wf = wrap_formula(a)
        metrics['max_wrap_formula_residual'] = max(metrics['max_wrap_formula_residual'],abs(dist-wf))
        assert abs(dist-wf) <= 1e-10*(1+dist)
        shifts = sum(hs2(a-np.roll(np.roll(a,r,axis=0),r,axis=1)) for r in range(p))/(2*p)
        metrics['max_shift_average_residual'] = max(metrics['max_shift_average_residual'],abs(dist-shifts))
        assert abs(dist-shifts) <= 1e-10*(1+dist)
        shift_error = hs2(a-np.roll(np.roll(a,1,axis=0),1,axis=1))
        shift_formula = 2*sum(abs(lower[n]-lower[p-n].conjugate())**2 for n in range(1,p))
        metrics['max_one_step_formula_residual'] = max(metrics['max_one_step_formula_residual'],abs(shift_error-shift_formula))
        assert abs(shift_error-shift_formula) <= 1e-10*(1+shift_error)
        assert dist/p <= shift_error/8 + 1e-10
        tau = float(rng.random())
        dvec = np.exp(2j*np.pi*tau*np.arange(p)/p)
        at = dvec.conj()[:,None]*a*dvec[None,:]
        tw = hs2(at-cyclic_average(at))
        metrics['max_twisted_formula_residual'] = max(metrics['max_twisted_formula_residual'],abs(tw-wrap_formula(a,tau)))
        assert abs(tw-wrap_formula(a,tau)) <= 1e-10*(1+tw)
        k = int(rng.integers(0,p//2+1))
        target = np.r_[np.zeros(k), np.ones(p-2*k), 2*np.ones(k)]
        z = rng.normal(size=(p,p))+1j*rng.normal(size=(p,p))
        u,_ = np.linalg.qr(z)
        q = (u*target) @ u.conj().T
        mq,marks = spectral_round(q,target)
        dw = hs2(q-cyclic_average(q))
        ratio = hs2(q-mq)/(2*dw) if dw > 1e-20 else 0
        metrics['max_projection_rounding_ratio'] = max(metrics['max_projection_rounding_ratio'],ratio)
        assert ratio <= 1+1e-10
        assert np.array_equal(np.sort(marks),target)
        # General A: choose the closest unitary orbit point with this target spectrum.
        lam,v = np.linalg.eigh(a)
        q = (v*target) @ v.conj().T
        r = math.sqrt(hs2(a-q)/p)
        w = math.sqrt(dist/p)
        ma,marks = spectral_round(a,target)
        bound = w*w+(r+w)**2
        ratio = hs2(a-ma)/(p*bound) if bound else 0
        metrics['max_general_rounding_ratio'] = max(metrics['max_general_rounding_ratio'],ratio)
        assert ratio <= 1+1e-10
        # Correctly conditional budgets; this does not claim source hypotheses hold.
        d = max(p//2+1, 3*p//4)
        if d < p:
            alpha = d/p
            s = (p-2*k)/p
            x = s-2/3
            e1 = hs2(a-np.eye(p))/p
            ash = a[:d,:d]/alpha-np.eye(d)/alpha
            u1 = max(0., e1-1/3, r*r-x)
            u2 = max(0., hs2(ash)/p-alpha/3)
            f = (2*alpha-1)/alpha**2
            lhs = math.sqrt(max(0., f*(1/3-x)))
            rhs = math.sqrt(alpha/3+u2)+math.sqrt(w*w+(math.sqrt(max(0.,x+u1))+w)**2)/math.sqrt(alpha)
            slack = rhs-lhs
            metrics['min_conditional_budget_slack'] = min(metrics['min_conditional_budget_slack'],slack)
            assert slack >= -1e-9
        # Positive discarded operator, assuming its actual Bessel upper bound.
        v = rng.normal(size=(p, max(1,p//3)))+1j*rng.normal(size=(p,max(1,p//3)))
        v /= np.linalg.norm(v,axis=0)
        weights = rng.integers(1,3,size=v.shape[1])
        hmat = (v*weights) @ v.conj().T
        b = float(np.linalg.eigvalsh(hmat)[-1])
        ratio = hs2(hmat)/(b*float(weights.sum()))
        assert ratio <= 1+1e-10
        metrics['max_discarded_bessel_ratio'] = max(metrics['max_discarded_bessel_ratio'],ratio)
    # Finite local extraction: random and near-lattice/collision configurations.
    for trial in range(samples):
        n = int(rng.integers(1,31))
        if trial % 2:
            x = rng.integers(-5,6,size=n)+rng.uniform(-0.045,0.045,size=n)+0.37
        else:
            x = rng.uniform(-5,5,size=n)
        local_match(x, rng.integers(1,3,size=n),0.1)
    example = local_match(np.array([0.02,1.01,2.02,2.03,3.00,4.01]),np.ones(6,dtype=int),0.1)
    assert example['collision_mass'] == 1
    # Vanishing count fraction alone does not make operator mass small.
    for k in range(2,30):
        p = k*k
        discarded_count_fraction = Fraction(k,p)
        normalized_hs2 = Fraction(k*k,p)
        assert discarded_count_fraction == Fraction(1,k) and normalized_hs2 == 1
    return {'status':'PASS','samples':samples,'seed':seed,'periods':'3..28',
            'metrics':metrics,'local_matching_samples':samples,
            'local_collision_example':example,
            'scope_guard':'k collinear discarded unit atoms in dimension k^2 have count fraction 1/k but normalized HS energy 1'}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples',type=int,default=120)
    parser.add_argument('--max-period',type=int,default=120)
    parser.add_argument('--seed',type=int,default=2026090506)
    parser.add_argument('--output',type=Path,default=Path('validation.json'))
    args = parser.parse_args()
    if not 1 <= args.samples <= 10000 or not 6 <= args.max_period <= 600:
        parser.error('samples must be 1..10000 and max-period 6..600')
    result = {'backend':{'python':platform.python_version(),'numpy':np.__version__,'mpmath':mp.__version__},
              'exact':exact_checks(args.max_period),
              'numerical':numerical_checks(args.samples,args.seed),
              'boundary':'Integer/rational subchecks plus seeded numerical tests; analytic statements remain solver proof candidates. No actual-zeta realization, source error closure, Lean build or independent verification.'}
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False))

if __name__ == '__main__':
    main()
