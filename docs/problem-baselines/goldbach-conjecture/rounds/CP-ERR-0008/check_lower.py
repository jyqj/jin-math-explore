#!/usr/bin/env python3
"""CP-ERR-0008: bounded tests and directed fixed-kernel certificates.

Python >=3.10; mpmath ==1.3.0. No network or subprocess use.
--compute recomputes all five integrals; --check does NOT rerun quadrature.
--output creates a NEW file (exclusive mode), never overwrites frozen evidence.
Analytic/source assumptions are in proof.md. No independent verification implied.
"""
from __future__ import annotations
import argparse
import copy
from fractions import Fraction as F
import hashlib
import itertools
import json
from math import gcd, prod, isqrt
from pathlib import Path
import sys
import mpmath as mp

ROOT = Path(__file__).resolve().parent
A, B = F(4, 53), F(4, 33)
RHO = F(1, 10**6)
CELLS, DPS = 4096, 50
CASES = (
    ('G1_fixed', F(6), 53),
    ('G2_log_limit', F(33, 8), 33),
    ('G2_old_rho', F(33, 8)-F(1,10**8), 33),
    ('G2_selected', F(33, 8)-RHO, 33),
    ('G2_overlarge_rho', F(33, 8)-2*RHO, 33),
)
SIGMA = B*RHO
FLOORS = {'G1_fixed':F('14.877114'), 'G2_selected':F('9.11587009')}
EXPECTED_COEFFS = {
    'G1': {'epsilon0':'160/7','q_a':'15','epsilon':'4081/50','C_BV*T^(3-A0)':'15'},
    'G2': {'epsilon0':'320/21','q_b':'10','epsilon':'1089/2','C_BV*T^(3-A0)':'15'},
    '3G1+G2': {'epsilon0':'1760/21','q_a':'45','q_b':'10','epsilon':'19734/25','C_BV*T^(3-A0)':'60'}
}
FILES = ('README.md','proof.md','contracts.json','prior-work.json','source-lock.json',
         'check_lower.py','results.json','error-handoff.json','computation-record.json',
         'computation-handoff.json','verification-ticket.md','validation.json')


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def iq(value: F | int):
    value = F(value)
    return mp.iv.mpf(value.numerator)/value.denominator


def exact_endpoint(value) -> F:
    sign, man, exp, bc = value
    require(bc >= 0, 'nonfinite interval')
    return F((-1 if sign else 1)*man) * (F(2)**exp)


def ibounds(value) -> tuple[F,F]:
    lo,hi = map(exact_endpoint, value._mpi_)
    require(lo<=hi,'reversed raw interval')
    return lo,hi


