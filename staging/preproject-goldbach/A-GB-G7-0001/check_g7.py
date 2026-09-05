#!/usr/bin/env python3
"""G7: exact parameter checks and directed interval midpoint certificate.

The result encloses the comparison integral I0, NOT the full G7 coefficient.
The quadrature remainder uses the piecewise |(H W)''| <= 2,000,000 proof in
proof.md. This script does not verify that proof, the sieve, BV, or Goldbach.
Requires mpmath==1.3.0; tested with Python 3.13.5.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from fractions import Fraction as Q
from pathlib import Path
import mpmath
from mpmath import iv

ROOT = Path(__file__).resolve().parent
ALPHA, BETA, GAMMA = Q(4, 53), Q(4, 33), Q(3, 11)
C = Q(1, 2) - 2 * ALPHA
TARGET = Q(379029, 100000)
N = 8192
D2 = Q(2000000)
DPS = 50
POINTS = [ALPHA+BETA, 2*BETA, ALPHA+GAMMA, C]


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def exact_checks() -> dict:
    a, b, g = ALPHA, BETA, GAMMA
    need(0 < a < b < g < C, 'parameter ordering')
    need(all(x < y for x, y in zip(POINTS, POINTS[1:])), 'slice ordering')
    width = C-a-g
    need(width == Q(1,1166), 'missing cap wedge width')
    need(b+g-C == Q(157,3498), 'old rectangle overrun')
    need((Q(1,2)-a-b)/a == Q(1061,264), 'maximum sieve parameter')
    strip = (b-a)/(a**3*b)
    shift = 4/a**2*(b/a-1)*(g/b-1)
    cap = width**3/(3*a**3*g)
    need(strip == Q(14045,16), 'strip coefficient')
    need(shift == Q(70225,132), 'shift coefficient')
    need(cap == Q(1,557568), 'cap surplus bound')
    # Elementary exp-series bounds used for log(smax-1)<6/5 and -log(3/40)<3.
    def exp_partial(x: Q, k: int) -> Q:
        term = total = Q(1)
        for j in range(1, k+1):
            term *= x/j
            total += term
        return total
    need(exp_partial(Q(6,5),4) > Q(797,264), 'log bound')
    need(exp_partial(Q(3),4) > Q(40,3), 'argument log bound')
    need(Q(1061,797)-Q(6,5)-Q(5,1584)>0, 'fhat monotonicity bound')
    # Rational evaluation of the analytic derivative envelope (not its proof).
    t0,y0,z0,L0 = Q(19,100),Q(3,20),Q(3,40),Q(6,5)
    H0 = 4*L0/y0
    H1 = 4*(L0/y0**2+1/(y0*z0))
    H2 = 4*(2*L0/y0**3+2/(y0**2*z0)+1/(y0*z0**2))
    A0,A1,A2 = Q(12),4/z0,4/z0**2
    W0 = A0/t0
    W1 = A1/t0+A0/t0**2
    W2 = A2/t0+2*A1/t0**2+2*A0/t0**3
    envelope = H2*W0+2*H1*W1+H0*W2
    need(envelope == Q(333783040000,185193) < D2, 'second derivative envelope')
    # Test slice endpoint formulas on rational representatives including breaks.
    for lo,hi in zip(POINTS,POINTS[1:]):
        for t in (lo, (lo+hi)/2, hi):
            left,right = max(a,t-g),min(b,t-b)
            need(left<=right, 'nonempty slice')
            need(a<=left<=right<=b and b<=t-right<=t-left<=g, 'rectangle slice')
    return {
        'alpha':str(a),'beta':str(b),'gamma':str(g),'cutoff':str(C),
        's_max':'1061/264','rectangle_overrun':'157/3498',
        'missing_cap_width':str(width),'cap_surplus_upper':str(cap),
        'strip_coefficient':str(strip),'shift_coefficient_upper':str(shift),
        'derivative_envelope_rational':str(envelope),'derivative_bound':str(D2),
        'slice_breakpoints':[str(x) for x in POINTS],
    }


def interval(q: Q):
    return iv.mpf(q.numerator)/q.denominator


def endpoint_fraction(t: tuple) -> Q:
    sign, mantissa, exponent, bitcount = t
    need(bitcount >= 0, 'nonfinite interval endpoint')
    v = Q(mantissa)*(Q(2)**exponent)
    return -v if sign else v


def decimal_outward(x: Q, digits: int, upper: bool) -> str:
    scale = 10**digits
    numerator = x.numerator*scale
    k = -((-numerator)//x.denominator) if upper else numerator//x.denominator
    sign = '-' if k<0 else ''
    k = abs(k)
    return f'{sign}{k//scale}.{k%scale:0{digits}d}'


def compute() -> dict:
    constants = exact_checks()
    need(mpmath.__version__ == '1.3.0', 're-lock mpmath version before recomputing')
    iv.dps = DPS
    a,b,g = map(interval,(ALPHA,BETA,GAMMA))
    half = interval(Q(1,2))
    quadrature = iv.mpf(0)
    for piece,(lo,hi) in enumerate(zip(POINTS,POINTS[1:])):
        step = (hi-lo)/N
        subtotal = iv.mpf(0)
        for k in range(N):
            tq = lo+(Q(2*k+1,2)*step)
            t = interval(tq)
            if piece == 0:
                left,right = a,t-b
            elif piece == 1:
                left,right = a,b
            else:
                left,right = t-g,b
            weight = iv.log(right*(t-left)/(left*(t-right)))/t
            H = 4*iv.log((half-a-t)/a)/(half-t)
            subtotal += H*weight
        quadrature += interval(step)*subtotal
    qlo,qhi = (endpoint_fraction(t) for t in quadrature._mpi_)
    error = D2*sum((hi-lo)**3 for lo,hi in zip(POINTS,POINTS[1:]))/(24*N**2)
    lo,hi = qlo-error,qhi+error
    need(lo > TARGET, 'comparison integral lower endpoint did not beat target')
    return {
        'schema':'jin-math-g7-certificate/v1','attempt_id':'A-GB-G7-0001',
        'scope':'comparison_integral_I0_and_exact_parameter_checks',
        'method':'directed_interval_midpoints_plus_analytic_second_derivative_remainder',
        'backend':{'python':sys.version.split()[0],'mpmath':mpmath.__version__,'iv_dps':DPS},
        'subintervals_per_piece':N,'pieces':3,'midpoint_evaluations':3*N,
        'constants':constants,
        'quadrature_interval_binary':[list(t) for t in quadrature._mpi_],
        'analytic_error_exact':str(error),
        'analytic_error_upper_decimal':decimal_outward(error,20,True),
        'I0_interval_outward_decimal':[decimal_outward(lo,18,False),decimal_outward(hi,18,True)],
        'target_exact':str(TARGET),
        'certified_margin_lower_decimal':decimal_outward(lo-TARGET,18,False),
        'lower_endpoint_above_target':True,
        'derivative_bound_proof':'proof.md#5-piecewise-quadrature-certificate',
        'trust_basis':['mpmath.iv outward arithmetic and log','Python exact integer/Fraction arithmetic','the analytic derivative-bound proof and I0<=g_R derivation in proof.md'],
        'independent_verification':False,
        'cannot_imply':['Does not enclose the full g_R from above: the nonnegative T(s) correction was omitted.','Does not prove the sieve/BV inputs or the transfer from the integral to G7.','Does not settle the twelve-term error budget, Li-Liu theorem, or binary Goldbach.'],
    }


def verify_saved() -> dict:
    r = json.loads((ROOT/'results.json').read_text(encoding='utf-8'))
    need(r['constants']==exact_checks(),'saved constants differ')
    need(r['midpoint_evaluations']==3*N,'mesh mismatch')
    qlo,qhi = map(endpoint_fraction,r['quadrature_interval_binary'])
    err = D2*sum((v-u)**3 for u,v in zip(POINTS,POINTS[1:]))/(24*N**2)
    need(Q(r['analytic_error_exact'])==err,'quadrature error mismatch')
    lo,hi=qlo-err,qhi+err
    need(qlo<=qhi and lo>TARGET,'invalid certificate interval')
    displayed = r['I0_interval_outward_decimal']
    need(Q(displayed[0])<=lo<=hi<=Q(displayed[1]),'decimal serialization not outward')
    need(r['independent_verification'] is False,'false independent status')
    checked=0
    if (ROOT/'attempt.json').exists():
        meta=json.loads((ROOT/'attempt.json').read_text(encoding='utf-8'))
        for name,sha in meta['artifact_sha256'].items():
            need(name!='attempt.json' and Path(name).name==name,'unsafe/self hash')
            need(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha, f'hash mismatch: {name}')
            checked+=1
    return {'ok':True,'scope':'saved_certificate_arithmetic_structure_and_hashes',
            'I0_interval':displayed,'lower_endpoint_above_target':True,
            'checked_hashes':checked,'mathematical_truth_verified':False}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--compute',action='store_true',help='actually recompute and write results.json')
    args=p.parse_args()
    if args.compute:
        result=compute()
        (ROOT/'results.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    print(json.dumps(verify_saved(),ensure_ascii=False))
    return 0

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (ValueError,KeyError,OSError,TypeError,json.JSONDecodeError) as e:
        print(f'FAIL: {e}',file=sys.stderr)
        raise SystemExit(1)
