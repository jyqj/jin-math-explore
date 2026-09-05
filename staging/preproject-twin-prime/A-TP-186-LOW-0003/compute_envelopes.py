"""Recompute a genuine upper enclosure for the first G0:R00 root integral.

No NumPy, float acceptance, FLINT patches, saved integral outputs or downloaded
modules. One 98,264-cell positive renewal bound plus GMP exact integer
Kronecker products; every acceptance operation is rational or integer.

See low-kernel-proof.md for the unreviewed analytic bridge. Arithmetic success
is not independent verification and does not prove the face target or all152.
"""
from fractions import Fraction as F
from functools import lru_cache
from collections import Counter
from pathlib import Path
from math import comb,prod,factorial
import json,ctypes,subprocess,tempfile,time,sys,hashlib
import argparse,platform,resource,os
P=160;B=1<<P
HERE=Path(__file__).resolve().parent
EXPECTED_INPUT_SHA256='a259961ab3354229b7d205188399136f2fd614b8ddf9d4b1fa193e292fbd1b8e'
CSOURCE='#include <gmp.h>\n#include <stdlib.h>\n#include <stdint.h>\n#include <string.h>\nvoid *poly_mul(const void *a,size_t an,const void *b,size_t bn,size_t slot,size_t n){\n if (!slot || slot>4096 || !n || n>2000000 || n>SIZE_MAX/slot) return NULL;\n mpz_t x,y,z;mpz_inits(x,y,z,NULL);\n mpz_import(x,an,-1,slot,-1,0,a);mpz_import(y,bn,-1,slot,-1,0,b);\n mpz_mul(z,x,y);mpz_fdiv_r_2exp(z,z,(mp_bitcnt_t)n*slot*8);\n void *out=calloc(n,slot);size_t count=0;\n if(out)mpz_export(out,&count,-1,slot,-1,0,z);\n mpz_clears(x,y,z,NULL);return out;\n}\nvoid free_result(void *p){free(p);}\nconst char *backend_version(void){return gmp_version;}\n'
params=None;h=None;N=None;co=None
sigs=[(),(2,),(3,),(4,),(5,),(6,),(2,2),(2,3),(2,4),(3,3),(2,2,2)]
lib=None;fn=None;build_directory=None

def require(ok,message):
    if not ok: raise ValueError(message)

