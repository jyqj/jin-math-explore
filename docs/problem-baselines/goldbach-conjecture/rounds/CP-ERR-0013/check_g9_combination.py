#!/usr/bin/env python3
"""CP-ERR-0013: finite identities and fixed integrals, NOT a Goldbach verifier.
Python >=3.10, mpmath==1.3.0. --compute integrates; --check never integrates.
--output creates a new file only. Source assumptions/analytic error: proof.md.
"""
from __future__ import annotations
import argparse
from collections import Counter
from fractions import Fraction as F
from functools import lru_cache
import hashlib
import itertools
import json
from math import gcd, isqrt, prod
from pathlib import Path
import sys
import mpmath as mp

ROOT = Path(__file__).resolve().parent
A, B, G, C = F(4,53), F(4,33), F(3,11), F(1,3)
CUT = F(1,10)
CELLS, DPS = 8192, 50
CAP = F('5.291548')
FILES = ('README.md','proof.md','contracts.json','prior-work.json','source-lock.json',
         'check_g9_combination.py','results.json','error-handoff.json',
         'computation-record.json','computation-handoff.json','verification-ticket.md','validation.json')


def need(ok: bool, msg: str) -> None:
    if not ok: raise ValueError(msg)


def ivq(x):
    x=F(x)
    return mp.iv.mpf(x.numerator)/x.denominator


def binary_fraction(t):
    sign, man, exponent, bits=t
    need(bits>=0,'nonfinite endpoint')
    x=F(-man if sign else man)
    return x*2**exponent if exponent>=0 else x/F(2**(-exponent))


def endpoints(v):
    lo,hi=map(binary_fraction,v._mpi_)
    need(lo<=hi,'interval orientation')
    return lo,hi


