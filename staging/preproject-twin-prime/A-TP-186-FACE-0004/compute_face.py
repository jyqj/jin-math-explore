"""Genuine G0:R00 face upper envelope, from fresh positive source laws.

Marginal artifacts must be produced by marginals.py and hash-bound; no saved
source moments or integral answers are read. Scope: one face scalar only.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter,defaultdict
from functools import lru_cache
from math import prod
import json,sys,time,hashlib,resource,platform,argparse,gc
import exact_backend as eb
from exact_backend import B,P,require,fp,mul,times,plus,expq,ceildiv,floorf,ceilf,conv,parts,marked_parts,HERE,load_inputs
from marginals import read_intervals

def coordinate_inputs(data):
    h=F(data['h']);N=data['rmax']+1;count=data['count'];started=time.monotonic()
    U=eb.density_envelope(count,data['first'],data['cap_index'],expq(-data['theta']*h))
    density_hash=eb.integer_hash(U)
    mark=[0]*data['last']
    for q in range(data['first'],data['last']):mark[q]=ceildiv(B,q)
    # Exact fixed dyadic mark dominates 1/q. Freeze D_j to a common upper mass.
    raw=eb.rawconv(U[:N],mark,N)
    W=[ceildiv(raw[j]+(raw[j-1] if j else 0),2*B) for j in range(N)]
    del raw,mark
    A=[([],[]) for _ in range(13)];D=[([],[]) for _ in range(13)]
    EA=([],[]);ED=([],[]);Zlo=Zhi=0
    ex=expq(-3*h);ratio=expq(-6*h)
    for j in range(count):
        t=(F(j)+F(1,2))*h
        g=F(21,200)/(1+t/100)+F(179,200)/(1+F(907,5)*t)
        z=h*g*g;Zlo+=floorf(z*B);Zhi+=ceilf(z*B)
        if j<N:
            weight=times(360*z,ex);a=mul(weight,(U[j],U[j]));d=mul(weight,(W[j],W[j]))
            erased=times(360*h,ex);ea=mul(erased,(U[j],U[j]));ed=mul(erased,(W[j],W[j]))
            EA[0].append(ea[0]);EA[1].append(ea[1]);ED[0].append(ed[0]);ED[1].append(ed[1])
            power=F(1)
            for e in range(13):
                lo,hi=times(power,a);A[e][0].append(lo);A[e][1].append(hi)
                lo,hi=times(power,d);D[e][0].append(lo);D[e][1].append(hi);power*=t
        ex=mul(ex,ratio)
    del U,W
    # Rtilt(s) is short-supported. Crop its leading zeros before convolution.
    rmin=data['rmin'];rmax=data['rmax'];theta=data['theta']
    x=theta*(data['last']*h-F(data['threshold'])+20*h)+(theta+6)*(rmin+20)*h
    v=expq(x);step=expq((theta+6)*h);R=([],[])
    for s in range(rmin,rmax+1):
        R[0].append(v[0]);R[1].append(v[1]);v=mul(v,step)
    offset=N-1-rmin;full_length=len(R[0])+N-1
    def erased_correlation(E):
        lo=[z//B for z in eb.rawconv(R[0],E[0][::-1],full_length)][offset:offset+N]
        hi=[ceildiv(z,B) for z in eb.rawconv(R[1],E[1][::-1],full_length)][offset:offset+N]
        require(len(lo)==N and len(hi)==N,'erased correlation shape')
        return lo,hi
    FA,FD=erased_correlation(EA),erased_correlation(ED)
    print('COORDINATES',round(time.monotonic()-started,3),'density',density_hash,file=sys.stderr,flush=True)
    return A,D,FA,FD,(Zlo,Zhi),density_hash

def load_prefixes(folder,data):
    record=json.loads((folder/'marginal-result.json').read_text())
    require(record['input_sha256']==hashlib.sha256((HERE/'inputs.json').read_bytes()).hexdigest(),'marginal input binding')
    out={}
    for r in record['records']:
        if 'prefix' not in r:continue
        entry=r['prefix'];p=folder/entry['path']
        require(hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'],'marginal payload hash')
        header,arrays=read_intervals(p)
        require(header['bits']==P and header['signatures']==data['signatures'] and header['rmax']==data['rmax'] and header['rmin']==0,'marginal metadata')
        require(header['physical_h_omitted'] and header['retained_profile_product_omitted'],'marginal normalization flags')
        out[header['prefix']]=arrays
    require(sorted(out)==data['needed_prefixes'],'prefix inventory')
    return out,record

def run(folder,output):
    data=load_inputs();h=F(data['h']);N=data['rmax']+1;started=time.monotonic();version=eb.init_backend()
    sigs=[tuple(s) for s in data['signatures']];S=sorted({tuple(sorted(s+t)) for s in sigs for t in sigs})
    prefix,marginal_record=load_prefixes(folder,data)
    A,D,FA,FD,Z,density_hash=coordinate_inputs(data)
    @lru_cache(None)
    def power(n):
        if n==0:return [B],[B]
        if n==1:return A[0]
        if n%2==0:
            half=power(n//2);return conv(half,half,N)
        return conv(power(n-1),A[0],N)
    @lru_cache(maxsize=80)
    def block(bs):
        if not bs:return [B],[B]
        if len(bs)==1:return A[bs[0]]
        return conv(block(bs[:-1]),A[bs[-1]],N)
    @lru_cache(maxsize=96)
    def background(n,bs):return conv(power(n-len(bs)),block(bs),N)
    @lru_cache(maxsize=64)
    def marked_term(own,bs):return conv(background(38,bs),D[own],N)
    pairs=defaultdict(list)
    for i in range(11):
        for j in range(i,11):pairs[tuple(sorted(sigs[i]+sigs[j]))].append((i,j,1 if i==j else 2))
    low_total=[0]*N;high_total=[0]*N
    # Both terms stay separate through the complete signed-square expansion.
    low_erased=[0]*N;high_erased=[0]*N;low_retained=[0]*N;high_retained=[0]*N
    a,b=F(data['a']),F(data['b']);cuts=data['face_radial_cutoffs']
    weights=[fp(F(1)),fp(a+b),fp(abs(b))]
    for si,sig in enumerate(S):
        ml=[0]*N;mh=[0]*N;dl=[0]*N;dh=[0]*N
        for bs,ct in parts(sig).items():
            c=ct*prod(range(39-len(bs)+1,40));x,y=background(39,bs)
            ml=[v+c*w for v,w in zip(ml,x)];mh=[v+c*w for v,w in zip(mh,y)]
        for (own,bs),ct in marked_parts(sig).items():
            c=39*ct*prod(range(38-len(bs)+1,39));x,y=marked_term(own,bs)
            dl=[v+c*w for v,w in zip(dl,x)];dh=[v+c*w for v,w in zip(dh,y)]
        pp=[]
        for arrays in prefix.values():
            for i,j,mult in pairs[sig]:pp.append((arrays[str(i)],arrays[str(j)],mult))
        for r in range(N):
            c=(0,0)
            for x,y,mult in pp:
                v=mul((x[0][r],x[1][r]),(y[0][r],y[1][r]))
                c=plus(c,(mult*v[0],mult*v[1]))
            w=weights[0 if r<=cuts[0] else 1 if r<=cuts[1] else 2]
            c=mul(c,w)
            e=mul(c,mul((ml[r],mh[r]),(FD[0][r],FD[1][r])))
            t=mul(c,mul((dl[r],dh[r]),(FA[0][r],FA[1][r])))
            low_erased[r]+=e[0];high_erased[r]+=e[1]
            low_retained[r]+=t[0];high_retained[r]+=t[1]
        print('FACE_SIGNATURE',si+1,len(S),'CONVOLUTIONS',eb.convcount,'SECONDS',round(time.monotonic()-started,2),'RSS',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,file=sys.stderr,flush=True)
    # Each complete (not per-signature!) square has nonnegative integral.
    require(min(high_erased)>=0 and min(high_retained)>=0,'negative complete-square upper endpoint')
    e=sum(high_erased);t=sum(high_retained)
    total=e+t;lower=sum(max(0,x) for x in low_erased)+sum(max(0,x) for x in low_retained)
    require(0<=lower<=total,'final source enclosure')
    factor=40*h*h*(F(B,360*Z[0]))**40
    ans=factor*F(total,B);units=ans/F(data['Iref'])*10**18
    up=ceilf(units*10**8)
    result={
        'format':'tp-face-result/v1','status':'FACE_BOUND_PROOF_CANDIDATE' if up<=10*10**8 else 'VALID_ENVELOPE_TARGET_NOT_MET_CANDIDATE',
        'input_sha256':hashlib.sha256((HERE/'inputs.json').read_bytes()).hexdigest(),
        'density_sha256':density_hash,'bits':P,'dimension':40,'source_row':'G0:R00',
        'face_relative_upper_units_1e8':up,'face_target_units':10,'face_target_met_arithmetically':up<=10*10**8,
        'erased_mark_relative_upper':str(factor*F(e,B)/F(data['Iref'])*10**18),
        'retained_mark_relative_upper':str(factor*F(t,B)/F(data['Iref'])*10**18),
        'absolute_upper_factors':{'face_count':40,'physical_marginal_factor':str(h*h),'contraction_upper_integer':str(total),'fixed_point_scale':str(B),'common_scale':'1/360','normalizer_lower_integer':str(Z[0]),'reference':data['Iref']},
        'contraction_lower_integer':str(lower),'normalizer_upper_integer':str(Z[1]),
        'moment_signature_count':len(S),'positive_convolutions':eb.convcount,
        'marginal_result_sha256':hashlib.sha256((folder/'marginal-result.json').read_bytes()).hexdigest(),
        'marginal_summary':{k:marginal_record[k] for k in ('stored_coefficient_intervals','cap_cell_intervals','direct_exact_checks')},
        'gmp_version':version,'python_version':platform.python_version(),
        'wall_seconds':round(time.monotonic()-started,3),'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'full_integral_evaluation':True,'physical_measure_normalization_imported':True,
        'independent_verification':False,'all_152_targets_verified':False,
        'cannot_imply':['An independent-verifier PASS.','The other151 scalar targets.','A smaller prime-gap bound.','The twin-prime conjecture.']
    }
    Path(output).write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--generated',type=Path,default=HERE/'generated');p.add_argument('--output',type=Path,default=HERE/'face-result.json');args=p.parse_args()
    if args.output.exists():raise FileExistsError('refusing to overwrite a face receipt')
    print(json.dumps(run(args.generated,args.output),indent=2))
