#!/usr/bin/env python3
"""Reproduce the CP-ERR-0004 G6 integral certificate, not a Goldbach proof.

Python >=3.10, mpmath ==1.3.0. No network, shell, CAS or prime database.
--compute recomputes and compares frozen results; --output creates a NEW file.
--check checks saved evidence/hashes only. --require-global deliberately fails.
The analytic bounds and source assumptions are in proof.md; code is not a verifier.
"""
from __future__ import annotations
import argparse
from fractions import Fraction as F
import hashlib
import itertools
import json
from pathlib import Path
import sys
import mpmath as mp

ROOT = Path(__file__).resolve().parent
A, B = F(4, 53), F(4, 33)
BREAKS = (2*A, A+B, F(21, 106), 2*B)
CELLS, DEGREE, DPS = 4096, 48, 50
H2 = F(53*13, 4)/A**3
TARGET, FLOOR = F('1.63357'), F('1.6335733')
FILES = ('README.md', 'proof.md', 'contracts.json', 'prior-work.json',
         'source-lock.json', 'check_g6.py', 'results.json', 'error-handoff.json',
         'computation-handoff.json', 'verification-ticket.md', 'validation.json')


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def ivq(x: F | int):
    x = F(x)
    return mp.iv.mpf(x.numerator)/x.denominator


def binary_fraction(t: tuple[int, int, int, int]) -> F:
    """mpmath 1.3.0 exact finite mpf tuple; no float endpoint conversion."""
    sign, mantissa, exponent, bits = t
    require(bits >= 0, 'nonfinite interval endpoint')
    value = F((-1 if sign else 1)*mantissa)
    return value*2**exponent if exponent >= 0 else value/F(2**(-exponent))


def bounds(x) -> tuple[F, F]:
    lo, hi = (binary_fraction(t) for t in x._mpi_)
    require(lo <= hi, 'reversed interval')
    return lo, hi


