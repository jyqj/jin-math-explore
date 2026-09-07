#!/usr/bin/env python3
"""Reproduce RH round 17 exact matching tests and synthetic operator regressions."""
from __future__ import annotations
import argparse
import copy
from fractions import Fraction as F
import hashlib
import itertools
import json
import math
from pathlib import Path
import platform
import random
import mpmath as mp
import numpy as np
import matching as mt

SEED = 2026090717


def brute_matching(adj: list[list[int]]) -> int:
    def rec(i,used):
        if i == len(adj): return 0
        return max([rec(i+1,used)]+[1+rec(i+1,used|{j}) for j in adj[i] if j not in used])
    return rec(0,set())


def subset_deficiency(adj: list[list[int]]) -> int:
    ans = 0
    for mask in range(1<<len(adj)):
        ids = [i for i in range(len(adj)) if mask>>i&1]
        neighbors = set().union(*(set(adj[i]) for i in ids)) if ids else set()
        ans = max(ans,len(ids)-len(neighbors))
    return ans


def brute_objective(p: dict):
    oo,Q = p['orbits'],p['Q']; lam,mu,nu = p['weights']
    best = None; leaves = 0
    def rec(i,mass,used,assignment):
        nonlocal best,leaves
        if mass > Q: return
        if i == len(oo):
            if mass != Q: return
            leaves += 1
            R = {}
            move = F(0); removed_simple = 0
            for k,o in enumerate(oo):
                rem = o['c']-(o['m'] if k in assignment else 0)
                R[o['k']] = R.get(o['k'],F(0))+rem*o['hi']
                if k in assignment:
                    move += o['m']*(o['x']-o['options'][assignment[k]])**2
                elif o['m']==1:
                    removed_simple += 1
            value = lam*move+mu*sum((p['loads'][k]*v for k,v in R.items()),F(0))+nu*removed_simple
            if best is None or value < best: best=value
            return
        rec(i+1,mass,used,assignment)
        for j in oo[i]['options']:
            if j not in used:
                assignment[i]=j
                rec(i+1,mass+oo[i]['m'],used|{j},assignment)
                del assignment[i]
    rec(0,0,set(),{})
    return best,leaves


def energy(x,a,c,alpha):
    x,a,c = map(lambda z:np.asarray(z,dtype=float),(x,a,c))
    if not len(x): return 0.0
    d = x[:,None]-x[None,:]
    K = np.zeros_like(d,dtype=complex)
    for e in (-1,1):
        for f in (-1,1):
            K += np.sinc(alpha*(d-1j*(e*a[:,None]+f*a[None,:])/(2*np.pi)))**2/4
    return float(np.real(c@K@c))


def integral_energy(x,a,c,alpha):
    u,w = np.polynomial.legendre.leggauss(96)
    x,a,c=map(np.asarray,(x,a,c))
    total=0.0
    for sign in (-1,1):
        t=sign*alpha*(u+1)/2
        B=(np.exp(2j*np.pi*t[:,None]*x)*np.cosh(t[:,None]*a))@c
        total += float(np.dot(w,(alpha-np.abs(t))/alpha**2*np.abs(B)**2)*alpha/2)
    return total


def periodic_energy(Q,x,a,c,alpha):
    v=np.arange(1,Q)/Q
    b=(np.exp(2j*np.pi*v[:,None]*x)*np.cosh(v[:,None]*a))@c/Q
    rho=sum(c)/Q
    return float(rho*rho/alpha+2/alpha**2*np.dot(np.maximum(alpha-v,0),abs(b)**2))


