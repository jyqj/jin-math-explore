#!/usr/bin/env python3
"""Finite self-checks of sparse mosaics and slow phase/depth modulation.
Analytic statements are in README. Floating checks are not interval proofs.
"""
from __future__ import annotations
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
import platform
import numpy as np
import mpmath as mp


def validate(m, tau, a, alpha):
    m, tau, a = np.asarray(m), np.asarray(tau), np.asarray(a)
    if not (len(m) == len(tau) == len(a) and len(m) >= 1):
        raise ValueError('equal nonempty arrays required')
    if not (0 < alpha <= 1 and np.all(np.isin(m, [0, 1, 2]))):
        raise ValueError('alpha in (0,1], marks 0/1/2 required')
    if not (np.all((tau >= 0) & (tau < 1)) and np.all(a >= 0)):
        raise ValueError('phases in [0,1) and nonnegative depths required')
    if np.any((m != 2) & (a != 0)):
        raise ValueError('only mark two may have nonzero depth')


def atoms(m, tau, a):
    z, w = [], []
    for p, (mm, tt, aa) in enumerate(zip(m, tau, a)):
        if mm == 0:
            continue
        if mm == 1 or aa == 0:
            z.append(complex(p+tt)); w.append(float(mm))
        else:
            z.extend([p+tt+1j*aa/(2*np.pi), p+tt-1j*aa/(2*np.pi)])
            w.extend([1., 1.])
    return np.array(z, complex), np.array(w, float)


def direct_moment(m, tau, a, alpha):
    validate(m, tau, a, alpha)
    z, w = atoms(m, tau, a)
    if not len(z):
        return 0.
    kernel = np.sinc(alpha*(z[:, None]-z[None, :]))**2
    value = np.sum(kernel*w[:, None]*w[None, :])
    assert abs(value.imag) <= 1e-8*max(1., abs(value.real))
    return float(value.real)


def kernel_integral(m, tau, a, alpha, nodes=256):
    v, weight = np.polynomial.legendre.leggauss(nodes)
    v = alpha*(v+1)/2; weight = alpha*weight/2
    t = np.arange(len(m))+tau
    field = (np.exp(2j*np.pi*v[:, None]*t[None, :])
             *np.cosh(v[:, None]*a[None, :]))@m
    return float(2/alpha**2*np.sum(weight*(alpha-v)*abs(field)**2))


def block_moment(length, mark, depth, alpha):
    h = np.arange(-length+1, length)
    values = (np.sinc(alpha*h)**2
              +np.real(np.sinc(alpha*(h+1j*depth/np.pi))**2))
    return float(mark**2/2*np.dot(length-abs(h), values))


def constants(alpha, cap):
    lip = math.cosh(alpha*cap)**2+alpha*cap*math.sinh(2*alpha*cap)
    decay = max(math.exp(2*alpha*cap),
                4*math.cosh(alpha*cap)**2/(math.pi**2*alpha**2))
    return lip, decay


def error_bound(p, j, alpha, cap):
    if not 1 <= j <= p:
        raise ValueError('1 <= number of blocks <= cells')
    lip, decay = constants(alpha, cap)
    own = 4*lip/alpha**2*j*(.5+math.log(p/j))
    b = j-1
    cross = 0. if b == 0 else 8*decay*b*(2+math.log(2*p/b))
    return own+cross


def variation(m, tau, a):
    return float(np.count_nonzero(np.diff(m))
                 +np.sum(abs(np.diff(a)))+2*np.pi*np.sum(abs(np.diff(tau))))


def coarsen(m, tau, a, eps):
    """Greedy consecutive blocks; every cut charges >eps variation."""
    if not 0 < eps < 1:
        raise ValueError('eps must lie in (0,1)')
    tau0, a0 = np.empty_like(tau), np.empty_like(a)
    starts = [0]; used = 0.
    for p in range(1, len(m)):
        step = (float(m[p] != m[p-1])+abs(a[p]-a[p-1])
                +2*np.pi*abs(tau[p]-tau[p-1]))
        if used+step > eps:
            starts.append(p); used = 0.
        else:
            used += step
    ends = starts[1:]+[len(m)]
    for lo, hi in zip(starts, ends):
        assert np.all(m[lo:hi] == m[lo])
        tau0[lo:hi] = tau[lo]; a0[lo:hi] = a[lo]
        assert np.max(abs(a[lo:hi]-a[lo])+2*np.pi*abs(tau[lo:hi]-tau[lo])) <= eps+1e-12
    assert len(starts)-1 <= variation(m, tau, a)/eps+1e-10
    return tau0, a0, len(starts)


