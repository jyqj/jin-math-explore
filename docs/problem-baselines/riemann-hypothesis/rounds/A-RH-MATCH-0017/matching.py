#!/usr/bin/env python3
"""Exact finite orbit matching; certificates prove only the stated surrogate optimum."""
from __future__ import annotations
import argparse
from dataclasses import dataclass
from fractions import Fraction as F
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def rational(x: Any) -> F:
    if isinstance(x, bool) or not isinstance(x, (int, str, F)):
        raise ValueError('Use integer or rational-string input, not floats.')
    return F(x)


@lru_cache(maxsize=4096)
def cosh_bounds(a: F) -> tuple[F, F]:
    """Rational Taylor enclosure, not a floating approximation."""
    if not 0 <= a <= 64:
        raise ValueError('This implementation accepts depths in [0,64].')
    total = term = F(1)
    for n in range(512):
        nxt = term*a*a/((2*n+1)*(2*n+2))
        ratio = a*a/((2*n+3)*(2*n+4))
        if ratio < 1:
            upper = total+nxt/(1-ratio)
            if upper-total <= F(1,10**18)*(1+total):
                return total, upper
        term = nxt
        total += term
    raise ArithmeticError('Taylor enclosure did not converge within its guard.')


def prepare(data: dict) -> dict:
    Q = data['Q']
    if type(Q) is not int or not 1 <= Q <= 128:
        raise ValueError('Implementation limit: 1<=Q<=128.')
    margin = rational(data.get('margin','1/16'))
    radius = rational(data.get('radius','1/4'))
    cap = rational(data.get('depth_cap','1'))
    weights = tuple(rational(w) for w in data.get('weights',['1','1','1']))
    if not 0 < margin <= F(1,2) or radius < 0 or not 0 <= cap <= 64:
        raise ValueError('Invalid margin, radius or depth cap.')
    if len(weights) != 3 or min(weights) < 0:
        raise ValueError('Three nonnegative objective weights are required.')
    if len(data['orbits']) > 256:
        raise ValueError('Implementation limit: at most 256 orbits.')
    orbits, loads = [], {}
    for item in data['orbits']:
        x, a, c = rational(item['x']), rational(item.get('a','0')), item['mass']
        if type(c) is not int or c < 1 or a < 0 or (a > 0 and c % 2):
            raise ValueError('A nonreal pair has even mass; masses are positive integers.')
        lo, hi = cosh_bounds(a)
        m, k = (1 if c == 1 else 2), math.floor(x)
        options = {}
        if a <= cap:
            for j in range(Q):
                y = min(max(x,F(j)+margin),F(j+1)-margin)
                if abs(x-y) <= radius:
                    options[j] = y
        orbits.append(dict(x=x,a=a,c=c,m=m,k=k,lo=lo,hi=hi,options=options))
        loads[k] = loads.get(k,F(0))+c*hi
    canonical = dict(Q=Q,margin=str(margin),radius=str(radius),depth_cap=str(cap),
                     weights=[str(w) for w in weights],
                     orbits=[dict(x=str(o['x']),a=str(o['a']),mass=o['c']) for o in orbits])
    digest = hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return dict(Q=Q,margin=margin,radius=radius,cap=cap,weights=weights,
                orbits=orbits,loads=loads,canonical=canonical,digest=digest)


def hall_deficiency(p: dict) -> dict:
    """Exact deficiency for whole-orbit injection, before retained-mass quotas."""
    Q, oo = p['Q'], p['orbits']
    empty = [i for i,o in enumerate(oo) if not o['options']]
    C, indices = {}, {}
    for u in range(Q):
        for v in range(u,Q):
            ids = [i for i,o in enumerate(oo) if o['options'] and
                   u <= min(o['options']) and max(o['options']) <= v]
            C[u,v], indices[u,v] = len(ids), ids
    dp, blocks = [0]*(Q+1), [[] for _ in range(Q+1)]
    for end in range(1,Q+1):
        dp[end], blocks[end] = dp[end-1], blocks[end-1][:]
        for u in range(end):
            gain = C[u,end-1]-(end-u)
            value = dp[u]+gain
            if value > dp[end]:
                dp[end], blocks[end] = value, blocks[u]+[[u,end-1]]
    witnesses = []
    for (u,v), ids in indices.items():
        excess = len(ids)-(v-u+1)
        if excess > 0:
            small = sorted(oo[i]['m']*oo[i]['lo'] for i in ids)[:excess]
            source_cells = len({oo[i]['k'] for i in ids})
            lower = sum(small,F(0))**2/(Q*source_cells)
            witnesses.append(dict(interval=[u,v],orbits=ids,excess=excess,
                                  Xi_lower=str(lower)))
    return dict(deficiency=len(empty)+dp[Q],empty_orbits=empty,
                maximizing_intervals=blocks[Q],witnesses=witnesses)


