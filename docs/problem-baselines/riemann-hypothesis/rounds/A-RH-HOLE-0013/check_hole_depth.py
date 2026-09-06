#!/usr/bin/env python3
"""Finite self-checks for A-RH-HOLE-0013; not independent/formal verification."""
from __future__ import annotations
import argparse
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import platform
import mpmath as mp
import numpy as np

SEED = 2026090713
BSTAR = 16.0 / 3.0


def spectral(m, t, a, alpha):
    q = len(m)
    v = np.arange(1, q) / q
    b = (np.exp(2j*np.pi*v[:, None]*t)*np.cosh(v[:, None]*a)) @ m/q
    return float(1/alpha+2/alpha**2*np.dot(np.maximum(alpha-v, 0), abs(b)**2))


def finite_energy(m, t, a, alpha):
    d = t[:, None]-t[None, :]
    kernel = np.zeros(d.shape, dtype=complex)
    for e in (-1, 1):
        for f in (-1, 1):
            z = alpha*(d-1j*(e*a[:, None]+f*a[None, :])/(2*np.pi))
            kernel += np.sinc(z)**2/4
    value = np.dot(m, kernel @ m)
    if abs(value.imag) > 1e-8*(1+abs(value.real)):
        raise AssertionError('non-real signed energy')
    return float(value.real)


def integral_energy(m, t, a, alpha, nodes=96):
    # Split at zero so the triangular weight is smooth on each panel.
    x, w = np.polynomial.legendre.leggauss(nodes)
    v = np.concatenate(((x-1)*alpha/2, (x+1)*alpha/2))
    weights = np.tile(w, 2)*alpha/2*(alpha-abs(v))/alpha**2
    b = (np.exp(2j*np.pi*v[:, None]*t)*np.cosh(v[:, None]*a)) @ m
    return float(weights @ (abs(b)**2))


def boundary(alpha, cap, length):
    return math.cosh(alpha*cap)**2/length*(8+32*(2+math.log(length))/(np.pi**2*alpha**2))


def depth_constants(alpha, cap):
    j = math.sqrt(2*BSTAR/alpha)*math.cosh(alpha*cap)
    k = math.sqrt(2*BSTAR*alpha)*math.sinh(alpha*cap)
    c = 2*BSTAR*math.sinh(2*alpha*cap)
    return j, k, c


def anchor_constant(cap):
    return 7+BSTAR/4*(2*math.cosh(cap)+1+math.sqrt(4*math.cosh(cap)**2-3))


def real_floor(alpha, r, s, defect):
    f = (2*alpha-1)/alpha**2
    c = 1/alpha-f
    interior = f*(2-s)+c*r/(r+2)
    wrap = 32*(3+math.log(r+2))/(np.pi**2*alpha**2*r)
    k = np.pi**2*alpha/2*(math.sqrt(2*BSTAR/alpha)+2/math.sqrt(alpha))
    return max(0, math.sqrt(max(0, interior-wrap))-k*r*math.sqrt(max(0, defect)))**2-boundary(alpha, 0, r)


def block_data(m, t, a, length):
    q = len(m)
    psize = math.lcm(q, length)
    result = []
    for start in range(0, psize, length):
        p = np.arange(start, start+length)
        ix = p % q
        mass = m[ix].copy()
        centers = p+(t[ix]-ix)
        depths = a[ix].copy()
        mu = int(mass.sum())
        simple = int(np.count_nonzero(mass == 1))
        avg = float(mass @ depths/mu) if mu and not simple else 0.0
        surrogate = np.where(mass > 0, avg, 0.0)
        variance = float(mass @ ((depths-surrogate)**2))
        result.append((mass, centers, depths, surrogate, mu, simple, variance))
    return psize, result


def rational_checks():
    count = 0
    for weights in ((2, 2), (2, 0, 2), (2, 2, 2), (1, 2, 1)):
        for i in range(9):
            for j in range(9):
                a = [F((i+p*j) % 9, 8) for p in range(len(weights))]
                mu = sum(weights)
                avg = sum(w*x for w, x in zip(weights, a))/mu
                var = sum(w*(x-avg)**2 for w, x in zip(weights, a))
                assert var == sum(w*x*x for w, x in zip(weights, a))-mu*avg*avg
                assert var <= F(mu, 4)
                count += 1
    r = 8192
    lower = F(32, 27)+F(4, 9)*F(r, r+2)-F(512, 81)*13/r
    upper = F(19, 12)+(8+F(512, 81)*12)/r
    certificate = {
        'interior_root': lower >= F(509, 400)**2,
        'budget_root': upper <= F(101, 80)**2,
        'log_bound': sum(F(10)**k/math.factorial(k) for k in range(11)) > r+2,
        'dispersion_threshold': (F(1, 100)/(125*r+4))**4 > F(1, 10**33),
        'counterexample_coefficient': F(2, 3)-F(2048, 27)/F(22, 7)**4 < F(-1, 10),
        'counterexample_remainder': -F(1, 10)*F(1, 10)**2+F(2, 5)*F(1, 10)**4 == -F(3, 3125),
        'ideal_gap': F(44, 27)-F(19, 12) == F(5, 108),
    }
    assert all(certificate.values())
    return {'weighted_variance_cases': count, 'rational_certificate': certificate,
            'safe_Omega_threshold': '1/10^33', 'counterexample_upper': '-3/3125'}


