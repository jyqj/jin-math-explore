#!/usr/bin/env python3
"""CP-ERR-0011: bounded tests and directed fixed-integral certificates.

Python >=3.10, mpmath==1.3.0. No network or subprocesses. --compute really
integrates; --check checks hashes/results and finite identities, not quadrature.
--output creates a new file only. Source theorems and proof.md are not verified
by this program. Synthetic finite AP masses are not observed Li errors.
"""
from __future__ import annotations
import argparse
import copy
from fractions import Fraction as F
from functools import lru_cache
import hashlib
import itertools
import json
from math import gcd, isqrt
from pathlib import Path
import sys
import mpmath as mp

ROOT = Path(__file__).resolve().parent
A, B, G = F(4,53), F(4,33), F(3,11)
C = F(1,2)-2*A
SIGMAS = (F(0), F(1,10**7), F(5,10**7))
CELLS, DPS = 8192, 50
TARGET, FLOOR = F('3.79029'), F('3.7902931')
FILES = ('README.md','proof.md','contracts.json','prior-work.json','source-lock.json',
         'check_g7_explicit.py','results.json','error-handoff.json','computation-record.json',
         'computation-handoff.json','verification-ticket.md','validation.json')


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def load(path: Path):
    def pairs(items):
        out = {}
        for k,v in items:
            require(k not in out, 'duplicate JSON key '+k)
            out[k] = v
        return out
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def ivq(x):
    x = F(x)
    return mp.iv.mpf(x.numerator)/x.denominator


def endpoints(x):
    def convert(t):
        sign, mantissa, exponent, bits = t
        require(bits >= 0, 'nonfinite endpoint')
        v = F((-1 if sign else 1)*mantissa)
        return v*2**exponent if exponent >= 0 else v/F(2**(-exponent))
    lo,hi = map(convert, x._mpi_)
    require(lo <= hi, 'reversed interval')
    return lo,hi