def load_inputs():
    global params,h,N,co
    raw=(HERE/'inputs.json').read_bytes()
    require(hashlib.sha256(raw).hexdigest()==EXPECTED_INPUT_SHA256,'frozen input bytes differ')
    params=json.loads(raw)
    h=F(params['h']);N=params['rmax']+1;co=params['coefficients']
    require(params['first']==F(params['lo'])//h,'lower cell endpoint')
    require(params['last']==-((-F(params['hi']))//h),'upper cell endpoint')
    require(params['cap_index']*h==F(params['cap']),'cap alignment')
    require(params['dimension']==40 and params['bits']==160 and params['tilt']==-6,'frozen numerical settings')
    require(params['theta']==-((-F(7)/F(params['hi']))//1),'Chernoff slope')
    require(len(co)==11 and all(len(row)==7 for row in co),'coefficient shape')

def init_backend():
    global lib,fn,build_directory
    build_directory=tempfile.TemporaryDirectory(prefix='tp186-low-')
    folder=Path(build_directory.name);(folder/'gmpconv.c').write_text(CSOURCE)
    subprocess.run(['gcc','-shared','-fPIC','-O2','-std=c11',str(folder/'gmpconv.c'),'-o',str(folder/'gmpconv.so'),'-lgmp'],check=True,capture_output=True)
    lib=ctypes.CDLL(str(folder/'gmpconv.so'));fn=lib.poly_mul
    fn.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_size_t,ctypes.c_size_t];fn.restype=ctypes.c_void_p
    lib.free_result.argtypes=[ctypes.c_void_p];lib.backend_version.restype=ctypes.c_char_p
    return lib.backend_version().decode()

def ceildiv(a,b):return -(-a//b)
def floorf(x):return x.numerator//x.denominator
def ceilf(x):return ceildiv(x.numerator,x.denominator)
def fp(x):return floorf(x*B),ceilf(x*B)
def mul(a,b):
 p=[a[0]*b[0],a[0]*b[1],a[1]*b[0],a[1]*b[1]];return min(p)//B,ceildiv(max(p),B)
def times(x,a):
 if x>=0:return floorf(x*a[0]),ceilf(x*a[1])
 return floorf(x*a[1]),ceilf(x*a[0])
def plus(a,b):return a[0]+b[0],a[1]+b[1]
def expq(x):
 if x<0:
  lo,hi=expq(-x);return B*B//hi,ceildiv(B*B,lo)
 k=0;y=x
 while y>F(1,8):y/=2;k+=1
 term=s=F(1)
 for n in range(1,512):
  term*=y/n;s+=term
  tail=term*y/(n+1)/(1-y/(n+2))
  if tail<F(1,1<<(P+k+16)):break
 else:raise ArithmeticError('Taylor')
 lo,hi=fp(s)[0],fp(s+tail)[1]
 for _ in range(k):lo=lo*lo//B;hi=ceildiv(hi*hi,B)
 return lo,hi
convcount=0

def rawconv(a,b,n):
 global convcount
 require(n>=1 and n<=2000000 and len(a)>0 and len(b)>0,'convolution sizes')
 require(all(isinstance(x,int) and x>=0 for x in a+b),'nonnegative integer coefficients required')
 if not any(a) or not any(b):return [0]*n
 if len(a)==1:return [a[0]*x for x in b[:n]]+[0]*max(0,n-len(b))
 if len(b)==1:return rawconv(b,a,n)
 # Max coefficient <= min(lengths)*max(a)*max(b); extra bit is conservative.
 slot=(max(a).bit_length()+max(b).bit_length()+min(len(a),len(b)).bit_length()+7)//8
 aa=b''.join(x.to_bytes(slot,'little') for x in a);bb=b''.join(x.to_bytes(slot,'little') for x in b)
 ptr=fn(aa,len(a),bb,len(b),slot,n)
 if not ptr:raise MemoryError('GMP output')
 out=ctypes.string_at(ptr,slot*n);lib.free_result(ptr);convcount+=1
 return [int.from_bytes(out[j:j+slot],'little') for j in range(0,len(out),slot)]
def conv(a,b):
 n=min(N,len(a[0])+len(b[0])-1)
 lo=[z//B for z in rawconv(a[0],b[0],n)]
 hi=[ceildiv(z,B) for z in rawconv(a[1],b[1],n)]
 return lo,hi

def density_envelope(count,L,C,q):
    """Bound cell-essential suprema using t*m=(w*m). See the proof file.

    Every U_j is an EXACT chosen dyadic upper density; rolling sums are
    outward enclosures of sums formed from those fixed U_j values.
    """
    require(2<=L<C and count>L and 0<q[0]<=q[1]<=B,'density input domain')
    ql,qh=[B],[B]
    for j in range(1,L):
        ql.append(ql[-1]*q[0]//B);qh.append(ceildiv(qh[-1]*q[1],B))
    U=qh[:];sl=sh=0
    for i in range(1,L):
        sl=U[i]+q[0]*sl//B;sh=U[i]+ceildiv(q[1]*sh,B)
    high=U[0]
    for j in range(L,count):
        U.append(min(B,ceildiv(sh+high,j-1)))
        old=U[j-L+1]
        sl=max(0,U[j]+q[0]*sl//B-ceildiv(qh[L-1]*old,B))
        sh=U[j]+ceildiv(q[1]*sh,B)-ql[L-1]*old//B
        high+=old
        if j-C>=0: high-=U[j-C]
        require(0<=sl<=sh and high>=0,'rolling interval failure')
    return U


def integer_array_hash(values):
    """Unambiguous signed-free integer stream: decimal, one value per line."""
    dig=hashlib.sha256()
    for value in values: dig.update((str(value)+'\n').encode())
    return dig.hexdigest()

def build_inputs():
 t=time.monotonic()
 U=density_envelope(params['count'],params['first'],params['cap_index'],expq(-params['theta']*h))
 global density_hash;density_hash=integer_array_hash(U)
 L,H=params['first'],params['last'];mark=([0]*H,[0]*H)
 for i in range(L,H):mark[0][i]=B//i;mark[1][i]=ceildiv(B,i)
 W=conv((U[:N],U[:N]),mark)
 W=([((W[0][i]+(W[0][i-1] if i else 0))//2) for i in range(N)],
    [ceildiv(W[1][i]+(W[1][i-1] if i else 0),2) for i in range(N)])
 # Common scale C=1/360; target normalizer Z=h sum g(mid)^2.
 A=[([],[]) for i in range(13)];D=[([],[]) for i in range(13)]
 ex=expq(-3*h);q=expq(-6*h);Zlo=Zhi=0
 for i in range(params['count']):
  tmid=(F(i)+F(1,2))*h
  g=F(21,200)/(1+tmid/100)+F(179,200)/(1+F(907,5)*tmid)
  z=g*g*h;Zlo+=floorf(z*B);Zhi+=ceilf(z*B)
  if i<N:
   w=times(z*360,ex)
   ordinary=mul(w,(U[i],U[i]));designated=mul(w,(W[0][i],W[1][i]))
   power=F(1)
   for e in range(13):
    low,up=times(power,ordinary);A[e][0].append(low);A[e][1].append(up)
    low,up=times(power,designated);D[e][0].append(low);D[e][1].append(up)
    power*=tmid
  ex=mul(ex,q)
 print('INPUTS_SECONDS',round(time.monotonic()-t,3),file=sys.stderr,flush=True)
 return A,D,(Zlo,Zhi)
@lru_cache(None)
def parts(sig):
 if not sig:return {():1}
 t=sig[0];d=Counter()
 for p,ct in parts(sig[1:]).items():
  d[tuple(sorted((t,)+p))]+=ct
  for i in range(len(p)):d[tuple(sorted(p[:i]+(p[i]+t,)+p[i+1:]))]+=ct
 return dict(d)
@lru_cache(None)
def mparts(sig):
 out=Counter()
 for mask in range(1<<len(sig)):
  own=sum(sig[i] for i in range(len(sig)) if mask>>i&1)
  rem=tuple(sig[i] for i in range(len(sig)) if not mask>>i&1)
  for p,ct in parts(rem).items():out[(own,p)]+=ct
 return dict(out)
S=sorted({tuple(sorted(s+t)) for s in sigs for t in sigs})
terms=sorted({q for s in S for q in mparts(s)})

def run():
 t=time.monotonic();A,D,Z=build_inputs()
 @lru_cache(None)
 def power(n):
  if n==0:return [B],[B]
  if n==1:return A[0]
  if n%2==0:p=power(n//2);return conv(p,p)
  return conv(power(n-1),A[0])
 @lru_cache(None)
 def block(bs):
  if not bs:return [B],[B]
  if len(bs)==1:return A[bs[0]]
  return conv(block(bs[:-1]),A[bs[-1]])
 # Precombine ordinary 39-coordinate block terms, cache 77 ~ 650MB.
 @lru_cache(None)
 def bg(bs):return conv(power(39-len(bs)),block(bs))
 rows={}
 sl=slice(params['rmin'],params['rmax']+1)
 for i,(own,bs) in enumerate(terms):
  out=conv(bg(bs),D[own]);rows[(own,bs)]=(out[0][sl],out[1][sl])
  if i%20==0:print('TERM',i,len(terms),'CONVOLUTIONS',convcount,'SECONDS',round(time.monotonic()-t,2),file=sys.stderr,flush=True)

 # Also cache the 77 background vectors for possible face contraction; local only.
 # Avoid including these multi-megabyte intermediates in published artifacts.
 moment={}
 for sig in S:
  lo=[0]*720;hi=[0]*720
  for (own,bs),ct in mparts(sig).items():
   c=40*ct*prod(range(39-len(bs)+1,40));a,b=rows[(own,bs)]
   lo=[x+c*y for x,y in zip(lo,a)];hi=[x+c*y for x,y in zip(hi,b)]
  moment[sig]=lo,hi
 exp0=expq(189*(params['last']*h-F(params['threshold'])+20*h)+(189+6)*(params['rmin']+20)*h)
 qe=expq(195*h);total=(0,0);q2low=[];q2up=[]
 for ii,r in enumerate(range(params['rmin'],params['rmax']+1)):
  d=(r+20)*h-F(9,10)
  vals=[]
  for cs in co:
   y=F(0)
   for c in reversed(cs):y=y*d+F(c,10**10)
   vals.append(y)
  coefficients=Counter()
  for i in range(11):
   for j in range(i,11):coefficients[tuple(sorted(sigs[i]+sigs[j]))]+=vals[i]*vals[j]*(1 if i==j else 2)
  sq=(0,0)
  for sig,c in coefficients.items():sq=plus(sq,times(c,(moment[sig][0][ii],moment[sig][1][ii])))
  if sq[1]<0:raise ArithmeticError('negative square enclosure')
  sq=(max(0,sq[0]),sq[1]);q2low.append(sq[0]);q2up.append(sq[1])
  total=plus(total,mul(sq,exp0));exp0=mul(exp0,qe)
 ans=40*F(total[1],B)*(F(B,360*Z[0]))**40
 units=ans/F(23685317816,10**24)*10**18
 up=ceilf(units*10**8)
 result={
  'format':'tp-186-low-result/v1','status':'ROOT_BOUND_PROOF_CANDIDATE',
  'input_sha256':EXPECTED_INPUT_SHA256,'density_sha256':density_hash,
  'bits':P,'dimension':40,'source_row':'G0:R00',
  'root_relative_upper_units_1e8':up,'root_target_units':11,
  'root_target_met_arithmetically':up<=11*10**8,
  'absolute_root_upper_factors':{'face_count':40,'contraction_upper_integer':str(total[1]),'fixed_point_scale':str(B),'common_scale':'1/360','normalizer_lower_integer':str(Z[0]),'reference_numerator':23685317816,'reference_denominator':10**24},
  'normalizer_lower_integer':str(Z[0]),'normalizer_upper_integer':str(Z[1]),
  'normalizer_scale':str(B),'moment_signature_count':len(S),'marked_monomial_count':len(terms),
  'density_cell_count':params['count'],'contraction_cell_count':N,'retained_radial_cell_count':720,
  'positive_convolutions':convcount,'gmp_version':lib.backend_version().decode(),
  'c_source_sha256':hashlib.sha256(CSOURCE.encode()).hexdigest(),
  'python_version':platform.python_version(),'wall_seconds':round(time.monotonic()-t,3),
  'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
  'face_target_status':'NOT_EVALUATED',
  'original_flint_engine_run':False,'lean_build_run':False,'independent_verification':False,
  'all_152_inputs_discharged':False,'true_integral_lower_bound_claimed':False,
  'evidence':'exact finite enclosure arithmetic plus an unreviewed analytic domination proof',
  'cannot_imply':['This is an independent-verifier PASS.','The second G0:R00 face target 10 is proved.','All 152 numerical inputs hold.','A new prime-gap bound or the twin prime conjecture is proved.']}
 return result


def main():
    parser=argparse.ArgumentParser(description='Recompute the G0:R00 root enclosure. Requires gcc and GMP development headers; no downloads or dependency modifications.')
    parser.add_argument('--run',action='store_true',required=True)
    parser.add_argument('--output',type=Path,required=True,help='Fresh output path; never overwritten')
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError('output already exists')
    load_inputs();init_backend()
    result=run()
    with args.output.open('x',encoding='utf-8') as out:
        json.dump(result,out,ensure_ascii=False,indent=2);out.write('\n')
    print(json.dumps({'status':result['status'],'root_upper_units_1e8':result['root_relative_upper_units_1e8'],'target_met':result['root_target_met_arithmetically'],'independent_verification':False}))
    return 0 if result['root_target_met_arithmetically'] else 1

if __name__=='__main__':
    try: raise SystemExit(main())
    except (OSError,ValueError,ArithmeticError,subprocess.CalledProcessError) as exc:
        print(type(exc).__name__+': '+str(exc),file=sys.stderr);raise SystemExit(2)
