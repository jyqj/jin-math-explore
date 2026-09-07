#!/usr/bin/env python3
"""A-RH-HSTAB-0015: exact finite checks and numerical regressions, not verification."""
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

SEED = 2026090715
B_STAR = 16 / 3


def moment(m, t, a, alpha):
    q = len(m)
    x = np.arange(q) / q
    b = (np.exp(2j * np.pi * x[:, None] * t) * np.cosh(x[:, None] * a)) @ m / q
    energy = (float(np.mean(m)) ** 2 / alpha
              + 2 / alpha**2 * np.dot(np.maximum(alpha-x[1:], 0), abs(b[1:])**2))
    return float(energy), b


def matrix(b):
    k = np.arange(len(b))[:, None] - np.arange(len(b))[None, :]
    return np.where(k >= 0, b[abs(k)], b[abs(k)].conj())


def finite_energy(m, t, a, alpha):
    d = t[:, None] - t[None, :]
    kernel = np.zeros(d.shape, dtype=complex)
    for e in (-1, 1):
        for f in (-1, 1):
            kernel += np.sinc(alpha * (d-1j*(e*a[:, None]+f*a[None, :])/(2*np.pi)))**2 / 4
    return float(np.sum(m[:, None]*m[None, :]*kernel).real)


def boundary(alpha, cap, length):
    return math.cosh(alpha*cap)**2 / length * (8+32*(2+math.log(length))/(math.pi**2*alpha**2))


def hole_error(alpha, defect, clipped=True):
    w = 2*alpha-1
    if clipped:
        # Stable evaluation of w-(sqrt(w)-sqrt(defect))_+^2.
        z = min(max(defect, 0), w)
        return (2*math.sqrt(w*z)-z) / alpha**2
    return 2*math.sqrt(w*max(defect, 0)) / alpha**2


def constants(alpha, cap):
    ca = 7+B_STAR/4*(2*math.cosh(cap)+1+math.sqrt(4*math.cosh(cap)**2-3))
    u = math.sqrt(2*B_STAR/alpha)*math.cosh(alpha*cap/2)
    v = math.sqrt(2*B_STAR/alpha)*math.sinh(alpha*cap/2)
    c = (math.cosh(alpha*cap/2)-1)/cap if cap else 0
    z = math.sinh(alpha*cap/2)/cap if cap else alpha/2
    x = math.pi*alpha*(u+2/math.sqrt(alpha))
    y = (u+2/math.sqrt(alpha))*c+v*z
    return ca, math.hypot(x/2, 2*y)


def mixed_error(alpha, cap, length, defect):
    f = (2*alpha-1)/alpha**2
    c = 1/alpha-f
    ca, r = constants(alpha, cap)
    eta = ca*(math.pi**2*length**2+cap**2/4)*max(defect, 0)
    wrap = 32*(3+math.log(length+2))/(math.pi**2*alpha**2*length)
    return (2*c/(length+2)+wrap+2*r*math.sqrt(2*eta/alpha)
            +hole_error(alpha, max(defect, 0)+2*boundary(1, cap, length), False)
            +2*boundary(alpha, cap, length))


def rational_certificate():
    length = 2**24
    tiny = F(1, 10**24)
    b1 = F(25, 16*length)*(8+F(32, 9)*26)
    ba = F(25, 16*length)*(8+F(512, 81)*26)
    wrap = F(512, 81)*28/length
    x = F(22, 7)*F(3, 4)*(F(9, 2)+F(12, 5))
    y = (F(9, 2)+F(12, 5))*F(9, 64)+F(3, 2)*F(27, 64)
    tests = [
        (x*x/4+4*y*y, F(100)),
        (F(43, 3), F(15)),
        (F(151)*F(8, 3), F(441)),
        (F(512, 81), F(9)),
        (F(420*length, 10**12), F(1, 100)),
        (tiny+2*b1, F(1, 40000)),
        (F(8, 9*(length+2))+wrap+2*ba, F(1, 1000)),
        (F(13, 500)+F(8, 9)*tiny, F(5, 108)),
    ]
    for left, right in tests:
        assert left < right, (left, right)
    assert F(5, 108)-F(13, 500) == F(137, 6750)
    return {'comparisons': len(tests), 'L': length, 'delta_cap': str(tiny),
            'error_upper': '13/500', 'residual_gap': '137/6750',
            'scope': 'exact rational comparisons; analytic constant majorants are in proof.md'}