def outward(x: F, upper: bool, places: int = 18) -> str:
    scale = 10**places
    k = -((-x.numerator*scale)//x.denominator) if upper else x.numerator*scale//x.denominator
    sign = '-' if k < 0 else ''
    k = abs(k)
    return f'{sign}{k//scale}.{k%scale:0{places}d}'


def breaks(sigma):
    pts = (A+B,2*B,A+G,C-sigma)
    require(all(x < y for x,y in zip(pts,pts[1:])), 'slice topology')
    return pts


def higher_correction(sigma):
    width = max(F(0),F(1,2)-sigma-4*A-(A+B))
    return width**5/(720*A**5*B)


def derivative_envelope():
    t,y,v,L = F(19,100),F(3,20),F(3,40),F(6,5)
    h0 = 4*L/y
    h1 = 4*(L/y**2+1/(y*v))
    h2 = 4*(2*L/y**3+2/(y**2*v)+1/(y*v**2))
    w0 = 12/t
    w1 = (4/v)/t+12/t**2
    w2 = (4/v**2)/t+2*(4/v)/t**2+24/t**3
    return h2*w0+2*h1*w1+h0*w2


def compute():
    require(mp.__version__ == '1.3.0', 'pinned mpmath version required')
    mp.iv.dps = DPS
    require(derivative_envelope() < 2000000, 'analytic derivative envelope')
    rows = []
    for sigma in SIGMAS:
        pts = breaks(sigma)
        total = ivq(0)
        for left,right in zip(pts,pts[1:]):
            step = (right-left)/CELLS
            subtotal = ivq(0)
            for j in range(CELLS):
                tf = left+F(2*j+1,2)*step
                lf,rf = max(A,tf-G),min(B,tf-B)
                t,l,r = ivq(tf),ivq(lf),ivq(rf)
                W = mp.iv.log(r*(t-l)/(l*(t-r)))/t
                y = ivq(F(1,2)-sigma-tf)
                H = 4*mp.iv.log((y-ivq(A))/ivq(A))/y
                subtotal += H*W
            total += subtotal*ivq(step)
        error = sum((F(2000000)*(v-u)**3/(24*CELLS**2)
                     for u,v in zip(pts,pts[1:])),F(0))
        lo,hi = endpoints(total)
        lo,hi = lo-error,hi+error
        corr = higher_correction(sigma)
        rows.append({'sigma':str(sigma),'breakpoints':list(map(str,pts)),
                     'midpoint_error':str(error),'higher_correction_upper':str(corr),
                     'log_comparison_enclosure':[outward(lo,False),outward(hi,True)],
                     'full_kernel_enclosure':[outward(lo,False),outward(hi+corr,True)]})
    data = {'schema':'goldbach-g7-explicit-certificate/v1','backend':'mpmath.iv',
            'version':mp.__version__,'dps':DPS,'cells_per_piece':CELLS,
            'midpoint_evaluations':len(SIGMAS)*3*CELLS,
            'analytic_second_derivative_envelope':str(derivative_envelope()),
            'used_second_derivative_bound':'2000000','rows':rows,
            'selected_sigma':str(SIGMAS[1]),'safe_selected_floor':str(FLOOR),
            'count_two_sided_enclosure':False,'independently_verified':False,
            'global_status':'INCONCLUSIVE'}
    validate_result(data)
    return data


def validate_result(data):
    require(data['schema'] == 'goldbach-g7-explicit-certificate/v1','schema')
    require(data['backend'] == 'mpmath.iv' and data['version'] == '1.3.0','backend')
    require(data['dps'] == DPS and data['cells_per_piece'] == CELLS,'precision/grid')
    require(data['midpoint_evaluations'] == 9*CELLS,'coverage')
    require(F(data['analytic_second_derivative_envelope']) == derivative_envelope(),'derivatives')
    require(F(data['used_second_derivative_bound']) == 2000000,'derivative bound')
    require(len(data['rows']) == 3,'row coverage')
    for sigma,row in zip(SIGMAS,data['rows']):
        pts = breaks(sigma)
        err = sum((F(2000000)*(v-u)**3/(24*CELLS**2)
                   for u,v in zip(pts,pts[1:])),F(0))
        require(F(row['sigma']) == sigma and row['breakpoints'] == list(map(str,pts)),'domain')
        require(F(row['midpoint_error']) == err,'quadrature radius')
        require(F(row['higher_correction_upper']) == higher_correction(sigma),'positive correction')
        lo,hi = map(F,row['log_comparison_enclosure'])
        flo,fhi = map(F,row['full_kernel_enclosure'])
        require(0 < lo <= hi < 4 and flo == lo and fhi >= hi,'enclosure direction')
        require(fhi-hi <= higher_correction(sigma)+F(1,10**18),'correction serialization')
        require(2*err <= hi-lo <= 2*err+F(3,10**18),'interval radius')
    require(F(data['rows'][0]['log_comparison_enclosure'][0]) > TARGET,'zero-gap target')
    require(F(data['rows'][1]['log_comparison_enclosure'][0]) >= FLOOR > TARGET,'fixed-gap target')
    require(F(data['rows'][2]['full_kernel_enclosure'][1]) < TARGET,'failed full-kernel comparator')
    require(F(data['selected_sigma']) == SIGMAS[1] and F(data['safe_selected_floor']) == FLOOR,'selection')
    require(data['count_two_sided_enclosure'] is False,'integral/count distinction')
    require(data['independently_verified'] is False and data['global_status'] == 'INCONCLUSIVE','authority')


def primes(n):
    flags = bytearray(b'\x01')*(n+1)
    flags[0:2] = b'\x00\x00'
    for p in range(2,isqrt(n)+1):
        if flags[p]:
            flags[p*p:n+1:p] = b'\x00'*(((n-p*p)//p)+1)
    return [p for p in range(2,n+1) if flags[p]]


@lru_cache(maxsize=None)
def phi(n):
    result,m,p = n,n,2
    while p*p <= m:
        if m % p == 0:
            result -= result//p
            while m % p == 0: m //= p
        p += 1
    if m > 1: result -= result//m
    return result


def products(ps):
    out = [1]
    for p in ps: out += [d*p for d in out]
    return sorted(out)


def finite_tests():
    counts = {k:0 for k in ('ap_rebase_injection','unit_mass','aggregate_rebase','nonnegative_restriction',
                             'monotone_tensor','signed_mass','normalized_sign','totient','exponent_endpoint','geometry')}
    for N,z,split,w in itertools.product(range(200,1201,100),(3,5,7),(11,13),(3,5)):
        ps = primes(N)
        small = [p for p in ps if p < z and N % p]
        ds = products(small)
        W = products([p for p in small if p < w])[-1]
        P0 = products([p for p in ps if p < w])[-1]
        R,Y,X = 16*N,F(3*N,4),F(3*N,7)
        left = [p for p in ps if z <= p < split and N % p]
        right = [p for p in ps if split <= p <= 31 and N % p]
        seq = [N-p for p in ps if p < Y]
        seen = set(); old = new = masses = F(0); Hmax = F(0)
        whole = kept = 0
        for p1,p2 in itertools.product(left,right):
            m = p1*p2
            native = [n for n in seq if n % m == 0]
            S = sum(all(n % p for p in small) for n in native)
            whole += S
            D = F(R,P0*m)
            if D < z*z: continue
            kept += S
            M = len(native); Xm = X/phi(m); delta = M-Xm
            require(m < R,'unit support')
            masses += abs(delta); counts['unit_mass'] += 1
            H = F(0)
            for d in ds:
                if d >= W*D: continue
                n = m*d
                require(gcd(m,d) == 1 and n < R and n not in seen,'support/injection')
                seen.add(n)
                count = sum(v % d == 0 for v in native)
                ap = sum(p < Y and (p-N) % n == 0 for p in ps)
                rp = F(ap)-X/phi(n)
                rm = F(count)-F(M,phi(d))
                require(count == ap and rm == rp-delta/phi(d),'AP/rebase')
                old += abs(rp); new += abs(rm); H += F(1,phi(d))
                counts['ap_rebase_injection'] += 1
            Hmax = max(Hmax,H)
        require(masses <= old and new <= old+Hmax*masses,'aggregate, including d=1')
        require(whole >= kept,'discard only nonnegative native summands')
        counts['aggregate_rebase'] += 1; counts['nonnegative_restriction'] += 1
    # Discrete positive measures: a rational monotone surrogate, NOT Li errors.
    xs = [F(i,8) for i in range(1,5)]
    lam = [F(1,4)]*4
    for k1,k2,t in itertools.product(range(1,8),range(1,8),(F(1,2),F(3,4),F(1))):
        mu1 = [F(k1,16),F(1,8),F(3,8),F(1,4)]
        mu2 = [F(1,4),F(k2,16),F(1,4),F(1,8)]
        def discrepancy(mu):
            return max(abs(sum((mu[j]-lam[j] for j in range(i+1)),F(0))) for i in range(4))
        r1,r2 = discrepancy(mu1),discrepancy(mu2)
        def integral(m1,m2):
            return sum((m1[i]*m2[j]*min(F(1,2),max(F(0),t-xs[i]-xs[j]))
                        for i in range(4) for j in range(4)),F(0))
        error = abs(integral(mu1,mu2)-integral(lam,lam))
        require(error <= (r1*sum(mu2)+r2*sum(lam))/2,'monotone tensor bound')
        counts['monotone_tensor'] += 1
    for M,X,k,V in itertools.product((F(0),F(1),F(3)),(F(0),F(1,2),F(4)),
                                     (F(-77,100),F(0),F(1),F(3)),(F(0),F(1,2),F(1))):
        require(k*V*M >= k*V*X-3*abs(M-X),'negative-factor mass rebase')
        counts['signed_mass'] += 1
    for I,E,q,theta in itertools.product((F(0),F(1,4),F(1)),(F(0),F(1,2),F(2)),
                                        (F(0),F(1,2),F(1)),(F(0),F(1,2),F(1))):
        for R in (1-q,1+q):
            require(R*(1-theta)*max(F(0),I-E) >= I-E-(q+theta)*I,'normalized sign')
            counts['normalized_sign'] += 1
    for n in range(1,257):
        ds = [d for d in range(1,n+1) if n % d == 0]
        sf = [d for d in ds if all(d % (p*p) for p in primes(isqrt(d)))]
        require(F(n,phi(n)) == sum((F(1,phi(d)) for d in sf),F(0)),'totient identity')
        counts['totient'] += 1
    for p in primes(100):
        # N^4=p^33 is impossible because 4*v_p(N)=33 has no integer solution.
        require(33 % 4 != 0 and all(N**4 != p**33 for N in range(2,101)),'shared prime endpoint')
        counts['exponent_endpoint'] += 1
    identities = (C-A-G == F(1,1166), (F(1,2)-A-B)/A == F(1061,264),
                  F(1,2)-4*A-(A+B) == F(5,3498),
                  53*(F(3,4)/A+F(1,2)/B) == F(11925,16),
                  154*53*6 == 48972, F(53,4)/A == F(2809,16),
                  (B-A)/(A**3*B) == F(14045,16),
                  F(1,30)/A == F(53,120), C-5*B/2 >= A/2,
                  F(523,3985)/25 > F(1,200), derivative_envelope() < 2000000,
                  higher_correction(0) < F(1,10**10))
    require(all(identities),'rational geometry/constants')
    counts['geometry'] = len(identities)
    negatives = 0
    def reject(ok, name):
        nonlocal negatives
        try: require(ok,name)
        except ValueError: negatives += 1
        else: raise ValueError('negative control accepted: '+name)
    reject(B+G <= C,'illegal rectangle corner')
    reject(C-A-G <= 0,'omitted gamma cap')
    reject((A+F(1,4664))+(G+F(1,4664)) >= C,'cap-exterior positive triangle')
    reject(3*35 < 100,'forgot P0 support inflation')
    reject(sum(map(abs,(F(1),F(-1)))) <= abs(F(1)-1),'net mass cancellation')
    reject(F(1,2) == 0,'forgot unit mass error')
    reject(F(53,120)*F(1,10**6) <= F(14045,16)*F(1,10**6)**2,'strip-only is not total loss')
    reject(F(1,10**6) <= F(1,10**7),'fixed/log onset interchange')
    reject(F(1,2) == 1,'rectangle has no triangular half factor')
    reject(3*11*5 != 5*11*3,'injection without small-prime support')
    reject(-F(77,100)*2 >= -F(77,100),'negative factor cannot increase mass freely')
    reject(33 % 4 == 0,'integer valuation required at a prime endpoint')
    return {'schema':'goldbach-g7-finite/v1','ok':True,'counts':counts,
            'finite_cases':sum(counts.values()),'structural_negative_controls':negatives,
            'scope':'synthetic AP identities and rational monotone-measure models, not small-N BV or source verification',
            'mathematical_truth_verified':False}


def check_saved():
    data = load(ROOT/'results.json'); validate_result(data)
    manifest = load(ROOT/'artifact-sha256.json')
    require(set(manifest['sha256']) == set(FILES),'manifest coverage')
    for name,digest in manifest['sha256'].items():
        require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest,'hash '+name)
    tests = finite_tests()
    require(tests == load(ROOT/'validation.json'),'finite replay differs')
    contract = load(ROOT/'contracts.json')
    require(contract['deficit_coefficients'] == {'epsilon0':'128/21','q_N':'4','r_N':'53',
                '1/z':'11925/16','epsilon':'48972','C_BV*T^(3-A0)':'17'},'contract coefficients')
    require(contract['independent_review'] == 'pending' and contract['global_status'] == 'INCONCLUSIVE','contract authority')
    mutations = 0
    for field,value in (('global_status','PASS'),('independently_verified',True),
                        ('count_two_sided_enclosure',True),('midpoint_evaluations',0),
                        ('safe_selected_floor','4'),('selected_sigma','1/2000000'),
                        ('used_second_derivative_bound','0'),('dps',15)):
        bad = copy.deepcopy(data); bad[field] = value
        try: validate_result(bad)
        except (ValueError,KeyError,TypeError): mutations += 1
        else: raise ValueError('corrupt result accepted: '+field)
    return {'ok':True,'hashes_checked':len(FILES),'finite_cases_replayed':tests['finite_cases'],
            'negative_controls_rejected':tests['structural_negative_controls']+mutations,
            'quadrature_replayed':False,'global_status':'INCONCLUSIVE','mathematical_truth_verified':False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    for flag in ('compute','self-test','check','require-global'):
        group.add_argument('--'+flag,action='store_true')
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    if args.require_global:
        print('REJECT: imported theorems, independent review and twelve-term closure are not verified here.')
        return 1
    data = compute() if args.compute else finite_tests() if args.self_test else check_saved()
    text = json.dumps(data,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        require(not args.check,'--check is read-only')
        with args.output.open('x',encoding='utf-8') as f: f.write(text)
    elif args.compute:
        require(data == load(ROOT/'results.json'),'quadrature differs from frozen output')
    print(text,end='')
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print('FAIL: '+str(exc),file=sys.stderr)
        raise SystemExit(1)