def decimal_out(x: F, upper: bool, places: int = 18) -> str:
    scale = 10**places
    k = -((-x.numerator*scale)//x.denominator) if upper else (x.numerator*scale)//x.denominator
    sign = '-' if k < 0 else ''
    k = abs(k)
    return f'{sign}{k//scale}.{k%scale:0{places}d}'


def enclosure(x, radius: F) -> list[str]:
    lo, hi = bounds(x)
    return [decimal_out(lo-radius, False), decimal_out(hi+radius, True)]


def t_coefficients(degree: int) -> list[F]:
    c = [F(0)] + [sum((F(1, k*2**(n-k+1)) for k in range(1, n+1)), F(0))
                      for n in range(1, degree-1)]
    result = [F(0)]*(degree+1)
    for k in range(3, degree+1):
        mag = sum((c[n]/((n+1)*3**(k-n-1)) for n in range(1, k-1)), F(0))/k
        require(0 < mag < F(1, 4*k), 'Taylor coefficient bound')
        result[k] = (-1 if k % 2 == 0 else 1)*mag
    return result


def validate_result(data: dict) -> None:
    require(data['schema'] == 'goldbach-g6-certificate/v1', 'schema')
    require(data['cells_per_piece'] == CELLS and data['taylor_degree'] == DEGREE, 'grid/degree')
    require(data['midpoint_evaluations'] == 3*CELLS, 'coverage')
    require(data['breakpoints'] == list(map(str, BREAKS)), 'breakpoint identity')
    expected_error = sum((H2*(v-u)**3/(24*CELLS**2) for u, v in zip(BREAKS, BREAKS[1:])), F(0))
    tail = F(5, 8)**(DEGREE+1)/(4*(DEGREE+1)*(1-F(5, 8)))
    require(F(data['outer_error']) == expected_error, 'outer error')
    require(F(data['outer_second_derivative_bound']) == H2, 'derivative bound')
    require(F(data['taylor_uniform_tail']) == tail, 'Taylor tail')
    require(F(data['integrated_tail_allowance']) == F(53, 6)*tail, 'integrated tail')
    lo, hi = map(F, data['g6_enclosure'])
    blo, bhi = map(F, data['log_only_enclosure'])
    require(0 < blo <= bhi < TARGET < FLOOR <= lo < hi < 2, 'enclosure/target direction')
    require(hi-lo < F(1, 1000000), 'certificate too wide')
    require(F(data['safe_floor']) == FLOOR, 'floor mutation')
    require(F(data['floor_gain_over_printed']) == FLOOR-TARGET, 'gain')
    require(data['actual_G6_two_sided_enclosure'] is False, 'integral/count distinction')
    require(data['global_paper_closure'] == 'INCONCLUSIVE', 'unauthorized global closure')
    require(data['independently_verified'] is False, 'unauthorized verification')


def compute() -> dict:
    require(mp.__version__ == '1.3.0', 'requires pinned mpmath 1.3.0')
    mp.iv.dps = DPS
    coeff = [ivq(x) for x in t_coefficients(DEGREE)]
    total, base = ivq(0), ivq(0)
    for left, right in zip(BREAKS, BREAKS[1:]):
        step = (right-left)/CELLS
        part, basepart = ivq(0), ivq(0)
        for j in range(CELLS):
            tf = left + F(2*j+1, 2)*step
            t = ivq(tf)
            s = (ivq(F(1, 2))-t)/ivq(A)
            weight = (mp.iv.log((t-ivq(A))/ivq(A)) if tf < A+B
                      else mp.iv.log(ivq(B)/(t-ivq(B))))/t
            logpsi = mp.iv.log(s-1)/s
            correction = ivq(0)
            if tf < F(21, 106):
                w = s-4
                for ck in reversed(coeff):
                    correction = correction*w+ck
                correction /= s
            basepart += 53*weight*logpsi
            part += 53*weight*(logpsi+correction)
        total += part*ivq(step)
        base += basepart*ivq(step)
    outer = sum((H2*(v-u)**3/(24*CELLS**2) for u, v in zip(BREAKS, BREAKS[1:])), F(0))
    tail = F(5, 8)**(DEGREE+1)/(4*(DEGREE+1)*(1-F(5, 8)))
    tail_cost = F(53, 6)*tail  # 53 * integral W <= 53/2; divide by s>=3
    data = {
        'schema': 'goldbach-g6-certificate/v1',
        'object': 'g6=53 integral_triangle psi((1/2-u-v)/a) du dv/(u v)',
        'backend': 'mpmath.iv', 'backend_version': mp.__version__, 'decimal_precision': DPS,
        'cells_per_piece': CELLS, 'midpoint_evaluations': 3*CELLS,
        'breakpoints': list(map(str, BREAKS)), 'taylor_degree': DEGREE,
        'outer_second_derivative_bound': str(H2), 'outer_error': str(outer),
        'taylor_uniform_tail': str(tail), 'integrated_tail_allowance': str(tail_cost),
        'g6_enclosure': enclosure(total, outer+tail_cost),
        'log_only_enclosure': enclosure(base, outer),
        'safe_floor': str(FLOOR), 'floor_gain_over_printed': str(FLOOR-TARGET),
        'actual_G6_two_sided_enclosure': False,
        'global_paper_closure': 'INCONCLUSIVE', 'independently_verified': False
    }
    validate_result(data)
    return data


def self_test() -> dict:
    mp.iv.dps = DPS
    for q in (F(0), F(-7, 9), F(1, 3), F(10)**30, F(1, 2**100)):
        lo, hi = bounds(ivq(q))
        require(lo <= q <= hi, 'binary interval conversion')
        require(F(decimal_out(q, False)) <= q <= F(decimal_out(q, True)), 'decimal outward conversion')
    c = t_coefficients(DEGREE)
    require(c[3] == F(1, 36) and c[4] == -F(1, 48), 'first Taylor coefficients')
    # Different exact identity: (3+w)T'(w) = integral_0^w j(2+x)dx.
    for n in range(2, DEGREE):
        cn = sum((F(1,k*2**(n-k)) for k in range(1,n)), F(0))
        require(3*(n+1)*c[n+1]+n*c[n] == (-1)**n*cn/n, 'Taylor ODE identity')
    require(53*B/(2*A)*F(3,2) == F(2809,44), 'PNT coefficient')
    require(53/A+F(53,2) == F(2915,4), 'coprime plus diagonal coefficient')
    require(F(53,2)/A == F(2809,8), 'drift coefficient')
    require(53*2*4*F(1,2) == 212, 'sieve penalty coefficient')
    require((F(1,2)-2*B)/A == F(901,264), 's minimum')
    require((F(1,2)-2*A)/A == F(37,8), 's maximum')
    require(F(1,2)-2*B-3*A == F(109,3498), 'compact-domain h bound')
    require(F(1,2)-2*B-2*A == F(373,3498), 'legal-domain h bound')
    require(H2 < 500000, 'outer derivative envelope')
    require(F(53,33) < F(13,8), 'log(53/33)<1/2 via exp series')
    # Finite factorization oracle, not enumeration of Goldbach representations.
    primes = (2,3,5,7,11,13,17,19,23,29,31)
    injectivity_cases = 0
    for z in (5,7,11,13):
        small = [p for p in primes if p < z]
        large = [p for p in primes if p >= z][:4]
        for N in (30,42,210,2310):
            small_good = [p for p in small if N % p]
            large_good = [p for p in large if N % p]
            seen = {}
            for p1,p2 in itertools.combinations(large_good,2):
                for mask in range(1 << len(small_good)):
                    d = 1
                    for k,p in enumerate(small_good):
                        if mask >> k & 1: d *= p
                    n = p1*p2*d
                    require(n not in seen, 'modulus collision')
                    seen[n] = (p1,p2,d)
                    injectivity_cases += 1
    weights = [F(1,p) for p in (5,7,11,13)]
    ordered = sum((u*v for u in weights for v in weights), F(0))
    strict = sum((weights[i]*weights[j] for i in range(4) for j in range(i+1,4)), F(0))
    diag = sum((u*u for u in weights), F(0))
    require(2*strict == ordered-diag, 'strict triangle identity')
    sign_cases = 0
    # Main nonnegative, penalty upper bounded separately, including I-D<0.
    for I,D,q,theta,e in itertools.product((F(0),F(1,20),F(1,2)),
            (F(0),F(1,10),F(2)), (F(0),F(1,2),F(1)),
            (F(0),F(1,2),F(1)), (F(0),F(1,10),F(2))):
        for R in (1-q,1+q):
            U = max(F(0),I-D)
            lhs = R*(1-theta)*(U-e)
            rhs = I-D-(q+theta)*I-(1+q)*e
            require(lhs >= rhs, 'separated lower main / upper penalty')
            sign_cases += 1
    negative_controls = 0
    def reject(test):
        nonlocal negative_controls
        try:
            test()
        except (ValueError, KeyError, TypeError):
            negative_controls += 1
        else:
            raise ValueError('negative control accepted')
    reject(lambda: require(2*strict == ordered, 'missing diagonal'))
    reject(lambda: require(strict == ordered-diag, 'missing half'))
    reject(lambda: require(F(1,2)-2*B-F(1,5) >= 2*A, 'illegal sieve level'))
    reject(lambda: require(25 % 5 != 0, 'squareful modulus cannot use mu^2=1'))
    reject(lambda: require((F(1)-F(1,2))*(-1) <= (F(1)+F(1,2))*(-1), 'negative combined factor'))
    reject(lambda: require(1 <= 0, 'a larger set supplies no lower bound for its subset'))
    reject(lambda: require(F('0.00172') == F('0.00172')-4*F('0.0004'), 'margin is not reserve'))
    reject(lambda: require(F(1,100)*100 < F(1,2), 'eta*C(eta) need not vanish'))
    return {'schema':'goldbach-g6-self-tests/v1', 'ok':True,
            'interval_conversion_cases':5, 'taylor_coefficients_checked': DEGREE-2, 'taylor_ode_identities': DEGREE-2,
            'injectivity_cases':injectivity_cases, 'signed_cases':sign_cases,
            'negative_controls_rejected':negative_controls,
            'mathematical_truth_verified':False,
            'scope':'finite algebra/arithmetic regression tests, not source theorem verification'}


def check_saved() -> dict:
    data = json.loads((ROOT/'results.json').read_text())
    validate_result(data)
    manifest = json.loads((ROOT/'artifact-sha256.json').read_text())
    require(set(manifest['sha256']) == set(FILES), 'manifest coverage')
    for name, expected in manifest['sha256'].items():
        require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, 'hash mismatch '+name)
    contract = json.loads((ROOT/'contracts.json').read_text())
    require(contract['global_status'] == 'INCONCLUSIVE', 'global contract')
    require(contract['independent_review'] == 'pending', 'review status')
    require(contract['source_gate']['uniform_Cs'] == 'assumption_not_discharged', 'source gate')
    require(contract['deficit_coefficients'] == {
        'epsilon0':'64/21', 'q_N':'2', 'r_N':'2809/44', '1/z':'2915/4',
        'h':'2809/8', 'e_star':'212', 'L*C_BV*logN^(2-A0)':'2'}, 'native coefficients')
    tests = self_test()
    require(tests == json.loads((ROOT/'validation.json').read_text()), 'saved self tests')
    mutations = 0
    for field,value in (('safe_floor','2'), ('global_paper_closure','PASS'),
                        ('actual_G6_two_sided_enclosure',True), ('midpoint_evaluations',4096),
                        ('g6_enclosure',['1.6335734','1.6335732']), ('outer_error','0')):
        bad = dict(data); bad[field] = value
        try: validate_result(bad)
        except (ValueError,KeyError,TypeError): mutations += 1
        else: raise ValueError('mutated result accepted')
    return {'ok':True, 'hashes_checked':len(FILES),
            'negative_controls_rejected':tests['negative_controls_rejected']+mutations,
            'full_quadrature_executed':False, 'global_paper_closure':'INCONCLUSIVE',
            'mathematical_truth_verified':False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    for flag in ('compute','check','self-test','require-global'):
        group.add_argument('--'+flag, action='store_true')
    parser.add_argument('--output', type=Path, help='create new output only; never modify frozen evidence')
    args = parser.parse_args()
    if args.require_global:
        print('REJECT: source uniformity, other eleven terms, and independent/global reconciliation are unclosed.')
        return 1
    data = compute() if args.compute else (self_test() if args.self_test else check_saved())
    if args.output:
        require(not args.check, '--check does not write')
        with args.output.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    elif args.compute:
        require(data == json.loads((ROOT/'results.json').read_text()), 'fresh computation differs from frozen output')
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print('FAIL: '+str(exc), file=sys.stderr)
        raise SystemExit(1)
