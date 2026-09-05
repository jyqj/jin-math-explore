#!/usr/bin/env python3
"""Reproducible finite checks for the periodic-rigidity candidate.

Analytic scope and proofs are in README.md. Numerical checks, high precision,
and a finite grid are not a proof certificate or independent verification.
"""
from __future__ import annotations
import argparse
from fractions import Fraction as F
import itertools
import json
import math
from pathlib import Path
import platform
import numpy as np
import mpmath as mp


def coefficients(m: np.ndarray, tau: np.ndarray, depth: np.ndarray,
                 frequencies: np.ndarray) -> np.ndarray:
    q=len(m)
    return ((np.exp(2j*np.pi*np.outer(frequencies,np.arange(q)+tau))
             *np.cosh(np.outer(frequencies,depth)))@m)/q


def moment(m: np.ndarray, tau: np.ndarray, depth: np.ndarray, alpha: float) -> float:
    q=len(m)
    if not 0<alpha<=1 or abs(float(m.sum())-q)>1e-10:
        raise ValueError('Require 0<alpha<=1 and mean mass one')
    n=np.arange(1,math.ceil(alpha*q),dtype=float)
    b=coefficients(m,tau,depth,n/q)
    return float(1/alpha+2/alpha**2*np.sum((alpha-n/q)*abs(b)**2))


def constants(cap: float) -> tuple[float,float]:
    c=math.cosh(cap)
    lam=(8/3)*(2*c+1+math.sqrt(4*c*c-3))
    ka=2*(math.sinh(cap/2)/cap)**2 if cap else .5
    return 7+lam/2,ka



def fiber_matrix(m,tau,depth):
    q=len(m);u=(np.arange(q)-(q-1)/2)/q
    f=np.exp(2j*np.pi*np.outer(u,np.arange(q)+tau))/math.sqrt(q)
    g=f*np.cosh(np.outer(u,depth));h=-1j*f*np.sinh(np.outer(u,depth))
    return (g*m[None,:])@g.conj().T-(h*m[None,:])@h.conj().T


def lock(m: np.ndarray,tau: np.ndarray,depth: np.ndarray,cap: float) -> dict:
    q=len(m); s=float(np.count_nonzero(m==1)/q)
    if s==0: raise ValueError('An anchor requires a positive simple fraction')
    delta=s+moment(m,tau,depth,1)-2
    ca,ka=constants(cap)
    eta=ca*(np.pi**2*q*q+cap*cap/4)*max(0.,delta)/(s*q)
    best=None
    for p in np.flatnonzero(m==1):
        theta=float(tau[p]); labels=np.rint(np.arange(q)+tau-theta).astype(int)
        errors=np.arange(q)+tau-theta-labels
        ep=float(np.dot(m,errors**2)/q); ed=float(np.dot(m,depth**2)/q)
        cost=4*ep+ed/4
        if best is None or cost<best['cost']:
            rounded=np.zeros(q)
            np.add.at(rounded,labels%q,m)
            best=dict(cost=cost,ep=ep,ed=ed,theta=theta,rounded=rounded)
    best.update(delta=delta,eta=eta,ca=ca,ka=ka,
                r=math.sqrt(q)*(math.pi*math.sqrt(eta)+4*ka*eta))
    return best


def anchor_energy(m: np.ndarray,tau: np.ndarray,depth: np.ndarray) -> float:
    centers=np.arange(len(m))+tau
    simple=np.flatnonzero(m==1); other=np.flatnonzero(m==2)
    d=centers[simple,None]-centers[None,simple]
    ss=np.sinc(d)**2; np.fill_diagonal(ss,0.)
    d2=centers[simple,None]-centers[None,other]
    cross=2*np.sum(abs(np.sinc(d2+1j*depth[None,other]/(2*np.pi)))**2)
    return float(ss.sum()+cross)


def finite_members(m,tau,depth,reps):
    q=len(m);zs=[];ws=[]
    for rep in range(reps):
        for p in np.flatnonzero(m):
            center=rep*q+p+tau[p]
            if m[p]==2 and depth[p]>0:
                zs.extend([center+1j*depth[p]/(2*np.pi),center-1j*depth[p]/(2*np.pi)])
                ws.extend([1.,1.])
            else: zs.append(complex(center));ws.append(float(m[p]))
    return np.array(zs),np.array(ws)


