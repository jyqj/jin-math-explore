#!/usr/bin/env python3
"""Reproduce finite tests for A-RH-OFFDIAG-0020; no actual zero computation."""
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
from offdiag_tools import (Profile,B,make_symbol,symbol_value,symbol_mean,
                          toeplitz_test,operators,lag_products,kernel_pair,continuous_integral)

SEED=2026090820

def exact_checks():
    counts={}; named={}
    n=0
    for L in range(1,25):
        for R in range(1,25):
            total=F(0)
            for k in range(L+R-1):
                pairs=sum(i+j==k for i in range(L) for j in range(R))
                assert pairs<=k+1
                total+=F(pairs,(k+1)**2); n+=1
            assert total<=sum((F(1,j) for j in range(1,L+R)),F(0))
    counts['interface_lag_multiplicities']=n
    counts['interface_harmonic_bounds']=24*24
    n=0
    for q in range(1,25):
        for width in range(0,7):
            b=[F((-1)**j*(j+1),j+2) for j in range(width+1)]
            g={}
            for j in range(len(b)):
                for k in range(len(b)):
                    g[j-k]=g.get(j-k,F(0))+b[j]*b[k]
            v=[F((j%5)-2,j+1) for j in range(q)]
            quadratic=sum((v[j]*v[k]*g.get(j-k,F(0))
                           for j in range(q) for k in range(q)),F(0))
            conv=[sum((b[k]*v[t-k] for k in range(len(b)) if 0<=t-k<q),F(0))
                  for t in range(q+width)]
            assert quadratic==sum((x*x for x in conv),F(0))>=0
            d=[F(j+1,q) for j in range(q)]
            norm=sum((d[j]*d[k]*g.get(j-k,F(0))**2 for j in range(q) for k in range(q)),F(0))
            lags=sum((g.get(h,F(0))**2*sum((d[j]*d[j+abs(h)] for j in range(q-abs(h))),F(0))
                      for h in range(-min(width,q-1),min(width,q-1)+1)),F(0))
            assert norm==lags; n+=1
    counts['toeplitz_psd_gram']=n; counts['weighted_lag_norms']=n
    n=0
    for q in range(1,17):
        heights=[F(j+1,q+1) for j in range(q)]
        K=[[F((j+2)*(k+2)%7-3,1+j+k) for k in range(q)] for j in range(q)]
        for power in range(1,5):
            direct=sum((K[j][k]*max(heights[j],heights[k])**power
                        for j in range(q) for k in range(q)),F(0))
            Aend=sum((x for row in K for x in row),F(0))
            cuts=[F(0)]+heights+[F(1)]
            integ=F(0)
            for left,right in zip(cuts,cuts[1:]):
                val=sum((K[j][k] for j in range(q) for k in range(q)
                         if max(heights[j],heights[k])<=left),F(0))
                integ+=val*(right**power-left**power)
            assert direct==Aend-integ; n+=1
    counts['signed_stieltjes_identities']=n
    coefficient=F(9,4)*(F(100,81)+F(1,2))
    assert coefficient==F(281,72)<4
    assert 4-coefficient==F(7,72)
    assert F(12,11)<F(3,2)
    assert F(5,2)-F(3,2)==1
    assert F(4)-F(2)==2
    counts['rational_scope_constants']=5
    named.update({'saturation_coefficient':str(coefficient),'coefficient_margin':str(4-coefficient),
                  'optimizer_sup_majorant':'12/11','translation_trace_T':'5/2 versus 3/2',
                  'translation_trace_T_squared':'4 versus 2'})
    return counts,named


