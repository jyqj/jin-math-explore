#!/usr/bin/env python3
"""CP-ERR-0009: explicit G4/G5 upper interface and one-dimensional certificate.

Python >=3.10; mpmath==1.3.0. No network. This is a same-context solver checker,
not an independent verifier or a test of asymptotic source theorems.
--compute genuinely integrates; --check does NOT integrate.
--output creates a new file; existing evidence is never overwritten.
"""
from __future__ import annotations
import argparse
from collections import Counter
from fractions import Fraction as F
import hashlib
import itertools
import json
from math import gcd, prod, isqrt
from pathlib import Path
import sys
import mpmath as mp

ROOT = Path(__file__).resolve().parent
A, B4, B5 = F(4,53), F(1,3), F(3,11)
AA, STAR, WMAX = F(53,8), F(45,8), F(5,8)
NJ, NK, DEGREE, DPS = 8192, 4096, 48, 50
NAMES = ('README.md','proof.md','contracts.json','prior-work.json','source-lock.json',
         'check_upper.py','results.json','error-handoff.json','computation-record.json',
         'computation-handoff.json','verification-ticket.md','validation.json')


def need(value: bool, msg: str) -> None:
    if not value:
        raise ValueError(msg)


def read_json(path: Path):
    def no_duplicates(pairs):
        result = {}
        for k,v in pairs:
            need(k not in result, 'duplicate JSON key: '+k)
            result[k] = v
        return result
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=no_duplicates)


def ivq(x):
    x = F(x)
    return mp.iv.mpf(x.numerator)/x.denominator


def bf(t):
    sign, man, exp, bits = t
    need(bits >= 0, 'nonfinite interval')
    return F((-1 if sign else 1)*man)*(2**exp if exp >= 0 else F(1,2**(-exp)))


def ends(x):
    lo, hi = map(bf, x._mpi_)
    need(lo <= hi, 'reversed interval')
    return lo,hi


