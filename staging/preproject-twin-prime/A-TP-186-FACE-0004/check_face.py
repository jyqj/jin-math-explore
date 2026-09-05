"""Finite exact tests and readback checks, NOT independent mathematical review.
The result check recomputes the final rational factors, not the integral.
"""
from fractions import Fraction as F
from pathlib import Path
from itertools import product
from collections import Counter
from math import prod
import json,hashlib,argparse,tempfile,random
import exact_backend as eb
import marginals as mg
EXPECTED_INPUT='2d22687c4842fa19b742a5dc4991cdbfdecbc12392d7eb0be938f6db222a5fbd'

def expect(condition,message):
    if not condition:raise ArithmeticError(message)

def check_input_bytes(raw):
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_INPUT:raise ValueError('frozen input bytes changed')
    return json.loads(raw)

def log_direct(x,bits):
    z=(x-1)/(x+1);p=z;total=F(0)
    for n in range(1000):
        total+=2*p/(2*n+1);p*=z*z
        tail=2*abs(p)/((2*n+3)*(1-z*z))
        if tail<F(1,1<<bits):return total-tail,total+tail
    raise ArithmeticError('direct log series')

def primitive_direct(j,k,bits):
    if j<=k:return F(j),F(j)
    ll,lh=log_direct(F(j,k),bits)
    lo,hi=2*j-k-j*lh,2*j-k-j*ll
    if j>2*k:
        y=F(j-2*k,k);p=y*y;g=F(0)
        # Independent exact rational evaluation of the finite delay polynomial.
        for c in mg.GCO:g+=c*p;p*=y
        tail=y**82/(82*(1-y));gl,gh=g-tail,g+tail
        l1,h1=log_direct(F(j-k,k),bits)
        lo+=(j*gl-(j-k)*h1+j-2*k)
        hi+=(j*gh-(j-k)*l1+j-2*k)
    return lo,hi

def naive_conv(a,b,n):
    return [sum((a[i]*b[j-i] for i in range(len(a)) if 0<=j-i<len(b)),0) for j in range(n)]

def pvalue(sig,coords):return prod(sum(t**e for t in coords) for e in sig)

def qconv(a,b,n):return naive_conv(a,b,n)

def moment(a,t,d,sig,n):
    powers=[[F(1)]+[F(0)]*(n-1)]
    for _ in range(d):powers.append(qconv(powers[-1],a,n))
    out=[F(0)]*n
    for bs,c in eb.parts(sig).items():
        term=powers[d-len(bs)]
        for e in bs:term=qconv(term,[x*y**e for x,y in zip(a,t)],n)
        coefficient=c*prod(range(d-len(bs)+1,d+1))
        out=[x+coefficient*y for x,y in zip(out,term)]
    return out

def marked_moment(a,b,t,d,sig,n):
    out=[F(0)]*n
    for (own,bs),ct in eb.marked_parts(sig).items():
        base=[F(1)]+[F(0)]*(n-1)
        for _ in range(d-1-len(bs)):base=qconv(base,a,n)
        for e in bs:base=qconv(base,[x*y**e for x,y in zip(a,t)],n)
        base=qconv(base,[x*y**own for x,y in zip(b,t)],n)
        c=d*ct*prod(range(d-1-len(bs)+1,d))
        out=[x+c*y for x,y in zip(out,base)]
    return out

