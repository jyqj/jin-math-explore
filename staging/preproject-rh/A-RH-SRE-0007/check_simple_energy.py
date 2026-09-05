#!/usr/bin/env python3
"""Reproduce bounded checks of the signed-to-simple energy candidates.

Analytic proofs are in README.md. Gauss-Legendre and binary64 checks are
not interval certificates or independent mathematical verification.
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


def herm(a: np.ndarray) -> np.ndarray:
    return (a + a.conj().T) / 2


def hs2(a: np.ndarray) -> float:
    return float(np.vdot(a, a).real)


def trace_norm(a: np.ndarray) -> float:
    return float(np.abs(np.linalg.eigvalsh(herm(a))).sum()) if a.size else 0.0


def basis(a: np.ndarray) -> np.ndarray:
    if not a.shape[1]:
        return np.zeros((a.shape[0], 0), dtype=complex)
    u, s, _ = np.linalg.svd(a, full_matrices=False)
    cutoff = max(a.shape) * np.finfo(float).eps * max(1.0, float(s[0])) * 32
    return u[:, s > cutoff]


def close_matching(x: np.ndarray, q: float = 0.5) -> tuple[list[int], list[tuple[int, int]]]:
    """Greedy maximal matching in the graph |x_i-x_j|<q."""
    order = list(np.argsort(x))
    kept: list[int] = []
    pairs: list[tuple[int, int]] = []
    j = 0
    while j < len(order):
        if j + 1 < len(order) and x[order[j + 1]] - x[order[j]] < q:
            pairs.append((int(order[j]), int(order[j + 1])))
            j += 2
        else:
            kept.append(int(order[j]))
            j += 1
    return kept, pairs


def local_matching(x: np.ndarray, width: float, h: float) -> tuple[int, float, float]:
    deleted = 0
    cost = 0.0
    phase_bound = 0.0
    if not len(x):
        return deleted, cost, phase_bound
    for cell in np.unique(np.floor(x / width).astype(int)):
        y = x[np.floor(x / width).astype(int) == cell]
        gram = np.sinc(y[:, None] - y[None, :])
        energy = hs2(gram - np.eye(len(y)))
        torus = (y[:, None] - y[None, :] + 0.5) % 1 - 0.5
        pivot = int(np.argmin((torus * torus).sum(axis=0)))
        err = torus[:, pivot]
        bound = math.pi**2 * width**2 * energy / (4 * len(y))
        assert float(np.dot(err, err)) <= bound + 2e-9
        keep = np.abs(err) <= h
        labels = np.rint(y[keep] - y[pivot]).astype(int)
        assert len(labels) == len(np.unique(labels)), "separation failed to prevent collisions"
        deleted += int((~keep).sum())
        cost += float(np.dot(err[keep], err[keep]))
        phase_bound += bound
    return deleted, cost, phase_bound


def signed_case(xs: np.ndarray, xr: np.ndarray, mr: np.ndarray,
                tp: np.ndarray, ap: np.ndarray, mpair: np.ndarray,
                nodes: np.ndarray, weights: np.ndarray) -> dict:
    dim = len(nodes)
    rootw = np.sqrt(weights)
    def vectors(t):
        return rootw[:, None] * np.exp(2j * np.pi * nodes[:, None] * np.asarray(t)[None, :])
    V = vectors(xs)
    real = vectors(xr)
    osc = vectors(tp)
    g = osc * np.cosh(nodes[:, None] * ap[None, :])
    h = -1j * osc * np.sinh(nodes[:, None] * ap[None, :])
    simple = V @ V.conj().T
    negative = (h * (2 * mpair)[None, :]) @ h.conj().T
    positive = (real * mr[None, :]) @ real.conj().T + (g * (2 * mpair)[None, :]) @ g.conj().T
    A = herm(simple + positive - negative)
    UB = basis(np.column_stack([real, g]))
    PU = UB @ UB.conj().T
    Ve = V - PU @ V
    EB = basis(Ve)
    PE = EB @ EB.conj().T
    PF = np.eye(dim) - PU - PE
    Q = 2 * PU + PE
    n, e, u = len(xs), EB.shape[1], UB.shape[1]
    mass_other = float(mr.sum() + 2 * mpair.sum())
    mass = n + mass_other
    defect = n + hs2(A) - 2 * mass
    scale = max(1.0, mass, hs2(A))
    tol = 2e-8 * scale
    assert defect >= -tol
    dsafe = max(0.0, defect)
    a = float(np.trace(PU @ simple).real)
    b = float(np.trace((np.eye(dim) - PU) @ negative).real)
    bf = float(np.trace(PF @ negative).real)
    slack_formula = hs2(A-Q) + 2 * (mass_other - 2*u) + 2*a + 2*b + 2*bf + n-e
    assert abs(defect-slack_formula) <= tol
    assert hs2(A-Q) + 2*a + 2*b + n-e <= defect+tol
    if e:
        L, s, RH = np.linalg.svd(EB.conj().T @ V, full_matrices=False)
        W = L @ RH
        Z = herm(W.conj().T @ (EB.conj().T @ (A-Q) @ EB) @ W)
        Pos = herm(V.conj().T @ PU @ V + W.conj().T @ (EB.conj().T @ negative @ EB) @ W)
        Ker = herm(np.eye(n) - W.conj().T @ W)
    else:
        Z = np.zeros((n,n), complex)
        Pos = herm(V.conj().T @ PU @ V)
        Ker = np.eye(n)
    F = herm(V.conj().T @ V)
    residual = np.linalg.norm(F-np.eye(n)-Z-Pos+Ker, 'fro')
    assert residual <= tol
    assert hs2(Z) <= defect+tol
    small_trace = float(np.trace(Pos+Ker).real)
    assert small_trace <= defect+tol
    assert trace_norm(F-np.eye(n)) <= math.sqrt(n*dsafe)+dsafe+tol
    # Check the independent exact integral formula, not only the sampled Gram.
    z = np.r_[xs.astype(complex), xr.astype(complex), tp+1j*ap/(2*np.pi), tp-1j*ap/(2*np.pi)]
    zm = np.r_[np.ones(n), mr, mpair, mpair]
    kernel_hs = np.sum((zm[:,None]*zm[None,:]) * np.sinc(z[:,None]-z[None,:])**2)
    assert abs(kernel_hs.imag) <= tol
    assert abs(hs2(A)-kernel_hs.real) <= tol
    true_F = np.sinc(xs[:,None]-xs[None,:])
    gram_residual = np.linalg.norm(F-true_F, 'fro')
    assert gram_residual <= tol
    kept, pairs = close_matching(xs)
    removed = 2 * len(pairs)
    witness = np.zeros((n,n))
    for i,j in pairs:
        witness[i,j]=witness[j,i]=1
    pairing = float(np.trace(witness @ (true_F-np.eye(n))))
    assert pairing >= (2/math.pi)*removed-1e-10
    assert pairing <= math.sqrt(removed*dsafe)+dsafe+tol
    assert removed <= 6*dsafe+tol
    tx = xs[kept]
    FR = np.sinc(tx[:,None]-tx[None,:])
    # Simple-anchor intrusion: this counts affected simple points, not pairs.
    cap = 8.0
    radius = 0.25
    intrusion_c = math.cos(math.pi*radius)**2 * 2*math.tanh(cap/2)/cap
    centers = np.r_[xr, tp[ap <= cap]]
    bad_anchor = np.any(np.abs(xs[:,None]-centers[None,:]) <= radius,axis=1) if len(centers) else np.zeros(n,dtype=bool)
    if np.any(bad_anchor):
        projections = np.real(np.diag(V.conj().T @ PU @ V))
        assert np.min(projections[bad_anchor]) >= intrusion_c-tol
    assert int(bad_anchor.sum()) <= dsafe/(2*intrusion_c)+tol
    raw = hs2(true_F-np.eye(n))
    energy = hs2(FR-np.eye(len(kept)))
    B = 14/3
    op = float(np.linalg.eigvalsh(FR)[-1]) if len(kept) else 0.0
    assert op <= B+tol
    energy_constant=(25+math.sqrt(141))/6
    assert energy <= energy_constant*dsafe+tol
    extra, cost, phase_bound = local_matching(tx, 3.0, 0.12)
    assert extra <= phase_bound/(0.12**2)+tol
    assert cost <= 7*math.pi**2*9*dsafe/4+tol
    assert removed+extra <= (6+7*math.pi**2*9/(4*0.12**2))*dsafe+tol
    return dict(defect=defect, mass=mass, raw_energy=raw, retained_energy=energy,
                removed=removed, retained=len(kept), local_extra=extra, intrusive_simple_anchors=int(bad_anchor.sum()),
                slack_identity_residual=abs(defect-slack_formula),
                gram_decomposition_residual=float(residual), gram_integral_residual=float(gram_residual),
                kernel_hs_residual=float(abs(hs2(A)-kernel_hs.real)),
                z_bound_ratio=hs2(Z)/dsafe if dsafe>1e-8 else 0.0,
                trace_bound_ratio=small_trace/dsafe if dsafe>1e-8 else 0.0,
                retained_energy_over_defect=energy/dsafe if dsafe>1e-8 else 0.0,
                removed_over_defect=removed/dsafe if dsafe>1e-8 else 0.0,
                retained_bessel_norm=op)


def exact_tests() -> dict:
    mp.mp.dps=70
    c=2/mp.pi
    deletion=((1+mp.sqrt(1+4*c))/(2*c))**2
    energy=(25+mp.sqrt(141))/6
    assert deletion<6 and energy<7
    # Exact scalar certificates for the conservative constants.
    # 6*c-1>13/5>sqrt(6), using c>3/5.
    assert Fraction(13,5)**2 > 6
    assert 141 < 17**2  # (25+sqrt(141))/6 < 7
    for k in range(2,101):
        r=k*k; n=4*r
        D=3*(k-1)+Fraction((k-1)**2,r)
        trace_hs=4*r+4*(k-1)+Fraction((k-1)**2,r)+(n-k+1)
        assert n+trace_hs-2*(n+2*r)==D
        assert Fraction(k*(k-1),1)>0
        # Cluster block: F-I = [(k-1)/k] J - [I-J/k] exactly.
        assert Fraction(k-1,k)-(1-Fraction(1,k)) == 0
        assert Fraction(k-1,k)+Fraction(1,k) == 1
        assert 2*(k-1)<=D
    k=10000; r=k*k
    D=3*(k-1)+Fraction((k-1)**2,r)
    a=mp.mpf('0.001')
    pair_defect=2*((mp.sinh(a)/a)**2-1)
    return dict(status='PASS', exact_clustered_cases=99,
                deletion_constant=str(deletion), retained_energy_constant=str(energy),
                clustered_example=dict(k=k, defect_over_mass=str(D/Fraction(6*r)),
                    raw_energy_over_mass=str(Fraction(k*(k-1),6*r)),
                    raw_energy_over_defect=str(Fraction(k*(k-1))/D)),
                shallow_pair=dict(a=str(a), defect=str(pair_defect),
                    defect_over_a_squared=str(pair_defect/a**2),
                    scope='one genuine off-real conjugate pair has D -> 0 as depth -> 0'))


def run(samples: int) -> dict:
    rng=np.random.default_rng(2026090507)
    nodes,weights=np.polynomial.legendre.leggauss(160)
    nodes=nodes/2; weights=weights/2
    cases=[]
    cases.append(signed_case(np.arange(8,dtype=float), np.array([9.,11.]),np.array([2.,2.]),
                            np.array([]),np.array([]),np.array([]),nodes,weights))
    cases.append(signed_case(np.array([]),np.array([]),np.array([]),
                            np.array([0.3]),np.array([1.0]),np.array([1.0]),nodes,weights))
    for j in range(samples):
        ns=int(rng.integers(1,15)); nr=int(rng.integers(0,4)); kp=int(rng.integers(0,5))
        total=ns+nr+kp
        slots=rng.choice(np.arange(-18,19),total,replace=False).astype(float)
        near=j%3==0
        slots += rng.uniform(-0.003 if near else -0.4,0.003 if near else 0.4,total)
        xs=slots[:ns]
        if j%7==0 and ns>=3:
            xs[:3]=rng.uniform(-0.02,0.02,3)+0.33
        xr=slots[ns:ns+nr]; tp=slots[ns+nr:]
        mr=np.full(nr,2.) if near else rng.integers(2,5,nr).astype(float)
        ap=rng.uniform(0.001,0.12,kp) if near else rng.uniform(0.1,8,kp)
        pm=np.ones(kp) if near else rng.integers(1,4,kp).astype(float)
        cases.append(signed_case(xs,xr,mr,tp,ap,pm,nodes,weights))
    keys=['slack_identity_residual','gram_decomposition_residual','gram_integral_residual',
          'kernel_hs_residual','z_bound_ratio','trace_bound_ratio','retained_energy_over_defect',
          'removed_over_defect','retained_bessel_norm']
    return dict(backend=dict(python=platform.python_version(),numpy=np.__version__,mpmath=mp.__version__),
        exact=exact_tests(), numerical=dict(status='PASS',samples=samples,seed=2026090507,
            quadrature_nodes=160,near_zero_equality_case=cases[0],
            max_metrics={k:max(t[k] for t in cases) for k in keys},
            near_saturation_cases=sum(0<=t['defect']/t['mass']<0.01 for t in cases),
            cases_with_nonempty_retained=sum(t['retained']>0 for t in cases)),
        boundary='Proof candidates plus exact scalar and floating-point finite tests. Quadrature is not interval-certified. No actual-zeta near-saturation assertion, full-multiset matching, Lean build or independent verification.')


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--samples',type=int,default=120)
    p.add_argument('--output',type=Path,default=Path('validation.json'))
    a=p.parse_args()
    if not 1<=a.samples<=10000: p.error('--samples must be between 1 and 10000')
    result=run(a.samples)
    text=json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n'
    a.output.write_text(text,encoding='utf-8')
    print(text,end='')

if __name__=='__main__': main()
