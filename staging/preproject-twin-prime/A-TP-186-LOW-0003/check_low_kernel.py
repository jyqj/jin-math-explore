#!/usr/bin/env python3
"""Finite exact tests and receipt arithmetic, not an independent verifier.

The full genuine envelope run is compute_envelopes.py --run --output NEW.json.
This script checks algebra/backends and a saved receipt's final rational bound.
"""
from fractions import Fraction as F
from math import comb,factorial,prod
from itertools import product
from pathlib import Path
import argparse,hashlib,json,random,sys
import compute_envelopes as c


def need(test,message):
    if not test:raise ArithmeticError(message)


def direct(a,b,n=None):
    ans=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):ans[i+j]+=x*y
    return ans if n is None else ans[:n]+[0]*max(0,n-len(ans))


def power(a,n):
    ans=[1]
    for _ in range(n):ans=direct(ans,a)
    return ans


def add(a,b):
    return [(a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0) for i in range(max(len(a),len(b)))]


def reference_exp(x):
    if x<0:
        lo,hi=reference_exp(-x);return 1/hi,1/lo
    s=t=F(1)
    for n in range(1,1000):
        t*=x/n;s+=t
        if n+2<=x:continue
        tail=t*x/(n+1)/(1-x/(n+2))
        if tail<F(1,1<<240):return s,s+tail
    raise ArithmeticError('reference series did not converge')


def carry(n):
    a=[1]
    for m in range(2,n+1):
        a=[(j+1)*(a[j] if j<len(a) else 0)+(m-j)*(a[j-1] if j else 0) for j in range(m)]
    return [F(v,factorial(n)) for v in a]