def hs_difference(m, tau, a, tau0, a0, alpha, nodes=256):
    v, wt = np.polynomial.legendre.leggauss(nodes)
    v = alpha*(v+1)/2; wt = alpha*wt/2
    base = np.arange(len(m))
    k1 = (np.exp(2j*np.pi*v[:, None]*(base+tau)[None, :])
          *np.cosh(v[:, None]*a[None, :]))@m
    k0 = (np.exp(2j*np.pi*v[:, None]*(base+tau0)[None, :])
          *np.cosh(v[:, None]*a0[None, :]))@m
    return float(2/alpha**2*np.dot(wt*(alpha-v), abs(k1-k0)**2))


def exact_counts():
    partitions = 0; lag_checks = 0
    for p in range(2, 10):
        for mask in range(1 << (p-1)):
            cuts = [int(bool(mask & (1 << r))) for r in range(p-1)]
            labels = np.r_[0, np.cumsum(cuts)]
            b = sum(cuts)
            total = Fraction(0)
            for n in range(1, p):
                count = int(np.count_nonzero(labels[n:] != labels[:-n]))
                assert count <= min(p-n, b*n)
                total += Fraction(count, n*n); lag_checks += 1
            if b:
                assert float(total) <= b*(2+math.log(2*p/b))
            else:
                assert total == 0
            partitions += 1
    assert Fraction(16,9)-Fraction(19,12) == Fraction(7,36)
    assert 1-Fraction(3,4)**2/3 == Fraction(13,16)
    return dict(partitions=partitions, exact_lag_count_checks=lag_checks,
                gap='7/36', conditional_slow_modulation_floor='13/16')


def regression(samples):
    rng = np.random.default_rng(2026090609)
    metrics = dict(max_kernel_integral_residual=0., max_mosaic_bound_ratio=0.,
                   max_self_block_ratio=0., max_cross_bound_ratio=0.,
                   max_perturbation_ratio=0., max_norm_transfer_residual=0.)
    for trial in range(samples):
        p = int(rng.integers(3, 49)); j = int(rng.integers(1, min(p, 9)+1))
        cuts = sorted(rng.choice(np.arange(1, p), size=j-1, replace=False).tolist())
        ends = [0]+cuts+[p]
        m = np.zeros(p, int); tau = np.zeros(p); a = np.zeros(p)
        alpha = float(rng.choice([.5, .625, .75, .9, 1.]))
        self_sum = 0.
        cap = 1.5
        lip, decay = constants(alpha, cap)
        for lo, hi in zip(ends, ends[1:]):
            mm = int(rng.integers(0,3)); tt = rng.uniform(.001, .999)
            aa = rng.uniform(.01, cap) if mm == 2 else 0.
            m[lo:hi] = mm; tau[lo:hi] = tt; a[lo:hi] = aa
            en = block_moment(hi-lo, mm, aa, alpha)
            sb = mm**2*lip/alpha**2*(.5+math.log(hi-lo))
            if sb:
                ratio = abs(en-mm**2*(hi-lo)/alpha)/sb
                assert ratio <= 1+1e-9
                metrics['max_self_block_ratio'] = max(metrics['max_self_block_ratio'], ratio)
            self_sum += en
        en = direct_moment(m, tau, a, alpha)
        quad = kernel_integral(m, tau, a, alpha)
        res = abs(en-quad)
        assert res <= 2e-8*max(1., abs(en))
        metrics['max_kernel_integral_residual'] = max(metrics['max_kernel_integral_residual'], res)
        if j > 1:
            cb = 8*decay*(j-1)*(2+math.log(2*p/(j-1)))
            cr = abs(en-self_sum)/cb
            assert cr <= 1+1e-9
            metrics['max_cross_bound_ratio'] = max(metrics['max_cross_bound_ratio'], cr)
        ratio = abs(en-float(np.dot(m,m))/alpha)/error_bound(p,j,alpha,cap)
        assert ratio <= 1+1e-9
        metrics['max_mosaic_bound_ratio'] = max(metrics['max_mosaic_bound_ratio'], ratio)
        tau1 = np.clip(tau+rng.uniform(-.025,.025,p), 0., .9999)
        a1 = np.where(m == 2, np.clip(a+rng.uniform(-.025,.025,p),0.,cap+.025),0.)
        e = float(np.sum(m*((a-a1)**2+4*np.pi**2*(tau-tau1)**2))/p)
        cap1 = max(float(a.max()),float(a1.max()))
        c = math.sqrt(2*alpha)*math.exp(alpha*(cap1+math.pi))
        err = hs_difference(m,tau,a,tau1,a1,alpha)
        if e:
            ratio = math.sqrt(max(0.,err)/p)/(c*math.sqrt(e))
            assert ratio <= 1+1e-8
            metrics['max_perturbation_ratio'] = max(metrics['max_perturbation_ratio'], ratio)
        en1=direct_moment(m,tau1,a1,alpha)
        transfer=abs(math.sqrt(max(0.,en))-math.sqrt(max(0.,en1)))-math.sqrt(max(0.,err))
        assert transfer <= 1e-7
        metrics['max_norm_transfer_residual'] = max(metrics['max_norm_transfer_residual'], transfer)
        coarsen(m,tau1,a1,.2)
    return dict(status='PASS',samples=samples,seed=2026090609,periods='3..48',metrics=metrics)


