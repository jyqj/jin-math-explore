#!/usr/bin/env python3
"""Exact finite regressions for WBV-G8; never an asymptotic theorem verifier.

Python >=3.10, standard library only. --compute reruns all finite cases and
compares frozen results. --output creates a new file, never overwrites one.
--check checks saved evidence, payload hashes and contract mutations only.
"""
from __future__ import annotations
import argparse
from functools import lru_cache
from fractions import Fraction as F
import hashlib
import json
from math import gcd, isqrt
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
FILES = ('README.md', 'proof.md', 'contracts.json', 'prior-work.json',
         'source-lock.json', 'check_wbv.py', 'results.json', 'error-handoff.json',
         'computation-handoff.json', 'verification-ticket.md', 'validation.json')


def require(test: bool, text: str) -> None:
    if not test:
        raise ValueError(text)


@lru_cache(None)
def divisors(n: int) -> tuple[int, ...]:
    require(n >= 1, 'positive modulus required')
    return tuple(d for d in range(1, n+1) if n % d == 0)


@lru_cache(None)
def factors(n: int) -> tuple[int, ...]:
    ans, d = [], 2
    while d*d <= n:
        if n % d == 0:
            ans.append(d)
            while n % d == 0:
                n //= d
        d += 1
    if n > 1:
        ans.append(n)
    return tuple(ans)


@lru_cache(None)
def phi(n: int) -> int:
    out = n
    for p in factors(n):
        out = out//p*(p-1)
    return out


@lru_cache(None)
def mu(n: int) -> int:
    fs = factors(n)
    return 0 if any(n % (p*p) == 0 for p in fs) else (-1)**len(fs)


