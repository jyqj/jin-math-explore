#!/usr/bin/env python3
"""CP-ERR-0010: fixed/log versus fixed-gap G6, not a Goldbach verifier.

Python >=3.10; mpmath==1.3.0 for directed quadrature. Finite tests use exact
integers/Fraction and SYNTHETIC analytic masses, not measured Li errors.
--compute reruns all three integrals. --check never runs quadrature.
--output creates a new file; no mode overwrites a frozen artifact.
"""
from __future__ import annotations
import argparse
import copy
from fractions import Fraction as F
import hashlib
import itertools
import json
from math import gcd, isqrt, prod
from pathlib import Path
import sys
import mpmath as mp

ROOT = Path(__file__).resolve().parent
A, B = F(4,53), F(4,33)
SIGMAS = (F(0), F(1,10**6), F(4,10**6))
CELLS, DEGREE, DPS = 4096, 48, 50
TARGET, BASE_FLOOR, FIXED_FLOOR = F('1.63357'), F('1.6335733'), F('1.6335722')
M2 = F(53*13,4)/A**3
COEFFICIENTS = {'epsilon0':'64/21', 'q_N':'2', 'r_N':'2809/44',
                '1/z':'2915/4', 'epsilon':'8162', 'C_BV*T^(3-A0)':'23'}
PAYLOADS = ('README.md','proof.md','contracts.json','prior-work.json',
            'source-lock.json','check_g6_explicit.py','results.json',
            'error-handoff.json','computation-record.json','computation-handoff.json',
            'verification-ticket.md','validation.json')


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def read_json(path: Path):
    def unique(items):
        out = {}
        for k,v in items:
            need(k not in out, 'duplicate JSON key '+k)
            out[k] = v
        return out
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique)


def ivq(x):
    x = F(x)
    return mp.iv.mpf(x.numerator)/x.denominator


def binary_fraction(t):
    sign, mantissa, exponent, bits = t
    need(bits >= 0, 'nonfinite endpoint')
    n = (-1 if sign else 1)*mantissa
    return F(n*2**exponent) if exponent >= 0 else F(n,2**(-exponent))


