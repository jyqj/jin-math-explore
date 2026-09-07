#!/usr/bin/env python3
"""Exact replay, separately coded value/count oracles and explicit evidence gates."""
from __future__ import annotations
import argparse
import copy
import hashlib
import itertools
import json
import sys
from fractions import Fraction as F
from math import gcd, prod, isqrt
from pathlib import Path
import physical_trace as p


def ensure(ok: bool, message: str) -> None:
    if not ok: raise ValueError(message)


def direct_trial(x: dict) -> F:
    h=F(x['mesh']); indices=[0]+x['retained_cell_indices']+[0]
    t=[h*F(2*j+1,2) for j in indices]; radial=sum(t)-F(9,10)
    value=F(0)
    for coeff,sig in zip(x['coefficients'],x['signatures']):
        angular=F(1)
        for degree in sig:
            angular*=sum(a**degree for a in t)
        value+=sum(F(c)*radial**i for i,c in enumerate(coeff))*angular
    for a in t:
        # Algebraically identical two-pole profile, evaluated as one fraction.
        value*= (F(21,200)*(1+F(907,5)*a)+F(179,200)*(1+a/100))/((1+a/100)*(1+F(907,5)*a))
    return value/x['coefficient_denominator']


def cap(bands: list, r: int) -> int:
    for upper,c in bands:
        if r<=upper:return c
    return 0


def geometry_oracle(data: dict) -> dict:
    tests=0
    thresholds=sorted({0,1,68225,68226}|{c+d for key in ('base_bands','enlarged_bands') for _,c in data[key] for d in (-1,0,1)})
    for r in range(98265):
        c0=cap(data['base_bands'],r); c1=cap(data['enlarged_bands'],r)
        ensure(c0<=c1,'base/enlarged projection not nested')
        for f in thresholds:
            a=c0>0 and f<=c0; b=c1>0 and f<=c1
            ensure(not a or b,'retained cap projection')
            tests+=1
    r=sum(data['retained_cell_indices'])
    ensure(cap(data['base_bands'],r)==cap(data['enlarged_bands'],r)==0,'zero capacity witness')
    pairs=[(i,j) for i in range(3) for j in range(3) if r+i+j<=98263]
    ensure(pairs==[(0,0)],'last shell double integral')
    ensure([(i,j) for i in range(2) for j in range(2) if 98262+i+j<=98263]==[(0,0),(0,1),(1,0)],'one-cell retreat control')
    return {'projection_tests':tests,'radius_values':98265}


def fibre_oracle() -> dict:
    count=0; zero=0
    weights=[F(1,3),F(2,5),F(7,6)]; values=[F(-3,2),F(4,3),F(-1,5)]
    for bits in itertools.product((0,1),repeat=3):
        M=sum(w*b for w,b in zip(weights,bits)); A=sum(w*v*b for w,v,b in zip(weights,values,bits))
        if not M:
            ensure(A==0,'empty actual fibre'); zero+=1; continue
        energy=sum(w*v*v*b for w,v,b in zip(weights,values,bits))
        residual=sum(w*(v-A/M)**2*b for w,v,b in zip(weights,values,bits))
        ensure(energy-A*A/M==residual and residual>=0,'capacity projection')
        for target in map(F,(-3,0,2)):
            helper=[target/M if b else F(0) for b in bits]
            ensure(sum(w*v for w,v in zip(weights,helper))==target,'trace recovery')
            ensure(sum(w*v*v for w,v in zip(weights,helper))==target*target/M,'minimum energy')
            count+=1
    return {'fibre_recoveries':count,'zero_capacity_cases':zero}


def isprime(n: int) -> bool:
    return n>=2 and all(n%d for d in range(2,isqrt(n)+1))