@dataclass
class Arc:
    u: int
    v: int
    capacity: int
    cost: F
    flow: int = 0
    pair: tuple[int,int] | None = None


def network(p: dict, r2: int) -> tuple[int,int,int,int,F,list[Arc]]:
    Q, oo = p['Q'], p['orbits']
    r1, n = Q-2*r2, len(oo)
    source, sink, V = 0, 3+n+Q, 4+n+Q
    lam, mu, nu = p['weights']
    baseline = mu*sum((v*v for v in p['loads'].values()),F(0))+nu*sum(o['m']==1 for o in oo)
    arcs = [Arc(0,1,r1,F(0)),Arc(0,2,r2,F(0))]
    for i,o in enumerate(oo):
        arcs.append(Arc(o['m'],3+i,1,F(0)))
        reward = mu*p['loads'][o['k']]*o['m']*o['hi']+nu*(o['m']==1)
        for j,y in o['options'].items():
            arcs.append(Arc(3+i,3+n+j,1,lam*o['m']*(o['x']-y)**2-reward,pair=(i,j)))
    arcs.extend(Arc(3+n+j,sink,1,F(0)) for j in range(Q))
    return source,sink,V,r1+r2,baseline,arcs


def residual(arcs: list[Arc]):
    for k,e in enumerate(arcs):
        if e.flow < e.capacity:
            yield e.u,e.v,e.capacity-e.flow,e.cost,k,1
        if e.flow:
            yield e.v,e.u,e.flow,-e.cost,k,-1


def shortest(V: int, arcs: list[Arc], source: int | None):
    dist = [F(0) if source is None else None for _ in range(V)]
    if source is not None:
        dist[source] = F(0)
    prev = [None]*V
    for step in range(V):
        changed = False
        for u,v,cap,cost,k,sgn in residual(arcs):
            if dist[u] is not None and (dist[v] is None or dist[u]+cost < dist[v]):
                dist[v],prev[v],changed = dist[u]+cost,(u,k,sgn),True
        if not changed:
            return dist,prev
    raise ArithmeticError('Negative residual cycle: solver invariant failed.')


def solve_quota(p: dict, r2: int) -> dict:
    source,sink,V,need,base,arcs = network(p,r2)
    value = 0
    while value < need:
        dist,prev = shortest(V,arcs,source)
        if dist[sink] is None:
            break
        v, path = sink, []
        while v != source:
            u,k,sgn = prev[v]
            path.append((k,sgn)); v = u
            if len(path) > V:
                raise ArithmeticError('Invalid predecessor path.')
        for k,sgn in path:
            arcs[k].flow += sgn
        value += 1
    result = dict(r2=r2,value=value,flows=[e.flow for e in arcs],
                  objective=str(base+sum((e.flow*e.cost for e in arcs),F(0))))
    if value == need:
        potentials,_ = shortest(V,arcs,None)
        result.update(status='optimal',potentials=[str(v) for v in potentials])
    else:
        reached = {source}
        while True:
            more = {v for u,v,*_ in residual(arcs) if u in reached}
            if more <= reached:
                break
            reached |= more
        result.update(status='infeasible',cut=sorted(reached))
    return result


def charge_ledger(p: dict, assignment: dict[int,int]) -> dict:
    Q, oo = p['Q'], p['orbits']
    if len(set(assignment.values())) != len(assignment):
        raise ValueError('Cell assignment is not injective.')
    if any(i not in range(len(oo)) or j not in oo[i]['options'] for i,j in assignment.items()):
        raise ValueError('Inadmissible orbit/cell edge.')
    if sum(oo[i]['m'] for i in assignment) != Q:
        raise ValueError('Retained mass differs from target cell count.')
    R = {}
    for i,o in enumerate(oo):
        removed = o['c']-(o['m'] if i in assignment else 0)
        R[o['k']] = R.get(o['k'],F(0))+removed*o['hi']
    Psum = sum((oo[i]['m']*(oo[i]['x']-oo[i]['options'][j])**2 for i,j in assignment.items()),F(0))
    Xi = sum((r*r for r in R.values()),F(0))/Q
    Xihat = sum((p['loads'][k]*r for k,r in R.items()),F(0))/Q
    n = sum(o['m']==1 for o in oo)
    ndel = sum(o['m']==1 and i not in assignment for i,o in enumerate(oo))
    N = sum(o['c'] for o in oo)
    lam,mu,nu = p['weights']
    return dict(assignment=[[i,j,str(oo[i]['options'][j])] for i,j in sorted(assignment.items())],
                source_mass=N,retained_mass=Q,removed_mass=N-Q,simple_deleted=ndel,
                s_model=str(F(n-ndel,Q)),source_mass_ratio=str(F(N,Q)),
                P=str(Psum/Q),Xi_enclosed=str(Xi),Xi_surrogate=str(Xihat),
                objective=str(lam*Psum+mu*Q*Xihat+nu*ndel))