def run(samples):
    rng=np.random.default_rng(SEED)
    residuals={}; min_slacks={}; counts={}
    def equal(name,left,right):
        e=float(np.max(abs(np.asarray(left)-np.asarray(right))))
        scale=1+float(np.max(abs(np.asarray(left))))+float(np.max(abs(np.asarray(right))))
        residuals[name]=max(residuals.get(name,0.),e)
        residuals[name+'_relative']=max(residuals.get(name+'_relative',0.),e/scale)
        if e>2e-9*scale:
            raise AssertionError((name,e,scale))
    def bound(name,left,right):
        slack=float(right-left); min_slacks[name]=min(min_slacks.get(name,math.inf),slack)
        if slack< -2e-9*(1+abs(left)+abs(right)):
            raise AssertionError((name,left,right))
    models=[]
    for i in range(samples):
        q=int(rng.choice([2,3,5,8,12,16,24,32])); k=int(rng.integers(1,9))
        centers=np.sort(rng.uniform(-.25*q,.6*q,k))
        masses=rng.integers(1,5,k)
        depths=np.where(masses%2==0,rng.uniform(0,2.0,k),0.)
        a=float(rng.uniform(-.24,.24))
        r=Profile(((0.,1.),(1.,a/2),(-1.,a/2)))
        d=Profile(((0.,1.),(2.,.2),(-2.,.2)))
        models.append((q,centers,masses,depths,r,d))
    one=Profile(((0.,1.),))
    models += [(1,[.3],[1],[0.],one,one), (2,[.2],[4],[2.],one,one),
               (8,list(range(8)),[1]*8,[0.]*8,one,one),
               (4,[.1,.100001,.3],[1,1,2],[0,0,1.5],one,one)]
    lagchecks=wrong_phase_detected=positive_bounds=endpointchecks=integrals=0
    for idx,(q,t,m,a,r,d) in enumerate(models):
        data=operators(q,t,m,a,r); T=data['T']; S=data['S']; N=data['N']; n=data['n']
        dv=d.values(data['u'])
        taps=[1.,.25+.2j,-.15j] if idx%2 else [1.,.5]
        coeffs=make_symbol(taps); C=toeplitz_test(q,dv,coeffs)
        bound('PSD_test',0,float(np.linalg.eigvalsh(C)[0]))
        gupper=sum(abs(complex(x)) for x in taps)**2
        bound('test_operator_norm',np.linalg.norm(C,2),float(np.max(dv))*gupper)
        exactnorm=sum(abs(c)**2*np.dot(dv[:q-abs(h)],dv[abs(h):])
                      for h,c in coeffs.items() if abs(h)<q)
        equal('test_Frobenius_lags',np.linalg.norm(C,'fro')**2,exactnorm)
        D=n+np.linalg.norm(T,'fro')**2-2*N
        bound('signed_slack',0,D)
        lhs=float(np.trace(C@(T@T-2*T+S)).real)
        rhs=-math.sqrt((4*np.linalg.norm(C,'fro')**2+2*n*np.linalg.norm(C,2)**2)*max(D,0))
        bound('positive_test_inequality',rhs,lhs)
        positive_bounds+=int(lhs>0)
        reconstruct=0j
        for h in range(min(4,q-1)+1):
            direct,pair,linear,pairlin,wrong=lag_products(data,dv,h)
            equal('exact_lag_pair',direct,pair); equal('exact_lag_linear',linear,pairlin)
            if h and abs(direct-wrong)>1e-6:
                wrong_phase_detected+=1
            if h in coeffs:
                reconstruct+=coeffs[h]*direct if h==0 else 2*np.real(coeffs[h]*direct)
            # Endpoint approximation to dr: a finite bound with the actual sqrt-profile derivative majorant.
            rv=data['r']; v=np.sqrt(dv*rv); z=data['z']; w=z[:,None]-z[None,:]
            H=np.sum((v[:q-h]*v[h:])[:,None,None]*np.exp(2j*np.pi*data['u'][:q-h,None,None]*w),axis=0)/q
            Fdr=np.sum((dv*rv)[:,None,None]*np.exp(2j*np.pi*data['u'][:,None,None]*w),axis=0)/q
            Ar=sum(abs(co) for _,co in r.terms); Ad=sum(abs(co) for _,co in d.terms)
            mr=sum(co for nu,co in r.terms if nu==0)-sum(abs(co) for nu,co in r.terms if nu!=0)
            md=sum(co for nu,co in d.terms if nu==0)-sum(abs(co) for nu,co in d.terms if nu!=0)
            Lr=2*np.pi*sum(abs(nu*co) for nu,co in r.terms)
            Ld=2*np.pi*sum(abs(nu*co) for nu,co in d.terms)
            Mv=math.sqrt(Ar*Ad); Lv=(Lr*Ad+Ld*Ar)/(2*math.sqrt(mr*md))
            major=(h/q)*(Mv*Lv+Mv*Mv)*np.exp(np.pi*abs(w.imag))
            bound('finite_endpoint_majorant',float(np.max(abs(H-Fdr)-major)),0.)
            lagchecks+=1; endpointchecks+=1
        equal('trace_reconstruction',np.trace(C@T@T)/N,reconstruct)
        if idx<12:
            # Deliberately separate continuous integral, only on modest synthetic lists.
            zz=data['z']*.2
            kg=kernel_pair(d.product(r),r,zz)
            val=continuous_integral(d.product(r),r,zz,nodes=80)
            equal('alternative_continuous_integral',kg.sum()/len(zz),val)
            integrals+=1
    counts.update({'finite_models':len(models),'PSD_tests':len(models),'lag_pair_and_linear_checks':lagchecks,
                   'endpoint_estimate_checks':endpointchecks,'detected_missing_height_phases':wrong_phase_detected,
                   'positive_observed_row_values':positive_bounds,'alternative_integrals':integrals})
    mp.mp.dps=80; lam=mp.mpf(1)/2+mp.cot(1/mp.sqrt(2))/mp.sqrt(2); sigma=float(2-lam)
    saturation=[]
    for i in range(samples):
        omega=float(rng.uniform(.1,2.7)); freq=omega/(2*np.pi)
        r=Profile(((freq,.5),(-freq,.5))).normalized()
        d=Profile(((0.,1.),(1.,.15),(-1.,.15),(2.,.08),(-2.,.08)))
        taps=[1.,complex(rng.uniform(-.5,.5),rng.uniform(-.5,.5)),.2j]
        coeffs=make_symbol(taps); G2=float(sum(abs(x)**2 for x in coeffs.values()))
        d2=d.product(d).integral(); dsup=sum(abs(x) for _,x in d.terms)
        gsup=sum(abs(x) for x in taps)**2
        for theta in (.9,.93,.97,1.):
            dr=d.product(r); br=B(theta,r,r); delta=br-float(lam)
            W=symbol_mean(coeffs,theta)
            bound('height_symbol_cauchy',W*W,G2/theta)
            bound('profile_defect',0.,delta)
            lhs=W*(B(theta,dr,r)-float(lam)*dr.integral())
            sharp=-math.sqrt(float(F(281,72))*d2*G2*max(delta,0))
            relaxed=-math.sqrt((4*d2*G2+2*sigma*dsup*dsup*gsup*gsup)*max(delta,0))
            bound('uniform_consistency',sharp,lhs); bound('source_row_relaxation',relaxed,lhs)
            if i<2:
                saturation.append({'theta':theta,'omega':omega,'height_average':W,'left':lhs,'lower':relaxed})
    counts['scalar_consistency_checks']=samples*4
    rstar=Profile(((math.sqrt(2)/(2*np.pi),.5),(-math.sqrt(2)/(2*np.pi),.5))).normalized()
    d=Profile(((0.,1.),(1.,.2),(-1.,.2)))
    equal('optimizer_stationarity',B(1,d.product(rstar),rstar),float(lam)*d.product(rstar).integral())
    # Translation does not change any difference-only kernel moment but changes non-diagonal traces.
    guards=[]; coeffs={0:1.,1:.5,-1:.5}
    for translation in (0.,1.):
        dat=operators(2,[translation,translation+.5],[1,1],[0,0],one)
        C=toeplitz_test(2,np.ones(2),coeffs); T=dat['T']
        guards.append({'translation':translation,'trace_T':float(np.trace(C@T).real),
                       'trace_T2':float(np.trace(C@T@T).real),'HS_squared':float(np.linalg.norm(T,'fro')**2)})
    equal('translation_exact_traces',[g['trace_T'] for g in guards],[2.5,1.5])
    equal('translation_exact_squared_traces',[g['trace_T2'] for g in guards],[4.,2.])
    equal('translation_difference_invariance',[g['HS_squared'] for g in guards],[3.,3.])
    growing=[]
    for q in (4,8,16,32,64):
        dat=operators(q,[0.],[1],[0.],one)
        h=q//2; exact=sum(dat['T'][j,j+h] for j in range(q-h))
        equal('growing_lag_endpoint',exact,.5)
        growing.append({'q':q,'lag':h,'exact_lag_trace':float(exact.real),'incorrect_fixed_lag_limit':1})
    ex,named=exact_checks()
    return {'ok':True,'attempt':'A-RH-OFFDIAG-0020','seed':SEED,'random_samples':samples,
            'counts':counts,'exact_counts':ex,'exact_total':sum(ex.values()),'exact_constants':named,
            'maximum_residuals':residuals,'minimum_slacks':min_slacks,
            'scalar_examples':saturation,'translation_guard':guards,'growing_lag_guard':growing,
            'known_benchmark':mp.nstr(2-lam,55),
            'backend':{'python':platform.python_version(),'numpy':np.__version__,'mpmath':mp.__version__},
            'scope':'Finite self-checks; no actual zeta zeros, PC remainders, asymptotic simulation or independent verification.',
            'independent_verification':False,'mathematical_truth_verified':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples',type=int,default=120)
    parser.add_argument('--output',type=Path,default=Path('validation.json'))
    parser.add_argument('--check-package',action='store_true')
    args=parser.parse_args()
    if args.check_package:
        root=Path(__file__).resolve().parent
        checkpoint=json.loads((root/'checkpoint.json').read_text())
        for name,digest in checkpoint['sha256'].items():
            path=root/name
            if Path(name).name!=name or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
                raise ValueError('invalid path or hash: '+name)
        claims=json.loads((root/'claims.json').read_text())['claims']
        assert len({c['id'] for c in claims})==len(claims)
        assert all(c['evidence_grade']=='proof_candidate' and c['cannot_imply'] for c in claims)
        print(json.dumps({'ok':True,'hashes':len(checkpoint['sha256']),'claims':len(claims),'scope':'integrity only'}))
        return 0
    if not 1<=args.samples<=2000:
        parser.error('--samples must be between 1 and 2000')
    out=run(args.samples)
    args.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'counts':out['counts'],'exact_counts':out['exact_counts'],
                      'exact_total':out['exact_total'],'output':str(args.output)}))
    return 0

if __name__=='__main__':
    sys.exit(main())
