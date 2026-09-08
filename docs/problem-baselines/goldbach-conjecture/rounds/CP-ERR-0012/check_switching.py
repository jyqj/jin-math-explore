#!/usr/bin/env python3
"""CP-ERR-0012: G3/G10 switching checks and fixed-integral certificates.

Python >=3.10; mpmath==1.3.0. --compute recomputes fixed integrals only.
--self-test checks bounded exact models; --check also verifies frozen hashes.
No command verifies a source theorem, a numerical N0, or binary Goldbach.
"""
from __future__ import annotations
import argparse
from collections import Counter
from fractions import Fraction as F
import hashlib
import itertools
import json
from math import gcd, isqrt
from pathlib import Path
import sys
import mpmath as mp

ROOT = Path(__file__).resolve().parent
BETA, GAMMA, TURN = F(4,33), F(3,11), F(2,11)
TAU0 = F(9,19)
CELLS, DPS, LOG_TERMS = 4096, 50, 32
DERIVATIVE_BOUND = F(21000)
FILES = ('README.md','proof.md','contracts.json','prior-work.json',
         'source-lock.json','check_switching.py','results.json',
         'error-handoff.json','computation-record.json','computation-handoff.json',
         'verification-ticket.md','validation.json')
COEFFICIENTS = {'epsilon_tau':'132','epsilon':'6930','q_V':'30',
                'ell_N':'20','h_star':'40','r3_N':'1024','r10_N':'768',
                'C_A*T^(3-A)':'95','T^2*(1+T)^2/(N^beta-1)':'12',
                '(4*E3+E10)*T^2/N':'2'}


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def load(name: str):
    def pairs(items):
        d = {}
        for k,v in items:
            need(k not in d, 'duplicate JSON key '+k)
            d[k] = v
        return d
    return json.loads((ROOT/name).read_text(encoding='utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))


def ivq(x):
    x = F(x)
    return mp.iv.mpf(x.numerator)/x.denominator


def bf(t):
    sign,mantissa,exponent,bits = t
    need(bits >= 0, 'nonfinite endpoint')
    v = F((-1 if sign else 1)*mantissa)
    return v*(2**exponent) if exponent>=0 else v/F(2**(-exponent))


def bounds(x):
    lo,hi = map(bf,x._mpi_)
    need(lo<=hi, 'reversed binary interval')
    return lo,hi


def dec(x: F, upper: bool, places: int = 18):
    scale=10**places
    k=-((-x.numerator*scale)//x.denominator) if upper else x.numerator*scale//x.denominator
    sign='-' if k<0 else ''; k=abs(k)
    return f'{sign}{k//scale}.{k%scale:0{places}d}'


def enclose(x, radius=F(0)):
    lo,hi=bounds(x)
    return [dec(lo-radius,False),dec(hi+radius,True)]


def log_rational(x: F, n=LOG_TERMS):
    need(x>=1 and n>0, 'log series domain')
    t=(x-1)/(x+1)
    lo=2*sum((t**(2*k+1)/(2*k+1) for k in range(n)),F(0))
    tail=2*t**(2*n+1)/((2*n+1)*(1-t*t))
    return lo,lo+tail


def compute():
    need(mp.__version__=='1.3.0','pin mpmath==1.3.0')
    mp.iv.dps=DPS
    sums=[]; errors=[]
    for l,r in ((BETA,TURN),(TURN,GAMMA)):
        step=(r-l)/CELLS; v=ivq(0)
        for j in range(CELLS):
            x=ivq(l+F(2*j+1,2)*step)
            v += 8*mp.iv.log((1-x-ivq(GAMMA))/ivq(GAMMA))/(x*(1-x))
        sums.append(v*ivq(step))
        errors.append(DERIVATIVE_BOUND*(r-l)**3/(24*CELLS**2))
    analytic_left=8*mp.iv.log(ivq(2))*mp.iv.log(ivq(F(29,18)))
    original=sums[0]+sums[1]
    active=analytic_left+sums[1]
    removed=sums[0]-analytic_left
    low3,high3=log_rational(F(10,9)); low3*=8; high3*=8
    data={'schema':'goldbach-switching-certificate/v1','backend':'mpmath.iv + Fraction',
          'mpmath_version':mp.__version__,'decimal_precision':DPS,
          'cells_per_piece':CELLS,'midpoint_evaluations':2*CELLS,
          'breakpoints':list(map(str,(BETA,TURN,GAMMA))),
          'second_derivative_bound':str(DERIVATIVE_BOUND),
          'piece_error_bounds':list(map(str,errors)),
          'g3_log_terms':LOG_TERMS,'g3_exact_interval':[str(low3),str(high3)],
          'g3_enclosure':[dec(low3,False),dec(high3,True)],
          'g10_original_enclosure':enclose(original,sum(errors)),
          'g10_active_enclosure':enclose(active,errors[1]),
          'g10_removed_wedge_enclosure':enclose(removed,errors[0]),
          'safe_g3_upper':dec(high3,True,9),
          'safe_g10_upper':dec(bounds(active)[1]+errors[1],True,6),
          'original_printed_g10':'5.40996','original_printed_g3':'0.84289',
          'actual_count_enclosure':False,'independently_verified':False,
          'global_status':'INCONCLUSIVE'}
    data['g10_gain_vs_printed']=str(F(data['original_printed_g10'])-F(data['safe_g10_upper']))
    validate_result(data)
    return data


def validate_result(d):
    need(d['schema']=='goldbach-switching-certificate/v1','schema')
    need(d['midpoint_evaluations']==2*CELLS and d['cells_per_piece']==CELLS,'grid')
    need(d['breakpoints']==list(map(str,(BETA,TURN,GAMMA))),'breakpoint')
    need(F(d['second_derivative_bound'])==DERIVATIVE_BOUND,'derivative bound')
    expected=[DERIVATIVE_BOUND*(r-l)**3/(24*CELLS**2) for l,r in ((BETA,TURN),(TURN,GAMMA))]
    need(list(map(F,d['piece_error_bounds']))==expected,'quadrature error')
    l3,h3=map(F,d['g3_exact_interval']); a3,b3=log_rational(F(10,9))
    need((l3,h3)==(8*a3,8*b3) and d['g3_log_terms']==LOG_TERMS,'exact log')
    lo,hi=map(F,d['g10_active_enclosure']); oldlo,oldhi=map(F,d['g10_original_enclosure'])
    wlo,whi=map(F,d['g10_removed_wedge_enclosure'])
    need(0<lo<hi<oldlo<oldhi<F('5.40996') and wlo>0 and whi>wlo,'scalar directions')
    need(oldlo-hi<=whi and oldhi-lo>=wlo,'wedge consistency')
    need(F(d['safe_g10_upper'])>=hi and F(d['safe_g10_upper'])-hi<=F(1,10**6),'upper rounding')
    need(F(d['safe_g3_upper'])>=h3 and F(d['safe_g3_upper'])<F('0.84289'),'g3 cap')
    need(d['g3_enclosure']==[dec(l3,False),dec(h3,True)],'g3 serialization')
    need(F(d['g10_gain_vs_printed'])==F('5.40996')-F(d['safe_g10_upper']),'gain')
    need(d['actual_count_enclosure'] is False and d['independently_verified'] is False,'scope')
    need(d['global_status']=='INCONCLUSIVE','global promotion')


def primes_upto(n):
    sieve=bytearray(b'\1')*(n+1)
    if n>=0: sieve[0]=0
    if n>=1: sieve[1]=0
    for p in range(2,isqrt(n)+1):
        if sieve[p]: sieve[p*p:n+1:p]=b'\0'*(((n-p*p)//p)+1)
    return [p for p in range(2,n+1) if sieve[p]]


def factors(n):
    out=[]; p=2
    while p*p<=n:
        if n%p==0:
            e=0
            while n%p==0: n//=p; e+=1
            out.append((p,e))
        p+=1
    if n>1: out.append((n,1))
    return out


def phi(n):
    out=n
    for p,_ in factors(n): out=out//p*(p-1)
    return out


def floor_power(n, exponent: F):
    target=n**exponent.numerator; d=exponent.denominator
    l,r=0,n+1
    while r-l>1:
        mid=(l+r)//2
        if mid**d<=target: l=mid
        else: r=mid
    return l


def native_pairs(n, primes):
    small=[p for p in primes if p**33>=n**4 and p**11<=n**3 and n%p]
    big=[p for p in primes if p**11>=n**3 and p*p<=n and n%p]
    return [(p,q) for p in small for q in big if p*q*q<=n]


def survives10(n,p,q,out,primes):
    a=n-out; m=p*q
    if a%m: return False
    return all(a%ell for ell in primes if ell*ell*m<n and n%ell and ell!=p)


def survives3(n,p,out,primes):
    a=n-out
    return a%p==0 and all(a%ell for ell in primes if ell<p and n%ell)


def parameter_row(A):
    D=B=A+8; J=2*A+12
    return {'A':A,'B':B,'D':D,'J':J,'small_SW':D+2-J,
            'large_front':3-B,'large_tail':3-D,'pi_Li':2-J,
            'small_removed_power':'2/3','cross_power':'5/6','endpoint_power':'1/2'}


def self_test():
    counts=Counter(); examples={}
    cases=list(range(100,1201,10))+[142,10002]
    for n in cases:
        ps=primes_upto(n); pset=set(ps); output=[r for r in ps if 4*r<3*n]
        pairs=native_pairs(n,ps)
        need(all(p<q for p,q in pairs),'shared prime endpoint')
        active=[(p,q) for p,q in pairs if p*q**3>=n]
        for p,q in pairs:
            need(p*q>=1 and (p*q)**3>=n and (p*q)**3<=n*n,'G10 slab')
            hits=[r for r in output if survives10(n,p,q,r,ps)]
            counts['native_pair_sets']+=1
            if p*q**3<n:
                need(not hits,'inactive summand survives'); counts['empty_pair_sets']+=1
            for r in hits:
                v=(n-r)//(p*q)
                bad=(gcd(n-r,n)>1 or (n-r)%(p*p)==0 or v==1)
                if not bad: need(v in pset,'unrepaired G10 residual')
                if v not in pset and v>1 and 'composite_residual' not in examples:
                    examples['composite_residual']=[n,p,q,r,v]
                counts['G10_survivors']+=1
        m10=[p*q for p,q in active]
        need(len(m10)==len(set(m10)),'ambiguous weight')
        m3=[p for p in ps if p**19>=n**9 and p*p<=n and n%p]
        bad10=0; bad3=0; g10=0; g3=0
        for p,q in active:
            for r in output:
                if survives10(n,p,q,r,ps):
                    g10+=1; v=(n-r)//(p*q)
                    if gcd(n-r,n)>1 or (n-r)%(p*p)==0 or v==1: bad10+=1
        for p in m3:
            need(p**3>=n and p**3<=n*n,'G3 slab')
            for r in output:
                if survives3(n,p,r,ps):
                    g3+=1; v=(n-r)//p
                    if gcd(n-r,n)>1 or v==1: bad3+=1
                    else: need(v in pset and v>=p,'G3 residual')
        for tag,ms,G,bad,multiplicity in [('G3',m3,g3,bad3,2),('G10',m10,g10,bad10,6)]:
            seq=[(m,r,n-m*r) for m in ms for r in ps if m*r<n]
            cnt=Counter(b for _,_,b in seq)
            need(max(cnt.values(),default=0)<=multiplicity,'multiset bound')
            need(G<=sum(b in pset for _,_,b in seq)+bad,'switching upper')
            counts['switching_and_multiplicity_models']+=1
            for Z in (3,5,7):
                if Z**4>n: continue
                sift=sum(all(b%ell for ell in ps if ell<Z and n%ell) for _,_,b in seq)
                need(G<=sift+bad+multiplicity*Z,'small-output cost')
                counts['sifted_upper_models']+=1
            # Synthetic positive analytic masses, NOT observed Li errors.
            xm={m:F(2*n,3*m) for m in ms}; X=sum(xm.values(),F(0)); mass=len(seq)
            for q in range(1,32):
                if gcd(q,n)>1 or any(e>1 for _,e in factors(q)): continue
                actual=sum((b%q==0) for _,_,b in seq)
                rq=sum((F(sum(1 for mm,r,_ in seq if mm==m and (m*r-n)%q==0))-xm[m]/phi(q)
                        for m in ms if gcd(m,q)==1),F(0))
                H=sum((xm[m]/phi(q) for m in ms if gcd(m,q)>1),F(0))
                need(F(actual)-X/phi(q)==rq-H,'noncoprime AP identity')
                need(F(actual)-F(mass,phi(q))==rq-H-F(mass-X,phi(q)),'mass rebasing')
                if q==1: need(H==0 and rq==mass-X,'unit modulus')
                if H>0: counts['nonzero_H_models']+=1
                for Z in (3,5,7):
                    smooth=all(p<Z for p,_ in factors(q))
                    if tag=='G3' and Z**4<=n and smooth: need(H==0,'G3 smooth H')
                counts['AP_rebase_models']+=1
        # Pure packing: at most six cross-range pairs per integer.
        L=floor_power(n,BETA)
        if L**33<n**4: L+=1
        need(bad10<=floor_power(n,F(7,11))+F(6*n,L-1)+6*len(factors(n)),'G10 exceptions')
        need(bad3<=isqrt(n)+2*len(factors(n)),'G3 exceptions')
        counts['exception_budgets']+=2
    # Explicit native counterexample, with all exact exponent/sieve checks.
    ps=primes_upto(142)
    need((3,5) in native_pairs(142,ps) and survives10(142,3,5,7,ps),'counterexample absent')
    need((142-7)//15==9 and 9 not in ps,'composite witness')
    examples['specified_composite_residual']={'N':142,'p1':3,'p2':5,'output':7,'residual':9}
    for p in (3,5,7,11):
        def nextprime(x):
            y=x+1
            while len(factors(y))!=1 or factors(y)[0][1]!=1: y+=1
            return y
        q=nextprime(p*p); a=p**3*q; r=nextprime(a); n=a+r
        need(p*p<q<2*p*p and a<r<2*a,'Bertrand witness')
        need(p**33>=n**4 and p**11<=n**3<=q**11 and p*q*q<n<=p*q**3,'family domain')
        need(gcd(p*q,n)==1 and p*p<(F(n,p*q)) and q*q>=F(n,p*q),'family sieve')
        need(16*r<15*n,'original cutoff for epsilon0<=1/16')
        counts['unbounded_family_samples']+=1
    need((5,13) in native_pairs(10002,primes_upto(10002)),'H example native')
    need(5*13**3>=10002 and gcd(65,10002)==1,'H example active')
    need(5**4<=10002 and 65%5==0 and 10002%5!=0,'noncoprime smooth witness')
    examples['nonzero_H_witness']={'N':10002,'m':65,'q':5,'illustrative_R':100,'illustrative_Z':10,
                                  'not_actual_large_N_level':True,'H_single_mass': 'Li(10002/65)/4 > 0'}
    packing=[(k,l,k*l) for k in range(9) for l in range(4) if 4*k+9*l<33]
    need(max(x[2] for x in packing)==6,'packing max')
    counts['packing_cases']=len(packing)
    # Finite exact bilinear square-root envelope; square lengths avoid floats.
    for m,p,r in itertools.product((4,9,16,25),(4,9,16,25),(1,2,7)):
        lhs=F((m+4*r*r)*(p+4*r*r)*m*p,r*r)
        rhs=F(m*p,r)+2*isqrt(m*p)*(isqrt(m)+isqrt(p))+4*r*isqrt(m*p)
        need(lhs<=rhs*rhs,'bilinear envelope'); counts['bilinear_envelopes']+=1
    for n in (125,216,343,512):
        lo=floor_power(n,F(1,3)); hi=floor_power(n,F(2,3)); ps=primes_upto(n)
        for m in range(lo,hi+1):
            M=1<<(m.bit_length()-1); P=n//M
            for p in ps:
                if m*p>n: break
                need(M<=m<2*M and p<=P,'dyadic coverage'); counts['hyperbola_points']+=1
    for A in (4,5,6,8,12):
        row=parameter_row(A)
        need(row['small_SW']<=-A and row['large_front']<=-A and row['large_tail']<=-A and row['pi_Li']<=-A,'log saving')
        counts['parameter_ledgers']+=1
    for eps,q,l,h in itertools.product((F(0),F(1,1000),F(1,200)),(F(0),F(1,4),F(1,2)),
                                     (F(0),F(1,4),F(1,2)),(F(0),F(1,8),F(1,4))):
        fac=(1+154*eps)*(1+q)*(1+l)/(1-2*h)
        need(fac<8 and fac-1<=693*eps+3*q+2*l+4*h,'normalization bound')
        counts['normalization_models']+=1
    # Closed-interval bounded-variation transfer with a rational surrogate measure.
    grid=[F(k,10) for k in range(1,10)]
    for shift in range(7):
        nu=[F(((i+shift)%5)-2,100) for i in range(len(grid))]
        cdf=[]; s=F(0)
        for v in nu: s+=v; cdf.append(s)
        discrepancy=max(map(abs,cdf))
        for left,right in ((1,4),(2,8),(5,5),(1,9)):
            vals=[1/(2-t) for t in grid]
            got=sum((v*k for t,v,k in zip(grid,nu,vals) if F(left,10)<=t<=F(right,10)),F(0))
            need(abs(got)<=2*max(vals)*discrepancy,'closed interval transfer')
            counts['Stieltjes_models']+=1
    for x in (F(0),F(1,3),F(-7,9),F(10**25),F(1,2**100)):
        need(F(dec(x,False))<=x<=F(dec(x,True)),'serialization')
        counts['serialization_cases']+=1
    controls=0
    def reject(ok):
        nonlocal controls
        try: need(ok,'expected rejection')
        except ValueError: controls+=1
        else: raise ValueError('negative control accepted')
    reject(9 in primes_upto(9))
    reject(F(1,2)>=F(6,11))  # CP6 lower support does not contain G3
    reject(F(41,99)>=F(6,11))  # even the active support starts below CP6
    reject(5*13%5!=0)
    need((3,7) in native_pairs(1030,primes_upto(1030)), 'inactive control native domain')
    reject(3*7**3>=1030)   # actual native pair is in the zero wedge
    reject(4*F('0.84289')+F('5.40996')==F('0.84289')+F('5.40996'))
    need(all(p<10 for p,_ in factors(105)) and 105<3*100, 'presieve control support')
    reject(105<100)         # smooth modulus below W*D, but not D
    reject(abs(F(1)-F(1))==abs(F(1))+abs(F(-1)))
    reject(F(1)-F(1,2)==F(1)-2*F(1,2))  # sequence {3}, X=2, d=3: mass rebasing
    witness_pairs=native_pairs(370,primes_upto(370))
    need((3,7) in witness_pairs and (3,11) in witness_pairs, 'multiset control native domain')
    need(370-21*11==139==370-33*7 and 3*7**3>=370, 'multiset control identity')
    reject(len({139,139})==len([(21,11),(33,7)]))  # invalid de-duplication
    reject(F(9,19)-F(1,1000)==F(9,19))
    reject(3**2*15<142 and 3!=3) # excluded p1 cannot be declared a sieving prime
    return {'schema':'goldbach-switching-regressions/v1','counts':dict(sorted(counts.items())),
            'total_counted_cases':sum(counts.values()),'structural_negative_controls':controls,
            'examples':dict(examples, inactive_native_pair=[1030,3,7],
                            duplicate_index_witness={'N':370,'output':139,'indices':[[21,11],[33,7]]}),
            'scope':'finite exact identities; synthetic AP masses and surrogate CDFs, not asymptotic source validation',
            'mathematical_truth_verified':False}


def check():
    d=load('results.json'); validate_result(d)
    manifest=load('artifact-sha256.json')
    need(set(manifest['sha256'])==set(FILES),'manifest coverage')
    for name,digest in manifest['sha256'].items():
        need(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'hash mismatch '+name)
    tests=self_test(); need(tests==load('validation.json'),'finite replay mismatch')
    c=load('contracts.json')
    need(c['joint_coefficients']==COEFFICIENTS and c['global_status']=='INCONCLUSIVE','contract mutation')
    need(c['distribution']['old_CP6_directly_applicable'] is False,'old scope widening')
    need(c['H10_zero'] is False,'H erased')
    mutations=0
    for key,value in [('midpoint_evaluations',1),('piece_error_bounds',['0','0']),
                      ('actual_count_enclosure',True),('independently_verified',True),
                      ('global_status','PASS'),('safe_g10_upper','0'),
                      ('g10_removed_wedge_enclosure',['-1','0']),('g3_log_terms',1)]:
        bad=dict(d); bad[key]=value
        try: validate_result(bad)
        except (ValueError,KeyError,TypeError): mutations+=1
        else: raise ValueError('corrupt result accepted '+key)
    return {'ok':True,'hashes_checked':len(FILES),'finite_cases_replayed':tests['total_counted_cases'],
            'negative_controls_rejected':tests['structural_negative_controls']+mutations,
            'quadrature_replayed':False,'global_status':'INCONCLUSIVE','mathematical_truth_verified':False}


def main():
    p=argparse.ArgumentParser(description=__doc__); g=p.add_mutually_exclusive_group(required=True)
    for name in ('compute','self-test','check','require-global'): g.add_argument('--'+name,action='store_true')
    p.add_argument('--output',type=Path); args=p.parse_args()
    if args.require_global:
        print('REJECT: imported source inputs, independent review and global twelve-term closure are not discharged.'); return 1
    data=compute() if args.compute else self_test() if args.self_test else check()
    if args.output:
        need(not args.check,'check mode does not write')
        with args.output.open('x',encoding='utf-8') as f: f.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    elif args.compute: need(data==load('results.json'),'quadrature differs from frozen fields')
    print(json.dumps(data,ensure_ascii=False,indent=2)); return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError) as e:
        print('FAIL: '+str(e),file=sys.stderr); raise SystemExit(1)