def solve(data: dict) -> dict:
    p = prepare(data)
    quotas = [solve_quota(p,r2) for r2 in range(p['Q']//2+1)]
    feasible = [q for q in quotas if q['status']=='optimal']
    best = min(feasible,key=lambda q:(F(q['objective']),q['r2'])) if feasible else None
    result = dict(format='rh-matching-certificate/v1',input=p['canonical'],
                  input_sha256=p['digest'],quotas=quotas,best_r2=None if best is None else best['r2'])
    if best is not None:
        *_,arcs = network(p,best['r2'])
        assignment = {e.pair[0]:e.pair[1] for e,f in zip(arcs,best['flows']) if e.pair is not None and f}
        result['ledger'] = charge_ledger(p,assignment)
    return result


def verify(data: dict, certificate: dict) -> dict:
    """Check primal flows plus dual potentials/cuts; never calls the optimizer."""
    p = prepare(data)
    if certificate.get('format') != 'rh-matching-certificate/v1' or certificate.get('input_sha256') != p['digest']:
        raise ValueError('Input/format binding failed.')
    if certificate.get('input') != p['canonical']:
        raise ValueError('Canonical input differs.')
    qq = certificate['quotas']
    if len(qq) != p['Q']//2+1:
        raise ValueError('Incomplete quota enumeration.')
    feasible = []
    for r2,q in enumerate(qq):
        source,sink,V,need,base,arcs = network(p,r2)
        if q['r2'] != r2 or len(q['flows']) != len(arcs):
            raise ValueError('Quota or arc inventory mismatch.')
        balance = [0]*V
        for e,f in zip(arcs,q['flows']):
            if type(f) is not int or not 0 <= f <= e.capacity:
                raise ValueError('Invalid integral flow.')
            e.flow=f; balance[e.u]+=f; balance[e.v]-=f
        value = balance[source]
        if type(q['value']) is not int or value != q['value'] or balance[sink] != -value or any(balance[v] for v in range(V) if v not in (source,sink)):
            raise ValueError('Flow conservation/value failed.')
        obj = base+sum((e.flow*e.cost for e in arcs),F(0))
        if rational(q['objective']) != obj:
            raise ValueError('Objective mismatch.')
        if q['status']=='optimal':
            potentials = [rational(x) for x in q['potentials']]
            if value != need or len(potentials) != V:
                raise ValueError('Full-flow or potential size failed.')
            if any(cost+potentials[u]-potentials[v] < 0 for u,v,cap,cost,*_ in residual(arcs)):
                raise ValueError('Negative reduced residual cost.')
            feasible.append(q)
        elif q['status']=='infeasible':
            cut = set(q['cut'])
            if not all(type(v) is int and 0 <= v < V for v in cut) or source not in cut or sink in cut or value >= need:
                raise ValueError('Invalid infeasibility cut.')
            capacity = sum(e.capacity for e in arcs if e.u in cut and e.v not in cut)
            if capacity != value:
                raise ValueError('Cut does not certify the flow upper bound.')
        else:
            raise ValueError('Unknown quota status.')
    best = min(feasible,key=lambda q:(F(q['objective']),q['r2'])) if feasible else None
    if certificate.get('best_r2') != (None if best is None else best['r2']):
        raise ValueError('Global surrogate optimum selection failed.')
    if best is None:
        if 'ledger' in certificate:
            raise ValueError('Infeasible certificate has a ledger.')
    else:
        *_,arcs = network(p,best['r2'])
        assn = {e.pair[0]:e.pair[1] for e,f in zip(arcs,best['flows']) if e.pair is not None and f}
        if certificate.get('ledger') != charge_ledger(p,assn):
            raise ValueError('Charged matching ledger failed.')
    return dict(ok=True,feasible=best is not None,quotas=len(qq),
                scope='exact finite surrogate optimum/cut certificate; not a zeta theorem')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input',type=Path)
    ap.add_argument('--output',type=Path)
    ap.add_argument('--verify',type=Path)
    args = ap.parse_args()
    data = json.loads(args.input.read_text(encoding='utf-8'))
    if args.verify:
        print(json.dumps(verify(data,json.loads(args.verify.read_text(encoding='utf-8')))))
    else:
        if args.output is None:
            ap.error('--output is required for solving')
        cert = solve(data)
        verify(data,cert)
        args.output.write_text(json.dumps(cert,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        print(json.dumps(dict(ok=True,feasible=cert['best_r2'] is not None,output=str(args.output))))


if __name__ == '__main__':
    main()
