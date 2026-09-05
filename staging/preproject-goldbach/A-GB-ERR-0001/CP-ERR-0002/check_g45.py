#!/usr/bin/env python3
"""CP-ERR-0002: exact G4/G5 error constants and validated integral enclosures.

Uses mpmath.iv 1.3.0 for outward logarithms and Fraction for exact decisions.
The J correction is integrated by midpoint quadrature with the MANUALLY
PROVED piecewise second-derivative bound 64. The common K correction uses
natural interval cubature, requiring no derivative estimate. Proof.md gives
the integral identities and analytic contract; this program does not prove
those identities, the external sieve/BV/PNT theorems, or global Goldbach.

--compute: run actual quadrature and save results.json.
--check: validate saved arithmetic, negative controls and artifact hashes.
--require-global: deliberately reject absent global proof receipts.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import itertools
import json
import sys
from math import isqrt
from fractions import Fraction as Q
from pathlib import Path
import mpmath
from mpmath import iv

ROOT = Path(__file__).resolve().parent
ALPHA=Q(4,53)
A=Q(53,8)
SMAX=Q(45,8)
BETA={'G4':Q(1,3),'G5':Q(3,11)}
TARGET={'G4':Q('23.60636'),'G5':Q('19.51976')}
MIDPOINT_N=4096
CUBATURE_N=64
D2=Q(64)
DPS=50
FILES={'README.md','proof.md','source-lock.json','contracts.json','error-handoff.json',
       'check_g45.py','results.json','computation-handoff.json','attempt.json'}

class CheckError(ValueError):
    pass

def need(ok, message):
    if not ok:
        raise CheckError(message)

def iq(x):
    x=Q(x)
    return iv.mpf(x.numerator)/x.denominator

def ef(t):
    sign,m,e,bc=t
    need(bc>=0,'nonfinite interval endpoint')
    return (-1 if sign else 1)*Q(m)*Q(2)**e

def ends(v):
    return tuple(ef(t) for t in v._mpi_)

def binary(v):
    return [list(t) for t in v._mpi_]

def dec(x,upper=False,places=18):
    x=Q(x); scale=10**places
    n=x.numerator*scale
    k=-((-n)//x.denominator) if upper else n//x.denominator
    sign='-' if k<0 else ''
    k=abs(k)
    return f'{sign}{k//scale}.{k%scale:0{places}d}'

def interval_record(v):
    lo,hi=ends(v)
    return {'binary':binary(v),'outward_decimal':[dec(lo),dec(hi,True)]}

def coeffs(b):
    r=b/ALPHA
    return {'b':str(b),'s_min':str((Q(1,2)-b)/ALPHA),
            'legal_h_max':str(Q(1,2)-b-2*ALPHA),
            'K_normalization':str(4/ALPHA*(r-1)),
            'K_level_shift':str(8/ALPHA**2*r),
            'K_prime_measure':str(8/ALPHA*r),
            'K_reciprocal':str(16/ALPHA),
            'K_sieve':str(8/ALPHA*(r+1))}

def exact_checks():
    c={name:coeffs(b) for name,b in BETA.items()}
    need(Q(c['G4']['legal_h_max'])==Q(5,318),'G4 legal slack')
    need(Q(c['G5']['legal_h_max'])==Q(89,1166),'G5 legal slack')
    need(A-SMAX==1,'A-SMAX normalization')
    need(4/ALPHA/A==8,'Fubini factor')
    need(SMAX-5==Q(5,8),'common triangle size')
    # Proof envelope for normalized F: J <= s-3; K <= (s-5)^3/72.
    need((1+SMAX-3+(SMAX-5)**3/72)/5<1,'normalized F bound')
    need((2+(SMAX-5)**2/24)/5<1,'normalized F derivative bound')
    need(Q(2,3)<1 and Q(1,4)<1,'remaining derivative pieces')
    # exp(2)>sum_{j=0}^4 2^j/j! = 7 > 435/64.
    need(Q(7)>Q(435,64),'logarithm envelope')
    # |j|<=1, |j prime|<=1, |j double prime|<=2; W<=16.
    envelope=2*16+2*Q(32,3)+Q(80,9)
    need(envelope==Q(560,9)<D2,'midpoint derivative envelope')
    return {'alpha':str(ALPHA),'A':str(A),'s_max':str(SMAX),
            'normalized_F_sup':'1','normalized_F_Lipschitz':'1',
            'second_derivative_envelope':str(envelope),'midpoint_D2':str(D2),
            'coefficients':c,
            'pair_fixed_sieve_coefficient':str(sum(Q(v['K_sieve']) for v in c.values()))}

def H(s):
    return 8*iv.ln(s/(iq(A)-s))

def mid_integral(lo,hi,sigma,constant_piece):
    step=(hi-lo)/MIDPOINT_N
    subtotal=iv.mpf(0)
    hs=H(iq(SMAX))
    for k in range(MIDPOINT_N):
        t=iq(lo+Q(2*k+1,2)*step)
        bottom=iq(sigma) if constant_piece else t+1
        subtotal += iv.ln(t-1)/t*(hs-H(bottom))
    raw=iq(step)*subtotal
    err=D2*(hi-lo)**3/(24*MIDPOINT_N**2)
    return raw,err

def common_cubature():
    # r in [0,d], v in [0,1], x=r*v. dt*du = r dr dv.
    # K common = int r*j(2+r*v)*log((3+r)/(3+r*v))/(4+r)
    #              *[H(SMAX)-H(5+r)] dr dv.
    d=iq(SMAX-5)
    hs=H(iq(SMAX))
    total=iv.mpf(0)
    for i in range(CUBATURE_N):
        r=d*iv.mpf([i,i+1])/CUBATURE_N
        outer=r/(4+r)*(hs-H(5+r))
        subtotal=iv.mpf(0)
        for j in range(CUBATURE_N):
            v=iv.mpf([j,j+1])/CUBATURE_N
            x=r*v
            subtotal += iv.ln(1+x)/(2+x)*iv.ln((3+r)/(3+x))*outer
        total += subtotal
    return total*d/CUBATURE_N**2

def compute():
    need(mpmath.__version__=='1.3.0','mpmath version must be re-locked')
    iv.dps=DPS
    constants=exact_checks()
    common=common_cubature()
    common_record=interval_record(common)
    out={}
    for name,b in BETA.items():
        sigma=(Q(1,2)-b)/ALPHA
        bp=[Q(2)]+([sigma-1] if sigma>3 else [])+[SMAX-1]
        mid=iv.mpf(0); error=Q(0)
        for i,(lo,hi) in enumerate(zip(bp,bp[1:])):
            val,err=mid_integral(lo,hi,sigma,sigma>3 and i==0)
            mid+=val;error+=err
        correction=mid+iv.mpf([-error.numerator,error.numerator])/error.denominator
        base=H(iq(SMAX))-H(iq(sigma))
        total=base+correction+common
        lo,hi=ends(total)
        need(hi<TARGET[name], f'{name}: upper enclosure misses paper bound')
        out[name]={'b':str(b),'sigma':str(sigma),'source_upper_bound':str(TARGET[name]),
                   'base':interval_record(base),'J_midpoint_raw':interval_record(mid),
                   'J_error_exact':str(error),'J_breakpoints':[str(t) for t in bp],
                   'enclosure':interval_record(total),
                   'slack_to_source_bound_lower':dec(TARGET[name]-hi)}
    pair_upper=sum(
        ef(v['enclosure']['binary'][1]) for v in out.values())
    # The conditional display-budget comparison is NOT an authority upgrade.
    old_main=Q(43,25000); reserve=Q(3,25000)
    possible_gain=sum(TARGET.values())-pair_upper
    result={'schema':'jin-math-g45-certificate/v1','attempt_id':'A-GB-ERR-0001',
        'checkpoint':'CP-ERR-0002','backend':{'python':sys.version.split()[0],
        'mpmath':mpmath.__version__,'iv_dps':DPS},
        'method':'Fubini reduction; interval midpoint plus derivative remainder for J; natural interval cubature for common K',
        'midpoint_subintervals_per_piece':MIDPOINT_N,'midpoint_evaluations':3*MIDPOINT_N,
        'cubature_grid_per_axis':CUBATURE_N,'cubature_cells':CUBATURE_N**2,
        'constants':constants,'common_K':common_record,'integrals':out,
        'certified_rational_caps':{'G4':'23.60573','G5':'19.51913'},
        'conditional_budget_only':{
           'source_budget_reserve':'3/25000',
           'pair_numeric_gain_lower':dec(possible_gain),
           'resulting_reserve_lower':dec(reserve+possible_gain),
           'resulting_D_over_S_before_analytic_errors_lower':dec((old_main+possible_gain)/4),
           'rational_cap_pair_gain':'63/50000',
           'rational_cap_reserve':'69/50000',
           'rational_cap_reserve_ratio':'23/2',
           'imported_into_global_ledger':False},
        'analytic_contract_status':'solver_candidate_under_declared_uniform_LS_BV_PNT_inputs',
        'global_closure':False,'independent_verification':False,
        'trust_basis':['mpmath.iv 1.3.0 interval arithmetic/log',
                       'manual Fubini identities and piecewise derivative bound in proof.md',
                       'exact Fraction decisions and outward decimal serialization'],
        'cannot_imply':['No external analytic theorem is proved by this program.',
                       'Enclosing fixed integrals does not verify their transfer to the twelve-term theorem.',
                       'The conditional budget gain is not a claim of a better Goldbach exponent or an independently verified result.']}
    return result

def validate_contract(c):
    need(c['checkpoint']=='CP-ERR-0002','contract checkpoint')
    need(c['global_closure'] is False,'unauthorized global closure')
    need(c['sequence_action']=='enlarge_for_upper_bound_only','wrong monotonicity direction')
    need(c['normalized_F']=={'sup':'1','lipschitz':'1','domain':['2','45/8']},'kernel envelope mismatch')
    need(c['sieve_constant']['uniform_in_eta'] is True,'eta-dependent fixed coefficient')
    for name,b in BETA.items():
        row=c['rows'][name]
        need(row['needed_direction']=='upper','wrong one-sided contract')
        need(row['coefficients']==coeffs(b),'contract constants differ')
        need(row['reciprocal_cost_present'] is True,'missing reciprocal correction')
    need(c['normalization_log_power']==2,'lost logarithmic normalization')

def reject(f):
    try:f()
    except CheckError as e:return str(e)
    raise CheckError('negative control was accepted')

def finite_injectivity():
    # Bounded test corroborates the unique-large-prime proof; not its replacement.
    primes=[n for n in range(2,101) if all(n%d for d in range(2,isqrt(n)+1))]
    seen={};count=0
    small=[p for p in primes if p<11]
    for bits in itertools.product((0,1),repeat=len(small)):
        q=1
        for p,take in zip(small,bits):
            if take:q*=p
        for p in primes:
            if p<11:continue
            d=p*q;pair=(p,q)
            need(d not in seen or seen[d]==pair,'large/small factor collision')
            seen[d]=pair;count+=1
    return count

def check_saved():
    r=json.loads((ROOT/'results.json').read_text())
    c=json.loads((ROOT/'contracts.json').read_text())
    validate_contract(c)
    need(r['constants']==exact_checks(),'saved exact constants mismatch')
    need(r['global_closure'] is False and r['independent_verification'] is False,'status mismatch')
    need(r['midpoint_subintervals_per_piece']==MIDPOINT_N and r['cubature_grid_per_axis']==CUBATURE_N,'mesh metadata mismatch')
    cap_gain=sum(TARGET.values())-sum(map(Q,r['certified_rational_caps'].values()))
    need(cap_gain==Q(63,50000),'conditional cap gain mismatch')
    need(Q(3,25000)+cap_gain==Q(r['conditional_budget_only']['rational_cap_reserve']),'conditional reserve mismatch')
    common_lo,common_hi=map(ef,r['common_K']['binary'])
    need(common_lo<=common_hi,'invalid common interval')
    for name,b in BETA.items():
        row=r['integrals'][name]
        s=(Q(1,2)-b)/ALPHA
        bp=[Q(2)]+([s-1] if s>3 else [])+[SMAX-1]
        err=D2*sum((hi-lo)**3 for lo,hi in zip(bp,bp[1:]))/(24*MIDPOINT_N**2)
        need(err==Q(row['J_error_exact']),'wrong quadrature remainder')
        raw_lo,raw_hi=map(ef,row['J_midpoint_raw']['binary'])
        base_lo,base_hi=map(ef,row['base']['binary'])
        lo,hi=map(ef,row['enclosure']['binary'])
        need(lo<=base_lo+raw_lo-err+common_lo,'unjustified lower endpoint')
        need(hi>=base_hi+raw_hi+err+common_hi,'unjustified upper endpoint')
        dl,dh=map(Q,row['enclosure']['outward_decimal'])
        need(dl<=lo<=hi<=dh,'decimal serialization not outward')
        need(hi<TARGET[name],'source numeric bound not met')
        need(hi<Q(r['certified_rational_caps'][name]),'rational upper cap not certified')
    negatives={}
    x=copy.deepcopy(c);x['rows']['G4']['needed_direction']='lower'
    negatives['wrong_direction']=reject(lambda:validate_contract(x))
    x=copy.deepcopy(c);x['sieve_constant']['uniform_in_eta']=False
    negatives['parameter_cycle']=reject(lambda:validate_contract(x))
    x=copy.deepcopy(c);x['rows']['G4']['reciprocal_cost_present']=False
    negatives['reciprocal_deleted']=reject(lambda:validate_contract(x))
    x=copy.deepcopy(c);x['normalization_log_power']=0
    negatives['lost_log_square']=reject(lambda:validate_contract(x))
    x=copy.deepcopy(c);x['global_closure']=True
    negatives['global_upgrade']=reject(lambda:validate_contract(x))
    negatives['illegal_h']=reject(lambda:need(Q(1,50)<=Q(5,318),'G4 level outside legal range'))
    hashes=0
    if (ROOT/'attempt.json').exists():
        m=json.loads((ROOT/'attempt.json').read_text())
        expected=m['artifact_sha256']
        need(set(expected)==FILES-{'attempt.json'},'manifest scope mismatch')
        need({p.name for p in ROOT.iterdir() if p.is_file()}==FILES,'unexpected checkpoint files')
        for name,value in expected.items():
            need(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value,'hash mismatch: '+name)
            hashes+=1
    return {'ok':True,'scope':'finite_enclosure_arithmetic_contract_structure_and_hashes',
            'integrals':{name:row['enclosure']['outward_decimal'] for name,row in r['integrals'].items()},
            'finite_injective_pairs':finite_injectivity(),'negative_controls':negatives,
            'checked_hashes':hashes,'global_closure':False,'independent_verification':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--compute',action='store_true')
    p.add_argument('--check',action='store_true')
    p.add_argument('--require-global',action='store_true')
    args=p.parse_args()
    if args.require_global:
        raise CheckError('global closure remains blocked: other ten contracts and independent receipts are not supplied')
    if args.compute:
        r=compute()
        (ROOT/'results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(check_saved(),ensure_ascii=False))
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (CheckError,OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print('FAIL: '+str(exc),file=sys.stderr)
        raise SystemExit(1)