def self_test():
    data=check_input_bytes((eb.HERE/'inputs.json').read_bytes());checks={};rejected=[]
    eb.init_backend();rng=random.Random(20260905)
    for trial in range(25):
        a=[rng.getrandbits(510) for _ in range(1+trial%9)]
        b=[rng.getrandbits(509) for _ in range(1+trial%7)];n=1+trial%18
        expect(eb.rawconv(a,b,n)==naive_conv(a,b,n),'GMP linear convolution mismatch')
    checks['positive_GMP_products']=25
    coeffs=[3,-2,4,0,1,-1,2];h=F(1,100);a=list(range(1,41));errors=[1+q%3 for q in range(40)]
    total=0
    for left,right in ((0,39),(7,20),(30,39)):
        centers,radii,den=mg.slide(coeffs,a,errors,h,left,right,50);value=mg.poly_setup(coeffs,h)[0]
        for r in range(51):
            qs=range(max(0,left-r),min(39,right-r)+1)
            dot=sum(a[q]*value(r+q) for q in qs)
            extreme=sum(errors[q]*abs(value(r+q)) for q in qs)
            expect(dot==centers[r] and extreme<=radii[r],'sliding center/error mismatch');total+=1
    checks['sliding_exact_windows']=total
    logs=mg.master_logs(32,68,96);low,high=mg.cap_cells(32,68,96,logs,32)
    for j in range(68):
        a0,a1=primitive_direct(j,32,150);b0,b1=primitive_direct(j+1,32,150)
        expect(F(low[j],1<<96)<=b0-a1<=b1-a0<=F(high[j],1<<96),'cap primitive enclosure')
    checks['cap_exact_primitive_comparisons']=68
    coords=[F(1,5),F(2,7)];z=F(3,11)
    for sig in map(tuple,data['signatures']):
        lhs=pvalue(sig,coords+[z]);rhs=sum(c*pvalue(rem,coords)*z**e for (rem,e),c in mg.fibers(sig).items())
        expect(lhs==rhs,'labeled erasure identity')
    checks['angular_erasure_identities']=11
    L,C,count=7,20,60;q=(3*eb.B//4,3*eb.B//4)
    U=eb.density_envelope(count,L,C,q)
    for j in range(L,count):
        numer=sum(F(U[j-k])*F(3,4)**(k-1) for k in range(1,L) if j-k>=0)+sum(F(U[j-k]) for k in range(L,C+1) if j-k>=0)
        expect(U[j]>=min(eb.B,numer/(j-1)),'positive renewal rolling sum')
    checks['renewal_exact_rolling_comparisons']=count-L
    # Tiny exact face identity includes both mark locations and signed squares.
    d=3;n=10;ts=[F(2*q+1,10) for q in range(4)];aa=[F(1,5),F(1,7),F(1,11),F(1,13)];bb=[F(0),F(1,17),F(1,19),F(1,23)]
    sigs=[(),(2,),(2,2)];co=[F(1),F(-3),F(2)];R=[F((s+1)%7,11) for s in range(10)]
    direct_e=direct_r=F(0)
    for inds in product(range(4),repeat=d):
        q,*js=inds;r=sum(js);v=sum(c*pvalue(sig,[ts[j] for j in js]) for sig,c in zip(sigs,co));weight=R[r+q]*v*v
        direct_e+=weight*bb[q]*prod(aa[j] for j in js)
        direct_r+=weight*aa[q]*sum(bb[js[i]]*prod(aa[js[k]] for k in range(d-1) if k!=i) for i in range(d-1))
    fd=[sum(R[r+q]*bb[q] for q in range(4) if r+q<len(R)) for r in range(n)]
    fa=[sum(R[r+q]*aa[q] for q in range(4) if r+q<len(R)) for r in range(n)]
    coefficients=Counter()
    for i,s in enumerate(sigs):
        for j in range(i,len(sigs)):coefficients[tuple(sorted(s+sigs[j]))]+=co[i]*co[j]*(1 if i==j else 2)
    got_e=got_r=F(0)
    for sig,c in coefficients.items():
        m=moment(aa,ts,d-1,sig,n);dm=marked_moment(aa,bb,ts,d-1,sig,n)
        got_e+=c*sum(x*y for x,y in zip(m,fd));got_r+=c*sum(x*y for x,y in zip(dm,fa))
    expect((got_e,got_r)==(direct_e,direct_r) and got_e>0 and got_r>0,'face location/partition identity')
    checks['two_mark_location_face_identity']=True
    def reject(name,fn):
        try:fn()
        except (ValueError,ArithmeticError,KeyError):rejected.append(name);return
        raise ArithmeticError('bad input accepted: '+name)
    reject('mutated_coefficients',lambda:check_input_bytes((eb.HERE/'inputs.json').read_bytes().replace(b'121730820431102',b'121730820431103')))
    reject('negative_convolution',lambda:eb.rawconv([-1],[2],1))
    reject('bool_convolution',lambda:eb.rawconv([True],[2],1))
    reject('zero_convolution_length',lambda:eb.rawconv([1],[2],0))
    reject('cap_outside_delay_range',lambda:mg.cap_cells(32,69,96,logs,32))
    reject('negative_delay',lambda:mg.extra_delay(F(-1,10),96))
    reject('oversized_delay',lambda:mg.extra_delay(F(1,4),96))
    reject('invalid_log_domain',lambda:mg.log_increment(0,96))
    reject('negative_weight_radius',lambda:mg.slide(coeffs,[1],[-1],h,0,0,0))
    reject('invalid_renewal_domain',lambda:eb.density_envelope(20,1,5,q))
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'test.bin';record=mg.save_intervals(p,{'test':([-7,0,3],[-5,0,8])},160,{'test':True});header,values=mg.read_intervals(p)
        expect(values=={'test':([-7,0,3],[-5,0,8])},'signed array roundtrip')
        p.write_bytes(b'BADMAGIC'+p.read_bytes()[8:]);reject('corrupt_array_magic',lambda:mg.read_intervals(p))
    checks['signed_array_roundtrip']=True
    return {'ok':True,'scope':'finite_exact_algebra_and_backend_tests_only','checks':checks,'rejected':rejected,'independent_verification':False,'full_integral_recomputed':False}

def check_result(path):
    data=check_input_bytes((eb.HERE/'inputs.json').read_bytes());r=json.loads(Path(path).read_text());f=r['absolute_upper_factors']
    expect(r['input_sha256']==EXPECTED_INPUT and r['bits']==160 and r['source_row']=='G0:R00','receipt binding')
    expect(f['face_count']==40 and f['physical_marginal_factor']==str(F(data['h'])**2) and f['common_scale']=='1/360','physical factors')
    Z=int(f['normalizer_lower_integer']);T=int(f['contraction_upper_integer']);scale=int(f['fixed_point_scale'])
    expect(Z>0 and T>=0 and scale==1<<160,'result signs/scales')
    val=40*F(data['h'])**2*F(T,scale)*F(scale,360*Z)**40/F(data['Iref'])*10**18
    up=eb.ceilf(val*10**8)
    expect(up==r['face_relative_upper_units_1e8'],'reported rounding')
    expect(r['face_target_met_arithmetically']==(up<=10**9),'target flag')
    return {'ok':True,'scope':'saved_result_final_rational_factors_only','face_upper_units_1e8':up,'target_met':up<=10**9,'full_integral_recomputed':False,'independent_verification':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();g=parser.add_mutually_exclusive_group(required=True);g.add_argument('--self-test',action='store_true');g.add_argument('--check-result',type=Path);args=parser.parse_args()
    print(json.dumps(self_test() if args.self_test else check_result(args.check_result),indent=2,sort_keys=True))