def diagonal_oracle(data: dict) -> dict:
    arrays,crt=p.toy(data); t=data['toy']; B=F(t['B']); P=t['primes']; checks=0
    y=arrays['y']; cy=arrays['cy']; target=arrays['target']
    opposite=p.marginal(p.marginal(y,3,B),0,B)
    ensure(opposite==target,'two erasures commute')
    ct=p.coefficients(target,B,P)
    for r,v in y.items():
        inv=B**4*prod(p.mu(a)*p.phi(a) for a in r)*sum((c/F(prod(d)) for d,c in cy.items() if all(b%a==0 for a,b in zip(r,d))),F(0))
        ensure(inv==v,'diagonal inversion'); checks+=1
    for d,c in ct.items():
        ensure(cy[(1,)+d+(1,)]==c,'coefficient double-face identity'); checks+=1
    differences=[(r,v,y[(1,)+r+(1,)]) for r,v in target.items() if v!=y[(1,)+r+(1,)]]
    ensure(differences,'point evaluation must fail in a signed example')
    # Exact direct counts; unlike CRT reconstruction this checks integer n literally.
    lift,G,lift_norm=p.optimal_lift(arrays['residual'],B,P,13)
    clift=p.coefficients(lift,B,P)
    ensure(p.marginal(p.marginal(lift,0,B),2,B)==arrays['residual'],'optimal lift trace')
    actual_norm=sum((v*v/F(prod(p.phi(a) for a in r)) for r,v in lift.items()),F(0))/B**4
    ensure(actual_norm==lift_norm,'optimal lift minimum diagonal norm')
    ensure(min(G.values())==1 and max(G.values())>1,'retained-dependent capacity')
    cpair=F(0); helper=F(0); rpair=F(0); direct=F(0); lift_count=F(0); pairs=0; ns=0
    for n in range(t['N'],t['N']+t['length']):
        if n%t['W']!=t['residue']:continue
        ns+=1
        a=p.sieve_value(cy,t['shifts'],n)
        b=p.sieve_value(arrays['cz'],t['shifts'][1:],n)
        c=p.sieve_value(arrays['cr'],t['shifts'][1:-1],n)
        lift_value=p.sieve_value(clift,t['shifts'],n); lift_count+=lift_value**2
        mask0=isprime(n); mask1=isprime(n+8)
        if mask0:helper+=b*b
        if mask0 and mask1:
            ensure(a==b+c,'prime endpoint residual identity'); pairs+=1
            ensure(lift_value==c,'lift equality on endpoint primes')
            cpair+=a*a; rpair+=c*c
        # Separate pointwise sieve evaluation, not evaluation of expanded coefficients.
        direct+=c*c*(1-int(n%7==0))**2*(1-int((n+8)%11==0))**2
    ensure(direct==crt['exact'],'direct enumeration versus CRT expansion')
    ensure(rpair<=direct<=crt['upper'],'residual two-prime majorant')
    ensure(rpair<=lift_count,'optimal lift counting majorant')
    ensure(abs(direct-crt['main'])<=crt['rounding_error'],'signed floor error bound')
    for tau in [F(1,10),F(1,2),F(1),F(2),F(10)]:
        ensure(cpair<=(1+tau)*helper+(1+1/tau)*rpair,'Young residual accounting')
    # Test non-coprime compatibility and residue representatives, including empty intervals.
    crt_tests=0
    for m in range(1,8):
        for n in range(1,8):
            period=m*n//gcd(m,n)
            for a in range(m):
                for b in range(n):
                    merged=p.merge_congruences([(a,m),(b,n)])
                    direct_solutions=[j for j in range(period) if j%m==a and j%n==b]
                    ensure((merged is None)==(not direct_solutions),'general CRT compatibility')
                    if merged:ensure(merged==(direct_solutions[0],period),'general CRT solution')
                    crt_tests+=1
    r,v,w=differences[0]
    return {'diagonal_equalities':checks,'literal_progression_points':ns,'endpoint_prime_pairs':pairs,
            'crt_compatibility_tests':crt_tests,'pair_square_sum':str(cpair),'helper_single_prime_sum':str(helper),
            'residual_pair_sum':str(rpair),'two_sieve_majorant':str(direct),'optimal_lift_counting_majorant':str(lift_count),
            'optimal_lift_diagonal_norm':str(lift_norm),
            'point_evaluation_counterexample':{'retained':list(r),'double_marginal':str(v),'point_value':str(w)}}