def outward(x: F, upper: bool, places: int = 18) -> str:
    scale = 10**places
    n = -((-x.numerator*scale)//x.denominator) if upper else (x.numerator*scale)//x.denominator
    sign = '-' if n < 0 else ''
    n = abs(n)
    return f'{sign}{n//scale}.{n%scale:0{places}d}'


def enclosing(x, radius):
    lo,hi = map(binary_fraction, x._mpi_)
    need(lo <= hi and radius >= 0, 'enclosure ordering')
    return [outward(lo-radius, False),outward(hi+radius, True)]


def coefficients():
    c = [F(0)] + [sum((F(1,k*2**(n-k+1)) for k in range(1,n+1)),F(0))
                     for n in range(1,DEGREE-1)]
    out = [F(0)]*(DEGREE+1)
    for k in range(3,DEGREE+1):
        mag = sum((c[n]/((n+1)*3**(k-n-1)) for n in range(1,k-1)),F(0))/k
        need(0 < mag < F(1,4*k), 'Taylor coefficient envelope')
        out[k] = (-1 if k%2 == 0 else 1)*mag
    return out


def breakpoints(sigma):
    return (2*A,A+B,F(21,106)-sigma,2*B)


def quadrature_error(sigma):
    points = breakpoints(sigma)
    return sum((M2*(r-l)**3/(24*CELLS**2) for l,r in zip(points,points[1:])),F(0))


def taylor_tail():
    return F(5,8)**(DEGREE+1)/(4*(DEGREE+1)*(1-F(5,8)))


def integrate(sigma, coeff):
    points = breakpoints(sigma)
    need(list(points) == sorted(points), 'piece order')
    total, log_only = ivq(0), ivq(0)
    for left,right in zip(points,points[1:]):
        step = (right-left)/CELLS
        acc, base = ivq(0), ivq(0)
        for j in range(CELLS):
            t_exact = left+F(2*j+1,2)*step
            t = ivq(t_exact)
            s = (ivq(F(1,2)-sigma)-t)/ivq(A)
            W = (mp.iv.log((t-ivq(A))/ivq(A)) if t_exact < A+B
                 else mp.iv.log(ivq(B)/(t-ivq(B))))/t
            logpsi = mp.iv.log(s-1)/s
            correction = ivq(0)
            if t_exact < F(21,106)-sigma:
                w = s-4
                for ck in reversed(coeff):
                    correction = correction*w+ck
                correction /= s
            acc += 53*W*(logpsi+correction)
            base += 53*W*logpsi
        total += acc*ivq(step)
        log_only += base*ivq(step)
    E = quadrature_error(sigma)
    return {'sigma':str(sigma), 'breakpoints':list(map(str,points)),
            'midpoints':3*CELLS, 'outer_error':str(E),
            'integral':enclosing(total,E+F(53,6)*taylor_tail()),
            'log_only':enclosing(log_only,E)}


def validate_result(data):
    need(data['schema'] == 'goldbach-g6-explicit-certificate/v1', 'schema')
    need(data['cells_per_piece'] == CELLS and data['degree'] == DEGREE, 'grid/degree')
    need(data['midpoints_total'] == 9*CELLS, 'coverage')
    need(data['dps'] == DPS and data['backend_version'] == '1.3.0', 'precision/backend')
    need(data['M2'] == str(M2) and data['taylor_tail'] == str(taylor_tail()), 'error identity')
    need(len(data['rows']) == 3, 'row count')
    for row,sigma in zip(data['rows'],SIGMAS):
        need(row['sigma'] == str(sigma), 'sigma identity')
        need(row['breakpoints'] == list(map(str,breakpoints(sigma))), 'moving breakpoint')
        need(row['midpoints'] == 3*CELLS and row['outer_error'] == str(quadrature_error(sigma)), 'row error/coverage')
        lo,hi = map(F,row['integral']); blo,bhi = map(F,row['log_only'])
        need(0 < blo < bhi < lo < hi < 2 and hi-lo < F(1,10**6), 'integral bounds')
    lo0,hi0 = map(F,data['rows'][0]['integral'])
    lo1,hi1 = map(F,data['rows'][1]['integral'])
    lo2,hi2 = map(F,data['rows'][2]['integral'])
    need(BASE_FLOOR <= lo0 and TARGET < FIXED_FLOOR <= lo1, 'safe lower floors')
    need(hi2 < TARGET and hi1 < lo0, 'failed large gap / real tradeoff')
    need(data['safe_floors'] == {'log_limit':str(BASE_FLOOR),'fixed_gap':str(FIXED_FLOOR)}, 'floor mutation')
    need(data['count_interval_claimed'] is False and data['independently_verified'] is False, 'authority')
    need(data['global_status'] == 'INCONCLUSIVE', 'global claim')


def compute():
    need(mp.__version__ == '1.3.0', 'requires mpmath1.3.0')
    mp.iv.dps = DPS
    coeff = list(map(ivq,coefficients()))
    result = {'schema':'goldbach-g6-explicit-certificate/v1',
              'backend':'mpmath.iv', 'backend_version':mp.__version__,
              'dps':DPS,'degree':DEGREE,'cells_per_piece':CELLS,'midpoints_total':9*CELLS,
              'M2':str(M2),'taylor_tail':str(taylor_tail()),
              'rows':[integrate(s,coeff) for s in SIGMAS],
              'safe_floors':{'log_limit':str(BASE_FLOOR),'fixed_gap':str(FIXED_FLOOR)},
              'count_interval_claimed':False,'independently_verified':False,'global_status':'INCONCLUSIVE'}
    validate_result(result)
    return result


def primes_upto(n):
    flags = bytearray(b'\1')*(n+1)
    if n >= 1: flags[0:2] = b'\0\0'
    for p in range(2,isqrt(n)+1):
        if flags[p]: flags[p*p:n+1:p] = b'\0'*((n-p*p)//p+1)
    return [p for p in range(2,n+1) if flags[p]]


def phi(n):
    value,m = n,n
    p = 2
    while p*p <= m:
        if m%p == 0:
            value = value//p*(p-1)
            while m%p == 0: m //= p
        p += 1
    if m>1: value = value//m*(m-1)
    return value


def divisors_of_product(primes):
    ds = [1]
    for p in primes: ds += [d*p for d in ds]
    return sorted(ds)


def finite_tests():
    counts = dict(native_AP=0, rebasing=0, unit_modulus=0, injection=0,
                  aggregate_budget=0, true_diagonal=0, measure_diagonal=0,
                  signed_mass=0, signed_main=0, taylor_ODE=0, serialization=0,
                  totient=0, parameter_budget=0)
    ps = primes_upto(1300)
    # Parameter-model data: these are NOT the original power cutoffs or Li errors.
    for N,z,w in itertools.product(range(200,1201,100),(5,7,11),(3,5)):
        Y, X = F(3*N,4), F(3*N,7)
        base = [N-p for p in ps if p < Y]
        small = [p for p in ps if p<z and N%p]
        ds = divisors_of_product(small)
        W = prod(p for p in ps if p<w and N%p)
        P0 = prod(p for p in ps if p<w)
        R = 8*N
        high = [p for p in ps if z<=p<=31 and N%p]
        seen, raw, rebased, delta_list, supports = {}, [], [], [], []
        real_all = real_strict = real_diag = 0
        for p,q in itertools.combinations_with_replacement(high,2):
            m = p*q
            count = sum(n%m==0 and all(n%l for l in small) for n in base)
            real_all += count
            if p==q: real_diag += count
            else: real_strict += count
        need(real_all-real_strict == real_diag >= 0,'real diagonal')
        counts['true_diagonal'] += 1
        for p,q in itertools.combinations(high,2):
            m = p*q; D = F(R,P0*m)
            if D <= 1: continue
            M = sum(n%m == 0 for n in base)
            Xm = X/phi(m); delta = M-Xm
            delta_list.append(delta)
            dlist = [d for d in ds if d < W*D]
            need(1 in dlist,'unit modulus missing')
            supports.append(sum((F(1,phi(d)) for d in dlist),F(0)))
            for d in dlist:
                md = m*d
                need(md<R and gcd(m,d)==1 and md not in seen,'support/injection')
                seen[md]=(p,q,d); counts['injection'] += 1
                c1=sum(n%md==0 for n in base)
                c2=sum((N-r)%md==0 for r in ps if r<Y)
                need(c1==c2 and phi(md)==phi(m)*phi(d),'AP or phi identity')
                r = F(c1)-X/phi(md)
                rm = F(c1)-F(M,phi(d))
                need(rm == r-delta/phi(d),'actual-mass rebase')
                raw.append(abs(r)); rebased.append(abs(rm))
                counts['native_AP'] += 1; counts['rebasing'] += 1
                if d==1:
                    need(r==delta and rm==0,'unit modulus rebase')
                    counts['unit_modulus'] += 1
        E = sum(raw,F(0)); Delta = sum(map(abs,delta_list),F(0))
        H = max(supports,default=F(0))
        need(Delta<=E and sum(rebased,F(0)) <= (1+H)*E,'aggregate rebase')
        counts['aggregate_budget'] += 1
        weights=[F(1,p) for p in high]
        mass=sum(weights,F(0)); diag=sum((x*x for x in weights),F(0))
        strict=sum((x*y for x,y in itertools.combinations(weights,2)),F(0))
        need(2*strict == mass**2-diag,'measure diagonal identity')
        counts['measure_diagonal'] += 1
    for mass,X,V,beta in itertools.product((F(0),F(1),F(10)),
            (F(0),F(1,3),F(12)),(F(0),F(1,3),F(1)),(-F(6),-F(1,2),F(0),F(1),F(6))):
        need(V*beta*mass >= V*beta*X-6*abs(mass-X),'negative main factor')
        counts['signed_mass'] += 1
    for I,delta,q,theta in itertools.product((F(0),F(1,20),F(1,2)),
            (F(0),F(1,10),F(2)),(F(0),F(1,2),F(1)),(F(0),F(1,2),F(1))):
        for Rn in (1-q,1+q):
            need(Rn*(1-theta)*max(F(0),I-delta) >= I-delta-(q+theta)*I,'normalized main')
            counts['signed_main'] += 1
    c = coefficients()
    for n in range(2,DEGREE):
        cn = sum((F(1,k*2**(n-k)) for k in range(1,n)),F(0))
        need(3*(n+1)*c[n+1]+n*c[n] == (-1)**n*cn/n,'Taylor ODE')
        counts['taylor_ODE'] += 1
    mp.iv.dps = DPS
    for x in (F(0),F(1,3),F(-7,9),F(10**30),F(1,2**100)):
        lo,hi = map(binary_fraction,ivq(x)._mpi_)
        need(lo <= x <= hi and F(outward(x,False))<=x<=F(outward(x,True)),'serialization')
        counts['serialization'] += 1
    # Exact Euler-product-based bound: sum 1/phi(n) <=3 harmonic(T).
    s = harmonic = F(0)
    for n in range(1,513):
        s += F(1,phi(n)); harmonic += F(1,n)
        need(s < 3*harmonic,'reciprocal-totient finite bound')
        counts['totient'] += 1
    for budget in map(F,('0.000001','0.000002','0.0001','1')):
        eps0=min(F(1,4),budget*F(21,256))
        eps=min(F(1,200),budget/F(32648))
        need(F(64,21)*eps0+8162*eps <= budget/2,'fixed loss allocation')
        counts['parameter_budget'] += 1
    need(F(53)*B/(2*A)*F(3,2)==F(2809,44),'r coefficient')
    need(53/A+F(53,2)==F(2915,4),'diagonal/coprime coefficient')
    need(F(53,2)/A==F(2809,8),'drift coefficient')
    need(106*77==8162 and 20+3==23,'explicit sieve/rebase coefficients')
    rejected=[]
    def reject(name,ok):
        need(not ok,'negative control accepted: '+name)
        rejected.append(name)
    reject('net_mass_is_not_absolute_mass',abs(F(1)-F(1))==abs(F(1))+abs(-F(1)))
    reject('squareful_phi_not_square',phi(25)==phi(5)**2)
    reject('strict_pair_needs_half',F(1,35)==2*F(1,35))
    reject('measure_diagonal_not_free',2*F(1,35)==(F(1,5)+F(1,7))**2)
    reject('missing_P0_support',143*105<10000)
    need(105 < F(3*10000,143),'support counterexample premise')
    reject('shared_large_prime_filter_needed',5*7*11 != 5*11*7)
    reject('negative_bracket_denominator',-F(1,phi(35)) >= -F(1,35))
    reject('larger_sequence_not_lower_bound',sum(1 for x in (1,2,3) if x%2) <= 1)
    reject('fixed_gap_onset_cannot_be_log_onset',F(1,1000) <= F(1,10**6))
    reject('factorable_bound_not_absolute_sum',abs(F(1)-F(1))==F(2))
    reject('A0_three_does_not_decay',3-3<0)
    reject('swapping_two_large_primes_not_injective',(5,7)==(7,5))
    return {'schema':'goldbach-g6-explicit-finite/v1','counts':counts,
            'finite_cases':sum(counts.values()),'negative_controls':rejected,
            'negative_controls_rejected':len(rejected),
            'AP_model':'N=200..1200 step100,z=5/7/11,w=3/5,upper31,R=8N,Y=3N/4,X=3N/7; synthetic, not Li or BV data',
            'independently_verified':False,'global_status':'INCONCLUSIVE'}


def check():
    data=read_json(ROOT/'results.json'); validate_result(data)
    manifest=read_json(ROOT/'artifact-sha256.json')
    need(set(manifest['sha256'])==set(PAYLOADS),'manifest inventory')
    for name,h in manifest['sha256'].items():
        need(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,'hash '+name)
    c=read_json(ROOT/'contracts.json')
    need(c['fixed_mode']['deficit_coefficients']==COEFFICIENTS,'native contract')
    need(c['global_status']=='INCONCLUSIVE' and c['independent_review']=='pending','contract authority')
    need(c['fixed_mode']['sigma']=='1/1000000' and c['fixed_mode']['kernel_drift']==0,'mode identity')
    tests=finite_tests(); need(tests==read_json(ROOT/'validation.json'),'finite replay')
    rejected=0
    for field,value in [('midpoints_total',12288),('degree',47),('M2','0'),
            ('count_interval_claimed',True),('independently_verified',True),
            ('global_status','PASS'),('safe_floors',{'log_limit':'2','fixed_gap':'2'})]:
        bad=copy.deepcopy(data); bad[field]=value
        try: validate_result(bad)
        except (ValueError,KeyError,TypeError): rejected+=1
        else: raise ValueError('mutation accepted '+field)
    bad=copy.deepcopy(data); bad['rows'][1]['breakpoints'][2]='21/106'
    try: validate_result(bad)
    except (ValueError,KeyError,TypeError): rejected+=1
    else: raise ValueError('moving-breakpoint mutation accepted')
    return {'ok':True,'hashes_checked':len(PAYLOADS),'finite_cases_replayed':tests['finite_cases'],
            'negative_controls_rejected':tests['negative_controls_rejected']+rejected,
            'quadrature_replayed':False,'global_status':'INCONCLUSIVE','mathematical_truth_verified':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    for flag in ('compute','self-test','check','require-global'): g.add_argument('--'+flag,action='store_true')
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    if args.require_global:
        print('REJECT: source/candidate independent review and remaining twelve-term closure are absent.')
        return 1
    data=compute() if args.compute else finite_tests() if args.self_test else check()
    if args.output:
        need(not args.check,'--check does not write')
        with args.output.open('x',encoding='utf-8') as stream:
            stream.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    elif args.compute:
        need(data==read_json(ROOT/'results.json'),'fresh quadrature differs from saved result')
    print(json.dumps(data,ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as exc:
        print('FAIL: '+str(exc),file=sys.stderr)
        raise SystemExit(1)
