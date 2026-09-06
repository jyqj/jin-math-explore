#!/usr/bin/env python3
"""A-RH-LOC-0012: reproducible finite checks, not independent proof verification."""
from __future__ import annotations
import argparse, hashlib, itertools, json, math, platform
from fractions import Fraction as F
from pathlib import Path
import numpy as np
import mpmath as mp

SEED = 2026090612

def kernel(d, a, b, alpha):
    out = np.zeros(np.broadcast_shapes(np.shape(d), np.shape(a), np.shape(b)), complex)
    for sign in (-1, 1):
        for other in (-1, 1):
            out += np.sinc(alpha*(d-1j*(sign*a+other*b)/(2*np.pi)))**2/4
    return out.real

def finite_energy(m, t, a, alpha):
    k = kernel(t[:,None]-t[None,:], a[:,None], a[None,:], alpha)
    return float(m@k@m)

def moments(m, tau, a, alpha):
    Q = len(m); x = np.arange(Q)/Q
    b = (np.exp(2j*np.pi*x[:,None]*(np.arange(Q)+tau))*np.cosh(x[:,None]*a))@m/Q
    return float(1/alpha+2/alpha**2*np.dot(np.maximum(alpha-x[1:],0),abs(b[1:])**2))

def constants(alpha, A, L):
    B = 16/3
    C = 7+B/4*(2*math.cosh(A)+1+math.sqrt(4*math.cosh(A)**2-3))
    U = math.sqrt(2*B/alpha)*math.cosh(alpha*A/2)
    V = math.sqrt(2*B/alpha)*math.sinh(alpha*A/2)
    c = (math.cosh(alpha*A/2)-1)/A if A else 0
    z = math.sinh(alpha*A/2)/A if A else alpha/2
    X = math.pi*alpha*(U+2/math.sqrt(alpha))
    Y = (U+2/math.sqrt(alpha))*c+V*z
    R = math.hypot(X/2,2*Y)
    cross = math.cosh(alpha*A)**2/L*(8+32/(math.pi**2*alpha**2)*(2+math.log(L)))
    wrap = 32/(math.pi**2*alpha**2*L)*(3+math.log(L+2))
    return C,R,cross,wrap