def run(samples: int):
    rng=random.Random(SEED)
    counts=dict(interval_families=0,bruteforce_optimization_cases=0,bruteforce_feasible_assignments=0,
                certificate_quotas=0,tamper_rejections=0,operator_models=0,operator_scale_checks=0,
                integral_comparisons=0,cosh_enclosures=0,charged_Hall_witness_checks=0,exact_feasible_models=0,repeated_cluster_cases=0)
    maxima={}; minima={}
    def bound(name,left,right):
        slack=float(right-left); minima[name]=min(minima.get(name,math.inf),slack)
        if slack < -2e-9*(1+abs(left)+abs(right)):
            raise AssertionError((name,left,right))
    def equal(name,left,right):
        err=abs(float(left-right));maxima[name]=max(maxima.get(name,0),err)
        if err > 2e-9*(1+abs(left)+abs(right)):
            raise AssertionError((name,left,right))
    for Q in range(1,5):
        choices=[[]]+[list(range(u,v+1)) for u in range(Q) for v in range(u,Q)]
        for n in range(5 if Q<4 else 4):
            for adj in itertools.product(choices,repeat=n):
                p=dict(Q=Q,orbits=[dict(options={j:F(j) for j in row},m=1,lo=F(1),k=i)
                                   for i,row in enumerate(adj)])
                h=mt.hall_deficiency(p)['deficiency']
                assert h==subset_deficiency(adj)==n-brute_matching(adj)
                counts['interval_families']+=1
    for _ in range(samples):
        Q=rng.randint(1,5); n=rng.randint(1,7)
        oo=[]
        for i in range(n):
            a=F(rng.choice([0,0,1,2]),4)
            c=rng.choice([2,4]) if a else rng.choice([1,1,2,3])
            oo.append(dict(x=str(F(rng.randint(-3,8*Q+3),8)),a=str(a),mass=c))
        data=dict(Q=Q,margin=rng.choice(['1/16','1/4','1/2']),radius=rng.choice(['0','1/4','1','2']),
                  depth_cap=rng.choice(['0','1/4','1/2']),weights=[str(rng.randint(0,3)) for _ in range(3)],orbits=oo)
        p=mt.prepare(data); cert=mt.solve(data); verdict=mt.verify(data,cert)
        best,leaves=brute_objective(p)
        observed=None if cert['best_r2'] is None else F(cert['ledger']['objective'])
        assert best==observed
        counts['bruteforce_optimization_cases']+=1
        counts['bruteforce_feasible_assignments']+=leaves
        counts['certificate_quotas']+=verdict['quotas']
        if observed is not None:
            counts['exact_feasible_models']+=1
            ledger=cert['ledger']; assert F(ledger['Xi_enclosed'])<=F(ledger['Xi_surrogate'])
            for witness in mt.hall_deficiency(p)['witnesses']:
                assert F(witness['Xi_lower'])<=F(ledger['Xi_enclosed'])
                counts['charged_Hall_witness_checks']+=1
    fixture=dict(Q=6,margin='1/8',radius='1/4',depth_cap='1/2',weights=['1','1','1'],orbits=[
        dict(x='1/2',mass=1),dict(x='3/5',mass=1),dict(x='3/2',a='1/2',mass=2),
        dict(x='5/2',mass=3),dict(x='7/2',mass=1),dict(x='9/2',a='3/4',mass=2),dict(x='11/2',mass=1)])
    cert=mt.solve(fixture);mt.verify(fixture,cert)
    assert cert['best_r2'] is not None
    bad=[]
    c=copy.deepcopy(cert);c['input_sha256']='0'*64;bad.append(c)
    c=copy.deepcopy(cert);c['quotas'].pop();bad.append(c)
    c=copy.deepcopy(cert);c['ledger']['P']='99';bad.append(c)
    opt=cert['best_r2']
    c=copy.deepcopy(cert);c['quotas'][opt]['flows'][0]+=1;bad.append(c)
    c=copy.deepcopy(cert);c['quotas'][opt]['objective']='-1';bad.append(c)
    c=copy.deepcopy(cert)
    p=mt.prepare(fixture);*_,arcs=mt.network(p,opt)
    for e,f in zip(arcs,c['quotas'][opt]['flows']):e.flow=f
    u,v,*_=next(mt.residual(arcs))
    c['quotas'][opt]['potentials'][v]=str(10**100);bad.append(c)
    c=copy.deepcopy(cert)
    iq=next(q for q in c['quotas'] if q['status']=='infeasible')
    iq['cut']=[];bad.append(c)
    for c in bad:
        try:mt.verify(fixture,c)
        except (ValueError,KeyError,TypeError):counts['tamper_rejections']+=1
        else:raise AssertionError('Tampered certificate accepted')
    crossing=dict(Q=3,margin='1/2',radius='3/2',depth_cap='0',weights=['1','0','0'],
                  orbits=[dict(x='0',mass=1),dict(x='1/10',mass=2)])
    cross=mt.solve(crossing);mt.verify(crossing,cross)
    assert F(cross['ledger']['objective'])==F(257,100)
    assert cross['ledger']['assignment']==[[0,1,'3/2'],[1,0,'1/2']]
    separated=dict(Q=3,margin='1/16',radius='0',depth_cap='0',orbits=[
        dict(x='9/20',mass=1),dict(x='11/20',mass=1),dict(x='49/20',mass=1),dict(x='51/20',mass=1)])
    hs=mt.hall_deficiency(mt.prepare(separated)); no=mt.solve(separated);mt.verify(separated,no)
    assert hs['deficiency']==2 and no['best_r2'] is None
    parity=dict(Q=3,margin='1/16',radius='0',orbits=[dict(x='1/2',mass=2),dict(x='3/2',mass=2)])
    assert mt.hall_deficiency(mt.prepare(parity))['deficiency']==0
    assert mt.solve(parity)['best_r2'] is None
    repeated = []
    for k in range(1,9):
        source = []
        for block in range(k):
            source += [dict(x=str(F(6*block)+F(j,10)),mass=1) for j in (2,3,4,5)]
            source.append(dict(x=str(F(6*block)+F(3,2)),mass=2))
        cluster_data=dict(Q=6*k,margin='1/16',radius='1/8',depth_cap='0',orbits=source)
        ph=mt.prepare(cluster_data);hh=mt.hall_deficiency(ph)
        assert hh['deficiency']==3*k
        # Each repeated source cell loses at least three simple masses.
        assert F(9*k,6*k)==F(3,2)
        repeated.append(dict(Q=6*k,source_mass=6*k,simple_fraction='2/3',
                             minimum_unmatched_orbits=3*k,Xi_lower='3/2'))
        counts['repeated_cluster_cases']+=1
    mp.mp.dps=100
    for a in [F(j,8) for j in range(33)]+[F(8),F(16),F(32),F(64)]:
        lo,hi=mt.cosh_bounds(a);v=mp.cosh(mp.mpf(a.numerator)/a.denominator)
        ml=mp.mpf(lo.numerator)/lo.denominator;mh=mp.mpf(hi.numerator)/hi.denominator
        assert ml-abs(v)*mp.mpf('1e-95')<=v<=mh+abs(v)*mp.mpf('1e-95')
        counts['cosh_enclosures']+=1
    for case in range(samples):
        Q=rng.randint(3,8); marks=[1]*Q
        for _ in range(rng.randrange(Q//2+1)):
            ones=[j for j,m in enumerate(marks) if m==1]
            if len(ones)<2:break
            u,v=rng.sample(ones,2);marks[u]=2;marks[v]=0
        oo=[]
        for j,m in enumerate(marks):
            if not m:continue
            a=F(rng.randrange(5),8) if m==2 else F(0)
            c=m+(rng.choice([0,0,2]) if m==2 and a else rng.choice([0,0,1]) if m==2 else 0)
            oo.append(dict(x=str(F(j)+F(8+rng.randint(-2,2),16)),a=str(a),mass=c))
        for extra in range(rng.randrange(3)):
            oo.append(dict(x=str(F(rng.randrange(Q))+F(2*extra+1,32)),
                           a='3/4' if extra else '0',mass=2 if extra else 1))
        data=dict(Q=Q,margin='1/8',radius='1/4',depth_cap='1/2',weights=['1','1','1'],orbits=oo)
        p=mt.prepare(data);cc=mt.solve(data);vv=mt.verify(data,cc)
        if not vv['feasible']:raise AssertionError('Constructed input lost its known feasible core')
        lg=cc['ledger'];assignment={i:j for i,j,_ in lg['assignment']}
        sx=[float(o['x']) for o in p['orbits']];sa=[float(o['a']) for o in p['orbits']]
        sc=[o['c'] for o in p['orbits']]
        ids=list(assignment);cx=[sx[i] for i in ids];ca=[sa[i] for i in ids]
        cm=[p['orbits'][i]['m'] for i in ids]
        tx=[float(p['orbits'][i]['options'][assignment[i]]) for i in ids]
        removed=[o['c']-(o['m'] if i in assignment else 0) for i,o in enumerate(p['orbits'])]
        for alpha in (0.5,0.75,1.0):
            D=energy(sx,sa,removed,alpha)/Q
            Kdel=3+1/(3*alpha*alpha)
            bound('deletion_enclosure',D,Kdel*float(F(lg['Xi_enclosed'])))
            bound('linear_surrogate',float(F(lg['Xi_enclosed'])),float(F(lg['Xi_surrogate'])))
            H=math.sqrt(2/alpha)*(math.exp(math.pi*alpha*(0.25+0.5))+math.exp(math.pi*alpha/2))
            trans=math.pi*alpha*H*math.cosh(alpha/2)*math.sqrt(float(F(lg['P'])))
            Etrans=energy(cx+tx,ca+ca,cm+[-m for m in cm],alpha)/Q
            bound('transport',Etrans,trans*trans)
            eps=math.sqrt(Kdel*float(F(lg['Xi_enclosed'])))+trans
            residual=energy(sx+tx,sa+ca,sc+[-m for m in cm],alpha)/Q
            bound('joint_residual',residual,eps*eps)
            Es=energy(sx,sa,sc,alpha)/Q
            b=math.cosh(alpha/2)**2/Q*(8+32*(2+math.log(Q))/(math.pi**2*alpha**2))
            Et=periodic_energy(Q,np.array(tx),np.array(ca),np.array(cm),alpha)
            bound('source_to_periodic_upper',Et,(math.sqrt(max(Es,0))+eps)**2+b)
            if case<8:
                alt=integral_energy(sx+tx,sa+ca,sc+[-m for m in cm],alpha)
                equal('integral_kernel',alt,residual*Q)
                counts['integral_comparisons']+=1
            counts['operator_scale_checks']+=1
        counts['operator_models']+=1
        counts['certificate_quotas']+=vv['quotas']
    return dict(ok=True,attempt='A-RH-MATCH-0017',seed=SEED,samples=samples,counts=counts,
                maximum_residuals=maxima,minimum_slacks=minima,
                fixture_certificate=cert,crossing_example=cross,
                disjoint_Hall_example=dict(data=separated,hall=hs,certificate=no),
                exact_mass_parity_obstruction=parity,repeated_cluster_obstruction=repeated,
                backend=dict(python=platform.python_version(),numpy=np.__version__,mpmath=mp.__version__),
                evidence_boundary='Finite exact certificates and synthetic numerical tests; no actual zeta assignment, asymptotic theorem or independent verification.',
                independent_verification=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--samples',type=int,default=120)
    ap.add_argument('--output',type=Path,default=Path('validation.json'))
    ap.add_argument('--check-package',action='store_true')
    args=ap.parse_args()
    if not 1<=args.samples<=1000:ap.error('samples must be in 1..1000')
    if args.check_package:
        root=Path(__file__).resolve().parent
        checkpoint=json.loads((root/'checkpoint.json').read_text())
        for name,digest in checkpoint['sha256'].items():
            if Path(name).name!=name or hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:
                raise ValueError('Artifact hash mismatch: '+name)
        claims=json.loads((root/'claims.json').read_text())['claims']
        assert len({c['id'] for c in claims})==len(claims)
        assert all(c['evidence_grade']=='proof_candidate' and c['cannot_imply'] for c in claims)
        result=json.loads((root/'validation.json').read_text())
        for name in ('fixture_certificate','crossing_example'):
            c=result[name];mt.verify(c['input'],c)
        c=result['disjoint_Hall_example']['certificate'];mt.verify(c['input'],c)
        print(json.dumps(dict(ok=True,hashes=len(checkpoint['sha256']),claims=len(claims),certificates=3)))
        return
    result=run(args.samples)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(dict(ok=True,counts=result['counts'],output=str(args.output)),sort_keys=True))


if __name__=='__main__':main()