def run(samples):
    rng = np.random.default_rng(SEED)
    metrics, counts = {}, {'model_scale_checks': 0, 'block_checks': 0, 'bad_blocks': 0,
                           'positive_depth_common_blocks': 0, 'quadrature_checks': 0}
    def le(name, left, right):
        slack = float(right-left)
        metrics[name] = min(metrics.get(name, math.inf), slack)
        if slack < -5e-9*(1+abs(left)+abs(right)):
            raise AssertionError((name, left, right, slack))
    configurations = []
    for i in range(samples):
        q = int(rng.choice([3, 6, 9, 12, 18, 24]))
        pairs = int(rng.integers(0, q//2+1))
        m = np.array([2]*pairs+[0]*pairs+[1]*(q-2*pairs))
        rng.shuffle(m)
        cap = (0.0, math.log(2), 1.0)[i % 3]
        tau = rng.uniform(0, 1, q)
        a = np.where(m == 2, rng.uniform(0, cap, q), 0)
        if i % 4 == 0:
            tau = np.clip(0.5+rng.normal(0, 1e-4, q), 0, 1-1e-10)
            a *= 1e-4
        configurations.append((m, np.arange(q)+tau, a, cap))
    configurations += [
        (np.array([1]), np.array([0.5]), np.array([0.0]), 0.0),
        (np.array([2, 0]), np.array([0.5, 1.5]), np.array([0.6, 0]), 0.6),
        (np.array([2, 2, 0, 0]), np.array([0.99, 1.01, 2.5, 3.5]), np.zeros(4), 0.0),
        (np.array([1, 1, 1, 1, 2, 0]), np.arange(6)+0.5, np.zeros(6), 0.0),
    ]
    max_quad = 0.0
    for case, (m, t, a, cap) in enumerate(configurations):
        q = len(m)
        assert m.sum() == q and np.all(a[m != 2] == 0)
        s = float(np.count_nonzero(m == 1)/q)
        long = spectral(m, t, a, 1)
        real_long = spectral(m, t, a*0, 1)
        delta, d0 = s+long-2, s+real_long-2
        le('signed_nonnegative', 0, delta)
        le('real_nonnegative', 0, d0)
        for length in (2, 3, 5, 8):
            psize, blocks = block_data(m, t, a, length)
            omega = sum(row[6] for row in blocks if not row[5])/psize
            good_depth = sum(row[6] for row in blocks if row[5])/psize
            variance = omega+good_depth
            hole_mass = sum(row[4] for row in blocks if not row[5])/psize
            least = min([row[5] for row in blocks if row[5]], default=length)
            eta = anchor_constant(cap)*(np.pi**2*length**2+cap*cap/4)*max(0, delta)/least
            le('hole_variance_cap', omega, cap*cap*hole_mass/4)
            le('inherited_good_depth', good_depth, 4*eta)
            eps1 = boundary(1, cap, length)+boundary(1, 0, length)+depth_constants(1, cap)[2]*math.sqrt(4*eta+omega)
            le('real_defect_transfer', d0, delta+eps1)
            for alpha in (0.625, 0.75, 1.0):
                total, common, real = 0.0, 0.0, 0.0
                j, k, c = depth_constants(alpha, cap)
                for weights, centers, depths, surrogate, mu, simple, var in blocks:
                    ea = finite_energy(weights, centers, depths, alpha)
                    ec = finite_energy(weights, centers, surrogate, alpha)
                    e0 = finite_energy(weights, centers, depths*0, alpha)
                    le('common_depth_domination', e0, ec)
                    le('operator_HS_cap', ea, j*j*mu)
                    difference = finite_energy(np.r_[weights, -weights], np.r_[centers, centers], np.r_[depths, surrogate], alpha)
                    le('depth_operator_perturbation', difference, k*k*var)
                    le('finite_energy_perturbation', abs(ea-ec), c*math.sqrt(mu*var))
                    total += ea; common += ec; real += e0
                    counts['block_checks'] += 1
                    counts['bad_blocks'] += int(not simple)
                    counts['positive_depth_common_blocks'] += int(mu and surrogate.max() > 0)
                orig = spectral(m, t, a, alpha)
                reference = spectral(m, t, a*0, alpha)
                le('signed_localization', abs(orig-total/psize), boundary(alpha, cap, length))
                le('summed_dispersion', abs(total-common)/psize, c*math.sqrt(variance))
                epsilon = boundary(alpha, cap, length)+boundary(alpha, 0, length)+c*math.sqrt(4*eta+omega)
                le('global_realification', reference, orig+epsilon)
                for r in (2, 7, 8192):
                    le('real_floor', real_floor(alpha, r, s, d0), reference)
                    le('combined_ledger', real_floor(alpha, r, s, max(0, delta+eps1))-epsilon, orig)
                counts['model_scale_checks'] += 1
        if case < 8:
            for alpha in (0.75, 1.0):
                exact_kernel = finite_energy(m, t, a, alpha)
                quad = integral_energy(m, t, a, alpha)
                err = abs(exact_kernel-quad)
                max_quad = max(max_quad, err)
                assert err < 5e-9*(1+abs(exact_kernel))
                counts['quadrature_checks'] += 1
    mp.mp.dps = 70
    eps = mp.mpf(1)/10
    coefficient = mp.mpf(2)/3-512*(mp.pi+1)/(27*mp.pi**4)
    difference = mp.quad(lambda x: 4*(1-abs(x))*((2*mp.cos(3*mp.pi*x/2)+mp.cosh(eps*x))**2-(2*mp.cos(3*mp.pi*x/2)+1)**2), [-1, 0, 1])
    m = np.array([2, 2, 2]); t = np.array([0.5, 1.5, 2.5]); a = np.array([0, 2/15, 0])
    direct_diff = finite_energy(m, t, a, 0.75)-finite_energy(m, t, a*0, 0.75)
    assert difference < -mp.mpf(3)/3125
    assert abs(float(difference)-direct_diff) < 1e-10
    thresholds = []
    for r in (2048, 4096, 8192, 16384):
        al = mp.mpf(3)/4
        interior = mp.mpf(32)/27+mp.mpf(4)/9*r/(r+2)
        wrap = 32*(3+mp.log(r+2))/(mp.pi**2*al**2*r)
        bd = (8+32*(2+mp.log(r))/(mp.pi**2*al**2))/r
        gap = mp.sqrt(max(0, interior-wrap))-mp.sqrt(mp.mpf(19)/12+bd)
        denom = mp.pi**2*(mp.sqrt(2)+mp.sqrt(3)/2)*r*mp.sqrt(20)+mp.sqrt(28*mp.sqrt(2)/3)
        value = (max(0, gap)/denom)**4
        thresholds.append({'R': r, 'gap': mp.nstr(gap, 25), 'omega_R_log2': mp.nstr(value, 35)})
    holes = []
    for k in (6, 12, 24, 48, 96):
        m = np.array([1]*(4*k)+[0]*k+[2]*k)
        t = np.arange(6*k)+0.5; a = np.where(m == 2, math.log(2), 0)
        psize, blocks = block_data(m, t, a, 5)
        omega = sum(row[6] for row in blocks if not row[5])/psize
        h = sum(row[4] for row in blocks if not row[5])/psize
        assert abs(omega) < 1e-28
        holes.append({'Q': 6*k, 'delta': 2/3+spectral(m, t, a, 1)-2,
                      'short': spectral(m, t, a, 0.75), 'h_L5': h, 'Omega_L5': omega})
    return {'ok': True, 'attempt': 'A-RH-HOLE-0013', 'seed': SEED,
            'random_models': samples, 'boundary_models': 4, 'counts': counts,
            'rational_checks': rational_checks(), 'minimum_slacks': metrics,
            'max_kernel_quadrature_residual': max_quad,
            'counterexample': {'coefficient': mp.nstr(coefficient, 35),
                              'energy_difference': mp.nstr(difference, 35),
                              'binary64_kernel_difference': direct_diff,
                              'analytic_upper_bound': '-3/3125'},
            'thresholds': thresholds, 'hole_family': holes,
            'nonvacuous_real_floor': real_floor(0.75, 8192, 2/3, 0),
            'versions': {'python': platform.python_version(), 'numpy': np.__version__, 'mpmath': mp.__version__},
            'scope': 'exact rational subchecks and finite numerical regressions; analytic quantifiers are proof candidates',
            'independent_verification': False, 'mathematical_truth_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', type=int, default=120)
    parser.add_argument('--output', type=Path, default=Path('validation.json'))
    parser.add_argument('--check-package', action='store_true')
    args = parser.parse_args()
    if args.check_package:
        root = Path(__file__).resolve().parent
        data = json.loads((root/'checkpoint.json').read_text())
        for name, digest in data['sha256'].items():
            path = root/name
            assert path.parent == root and hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
        claims = json.loads((root/'claims.json').read_text())['claims']
        assert len({c['id'] for c in claims}) == len(claims)
        assert all(c['evidence_grade'] == 'proof_candidate' and c['cannot_imply'] for c in claims)
        print(json.dumps({'ok': True, 'hashes': len(data['sha256']), 'claims': len(claims), 'scope': 'package integrity only'}))
        return
    if not 1 <= args.samples <= 10000:
        parser.error('--samples must be in [1,10000]')
    result = run(args.samples)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps({'ok': result['ok'], 'counts': result['counts'], 'output': str(args.output)}, sort_keys=True))


if __name__ == '__main__':
    main()
