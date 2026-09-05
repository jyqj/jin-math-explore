#!/usr/bin/env python3
"""Bounded self-checks for anchor observability and hole-phase obstruction.

Proof arguments and scope are in README.md. Binary64 quadrature is not
interval-certified; high precision is not a proof or independent review.
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


def hs2(x: np.ndarray) -> float:
    return float(np.vdot(x, x).real)


def basis(x: np.ndarray) -> np.ndarray:
    if x.shape[1] == 0:
        return np.zeros((x.shape[0], 0), dtype=complex)
    u, s, _ = np.linalg.svd(x, full_matrices=False)
    tol = 64 * max(x.shape) * np.finfo(float).eps * max(1.0, float(s[0]))
    return u[:, s > tol]


def op2(x: np.ndarray) -> float:
    return float(np.linalg.norm(x, 2)**2) if x.size else 0.0


def bound_constants(q: float, cap: float, mult: int,
                    simple_bessel: float = 14/3) -> tuple[float, float, float]:
    if q <= 0 or cap < 0 or mult < 1:
        raise ValueError('q>0, cap>=0 and integer multiplicity>=1 required')
    bq = 2 + 2/(3*q*q)
    cg = 2*mult*bq*math.cosh(cap/2)**2
    ch = 2*mult*bq*math.sinh(cap/2)**2
    lam = (cg+ch+simple_bessel + math.sqrt((cg+ch-simple_bessel)**2
                                             + 4*ch*simple_bessel))/2
    return cg, ch, lam


def separated(rng: np.random.Generator, n: int, q: float, start: float) -> np.ndarray:
    return start + np.r_[0.0, np.cumsum(q+rng.uniform(.02, .8, max(0,n-1)))] if n else np.array([])


def finite_case(rng: np.random.Generator, nodes: np.ndarray,
                weights: np.ndarray, serial: int) -> dict:
    ns = int(rng.integers(1, 9)); npair = int(rng.integers(1, 6))
    nr = int(rng.integers(0, 3)); q = .5
    xs = separated(rng, ns, .5, rng.uniform(-3, 0))
    tp = separated(rng, npair, q, rng.uniform(-1, 2))
    ap = rng.uniform(.04, 2.0, npair)
    bp = rng.integers(1, 4, npair).astype(float)
    xr = np.arange(nr)*1.1-5.13
    mr = rng.integers(2, 6, nr).astype(float)
    # An extra, unselected pair need not satisfy the selected depth/separation cap.
    extra_t = np.array([tp[-1]+.23]) if serial % 3 == 0 else np.array([])
    extra_a = np.array([4.0]) if len(extra_t) else np.array([])
    extra_b = np.array([2.0]) if len(extra_t) else np.array([])
    all_t = np.r_[tp, extra_t]; all_a = np.r_[ap, extra_a]; all_b = np.r_[bp, extra_b]
    rootw = np.sqrt(weights)
    def f(t):
        return rootw[:,None] * np.exp(2j*np.pi*nodes[:,None]*t[None,:])
    V, real, osc = f(xs), f(xr), f(all_t)
    g = osc*np.cosh(nodes[:,None]*all_a[None,:])
    h = -1j*osc*np.sinh(nodes[:,None]*all_a[None,:])
    G = g*np.sqrt(2*all_b)[None,:]
    H = h*np.sqrt(2*all_b)[None,:]
    P = (real*mr[None,:])@real.conj().T+G@G.conj().T
    Neg=H@H.conj().T; S=V@V.conj().T
    A=S+P-Neg
    mass=ns+float(mr.sum()+2*all_b.sum())
    D=ns+hs2(A)-2*mass
    tol=3e-9*max(1.0,hs2(A),mass)
    U=basis(np.column_stack([real,g])); PU=U@U.conj().T
    a=hs2(PU@V); b=hs2(H-PU@H)
    nu=float(mr.sum()+2*all_b.sum())
    assert D>=-tol and 2*(a+b)<=D+tol
    assert U.shape[1]==nr+len(all_t), 'sample is numerically rank deficient'
    excess=float((mr-2).sum()+2*(all_b-1).sum())
    assert 2*excess<=D+tol
    heavy=float(mr[mr>=3].sum()+2*all_b[all_b>=2].sum())
    assert heavy<=1.5*D+tol
    assert float(2*all_b[all_b>=2].sum())<=D+tol
    cap=float(ap.max()); mult=int(bp.max())
    cg,ch,lam=bound_constants(q,cap,mult)
    GJ,HJ=G[:,:npair],H[:,:npair]
    assert op2(V)<=14/3+tol
    assert op2(GJ)<=cg+tol and op2(HJ)<=ch+tol
    cross=hs2(V.conj().T@GJ)+hs2(V.conj().T@HJ)
    phase=xs[:,None]-tp[None,:]
    exact_kernel=np.abs(np.sinc(phase+1j*ap[None,:]/(2*np.pi)))**2
    exact_cross=float((exact_kernel*(2*bp)[None,:]).sum())
    residual=abs(cross-exact_cross)
    assert residual<=tol
    coupled=(cg+ch)*a+(14/3)*b+2*math.sqrt(max(0.0,ch*(14/3)*a*b))
    assert cross<=coupled+tol and coupled<=lam*D/2+tol
    radius=1.1
    covered=np.min(np.abs(phase),axis=0)<=radius
    depth_sum=float(np.sum(bp[covered]*ap[covered]**2))
    depth_bound=(4*np.pi**2*radius**2+cap**2)*lam*D/4
    assert depth_sum<=depth_bound+tol
    low=.3
    selected=(ap>=low)
    total_mass=float((2*bp[selected]).sum())
    holes=float((2*bp[selected & ~covered]).sum())
    assert total_mass<=holes+(4*np.pi**2*radius**2+cap**2)*lam*D/(2*low**2)+tol
    return dict(kernel_residual=residual, cross_over_bound=cross/(lam*D/2) if D>tol else 0.,
                g_bessel_ratio=op2(GJ)/cg, h_bessel_ratio=op2(HJ)/ch if ch else 0.,
                mass=mass, defect=D, heavy_mass=heavy,
                covered_pairs=int(covered.sum()), unselected_deep_pairs=len(extra_t))


def sinc_sq(z):
    return mp.mpf(1) if z==0 else (mp.sin(mp.pi*z)/(mp.pi*z))**2


def phase_formula(k: int, alpha):
    """O(k) exact finite sum formula evaluated with mpmath; no quadrature."""
    alpha=mp.mpf(alpha); a=mp.log(2); b=a/(2*mp.pi)
    simple=4*k+2*mp.fsum((4*k-h)*sinc_sq(alpha*h) for h in range(1,4*k))
    def pp(h):
        return 2*sinc_sq(alpha*h)+2*mp.re(sinc_sq(alpha*(h+2j*b)))
    pair=k*pp(0)+2*mp.fsum((k-h)*pp(h) for h in range(1,k))
    cross=mp.mpf(0)
    for h in range(k+1,6*k):
        count=max(0,min(6*k-1,h+4*k-1)-max(5*k,h)+1)
        cross+=4*count*mp.re(sinc_sq(alpha*(h+1j*b)))
    return simple+pair+cross, pair, cross


def phase_direct(k: int, alpha: float) -> float:
    a=math.log(2); b=a/(2*np.pi)
    simp=np.arange(4*k,dtype=float)
    cen=np.arange(5*k,6*k,dtype=float)
    z=np.r_[simp.astype(complex),cen+1j*b,cen-1j*b]
    return float(np.sum(np.sinc(alpha*(z[:,None]-z[None,:]))**2).real)


def scalar_and_phase() -> dict:
    mp.mp.dps=60
    # Exact finite integer checks of the high-multiplicity cost.
    for m in range(3,102):
        assert m<=3*(m-2)
    for b in range(2,101):
        assert 2*b<=4*(b-1)
    assert Fraction(16,9)-Fraction(19,12)==Fraction(7,36)
    a=mp.log(2)
    assert abs(mp.sinh(a)**2-mp.mpf(9)/16)<mp.mpf('1e-55')
    lam=mp.mpf(7)/6*(7+mp.sqrt(13))
    numeric_lam=bound_constants(.5,float(a),1)[2]
    assert abs(numeric_lam-float(lam))<1e-12
    # Coupled-observable modulus identity at removable/symmetric boundaries.
    max_modulus=mp.mpf(0)
    for aa in [mp.mpf(0),mp.mpf('.001'),a,mp.mpf(3)]:
        for t in [mp.mpf(0),mp.mpf('.5'),mp.mpf(1),mp.mpf('2.37')]:
            z=t+1j*aa/(2*mp.pi)
            lhs=abs(mp.sqrt(sinc_sq(z)))**2
            denom=mp.pi**2*t**2+aa**2/4
            rhs=(mp.sin(mp.pi*t)**2+mp.sinh(aa/2)**2)/denom if denom else 1
            max_modulus=max(max_modulus,abs(lhs-rhs))
    assert max_modulus<mp.mpf('1e-50')
    rows=[]; max_direct=0.0
    for k in [1,2,4,8,16,32,64,128,256]:
        total,pair,cross=phase_formula(k,1)
        defect=total-8*k; pair_defect=pair-4*k
        bound=mp.mpf(9)/8*(1+mp.log(k))
        assert 0<defect<=pair_defect<=bound and cross<0
        short,_,_=phase_formula(k,mp.mpf(3)/4)
        if k<=16:
            max_direct=max(max_direct,abs(float(total)-phase_direct(k,1.)),
                           abs(float(short)-phase_direct(k,.75)))
        rows.append(dict(k=k,defect=str(defect),defect_over_mass=str(defect/(6*k)),
                         defect_upper=str(bound),short_moment_over_mass=str(short/(6*k)),
                         nearest_simple_distance=k+1,nonreal_mass_fraction='1/3'))
    assert max_direct<1e-8
    assert float(rows[-1]['short_moment_over_mass'])>19/12
    assert abs(float(rows[-1]['short_moment_over_mass'])-16/9)<.005
    return dict(status='PASS',integer_multiplicity_cases=198,
                modulus_identity_max_residual=str(max_modulus),
                special_lambda=str(lam),phase_depth='log(2)',phase_rows=rows,
                phase_max_direct_residual=max_direct,short_limit='16/9',
                short_budget='19/12',short_limit_excess='7/36')


def phase_quadrature_check() -> dict:
    # Direct integral of the exact finite pair block defect, split at its zeros.
    mp.mp.dps=40; a=mp.log(2); residual=mp.mpf(0)
    for k in [1,2,4,8]:
        def fun(v):
            if abs(v)<mp.mpf('1e-38') or abs(v-1)<mp.mpf('1e-38'):
                return mp.mpf(0)
            dk=mp.sin(mp.pi*k*v)/mp.sin(mp.pi*v)
            return 8*(1-v)*mp.sinh(a*v)**2*dk**2
        val=mp.quad(fun,[mp.mpf(j)/k for j in range(k+1)])
        _,pair,_=phase_formula(k,1)
        residual=max(residual,abs(val-(pair-4*k)))
    assert residual<mp.mpf('1e-30')
    return dict(status='PASS',k_values=[1,2,4,8],max_residual=str(residual),
                scope='mpmath quadrature consistency, not interval certification')


def run(samples: int) -> dict:
    rng=np.random.default_rng(2026090508)
    nodes,weights=np.polynomial.legendre.leggauss(160)
    nodes/=2; weights/=2
    rows=[finite_case(rng,nodes,weights,j) for j in range(samples)]
    numerical=dict(status='PASS',samples=samples,seed=2026090508,quadrature_nodes=160,
                   max_kernel_residual=max(r['kernel_residual'] for r in rows),
                   max_cross_over_bound=max(r['cross_over_bound'] for r in rows),
                   max_g_bessel_ratio=max(r['g_bessel_ratio'] for r in rows),
                   max_h_bessel_ratio=max(r['h_bessel_ratio'] for r in rows),
                   total_covered_pairs=sum(r['covered_pairs'] for r in rows),
                   cases_with_unselected_deep_pair=sum(bool(r['unselected_deep_pairs']) for r in rows))
    return dict(backend=dict(python=platform.python_version(),numpy=np.__version__,mpmath=mp.__version__),
                scalar_and_phase=scalar_and_phase(),pair_block_integral=phase_quadrature_check(),
                numerical=numerical,boundary='Solver derivations plus exact integer checks, high-precision finite sums and seeded quadrature tests. No independent verification, actual-zeta coverage, arithmetic moment estimate or RH result.')


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--samples',type=int,default=120)
    p.add_argument('--output',type=Path,default=Path('validation.json'))
    args=p.parse_args()
    if not 1<=args.samples<=1000:
        p.error('samples must be between 1 and 1000')
    result=run(args.samples)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=='__main__':
    main()