def partition(m, tau, a, L, shift=0):
    Q = len(m); P = math.lcm(Q,L); p = np.arange(shift,shift+P)
    mm,tt,aa = m[p%Q],p+tau[p%Q],a[p%Q]
    blocks=[]; cost=0.; hmass=0; nbad=0; kmin=L
    for start in range(0,P,L):
        mb,tb,ab=mm[start:start+L],tt[start:start+L],aa[start:start+L]
        anchors=np.flatnonzero(mb==1)
        if not len(anchors):
            hmass+=int(mb.sum());nbad+=1
            blocks.append((mb,tb,ab,None,None));continue
        kmin=min(kmin,len(anchors))
        best=None
        for i in anchors:
            theta=tb[i]%1; kk=np.floor(tb-theta+.5).astype(int); e=tb-theta-kk
            value=float(np.dot(mb,4*e*e+ab*ab/4))
            if best is None or value<best[0]:best=value,theta,kk
        value,theta,kk=best;cost+=value
        # Always fit the rounded support in L+2 consecutive integer sites.
        lo=shift+start-1; M=np.zeros(L+2,int)
        np.add.at(M,kk-lo,mb)
        assert np.max(M)<=4 and M.sum()==mb.sum() and np.dot(M,M)>=np.dot(mb,mb)
        blocks.append((mb,tb,ab,theta+kk,M))
    return blocks,P,hmass/P,nbad/(P//L),cost/P,kmin

def run(samples):
    rng=np.random.default_rng(SEED);slacks={};residuals={}
    def le(name,left,right):
        d=float(right-left);slacks[name]=min(slacks.get(name,math.inf),d)
        if d < -5e-9*(1+abs(left)+abs(right)):raise AssertionError((name,left,right))
    def eq(name,left,right):
        d=float(np.max(np.abs(np.asarray(left)-right)));residuals[name]=max(residuals.get(name,0),d)
        if d>5e-9*(1+float(np.max(np.abs(right)))):raise AssertionError((name,d))
    exact_cross=exact_wrap=exact_rounding=0
    for L in range(2,33):
        for r in range(1,3*L+1):
            assert sum((p+r)//L!=p//L for p in range(L))==min(r,L)
            assert sum((p-r)//L!=p//L for p in range(L))==min(r,L)
            exact_cross+=2
    for K in range(2,21):
        for d in range(1,3*K+1):
            count=sum(1 for p in range(K) for q in range(K) if (d-p+q)%K==0 and (d-p+q)//K!=0)
            assert count==min(d,K);exact_wrap+=1
    for L in range(1,5):
        for tau in itertools.product((F(0),F(1,2),F(3,4)),repeat=L):
            for theta in (F(0),F(1,4),F(1,2),F(3,4)):
                occ=[0]*(L+2)
                for p in range(L):occ[math.floor(p+tau[p]-theta+F(1,2))+1]+=2
                assert max(occ)<=4 and sum(occ)==2*L;exact_rounding+=1
    h=F(1,10)
    lower=F(32,27)+F(2,9)*h+F(4,9)*(1-h)**2/(1-h/2)
    assert lower-F(19,12)==F(31,10260)
    assert F(3,16)/18==F(1,96)
    relaxed=F(16,27)+F(16,63)+F(2,3)
    assert relaxed==F(286,189) and F(19,12)-relaxed==F(53,756)
    configs=[]
    for j in range(samples):
        Q=int(rng.choice([6,12,18,24,36]));d=int(rng.integers(0,Q//2+1))
        m=np.array([2]*d+[0]*d+[1]*(Q-2*d));rng.shuffle(m)
        A=[0,math.log(2),1.25][j%3]
        if j%4==0:
            tau=np.clip(.5+rng.normal(0,1e-4,Q),0,1-1e-10)
            a=np.where(m==2,rng.uniform(0,1e-4,Q)*A,0)
        else:
            tau=rng.random(Q);a=np.where(m==2,rng.uniform(0,A,Q),0)
        configs.append((m,tau,a,A,int(rng.choice([2,3,4,6,9,12])),int(rng.integers(0,Q))))
    configs += [(np.array([1]),np.array([.3]),np.zeros(1),0,3,0),
        (np.array([2,0]),np.array([.3,.5]),np.array([.7,0]),.7,3,0),
        (np.array([2,2,1,1,0,0]),np.array([.99,.01,.5,.5,.5,.5]),np.zeros(6),0,6,0),
        (np.array([1,1,1,1,2,0]),np.full(6,.5),np.zeros(6),0,4,1)]
    count=good_count=bad_count=collision_count=0
    for m,tau,a,A,L,shift in configs:
        Q=len(m);s=float(np.count_nonzero(m==1)/Q);delta=s+moments(m,tau,a,1)-2
        le('signed_delta',0,delta)
        blocks,P,h,beta,cost,kmin=partition(m,tau,a,L,shift)
        le('hole_capacity',h/2,beta)
        C,_,_,_=constants(.75,A,L)
        eta=C*(math.pi**2*L*L+A*A/4)*max(delta,0)/kmin
        le('local_anchor_cost',cost,eta)
        for alpha in (.6,.75,.9,1.):
            C,R,Bnd,W=constants(alpha,A,L)
            E=Egood=Ebad=E0=0.
            for mb,tb,ab,t0,M in blocks:
                Eb=finite_energy(mb,tb,ab,alpha);E+=Eb
                le('finite_signed_block',2*mb.sum()-np.count_nonzero(mb==1),Eb)
                if t0 is None:Ebad+=Eb;bad_count+=1
                else:
                    Egood+=Eb;E0+=finite_energy(mb,t0,np.zeros(L),alpha);good_count+=1
                    collision_count+=int(max(M)>2)
                    K=L+2;f=(2*alpha-1)/alpha**2;c=1/alpha-f
                    per=0.
                    mh=np.fft.fft(M)/K
                    xx=np.arange(K)/K
                    sym=(np.maximum(alpha-xx,0)+np.maximum(alpha-1+xx,0))/alpha**2
                    sym[0]=1/alpha
                    per=K*float(np.dot(sym,abs(mh)**2))
                    Ef=finite_energy(M,np.arange(K),np.zeros(K),alpha)
                    wrap=32/(math.pi**2*alpha**2)*(3+math.log(K))
                    le('integer_wrap_nonnegative',Ef,per)
                    le('integer_wrap_upper',per-Ef,wrap)
                    le('finite_integer_floor',f*np.dot(M,M)+c*M.sum()**2/K-wrap,Ef)
            le('signed_cross_localization',abs(moments(m,tau,a,alpha)-E/P),Bnd)
            le('good_block_RMS',abs(math.sqrt(max(0,Egood/P))-math.sqrt(max(0,E0/P))),R*math.sqrt(cost))
            f=(2*alpha-1)/alpha**2;c=1/alpha-f
            I=0 if beta==1 else f*(2*(1-h)-s)+c*L/(L+2)*(1-h)**2/(1-beta)
            le('combined_integer_floor',I-W,E0/P)
            actual_lower=2*h+max(0,math.sqrt(max(0,I-W))-R*math.sqrt(cost))**2-Bnd
            theorem_lower=2*h+max(0,math.sqrt(max(0,I-W))-R*math.sqrt(eta))**2-Bnd
            le('local_ledger_actual_cost',actual_lower,moments(m,tau,a,alpha))
            le('local_ledger_defect_cost',theorem_lower,moments(m,tau,a,alpha));count+=1
    # Distinct implementation: continuous two-variable quadrature for a signed block.
    xx,ww=np.polynomial.legendre.leggauss(96)
    quadrature=[]
    for alpha in (.75,1.):
        m=np.array([2,1,0,2]);t=np.array([.95,1.02,2.4,3.6]);a=np.array([.7,0,0,.4])
        u=xx*alpha/2;w=ww*alpha/2;v=u[:,None]-u[None,:]
        B=sum(mi*np.exp(2j*np.pi*ti*v)*np.cosh(ai*v) for mi,ti,ai in zip(m,t,a))
        integral=float(np.sum(w[:,None]*w[None,:]*abs(B)**2)/alpha**2)
        direct=finite_energy(m,t,a,alpha);eq('continuous_quadrature',integral,direct)
        quadrature.append({'alpha':alpha,'direct':direct,'integral':integral})
    strain=[];hole=[]
    for Q in (36,72,144,288,576):
        m=np.tile([1,1,1,1,2,0],Q//6);p=np.arange(Q);tau=.5+np.sin(2*np.pi*p/Q)/8
        a=np.zeros(Q);delta=2/3+moments(m,tau,a,1)-2
        _,_,h,_,cost,_=partition(m,tau,a,6)
        eq('strain_holes',h,0.);le('strain_lower_Qdelta',1/96,Q*delta)
        le('strain_upper_Qdelta',Q*delta,math.pi**4/16)
        strain.append({'Q':Q,'delta':delta,'Q_delta':Q*delta,'local_cost_L6':cost,'h_L6':h,'short':moments(m,tau,a,.75)})
        k=Q//6;m=np.array([1]*(4*k)+[0]*k+[2]*k);tau=np.full(Q,.5);a=np.where(m==2,math.log(2),0)
        _,_,h,_,_,_=partition(m,tau,a,6)
        hole.append({'Q':Q,'delta':2/3+moments(m,tau,a,1)-2,'h_L6':h,'short':moments(m,tau,a,.75)})
    mp.mp.dps=70;threshold=(mp.mpf(101)-mp.sqrt(7321))/144
    # Nontrivial finite certificate: fully covered, zero-defect tangent word;
    # L can be large without constructing a dense Q-by-Q numerical matrix.
    alpha=.75;A=math.log(2);L=1000000
    _,R,Bnd,W=constants(alpha,A,L)
    I=(2*alpha-1)/alpha**2*(2-2/3)+(1/alpha-(2*alpha-1)/alpha**2)*L/(L+2)
    finite_bound=I-W-Bnd
    le('nontrivial_finite_margin',19/12,finite_bound)
    return {'ok':True,'attempt':'A-RH-LOC-0012','seed':SEED,'samples':samples,'boundary_configs':4,
        'model_scale_checks':count,'good_block_evaluations':good_count,'bad_block_evaluations':bad_count,
        'rounded_collision_evaluations':collision_count,
        'exact_checks':{'cross_boundary_counts':exact_cross,'wrap_counts':exact_wrap,'rounding_assignments':exact_rounding,
            'ten_percent_gap':'31/10260','cyclic_strain_Qdelta_lower':'1/96','relaxed_floor':'286/189','relaxed_gap':'53/756'},
        'minimum_slacks':slacks,'maximum_residuals':residuals,'quadrature':quadrature,'strain':strain,'hole_family':hole,
        'hole_threshold':mp.nstr(threshold,50),'nontrivial_scalar_certificate':{'L':L,'A':A,'delta':0,'h':0,'lower':finite_bound,'budget':19/12},
        'versions':{'python':platform.python_version(),'numpy':np.__version__,'mpmath':mp.__version__},
        'scope':'exact finite combinatorics and numerical regressions only; analytic statements remain proof candidates',
        'independent_verification':False,'mathematical_truth_verified':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--samples',type=int,default=120)
    p.add_argument('--output',type=Path,default=Path('validation.json'));p.add_argument('--check-package',action='store_true');args=p.parse_args()
    if args.check_package:
        root=Path(__file__).resolve().parent;cp=json.loads((root/'checkpoint.json').read_text())
        for name,h in cp['sha256'].items():
            if Path(name).name!=name or hashlib.sha256((root/name).read_bytes()).hexdigest()!=h:raise ValueError(name)
        claims=json.loads((root/'claims.json').read_text())['claims']
        assert len({c['id'] for c in claims})==len(claims) and all(c['evidence_grade']=='proof_candidate' for c in claims)
        print(json.dumps({'ok':True,'hashes':len(cp['sha256']),'claims':len(claims),'scope':'integrity only'}));return
    if not 1<=args.samples<=10000:p.error('samples must be in [1,10000]')
    result=run(args.samples);args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('ok','samples','model_scale_checks','exact_checks','hole_threshold','maximum_residuals')}))
if __name__=='__main__':main()