def outward(value: F, upper: bool, places: int=18) -> str:
    scale=10**places
    k=(-((-value.numerator*scale)//value.denominator) if upper
       else (value.numerator*scale)//value.denominator)
    sign='-' if k<0 else ''; k=abs(k)
    return f'{sign}{k//scale}.{k%scale:0{places}d}'


def kernel(s: F,c: int) -> dict:
    require(4<=s<=6, 'kernel outside proved range')
    step=(s-4)/CELLS
    total=iq(0)
    si=iq(s)
    if step:
        for j in range(CELLS):
            u=iq(2+F(2*j+1,2)*step)
            total += mp.iv.log(u-1)/u * mp.iv.log((si-1)/(u+1))
    value=iq(F(c)/s)*(mp.iv.log(si-1)+iq(step)*total)
    radius=F(c)/s * 3*(s-4)**3/(24*CELLS**2)
    lo,hi=ibounds(value)
    return {'s':str(s),'coefficient':c,'midpoint_evaluations':CELLS,
            'scaled_quadrature_error':str(radius),
            'interval':[outward(lo-radius,False),outward(hi+radius,True)]}


def validate_result(data: dict) -> None:
    require(data['schema']=='goldbach-explicit-lower-certificate/v1','schema')
    require(data['cells_per_integral']==CELLS and data['decimal_precision']==DPS,'precision/grid')
    require(data['backend']=='mpmath.iv' and data['backend_version']=='1.3.0','backend pin')
    require(data['total_midpoints']==len(CASES)*CELLS,'coverage')
    require(data['selected_rho']==str(RHO) and data['selected_sigma']==str(SIGMA),'level identity')
    require(data['sigma_gain_over_cp3']==100,'margin ratio')
    require(data['safe_floors']=={k:str(v) for k,v in FLOORS.items()},'floor identity')
    require(set(data['integrals'])=={name for name,_,_ in CASES},'integral identities')
    for name,s,c in CASES:
        row=data['integrals'][name]
        require(row['s']==str(s) and row['coefficient']==c,'s/coefficient changed')
        require(row['midpoint_evaluations']==CELLS,'partial quadrature')
        error=F(c)/s*3*(s-4)**3/(24*CELLS**2)
        require(F(row['scaled_quadrature_error'])==error,'analytic remainder')
        lo,hi=map(F,row['interval'])
        require(0<lo<hi<(15 if c==53 else 10),'kernel enclosure bounds')
        require(hi-lo< (F(2,10**6) if c==53 else F(1,10**9)),'enclosure width')
    for name,floor in FLOORS.items():
        require(F(data['integrals'][name]['interval'][0])>=floor,'floor not certified')
    require(F(data['integrals']['G2_overlarge_rho']['interval'][1])<F('9.11587'),'failed comparator not separated')
    require(F(data['selected_weighted_floor'])==3*FLOORS['G1_fixed']+FLOORS['G2_selected'],'weighted floor')
    require(data['global_status']=='INCONCLUSIVE' and data['independently_verified'] is False,'authority')
    require(data['actual_G_counts_enclosed'] is False,'integral versus count')


def compute() -> dict:
    require(mp.__version__=='1.3.0','requires mpmath 1.3.0')
    mp.iv.dps=DPS
    data={'schema':'goldbach-explicit-lower-certificate/v1',
          'backend':'mpmath.iv','backend_version':mp.__version__,
          'decimal_precision':DPS,'cells_per_integral':CELLS,
          'total_midpoints':len(CASES)*CELLS,
          'integrals':{name:kernel(s,c) for name,s,c in CASES},
          'selected_rho':str(RHO),'selected_sigma':str(SIGMA),
          'sigma_gain_over_cp3':100,
          'safe_floors':{k:str(v) for k,v in FLOORS.items()},
          'selected_weighted_floor':str(3*FLOORS['G1_fixed']+FLOORS['G2_selected']),
          'actual_G_counts_enclosed':False,
          'global_status':'INCONCLUSIVE','independently_verified':False}
    validate_result(data)
    return data


def primes_to(n: int) -> list[int]:
    flags=bytearray(b'\1')*(n+1); flags[:2]=b'\0\0'
    for p in range(2,isqrt(n)+1):
        if flags[p]: flags[p*p:n+1:p]=b'\0'*((n-p*p)//p+1)
    return [p for p in range(2,n+1) if flags[p]]


def phi(n: int) -> int:
    out=n; k=2; rest=n
    while k*k<=rest:
        if rest%k==0:
            out-=out//k
            while rest%k==0: rest//=k
        k+=1
    if rest>1: out-=out//rest
    return out


def squarefree(n: int) -> bool:
    return all(n%(p*p) for p in range(2,isqrt(n)+1))


def self_test() -> dict:
    counts={}
    mp.iv.dps=DPS
    for value in (F(0),F(-7,9),F(1,3),F(1,2**100),F(10)**30):
        lo,hi=ibounds(iq(value))
        require(lo<=value<=hi,'interval conversion')
        require(F(outward(value,False))<=value<=F(outward(value,True)),'decimal conversion')
    counts['interval_serialization']=5
    identities=(
        (F(1,2)-6*A,F(5,106)),
        (F(1,2)-B*(F(33,8)-RHO),SIGMA),
        (SIGMA/(B*F(1,10**8)),F(100)),
        (B/F(8),F(1,66)),
        (154*53*F(1,100),F(4081,50)),
        (154*33*F(3,28),F(1089,2)),
        (3*F(4081,50)+F(1089,2),F(19734,25)),
        (3*15*F(32,21)+10*F(32,21),F(1760,21)),
        (4*15,F(60)),
        (F(1089,16),F(33)*F(1,4)/B),
    )
    for got,want in identities: require(got==want,'coefficient/level algebra')
    require(F(8,3)**2>7 and F(8,3)**4>50,'elementary exponential envelopes')
    counts['coefficient_level_identities']=len(identities)+1
    # Exact torus-free arithmetic on the original truncated prime sequence.
    primes=primes_to(1024); cases=0; aggregations=0; strict_cases=0
    for N in range(16,258,2):
        for eps0 in (F(1,16),F(1,2)):
            Y=(1-eps0)*N
            seq=[N-p for p in primes if p<Y]
            M=len(seq)
            mods=[d for d in range(1,33) if squarefree(d) and gcd(d,N)==1]
            for shift in (F(-3,2),F(0),F(5,3)):
                X=M+shift; delta=F(M)-X
                raw=[]; rebased=[]; densities=[]
                for d in mods:
                    hit=sum(a%d==0 for a in seq)
                    via_ap=sum(p<Y and (p-N)%d==0 for p in primes)
                    require(hit==via_ap,'native AP identity')
                    g=F(1,phi(d)); r=hit-X*g; rm=hit-M*g
                    require(rm==r-g*delta,'mass rebasing sign')
                    if d==1: require(r==delta and rm==0,'unit modulus')
                    raw.append(abs(r)); rebased.append(abs(rm)); densities.append(g)
                    cases+=1
                E=sum(raw,F(0))
                require(abs(delta)<=E,'d=1 controls shared mass')
                require(sum(rebased,F(0))<=(1+sum(densities,F(0)))*E,'absolute rebase bound')
                aggregations+=1
            if Y.denominator==1 and int(Y) in primes:
                require(sum(p<=Y for p in primes)-M==1,'strict endpoint example')
                strict_cases+=1
    counts['native_ap_and_rebase']=cases
    counts['aggregate_rebase']=aggregations
    counts['strict_prime_endpoints']=strict_cases
    # Reciprocal-totient bound is checked against 3 H_n, entirely rational.
    H,total=F(0),F(0)
    for n in range(1,257):
        H+=F(1,n); total+=F(1,phi(n))
        rhs=sum((F(1,phi(d)) for d in range(1,n+1) if n%d==0 and squarefree(d)),F(0))
        require(F(n,phi(n))==rhs,'totient divisor identity')
        require(total<3*H,'reciprocal totient bound')
    counts['totient_identities_and_bounds']=256
    # P0 inflation: combinatorial support only, not a sampled theorem proof.
    support_cases=0
    small=(2,3,5,7,11); P0=prod(small)
    for N,D in itertools.product((30,42,70,256),(4,9,16,25,64)):
        W=prod(p for p in small if N%p)
        R=P0*D
        good=[p for p in primes if p<20 and N%p]
        for bits in itertools.product((0,1),repeat=len(good)):
            d=prod(p for p,bit in zip(good,bits) if bit)
            if d<W*D:
                require(d<R,'presieve support')
                support_cases+=1
    counts['presieve_support']=support_cases
    # Lower main-mass transfer is valid for both signs, without selecting a sign.
    sign_cases=0
    for M,X,V,t in itertools.product((F(0),F(1),F(3)),(F(0),F(2),F(5)),
                                    (F(0),F(1,3),F(1)),(F(-2),F(-1),F(0),F(1,2),F(2))):
        require(t*V*M>=t*V*X-2*abs(M-X),'negative-main-factor guard')
        sign_cases+=1
    counts['signed_mass_transfer']=sign_cases
    normalization=0
    for k,q,theta,Rbit,e in itertools.product((F(1,4),F(1),F(15)),
            (F(0),F(1,3),F(1)),(F(0),F(1,2),F(1)),(-1,1),(F(0),F(1,2),F(20))):
        r=1+Rbit*q
        require(r*(1-theta)*(k-e)>=k-k*(q+theta)-2*e,'separated main and epsilon penalty')
        normalization+=1
    counts['normalized_sign_transfer']=normalization
    budget_cases=0
    fixedmax=F(320,21)+F(1089,2)
    for delta in (F(1,10),F(1,10**5),F(1,25_000_000),F(1,10**10)):
        eps=min(F(1,400),delta/(4*fixedmax))
        for cf in (F(160,7)+F(4081,50),fixedmax):
            require(cf*eps<=delta/4,'small parameter budget')
            budget_cases+=1
    counts['shared_parameter_allocations']=budget_cases
    rejected=[]
    def reject(label,test):
        try: test()
        except (ValueError,KeyError,TypeError): rejected.append(label)
        else: raise ValueError('negative control accepted: '+label)
    reject('forget_P0',lambda:require(105<100,'W=3,D=100 permits d=105 but R=100 does not'))
    reject('negative_factor_flip',lambda:require(F(-3)>=F(-1),'multiplication reverses lower bound'))
    reject('rebase_wrong_sign',lambda:require(F(1,2)==F(-1,2),'rM=r-g*Delta'))
    reject('missing_unit_modulus',lambda:require(abs(F(-1))<=0,'old r(3)=0 does not bound Delta'))
    reject('enlarge_lower_sequence',lambda:require(len([2])>=len([2,3]),'subset lower bound'))
    reject('strict_endpoint_as_closed',lambda:require(sum(p<19 for p in primes)==sum(p<=19 for p in primes),'strict endpoint'))
    reject('mix_log_and_fixed_modes',lambda:require(F(1,66)<=SIGMA,'log-mode onset cannot justify fixed mode'))
    reject('forget_presieve_log',lambda:require(F(1,100)<=SIGMA,'log P0/T term is not zero'))
    reject('lose_combination_weight',lambda:require(3*15+10==15+10,'G1 has weight3'))
    reject('reuse_old_G2_floor',lambda:require(F('9.11587009')>=F('9.1158704'),'new onset trades away old margin'))
    reject('same_order_decay',lambda:require(3-3<0,'A0 must exceed3'))
    reject('epsilon_Cepsilon',lambda:require(F(1,100)*100<F(1,2),'unknown C(epsilon) cannot be suppressed'))
    return {'schema':'goldbach-explicit-lower-tests/v1','ok':True,'counts':counts,
            'total_finite_cases':sum(counts.values()),'negative_controls_rejected':len(rejected),
            'negative_control_labels':rejected,'mathematical_truth_verified':False}


def check_saved() -> dict:
    data=json.loads((ROOT/'results.json').read_text())
    validate_result(data)
    manifest=json.loads((ROOT/'artifact-sha256.json').read_text())
    require(set(manifest['sha256'])==set(FILES),'manifest coverage')
    for name,digest in manifest['sha256'].items():
        require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'hash mismatch '+name)
    tests=self_test()
    require(tests==json.loads((ROOT/'validation.json').read_text()),'finite replay differs')
    contract=json.loads((ROOT/'contracts.json').read_text())
    require(contract['deficit_coefficients']==EXPECTED_COEFFS,'contract coefficients')
    require(contract['source_inputs']==['U-BJS-v6','U-BV-classical','U-Mertens'],'wrong source imports')
    require(contract['global_status']=='INCONCLUSIVE','global contract promotion')
    require(contract['old_Cs_discharged'] is False,'original source audit not performed')
    mutations=0
    for field,value in (('selected_rho','1/100000000'),('selected_sigma','0'),
        ('sigma_gain_over_cp3',10000),('total_midpoints',4096),('actual_G_counts_enclosed',True),
        ('independently_verified',True),('global_status','PASS')):
        bad=copy.deepcopy(data); bad[field]=value
        try: validate_result(bad)
        except (ValueError,TypeError,KeyError): mutations+=1
        else: raise ValueError('result mutation accepted')
    for mode in ('error','floor','ordering'):
        bad=copy.deepcopy(data)
        if mode=='error': bad['integrals']['G2_selected']['scaled_quadrature_error']='0'
        if mode=='floor': bad['safe_floors']['G2_selected']='10'
        if mode=='ordering': bad['integrals']['G2_selected']['interval']=['10','9']
        try: validate_result(bad)
        except (ValueError,TypeError,KeyError): mutations+=1
        else: raise ValueError('nested result mutation accepted')
    return {'ok':True,'hashes_checked':len(FILES),
            'finite_cases_replayed':tests['total_finite_cases'],
            'negative_controls_rejected':tests['negative_controls_rejected']+mutations,
            'quadrature_replayed':False,'global_status':'INCONCLUSIVE',
            'mathematical_truth_verified':False}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    for flag in ('compute','self-test','check','require-global'):
        group.add_argument('--'+flag,action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.require_global:
        print('REJECT: source imports, independent review and remaining ten-term/global closure are not certified.')
        return 1
    result=compute() if args.compute else (self_test() if args.self_test else check_saved())
    if args.output:
        require(not args.check,'--check never writes')
        with args.output.open('x',encoding='utf-8') as fp:
            fp.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    elif args.compute:
        require(result==json.loads((ROOT/'results.json').read_text()),'quadrature differs from frozen result')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as exc:
        print('FAIL: '+str(exc),file=sys.stderr)
        raise SystemExit(1)
