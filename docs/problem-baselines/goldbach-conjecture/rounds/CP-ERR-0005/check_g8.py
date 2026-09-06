#!/usr/bin/env python3
"""CP-ERR-0005: exact G8 scalar certificate and finite switching regressions.

Python >=3.10; standard library only. No network or external executable.
--compute recomputes and compares the frozen scalar; --output writes a NEW file.
--self-test executes bounded exact models, not a universal theorem verification.
--check checks hashes, saved scalar algebra, contracts and regression evidence.
--require-global always rejects: external inputs and other terms remain open.
"""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import itertools
import json
from math import gcd, isqrt, prod
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
DEGREE = 96
R = F(2, 3)
CAP = F('0.609611574')
PRINTED = F('0.60962')
FILES = ('README.md', 'proof.md', 'contracts.json', 'prior-work.json',
         'source-lock.json', 'check_g8.py', 'results.json', 'error-handoff.json',
         'computation-handoff.json', 'verification-ticket.md', 'validation.json')


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def unique_object(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, 'duplicate JSON key: '+key)
        out[key] = value
    return out


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique_object)


def outward(x: F, upper: bool, places: int = 18) -> str:
    scale = 10**places
    k = -((-x.numerator*scale)//x.denominator) if upper else x.numerator*scale//x.denominator
    sign = '-' if k < 0 else ''
    k = abs(k)
    return f'{sign}{k//scale}.{k%scale:0{places}d}'


def coefficients(k: int) -> list[F]:
    c = [F(0)]
    for n in range(1, k+1):
        c.append(c[-1]/2+F(1, 2*n))
    return c


def compute() -> dict:
    c = coefficients(DEGREE)
    s = 8*sum(((-1)**(n+1)*c[n]*R**(n+1)/(n+1)
               for n in range(1, DEGREE+1)), F(0))
    tail = 8*R**(DEGREE+2)/((DEGREE+2)*(1-R))
    result = {
        'schema': 'goldbach-g8-exact-series/v1', 'degree': DEGREE,
        'object': '8*integral_0^(2/3) log(1+x)/(2+x) dx',
        'backend': 'Python fractions.Fraction; no floating-point acceptance',
        'partial_sum': str(s), 'tail_bound': str(tail),
        'lower_exact': str(s-tail), 'upper_exact': str(s+tail),
        'decimal_enclosure': [outward(s-tail, False), outward(s+tail, True)],
        'safe_upper': str(CAP), 'printed_upper': str(PRINTED),
        'coefficient_gain': str(PRINTED-CAP),
        'weighted_gain_before_dividing_by_four': str(2*(PRINTED-CAP)),
        'actual_G8_count_enclosed': False, 'global_status': 'INCONCLUSIVE',
        'independently_verified': False}
    validate_result(result)
    return result


def validate_result(d: dict) -> None:
    require(d['schema'] == 'goldbach-g8-exact-series/v1', 'result schema')
    require(d['degree'] == DEGREE, 'wrong truncation order')
    s, e, lo, hi = (F(d[k]) for k in ('partial_sum','tail_bound','lower_exact','upper_exact'))
    require(e == 8*R**(DEGREE+2)/((DEGREE+2)*(1-R)), 'incorrect tail')
    require(lo == s-e and hi == s+e, 'enclosure algebra')
    require(0 < lo < hi < CAP < PRINTED, 'upper-bound direction/target')
    require(hi-lo < F(1,10**17), 'certificate too wide')
    require(d['decimal_enclosure'] == [outward(lo,False),outward(hi,True)], 'decimal rounding')
    require(F(d['safe_upper']) == CAP and F(d['printed_upper']) == PRINTED, 'cap identity')
    require(F(d['coefficient_gain']) == PRINTED-CAP, 'coefficient gain')
    require(F(d['weighted_gain_before_dividing_by_four']) == 2*(PRINTED-CAP), 'weight -2')
    require(d['actual_G8_count_enclosed'] is False, 'scalar is not a count enclosure')
    require(d['global_status'] == 'INCONCLUSIVE' and d['independently_verified'] is False, 'authority')


def is_prime(n: int) -> bool:
    if n < 2: return False
    if n % 2 == 0: return n == 2
    return all(n % d for d in range(3, isqrt(n)+1, 2))


def next_prime(n: int) -> int:
    n += 1
    while not is_prime(n): n += 1
    return n


def prime_factors(n: int) -> list[int]:
    out = []
    for p in (2,):
        if n % p == 0:
            out.append(p)
            while n % p == 0: n //= p
    d = 3
    while d*d <= n:
        if n % d == 0:
            out.append(d)
            while n % d == 0: n //= d
        d += 2
    if n > 1: out.append(n)
    return out


def root_floor(n: int, k: int) -> int:
    lo, hi = 0, 1 << ((n.bit_length()+k-1)//k)
    while lo+1 < hi:
        m = (lo+hi)//2
        if m**k <= n: lo = m
        else: hi = m
    return lo


def eligible(N: int, p: int, q: int) -> bool:
    return (p <= q and p**11 >= N**3 and p*q*q <= N
            and gcd(p*q,N) == 1)


def survives(N: int, p: int, q: int, b: int) -> bool:
    a = N-b
    return (is_prime(b) and 0 < b < N and eligible(N,p,q) and a % (p*q) == 0
            and all(t >= q or (N*p) % t == 0 for t in prime_factors(a)))


def check_family(p: int, q: int, b: int) -> dict:
    N = p*p*q+b
    require(p >= 37 and is_prime(p) and is_prime(q) and is_prime(b), 'family primes')
    require(p < q < 2*p and 4*p**3 < b < 8*p**3, 'Bertrand intervals')
    require(N % 2 == 0 and eligible(N,p,q) and survives(N,p,q,b), 'family source domain')
    require(16*(N-b) > N and gcd(N,N-b) == 1, 'cutoff/gcd')
    require((N-b)//(p*q) == p < q, 'family contradicts prime >= p2')
    return {'N':N,'p1':p,'p2':q,'output_prime':b,'residual':p}


def validate_contract(c: dict) -> None:
    require(c['combination_coefficient'] == '-2', 'combination sign')
    require(c['switching']['object'] == 'indexed_multiset', 'set/multiset')
    require(c['switching']['cutoff'] == 'Z=sqrt(Q)', 'illegal sieve cutoff')
    require(c['switching']['H_term'] == 'identically_zero_on_q_divides_P_N_Z', 'support-specific H term')
    require(c['source_gates']['U_WBV'] == 'assumed_not_originally_audited', 'weighted source gate')
    require(c['source_gates']['uniform_Cs'] == 'assumed_not_discharged', 'uniformity gate')
    require(c['error_coefficients'] == {
        'ell_N':'1','r_N':'112','q_N':'16','h':'32','e_N':'32',
        'L*C_W*logN^(2-A)':'2','E_exc*logN^2/N':'2'}, 'error constants')
    require(c['global_status'] == 'INCONCLUSIVE' and c['independent_review'] == 'pending', 'global gate')


def self_test() -> dict:
    cn = coefficients(DEGREE)
    for n in range(1,DEGREE+1):
        direct = sum((F(1,k*2**(n-k+1)) for k in range(1,n+1)),F(0))
        require(cn[n] == direct and 0 < cn[n] < 1, 'series coefficient identity/bound')
    for x in (F(-7,9),F(0),F(1,3),F(1,2**100),F(10**25)):
        require(F(outward(x,False)) <= x <= F(outward(x,True)), 'outward rounding')
    require(F(1,2)-F(6,11) == -F(1,22), 'native level obstruction')
    require(F(1,4) < F(3,11) and 4*F(3,11)>1, 'size separation')
    require(survives(254,5,7,79), 'explicit source witness')
    require((254-79)//35 == 5 < 7, 'residual below p2')
    families = [check_family(p,next_prime(p),next_prime(4*p**3)) for p in (37,41,59,101)]
    triples = [[143,17],[187,13],[221,11]]
    require(is_prime(1601) and all(4032-m*p==1601 for m,p in triples), 'multiset witness')
    require(all(eligible(4032,*prime_factors(m)) for m,p in triples), 'duplicate source geometry')
    require(eligible(254,5,7) and 254-35*2 == 184 and not is_prime(184), 'composite B witness')
    require(gcd(5,35)>1 and gcd(5,254)==1 and 5<isqrt(254), 'outside-support H witness')
    tally = Counter(); max_mult = 0; modulus_cases = 0; objects = 0
    triple_total = 0; identity_mismatch_N = 0
    epsilon0 = F(1,10**11)
    # Exact exhaustive finite domain, not a prime conjecture verification range.
    for N in range(16,1201,2):
        primes = [p for p in range(2,N) if is_prime(p)]
        large = [p for p in primes if p**11 >= N**3]
        pairs = [(p,q) for p in large if p**3 <= N for q in large
                 if eligible(N,p,q)]
        by_b = Counter(); counts = Counter(); triple_N = 0
        for p,q in pairs:
            for b in primes:
                if not survives(N,p,q,b): continue
                objects += 1; by_b[b] += 1
                require(b < (1-epsilon0)*N, 'finite original strict cutoff')
                a = N-b; residual = a//(p*q)
                if gcd(a,N)==1 and is_prime(residual) and residual>=q:
                    triple_N += 1
                if gcd(a,N)>1: kind='output_divides_N'
                elif a%(p*p)==0: kind='repeated_p1'
                elif residual==1: kind='residual_one'
                else:
                    require(is_prime(residual) and residual>=q, 'uncovered bad residual')
                    kind='good_triple'
                counts[kind] += 1
        require(max(by_b.values(), default=0)<=3, 'native multiplicity bound')
        max_mult = max(max_mult, max(by_b.values(),default=0))
        zfloor = root_floor(N**3,11)
        zceil = zfloor + (zfloor**11 < N**3)
        require(counts['repeated_p1'] <= F(3*N,zceil-1), 'square branch bound')
        require(counts['residual_one'] <= root_floor(N*N,3), 'unit branch bound')
        require(counts['output_divides_N'] <= 3*len(prime_factors(N)), 'gcd branch bound')
        require(triple_N <= sum(counts.values()), 'ordered triple inclusion')
        require(sum(counts.values())-triple_N <= sum(counts[k] for k in
                ('repeated_p1','residual_one','output_divides_N')), 'repaired identity budget')
        triple_total += triple_N
        identity_mismatch_N += triple_N != sum(counts.values())
        tally.update(counts)
        # Finite legal level Q=Z^2<=sqrt(N); actual proof uses real Z=sqrt(Q).
        Z = root_floor(N,4); Q = Z*Z
        small = [p for p in primes if p<Z and N%p]
        qlist = [prod(s) for k in range(len(small)+1) for s in itertools.combinations(small,k)
                 if prod(s)<Q]
        indexed = [(p*q,t,N-p*q*t) for p,q in pairs for t in primes if p*q*t<N]
        require(max(Counter(b for m,t,b in indexed).values(),default=0)<=3, 'switched multiplicity')
        for d in qlist:
            require(all(gcd(p*q,d)==1 for p,q in pairs), 'H nonzero on actual support')
            left = sum(b%d==0 for m,t,b in indexed)
            right = sum(t%d == (N*pow(p*q,-1,d))%d
                        for p,q in pairs for t in primes if p*q*t<N) if d>1 else len(indexed)
            require(left==right, 'switched AP identity')
            modulus_cases += 1
    product_cases = 0
    for J,ell,r,q,h,e in itertools.product((F(0),F(1,8)),(F(0),F(1)),
            (F(0),F(1,32)),(F(0),F(1)),(F(0),F(1,4)),(F(0),F(1,10),F(10))):
        x=(1+ell)*(J+7*r)
        require(x<=1, 'x cap')
        lhs=8*x*(1+q)*(1+e)/(1-2*h)
        rhs=8*J+ell+112*r+16*q+32*h+32*e
        require(lhs<=rhs, 'expanded upper error contract')
        product_cases += 1
    return {'schema':'goldbach-g8-finite-regressions/v1','ok':True,
            'scalar_coefficients_checked':DEGREE,'outward_cases':5,
            'even_N_range_inclusive':[16,1200],'even_N_cases':593,
            'original_summands_checked':objects,'finite_cutoff_epsilon0':str(epsilon0),
            'ordered_prime_triples':triple_total,'literal_identity_mismatch_N_cases':identity_mismatch_N,'classification_counts':dict(sorted(tally.items())),
            'max_native_multiplicity':max_mult,'switched_modulus_identities':modulus_cases,
            'upper_product_cases':product_cases,'infinite_family_samples':families,
            'literal_residual_witness':{'N':254,'p1':5,'p2':7,'output_prime':79,'residual':5},
            'multiset_witness':{'N':4032,'b':1601,'representations':triples},
            'composite_B_witness':{'N':254,'m':35,'p':2,'b':184},
            'mathematical_truth_verified':False}


def check_saved() -> dict:
    manifest=read_json(ROOT/'artifact-sha256.json')['sha256']
    require(set(manifest)==set(FILES),'manifest file coverage')
    for name,expected in manifest.items():
        require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,'hash '+name)
    result=read_json(ROOT/'results.json'); validate_result(result)
    contract=read_json(ROOT/'contracts.json'); validate_contract(contract)
    fresh=self_test(); require(fresh==read_json(ROOT/'validation.json'),'regression output mismatch')
    negative=0
    def reject(fn):
        nonlocal negative
        try: fn()
        except (ValueError,KeyError,TypeError): negative+=1
        else: raise ValueError('negative control accepted')
    for key,value in (('degree',95),('tail_bound','0'),('safe_upper','0.60961157'),
            ('global_status','PASS'),('actual_G8_count_enclosed',True),
            ('weighted_gain_before_dividing_by_four','0'),('lower_exact',result['upper_exact'])):
        d=dict(result); d[key]=value; reject(lambda d=d:validate_result(d))
    for path,value in ((('combination_coefficient',),'2'),(('switching','object'),'distinct_set'),
            (('switching','cutoff'),'sqrt(N)'),(('source_gates','U_WBV'),'classical_BV_only'),
            (('source_gates','uniform_Cs'),'independently_verified')):
        d=deepcopy(contract)
        if len(path)==1: d[path[0]]=value
        else: d[path[0]][path[1]]=value
        reject(lambda d=d:validate_contract(d))
    reject(lambda:require((254-79)//35>=7,'incorrect residual implication'))
    reject(lambda:require(is_prime(184),'all B prime'))
    reject(lambda:require(len({1601 for _ in range(3)})==3,'multiplicity erased'))
    reject(lambda:require(gcd(5,35)==1,'H zero outside smooth support'))
    return {'ok':True,'hashes_checked':len(FILES),'negative_controls_rejected':negative,
            'scalar_series_recomputed':False,'finite_regressions_reexecuted':True,
            'global_status':'INCONCLUSIVE','mathematical_truth_verified':False}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    for name in ('compute','self-test','check','require-global'): g.add_argument('--'+name,action='store_true')
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    if args.require_global:
        print('REJECT: U-WBV/U-LS source gates, other eleven terms and independent/global reconciliation remain open.')
        return 1
    data=compute() if args.compute else self_test() if args.self_test else check_saved()
    if args.output:
        require(not args.check,'check is read-only')
        with args.output.open('x',encoding='utf-8') as f:
            f.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    elif args.compute:
        require(data==read_json(ROOT/'results.json'),'fresh scalar differs from frozen output')
    print(json.dumps(data,ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as e:
        print('FAIL: '+str(e),file=sys.stderr)
        raise SystemExit(1)