def run(samples):
    rng = np.random.default_rng(SEED)
    min_slack, max_residual, counts = {}, {}, {}
    def count(name, number=1):
        counts[name] = counts.get(name, 0)+number
    def le(name, left, right):
        slack = float(right-left)
        min_slack[name] = min(min_slack.get(name, math.inf), slack)
        if slack < -2e-8*(1+abs(left)+abs(right)):
            raise AssertionError((name, left, right))
        count(name)
    def eq(name, left, right):
        residual = float(np.max(abs(np.asarray(left)-np.asarray(right))))
        max_residual[name] = max(max_residual.get(name, 0), residual)
        if residual > 2e-8*(1+float(np.max(abs(np.asarray(right))))):
            raise AssertionError((name, residual))
        count(name)

    coefficient_checks = 0
    for q in range(1, 97):
        for d in range((q+1)//2, q+1):
            h = q-d
            for k in range(q):
                left = d-h if k == 0 else 2*(max(d-k, 0)-max(h-k, 0))
                right = d-h if k == 0 else sum(int(i >= k)+int(i+k < q) for i in range(h, d))
                assert left == right
                coefficient_checks += 1

    # Independent abstract projection-row inequality; Toeplitz is NOT required here.
    for _ in range(samples):
        q = int(rng.integers(2, 25))
        u, _ = np.linalg.qr(rng.normal(size=(q, q))+1j*rng.normal(size=(q, q)))
        rank = int(rng.integers(q+1)); p = u[:, :rank]@u[:, :rank].conj().T
        r = rng.normal(size=(q, q))+1j*rng.normal(size=(q, q)); r = (r+r.conj().T)/2
        r *= 10**rng.uniform(-5, 0)/max(np.linalg.norm(r), 1e-30)
        t = 2*p+r; n = int(rng.integers(1, q+1)); ix = rng.choice(q, n, replace=False)
        x = np.linalg.norm(r[:, ix]); df = np.linalg.norm(r)**2
        tr = float(np.diag(t@t-2*t)[ix].sum().real)
        eq('projection_row_expansion', tr, 2*np.trace((2*p-np.eye(q))[ix, :]@r[:, ix]).real+x*x)
        mu = n-max(math.sqrt(n)-math.sqrt(df), 0)**2
        le('projection_row_lower', -mu, tr)

    hole_cases = []
    for i in range(samples):
        q = int(rng.integers(2, 49)); occupied = int(rng.integers(q+1))
        m = np.zeros(q); m[rng.choice(q, occupied, replace=False)] = 2
        cap = [0.0, math.log(2), 2.0, 8.0][i % 4]
        tau = rng.random(q); a = rng.random(q)*cap; a[m == 0] = 0
        if i % 5 == 0:
            tau = 0.5+rng.normal(0, 1e-5, q)
            a = np.where(m == 2, rng.random(q)*1e-5, 0)
        hole_cases.append((m, tau, a))
    hole_cases += [(np.array([0.]), np.array([0.]), np.array([0.])),
                   (np.array([2.]), np.array([0.6]), np.array([12.])),
                   (np.array([2., 0., 2., 0.]), np.full(4, 0.5), np.zeros(4)),
                   (np.full(4, 2.), np.full(4, 0.3), np.full(4, 2.0)),
                   (np.array([2., 2.]), np.array([0.99, 0.01]), np.array([0., 0.1]))]
    for m, tau, a in hole_cases:
        q = len(m); t = np.arange(q)+tau; rho = float(np.mean(m)); r = np.count_nonzero(m)
        e1, b = moment(m, t, a, 1); defect = e1-2*rho; tmat = matrix(b)
        le('hole_defect_nonnegative', 0, defect)
        eq('finite_reconstruction', np.linalg.norm(tmat)**2/q, e1)
        u = (np.arange(q)-(q-1)/2)/q
        v = np.exp(2j*np.pi*u[:, None]*t)*np.sqrt(m)/math.sqrt(q)
        g, h = v*np.cosh(u[:, None]*a), v*np.sinh(u[:, None]*a)
        eq('signed_matrix', g@g.conj().T-h@h.conj().T, tmat)
        ug, singular, _ = np.linalg.svd(g, full_matrices=False)
        rank = int(np.count_nonzero(singular > 1e-11*max(1, singular[0])))
        proj = ug[:, :rank]@ug[:, :rank].conj().T
        residual = tmat-2*proj
        rhs = np.linalg.norm(residual)**2+4*(r-rank)+4*np.linalg.norm((np.eye(q)-proj)@h)**2
        eq('signed_slack', q*defect, rhs)
        for d in sorted(set([(q+1)//2, max((q+1)//2, 3*q//4), q])):
            hsize = q-d
            left = np.linalg.norm(tmat[:d, :d])**2
            right = np.linalg.norm(tmat[:hsize, :hsize])**2+np.sum(abs(tmat[hsize:d, :])**2)
            eq('row_identity', left, right)
        for alpha in (0.5, 0.625, 0.75, math.sqrt(0.5), 0.9, 1.0):
            ea, _ = moment(m, t, a, alpha)
            floor = (2*(2*alpha-1)*rho+(1-alpha)*rho*rho)/alpha**2
            le('uniform_hole_floor', floor-hole_error(alpha, defect), ea)
        # Rational-alpha argument repeats the PATTERN, not the finite matrix.
        rep = 4
        mm, aa = np.tile(m, rep), np.tile(a, rep)
        tt = np.arange(rep*q)+np.tile(tau, rep)
        ep, _ = moment(mm, tt, aa, 0.75)
        eq('period_replication', ep, moment(m, t, a, 0.75)[0])

    for i in range(samples):
        q = int(rng.choice([6, 12, 18, 24, 30])); k = int(rng.integers(q//2+1))
        m = np.array([2.]*k+[0.]*k+[1.]*(q-2*k)); rng.shuffle(m)
        tau = rng.random(q); cap = [0.0, math.log(2), 1.5][i % 3]
        a = np.where(m == 2, rng.random(q)*cap, 0); s = float(np.mean(m == 1))
        e1, _ = moment(m, np.arange(q)+tau, a, 1); defect = e1+s-2
        le('mixed_defect_nonnegative', 0, defect)
        for length in (2, 5, 8):
            p = math.lcm(q, length)
            bad_mass = bad_count = bad_defect = 0.0
            longsum = 0.0; bads = []; good_short = {}; bad_short = {}
            for start in range(0, p, length):
                ix = np.arange(start, start+length) % q
                mb, ab = m[ix], a[ix]; tb = np.arange(length)+tau[ix]
                mass = float(mb.sum()); n = int(np.count_nonzero(mb == 1))
                el = finite_energy(mb, tb, ab, 1); longsum += el
                le('finite_block_defect', 0, el+n-2*mass)
                if n == 0:
                    bad_mass += mass; bad_count += 1
                    eper, _ = moment(mb, tb, ab, 1)
                    db = eper-2*mass/length
                    bad_defect += length*max(db, 0)
                    le('bad_periodization_long', abs(eper-el/length), boundary(1, cap, length))
                    bads.append((mb, tb, ab, mass/length, db))
                for alpha in (0.625, 0.75, 0.9):
                    value = finite_energy(mb, tb, ab, alpha)
                    target = bad_short if n == 0 else good_short
                    target[alpha] = target.get(alpha, 0)+value
                    count('finite_block_short_evaluations')
            beta, hm = bad_count*length/p, bad_mass/p
            le('total_block_defect_budget', longsum/p+s-2, defect+boundary(1, cap, length))
            le('bad_defect_average', bad_defect/p, max(defect, 0)+(1+beta)*boundary(1, cap, length))
            for alpha in (0.625, 0.75, 0.9):
                f = (2*alpha-1)/alpha**2; c = 1/alpha-f
                massfloor = 2*f*hm+(c*hm*hm/beta if beta else 0)
                baderr = 2*math.sqrt(2*alpha-1)/alpha**2*math.sqrt(beta*(max(defect, 0)+(1+beta)*boundary(1, cap, length)))+beta*boundary(alpha, cap, length)
                le('bad_average_floor', massfloor-baderr, bad_short.get(alpha, 0)/p)
                ea, _ = moment(m, np.arange(q)+tau, a, alpha)
                le('signed_localization', abs(ea-(good_short.get(alpha, 0)+bad_short.get(alpha, 0))/p), boundary(alpha, cap, length))
                le('assembled_mixed_floor', f*(2-s)+c-mixed_error(alpha, cap, length, defect), ea)
        if i < 12:
            # Different implementation: continuous triangular-weight integral.
            nodes, weights = np.polynomial.legendre.leggauss(128)
            tb = np.arange(6)+tau[:6]; mb, ab = m[:6], a[:6]; alpha = 0.75
            val = 0.0
            for lo, hi in ((-alpha, 0), (0, alpha)):
                x = (hi-lo)*nodes/2+(hi+lo)/2
                transform = (np.exp(2j*np.pi*x[:, None]*tb)*np.cosh(x[:, None]*ab))@mb
                val += float(np.dot(weights*(hi-lo)/2, (alpha-abs(x))*abs(transform)**2/alpha**2))
            eq('integral_kernel', val, finite_energy(mb, tb, ab, alpha))

    # Scope guard: the hole theorem cannot be applied unchanged to simple atoms.
    simple_energy = moment(np.array([1.]), np.array([0.5]), np.array([0.]), 0.75)[0]
    assert simple_energy < 20/9
    rational = rational_certificate()
    mp.mp.dps = 70
    d = mp.mpf('1e-24'); length = 2**24; aa = mp.mpf(3)/4; cap = mp.log(2)
    # The scalar formula is evaluated in binary64 as a regression; rational bounds certify sufficiency.
    error_value = mixed_error(0.75, math.log(2), length, float(d))
    assert error_value < 13/500
    return {'ok': True, 'attempt': 'A-RH-HSTAB-0015', 'seed': SEED, 'samples': samples,
            'hole_models': len(hole_cases), 'mixed_models': samples, 'counts': counts,
            'exact_row_coefficient_checks': coefficient_checks, 'rational_certificate': rational,
            'minimum_slacks': min_slack, 'maximum_residuals': max_residual,
            'finite_scalar_example': {'A': 'log(2)', 'L': length, 'delta': '1e-24',
                'error_binary64': error_value, 'short_floor_binary64': 44/27-error_value,
                'exact_error_upper': '13/500'},
            'scope_guard': {'all_simple_energy': '4/3', 'invalid_hole_floor': '20/9'},
            'universal_modulus_coefficient': mp.nstr(16*mp.sqrt(2)/9, 50),
            'backend': {'python': platform.python_version(), 'numpy': np.__version__, 'mpmath': mp.__version__},
            'evidence': 'exact finite subchecks and sampled numerical regressions; analytic claims are proof candidates',
            'independent_verification': False, 'mathematical_truth_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', type=int, default=120)
    parser.add_argument('--output', type=Path, default=Path('validation.json'))
    parser.add_argument('--check-package', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.samples <= 1000:
        parser.error('--samples must be in 1..1000')
    if args.check_package:
        root = Path(__file__).resolve().parent
        cp = json.loads((root/'checkpoint.json').read_text())
        for name, digest in cp['sha256'].items():
            path = root/name
            if path.parent != root or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError('hash mismatch: '+name)
        claims = json.loads((root/'claims.json').read_text())['claims']
        assert len({c['id'] for c in claims}) == len(claims)
        assert all(c['evidence_grade'] == 'proof_candidate' and c['cannot_imply'] for c in claims)
        print(json.dumps({'ok': True, 'hashes': len(cp['sha256']), 'claims': len(claims), 'scope': 'package integrity only'}))
        return 0
    result = run(args.samples)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps({'ok': result['ok'], 'samples': args.samples,
                      'hole_models': result['hole_models'], 'exact_row_coefficient_checks': result['exact_row_coefficient_checks'],
                      'rational_comparisons': result['rational_certificate']['comparisons'], 'output': str(args.output)}, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