def dec(x: F, up: bool, places=18):
    scale=10**places
    k=-((-x.numerator*scale)//x.denominator) if up else (x.numerator*scale)//x.denominator
    sign='-' if k<0 else ''; k=abs(k)
    return f'{sign}{k//scale}.{k%scale:0{places}d}'


def box(value, error):
    lo,hi=endpoints(value)
    return [dec(lo-error,False),dec(hi+error,True)]


def derivative_bounds():
    b0=1/A+F(3,2); b1=1/A**2+F(9,4); b2=2/A**3+F(27,4)
    h0=8*b0; h1=8*(3*b0+b1); h2=8*(9*b0+6*b1+b2)
    mixed=h2*F(27,20)+2*h1*F(81,40)+h0*F(243,40)
    need(h2<50000 and mixed<100000,'analytic derivative envelope')
    return {'base_derived':str(h2),'mixed_derived':str(mixed),
            'base_used':'50000','mixed_used':'100000','penalty_used':'150000'}


def compute():
    need(mp.__version__=='1.3.0','requires mpmath 1.3.0')
    mp.iv.dps=DPS
    low=ivq(0); mixed_low=ivq(0); penalty=ivq(0); high=ivq(0); wedge=ivq(0)
    for left,right,kind in ((A,CUT,'low'),(CUT,C,'high'),(B,1-3*G,'wedge')):
        step=(right-left)/CELLS
        for j in range(CELLS):
            u=ivq(left+F(2*j+1,2)*step)
            h=8*mp.iv.log(2-3*u)/(u*(1-u)) if kind!='wedge' else 8*mp.iv.log((1-ivq(G)-u)/(2*ivq(G)))/(u*(1-u))
            term=h*ivq(step)
            if kind=='low':
                ratio=ivq(F(9,10))/(1-u)
                low+=term; mixed_low+=term*ratio; penalty+=term*(1-ratio)
            elif kind=='high': high+=term
            else: wedge+=term
    e_low=F(50000)*(CUT-A)**3/(24*CELLS**2)
    e_hi=F(50000)*(C-CUT)**3/(24*CELLS**2)
    e_mix=2*e_low+e_hi; e_bv=e_low+e_hi; e_pen=3*e_low
    e_w=F(50000)*(1-3*G-B)**3/(24*CELLS**2)
    out={'schema':'goldbach-g9-combination-integrals/v1','checkpoint':'CP-ERR-0013',
         'backend':'mpmath.iv','backend_version':mp.__version__,'decimal_precision':DPS,
         'cells_per_piece':CELLS,'distinct_midpoint_nodes':3*CELLS,
         'derivative_bounds':derivative_bounds(),
         'g9_half_level':box(low+high,e_bv),'g9_mixed_formula':box(mixed_low+high,e_mix),
         'half_minus_mixed':box(penalty,e_pen),'wedge_comparison':box(wedge,e_w),
         'errors':{'half':str(e_bv),'mixed':str(e_mix),'penalty':str(e_pen),'wedge':str(e_w)},
         'g9_half_safe_cap':str(CAP),'cap_increase_vs_printed':'9619/500000',
         'mixed_formula_is_accepted_G9_bound':False,'intervals_are_actual_counts':False,
         'CP12_wedge_gain_globally_spendable':False,'independently_verified':False,
         'aggregate_theorem_refuted':False,'global_status':'INCONCLUSIVE'}
    validate_results(out)
    return out


def validate_results(d):
    need(d['schema']=='goldbach-g9-combination-integrals/v1','schema')
    need(d['checkpoint']=='CP-ERR-0013','checkpoint')
    need(d['cells_per_piece']==CELLS and d['distinct_midpoint_nodes']==3*CELLS,'coverage')
    need(d['derivative_bounds']==derivative_bounds(),'derivative bound mutation')
    e_low=F(50000)*(CUT-A)**3/(24*CELLS**2); e_hi=F(50000)*(C-CUT)**3/(24*CELLS**2)
    expected={'half':str(e_low+e_hi),'mixed':str(2*e_low+e_hi),'penalty':str(3*e_low),
              'wedge':str(F(50000)*(1-3*G-B)**3/(24*CELLS**2))}
    need(d['errors']==expected,'quadrature radius mutation')
    bv=tuple(map(F,d['g9_half_level'])); mix=tuple(map(F,d['g9_mixed_formula']))
    p=tuple(map(F,d['half_minus_mixed'])); w=tuple(map(F,d['wedge_comparison']))
    need(F('5.29154')<bv[0]<=bv[1]<CAP<6,'half-level enclosure')
    need(F('5.27229')<mix[0]<=mix[1]<F('5.27231'),'mixed enclosure')
    need(F('.019247')<p[0]<=p[1]<F('.019248'),'penalty enclosure')
    need(F('.215661')<w[0]<=w[1]<F('.215662'),'wedge enclosure')
    need(bv[0]<=mix[1]+p[1] and mix[0]+p[0]<=bv[1],'formula relation')
    need(F(d['g9_half_safe_cap'])==CAP,'cap')
    need(F(d['cap_increase_vs_printed'])==CAP-F('5.27231'),'printed comparator')
    for k in ('mixed_formula_is_accepted_G9_bound','intervals_are_actual_counts',
              'CP12_wedge_gain_globally_spendable','independently_verified','aggregate_theorem_refuted'):
        need(d[k] is False,'scope escalation: '+k)
    need(d['global_status']=='INCONCLUSIVE','global escalation')


@lru_cache(None)
def primes(n):
    if n<2: return ()
    sieve=bytearray(b'\1')*(n+1); sieve[:2]=b'\0\0'
    for p in range(2,isqrt(n)+1):
        if sieve[p]: sieve[p*p:n+1:p]=b'\0'*(((n-p*p)//p)+1)
    return tuple(i for i in range(2,n+1) if sieve[i])


@lru_cache(None)
def factors(n):
    ans=[]; x=n
    for p in primes(isqrt(n)):
        if p*p>x: break
        if x%p==0:
            e=0
            while x%p==0: e+=1; x//=p
            ans.append((p,e))
    if x>1: ans.append((x,1))
    return tuple(ans)


def phi(n):
    result=n
    for p,_ in factors(n): result=result//p*(p-1)
    return result


def le_power(p,N,x): return p**x.denominator<=N**x.numerator

def ge_power(p,N,x): return p**x.denominator>=N**x.numerator


def sift(n,mod,excluded,cut=None,square_ratio=None,power=None):
    if n%mod: return 0
    for p,_ in factors(n):
        if excluded%p==0: continue
        small=(p<cut) if cut is not None else (p*p*square_ratio[1]<square_ratio[0] if square_ratio is not None else p**power[1].denominator<power[0]**power[1].numerator)
        if small: return 0
    return 1


def tuples_dividing(n,k):
    fs=[p for p,_ in factors(n)]
    return [ps for ps in itertools.combinations_with_replacement(fs,k) if n%prod(ps)==0]


def pointwise(N,n):
    need(N%2==0 and 1<=n<N,'native N,n')
    s=lambda mod,ex,**kw:sift(n,mod,ex,**kw)
    vals=[s(1,N,power=(N,A)),s(1,N,power=(N,B)),0,0,0,0,0,0,0,0,0,0]
    for p,_ in factors(n):
        if gcd(p,N)!=1: continue
        if ge_power(p,N,F(9,19)) and p*p<=N: vals[2]+=s(p,N,cut=p)
        if ge_power(p,N,A) and le_power(p,N,C): vals[3]+=s(p,N,power=(N,A))
        if ge_power(p,N,A) and le_power(p,N,G): vals[4]+=s(p,N,power=(N,A))
    aux={'S5':0,'C_wedge':0,'C_order':0,'G16_literal':0,'G16_subscript_only':0,
         'S6':0,'G14':0,'G15':0}
    for p,q in tuples_dividing(n,2):
        mod=p*q
        if gcd(mod,N)!=1: continue
        if ge_power(p,N,A) and le_power(q,N,B): vals[5]+=s(mod,N,power=(N,A))
        if ge_power(p,N,A) and le_power(p,N,B) and ge_power(q,N,B) and le_power(q,N,G): vals[6]+=s(mod,N,power=(N,A))
        if p*q*q<=N:
            if ge_power(p,N,G): vals[7]+=s(mod,N*p,cut=q)
            if ge_power(p,N,A) and le_power(p,N,C) and ge_power(q,N,C): vals[8]+=s(mod,N*p,cut=q)
            if ge_power(p,N,B) and le_power(p,N,G) and ge_power(q,N,G):
                small=s(mod,N*p,cut=q); large=s(mod,N*p,square_ratio=(N,mod))
                vals[9]+=large; aux['S5']+=small
                need(p!=q and p*q**3!=N,'native endpoints')
                if p*q**3<N: aux['C_wedge']+=small; need(large==0,'zero wedge')
                else: aux['C_order']+=large-small; need(large>=small,'active monotonicity')
                for t in primes(isqrt(N//mod)):
                    if t<q or gcd(t,N)>1: continue
                    aux['G16_literal']+=s(mod,N*p,cut=t)
                    aux['G16_subscript_only']+=s(mod*t,N*p,cut=t)
    for ps in tuples_dividing(n,3):
        p,q,r=ps; mod=prod(ps)
        if gcd(mod,N)>1: continue
        if ge_power(p,N,A) and le_power(r,N,C): aux['S6']+=s(mod,N*p,cut=q)
        if ge_power(p,N,A) and le_power(r,N,B): aux['G14']+=s(mod,N,cut=p)
        if ge_power(p,N,A) and le_power(q,N,B) and ge_power(r,N,B) and le_power(r,N,G): aux['G15']+=s(mod,N,cut=p)
    for ps in tuples_dividing(n,4):
        p,q,r,t=ps; mod=prod(ps)
        if gcd(mod,N)>1: continue
        if ge_power(p,N,A) and le_power(t,N,B): vals[10]+=s(mod,N*p,cut=q)
        if ge_power(p,N,A) and le_power(r,N,B) and ge_power(t,N,B) and le_power(t,N,G): vals[11]+=s(mod,N*p,cut=q)
    aux['pointwise_combination']=sum(v*w for v,w in zip(vals,(3,1,-4,-1,-1,1,1,-2,-1,-1,-1,-1)))
    aux['G_values']=vals
    return aux


def self_test():
    mp.iv.dps=DPS; counts=Counter()
    for x in (F(0),F(1,3),F(-7,9),F(10)**25,F(1,2**100)):
        lo,hi=endpoints(ivq(x)); need(lo<=x<=hi and F(dec(x,False))<=x<=F(dec(x,True)),'serialization'); counts['serialization']+=1
    for n in range(1,257):
        need(F(n,phi(n))==sum((F(1,phi(d)) for d in range(1,n+1) if n%d==0 and all(e==1 for _,e in factors(d))),F(0)),'totient identity'); counts['totient_identity']+=1
    for N in range(100,701,100):
        # Exact identities for arbitrary singleton data, not an asymptotic claim.
        for n in range(1,N,2):
            v=pointwise(N,n)
            need(v['S5']==v['G_values'][9]+v['C_wedge']-v['C_order'],'two-sided cutoff identity')
            need(v['G16_literal']==v['C_wedge'],'literal G16 collapse')
            counts['cutoff_and_G16_models']+=1
    witness=pointwise(144568,144565)
    need(factors(144565)==((5,1),(29,1),(997,1)),'squarefree witness')
    need(witness['G_values']==[1,1,0,2,1,0,0,0,0,0,0,0],'twelve weights')
    need(witness['pointwise_combination']==1 and witness['S6']==0 and witness['G14']==0 and witness['G15']==0 and witness['G16_literal']==1 and witness['G16_subscript_only']==0,'pointwise counterexample')
    need(144568-144565==3 and 3 in primes(3),'actual prime output')
    other=pointwise(5504,4495)
    need(1009 in primes(1009) and factors(4495)==((5,1),(29,1),(31,1)),'ordering witness')
    need(other['S5']==1 and other['G_values'][9]==2 and other['C_wedge']==0 and other['C_order']==1,'missing negative ordering correction')
    four=pointwise(166318,166315)
    need(factors(166315)==((5,1),(29,1),(31,1),(37,1)) and four['C_wedge']==1,'four-prime wedge witness')
    need(sift(166315,5*29,166318*5,cut=29)==1 and 31*37 not in primes(31*37),'composite wedge residual')
    counts['explicit_pointwise_witnesses']+=3
    # Family geometry on all corners; endpoints need not themselves be prime.
    for x in (729,1000,10000):
        for e1,e2,e3 in itertools.product((1,2),repeat=3):
            p=e1*x**6; q=e2*x**11; r=e3*x**23; N=p*q*r+3
            need(ge_power(p,N,B) and le_power(p,N,G) and ge_power(q,N,G) and le_power(q,N,C) and ge_power(r,N,C),'family intervals')
            need(p*q**3<N and p*r*r>N and N<9*x**40,'family wedge/large prime')
            counts['family_corner_geometry']+=1
    nonzero_H=0; native_survivors=0; max_mult=0
    for N in (502,1002,2002,5002,10002):
        ps=primes(N); ps_set=set(ps)
        pairs=[(p,q) for p in ps if ge_power(p,N,A) and le_power(p,N,C) and N%p
               for q in ps if q>=p and ge_power(q,N,C) and p*q*q<=N and N%q]
        need(all(p<q for p,q in pairs),'separated native G9 ranges')
        masses={p*q:[t for t in ps if p*q*t<N] for p,q in pairs}
        need(len(masses)==len(pairs),'product multiplicity')
        for m in masses: need(m**3>=N and m**3<=N*N,'slab inclusion'); counts['native_support']+=1
        seq=[N-m*t for m in masses for t in masses[m]]
        mult=Counter(seq); max_mult=max(max_mult,max(mult.values(),default=0)); need(max(mult.values(),default=0)<=3,'switched multiplicity')
        counts['indexed_sequences']+=1
        for b0 in ps:
            if 4*b0>=3*N: continue
            n=N-b0
            for p,q in pairs:
                if not sift(n,p*q,N*p,cut=q): continue
                native_survivors+=1
                if gcd(n,N)>1 or n%(p*p)==0 or n==p*q: continue
                r=n//(p*q); need(r in ps_set and r>=q and r in masses[p*q],'native residual classification')
        R=N//2; P0=6; W=3 if N%3 else 1; D=F(R,P0); Z=isqrt(R//P0)
        mods=[d for d in range(1,R) if d<W*D and gcd(d,N)==1 and all(e==1 and p<Z for p,e in factors(d))]
        need(1 in mods,'unit modulus')
        Xs={m:F(2*N,3*m) for m in masses}; X=sum(Xs.values(),F(0)); delta=len(seq)-X
        raw_budget=rebudget=Hbudget=tot=F(0)
        for d in mods:
            cnt=sum(n%d==0 for n in seq)
            cop=sum((xm for m,xm in Xs.items() if gcd(m,d)==1),F(0))
            H=(X-cop)/phi(d); e=F(cnt)-cop/phi(d)
            raw=F(cnt)-X/phi(d); rebased=F(cnt)-F(len(seq),phi(d))
            need(raw==e-H and rebased==e-H-delta/phi(d),'AP H and mass rebasing')
            need(d<R,'exceptional-prime support')
            if d==1: need(H==0 and e==delta and rebased==0,'d=1 shared mass')
            if H>0: nonzero_H+=1
            raw_budget+=abs(e); rebudget+=abs(rebased); Hbudget+=H; tot+=F(1,phi(d))
            counts['AP_H_rebase_support']+=1
        need(rebudget<=raw_budget+Hbudget+abs(delta)*tot,'aggregate rebase bound'); counts['aggregate_budgets']+=1
    # Finite algebra for the normalized contract; not tests of Mertens/BV.
    for q,ell,h,r,eps in itertools.product((F(0),F(1,4),F(1,2)),(F(0),F(1,4),F(1,2)),(F(0),F(1,8),F(1,4)),(F(0),F(1,4),F(1,2)),(F(0),F(1,200))):
        I=F(2,3)
        main=8*(1+q)*(1+ell)*(I+15*r)/(1-2*h)
        need(main<=8*I+15*q+15*ell+24*h+540*r,'normalization bound')
        need(154*216*eps==33264*eps,'sieve coefficient'); counts['normalized_algebra']+=1
    # Signed cancellation and source-level classes are deliberately not identified.
    failures=0
    def reject(ok):
        nonlocal failures
        try: need(ok,'negative control')
        except ValueError: failures+=1
        else: raise ValueError('negative control accepted')
    reject(witness['pointwise_combination']<=0)
    reject(witness['S6']>=witness['G14']+witness['G15']+witness['G16_literal'])
    reject(witness['G16_literal']==witness['G16_subscript_only'])
    reject(witness['S5']==witness['G_values'][9]+witness['G16_subscript_only'])
    reject(other['S5']==other['G_values'][9]+other['C_wedge'])
    reject(other['C_order']==0)
    reject(F(1)-F(1)==abs(F(1))+abs(F(-1)))
    reject(105<100)  # 105=3*5*7 <3*100; forgetting W inflates support.
    reject(nonzero_H==0)
    reject(F(65,159)>=F(6,11))  # the old narrower CP6 does not cover G9.
    reject(F(36,5)/(1-F(2,25))==8)
    reject(31*37 in primes(31*37))
    return {'schema':'goldbach-g9-combination-finite/v1','checkpoint':'CP-ERR-0013',
            'counts':dict(sorted(counts.items())),'finite_cases':sum(counts.values()),
            'native_G9_survivors_classified':native_survivors,'nonzero_H_models':nonzero_H,
            'max_switched_multiplicity_observed':max_mult,'witness_144568':witness,'ordering_witness_5504':other,'four_prime_wedge_witness_166318':four,
            'structural_negative_controls_rejected':failures,'finite_AP_main':'synthetic X_m=2N/(3m), not Li data',
            'family_corner_tests_are_not_prime_enumeration':True,'aggregate_theorem_refuted':False,
            'independent_verification':False}


def check():
    d=json.loads((ROOT/'results.json').read_text()); validate_results(d)
    manifest=json.loads((ROOT/'artifact-sha256.json').read_text())
    need(set(manifest['sha256'])==set(FILES),'manifest coverage')
    for name,sha in manifest['sha256'].items(): need(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,'hash '+name)
    tests=self_test(); need(tests==json.loads((ROOT/'validation.json').read_text()),'finite replay')
    contract=json.loads((ROOT/'contracts.json').read_text())
    need(contract['global_status']=='INCONCLUSIVE' and contract['combination_gate']=='BLOCKED_POINTWISE_ROUTE','contract authority')
    need(contract['CP12_wedge_gain_globally_spendable'] is False,'wedge gate')
    mutations=0
    for key,value in [('global_status','PASS'),('aggregate_theorem_refuted',True),('CP12_wedge_gain_globally_spendable',True),('independently_verified',True),('g9_half_safe_cap','5'),('distinct_midpoint_nodes',8192),('errors',{}),('g9_half_level',['6','5'])]:
        bad=dict(d); bad[key]=value
        try: validate_results(bad)
        except (ValueError,KeyError,TypeError): mutations+=1
        else: raise ValueError('result mutation accepted')
    return {'ok':True,'hashes_checked':len(FILES),'finite_cases_replayed':tests['finite_cases'],
            'negative_controls_rejected':tests['structural_negative_controls_rejected']+mutations,
            'quadrature_replayed':False,'global_status':'INCONCLUSIVE','aggregate_theorem_refuted':False}


def main():
    p=argparse.ArgumentParser(description=__doc__); group=p.add_mutually_exclusive_group(required=True)
    for flag in ('compute','self-test','check','require-global'): group.add_argument('--'+flag,action='store_true')
    p.add_argument('--output',type=Path); args=p.parse_args()
    if args.require_global:
        print('REJECT: G16 pointwise route fails; aggregate repair and independent source/candidate review remain open.'); return 1
    result=compute() if args.compute else (self_test() if args.self_test else check())
    if args.output:
        need(not args.check,'check never writes')
        with args.output.open('x',encoding='utf-8') as f: f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    elif args.compute: need(result==json.loads((ROOT/'results.json').read_text()),'fresh numerical result differs')
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0

if __name__=='__main__':
    try: sys.exit(main())
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print('FAIL: '+str(exc),file=sys.stderr); sys.exit(1)