def validate(cert: dict,result: dict,data: dict) -> None:
    expected_cert,expected_result=p.build(data)
    ensure(cert==expected_cert,'certificate replay mismatch')
    ensure(result==expected_result,'result/evidence boundary mismatch')
    w=cert['witness']; v=direct_trial(data); h=F(data['mesh'])
    ensure(F(w['trial_value'])==v and v!=0,'independent trial evaluation')
    ensure(F(w['double_trace'])==h*h*v,'cell mass factor h squared')
    ensure(F(w['trial_bracket'][0])<=v<F(w['trial_bracket'][1]),'outward value bracket')


def negatives(cert: dict,result: dict,data: dict) -> int:
    # Each tampered payload is checked by the real validator, not a forced rejection stub.
    fixtures=[]
    def add(which: int,mutate) -> None:
        triple=[copy.deepcopy(cert),copy.deepcopy(result),copy.deepcopy(data)]
        mutate(triple[which]); fixtures.append(triple)
    add(0,lambda x:x['witness'].update(double_trace=x['witness']['trial_value']))
    add(0,lambda x:x['witness'].update(endpoint_cells=[[0,0],[0,1]]))
    add(0,lambda x:x['witness'].update(polynomial='0'))
    add(0,lambda x:x['witness'].update(base_fibre_empty=False))
    add(0,lambda x:x['finite_crt'].update(exact='0'))
    add(0,lambda x:x['finite_crt'].update(rounding_error='0'))
    add(0,lambda x:x.update(input_sha256='0'*64))
    add(1,lambda x:x.update(independently_verified=True))
    add(1,lambda x:x.update(restored_profile_obstruction_proved=True))
    add(1,lambda x:x.update(residual_bound_asymptotically_small=True))
    add(1,lambda x:x.update(new_prime_gap_bound=True))
    add(1,lambda x:x.update(twin_prime_conjecture_proved=True))
    add(1,lambda x:x.update(cannot_imply=[]))
    add(2,lambda x:x['coefficients'][0].__setitem__(0,10000000001))
    add(2,lambda x:x.update(mesh='1/100000'))
    add(2,lambda x:x['retained_cell_indices'].__setitem__(0,2585))
    for i,fixture in enumerate(fixtures):
        try:validate(*fixture)
        except (ValueError,KeyError,TypeError):continue
        raise ValueError(f'corruption {i} accepted')
    return len(fixtures)


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--check-hashes',action='store_true')
    ap.add_argument('--require-global',action='store_true')
    a=ap.parse_args()
    try:
        ensure(not a.require_global,'refused: neither a new prime-gap theorem nor a restored-profile certificate')
        read=lambda n:json.loads((a.root/n).read_text())
        cert,result,data=[read(n) for n in ('certificate.json','results.json','inputs.json')]
        validate(cert,result,data); report={'ok':True,'exact_trial_replay':True,'independently_verified':False,'new_prime_gap_bound':False}
        if a.self_test:
            report.update(geometry_oracle(data)); report.update(fibre_oracle()); report.update(diagonal_oracle(data))
            report['corruptions_rejected']=negatives(cert,result,data)
        if a.check_hashes:
            manifest=read('artifact-sha256.json')
            names={'README.md','proof.md','physical_trace.py','check_physical_trace.py','inputs.json','certificate.json',
                   'results.json','source-lock.json','computation-record.json','computation-handoff.json','verification-ticket.md'}
            ensure(set(manifest)==names,'exact manifest scope')
            for n,digest in manifest.items():
                ensure(hashlib.sha256((a.root/n).read_bytes()).hexdigest()==digest,'hash mismatch: '+n)
            report['hashes_verified']=len(manifest)
        print(json.dumps(report,sort_keys=True)); return 0
    except (ValueError,KeyError,TypeError,OSError) as e:
        print(json.dumps({'ok':False,'error':str(e)}),file=sys.stderr); return 1


if __name__=='__main__':
    sys.exit(main())