def finite_energy(m,tau,depth,reps,alpha):
    z,w=finite_members(m,tau,depth,reps)
    kernel=np.sinc(alpha*(z[:,None]-z[None,:]))**2
    value=np.sum(w[:,None]*w[None,:]*kernel)
    assert abs(value.imag)<1e-8*max(1.,abs(value.real))
    return float(value.real)


def integral_energy(m,tau,depth,reps,alpha,nodes=256):
    # Integrate separately on +/- halves to avoid the corner in |t|.
    x,w=np.polynomial.legendre.leggauss(nodes)
    t=alpha*(x+1)/2
    q=len(m)
    b=coefficients(m,tau,depth,t)*q
    dm=np.exp(2j*np.pi*np.outer(q*t,np.arange(reps))).sum(axis=1)
    return float(np.dot(w,(alpha-t)*abs(b*dm)**2)/alpha)


def finite_error(q,alpha,cap,reps):
    c=math.cosh(alpha*cap);h=math.sinh(alpha*cap)
    hh=c*c+2*alpha*c*(2*np.pi*q*c+cap*h)
    ff=(2*math.ceil(alpha*q)+2)*hh/(alpha*alpha*q)
    return ff*(.25+.5*math.log(reps))/reps


def exact_checks():
    assert F(64,9)>7
    cos6=[F(1),F(1,2),F(-1,2),F(-1),F(-1,2),F(1,2)]
    rows=[]
    for gap in [1,2,3]:
        value=F(4,3)+F(32,9)*sum((F(3,4)-F(n,6))*(1-cos6[(gap*n)%6])/18
                                  for n in range(1,5))
        assert value-F(19,12)>=F(5,108)
        rows.append(dict(pair_vacancy_distance=gap,short_moment=str(value),
                         excess=str(value-F(19,12))))
    assert rows[0]['short_moment']=='398/243'
    weights=0
    for q in range(1,65):
        for aa in [F(1,2),F(3,4),F(1)]:
            total=sum(2*(aa-F(n,q))/(aa*aa) for n in range(1,q) if F(n,q)<aa)
            assert total<=q;weights+=1
    return dict(status='PASS',tangent_period_six=rows,
                exact_spectral_weight_checks=weights,
                bound_minus_budget=str(F(44,27)-F(19,12)),
                seven_energy_constant_certificate='(8/3)^2 > 7')