def families():
    rows=[]
    for k in [2,4,8,16,32,64,128]:
        p=6*k; m=np.r_[np.ones(4*k,int),np.zeros(k,int),np.full(k,2,int)]
        tau=.4*np.arange(p)/p
        a=np.zeros(p); a[5*k:]=math.log(2)+.2*np.sin(2*np.pi*np.arange(k)/k)
        vv=variation(m,tau,a); eps=min(.5,(vv/p)**(1/3))
        t0,a0,j=coarsen(m,tau,a,eps)
        E1=direct_moment(m,tau,a,1.)/p
        Es=direct_moment(m,tau,a,.75)/p
        rows.append(dict(cells=p,variation=vv,variation_density=vv/p,
                         long_defect_density=E1-4/3,short_moment=Es,
                         short_gap=Es-19/12,coarsening_epsilon=eps,blocks=j))
    assert rows[-1]['short_moment']>19/12
    assert abs(rows[-1]['short_moment']-16/9)<.03
    rng=np.random.default_rng(909)
    mosaics=[]
    for k in [1,2,4,8,16]:
        p=6*k*k; m=np.zeros(p,int); tau=np.zeros(p); a=np.zeros(p)
        for group in range(k):
            lo=6*k*group
            m[lo:lo+4*k]=1; m[lo+5*k:lo+6*k]=2
            for start,end in [(lo,lo+4*k),(lo+4*k,lo+5*k),(lo+5*k,lo+6*k)]:
                tau[start:end]=rng.uniform(0.,.99)
            a[lo+5*k:lo+6*k]=rng.uniform(.2,1.2)
        es=direct_moment(m,tau,a,.75)/p
        mosaics.append(dict(cells=p,blocks=3*k,interface_density=(3*k-1)/p,short_moment=es))
    motif=np.array([1,1,1,1,2,0]); p=120
    m=np.tile(motif,p//6); t=np.zeros(p); a=np.zeros(p)
    long=direct_moment(m,t,a,1.); short=direct_moment(m,t,a,.75)/p
    assert abs(long+p*2/3-2*p)<1e-10
    assert variation(m,t,a)/p>.45
    return dict(slow_modulation=rows,many_blocks=mosaics,
                rapid_interlacing=dict(cells=p,defect=long+p*2/3-2*p,
                    variation_density=variation(m,t,a)/p,short_moment=short,
                    scope='one-scale exact equality does not force low variation'))


def high_precision_guards():
    mp.mp.dps=60
    checks=[]
    for p in [100,10000,1000000,100000000]:
        alpha=mp.mpf(3)/4; aa=mp.log(p)
        pairnorm=mp.sqrt(2+2*(mp.sinh(alpha*aa)/(alpha*aa))**2)
        simplenorm=mp.sqrt(mp.mpf(p-2)/alpha)
        lower=max(mp.mpf(0),pairnorm-simplenorm)**2/p
        checks.append(dict(cells=p,depth=str(aa),short_energy_lower=str(lower)))
    assert mp.mpf(checks[-1]['short_energy_lower'])>10
    resid=mp.mpf(0)
    for ell in [1,2,5,9]:
        alpha=mp.mpf(3)/4; aa=mp.log(2)
        def sinc(z): return mp.sin(mp.pi*z)/(mp.pi*z) if z else mp.mpf(1)
        finite=2*mp.fsum((ell-abs(h))*(sinc(alpha*h)**2+
                    mp.re(sinc(alpha*(h+1j*aa/mp.pi))**2)) for h in range(-ell+1,ell))
        def integrand(v):
            dl=ell if not v else mp.sin(mp.pi*ell*v)/mp.sin(mp.pi*v)
            return 8/alpha**2*(alpha-v)*mp.cosh(aa*v)**2*dl**2
        grid=sorted(set([mp.mpf(0),alpha]+[mp.mpf(i)/ell for i in range(1,ell) if mp.mpf(i)/ell<alpha]))
        integ=mp.quad(integrand,grid)
        resid=max(resid,abs(finite-integ))
    assert resid<mp.mpf('1e-45')
    return dict(growing_depth_guard=checks,small_block_integral_residual=str(resid),
                scope='mpmath high precision is not interval certification')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples',type=int,default=120)
    parser.add_argument('--output',type=Path,default=Path('validation.json'))
    args=parser.parse_args()
    if not 1<=args.samples<=500:
        parser.error('samples must be 1..500')
    result=dict(backend=dict(python=platform.python_version(),numpy=np.__version__,mpmath=mp.__version__),
                exact=exact_counts(),regression=regression(args.samples),families=families(),
                guards=high_precision_guards(),boundary='Analytic proof candidates plus exact finite combinatorics and floating/high-precision checks. No independent verification, general-near-extremizer classification, zeta proportion, or RH claim.')
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