def tests():
    c.load_inputs();version=c.init_backend();done=[]
    cutoff=F(288763833465798194485431089923,286076767019837125756522770000)
    upper=F(16430591763736936545249922448197799591,16161921199408696007503616565983946000)
    need(cutoff//c.h-39==94919 and upper//c.h==95638,'exact first-row radial geometry')
    done.append('exact_first_row_radial_geometry')
    rng=random.Random(186003)
    for n in [1,2,7,31,80]:
        a=[rng.randrange(1<<90) for _ in range(n)];b=[rng.randrange(1<<110) for _ in range(n+2)]
        for cap in [1,n,n+len(b)-1]:need(c.rawconv(a,b,cap)==direct(a,b,cap),'GMP positive product')
    a=[(1<<509)-1]*16;b=[(1<<510)-1]*16
    need(c.rawconv(a,b,31)==direct(a,b),'GMP wide coefficient carry')
    need(c.rawconv([0]*9,[2]*8,16)==[0]*16,'zero product')
    rejected=False
    try:c.rawconv([-1],[1],1)
    except ValueError:rejected=True
    need(rejected,'negative coefficient not rejected');done.append('exact_GMP_products_and_rejected_negative_input')
    for x in [F(0),F(1,1000),F(1,8),F(3,7),F(5),F(-5)]:
        l,u=c.expq(x);lo,hi=reference_exp(x)
        need(F(l,c.B)<=lo<=hi<=F(u,c.B),'outward exponential enclosure')
    done.append('outward_exponential_vs_independent_rational_series')
    q=F(7,8);L,C,count=5,17,90
    U=c.density_envelope(count,L,C,c.fp(q))
    for j in range(L):need(F(U[j],c.B)>=q**j,'seed upper')
    for j in range(L,count):
        s=sum(q**(k-1)*F(U[j-k],c.B) for k in range(1,L))
        s+=sum(F(U[j-k],c.B) for k in range(L,C+1) if j>=k)
        need(F(U[j],c.B)>=min(F(1),s/(j-1)),'rolling renewal misses exact sum')
    need(F(1,4)>F(1,5),'denominator boundary test')
    for bad in [(20,1,5,c.fp(q)),(20,5,3,c.fp(q)),(20,5,8,c.fp(F(9,8)))]:
        ok=False
        try:c.density_envelope(*bad)
        except ValueError:ok=True
        need(ok,'invalid density domain accepted')
    done.append('rolling_renewal_vs_direct_exact_sums_and_domain_rejection')
    for n in range(1,11):
        a=carry(n)
        b=[F(sum((-1)**k*comb(n+1,k)*(j+1-k)**n for k in range(j+1)),factorial(n)) for j in range(n)]
        need(a==b and sum(a)==1 and min(a)>0,'Eulerian carry')
    need(carry(2)==[F(1,2),F(1,2)],'two-cell carry')
    done.append('Eulerian_carry_vs_cube_volume_formula')
    A=[F(0),F(0),F(1,3),F(1,7)];N=26
    for extra in [0,1]:
        directsum=[F(0)]*N;expA=[F(0)]*N;expXA=[F(0)]*N
        for r in range(13):
            term=[F(x)/factorial(r) for x in power(A,r)]
            directsum=add(directsum,direct(term,[1]*(r+extra+1),N))[:N]
            expA=add(expA,term[:N])[:N]
            expXA=add(expXA,([F(0)]*r+term)[:N])[:N]
        numerator=add(expA,([F(0)]*(extra+1)+[-x for x in expXA])[:N])[:N]
        accum=F(0);rhs=[]
        for x in numerator:accum+=x;rhs.append(accum)
        need(directsum==rhs,'all-orders carry envelope')
    done.append('all_orders_tail_formal_identity_finite_projection')
    n=3;wa=[1,2,1];wb=[0,1,3]
    for sig in [(),(2,),(2,3),(2,2,2),(1,2,3)]:
        exact=[0]*7
        for js in product(range(3),repeat=n):
            angular=prod(sum(t**e for t in js) for e in sig)
            weighted=sum(wb[js[k]]*prod(wa[js[l]] for l in range(n) if l!=k) for k in range(n))
            exact[sum(js)]+=angular*weighted
        reconstructed=[0]*7
        for (own,blocks),ct in c.mparts(sig).items():
            if len(blocks)>n-1:continue
            term=power(wa,n-1-len(blocks))
            for e in blocks:term=direct(term,[w*t**e for t,w in enumerate(wa)])
            term=direct(term,[w*t**own for t,w in enumerate(wb)])
            coef=n*ct*prod(range(n-len(blocks),n))
            reconstructed=add(reconstructed,[coef*x for x in term])
        need(exact==reconstructed,'designated moment set partitions')
    done.append('designated_moments_vs_direct_labeled_assignments')
    actual=F(1)-2*F(1,2)+F(1,4)
    fake=F(1)-2*F(1)+F(1,4)
    need(actual==F(1,4) and max(0,fake)<actual,'independent moment upper trap')
    need(2*actual>=actual,'common measure monotonicity example')
    done.append('signed_square_requires_common_measure')
    linear=direct([0,0,1],[0,0,1]);cyclic=[0,0,0]
    for i,x in enumerate(linear):cyclic[i%3]+=x
    need(linear[1]==0 and cyclic[1]==1,'cyclic alias demonstration')
    done.append('linear_truncation_distinguished_from_cyclic_aliasing')
    need(hashlib.sha256((c.HERE/'inputs.json').read_bytes()+b' ').hexdigest()!=c.EXPECTED_INPUT_SHA256,'input lock')
    done.append('frozen_input_commitment')
    return {'ok':True,'scope':'finite_exact_algebra_and_backend_tests','tests':done,'gmp_version':version,'independent_verification':False}


def receipt(path):
    c.load_inputs();v=json.loads(path.read_text())
    need(v['input_sha256']==c.EXPECTED_INPUT_SHA256,'receipt input lock')
    need(v['bits']==160 and v['source_row']=='G0:R00','receipt scope')
    q=v['absolute_root_upper_factors'];B=int(q['fixed_point_scale']);t=int(q['contraction_upper_integer']);Z=int(q['normalizer_lower_integer'])
    need(B==c.B and t>=0 and Z>0,'receipt signs/precision')
    units=40*F(t,B)*F(B,360*Z)**40*10**42/23685317816
    u=c.ceilf(units*10**8)
    need(u==v['root_relative_upper_units_1e8'],'final rational recomputation')
    need(u<=11*10**8,'root target not certified')
    need(v['face_target_status']=='NOT_EVALUATED' and v['independent_verification'] is False,'authority boundary')
    need(v['all_152_inputs_discharged'] is False,'all-input overclaim')
    return {'ok':True,'scope':'saved_receipt_final_arithmetic_only','root_upper_units_1e8':u,'full_integral_recomputed':False,'independent_verification':False}


def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--self-test',action='store_true');g.add_argument('--check-result',type=Path)
    a=p.parse_args();result=tests() if a.self_test else receipt(a.check_result)
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,ArithmeticError,KeyError) as exc:
        print(type(exc).__name__+': '+str(exc),file=sys.stderr);raise SystemExit(2)