def regression(samples):
    rng=np.random.default_rng(2026090610)
    metrics=dict(min_delta=math.inf,max_lock_ratio=0.,max_anchor_ratio=0.,
                 max_coefficient_ratio=0.,max_short_transfer_ratio=0.,
                 max_integral_residual=0.,max_repetition_error_ratio=0.,
                 max_rounded_floor_residual=0.,max_fiber_moment_residual=0.)
    collisions=0;near=0
    for case in range(samples):
        q=int(rng.integers(3,19));k=int(rng.integers(0,(q-1)//2+1))
        m=np.ones(q); perm=rng.permutation(q)
        m[perm[:k]]=2;m[perm[k:2*k]]=0
        tau=rng.uniform(0,1,q);a=np.zeros(q);a[m==2]=rng.uniform(.01,2,np.count_nonzero(m==2))
        if case%3==0:
            tau=np.clip(.4+rng.normal(0,1e-4,q),0,1-1e-8);a*=1e-4;near+=1
        cap=float(a.max());s=float(np.count_nonzero(m==1)/q)
        r=lock(m,tau,a,cap);delta=r['delta']
        tol=3e-9*max(1.,abs(moment(m,tau,a,1)))
        assert delta>=-tol
        tq=fiber_matrix(m,tau,a)
        fiber_residual=abs(float(np.vdot(tq,tq).real/q)-moment(m,tau,a,1))
        assert fiber_residual<=tol
        metrics['max_fiber_moment_residual']=max(metrics['max_fiber_moment_residual'],fiber_residual)
        assert r['cost']<=r['eta']+tol
        tp=anchor_energy(m,tau,a)
        assert tp<=r['ca']*q*max(delta,0)+tol*q
        assert np.dot(r['rounded'],r['rounded'])+tol>=np.dot(m,m)
        collisions+=int(np.count_nonzero(r['rounded'])<np.count_nonzero(m))
        metrics['min_delta']=min(metrics['min_delta'],delta)
        if r['eta']>tol: metrics['max_lock_ratio']=max(metrics['max_lock_ratio'],r['cost']/r['eta'])
        if delta>tol: metrics['max_anchor_ratio']=max(metrics['max_anchor_ratio'],tp/(r['ca']*q*delta))
        for alpha in [.55,.75,1.]:
            ell=moment(m,tau,a,alpha)
            ell0=moment(r['rounded'],np.full(q,r['theta']),np.zeros(q),alpha)
            if alpha<1:
                floor=1/alpha+(2*alpha-1)/alpha**2*(1-s)
                assert ell0>=floor-tol
                metrics['max_rounded_floor_residual']=max(metrics['max_rounded_floor_residual'],max(0.,floor-ell0))
                assert math.sqrt(max(0.,(2*alpha-1)/alpha**2*(1-s)))<=math.sqrt(max(0.,ell-1/alpha))+r['r']+tol
            ns=np.arange(1,math.ceil(alpha*q));weights=2*(alpha-ns/q)/alpha**2
            db=coefficients(m,tau,a,ns/q)-coefficients(r['rounded'],np.full(q,r['theta']),np.zeros(q),ns/q)
            err=math.sqrt(float(np.sum(weights*abs(db)**2)))
            assert err<=r['r']+tol
            assert abs(math.sqrt(max(0.,ell-1/alpha))-math.sqrt(max(0.,ell0-1/alpha)))<=err+tol
            if r['r']>tol: metrics['max_short_transfer_ratio']=max(metrics['max_short_transfer_ratio'],err/r['r'])
            scalar=math.pi*math.sqrt(r['eta'])+4*r['ka']*r['eta']
            if len(db):
                assert abs(db).max()<=scalar+tol
                if scalar>tol: metrics['max_coefficient_ratio']=max(metrics['max_coefficient_ratio'],float(abs(db).max()/scalar))
        if case<12:
            alpha=.75;reps=3
            direct=finite_energy(m,tau,a,reps,alpha)
            integ=integral_energy(m,tau,a,reps,alpha)
            residual=abs(direct-integ)
            assert residual<=2e-8*max(1.,abs(direct))
            metrics['max_integral_residual']=max(metrics['max_integral_residual'],residual)
            error=abs(direct/(reps*q)-moment(m,tau,a,alpha))
            bound=finite_error(q,alpha,cap,reps)
            assert error<=bound+tol
            metrics['max_repetition_error_ratio']=max(metrics['max_repetition_error_ratio'],error/bound)
    # An explicit collision in the rounded period is kept by aggregation.
    m=np.array([2.,2.,1.,1.,0.,0.]);tau=np.array([.99,.01,0.,0.,0.,0.]);a=np.array([.3,.7,0.,0.,0.,0.])
    r=lock(m,tau,a,.7)
    assert max(r['rounded'])==4 and r['rounded'].sum()==6
    return dict(status='PASS',samples=samples,seed=2026090610,near_equality_cases=near,
                random_rounding_collision_cases=collisions,metrics=metrics,
                collision_guard=dict(original_marks=m.tolist(),rounded_marks=r['rounded'].tolist(),
                                      original_mass_square=float(m@m),rounded_mass_square=float(r['rounded']@r['rounded'])))


def grid_scan():
    feasible=[];count=0;minmargin=math.inf
    for vacancy in [1,2,3]:
        m=np.ones(6);m[0]=2;m[vacancy]=0
        anchor=int(np.flatnonzero(m==1)[0]);variables=[p for p in np.flatnonzero(m) if p!=anchor]
        for digits in itertools.product(range(3),repeat=4):
            tau=np.full(6,1/3);tau[variables]=np.array(digits)/3
            for value in [0.,math.log(2),1.,2.]:
                a=np.zeros(6);a[0]=value
                l1=moment(m,tau,a,1);l2=moment(m,tau,a,.75);count+=1
                minmargin=min(minmargin,abs(l2-19/12))
                if l2<19/12:
                    feasible.append(dict(delta=l1-4/3,short_moment=l2,vacancy=vacancy,
                                         phases=tau.tolist(),depth=value))
    assert count==972 and len(feasible)>0
    best=min(feasible,key=lambda r:r['delta'])
    assert best['delta']>1e-3
    return dict(status='PASS',points=count,short_budget_feasible=len(feasible),
                minimum_distance_to_short_cutoff=minmargin,smallest_delta_among_grid_feasible=best,
                scope='A specified finite floating-point grid only; no continuous optimization certificate.')


def high_precision():
    mp.mp.dps=70;aa=mp.log(2);cc=mp.cosh(aa)
    ca=7+mp.mpf(4)/3*(2*cc+1+mp.sqrt(4*cc*cc-3));ka=(cc-1)/aa**2
    gap=mp.sqrt(mp.mpf(8)/27)-mp.mpf(1)/2
    rows=[]
    for q in [6,12,24,48,96]:
        hh=ca*(mp.pi**2*q*q+aa**2/4)/(mp.mpf(2)/3*q)
        pp=mp.pi*mp.sqrt(q*hh);qq=4*ka*hh*mp.sqrt(q)
        value=(2*gap/(pp+mp.sqrt(pp*pp+4*qq*gap)))**2
        residual=abs(pp*mp.sqrt(value)+qq*value-gap)
        assert residual<mp.mpf('1e-65')
        rows.append(dict(period=q,threshold=str(value),Q_squared_threshold=str(q*q*value),residual=str(residual)))
    return dict(status='PASS',precision_digits=70,cap='log(2)',rows=rows,
                scope='High-precision evaluation of an analytically derived conservative threshold; not an interval certificate.')


def examples():
    m=np.array([1.,1.,1.,1.,2.,0.]);tau=np.zeros(6);a=np.zeros(6);a[4]=math.log(2)
    l1=moment(m,tau,a,1);l2=moment(m,tau,a,.75)
    rows=[]
    for reps in [1,2,4,8,16,32,64]:
        e1=finite_energy(m,tau,a,reps,1)/(6*reps)
        e2=finite_energy(m,tau,a,reps,.75)/(6*reps)
        assert abs(e2-l2)<=finite_error(6,.75,math.log(2),reps)+1e-9
        rows.append(dict(repetitions=reps,long_moment=e1,short_moment=e2,short_error=abs(e2-l2)))
    growth=[]
    for k in [1,2,4,8,16,32,64]:
        q=6*k;m=np.zeros(q);m[:4*k]=1;m[5*k:]=2;a=np.zeros(q);a[m==2]=math.log(2);tau=np.zeros(q)
        delta=moment(m,tau,a,1)-4/3
        growth.append(dict(period=q,delta=delta,Q_squared_delta=q*q*delta,short_moment=moment(m,tau,a,.75)))
    assert growth[-1]['delta']<growth[0]['delta'] and growth[-1]['short_moment']>19/12
    anchorless=[]
    for dep in [0.,.1,math.log(2)]:
        mm=np.array([2.,0.,2.,0.,2.,0.]);at=np.zeros(6);at[mm==2]=dep
        tq=fiber_matrix(mm,np.zeros(6),at)
        defect=float(np.vdot(tq,tq).real/6)-2
        assert defect>=-1e-10 and (dep==0 or defect>0)
        anchorless.append(dict(depth=dep,delta=defect))
    return dict(anchorless_fiber_cases=anchorless,fixed_period=dict(period=6,depth='log(2)',limiting_long=l1,limiting_short=l2,prefixes=rows),
                growing_period_hole=growth,
                scope='The growing-period family is a scope guard; its short moment is not claimed to satisfy the target budget.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples',type=int,default=120)
    parser.add_argument('--output',type=Path,default=Path('validation.json'))
    args=parser.parse_args()
    if not 12<=args.samples<=1000: parser.error('samples must be in [12,1000]')
    result=dict(backend=dict(python=platform.python_version(),numpy=np.__version__,mpmath=mp.__version__),
                exact=exact_checks(),regression=regression(args.samples),grid=grid_scan(),
                thresholds=high_precision(),examples=examples(),
                boundary='Solver analytic candidates plus bounded rational and numerical self-checks. No independent verification, actual-zeta source transfer, period-independent theorem, optimized proportion or RH claim.')
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=='__main__': main()
