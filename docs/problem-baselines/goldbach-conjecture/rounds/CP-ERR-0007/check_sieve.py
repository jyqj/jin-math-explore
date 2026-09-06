#!/usr/bin/env python3
"""Exact finite checks for CP-ERR-0007, NOT a Goldbach/linear-sieve verifier.
Python >=3.10, standard library only. --compute recomputes the finite suite and
scalar; --check checks frozen fields/hashes. --output creates a NEW file only.
Source Theorem 6, Mertens and the distribution input are not proved by this code.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from fractions import Fraction as F
import hashlib
from itertools import product
import json
from math import gcd, isqrt, prod
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
FILES = ('README.md', 'proof.md', 'contracts.json', 'prior-work.json',
         'source-lock.json', 'check_sieve.py', 'results.json', 'error-handoff.json',
         'computation-handoff.json', 'verification-ticket.md', 'validation.json')
DEGREE = 96
CAP = F('0.609611574')
COEFFICIENTS = {'q_X':'48', 'q_V':'2', 'h_star':'4', 'epsilon':'462',
                'C_A*logN^(3-A)':'19', 'E_exc*logN^2/N':'2'}


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def primes_to(n: int) -> list[int]:
    flags = bytearray(b'\x01')*(n+1)
    flags[:2] = b'\x00\x00'
    for p in range(2, isqrt(n)+1):
        if flags[p]:
            flags[p*p:n+1:p] = b'\x00'*((n-p*p)//p+1)
    return [i for i in range(2,n+1) if flags[i]]


def prime_factors(n: int) -> list[int]:
    out = []
    p = 2
    while p*p <= n:
        if n % p == 0:
            out.append(p)
            while n % p == 0: n //= p
        p += 1
    if n > 1: out.append(n)
    return out


def phi(n: int) -> int:
    need(n >= 1, 'positive totient argument')
    ans = n
    for p in prime_factors(n): ans = ans//p*(p-1)
    return ans


def divisors(n: int) -> list[int]:
    return [d for d in range(1,n+1) if n % d == 0]


def squarefree(n: int) -> bool:
    return all(n % (p*p) for p in prime_factors(n))


def squarefree_products(ps: list[int]) -> list[int]:
    out = [1]
    for p in ps: out += [p*d for d in out]
    return sorted(out)


def outward(x: F, upper: bool, places: int = 18) -> str:
    scale = 10**places
    k = -((-x.numerator*scale)//x.denominator) if upper else x.numerator*scale//x.denominator
    sign = '-' if k < 0 else ''
    k = abs(k)
    return f'{sign}{k//scale}.{k%scale:0{places}d}'


def scalar() -> dict:
    u = F(2,3)
    total = F(0)
    for n in range(1,DEGREE+1):
        c = sum((F(1,k*2**(n-k+1)) for k in range(1,n+1)), F(0))
        need(0 < c < 1, 'power-series coefficient envelope')
        total += 8*(-1)**(n+1)*c*u**(n+1)/(n+1)
    radius = 8*u**(DEGREE+2)/((DEGREE+2)*(1-u))
    lo, hi = total-radius, total+radius
    need(0 < lo < hi < CAP < F('0.60962') < 1, 'scalar cap')
    return {'degree':DEGREE, 'center':str(total), 'tail_radius':str(radius),
            'exact_lower':str(lo), 'exact_upper':str(hi),
            'outward_decimal':[outward(lo,False),outward(hi,True)],
            'retained_cap':str(CAP), 'coefficient_changed':False}


def self_tests() -> dict:
    counts = {}
    # Literal level-one support excludes every positive integer; closed support
    # contains the Dirichlet-convolution identity. The general proof is in proof.md.
    counts['level_one_and_convolution'] = 0
    for Q in range(1,33):
        for n in range(1,33):
            strict_first = {j:F(0) for j in range(1,33)}
            seq = {j:F((-1)**j,j+1) for j in range(1,Q+1)}
            conv_zero = sum((strict_first[d]*seq.get(n//d,F(0)) for d in divisors(n)),F(0))
            conv_unit = sum(((F(1) if d==1 else F(0))*seq.get(n//d,F(0)) for d in divisors(n)),F(0))
            need(conv_zero == 0 and conv_unit == seq.get(n,F(0)), 'unit support')
            counts['level_one_and_convolution'] += 1
    counts['totient_divisor_identities'] = 0
    counts['reciprocal_totient_bounds'] = 0
    H, harmonic = F(0), F(0)
    for n in range(1,513):
        rhs = sum((F(1,phi(d)) for d in divisors(n) if squarefree(d)),F(0))
        need(F(n,phi(n)) == rhs, 'totient divisor identity')
        H += F(1,phi(n)); harmonic += F(1,n)
        need(H < 3*harmonic, 'finite totient sum majorant')
        counts['totient_divisor_identities'] += 1
        counts['reciprocal_totient_bounds'] += 1
    # Exact finite pre-sieve containment, including the strict d bound.
    ps = primes_to(31)
    counts['presieve_modulus_containment'] = 0
    for w,N,R in product((3,5,7,11),(30,42,254,2310),(F(100),F(1001,3),F(10000))):
        P0 = prod(p for p in ps if p<w)
        W = prod(p for p in ps if p<w and N%p)
        need(P0 % W == 0, 'exceptional product divides universal product')
        D = R/P0
        if D < 4: continue
        sieve_ps = [p for p in ps if p*p < D and N%p]
        for d in squarefree_products(sieve_ps):
            if d < W*D:
                need(d < R, 'pre-sieve modulus escaped distribution level')
                counts['presieve_modulus_containment'] += 1
    # d=105 is on the bad D=R=100, Z=10 support, W=3, yet d>R.
    need(all(p<10 and 254%p for p in prime_factors(105)) and 100<105<3*100,
         'lost-preproduct witness')
    # Universal finite rebasing on nonnegative rational sequences; all d=1 cases included.
    counts['rebase_identities'] = counts['rebase_sum_bounds'] = 0
    for seed,N,Z in product(range(7),(30,42,254),(5,7,11)):
        weights = {n:F((seed*n+3*n*n+1)%7,3) for n in range(1,41)}
        mass = sum(weights.values(),F(0))
        moduli = [d for d in squarefree_products([p for p in ps if p<Z and N%p]) if d<150]
        for shift in (F(-3),F(-1,2),F(0),F(1,3),F(4)):
            X = mass+shift
            delta = mass-X
            E = Eprime = Gsum = F(0)
            for d in moduli:
                gd = F(1,phi(d))
                Ad = sum((v for n,v in weights.items() if n%d==0),F(0))
                r, rp = Ad-X*gd, Ad-mass*gd
                need(rp == r-delta*gd, 'rebase sign')
                E += abs(r); Eprime += abs(rp); Gsum += gd
                counts['rebase_identities'] += 1
            need(abs(delta)<=E and Eprime<=E+abs(delta)*Gsum, 'absolute remainder rebase')
            counts['rebase_sum_bounds'] += 1
    # Actual indexed B+ examples, without using Li floating-point evaluations.
    counts['actual_switched_rebase'] = 0
    counts['actual_smooth_coprimality'] = 0
    actual_cases = []
    for N in (254,512,1000,2048,4032,4096,10000):
        pp = primes_to(N)
        Ms = []
        p1s = [p for p in pp if p**11 >= N**3 and p**3 <= N]
        for p1 in p1s:
            for p2 in pp:
                if p2 < p1: continue
                if p1*p2*p2 > N: break
                if gcd(p1*p2,N)==1: Ms.append(p1*p2)
        need(len(Ms)==len(set(Ms)), 'unique extracted product')
        seq = [N-m*p for m in Ms for p in pp if m*p<N]
        Z = isqrt(isqrt(N))
        ds = [d for d in squarefree_products([p for p in pp if p<Z and N%p]) if d<isqrt(N)]
        for d in ds:
            for m in Ms:
                need(gcd(m,d)==1, 'actual smooth support')
                counts['actual_smooth_coprimality'] += 1
            Ad = sum(b%d==0 for b in seq)
            X = F(len(seq))+F(2,3)
            r = F(Ad)-X/phi(d)
            rp = F(Ad)-F(len(seq),phi(d))
            need(rp == r-(F(len(seq))-X)/phi(d), 'actual indexed mass rebase')
            counts['actual_switched_rebase'] += 1
        actual_cases.append({'N':N,'products':len(Ms),'mass':len(seq),'moduli':len(ds)})
    # Algebraic main-bound transfer, not sampling primes or source constants.
    counts['main_coefficient_inequalities'] = 0
    for eps,qv,h,qx,g in product((F(1,200),F(1,1000),F(1,10**8)),
          (F(0),F(1,10),F(1,2)),(F(0),F(1,20),F(1,4)),
          (F(0),F(1,100),F(1,2)),(F(0),F(3,5),F(1))):
        factor = (1+154*eps)*(1+qv)/(1-2*h)
        need(factor<=6, 'bounded transfer factor')
        lhs = factor*(g+8*qx)
        rhs = g+48*qx+2*qv+4*h+462*eps
        need(lhs<=rhs, 'six-term main contract')
        counts['main_coefficient_inequalities'] += 1
    counts['parameter_budgets'] = 0
    for delta in (F(1,100),F(1,10**4),F(8,10**6),F(1,10**10)):
        eps = min(F(1,400),delta/(4*462))
        need(0<eps<=F(1,200) and 462*eps<=delta/4,'parameter order/fixed budget')
        counts['parameter_budgets'] += 1
    for x in (F(0),F(-1,3),F(7,9),F(1,10**30)):
        need(F(outward(x,False))<=x<=F(outward(x,True)), 'decimal direction')
    return {'schema':'goldbach-cp7-finite-tests/v1','ok':True,'counts':counts,
            'actual_B_plus_cases':actual_cases,'source_theorem_verified':False,
            'scope':'finite rational identities and inequality regressions only'}


def validate(data: dict) -> None:
    need(data['schema']=='goldbach-cp7-results/v1','result schema')
    s = data['scalar']
    need(s['degree']==DEGREE,'scalar degree')
    need(F(s['exact_lower'])==F(s['center'])-F(s['tail_radius']),'scalar lower')
    need(F(s['exact_upper'])==F(s['center'])+F(s['tail_radius']),'scalar upper')
    expected_tail = 8*F(2,3)**(DEGREE+2)/((DEGREE+2)*(1-F(2,3)))
    need(F(s['tail_radius'])==expected_tail,'analytic tail')
    lo,hi = F(s['exact_lower']),F(s['exact_upper'])
    need(F(s['outward_decimal'][0])<=lo<hi<=F(s['outward_decimal'][1])<CAP,'outward enclosure')
    need(s['retained_cap']==str(CAP) and s['coefficient_changed'] is False,'old scalar immutable')
    need(data['new_contract_coefficients']==COEFFICIENTS,'native constants')
    need(data['Cs_used'] is False and data['L_eta_used'] is False,'old constants smuggled in')
    need(data['distribution_power']=='3-A' and data['requires_A_at_least']==4,'lost logarithm')
    need(data['original_Cs_audit']=='UNRESOLVED' and data['global_status']=='INCONCLUSIVE','source/global promotion')
    need(data['independently_verified'] is False,'self-verification')
    need(data['presieve_divisor']=='P0' and data['rebasing_includes_d1'] is True,'source-interface omissions')


def compute() -> dict:
    data = {'schema':'goldbach-cp7-results/v1','scalar':scalar(),'finite_tests':self_tests(),
            'new_contract_coefficients':COEFFICIENTS,'Cs_used':False,'L_eta_used':False,
            'distribution_power':'3-A','requires_A_at_least':4,
            'presieve_divisor':'P0','rebasing_includes_d1':True,
            'original_Cs_audit':'UNRESOLVED','global_status':'INCONCLUSIVE',
            'independently_verified':False}
    validate(data)
    return data


def negatives(data: dict) -> int:
    changes = [('Cs_used',True),('L_eta_used',True),('distribution_power','2-A'),
               ('requires_A_at_least',3),('presieve_divisor','1'),('rebasing_includes_d1',False),
               ('original_Cs_audit','PASS'),('global_status','PASS'),('independently_verified',True)]
    rejected = 0
    for field,val in changes:
        bad=deepcopy(data); bad[field]=val
        try: validate(bad)
        except ValueError: rejected+=1
        else: raise ValueError('negative result accepted: '+field)
    for field,val in [('tail_radius','0'),('outward_decimal',['1','0']),('coefficient_changed',True)]:
        bad=deepcopy(data); bad['scalar'][field]=val
        try: validate(bad)
        except ValueError: rejected+=1
        else: raise ValueError('negative scalar accepted: '+field)
    # Additional semantic counterexamples have actual rational witnesses.
    witnesses = [bool([n for n in range(1,5) if n<1]), # strict level1 has no unit
                 105<100, # omitted exceptional product
                 F(1)-F(1,2)==F(1)-F(2,2), # omitted rebase of A={3},X=2
                 F(1,4) >= F(3,11), # false claim that the sieve reaches extracted primes
                 F(462,200)<=F(1,10**6), # unchosen epsilon not a tiny fixed loss
                 F(1,100)*100 < F(1,2)] # eta Cs(eta) need not vanish
    for claim in witnesses:
        try: need(claim,'deliberately false semantic claim')
        except ValueError: rejected+=1
        else: raise ValueError('semantic negative accepted')
    return rejected


def check_saved() -> dict:
    data=json.loads((ROOT/'results.json').read_text())
    validate(data)
    expected_tests=json.loads((ROOT/'validation.json').read_text())
    need(data['finite_tests']==expected_tests,'saved finite results disagree')
    manifest=json.loads((ROOT/'artifact-sha256.json').read_text())
    need(set(manifest['sha256'])==set(FILES),'manifest coverage')
    for name,h in manifest['sha256'].items():
        need(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,'hash '+name)
    contract=json.loads((ROOT/'contracts.json').read_text())
    need(contract['coefficients']==COEFFICIENTS,'contract constants')
    need(contract['source_inputs']['U_WBV']=='unverified_predecessor_dependency','WBV authority')
    need(contract['source_inputs']['BJS_Theorem6']=='imported_not_reproved','source receipt')
    return {'ok':True,'hashes_checked':len(FILES),'negative_controls_rejected':negatives(data),
            'full_finite_suite_rerun':False,'mathematical_truth_verified':False}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    for name in ('compute','self-test','check','require-global'):
        group.add_argument('--'+name,action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.require_global:
        print('REJECT: original Cs audit, independent review and global twelve-term closure are unresolved.')
        return 1
    data=compute() if args.compute else (self_tests() if args.self_test else check_saved())
    if args.output:
        need(not args.check,'saved-result checking writes nothing')
        with args.output.open('x',encoding='utf-8') as stream:
            stream.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    elif args.compute:
        need(data==json.loads((ROOT/'results.json').read_text()),'fresh finite computation differs')
    print(json.dumps(data,ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':
    try: raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print('FAIL: '+str(exc),file=sys.stderr)
        raise SystemExit(1)