@lru_cache(None)
def primes(n: int) -> tuple[int, ...]:
    if n < 2:
        return ()
    sieve = bytearray(b'\x01')*(n+1)
    sieve[:2] = b'\x00\x00'
    for p in range(2, isqrt(n)+1):
        if sieve[p]:
            sieve[p*p:n+1:p] = b'\x00'*((n-p*p)//p+1)
    return tuple(p for p in range(2, n+1) if sieve[p])


@lru_cache(None)
def kernel(d: int, x: int, y: int) -> int:
    """Sum of chi(x)*conj(chi(y)) over primitive characters, exactly."""
    if gcd(x*y, d) != 1:
        return 0
    return sum(mu(d//e)*phi(e) for e in divisors(d) if (x-y) % e == 0)


@lru_cache(None)
def lifted_nonprincipal(q: int, b: int, n: int) -> int:
    return sum(kernel(d, b % d, n % d) for d in divisors(q)
               if d > 1 and gcd(n, q//d) == 1)


def in_slab(m: int, N: int) -> bool:
    return m**11 >= N**6 and m**3 <= N**2


def g8_products(N: int) -> tuple[int, ...]:
    ps = primes(isqrt(N))
    found = []
    for i, p in enumerate(ps):
        if p**3 > N:
            break
        if p**11 < N**3:
            continue
        for r in ps[i:]:
            if p*r*r > N:
                break
            if gcd(p*r, N) == 1:
                found.append(p*r)
    require(len(found) == len(set(found)), 'duplicate unordered semiprime')
    require(all(in_slab(m, N) for m in found), 'G8 support outside slab')
    return tuple(sorted(found))


def decomposition(N: int, weights: dict[int, int], q: int, b: int) -> dict:
    require(gcd(b, q) == 1, 'residue must be reduced')
    count = pi_mass = removed = nonprincipal = 0
    for m, w in weights.items():
        if gcd(m, q) != 1:
            continue
        ps = primes(N//m)
        pi_mass += w*len(ps)
        removed += w*sum(N//m >= p for p in factors(q))
        for p in ps:
            count += w*((m*p-b) % q == 0)
            nonprincipal += w*lifted_nonprincipal(q, b, m*p)
    lhs = F(count)-F(pi_mass, phi(q))
    rhs = F(nonprincipal-removed, phi(q))
    require(lhs == rhs, 'principal/imprimitive decomposition failed')
    return {'N':N, 'q':q, 'residue':b, 'count':count, 'pi_mass':pi_mass,
            'removed_prime_mass':removed, 'nonprincipal_sum':nonprincipal,
            'error_pi':str(lhs), 'character_only':str(F(nonprincipal,phi(q)))}


def exponent_ledger(A: int) -> dict:
    require(A >= 3, 'this explicit parameter plan requires A>=3')
    B = D = A+8
    J = 2*A+12
    rows = [
        ('large_Q', F(1), 4-B), ('large_smallest_conductor', F(1), 4-D),
        ('large_m_side', F(5,6), 4), ('large_p_side', F(8,11), 4),
        ('small_SW', F(1), D+2-J), ('small_removed_primes', F(2,3), D+2),
        ('principal_correction', F(2,3), 2), ('pi_to_Li', F(1), 2-J)]
    for _, power, logs in rows:
        require(power < 1 or (power == 1 and logs <= -A), 'saving does not close')
    require((1+F(2,3))/2 == F(5,6) and 1-F(6,11)/2 == F(8,11), 'slab powers')
    return {'A':A, 'B':B, 'D':D, 'J':J,
            'rows':[{'id':name,'N_power':str(p),'log_power':k} for name,p,k in rows],
            'normalized_G8_log_power':2-A, 'G8_multiplier':2,
            'lower_combination_multiplier_before_dividing_four':4}


def validate_contract(c: dict) -> None:
    require(c['schema'] == 'goldbach-wbv-bridge/v1', 'contract schema')
    require(c['support'] == ['6/11','2/3'], 'support changed')
    require(c['weight_bound'] == '1' and c['weights_may_depend_on_N'] is True, 'weight class')
    require(c['weights_may_depend_on_q'] is False, 'uncontrolled modulus-dependent coefficients')
    require(c['cutoff'] == 'mp<=N' and c['arbitrary_m_endpoints'] is False, 'endpoint overclaim')
    require(c['absolute_value'] == 'outside_complete_m_sum', 'lost cancellation')
    require(c['parameters'] == {'minimum_A':3,'B':'A+8','D':'A+8','J':'2*A+12'}, 'log plan')
    require(c['principal_correction'] == '-D_q/phi(q)', 'principal removal missing or wrong sign')
    require(c['imprimitive_identity'] == 'chi(n)=chi_star(n)*1_gcd(n,l)=1', 'induction filter')
    require(c['normalized_remainder_multiplier'] == 2 and c['combination_multiplier'] == 4, 'sign/factor')
    require(c['linear_sieve_Cs_uniformity'] == 'unresolved', 'different source gate silently discharged')
    require(c['original_Pan_Ding_full_text_audited'] is False, 'unavailable original proof claimed read')
    require(c['effective_numeric_N0'] is None, 'ineffectivity lost')
    require(c['global_status'] == 'INCONCLUSIVE' and c['independently_verified'] is False, 'authority overclaim')


def negative_controls(c: dict) -> int:
    mutations = [('support',['0','1']), ('weights_may_depend_on_q',True),
        ('weight_bound','unbounded'), ('arbitrary_m_endpoints',True),
        ('cutoff','arbitrary_r2(m)'), ('absolute_value','inside_m_sum'),
        ('principal_correction','0'), ('principal_correction','+D_q/phi(q)'),
        ('imprimitive_identity','chi=chi_star'), ('normalized_remainder_multiplier',1),
        ('combination_multiplier',2), ('linear_sieve_Cs_uniformity','proved'),
        ('original_Pan_Ding_full_text_audited',True), ('effective_numeric_N0',1000),
        ('global_status','PASS'), ('independently_verified',True),
        ('parameters',{'minimum_A':3,'B':'A','D':'A','J':'A'})]
    count = 0
    for key, value in mutations:
        bad = dict(c); bad[key] = value
        try:
            validate_contract(bad)
        except (ValueError, KeyError, TypeError):
            count += 1
        else:
            raise ValueError('invalid contract accepted: '+key)
    return count


def compute() -> dict:
    stats = dict(orthogonality_cases=0, totient_identities=0, totient_product_cases=0,
                 arbitrary_weight_AP_cases=0, G8_N_cases=0, G8_nonempty_cases=0,
                 G8_AP_cases=0, smooth_support_cases=0, nonzero_D_on_smooth_support=0,
                 endpoint_checks=0, dyadic_pair_checks=0, exact_large_sieve_cases=0,
                 radical_envelope_cases=0, conductor_partition_cases=0)
    for q in range(1,41):
        for b in range(q):
            if gcd(b,q) != 1: continue
            for n in range(2*q+1):
                total = sum(kernel(d,b%d,n%d) for d in divisors(q) if gcd(n,q//d)==1)
                expected = phi(q) if gcd(n,q)==1 and (n-b)%q==0 else 0
                require(total == expected, 'primitive orthogonality/lift')
                stats['orthogonality_cases'] += 1
    for n in range(1,201):
        require(F(n,phi(n)) == sum((F(mu(d)**2,phi(d)) for d in divisors(n)),F(0)), 'totient convolution')
        stats['totient_identities'] += 1
    for d in range(1,41):
        for l in range(1,41):
            require(phi(d*l)>=phi(d)*phi(l), 'totient product')
            stats['totient_product_cases'] += 1
    for N in (16,31,64,125,254,511,1000):
        ms = [m for m in range(1,isqrt(N*N)+1) if in_slab(m,N)]
        for mode in range(3):
            ws = {m:(1 if mode==0 else (-1)**m if mode==1 else m%3-1) for m in ms}
            for q in range(1,19):
                for b in range(q):
                    if gcd(b,q)==1:
                        decomposition(N,ws,q,b)
                        stats['arbitrary_weight_AP_cases'] += 1
    for N in tuple(range(16,513,2))+(1000,2000,4032,10000):
        ms = g8_products(N)
        stats['G8_N_cases'] += 1
        stats['G8_nonempty_cases'] += bool(ms)
        for m in ms:
            require(N%m != 0, 'strict endpoint not identical')
            stats['endpoint_checks'] += 1
        if not ms: continue
        Q0 = isqrt(N)  # illustrative legal B=0 support; no asymptotic onset claim
        for q in range(1,min(Q0,40)+1):
            if gcd(N,q)!=1: continue
            row = decomposition(N,{m:1 for m in ms},q,N%q)
            stats['G8_AP_cases'] += 1
            if q<Q0 and mu(q)!=0 and all(p*p<Q0 for p in factors(q)):
                require(all(gcd(m,q)==1 for m in ms), 'smooth H=0 failed')
                stats['smooth_support_cases'] += 1
                stats['nonzero_D_on_smooth_support'] += row['removed_prime_mass'] != 0
    for N in range(16,257):
        direct, blocked = set(), set()
        ms = [m for m in range(1,N+1) if in_slab(m,N)]
        for m in ms:
            direct.update((m,p) for p in primes(N//m))
        M = 1
        while M<=N:
            for m in ms:
                if M<=m<2*M:
                    for p in primes(N//M):
                        if m*p<=N:
                            require((m,p) not in blocked, 'duplicate dyadic cell')
                            blocked.add((m,p))
            M *= 2
        require(direct == blocked, 'hyperbola coverage')
        stats['dyadic_pair_checks'] += len(direct)
    for shift in (1,3,9):
        for length in range(1,7):
            ns = list(range(shift,shift+length))
            for mode in range(3):
                coeff = [(1,0) if mode==0 else ((-1)**n,n%2) if mode==1
                         else (n%3-1,(-1)**n) for n in ns]
                norm = sum(x*x+y*y for x,y in coeff)
                for Q in range(1,9):
                    lhs = F(0)
                    for d in range(1,Q+1):
                        sq = sum((coeff[i][0]*coeff[j][0]+coeff[i][1]*coeff[j][1])
                                 *kernel(d,ns[i]%d,ns[j]%d)
                                 for i in range(length) for j in range(length))
                        require(sq>=0, 'negative character energy')
                        lhs += F(d,phi(d))*sq
                    require(0<=lhs<=(length+Q*Q)*norm, 'finite large-sieve bound')
                    stats['exact_large_sieve_cases'] += 1
    for a in range(1,6):
        for b in range(1,6):
            M,P = a*a,b*b
            for R in range(1,9):
                square = F((M+4*R*R)*(P+4*R*R)*M*P,R*R)
                upper = F(M*P,R)+2*a*b*(a+b)+4*R*a*b
                require(square <= upper*upper, 'radical envelope')
                stats['radical_envelope_cases'] += 1
    for Q in (7,16,31,64):
        for D0 in (1,3,5):
            bins = list(range(2,min(D0,Q)+1)); R=D0
            while R<Q:
                bins.extend(range(R+1,min(2*R,Q)+1)); R*=2
            require(sorted(bins)==list(range(2,Q+1)), 'conductor partition')
            stats['conductor_partition_cases'] += 1
    witness = decomposition(254,{m:1 for m in g8_products(254)},3,2)
    require(g8_products(254)==(25,35), 'witness object mismatch')
    require(witness['error_pi']=='-1' and witness['character_only']=='0' and witness['removed_prime_mass']==2, 'witness values')
    require(13*5>64 and 5<=64//8 and 8<=13<16 and in_slab(13,64), 'rectangle negative witness')
    require(kernel(3,1,2)==-1 and gcd(2,6//3)!=1, 'imprimitive negative witness')
    return {'schema':'goldbach-wbv-exact-regressions/v1', 'stats':stats,
            'principal_correction_witness':witness,
            'imprimitive_witness':{'q':6,'d':3,'n':2,'primitive_value':-1,'induced_value':0},
            'hyperbola_witness':{'N':64,'m':13,'p':5,'M':8,'rectangle_includes':True,'product_cutoff_includes':False},
            'parameter_cases':[exponent_ledger(A) for A in range(3,13)],
            'finite_only':True,'mathematical_truth_verified':False,'effective_numeric_N0':None,
            'global_status':'INCONCLUSIVE'}


def validate_result(r: dict) -> None:
    require(r['schema']=='goldbach-wbv-exact-regressions/v1', 'result schema')
    require(r['parameter_cases']==[exponent_ledger(A) for A in range(3,13)], 'parameter results')
    require(r['principal_correction_witness']==decomposition(254,{25:1,35:1},3,2), 'principal witness mutation')
    require(r['finite_only'] is True and r['mathematical_truth_verified'] is False, 'finite/universal boundary')
    require(r['effective_numeric_N0'] is None and r['global_status']=='INCONCLUSIVE', 'global result overclaim')
    require(all(isinstance(v,int) and v>0 for v in r['stats'].values()), 'missing test coverage')


def check_saved() -> dict:
    c = json.loads((ROOT/'contracts.json').read_text()); validate_contract(c)
    r = json.loads((ROOT/'results.json').read_text()); validate_result(r)
    v = json.loads((ROOT/'validation.json').read_text())
    require(v['stats']==r['stats'], 'validation coverage differs')
    nc = negative_controls(c)
    require(v['contract_mutations_rejected']==nc, 'negative-control count')
    manifest = json.loads((ROOT/'artifact-sha256.json').read_text())
    require(set(manifest['sha256'])==set(FILES), 'manifest inventory')
    for file in FILES:
        require(hashlib.sha256((ROOT/file).read_bytes()).hexdigest()==manifest['sha256'][file], 'hash mismatch '+file)
    mutations=0
    for key,val in [('effective_numeric_N0',1000),('global_status','PASS'),
                    ('finite_only',False),('mathematical_truth_verified',True),('parameter_cases',[])]:
        bad=dict(r);bad[key]=val
        try: validate_result(bad)
        except (ValueError,KeyError,TypeError): mutations+=1
        else: raise ValueError('corrupt result accepted')
    return {'ok':True,'hashes_checked':len(FILES),'negative_controls_rejected':nc+mutations,
            'full_finite_suite_executed':False,'mathematical_truth_verified':False}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    for flag in ('compute','check','require-global'):
        group.add_argument('--'+flag,action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.require_global:
        print('REJECT: independent review, Cs uniformity and the global twelve-term proof are unclosed.')
        return 1
    data=compute() if args.compute else check_saved()
    if args.compute: validate_result(data)
    if args.output:
        require(args.compute, '--check does not write')
        with args.output.open('x',encoding='utf-8') as f:
            f.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    elif args.compute:
        require(data==json.loads((ROOT/'results.json').read_text()), 'fresh finite output differs')
    print(json.dumps(data,ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print('FAIL: '+str(exc),file=sys.stderr)
        raise SystemExit(1)
