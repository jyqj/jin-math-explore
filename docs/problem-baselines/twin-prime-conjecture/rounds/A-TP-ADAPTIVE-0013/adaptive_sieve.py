#!/usr/bin/env python3
"""Exact root-adaptive auxiliary sieve. No floating-point or global theorem acceptance."""
from __future__ import annotations
import argparse
from collections import defaultdict
from fractions import Fraction as Q
from functools import lru_cache
from itertools import product
from math import gcd, lcm, prod
from pathlib import Path
import json

INPUTS = {'schema':'twin-adaptive-input/v1','attempt':'A-TP-ADAPTIVE-0013',
          'rho':'2624989/10000000','gamma':'2742997/10000000','budget':'4992997/10000000',
          'finite':{'primes':[5,7,11],'shifts':[0,2,6,8],'B':'7/3','W':6,'residue':5,
                    'start':1001,'length':6000,'root_max':385,'fixed_Z':77,
                    'helper_root_max':7,'helper_total_max':35}}


def need(ok: bool, message: str) -> None:
    if not ok: raise ValueError(message)


def encode(v):
    if isinstance(v,Q): return str(v)
    if isinstance(v,dict): return {str(k):encode(x) for k,x in v.items()}
    if isinstance(v,(tuple,list)): return [encode(x) for x in v]
    return v


@lru_cache(None)
def factors(n: int) -> tuple[int,...]:
    out=[];p=2
    while p*p<=n:
        while n%p==0:out.append(p);n//=p
        p+=1
    if n>1:out.append(n)
    return tuple(out)


def phi(n: int) -> int:
    out=n
    for p in set(factors(n)):out-=out//p
    return out


def mobius(n: int) -> int:
    f=factors(n)
    return (-1)**len(f) if len(set(f))==len(f) else 0


@lru_cache(None)
def divisors(n: int) -> tuple[int,...]:
    return tuple(d for d in range(1,n+1) if n%d==0)


def squarefree(ps: list[int]) -> list[int]:
    return sorted(prod(p for p,b in zip(ps,bs) if b) for bs in product((0,1),repeat=len(ps)))


def coefficients(raw: dict[tuple[int,...],Q]) -> dict[tuple[int,...],Q]:
    # raw already includes B^(-m)/G_r. Retain shared-prime raw states before transforming.
    out=defaultdict(Q)
    for r,v in raw.items():
        weight=v/prod(phi(a) for a in r)
        for d in product(*(divisors(a) for a in r)):
            out[d]+=weight*prod(mobius(a)*a for a in d)
    return dict(out)


def arrays(cfg: dict, adaptive: bool) -> tuple[dict,dict,list]:
    sf=squarefree(cfg['primes']);B=Q(cfg['B']);T=cfg['root_max']*cfg['fixed_Z']
    roots={(r,s):Q((3*r+5*s)%11-5,7) for r in sf for s in sf if gcd(r,s)==1 and r*s<=cfg['root_max']}
    raw={};rows=[]
    for r,u in sorted(roots.items()):
        Z=T//prod(r) if adaptive else cfg['fixed_Z']
        pairs=[(a,b) for a in sf for b in sf if gcd(a,b)==1 and a*b<=Z]
        G=sum((Q(1,phi(a)*phi(b)) for a,b in pairs),Q(0))
        need(G>0,'empty auxiliary fibre')
        for a,b in pairs:raw[(a,*r,b)]=u/(B**2*G)
        rows.append({'root':r,'u':u,'Z':Z,'capacity':G,'pair_count':len(pairs)})
    return roots,raw,rows


@lru_cache(None)
def crt(system: tuple[tuple[int,int],...]) -> tuple[int,int] | None:
    a,q=0,1
    for b,r in system:
        g=gcd(q,r)
        if (b-a)%g:return None
        v=r//g;t=0 if v==1 else (((b-a)//g)*pow(q//g,-1,v))%v
        a=(a+q*t)%(q*v);q*=v
    return a,q


def crt_stats(co: dict,cfg: dict) -> dict:
    terms=sorted(co.items());mean=total=Q(0);compatible=0
    for i,(d,cd) in enumerate(terms):
        for j in range(i+1):
            e,ce=terms[j];mult=1 if i==j else 2
            sol=crt(((cfg['residue'],cfg['W']),)+tuple((-h,lcm(a,b)) for h,a,b in zip(cfg['shifts'],d,e)))
            if sol is None:continue
            a,q=sol;compatible+=mult;N=cfg['start'];L=cfg['length']
            count=(N+L-1-a)//q-(N-1-a)//q
            mean+=mult*cd*ce*Q(cfg['W'],q);total+=mult*cd*ce*count
    tv=sum(map(abs,co.values()),Q(0))
    need(abs(total-Q(cfg['length'],cfg['W'])*mean)<=tv**2,'CRT error')
    return {'coefficient_count':len(co),'ordered_pairs':len(co)**2,'compatible_pairs':compatible,
            'mean':mean,'interval_sum':total,'TV_squared':tv**2}


def independent_mean(raw: dict) -> Q:
    return sum((v*v/prod(phi(t) for t in r) for r,v in raw.items()),Q(0))


def tensor_bound(raw: dict,ps: list[int],m: int=2) -> Q:
    dprod=big=Q(1)
    for p in ps:
        q=Q(1,p-1);d=(1+m*q)*(1+2*q)
        delta=(m*m+17*m+2)*q*q+(10*m*m-12*m)*q**3+(2*m*m-4*m)*q**4
        dprod*=d;big*=d+delta
    return max(map(abs,raw.values()))**2*(big-dprod)


