#!/usr/bin/env python3
"""Exact simplex moment forms for the endpoint-trace research archive."""
from __future__ import annotations
from fractions import Fraction as Q
from math import factorial as fac, comb
import hashlib
import json


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def basis(d: int) -> list[tuple[int, int, int, int]]:
    require(type(d) is int and d >= 0, 'nonnegative integer degree required')
    return [(a,b,c,d-a-b-c) for a in range(d+1)
            for b in range(d-a+1) for c in range(d-a-b+1)]


def entry(k: int, x: tuple, y: tuple) -> tuple[Q, Q, Q, Q, Q]:
    """Return k! times I,J_s,J_t,J_interior,K for two Bernstein monomials."""
    require(type(k) is int and k >= 4, 'k>=4 required')
    a,b,c,e = x
    A,B,C,E = y
    require(all(type(t) is int and t >= 0 for t in (*x,*y)), 'invalid exponents')
    require(sum(x) == sum(y), 'use one homogeneous degree')
    m, d = k-2, sum(x)
    den_i, den_j = fac(2*d+k), fac(2*d+k+1)
    scale = fac(k)
    I = Q(scale*fac(a+A)*fac(b+B)*fac(c+C+m-1)*fac(e+E), fac(m-1)*den_i)
    def endpoint(p,q,r,h,P,Q_,R,H):
        return (Q(fac(p)*fac(h),fac(p+h+1))*Q(fac(P)*fac(H),fac(P+H+1))
                *Q(scale*fac(q+Q_)*fac(r+R+m-1)*fac(p+h+P+H+2),fac(m-1)*den_j))
    Js = endpoint(a,b,c,e,A,B,C,E)
    Jt = endpoint(b,a,c,e,B,A,C,E)
    Ji = Q(0)
    for r in range(c+1):
        for R in range(C+1):
            Ji += (comb(c,r)*comb(C,R)*Q(fac(r)*fac(e),fac(r+e+1))
                   *Q(fac(R)*fac(E),fac(R+E+1))
                   *Q(scale*fac(a+A)*fac(b+B)*fac(c+C-r-R+m-2)*fac(r+e+R+E+2),
                      fac(m-2)*den_j))
    tx = Q(fac(a)*fac(b)*fac(e),fac(a+b+e+2))
    ty = Q(fac(A)*fac(B)*fac(E),fac(A+B+E+2))
    K = tx*ty*Q(scale*fac(c+C+m-1)*fac(a+b+e+A+B+E+3),fac(m-1)*den_j)
    return I, Js, Jt, Ji, K


def matrices(k: int, d: int) -> dict[str, list[list[Q]]]:
    bs = basis(d)
    names = ('I','Js','Jt','Ji','K')
    out = {name: [[Q(0) for _ in bs] for _ in bs] for name in names}
    for i,x in enumerate(bs):
        for j in range(i+1):
            for name,v in zip(names,entry(k,x,bs[j])):
                out[name][i][j] = out[name][j][i] = v
    out['J'] = [[out['Js'][i][j]+out['Jt'][i][j]+(k-2)*out['Ji'][i][j]
                 for j in range(len(bs))] for i in range(len(bs))]
    out['B'] = [[out['J'][i][j]-out['K'][i][j] for j in range(len(bs))] for i in range(len(bs))]
    return out


def digest(value: object) -> str:
    def plain(x):
        if isinstance(x,Q):
            return str(x)
        if isinstance(x,(tuple,list)):
            return [plain(t) for t in x]
        if isinstance(x,dict):
            return {k:plain(v) for k,v in x.items()}
        return x
    return hashlib.sha256(json.dumps(plain(value),sort_keys=True,separators=(',',':')).encode()).hexdigest()


def ldl_positive(A: list[list[Q]]) -> list[Q]:
    """Exact unpivoted Schur elimination; positive pivots prove positive definiteness."""
    n = len(A)
    require(all(len(row)==n for row in A), 'square matrix required')
    require(all(A[i][j]==A[j][i] for i in range(n) for j in range(i)), 'symmetric matrix required')
    S = [row[:] for row in A]
    pivots = []
    for j in range(n):
        p = S[j][j]
        require(p > 0, f'nonpositive pivot {j}')
        pivots.append(p)
        for i in range(j+1,n):
            q = S[i][j]/p
            for h in range(i,n):
                S[h][i] -= q*S[h][j]
                S[i][h] = S[h][i]
    return pivots


def quadratic(A: list[list[Q]], v: list[Q]) -> Q:
    require(len(v)==len(A), 'vector size')
    return sum((v[i]*v[j]*a for i,row in enumerate(A) for j,a in enumerate(row)),Q(0))