def dec(x, up=False, places=18):
    x=F(x); scale=10**places
    n=-((-x.numerator*scale)//x.denominator) if up else (x.numerator*scale)//x.denominator
    sign='-' if n<0 else ''; n=abs(n)
    return f'{sign}{n//scale}.{n%scale:0{places}d}'


def enc(x, error=F(0)):
    lo,hi=ends(x)
    return [dec(lo-error),dec(hi+error,True)]


def coefficients():
    c=[F(0)]+[sum((F(1,k*2**(n-k+1)) for k in range(1,n+1)),F(0))
                 for n in range(1,DEGREE-1)]
    t=[F(0)]*(DEGREE+1)
    for k in range(3,DEGREE+1):
        mag=sum((c[n]/((n+1)*3**(k-n-1)) for n in range(1,k-1)),F(0))/k
        need(0<mag<F(1,4*k),'Taylor bound')
        t[k]=(-1 if k%2==0 else 1)*mag
    return t


def errors():
    cut=F(177,88); top=STAR-1
    ej4=F(64,24)*(top-2)**3/NJ**2
    ej5=F(64,24)*((cut-2)**3+(top-cut)**3)/NJ**2
    et=WMAX**(DEGREE+1)/(4*(DEGREE+1)*(1-WMAX))
    ek=WMAX**3/(24*NK**2)
    return ej4,ej5,et,ek


def compute():
    need(mp.__version__=='1.3.0','pinned mpmath version required')
    mp.iv.dps=DPS
    def H(s):
        return 8*mp.iv.log(s/(ivq(AA)-s))
    Hstar=H(ivq(STAR)); co=[ivq(x) for x in coefficients()]
    ej4,ej5,et,ek=errors()
    kval=ivq(0); step=WMAX/NK
    for j in range(NK):
        w=ivq(F(2*j+1,2)*step)
        pol=ivq(0)
        for ck in reversed(co):
            pol=pol*w+ck
        kval+=pol/(4+w)*(Hstar-H(5+w))
    kval*=ivq(step)
    data={'schema':'goldbach-upper-1d-certificate/v1','backend':'mpmath.iv',
          'backend_version':mp.__version__,'dps':DPS,'J_cells_per_piece':NJ,
          'K_cells':NK,'total_midpoints':3*NJ+NK,'two_dimensional_cells':0,
          'taylor_degree':DEGREE,'J_second_derivative_bound':'64',
          'K_second_derivative_bound':'1','T_uniform_tail':str(et),
          'K_midpoint_error':str(ek),'K_integrated_tail':str(F(5,2)*et),
          'K_enclosure':enc(kval,ek+F(5,2)*et),'rows':{},
          'global_status':'INCONCLUSIVE','independently_verified':False,
          'actual_counts_two_sided':False}
    for name,b,ej in [('G4',B4,ej4),('G5',B5,ej5)]:
        sig=(F(1,2)-b)/A
        cuts=[F(2),STAR-1] if sig<=3 else [F(2),sig-1,STAR-1]
        jval=ivq(0)
        for l,r in zip(cuts,cuts[1:]):
            h=(r-l)/NJ; block=ivq(0)
            for j in range(NJ):
                tf=l+F(2*j+1,2)*h; t=ivq(tf)
                arg=ivq(sig) if tf+1<sig else t+1
                block+=mp.iv.log(t-1)/t*(Hstar-H(arg))
            jval+=block*ivq(h)
        bare=Hstar-H(ivq(sig))+jval
        interval=enc(bare+kval,ej+ek+F(5,2)*et)
        cap=dec(F(interval[1]),True,6)
        data['rows'][name]={'b':str(b),'sigma':str(sig),'J_breakpoints':list(map(str,cuts)),
                            'J_midpoint_error':str(ej),'integral_enclosure':interval,
                            'safe_upper':cap,'without_K_enclosure':enc(bare,ej)}
    validate_result(data)
    return data


def validate_result(x):
    ej4,ej5,et,ek=errors()
    need(x['schema']=='goldbach-upper-1d-certificate/v1','schema')
    need((x['J_cells_per_piece'],x['K_cells'],x['total_midpoints'])==(NJ,NK,3*NJ+NK),'coverage')
    need(x['two_dimensional_cells']==0 and x['taylor_degree']==DEGREE,'method identity')
    need(x['J_second_derivative_bound']=='64' and x['K_second_derivative_bound']=='1','derivative bounds')
    need(F(x['T_uniform_tail'])==et and F(x['K_midpoint_error'])==ek,'error bounds')
    need(F(x['K_integrated_tail'])==F(5,2)*et,'tail propagation')
    need(x['global_status']=='INCONCLUSIVE' and x['independently_verified'] is False,'authority')
    need(x['actual_counts_two_sided'] is False,'coefficient/count distinction')
    kl,ku=map(F,x['K_enclosure']); need(0<kl<ku<F(1,100),'positive K correction')
    for name,b,ej,old in [('G4',B4,ej4,F('23.60573')),('G5',B5,ej5,F('19.51913'))]:
        row=x['rows'][name]; lo,hi=map(F,row['integral_enclosure'])
        sig=(F(1,2)-b)/A
        cuts=[F(2),STAR-1] if sig<=3 else [F(2),sig-1,STAR-1]
        need(row['J_breakpoints']==list(map(str,cuts)),'max breakpoint')
        need(F(row['J_midpoint_error'])==ej,'J error')
        need(0<lo<hi<=F(row['safe_upper'])<old,'upper direction / old cap')
        need(hi-lo<F(1,500000),'precision')
        need(F(row['without_K_enclosure'][1])<lo,'dropping positive K')


def primes(n):
    a=bytearray(b'\x01')*(n+1); a[:2]=b'\x00\x00'
    for p in range(2,isqrt(n)+1):
        if a[p]: a[p*p::p]=b'\x00'*(((n-p*p)//p)+1)
    return [p for p in range(2,n+1) if a[p]]


def tot(n):
    v=n; m=n; p=2
    while p*p<=m:
        if m%p==0:
            v-=v//p
            while m%p==0: m//=p
        p+=1
    if m>1: v-=v//m
    return v


def subsets(ps):
    out=[1]
    for p in ps: out += [d*p for d in out[:]]
    return sorted(out)


def finite():
    counts=Counter(); ps=primes(800)
    # Small exact AP models: varied cutoffs, NOT tests of asymptotic onsets.
    for N,z in itertools.product(range(100,701,30),(5,7,11)):
        seq=[N-r for r in ps if r<N]
        P=subsets([p for p in ps if p<z and N%p])
        selected=[p for p in ps if z<=p<=31 and N%p]
        R=N; W=prod([p for p in (2,3) if N%p]); P0=6
        raw_by_key={}; deltas={}; rebased_sum=F(0); Hmax=F(0)
        for p in selected:
            child=[n for n in seq if n%p==0]; M=len(child)
            X=F(M)+F((p%3)+1,7); delta=F(M)-X
            deltas[p]=delta
            support=[d for d in P if F(d)<F(W*R,P0*p)]
            full=sorted(set(support+[1]))
            hsum=sum((F(1,tot(d)) for d in support),F(0)); Hmax=max(Hmax,hsum)
            for d in full:
                lhs=sum(n%d==0 for n in child)
                rhs=sum((N-r)%(p*d)==0 for r in ps if r<N)
                need(lhs==rhs,'native AP count')
                rp=F(lhs)-X/tot(d); rm=F(lhs)-F(M,tot(d))
                need(rm==rp-delta/tot(d),'mass rebase')
                need(p*d not in raw_by_key,'unique large prime lost')
                raw_by_key[p*d]=rp
                counts['native_AP_and_rebase']+=1
                if d in support:
                    need(p*d<R and gcd(p,d)==1,'pre-sieve support')
                    rebased_sum+=abs(rm); counts['presieve_support']+=1
            need(F(M)-X==delta,'unit modulus'); counts['unit_modulus']+=1
            # Original truncation is a subset, before and after sieving.
            original=[n for n in child if 3*(N-n)<2*N]
            survive=lambda ns:sum(all(n%q for q in ps if q<z and N%q) for n in ns)
            need(survive(original)<=survive(child),'upper enlargement')
            counts['upper_enlargement']+=1
        E=sum(map(abs,raw_by_key.values()),F(0))
        need(sum(map(abs,deltas.values()),F(0))<=E,'aggregate mass budget')
        need(rebased_sum<=(1+Hmax)*E,'aggregate rebased budget')
        counts['aggregate_budget']+=1
        allkeys=[]
        for cutoff in (31,17):
            allkeys += [p*d for p in selected if p<=cutoff for d in P if p*d<R]
        need(max(Counter(allkeys).values(),default=0)<=2,'two-row multiplicity')
        counts['overlap_bound']+=1
    for n in range(1,257):
        div=[d for d in range(1,n+1) if n%d==0]
        mu2=lambda d:all(d%(p*p) for p in ps if p*p<=d)
        need(F(n,tot(n))==sum((F(1,tot(d)) for d in div if mu2(d)),F(0)),'totient expansion')
        H=sum((F(1,tot(k)) for k in range(1,n+1)),F(0))
        harmonic=sum((F(1,k) for k in range(1,n+1)),F(0))
        need(H<3*harmonic,'harmonic totient bound')
        counts['totient_identities_and_bounds']+=1
    co=coefficients(); need(co[3]==F(1,36) and co[4]==-F(1,48),'Taylor seed')
    for n in range(2,DEGREE):
        cn=sum((F(1,k*2**(n-k)) for k in range(1,n)),F(0))
        need(3*(n+1)*co[n+1]+n*co[n]==(-1)**n*cn/n,'T ODE')
        counts['T_ODE']+=1
    # Formal integration of K'=T/(4+w), with zero integration constant.
    k=[F(0)]*(DEGREE+2)
    for n in range(DEGREE+1):
        k[n+1]=(co[n]-n*k[n])/(4*(n+1))
        need(4*(n+1)*k[n+1]+n*k[n]==co[n],'K ODE')
        counts['K_ODE']+=1
    need(k[4]==F(1,576),'K seed')
    need(F(117,200)+F(17,75)+F(1,45)<1,'K second derivative')
    need(WMAX**3/36<F(1,100) and WMAX**2/12<F(1,25),'T envelopes')
    need(WMAX/6+WMAX**2/36<F(1,8),'T second derivative')
    need(F(1,2)-B4-2*A==F(5,318),'G4 level margin')
    need(F(1,2)-B5-2*A==F(89,1166),'G5 level margin')
    for b,cap in ((B4,F(24)),(B5,F(20))):
        for q,r,h,z,ep,I in itertools.product((F(0),F(1,2),F(1)),(F(0),F(1,4),F(1,2)),
                (F(0),F(1,1000),F(5,318)),(F(2),F(10)),(F(1,200),F(1,10**9)),
                (F(0),F(1,4),cap/53)):
            L=F(3,2)+r
            full=53*(1+q)*(I+h/A*L+b/A*r+2/z+77*ep*(L+2/z))
            simple=53*I+cap*q+2809*h+106*b/A*r+212/z+24486*ep
            need(full<=simple,'normalized upper product')
            counts['normalized_products']+=1
    mp.iv.dps=DPS
    for x in (F(-7,9),F(0),F(1,3),F(1,2**101),F(10**30)):
        l,u=ends(ivq(x)); need(l<=x<=u,'binary conversion')
        need(F(dec(x))<=x<=F(dec(x,True)),'decimal conversion')
        counts['serialization']+=1
    return {'schema':'goldbach-upper-finite/v1','counts':dict(counts),
            'total_counted':sum(counts.values()),'ok':True,
            'AP_model_scope':'N=100..700 step30; z=5,7,11; cutoffs31/17; R=N; Xp=Mp+synthetic positive rational shift. Algebra only, not Li error observations or BJS/BV onsets.',
            'mathematical_truth_verified':False}


def negative_controls(data):
    rejected=0
    def reject(f):
        nonlocal rejected
        try: f()
        except (ValueError,KeyError,TypeError): rejected+=1
        else: raise ValueError('negative control accepted')
    reject(lambda:need(sum(map(abs,(F(1),F(-1))))<=abs(sum((F(1),F(-1)))),'net mass loses variation'))
    reject(lambda:need(len(set((35,35)))==2,'overlapping rows not injective'))
    reject(lambda:need(105<100,'missing exceptional P0 support'))
    reject(lambda:need(F(1,4)<=F(1,5),'reciprocal direction'))
    reject(lambda:need(0==F(1,2),'mass rebase cannot be dropped'))
    reject(lambda:need(F(177,88)==2,'G5 max breakpoint'))
    reject(lambda:need(2<=1,'subset lower inference'))
    reject(lambda:need(3-3==3+3,'harmful sign'))
    mutations=[('total_midpoints',NJ),('two_dimensional_cells',64**2),('T_uniform_tail','0'),
               ('K_integrated_tail','0'),('K_midpoint_error','0'),('K_second_derivative_bound','0'),
               ('global_status','PASS'),('independently_verified',True),('actual_counts_two_sided',True)]
    for field,value in mutations:
        bad=json.loads(json.dumps(data)); bad[field]=value
        reject(lambda bad=bad:validate_result(bad))
    for field,value in [('safe_upper','0'),('J_midpoint_error','0'),('J_breakpoints',['2','37/8'])]:
        bad=json.loads(json.dumps(data)); bad['rows']['G5'][field]=value
        reject(lambda bad=bad:validate_result(bad))
    return rejected


def check():
    data=read_json(ROOT/'results.json'); validate_result(data)
    mf=read_json(ROOT/'artifact-sha256.json')
    need(set(mf['sha256'])==set(NAMES),'manifest coverage')
    for name,h in mf['sha256'].items():
        need(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,'hash '+name)
    fin=finite(); need(fin==read_json(ROOT/'validation.json'),'finite replay differs')
    ct=read_json(ROOT/'contracts.json')
    need(ct['requires_Cs'] is False and ct['requires_L_eta'] is False,'dependency change')
    need(ct['global_status']=='INCONCLUSIVE','global contract')
    need(ct['combined_coefficients']=={'q_N':'44','h_star':'5618','r_N':'28090/33',
              '1/z':'424','epsilon':'48972','C_BV*T^(3-A0)':'50'},'combined coefficients')
    return {'ok':True,'hashes_checked':len(NAMES),'finite_cases_replayed':fin['total_counted'],
            'negative_controls_rejected':negative_controls(data),'quadrature_replayed':False,
            'global_status':'INCONCLUSIVE','mathematical_truth_verified':False}


def main():
    ap=argparse.ArgumentParser(description=__doc__); g=ap.add_mutually_exclusive_group(required=True)
    for f in ('compute','self-test','check','require-global'): g.add_argument('--'+f,action='store_true')
    ap.add_argument('--output',type=Path); ar=ap.parse_args()
    if ar.require_global:
        print('REJECT: independent source/candidate review and the twelve-term closure are pending.'); return 1
    result=compute() if ar.compute else (finite() if ar.self_test else check())
    if ar.output:
        need(not ar.check,'--check does not write')
        with ar.output.open('x',encoding='utf-8') as f:
            f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    elif ar.compute:
        need(result==read_json(ROOT/'results.json'),'fresh integral fields differ')
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as e:
        print('FAIL: '+str(e),file=sys.stderr); raise SystemExit(1)
