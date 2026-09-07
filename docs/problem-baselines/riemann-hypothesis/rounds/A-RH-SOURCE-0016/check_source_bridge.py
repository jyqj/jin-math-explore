#!/usr/bin/env python3
"""A-RH-SOURCE-0016: finite self-checks, not source asymptotics or verification."""
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
import sympy as sp

SEED = 2026090716

def smooth(t):
    return 1-10*t**3+15*t**4-6*t**5

def profile_nodes(p, e, order=64):
    z,w = np.polynomial.legendre.leggauss(order)
    points=[]; weights=[]; values=[]; derivatives=[]
    intervals=[(-p/2-e,-p/2),(p/2,p/2+e)]
    if p>0: intervals.append((-p/2,p/2))
    for lo,hi in intervals:
        x=(lo+hi)/2+(hi-lo)*z/2
        t=np.maximum((np.abs(x)-p/2)/e,0)
        inside=np.abs(x)<=p/2
        r=np.where(inside,1,smooth(t))
        dr=np.where(inside,0,-30*t*t*(1-t)**2*np.sign(x)/e)
        points.extend(x); weights.extend(w*(hi-lo)/2)
        values.extend(r); derivatives.extend(dr)
    return tuple(np.asarray(x) for x in (points,weights,values,derivatives))

def transform(z, nodes, derivative=False):
    x,w,r,dr=nodes
    z=np.asarray(z)
    return (np.exp(-2j*np.pi*z[...,None]*x)*(w*(dr if derivative else r))).sum(axis=-1)

def kernel(d,a,b,alpha):
    out=np.zeros(np.broadcast_shapes(np.shape(d),np.shape(a),np.shape(b)),complex)
    for e in (-1,1):
        for f in (-1,1):
            out+=np.sinc(alpha*(d-1j*(e*a+f*b)/(2*np.pi)))**2/4
    return out.real

def cross(m,t,a,n,u,b,alpha):
    if not len(m) or not len(n): return 0.0
    return float(m@kernel(t[:,None]-u[None,:],a[:,None],b[None,:],alpha)@n)

def energy(m,t,a,alpha):
    return cross(m,t,a,m,t,a,alpha)

def periodic(m,t,a,Q,alpha):
    v=np.arange(1,Q)/Q
    b=(np.exp(2j*np.pi*v[:,None]*t)*np.cosh(v[:,None]*a))@m/Q
    return float((sum(m)/Q)**2/alpha+2/alpha**2*np.dot(np.maximum(alpha-v,0),abs(b)**2))

def tail_charge(m,t,a,alpha,Q):
    load={}
    for c,x,d in zip(m,t,a):
        k=math.floor(x); load[k]=load.get(k,0)+abs(c)*math.cosh(alpha*d)
    return (3+1/(3*alpha**2))*sum(v*v for v in load.values())/Q

def move_bound(m,x,a,y,b,alpha,A,h,Q):
    P=float(np.dot(m,(x-y)**2)/Q); Z=float(np.dot(m,(a-b)**2)/Q)
    L=math.sqrt(2/alpha)*(math.exp(math.pi*alpha*(h+0.5))+math.exp(math.pi*alpha/2))
    return math.pi*alpha*L*math.cosh(alpha*A)*math.sqrt(P)+alpha*L*math.sinh(alpha*A)*math.sqrt(Z)/2

def boundary(alpha,A,Q):
    return math.cosh(alpha*A)**2/Q*(8+32*(2+math.log(Q))/(math.pi**2*alpha**2))

def parent_error(alpha,A,L,delta):
    B=16/3; C=7+B/4*(2*math.cosh(A)+1+math.sqrt(4*math.cosh(A)**2-3))
    U=math.sqrt(2*B/alpha)*math.cosh(alpha*A/2)
    V=math.sqrt(2*B/alpha)*math.sinh(alpha*A/2)
    c=(math.cosh(alpha*A/2)-1)/A if A else 0
    z=math.sinh(alpha*A/2)/A if A else alpha/2
    X=math.pi*alpha*(U+2/math.sqrt(alpha)); Y=(U+2/math.sqrt(alpha))*c+V*z
    R=math.hypot(X/2,2*Y); f=(2*alpha-1)/alpha**2; ca=(1-alpha)/alpha**2
    W=32*(3+math.log(L+2))/(math.pi**2*alpha**2*L)
    return (2*ca/(L+2)+W+2*R*math.sqrt(2*C*(math.pi**2*L*L+A*A/4)*delta/alpha)
        +2*math.sqrt(2*alpha-1)/alpha**2*math.sqrt(delta+2*boundary(1,A,L))+2*boundary(alpha,A,L))