def trace_map(d: int) -> list[list[Q]]:
    bs = basis(d)
    return [[Q(fac(a)*fac(b)*fac(e),fac(a+b+e+2)) if c==r else Q(0)
             for a,b,c,e in bs] for r in range(d+1)]


def null_columns(d: int) -> list[dict[int,Q]]:
    """Sparse exact basis of the trace kernel; one pivot for each c block."""
    T = trace_map(d)
    columns = []
    for row in T:
        support = [i for i,q in enumerate(row) if q]
        p = support[0]
        for j in support[1:]:
            columns.append({j:Q(1),p:-row[j]/row[p]})
    return columns


def restrict(A: list[list[Q]], columns: list[dict[int,Q]]) -> list[list[Q]]:
    return [[sum((u*v*A[i][j] for i,u in x.items() for j,v in y.items()),Q(0))
             for y in columns] for x in columns]


def lift(v: list[Q], columns: list[dict[int,Q]], n: int) -> list[Q]:
    out = [Q(0)]*n
    require(len(v)==len(columns), 'kernel coordinate length')
    for q,col in zip(v,columns):
        for i,a in col.items():
            out[i] += q*a
    return out


def upper_matrix(I: list[list[Q]], B: list[list[Q]], u: Q) -> list[list[Q]]:
    return [[u*a-b for a,b in zip(ir,br)] for ir,br in zip(I,B)]


def propose(output: str) -> None:
    """Optional floating proposals; every accepted endpoint is rechecked exactly."""
    import numpy as np
    import scipy
    from scipy.linalg import eigh
    from pathlib import Path
    from math import ceil
    certs, summaries = [], []
    for d in range(7):
        M = matrices(40,d)
        cols = null_columns(d)
        record = {'degree':d,'dimension':len(M['I']),'trace_rank':d+1,'nullity':len(cols),
                  'matrix_sha256':digest(M),'bounds':{}}
        row = {'degree':d,'dimension':len(M['I']),'trace_rank':d+1,'nullity':len(cols)}
        for name in ('ordinary','penalized','trace_null'):
            if name=='trace_null' and not cols:
                continue
            I = restrict(M['I'],cols) if name=='trace_null' else M['I']
            B = restrict(M['J'],cols) if name=='trace_null' else M['J' if name=='ordinary' else 'B']
            vals, vectors = eigh(np.array(B,float),np.array(I,float))
            raw = vectors[:,-1]
            v = [int(round(float(x/max(abs(raw)))*10**12)) for x in raw]
            q = quadratic(B,v)/quadratic(I,v)
            lower = Q((q*10**6).__floor__(),10**6)
            upper = Q(ceil(float(vals[-1])*10**6),10**6)
            pivots = ldl_positive(upper_matrix(I,B,upper))
            require(lower <= q < upper and upper-lower <= Q(1,10**6), 'certificate width')
            record['bounds'][name] = {'lower':str(lower),'upper':str(upper),'vector':v,
                                     'pivot_sha256':digest(pivots),'positive_pivots':len(pivots)}
            row[name] = [str(lower),str(upper)]
        certs.append(record)
        summaries.append(row)
        print(json.dumps(row,sort_keys=True),flush=True)
    payload = {'schema':'twin-trace-certificates/v1','k':40,'max_degree':6,'cases':certs}
    results = {'schema':'twin-trace-results/v1','status':'solver_candidate','rows':summaries,
               'basis_family':'polynomials in two endpoints and the sum of38 interior coordinates; degree<=6',
               'classical_endpoint_rho':'1/4','penalized_score_upper':'3143127/4000000',
               'ordinary_score_upper':'3164151/4000000','trace_null_score_upper':'1543017/2000000',
               'finite_family_positive_detector':False,'actual_186_trial_evaluated':False,
               'new_prime_gap_bound':False,'independently_verified':False,
               'cannot_imply':['all40-variable functions fail','enlarged186-support failure',
                               'a new prime-gap bound','the twin-prime conjecture']}
    target=Path(output); target.mkdir(parents=True,exist_ok=True)
    for name,x in [('certificates.json',payload),('results.json',results)]:
        text=json.dumps(x,separators=(',',':')) if name=='certificates.json' else json.dumps(x,indent=2)
        (target/name).write_text(text+'\n',encoding='utf-8')
    print(json.dumps({'proposal_versions':{'numpy':np.__version__,'scipy':scipy.__version__},
                      'exact_acceptance':'Fraction LDL and rational quadratic witnesses','cases':7}))


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--propose',type=str,help='output directory; optional NumPy/SciPy needed only here')
    args=ap.parse_args()
    if args.propose is None:
        ap.error('use --propose DIR, or run check_trace.py for stdlib-only certificate verification')
    propose(args.propose)
