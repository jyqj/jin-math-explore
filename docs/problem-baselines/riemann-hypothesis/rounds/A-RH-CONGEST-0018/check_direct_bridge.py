#!/usr/bin/env python3
"""Finite self-checks for RH round 18, not an independent/formal proof."""
from __future__ import annotations
import argparse
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import mpmath as mp
import numpy as np

SEED = 2026090718
TOL = 2e-8

def basis(a: np.ndarray) -> np.ndarray:
    """Numerical range for diagnostics only; proof uses exact subspaces."""
    if not a.shape[1]:
        return np.zeros((a.shape[0], 0), dtype=complex)
    u, s, _ = np.linalg.svd(a, full_matrices=False)
    return u[:, s > 1e-10 * max(1.0, float(s.max()))]

def components(Q: int, t: np.ndarray, a: np.ndarray, m: np.ndarray):
    u = (np.arange(Q) - (Q-1)/2)/Q
    v = np.exp(2j*np.pi*u[:, None]*t)/math.sqrt(Q)
    simple = m == 1
    V = v[:, simple]
    G = v[:, ~simple]*np.sqrt(m[~simple])*np.cosh(u[:, None]*a[~simple])
    H = v[:, ~simple]*np.sqrt(m[~simple])*np.sinh(u[:, None]*a[~simple])
    S, P, N = V@V.conj().T, G@G.conj().T, H@H.conj().T
    return S+P-N, S, N, V, G, H

def continuous_energy(t, a, m, alpha):
    d = t[:, None]-t[None, :]
    K = np.zeros(d.shape, dtype=complex)
    for e in (-1, 1):
        for f in (-1, 1):
            z = d+1j*(e*a[:, None]+f*a[None, :])/(2*np.pi)
            K += np.sinc(alpha*z)**2/4
    return float((m@K@m).real / m.sum())

def sampled_pair_energy(Q, t, a, m, alpha):
    d = t[:, None]-t[None, :]
    K = np.zeros(d.shape, dtype=complex)
    for e in (-1, 1):
        for f in (-1, 1):
            z = d+1j*(e*a[:, None]+f*a[None, :])/(2*np.pi)
            K += (np.sinc(alpha*z)/np.sinc(z/Q))**2/4
    return float((m@K@m).real / m.sum())

def integral_energy(t, a, m, alpha):
    nodes, weights = np.polynomial.legendre.leggauss(160)
    total = 0.0
    for lo, hi in ((-alpha, 0), (0, alpha)):
        v = (lo+hi)/2+(hi-lo)*nodes/2
        B = (np.exp(2j*np.pi*v[:, None]*t)*np.cosh(v[:, None]*a))@m
        total += (hi-lo)/2*np.dot(weights, (alpha-np.abs(v))*abs(B)**2/alpha**2)
    return float(total/m.sum())

