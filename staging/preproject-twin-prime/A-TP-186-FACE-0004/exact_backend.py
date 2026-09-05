"""Portable outward arithmetic and GMP positive linear convolution.
Adapted and rechecked from frozen solver cec587a86e...; not an independent
verification of that candidate. No original FLINT module is executed.
"""
from fractions import Fraction as F
from functools import lru_cache
from collections import Counter
from pathlib import Path
import ctypes, subprocess, tempfile, hashlib, json
P=160
B=1<<P
HERE=Path(__file__).resolve().parent
CSOURCE=r'''#include <gmp.h>
#include <stdlib.h>
#include <stdint.h>
void *poly_mul(const void *a,size_t an,const void *b,size_t bn,size_t slot,size_t n){
 if (!slot || slot>4096 || !n || n>2000000 || n>SIZE_MAX/slot) return NULL;
 mpz_t x,y,z; mpz_inits(x,y,z,NULL);
 mpz_import(x,an,-1,slot,-1,0,a); mpz_import(y,bn,-1,slot,-1,0,b);
 mpz_mul(z,x,y); mpz_fdiv_r_2exp(z,z,(mp_bitcnt_t)n*slot*8);
 void *out=calloc(n,slot); size_t count=0;
 if(out) mpz_export(out,&count,-1,slot,-1,0,z);
 mpz_clears(x,y,z,NULL); return out;
}
void free_result(void *p){free(p);}
const char *backend_version(void){return gmp_version;}
'''
lib=None
fn=None
build_directory=None
convcount=0

def require(ok,message):
    if not ok: raise ValueError(message)
def ceildiv(a,b):
    require(b>0,'nonpositive divisor')
    return -(-a//b)
def floorf(x): return x.numerator//x.denominator
def ceilf(x): return -(-x.numerator//x.denominator)
def fp(x): return floorf(x*B),ceilf(x*B)
def plus(a,b): return a[0]+b[0],a[1]+b[1]
def mul(a,b):
    vals=(a[0]*b[0],a[0]*b[1],a[1]*b[0],a[1]*b[1])
    return min(vals)//B,-(-max(vals)//B)
def times(x,a):
    if x>=0: return floorf(x*a[0]),ceilf(x*a[1])
    return floorf(x*a[1]),ceilf(x*a[0])
def expq(x):
    x=F(x)
    if x<0:
        lo,hi=expq(-x);return B*B//hi,ceildiv(B*B,lo)
    k=0;y=x
    while y>F(1,8):y/=2;k+=1
    term=s=F(1)
    for n in range(1,512):
        term*=y/n;s+=term
        tail=term*y/(n+1)/(1-y/(n+2))
        if tail<F(1,1<<(P+k+16)):break
    else:raise ArithmeticError('Taylor budget')
    lo,hi=floorf(s*B),ceilf((s+tail)*B)
    for _ in range(k):lo=lo*lo//B;hi=ceildiv(hi*hi,B)
    return lo,hi

def init_backend():
    global lib,fn,build_directory
    if lib is not None:return lib.backend_version().decode()
    build_directory=tempfile.TemporaryDirectory(prefix='tp-face-gmp-')
    folder=Path(build_directory.name);(folder/'conv.c').write_text(CSOURCE)
    subprocess.run(['gcc','-shared','-fPIC','-O2','-std=c11',str(folder/'conv.c'),'-o',str(folder/'conv.so'),'-lgmp'],check=True,capture_output=True)
    lib=ctypes.CDLL(str(folder/'conv.so'));fn=lib.poly_mul
    fn.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_size_t,ctypes.c_size_t];fn.restype=ctypes.c_void_p
    lib.free_result.argtypes=[ctypes.c_void_p];lib.backend_version.restype=ctypes.c_char_p
    return lib.backend_version().decode()

def rawconv(a,b,n):
    global convcount
    require(0<n<=2000000 and a and b,'convolution lengths')
    require(all(isinstance(x,int) and not isinstance(x,bool) and x>=0 for x in a) and all(isinstance(x,int) and not isinstance(x,bool) and x>=0 for x in b),'nonnegative integer input')
    if not any(a) or not any(b):return [0]*n
    if len(a)==1:return [a[0]*x for x in b[:n]]+[0]*max(0,n-len(b))
    if len(b)==1:return rawconv(b,a,n)
    init_backend()
    slot=(max(a).bit_length()+max(b).bit_length()+min(len(a),len(b)).bit_length()+7)//8
    aa=b''.join(x.to_bytes(slot,'little') for x in a);bb=b''.join(x.to_bytes(slot,'little') for x in b)
    ptr=fn(aa,len(a),bb,len(b),slot,n)
    if not ptr:raise MemoryError('GMP convolution allocation')
    try:out=ctypes.string_at(ptr,slot*n)
    finally:lib.free_result(ptr)
    convcount+=1
    return [int.from_bytes(out[j:j+slot],'little') for j in range(0,len(out),slot)]

def conv(a,b,n):
    length=min(n,len(a[0])+len(b[0])-1)
    require(len(a[0])==len(a[1]) and len(b[0])==len(b[1]),'interval lengths')
    lo=[z//B for z in rawconv(a[0],b[0],length)]
    hi=[ceildiv(z,B) for z in rawconv(a[1],b[1],length)]
    return lo,hi

def density_envelope(count,L,C,q):
    """Common chosen dyadic upper density, via the cell-sup renewal bound.
    Lower/upper rolling sums enclose sums of those SAME chosen U_i values.
    """
    require(2<=L<C and count>L and 0<q[0]<=q[1]<=B,'density domain')
    ql,qh=[B],[B]
    for j in range(1,L):ql.append(ql[-1]*q[0]//B);qh.append(ceildiv(qh[-1]*q[1],B))
    U=qh[:];sl=sh=0
    for i in range(1,L):sl=U[i]+q[0]*sl//B;sh=U[i]+ceildiv(q[1]*sh,B)
    high=U[0]
    for j in range(L,count):
        U.append(min(B,ceildiv(sh+high,j-1)))
        old=U[j-L+1]
        sl=max(0,U[j]+q[0]*sl//B-ceildiv(qh[L-1]*old,B))
        sh=U[j]+ceildiv(q[1]*sh,B)-ql[L-1]*old//B
        high+=old
        if j-C>=0:high-=U[j-C]
        require(0<=sl<=sh and high>=0,'rolling enclosure failure')
    return U

@lru_cache(None)
def parts(sig):
    if not sig:return {():1}
    e=sig[0];out=Counter()
    for bs,c in parts(sig[1:]).items():
        out[tuple(sorted((e,)+bs))]+=c
        for i in range(len(bs)):out[tuple(sorted(bs[:i]+(bs[i]+e,)+bs[i+1:]))]+=c
    return dict(out)

@lru_cache(None)
def marked_parts(sig):
    out=Counter()
    for mask in range(1<<len(sig)):
        e=sum(sig[i] for i in range(len(sig)) if mask>>i&1)
        rem=tuple(sig[i] for i in range(len(sig)) if not mask>>i&1)
        for bs,c in parts(rem).items():out[(e,bs)]+=c
    return dict(out)

def integer_hash(a):
    d=hashlib.sha256()
    for x in a:d.update((str(x)+'\n').encode())
    return d.hexdigest()

def load_inputs():
    data=json.loads((HERE/'inputs.json').read_text())
    require(data['dimension']==40 and data['count']==98264 and data['source_bits']==160,'input dimensions')
    require(data['h']=='2742997/258046918656' and data['needed_prefixes']==[2,3],'input geometry')
    return data
