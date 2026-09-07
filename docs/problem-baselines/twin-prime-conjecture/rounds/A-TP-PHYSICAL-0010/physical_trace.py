#!/usr/bin/env python3
"""Exact physical-trace witness and finite diagonal/CRT arithmetic. Stdlib only."""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
from fractions import Fraction as Q
from math import gcd, prod
from pathlib import Path


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def canonical(x: object) -> bytes:
    return json.dumps(x, sort_keys=True, separators=(',', ':')).encode('utf-8')


def profile(t: Q) -> Q:
    return Q(21,200)/(1+t/100)+Q(179,200)/(1+Q(907,5)*t)


def trial(data: dict, indices: list[int]) -> tuple[Q,Q]:
    h=Q(data['mesh']); ts=[(Q(j)+Q(1,2))*h for j in indices]
    z=sum(ts)-Q(9,10); ps={e:sum(t**e for t in ts) for e in range(2,7)}
    polynomial=Q(0)
    for row,sig in zip(data['coefficients'],data['signatures']):
        radial=Q(0)
        for a in reversed(row):
            radial=radial*z+a
        polynomial+=radial*prod(ps[e] for e in sig)
    polynomial/=data['coefficient_denominator']
    return polynomial,polynomial*prod(profile(t) for t in ts)


def witness(data: dict) -> dict:
    h=Q(data['mesh']); js=data['retained_cell_indices']; r=sum(js)
    need(len(js)==38 and r==98263,'retained grid identity')
    need(data['outer_bands'][-1]==[98263,46580],'last outer shell')
    need(max(js)+1<46580,'all fragment caps automatic from total mass')
    p,v=trial(data,[0]+js+[0]); need(p!=0,'nonzero exact polynomial')
    lower=Q(v.numerator*10**30//v.denominator,10**30)
    return {'retained_radius':r,'endpoint_cells':[[0,0]],'midpoint_radius':98283,
            'polynomial':str(p),'trial_value':str(v),'trial_bracket':[str(lower),str(lower+Q(1,10**30))],
            'double_trace':str(h*h*v),'box_measure_power':38,
            'trace_error_lower_bound':{'expression':'mesh^42 * trial_value^2','strictly_positive':True},
            'base_fibre_empty':r>data['base_bands'][-1][0],
            'enlarged_fibre_empty':r>data['enlarged_bands'][-1][0],
            'restored_profile_obstruction_proved':False}


def tuples(m: int, primes: list[int]) -> list[tuple[int,...]]:
    out=[]
    for owners in itertools.product(range(m+1),repeat=len(primes)):
        row=[1]*m
        for p,i in zip(primes,owners):
            if i<m: row[i]*=p
        out.append(tuple(row))
    return sorted(out)


def phi(n: int) -> int:
    return sum(gcd(i,n)==1 for i in range(1,n+1))


def mu(n: int) -> int:
    ans=1; p=2
    while p*p<=n:
        if n%p==0:
            n//=p; ans=-ans
            if n%p==0:return 0
        p+=1
    return -ans if n>1 else ans


def marginal(y: dict, i: int, B: Q) -> dict:
    out={}
    for r,v in y.items():
        key=r[:i]+r[i+1:]
        out[key]=out.get(key,Q(0))+v/(B*phi(r[i]))
    return out


def coefficients(y: dict, B: Q, primes: list[int]) -> dict:
    m=len(next(iter(y))); out={}
    for d in tuples(m,primes):
        s=sum((v/Q(prod(phi(t) for t in r)) for r,v in y.items()
               if all(rj%dj==0 for rj,dj in zip(r,d))),Q(0))
        out[d]=s*prod(mu(t)*t for t in d)/B**m
    return out


def sieve_value(c: dict, shifts: list[int], n: int) -> Q:
    return sum((v for d,v in c.items() if all((n+s)%a==0 for s,a in zip(shifts,d))),Q(0))


def merge_congruences(pairs: list[tuple[int,int]]) -> tuple[int,int] | None:
    a,m=0,1
    for b,n in pairs:
        g=gcd(m,n)
        if (b-a)%g:return None
        nn=n//g
        t=0 if nn==1 else ((b-a)//g*pow(m//g,-1,nn))%nn
        a+=m*t; m*=nn; a%=m
    return a,m


def crt_square(c: dict, shifts: list[int], N: int, length: int, W: int, b: int) -> dict:
    entries=[(d,v) for d,v in c.items() if v]; exact=Q(0); main=Q(0); valid=0
    for d,v in entries:
        for e,w in entries:
            congr=[(b,W)]+[(-s,a) for s,a in zip(shifts,d)]+[(-s,a) for s,a in zip(shifts,e)]
            merged=merge_congruences(congr)
            if merged is None:continue
            a,m=merged; valid+=1
            count=(N+length-1-a)//m-(N-1-a)//m
            exact+=v*w*count; main+=v*w*Q(length,m)
    error=sum(abs(v) for _,v in entries)**2
    return {'exact':exact,'main':main,'rounding_error':error,'upper':main+error,
            'coefficient_count':len(entries),'compatible_ordered_pairs':valid}


def toy(data: dict) -> tuple[dict,dict]:
    t=data['toy']; P=t['primes']; B=Q(t['B']); shifts=t['shifts']
    y={r:Q((sum((i+2)*v for i,v in enumerate(r))+3*prod(r))%13-6,7) for r in tuples(4,P)}
    g=marginal(y,0,B); target=marginal(g,2,B)
    z={r:(v if prod(r)<=77 else Q(0)) for r,v in g.items()}
    tz=marginal(z,2,B); residual={r:v-tz[r] for r,v in target.items()}
    cy=coefficients(y,B,P); cz=coefficients(z,B,P); cr=coefficients(residual,B,P)
    # Two elementary Selberg-type squares; alpha_1=1 and alpha_p=-1.
    alpha={1:Q(1),7:Q(-1)}; beta={1:Q(1),11:Q(-1)}
    combined={(d,)+r+(e,):v*a*b for r,v in cr.items() for d,a in alpha.items() for e,b in beta.items()}
    crt=crt_square(combined,shifts,t['N'],t['length'],t['W'],t['residue'])
    return {'y':y,'g':g,'z':z,'target':target,'residual':residual,'cy':cy,'cz':cz,'cr':cr,'combined':combined},crt


def optimal_lift(target: dict, B: Q, primes: list[int], Z: int) -> tuple[dict,dict,Q]:
    """Minimum diagonal norm with both endpoint roots <= Z; exact finite capacities."""
    m=len(next(iter(target)))+2; allowed=[]; G={r:Q(0) for r in target}
    for q in tuples(m,primes):
        r=q[1:-1]
        if q[0]<=Z and q[-1]<=Z:
            mass=Q(1,phi(q[0])*phi(q[-1])); G[r]+=mass; allowed.append(q)
    lift={q:B*B*target[q[1:-1]]/G[q[1:-1]] for q in allowed}
    energy=sum((target[r]**2/(prod(phi(a) for a in r)*G[r]) for r in target),Q(0))*B**(4-m)
    return lift,G,energy


def build(data: dict) -> tuple[dict,dict]:
    w=witness(data); arrays,crt=toy(data)
    t=data['toy']; lift,G,energy=optimal_lift(arrays['residual'],Q(t['B']),t['primes'],13)
    cert={'schema':'physical-trace-certificate/v1','input_sha256':hashlib.sha256(canonical(data)).hexdigest(),
          'witness':w,'optimal_lift':{'Z':13,'capacity_min':str(min(G.values())),'capacity_max':str(max(G.values())),
          'diagonal_norm':str(energy),'nonzero_roots':sum(v!=0 for v in lift.values())},'finite_crt':{k:str(v) if isinstance(v,Q) else v for k,v in crt.items()}}
    result={'schema':'physical-trace-result/v1','status':'proof_candidate_and_exact_check',
            'actual_trial_nonzero_trace':True,'exact_base_or_enlarged_helper_exists':False,
            'diagonal_trace_is_point_evaluation':False,'residual_bound_asymptotically_small':False,
            'restored_profile_obstruction_proved':False,'independently_verified':False,
            'new_prime_gap_bound':False,'twin_prime_conjecture_proved':False,
            'cannot_imply':['restored P_O H has the same obstruction','a quantitatively large trace error',
                           'asymptotic residual smallness','a new prime-gap theorem','twin primes']}
    return cert,result


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inputs',type=Path,default=Path(__file__).with_name('inputs.json'))
    ap.add_argument('--output-dir',type=Path,required=True)
    a=ap.parse_args(); data=json.loads(a.inputs.read_text()); cert,result=build(data)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    for name,obj in [('certificate.json',cert),('results.json',result)]:
        (a.output_dir/name).write_text(json.dumps(obj,indent=2)+'\n')
    print(json.dumps({'ok':True,'trial_bracket':cert['witness']['trial_bracket'],
                      'nonzero_double_trace':True,'finite_crt':cert['finite_crt']},sort_keys=True))


if __name__=='__main__':
    main()