def soft(data: list,theta: Q,rho: Q,derivative: bool=False) -> Q:
    need(0<theta<1,'theta outside open interval')
    if derivative:
        return sum((-w*rho*k*(rho-k*c)/(rho*theta+k*c*(1-theta))**2 for w,c,k in data),Q(0))
    return sum((w*rho*k/(rho*theta+k*c*(1-theta)) for w,c,k in data),Q(0))


def optimum(data: list,rho: Q) -> dict:
    lo,hi=Q(1,1024),Q(1023,1024)
    f=lambda t:soft(data,t,rho);df=lambda t:soft(data,t,rho,True)
    need(df(lo)<0<df(hi),'no interior minimum bracket')
    for _ in range(36):
        t=(lo+hi)/2
        if df(t)<0:lo=t
        else:hi=t
    lower=max(f(lo)+df(lo)*(hi-lo),f(hi)+df(hi)*(lo-hi));upper=f((lo+hi)/2);D=10**12
    floor=lambda x:x.numerator//x.denominator
    return {'theta_lower':lo,'theta_upper':hi,'minimum_lower':Q(floor(D*lower),D),
            'minimum_upper':Q(-floor(-D*upper),D)}


def helper(cfg: dict,rows: list,rho: Q) -> dict:
    B=Q(cfg['B']);sf=squarefree(cfg['primes']);data=[];fixed=[];G0=min(r['capacity'] for r in rows)
    for row in rows:
        r=row['root'];A=row['u']
        allowed=[t for t in sf if t<=cfg['helper_root_max'] and t*prod(r)<=cfg['helper_total_max'] and gcd(t,prod(r))==1]
        c=sum((Q(1,B*phi(t)) for t in allowed),Q(0));w=A*A/(B**2*prod(phi(t) for t in r))
        data.append((w,c,B*B/row['capacity']));fixed.append((w,c,B*B/G0))
    return {'data':data,'fixed_data':fixed,'adaptive_optimum':optimum(data,rho),'fixed_optimum':optimum(fixed,rho),
            'scope':'abstract finite quadratic target with B^2/G_r costs, not an asymptotic physical value'}


def parameters(rho: Q,gamma: Q,ell: Q) -> dict:
    need(0<rho and 0<gamma<ell<Q(1,2),'require 0<gamma<ell<1/2 and rho>0')
    S=gamma/rho;zmin=ell-gamma;kmax=2*rho*rho/zmin**2
    samples=[]
    for j in range(5):
        t=gamma*j/4;s=t/rho;k=2*rho*rho/(ell-t)**2
        samples.append({'root_exponent':t,'retained_mass':s,'penalty':k,
                        'relative_penalty':k/kmax,'trace_mass_bound':(S-s)**2/2})
    return {'rho':rho,'gamma':gamma,'ell':ell,'S':S,'z_min':zmin,'power_slack':1-2*ell,
            'fixed_penalty':kmax,'samples':samples,
            'restoration_theta_times_new_bound':gamma*gamma/ell**2,
            'restoration_theta_times_old_bound':gamma*gamma/zmin**2,
            'bound_ratio':zmin*zmin/ell**2,'worst_root_penalty_unchanged':True}


def build(inp: dict) -> tuple[dict,dict]:
    need(inp==INPUTS,'input identity')
    cfg=inp['finite'];rho=Q(inp['rho']);rows={};records={};raws={}
    for mode in ('fixed','adaptive'):
        _,raw,rr=arrays(cfg,mode=='adaptive');raws[mode]=raw;rows[mode]=rr
        rec=crt_stats(coefficients(raw),cfg);rec['raw_count']=len(raw)
        rec['independent_mean']=independent_mean(raw);rec['tensor_error_bound']=tensor_bound(raw,cfg['primes'])
        need(abs(rec['mean']-rec['independent_mean'])<=rec['tensor_error_bound'],'signed tensor error')
        records[mode]=rec
    need(records['adaptive']['independent_mean']<=records['fixed']['independent_mean'],'comparison energy')
    pars=parameters(rho,Q(inp['gamma']),Q(inp['budget']));hc=helper(cfg,rows['adaptive'],rho)
    cert={'schema':'twin-adaptive-certificate/v1','parameters':pars,'capacity_rows':rows['adaptive'],
          'finite':records,'helper':hc}
    result={'schema':'twin-adaptive-results/v1','status':'proof_candidate_and_exact_check',
            'adaptive_constant':'2*rho^2/(ell-log_x(prod r))^2','restoration_bound_ratio':pars['bound_ratio'],
            'finite_adaptive_sum':records['adaptive']['interval_sum'],'finite_fixed_sum':records['fixed']['interval_sum'],
            'finite_adaptive_helper':hc['adaptive_optimum'],'finite_fixed_helper':hc['fixed_optimum'],
            'worst_root_constant_improved':False,'actual_restored_trace_evaluated':False,
            'helper_prime_contract_verified':False,'independently_verified':False,'new_prime_gap_bound':False,
            'cannot_imply':['new prime-gap theorem or twin primes','strict improvement for every residual',
                            'finite CRT monotonicity','actual restoration error or detection positivity']}
    return encode(cert),encode(result)


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output-dir',type=Path,required=True)
    args=ap.parse_args();cert,res=build(INPUTS);args.output_dir.mkdir(parents=True,exist_ok=True)
    for name,value in [('inputs.json',INPUTS),('certificates.json',cert),('results.json',res)]:
        (args.output_dir/name).write_text(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'finite':cert['finite'],'restoration_bound_ratio':res['restoration_bound_ratio']},sort_keys=True))
    return 0


if __name__=='__main__':raise SystemExit(main())