def exact_checks():
    x=sp.symbols('x'); S=1-10*x**3+15*x**4-6*x**5
    assert sp.expand(S-(1-x)**3*(1+3*x+6*x*x))==0
    assert all(sp.diff(S,x,j).subs(x,k)==v for j,k,v in
               [(0,0,1),(0,1,0),(1,0,0),(1,1,0),(2,0,0),(2,1,0)])
    assert sp.integrate(S,(x,0,1))==sp.Rational(1,2)
    assert sp.integrate(S*S,(x,0,1))==sp.Rational(181,462)
    assert sp.integrate(sp.diff(S,x)**2,(x,0,1))==sp.Rational(10,7)
    p,e=sp.symbols('p e'); H=sp.integrate(S,(x,0,x))
    moment=sp.expand((p+e)**2*p/2-p**3/6+e*sp.integrate((p+e)**2-(p+2*e*H)**2,(x,0,1)))
    assert sp.expand(moment-(p**3/3+p*p*e+15*p*e*e/14+sp.Rational(3559,9009)*e**3))==0
    envelope=scale=endpoint=clip=0
    for p in (F(i,20) for i in range(1,19)):
        for e in (F(i,400) for i in range(1,20)):
            if p+2*e>=1: continue
            C=p+181*e/231+p**3/3+p*p*e+15*p*e*e/14+3559*e**3/9009
            assert p+p**3/3<=C<=p+2*e+(p+2*e)**3/3
            envelope+=1
    for theta in (F(i,17) for i in range(1,17)):
        for alpha in (F(i,13) for i in range(1,14)):
            k=lambda b:1/b+b/3
            assert k(theta)-F(4,3)==(1-theta)*(3-theta)/(3*theta)
            assert k(alpha*theta)-k(alpha)==(1-theta)*(1/(alpha*theta)-alpha/3)>0
            scale+=1
    for n in range(4,257):
        for b in (F(1,2),F(3,4),F(7,8)):
            H=lambda b:n*max(b-F(n-1,n),0)/(b*b)
            assert H(F(1))==1
            if b<=F(n-1,n): assert H(b)==0
            endpoint+=1
    for m in range(2,101):
        assert m-2>=0 and (m<=3*(m-2) if m>=3 else True)
        assert 2*m-2>=0 and 2*m<=2*(2*m-2)
        clip+=1
    return {'symbolic_profile_identities':11,'rational_envelopes':envelope,
            'rational_bandwidth_cases':scale,'rational_endpoint_cases':endpoint,
            'integer_multiplicity_cases':clip}