def run(samples: int) -> dict:
    rng = np.random.default_rng(SEED)
    residuals: dict[str, float] = {}
    slacks: dict[str, float] = {}
    counts: dict[str, int] = {}
    def tick(name, amount=1):
        counts[name] = counts.get(name, 0)+amount
    def equal(name, left, right):
        l, r = np.asarray(left), np.asarray(right)
        error = float(np.max(np.abs(l-r))) if l.size else 0.0
        scale = 1+float(np.max(np.abs(l)))+float(np.max(np.abs(r))) if l.size else 1.0
        residuals[name] = max(residuals.get(name, 0), error)
        if error > TOL*scale:
            raise AssertionError((name, error, scale))
    def le(name, left, right):
        slack = float(right-left)
        slacks[name] = min(slacks.get(name, math.inf), slack)
        if slack < -TOL*(1+abs(left)+abs(right)):
            raise AssertionError((name, left, right, slack))

    # Direct exact counting, not use of the closed formula as its own oracle.
    for Q in range(1, 81):
        for d in range((Q+1)//2, Q+1):
            h, c = Q-d, 2*d-Q
            assert d-h == c
            for k in range(1, Q):
                direct = sum(int(i >= k)+int(i+k < Q) for i in range(h, d))
                assert direct == 2*(max(d-k, 0)-max(h-k, 0))
                tick('exact_central_coefficients')
    for i in range(3):
        for j in range(3):
            b = (1, 0, -1)[i]+(1, 0, -1)[j]+int(i == j == 1)
            assert b*b <= 4
            tick('exact_block_multiplier_checks')
    aa, bb, rad = F(-215, 224), F(5, 336), 4162
    assert 64512*(aa*aa+bb*bb*rad)+123840*aa-25 == 0
    assert 129024*aa*bb+123840*bb == 0
    assert (F(5,192)-F(1,10000))**2-(F(10,3)+F(2,5000))*F(1,5000) == F(89617,14400000000)
    poly = lambda x: 64512*x*x+123840*x-25
    assert poly(F(1,5000)) < 0 < poly(F(1,4900))
    assert F(1,4900) < F(5,96)
    counts['exact_scalar_checks'] = 5

    models = []
    for i in range(samples):
        Q = int(rng.choice([8, 12, 16, 24, 32]))
        kind = i % 6
        if kind == 0:
            Q = int(rng.choice([12, 24, 36]))
            mm = np.tile([1,1,1,1,2,0], Q//6)
            keep = mm > 0
            m = mm[keep]
            t = np.arange(Q)[keep]+.5+rng.normal(0, 1e-3, len(m))
            a = np.where(m == 2, rng.uniform(0, 1e-3, len(m)), 0)
        else:
            n = int(rng.integers(1, 2*Q+1))
            m = rng.integers(1, 7, n)
            t = np.sort(rng.uniform(0, .9*Q, n))
            a = np.where(m % 2 == 0, rng.uniform(0, 4, n), 0)
            if kind == 1:
                t = np.linspace(.01, .21, n)  # no cell capacity bound
            elif kind == 3:
                a = np.where(m % 2 == 0, rng.uniform(4, 8, n), 0)
            elif kind == 4:
                m = np.ones(n, dtype=int)
                t = Q*np.arange(n, dtype=float)  # distinct but sampled aliases
                a = np.zeros(n)
            elif kind == 5:
                m = 2*rng.integers(1, 4, n)
                a = rng.uniform(0, 3, n)
        models.append((Q, np.asarray(t), np.asarray(a), np.asarray(m), f'type{kind}'))
    models += [
        (1, np.array([0.]), np.array([0.]), np.array([1]), 'Q1_simple'),
        (1, np.array([0.]), np.array([7.]), np.array([6]), 'Q1_pair'),
        (8, np.arange(8)+.5, np.zeros(8), np.ones(8, dtype=int), 'simple_grid'),
        (8, np.arange(8)+.5, np.full(8, 5.), np.full(8, 2), 'full_common_depth'),
        (4, np.array([.5, 2.5]), np.array([0., 0.]), np.array([2, 2]), 'sparse_double'),
        (4, np.array([0., .1, .2]), np.zeros(3), np.array([3, 4, 5]), 'odd_multiplicity')]
    nonvacuous = 0
    for Q, t, a, m, kind in models:
        T, S, N, V, G, H = components(Q, t, a, m)
        n, mass = V.shape[1], int(m.sum())
        rho, s = mass/Q, n/Q
        D = n+np.linalg.norm(T, 'fro')**2-2*mass
        le('defect_nonnegative', 0., D)
        Ub = basis(G); U = Ub@Ub.conj().T
        Eb = basis((np.eye(Q)-U)@V); E = Eb@Eb.conj().T
        Fp = np.eye(Q)-U-E
        Qop = 2*U+E; R = T-Qop; J = Qop-np.eye(Q)
        xi = float(np.trace(U@S).real)
        zeta = float(np.trace((np.eye(Q)-U)@N).real)
        zeta_F = float(np.trace(Fp@N).real)
        exact_slack = np.linalg.norm(R, 'fro')**2+2*(mass-n-2*Ub.shape[1])+2*xi+2*zeta+2*zeta_F+n-Eb.shape[1]
        equal('signed_slack', D, exact_slack)
        le('allocated_defect', np.linalg.norm(R, 'fro')**2+2*xi, D)
        equal('flat_simple_diagonal', np.diag(S), np.full(Q, s))
        VU, VE = U@V, E@V
        all_C = []
        for d in range((Q+1)//2, Q+1):
            h, c = Q-d, 2*d-Q
            mask = (np.arange(Q) >= h)&(np.arange(Q) < d)
            all_C.append(mask)
            Td, Th = T[:d, :d], T[:h, :h]
            equal('central_row_identity', np.linalg.norm(Td, 'fro')**2-np.linalg.norm(Th, 'fro')**2, np.diag(T@T)[mask].real.sum())
            alpha = d/Q; w = 2*alpha-1
            lhs = np.linalg.norm(Td, 'fro')**2/(alpha**2*Q)
            rhs = w/alpha**2*(2*rho-s)+(1-alpha)/alpha**2*rho*rho-math.sqrt((4*w+2*s)*max(D/Q,0))/alpha**2
            le('mixed_short_floor', rhs, lhs)
            nonvacuous += int(rhs > 0)
            tick('integer_short_dimensions')
        all_C += [rng.random(Q) < .5, np.zeros(Q, dtype=bool)]
        for mask in all_C:
            C = np.diag(mask.astype(float)); c = int(mask.sum())
            B = C@J+J@C+E@C@E
            residual_part = float(np.trace(B@R).real)
            positive_part = float(np.trace(C@(R@R+U@S@U+E@N@E)).real)
            cross = 2*float(np.trace(C@VU@VE.conj().T).real)
            row_value = float(np.trace(C@(T@T-2*T+S)).real)
            equal('mixed_selected_expansion', row_value, residual_part+positive_part+cross)
            le('block_multiplier_norm', np.linalg.norm(B, 'fro'), 2*math.sqrt(c))
            le('mixed_selected_bound', -math.sqrt((4*c+2*n)*max(D,0)), row_value)
            tick('selected_coordinate_tests')
        tick('mixed_models')
    counts['positive_mixed_floors'] = nonvacuous

    for i in range(samples):
        Q = int(rng.choice([8, 12, 20, 32, 48]))
        theta = [.25, .5, .9, .99][i%4]
        n = int(rng.integers(2, Q+1))
        t = np.sort(rng.uniform(0, theta*Q, n)); t[0], t[-1] = 0., theta*Q
        m = rng.integers(1, 7, n)
        a = np.where(m % 2 == 0, rng.uniform(0, 3, n), 0.)
        T = components(Q, t, a, m)[0]
        mass = int(m.sum()); A = float(a.max())
        Ctheta = 2/math.pi**2*((1-theta)**-2+(1-theta)**-1)
        for alpha in (.5, .75, 1.):
            d = int(alpha*Q)
            discrete = float(np.linalg.norm(T[:d,:d], 'fro')**2/(alpha**2*mass))
            paired = sampled_pair_energy(Q, t, a, m, alpha)
            cont = continuous_energy(t, a, m, alpha)
            equal('sampled_pair_dictionary', discrete, paired)
            weight = float(np.dot(m, np.exp(alpha*a)))
            sharper = Ctheta*weight**2/(mass*alpha**2*Q**2)
            coarse = Ctheta*mass*math.exp(2*alpha*A)/(alpha**2*Q**2)
            le('alias_comparison', abs(discrete-cont), sharper)
            le('alias_weight_majorant', sharper, coarse)
            if i < 8:
                equal('integral_kernel', integral_energy(t,a,m,alpha), cont)
                tick('independent_integral_evaluations')
            tick('alias_scale_comparisons')
    # Scalar complex pair formula versus partial-fraction remainder bound.
    for i in range(120):
        Q = int(rng.choice([8, 16, 32])); alpha = [.5,.75,1.][i%3]; theta = [.2,.6,.95][i%3]
        z = complex(rng.uniform(-theta*Q,theta*Q),rng.uniform(-3,3))
        H = 1/np.sin(np.pi*z/Q)**2-1/(np.pi*z/Q)**2
        Ctheta = 2/math.pi**2*((1-theta)**-2+(1-theta)**-1)
        le('partial_fraction_bound', abs(H), Ctheta)
        difference = (np.sinc(alpha*z)/np.sinc(z/Q))**2-np.sinc(alpha*z)**2
        formula = np.sin(np.pi*alpha*z)**2*H/(alpha**2*Q**2)
        equal('alias_remainder_identity', difference, formula)
        tick('complex_remainder_cases')

    alias_guards = []
    for Q in (4, 8, 16, 32, 64):
        t = np.array([0., float(Q)]); a = np.zeros(2); m = np.ones(2, dtype=int)
        T = components(Q,t,a,m)[0]
        for alpha in (.5,.75,1.):
            d = int(alpha*Q)
            disc = float(np.linalg.norm(T[:d,:d], 'fro')**2/(alpha**2*2))
            cont = continuous_energy(t,a,m,alpha)
            equal('resonant_alias_guard', disc-cont, 1.)
            tick('resonant_alias_guards')
        alias_guards.append({'Q':Q,'difference':disc-cont})
    mp.mp.dps = 80
    eps = (10*mp.sqrt(4162)-645)/672
    sigma = mp.mpf(2)/3+eps
    old = mp.mpf(3)/2-mp.cot(1/mp.sqrt(2))/mp.sqrt(2)
    assert eps > mp.mpf(1)/5000 and sigma < old
    scalar = {'epsilon_root':mp.nstr(eps,50),'source_candidate_fraction':mp.nstr(sigma,50),
              'source_reference_stronger_fraction':mp.nstr(old,50),
              'not_a_new_best_bound':True,'rational_epsilon_lower':'1/5000',
              'rational_squared_gap':'89617/14400000000'}
    return {'ok':True,'attempt':'A-RH-CONGEST-0018','seed':SEED,'samples':samples,
            'counts':counts,'maximum_residuals':residuals,'minimum_slacks':slacks,
            'scalar':scalar,'resonant_alias_examples':alias_guards,
            'backend':{'python':platform.python_version(),'numpy':np.__version__,'mpmath':mp.__version__},
            'numerical_tolerance':TOL,'range_threshold':'1e-10*max(1,largest singular value)',
            'scope':'finite exact checks and numerical regressions; no actual zero computation',
            'independent_verification':False,'mathematical_truth_verified':False}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples',type=int,default=120)
    parser.add_argument('--output',type=Path,default=Path('validation.json'))
    parser.add_argument('--check-package',action='store_true')
    args = parser.parse_args()
    if args.check_package:
        root=Path(__file__).resolve().parent
        cp=json.loads((root/'checkpoint.json').read_text())
        for name, expected in cp['sha256'].items():
            if Path(name).name != name or hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
                raise ValueError('artifact mismatch: '+name)
        claims=json.loads((root/'claims.json').read_text())['claims']
        assert len({c['id'] for c in claims})==len(claims)
        assert all(c['evidence_grade']=='proof_candidate' and c['cannot_imply'] for c in claims)
        print(json.dumps({'ok':True,'hashes':len(cp['sha256']),'claims':len(claims),'scope':'integrity only'}))
        return 0
    if not 1<=args.samples<=2000:
        parser.error('--samples must be between 1 and 2000')
    result=run(args.samples)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'counts':result['counts'],'output':str(args.output)},sort_keys=True))
    return 0

if __name__=='__main__':
    sys.exit(main())
