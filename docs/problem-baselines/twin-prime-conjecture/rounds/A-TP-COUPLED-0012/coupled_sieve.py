#!/usr/bin/env python3
"""Exact coupled endpoint sieve and restoration-bridge certificates (stdlib only)."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from fractions import Fraction as Q
from functools import lru_cache
from itertools import product
from math import gcd, lcm, prod
from pathlib import Path
import json

INPUTS = {"schema":"twin-coupled-input/v1","attempt":"A-TP-COUPLED-0012",
          "m":38,"rho":"2624989/10000000","gamma":"2742997/10000000",
          "outer_radius":"2742997/2624989","z_choices":["1/5","11/50","9/40","141/625"],
          "finite":{"primes":[5,7,11],"shifts":[0,2,6,8],"B":"7/3","W":6,"residue":5,
                    "start":1001,"length":6000,"Z":77,"Za_old":7,"Zb_old":11,
                    "helper_new_root_cutoff":7,"helper_product_cutoff":35}}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def encode(value):
    if isinstance(value, Q): return str(value)
    if isinstance(value, dict): return {str(k):encode(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)): return [encode(x) for x in value]
    return value


def states(m: int) -> list[int]:
    require(type(m) is int and m >= 0,"nonnegative integral dimension required")
    return [e | r for e in (0,1,2) for r in [0]+[1 << (j+2) for j in range(m)]]


def kernel(p: int,s: int,t: int) -> Q:
    return Q(1-(s|t).bit_count()+(p-1)*(s&t).bit_count(),(p-1)**(s.bit_count()+t.bit_count()))


def census(m: int) -> list[list[int]]:
    counts=Counter((s.bit_count(),t.bit_count(),(s|t).bit_count(),(s&t).bit_count(),int(s==t))
                   for s in states(m) for t in states(m))
    return [list(key)+[counts[key]] for key in sorted(counts)]


def delta_coefficients(m: int) -> list[int]:
    return [0,0,m*m+17*m+2,10*m*m-12*m,2*m*m-4*m]


def local_record(m: int,p: int) -> dict:
    require(p>=max(5,m+2),"distinct residues and p>=5 required")
    delta=Q(0);d=Q(0)
    for s,t,v,c,e,n in census(m):
        kp=Q(1-v+(p-1)*c,(p-1)**(s+t));dp=Q(1,(p-1)**s) if e else Q(0)
        delta+=n*abs(kp-dp);d+=n*dp
    q=Q(1,p-1)
    require(delta==sum(a*q**i for i,a in enumerate(delta_coefficients(m))),"local L1 polynomial mismatch")
    require(d==(1+m*q)*(1+2*q),"diagonal mass mismatch")
    return {"m":m,"p":p,"delta":delta,"D_mass":d}


def squarefree(ps: list[int]) -> list[int]:
    return sorted(prod(p for p,b in zip(ps,bs) if b) for bs in product((0,1),repeat=len(ps)))


@lru_cache(None)
def phi(n: int) -> int:
    out=n;d=2
    while d*d<=n:
        if n%d==0:
            out-=out//d
            while n%d==0:n//=d
        d+=1
    return out-out//n if n>1 else out


@lru_cache(None)
def mobius(n: int) -> int:
    val=1;d=2
    while d*d<=n:
        if n%d==0:
            n//=d;val=-val
            if n%d==0:return 0
        d+=1
    return -val if n>1 else val


@lru_cache(None)
def divisors(n: int) -> tuple[int,...]:
    return tuple(d for d in range(1,n+1) if n%d==0)


def roots(ps: list[int],m: int) -> dict[tuple[int,...],Q]:
    arr={}
    for assignment in product(range(m+1),repeat=len(ps)):
        r=tuple(prod(p for p,i in zip(ps,assignment) if i==j+1) for j in range(m))
        arr[r]=Q((sum((2*j+3)*v for j,v in enumerate(r))%11)-5,7)
    return arr


def transform(arr: dict[tuple[int,...],Q],B: Q) -> dict[tuple[int,...],Q]:
    m=len(next(iter(arr)));out=defaultdict(Q)
    for r,u in arr.items():
        w=u/B**m/prod(phi(v) for v in r)
        for d in product(*(divisors(v) for v in r)):
            out[d]+=w*prod(mobius(v)*v for v in d)
    return dict(out)


def coupled(ps: list[int],Z: int) -> tuple[Q,dict[tuple[int,int],Q],list[tuple[int,int]]]:
    sf=squarefree(ps)
    allowed=[(a,b) for a in sf for b in sf if a*b<=Z and gcd(a,b)==1]
    G=sum((Q(1,phi(a)*phi(b)) for a,b in allowed),Q(0))
    lam=transform({r:1/G for r in allowed},Q(1))
    require(lam[(1,1)]==1,"coupled coefficient at identity")
    require(all(abs(v)<=Q(prod(d),phi(prod(d))) for d,v in lam.items()),"auxiliary coefficient bound")
    return G,lam,allowed


def one_aux(ps: list[int],Z: int) -> tuple[Q,dict[int,Q]]:
    sf=[n for n in squarefree(ps) if n<=Z];G=sum((Q(1,phi(n)) for n in sf),Q(0))
    lam=transform({(n,):1/G for n in sf},Q(1))
    return G,{d[0]:v for d,v in lam.items()}


@lru_cache(None)
def crt(system: tuple[tuple[int,int],...]) -> tuple[int,int] | None:
    a,q=0,1
    for b,r in system:
        g=gcd(q,r)
        if (b-a)%g:return None
        v=r//g
        t=0 if v==1 else (((b-a)//g)*pow(q//g,-1,v))%v
        a=(a+q*t)%(q*v);q*=v
    return a,q


def count(a: int,q: int,N: int,L: int) -> int:
    return (N+L-1-a)//q-(N-1-a)//q


def mean_and_sum(co: dict[tuple[int,...],Q],cfg: dict) -> dict:
    mean=Q(0);exact=Q(0);compatible=0
    for d,cd in co.items():
        for e,ce in co.items():
            sol=crt(((cfg['residue'],cfg['W']),)+tuple((-h,lcm(a,b)) for h,a,b in zip(cfg['shifts'],d,e)))
            if sol is not None:
                a,q=sol;compatible+=1
                mean+=cd*ce*Q(cfg['W'],q)
                exact+=cd*ce*count(a,q,cfg['start'],cfg['length'])
    tv=sum(map(abs,co.values()),Q(0))
    require(abs(exact-Q(cfg['length'],cfg['W'])*mean)<=tv**2,"CRT total-variation bound")
    return {"coefficient_count":len(co),"ordered_pairs":len(co)**2,"compatible_pairs":compatible,
            "CRT_mean":mean,"interval_sum":exact,"counting_error_bound":tv**2}


def finite_certificate(cfg: dict) -> dict:
    ps=cfg['primes'];B=Q(cfg['B']);arr=roots(ps,2);lam=transform(arr,B)
    G,aux,allowed=coupled(ps,cfg['Z'])
    co={(a,*d,b):v*w for d,v in lam.items() for (a,b),w in aux.items()}
    exact=mean_and_sum(co,cfg)
    diag=B**-4*sum((v*v/prod(phi(a) for a in r) for r,v in arr.items()),Q(0))/G
    dp=Q(1);big=Q(1)
    for p in ps:
        rec=local_record(2,p);dp*=rec['D_mass'];big*=rec['D_mass']+rec['delta']
    tensor=(max(map(abs,arr.values()))/B**2/G)**2*(big-dp)
    require(abs(exact['CRT_mean']-diag)<=tensor,"signed tensor comparison")
    Ga,aa=one_aux(ps,cfg['Za_old']);Gb,bb=one_aux(ps,cfg['Zb_old'])
    old={(a,*d,b):v*x*y for d,v in lam.items() for a,x in aa.items() for b,y in bb.items()}
    old_stats=mean_and_sum(old,cfg)
    independent_capacity=sum((Q(1,phi(a)*phi(b)) for a in squarefree(ps) for b in squarefree(ps) if a*b<=cfg['Z']),Q(0))
    return {"auxiliary_pairs":allowed,"G2":G,"unrestricted_triangle_capacity":independent_capacity,
            "deleted_collision_capacity":independent_capacity-G,
            "coefficient_at_identity":aux[(1,1)],"independent_mean":diag,"tensor_error_bound":tensor,
            "coupled":exact,"rectangular_same_total_cutoff":old_stats,"rectangular_capacity":Ga*Gb,
            "root_array":[[r,v] for r,v in sorted(arr.items())],
            "finite_comparison_is_not_uniform_in_all_arrays":True}


def helper_data(cfg: dict) -> list[tuple[Q,Q]]:
    B=Q(cfg['B']);data=[]
    for r,A in sorted(roots(cfg['primes'],2).items()):
        allowed=[t for t in squarefree(cfg['primes']) if t<=cfg['helper_new_root_cutoff']
                 and t*prod(r)<=cfg['helper_product_cutoff'] and gcd(t,prod(r))==1]
        cap=sum((Q(1,B*phi(t)) for t in allowed),Q(0))
        data.append((A*A/(B**2*prod(phi(t) for t in r)),cap))
    return data


def soft(data: list[tuple[Q,Q]],rho: Q,kappa: Q,t: Q) -> Q:
    require(0<t<1,"theta outside open interval")
    return sum((w*rho*kappa/(rho*t+kappa*c*(1-t)) for w,c in data),Q(0))


def derivative(data: list[tuple[Q,Q]],rho: Q,kappa: Q,t: Q) -> Q:
    return sum((-w*rho*kappa*(rho-kappa*c)/(rho*t+kappa*c*(1-t))**2 for w,c in data),Q(0))


def optimize(data: list[tuple[Q,Q]],rho: Q,kappa: Q) -> dict:
    lo,hi=Q(1,1024),Q(1023,1024)
    require(derivative(data,rho,kappa,lo)<0<derivative(data,rho,kappa,hi),"no certified interior bracket")
    for _ in range(40):
        mid=(lo+hi)/2
        if derivative(data,rho,kappa,mid)<0:lo=mid
        else:hi=mid
    f=lambda t:soft(data,rho,kappa,t);df=lambda t:derivative(data,rho,kappa,t)
    lower=max(f(lo)+df(lo)*(hi-lo),f(hi)+df(hi)*(lo-hi));upper=f((lo+hi)/2);scale=10**12
    floor=lambda x:x.numerator//x.denominator
    return {"theta_lower":lo,"theta_upper":hi,"derivative_lower":df(lo),"derivative_upper":df(hi),
            "minimum_lower":Q(floor(lower*scale),scale),"minimum_upper":Q(-floor(-upper*scale),scale)}


def exponent_certificate(rho: Q,gamma: Q,choices: list[str]) -> dict:
    require(rho>0 and 0<gamma<Q(1,2),"invalid exponent parameters")
    rows=[]
    for text in choices:
        z=Q(text);eta=2*gamma+2*z
        require(z>0 and eta<1,"strict counting budget violated")
        kappa=2*rho*rho/z**2
        rows.append({"joint_z":z,"counting_exponent":eta,"power_slack":1-eta,
                     "coupled_penalty":kappa,"old_equal_rectangle_penalty":2*kappa})
    star=Q(1,2)-gamma
    return {"admissible":rows,"z_supremum":star,"penalty_infimum":2*rho*rho/star**2,
            "infimum_attained":False,"same_total_budget_factor":Q(1,2)}


def build(inp: dict) -> tuple[dict,dict]:
    require(inp==INPUTS,"input identity mismatch")
    m=inp['m'];rho=Q(inp['rho']);gamma=Q(inp['gamma']);S=Q(inp['outer_radius'])
    data=helper_data(inp['finite']);old=rho*rho/Q(1,10)**2;new=old/2
    helper={"finite_data":data,"old_kappa":old,"new_kappa":new,
            "old_optimum":optimize(data,rho,old),"new_optimum":optimize(data,rho,new),
            "scope":"same finite helper target as T11, not actual restored trial or finite prime sum"}
    exp=exponent_certificate(rho,gamma,inp['z_choices'])
    stability=[{"theta":t,"kappa":new,"outer_radius":S,"trace_operator_bound_squared":S*S/2,
                "weighted_error_multiplier":new*S*S/(2*t)} for t in (Q(1,4),Q(1,2),Q(3,4))]
    cert={"schema":"twin-coupled-certificate/v1","kernel":{"census":census(m),"delta_coefficients":delta_coefficients(m),
          "records":[local_record(m,p) for p in (41,43,47)],"uniform_L1_constant":5759},
          "finite":finite_certificate(inp['finite']),"exponents":exp,"helper":helper,"stability":stability}
    result={"schema":"twin-coupled-results/v1","status":"solver_proof_candidate_and_exact_check",
            "states":len(states(m)),"ordered_state_pairs":len(states(m))**2,"delta_coefficients":delta_coefficients(m),
            "penalty_at_9_over_40":exp['admissible'][2]['coupled_penalty'],"factor_at_equal_support_budget":Q(1,2),
            "penalty_infimum_not_attained":exp['penalty_infimum'],
            "old_finite_helper_optimum":[helper['old_optimum']['minimum_lower'],helper['old_optimum']['minimum_upper']],
            "new_finite_helper_optimum":[helper['new_optimum']['minimum_lower'],helper['new_optimum']['minimum_upper']],
            "actual_restored_trace_evaluated":False,"restoration_error_numerically_supplied":False,
            "helper_prime_contract_verified":False,"independently_verified":False,"new_prime_gap_bound":False,
            "cannot_imply":["a new prime-gap bound or twin primes","factor-two improvement of every finite interval bound",
                            "factor-two improvement of the entire soft-helper objective","global optimality of the sieve",
                            "actual restored trial meets the positive detection margin"]}
    return encode(cert),encode(result)


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output-dir',required=True,type=Path)
    args=ap.parse_args();cert,res=build(INPUTS);args.output_dir.mkdir(parents=True,exist_ok=True)
    for name,value in [('inputs.json',INPUTS),('certificates.json',cert),('results.json',res)]:
        (args.output_dir/name).write_text(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'states':res['states'],'ordered_state_pairs':res['ordered_state_pairs'],
                      'penalty':res['penalty_at_9_over_40'],'new_helper':res['new_finite_helper_optimum']},sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