def run(samples):
    rng=np.random.default_rng(SEED); exact=exact_checks(); slacks={}; residuals={}; counts={}
    def bound(name,left,right):
        d=float(right-left); slacks[name]=min(slacks.get(name,math.inf),d)
        counts[name]=counts.get(name,0)+1
        if d < -5e-8*(1+abs(left)+abs(right)): raise AssertionError((name,left,right))
    def equal(name,left,right):
        err=float(np.max(np.abs(np.asarray(left)-np.asarray(right))))
        residuals[name]=max(residuals.get(name,0),err)
        counts[name]=counts.get(name,0)+1
        if err>5e-8*(1+float(np.max(np.abs(right)))): raise AssertionError((name,err))
    for i in range(samples):
        Q=int(rng.choice([4,6,8,12,18,24])); d=int(rng.integers(0,Q//2+1))
        full=np.array([2]*d+[0]*d+[1]*(Q-2*d)); rng.shuffle(full)
        k=np.flatnonzero(full); m=full[k].astype(float)
        y=k+rng.uniform(.05,.95,len(k)); A=[0.0,math.log(2),2.0][i%3]; h=.25
        b=np.where(m==2,rng.uniform(0,A,len(m)),0)
        a=np.where(m==2,np.clip(b+rng.normal(0,.1,len(m)),0,A),0)
        x=y+rng.uniform(-h,h,len(m)); excess=np.where(m==2,2*rng.integers(0,3,len(m)),0)
        # Whole extra orbits are deleted, while core simple marks remain simple.
        em=np.array([1.,2.]); et=np.array([-.8,Q+.4]); ea=np.array([0.,rng.uniform(0,4)])
        sm=np.r_[m+excess,em]; st=np.r_[x,et]; sa=np.r_[a,ea]
        dm=np.r_[excess,em]; dt=st; da=sa
        N=sum(sm); n=np.count_nonzero((sm==1)&(sa==0)); nd=1
        s=np.count_nonzero(m==1)/Q; ratio=N/Q
        equal('simple_count_ledger',s,ratio*(n/N)-nd/Q)
        Us={}
        for alpha in (.5,.75,1.):
            E=energy(sm,st,sa,alpha); Fm=energy(m,y,b,alpha)
            bound('source_energy_nonnegative',0,E)
            C=tail_charge(dm,dt,da,alpha,Q)
            bound('weighted_tail',energy(dm,dt,da,alpha)/Q,C)
            mb=move_bound(m,x,a,y,b,alpha,A,h,Q)
            actual=energy(np.r_[m,-m],np.r_[x,y],np.r_[a,b],alpha)/Q
            bound('transport',actual,mb*mb)
            eps=math.sqrt(C)+mb
            all_diff=energy(np.r_[sm,-m],np.r_[st,y],np.r_[sa,b],alpha)/Q
            bound('combined_residual',all_diff,eps*eps)
            per=periodic(m,y,b,Q,alpha)
            bound('periodization',abs(per-Fm/Q),boundary(alpha,A,Q))
            Us[alpha]=(math.sqrt(max(0,E/Q))+eps)**2+boundary(alpha,A,Q)
            bound('source_to_model_upper',per,Us[alpha])
            if i<12:
                z,w=np.polynomial.legendre.leggauss(96); v=np.r_[(z-1)*alpha/2,(z+1)*alpha/2]
                weights=np.r_[w,w]*alpha/2*(alpha-abs(v))/alpha**2
                Bv=(np.exp(2j*np.pi*v[:,None]*st)*np.cosh(v[:,None]*sa))@sm
                equal('integral_vs_kernel',float(np.dot(weights,abs(Bv)**2)),E)
        Delta=s+Us[1.]-2
        bound('defect_upper_nonnegative',0,Delta)
        for alpha in (.75,1.):
            f=(2*alpha-1)/alpha**2; c=(1-alpha)/alpha**2
            bound('parent_feasibility',f*(2-s)+c,Us[alpha]+parent_error(alpha,A,8,max(0,Delta)))
        # A different small synthetic multiset tests the positive envelope sandwich.
        nt=4; mm=np.array([1.,2.,2.,1.]); tt=rng.uniform(-3,3,nt)
        aa=np.array([0.,rng.uniform(0,2),rng.uniform(0,2),0.])
        zz=np.r_[tt+1j*aa/(2*np.pi),tt-1j*aa/(2*np.pi)]
        ww=np.r_[mm/2,mm/2]; dif=zz[:,None]-zz[None,:]
        band=float(rng.choice([.4,.6,.8])); e=.04
        energies=[]
        for p in (band-2*e,band):
            nodes=profile_nodes(p,e)
            K=transform(dif,nodes); val=complex(ww@(K*K)@ww)
            equal('profile_imaginary',val.imag,0.)
            energies.append(val.real)
            zc=rng.uniform(-2,2,5)+1j*rng.uniform(-.5,.5,5)
            Kr=transform(zc,nodes); Dr=transform(zc,nodes,True)
            ell=7.
            equal('fixed_test_deweight',(Kr*Kr-Dr*Dr/(4*ell*ell))/(1+np.pi**2*zc*zc/(ell*ell)),Kr*Kr)
        Eb=energy(mm,tt,aa,band)
        bound('inner_profile',energies[0],band*band*Eb)
        bound('outer_profile',band*band*Eb,energies[1])
    clusters=[]
    for k in (2,4,8,16,32,64,128):
        E=energy(np.ones(k),np.arange(k)/(4*k),np.zeros(k),1)/(k*k)
        bound('cluster_obstruction',4/math.pi**2,E)
        clusters.append({'k':k,'deleted_fraction':1/k,'normalized_residual_energy':E})
    mp.mp.dps=70; pairs=[]
    for N in (16,256,4096,65536,1048576):
        a=mp.log(N); val=(2+2*(mp.sinh(a)/a)**2)/N
        direct=energy(np.array([2.]),np.array([0.]),np.array([float(a)]),1)/N
        equal('deep_pair_formula',direct,float(val))
        pairs.append({'N':N,'deleted_fraction':2/N,'normalized_residual_energy':mp.nstr(val,32)})
    return {'ok':True,'attempt':'A-RH-SOURCE-0016','seed':SEED,'samples':samples,
        'exact_checks':exact,'counts':counts,'maximum_residuals':residuals,'minimum_slacks':slacks,
        'clusters':clusters,'deep_pairs':pairs,
        'backend':{'python':platform.python_version(),'numpy':np.__version__,'mpmath':mp.__version__,'sympy':sp.__version__},
        'scope':'Finite synthetic lists, exact polynomial/rational checks and floating regressions; no actual zeta zeros or PC asymptotic evaluated.',
        'parent_feasibility_boundary':'Small random feasibility inequalities are conservative and vacuous; no actual source assignment is certified.',
        'independent_verification':False,'mathematical_truth_verified':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--samples',type=int,default=120); p.add_argument('--output',type=Path,default=Path('validation.json'))
    p.add_argument('--check-package',action='store_true'); args=p.parse_args()
    if not 1<=args.samples<=10000: p.error('--samples must be in 1..10000')
    if args.check_package:
        root=Path(__file__).resolve().parent; data=json.loads((root/'checkpoint.json').read_text())
        for name,digest in data['sha256'].items():
            if Path(name).name!=name or hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:
                raise ValueError('hash mismatch: '+name)
        claims=json.loads((root/'claims.json').read_text())['claims']
        assert len({c['id'] for c in claims})==len(claims)
        assert all(c['evidence_grade']=='proof_candidate' and c['cannot_imply'] for c in claims)
        print(json.dumps({'ok':True,'hashes':len(data['sha256']),'claims':len(claims),'scope':'integrity only'})); return
    result=run(args.samples)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'ok':result['ok'],'samples':args.samples,'exact_checks':result['exact_checks'],'counts':result['counts']},sort_keys=True))

if __name__=='__main__':
    main()
