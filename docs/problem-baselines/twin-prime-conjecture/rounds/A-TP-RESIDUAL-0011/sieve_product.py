#!/usr/bin/env python3
"""Exact two-auxiliary Selberg product certificates; no asymptotic acceptance."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from fractions import Fraction as Q
from functools import lru_cache
from itertools import product
from math import gcd, lcm, prod
from pathlib import Path
import json

INPUTS = {"schema":"twin-residual-input/v1","attempt":"A-TP-RESIDUAL-0011",
          "retained_dimension":38,"rho":"2624989/10000000","gamma":"2742997/10000000",
          "z_choices":["1/10","11/100","9/80","141/1250"],
          "finite":{"primes":[5,7,11],"shifts":[0,2,6,8],"B":"7/3","W":6,"residue":5,
                    "start":1001,"length":6000,"Za":7,"Zb":11,"helper_product_cutoff":35}}


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def encode(x):
    if isinstance(x,Q):
        return str(x)
    if isinstance(x,dict):
        return {str(k):encode(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):
        return [encode(v) for v in x]
    return x


def states(m: int) -> list[int]:
    need(type(m) is int and m >= 0,"invalid retained dimension")
    return [e | r for e in range(4) for r in [0]+[1 << (j+2) for j in range(m)]]


def census(m: int) -> list[list[int]]:
    c=Counter((s.bit_count(),t.bit_count(),(s|t).bit_count(),(s&t).bit_count(),int(s==t))
              for s in states(m) for t in states(m))
    return [list(key)+[c[key]] for key in sorted(c)]


def kernel(p: int, s: int, t: int) -> Q:
    n=s.bit_count()+t.bit_count()
    return Q(1-(s|t).bit_count()+(p-1)*(s&t).bit_count(),(p-1)**n)


def delta_coefficients(m: int) -> list[int]:
    return [0,0,m*m+17*m+9,10*m*m+7*m-6,12*m*m-22*m+1,-10*m*m-5*m,-3*m*m+5*m]


def local_record(m: int,p: int) -> dict:
    need(p>=max(5,m+2),"local prime must allow distinct shift residues")
    delta=Q(0); diags=Q(0)
    for s,t,v,c,e,n in census(m):
        kv=Q(1-v+(p-1)*c,(p-1)**(s+t));dv=Q(1,(p-1)**s) if e else Q(0)
        delta+=n*abs(kv-dv);diags+=n*dv
    x=Q(1,p-1)
    need(delta==sum(a*x**j for j,a in enumerate(delta_coefficients(m))),"delta polynomial")
    need(diags==(1+m*x)*(1+x)**2,"independent mass")
    return {"m":m,"p":p,"states":4*(m+1),"delta":delta,"independent_mass":diags}


def squarefree(ps: list[int]) -> list[int]:
    return sorted(prod(p for p,b in zip(ps,bits) if b) for bits in product((0,1),repeat=len(ps)))


def phi(n: int) -> int:
    out=n;d=2
    while d*d<=n:
        if n%d==0:
            out-=out//d
            while n%d==0:n//=d
        d+=1
    if n>1:out-=out//n
    return out


def mobius(n: int) -> int:
    val=1;d=2
    while d*d<=n:
        if n%d==0:
            n//=d;val=-val
            if n%d==0:return 0
        d+=1
    return -val if n>1 else val


def divisors(n: int) -> list[int]:
    return [d for d in range(1,n+1) if n%d==0]


def root_array(ps: list[int],m: int) -> dict[tuple[int,...],Q]:
    arr={}
    for assignment in product(range(m+1),repeat=len(ps)):
        r=tuple(prod(p for p,i in zip(ps,assignment) if i==j+1) for j in range(m))
        arr[r]=Q((sum((2*j+3)*v for j,v in enumerate(r))%11)-5,7)
    return arr


def transform(arr: dict[tuple[int,...],Q],B: Q) -> dict[tuple[int,...],Q]:
    m=len(next(iter(arr)));out=defaultdict(Q)
    for r,u in arr.items():
        weight=u/B**m/prod(phi(v) for v in r)
        for d in product(*(divisors(v) for v in r)):
            out[d]+=weight*prod(mobius(v)*v for v in d)
    return dict(out)


def selberg(ps: list[int],Z: int) -> tuple[Q,dict[int,Q],list[int]]:
    roots=[a for a in squarefree(ps) if a<=Z]
    G=sum((Q(1,phi(a)) for a in roots),Q(0))
    coeff={d:Q(mobius(d)*d,G)*sum((Q(1,phi(a)) for a in roots if a%d==0),Q(0)) for d in roots}
    need(coeff[1]==1,"Selberg endpoint normalization")
    return G,coeff,roots


@lru_cache(None)
def crt(congruences: tuple[tuple[int,int],...]) -> tuple[int,int] | None:
    a,q=0,1
    for b,r in congruences:
        g=gcd(q,r)
        if (b-a)%g:return None
        v=r//g
        step=0 if v==1 else (((b-a)//g)*pow(q//g,-1,v))%v
        a=(a+q*step)%(q*v);q*=v
    return a,q


def count_interval(a: int,q: int,N: int,L: int) -> int:
    return (N+L-1-a)//q-(N-1-a)//q


def finite_certificate(cfg: dict) -> dict:
    ps=cfg["primes"];B=Q(cfg["B"]);W=cfg["W"];h=cfg["shifts"];N=cfg["start"];L=cfg["length"]
    arr=root_array(ps,2);lam=transform(arr,B)
    Ga,alpha,ar=selberg(ps,cfg["Za"]);Gb,beta,br=selberg(ps,cfg["Zb"])
    co={(a,*d,b):v*alpha[a]*beta[b] for d,v in lam.items() for a in alpha for b in beta}
    mean=Q(0);exact=Q(0);compatible=0
    for d,cd in co.items():
        for e,ce in co.items():
            sol=crt(((cfg["residue"],W),)+tuple((-hi,lcm(di,ei)) for hi,di,ei in zip(h,d,e)))
            if sol is not None:
                a,q=sol;compatible+=1
                mean+=cd*ce*Q(W,q)
                exact+=cd*ce*count_interval(a,q,N,L)
    tv=sum(map(abs,co.values()),Q(0));error=tv*tv
    diag=B**-4*sum((u*u/prod(phi(v) for v in r) for r,u in arr.items()),Q(0))/Ga/Gb
    dprod=Q(1);expanded=Q(1)
    for p in ps:
        rec=local_record(2,p);dprod*=rec["independent_mass"];expanded*=rec["independent_mass"]+rec["delta"]
    cmax=max(map(abs,arr.values()))/(B**2*Ga*Gb)
    tensor_bound=cmax*cmax*(expanded-dprod)
    need(abs(mean-diag)<=tensor_bound,"finite tensor error")
    need(abs(exact-Q(L,W)*mean)<=error,"finite CRT error")
    return {"root_count":len(arr),"coefficient_count":len(co),"ordered_coefficient_pairs":len(co)**2,
            "compatible_coefficient_pairs":compatible,"Ga":Ga,"Gb":Gb,"CRT_mean":mean,
            "independent_mean":diag,"kernel_error_bound":tensor_bound,"interval_sum":exact,
            "interval_main":Q(L,W)*mean,"CRT_error_bound":error,
            "roots":[[list(r),u] for r,u in sorted(arr.items())]}


def helper_certificate(cfg: dict,rho: Q,kappa: Q) -> dict:
    ps=cfg["primes"];B=Q(cfg["B"]);arr=root_array(ps,2);options=[t for t in squarefree(ps) if t<=cfg["Za"]]
    cases=[]
    for tau in (Q(1,4),Q(1),Q(4)):
        a=rho*(1+tau);b=kappa*(1+1/tau);rows=[];soft=Q(0);zero=Q(0);hard=Q(0)
        for r,A in sorted(arr.items()):
            allowed=[t for t in options if gcd(t,prod(r))==1 and t*prod(r)<=cfg["helper_product_cutoff"]]
            weights=[Q(1,B*phi(t)) for t in allowed];cap=sum(weights,Q(0));mu=Q(1,B**2*prod(phi(v) for v in r))
            value=b*A/(a+b*cap);residual=A-cap*value;cost=a*cap*value**2+b*residual**2
            need(cost==a*b*A*A/(a+b*cap),"soft minimum")
            soft+=mu*cost;zero+=mu*b*A*A;hard+=mu*(a*A*A/cap if cap else b*A*A)
            rows.append({"root":r,"target":A,"allowed":allowed,"capacity":cap,"helper_value":value,"residual":residual})
        need(soft<=zero and soft<=hard,"soft comparison")
        cases.append({"tau":tau,"a":a,"b":b,"soft_cost":soft,"zero_helper_cost":zero,
                      "hard_on_positive_fibres_cost":hard,"zero_capacity_fibres":sum(x["capacity"]==0 for x in rows),"fibres":rows})
    # theta=tau/(1+tau): the fully optimized envelope is convex in theta.
    data=[(Q(1,B**2*prod(phi(v) for v in row["root"]))*row["target"]**2,row["capacity"])
          for row in cases[0]["fibres"]]
    def objective(t):
        return sum((mu*rho*kappa/(rho*t+kappa*c*(1-t)) for mu,c in data),Q(0))
    def derivative(t):
        return sum((-mu*rho*kappa*(rho-kappa*c)/(rho*t+kappa*c*(1-t))**2 for mu,c in data),Q(0))
    lo,hi=Q(1,1024),Q(1023,1024)
    need(derivative(lo)<0<derivative(hi),"interior optimizer bracket")
    for _ in range(40):
        mid=(lo+hi)/2
        if derivative(mid)<0:lo=mid
        else:hi=mid
    lower=max(objective(lo)+derivative(lo)*(hi-lo),objective(hi)+derivative(hi)*(lo-hi))
    upper=objective((lo+hi)/2);scale=10**12
    floor=lambda q:q.numerator//q.denominator
    ceil=lambda q:-((-q.numerator)//q.denominator)
    optimum={"theta_lower":lo,"theta_upper":hi,"tau_lower":lo/(1-lo),"tau_upper":hi/(1-hi),
             "minimum_lower":Q(floor(lower*scale),scale),"minimum_upper":Q(ceil(upper*scale),scale),
             "proof":"positive second derivative plus rational tangent lower bound and midpoint upper bound",
             "scope":"all real finite helper coefficients and all positive Young parameters for this frozen example"}
    return {"cases":cases,"optimized":optimum,"scope":"finite diagonal-fibre example, not the restored 186 profile"}


def exponents(rho: Q,gamma: Q,choices: list[str]) -> dict:
    star=(1-2*gamma)/4
    need(star>0,"empty exponent budget")
    rows=[]
    for s in choices:
        z=Q(s);gap=1-2*gamma-4*z
        need(z>0 and gap>0,"strict exponent budget")
        rows.append({"z":z,"counting_exponent":1-gap,"power_slack":gap,"penalty":rho*rho/(z*z)})
    return {"equal_cutoff_supremum":star,"penalty_infimum_not_attained":rho*rho/star**2,
            "admissible":rows,"boundary_admissible":False}


def build(inp: dict) -> tuple[dict,dict]:
    need(inp==INPUTS,"input identity")
    rho=Q(inp["rho"]);gamma=Q(inp["gamma"]);m=inp["retained_dimension"]
    cert={"schema":"twin-residual-certificate/v1","kernel":{"census":census(m),
          "delta_polynomial":delta_coefficients(m),"records":[local_record(m,p) for p in (41,43,47)],
          "triple_diagonal_at43":kernel(43,7,7),"false_independent_triple":Q(1,42**3)},
          "finite":finite_certificate(inp["finite"]),"exponents":exponents(rho,gamma,inp["z_choices"]),
          "soft_helper":helper_certificate(inp["finite"],rho,rho*rho/Q(1,10)**2)}
    result={"schema":"twin-residual-results/v1","status":"solver_proof_candidate_and_exact_check",
            "local_states":len(states(m)),"local_ordered_entries":len(states(m))**2,
            "delta_polynomial":delta_coefficients(m),"exponent_summary":cert["exponents"],
            "asymptotic_candidate":"residual_pair/C_x <= rho^2/(z_a*z_b)*norm_u_squared + o(1)",
            "uniformity":"fixed dimension, support exponents, shifts and supremum bound; additive o(1)",
            "arithmetic_bridge_to_actual_restored_trial":False,"independently_verified":False,"new_prime_gap_bound":False,
            "cannot_imply":["actual restored residual is within the detection surplus","184 or twin-prime theorem",
                            "a uniform replacement of root-dependent capacity by product capacity","independent mathematical review"]}
    return encode(cert),encode(result)


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args();cert,res=build(INPUTS);args.output_dir.mkdir(parents=True,exist_ok=True)
    for name,data in (("inputs.json",INPUTS),("certificates.json",cert),("results.json",res)):
        (args.output_dir/name).write_text(json.dumps(data,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps({"ok":True,"local_states":156,"local_ordered_entries":24336,"finite_pairs":cert["finite"]["ordered_coefficient_pairs"]},sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
