"""Portable Python driver for GMP integer Kronecker convolution.

Every multiplication here has nonnegative integer coefficients. Radix headroom
is proved by min(len(a),len(b))*max(a)*max(b). No numerical FFT is exposed.
Only after the exact integer product do we round down/up at a dyadic scale.
"""
from __future__ import annotations
import ctypes, math
from pathlib import Path
from time import monotonic

LIB=ctypes.CDLL(str(Path(__file__).with_name('packed_gmp.so')))
LIB.packed_multiply.argtypes=[ctypes.c_char_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t]
LIB.packed_multiply.restype=ctypes.c_int
LIB.packed_gmp_version.restype=ctypes.c_char_p
COUNTS={'multiplications':0,'seconds':0.0,'max_coefficient_slot_bytes':0}

def require(b,msg):
    if not b:raise ValueError(msg)

def ceildiv(a,b):return -((-a)//b)

def conv_int(a:list[int],b:list[int],n:int)->list[int]:
    require(type(n) is int and n>0,'positive truncation')
    require(all(type(x) is int and x>=0 for x in a) and all(type(x) is int and x>=0 for x in b),'nonnegative integer coefficients required')
    na=min(len(a),n);nb=min(len(b),n)
    la=next((i for i in range(na) if a[i]),na)
    lb=next((i for i in range(nb) if b[i]),nb)
    if la==na or lb==nb or la+lb>=n:return [0]*n
    off=la+lb;m=n-off
    aa=a[la:min(na,la+m)];bb=b[lb:min(nb,lb+m)]
    while aa and aa[-1]==0:aa.pop()
    while bb and bb[-1]==0:bb.pop()
    if len(aa)==1:return [0]*off+[aa[0]*x for x in bb]+[0]*(n-off-len(bb))
    if len(bb)==1:return [0]*off+[bb[0]*x for x in aa]+[0]*(n-off-len(aa))
    L=min(m,len(aa)+len(bb)-1)
    bound=min(len(aa),len(bb))*max(aa)*max(bb)
    sb=max(1,(bound.bit_length()+7)//8)
    # bound < 256**sb, so no carry can reach the next coefficient.
    require(bound < 1<<(8*sb),'Kronecker radix too small')
    t=monotonic()
    pa=b''.join(x.to_bytes(sb,'little') for x in aa)
    pb=pa if aa==bb else b''.join(x.to_bytes(sb,'little') for x in bb)
    out=ctypes.create_string_buffer(L*sb)
    code=LIB.packed_multiply(pa,len(pa),pb,len(pb),out,len(out))
    require(code==0,'GMP packed multiplication failed')
    view=memoryview(out.raw)
    vals=[int.from_bytes(view[i*sb:(i+1)*sb],'little') for i in range(L)]
    COUNTS['multiplications']+=1;COUNTS['seconds']+=monotonic()-t
    COUNTS['max_coefficient_slot_bytes']=max(COUNTS['max_coefficient_slot_bytes'],sb)
    return [0]*off+vals+[0]*(n-off-L)

def mul_up(a,b,n,bits):
    mask=(1<<bits)-1
    return [(v>>bits)+bool(v&mask) for v in conv_int(a,b,n)]

def mul_interval(x,y,n,bits):
    l=conv_int(x[0],y[0],n)
    same=x[0] is x[1] and y[0] is y[1]
    u=l if same else conv_int(x[1],y[1],n)
    mask=(1<<bits)-1
    return ([v>>bits for v in l],[(v>>bits)+bool(v&mask) for v in u])

def add_interval(x,y):return ([a+b for a,b in zip(x[0],y[0])],[a+b for a,b in zip(x[1],y[1])])
def scale_int(x,c):
    require(type(c) is int and c>=0,'positive integer scale')
    return ([a*c for a in x[0]],[a*c for a in x[1]])
def point_interval(a):return (a,a)

def tests():
    import random
    rng=random.Random(186005);count=0
    for length in [1,2,9,17,34,66]:
      for width in [1,8,31,64,193,321]:
       a=[rng.getrandbits(width) if rng.randrange(4) else 0 for _ in range(length)]
       b=[rng.getrandbits(width) if rng.randrange(3) else 0 for _ in range(length+1)]
       for n in [1,length,2*length]:
        oracle=[sum(a[i]*b[k-i] for i in range(len(a)) if 0<=k-i<len(b)) for k in range(n)]
        require(conv_int(a,b,n)==oracle,'naive convolution mismatch');count+=1
    for n in [16,32]:
      a=[(1<<509)-1]*n;b=[(1<<510)-1]*n
      exact=[min(i+1,2*n-1-i,n)*a[0]*b[0] for i in range(2*n-1)]
      require(conv_int(a,b,2*n-1)==exact,'carry headroom regression');count+=1
    # Large production-length identity tests the same import/export path.
    n=98264;a=[1<<320]*n;b=[1<<319]*n
    c=conv_int(a,b,n)
    require(all(v==(j+1)*(1<<639) for j,v in enumerate(c)),'production triangular identity')
    return {'naive_and_headroom_tests':count,'production_coefficients_checked':n,'gmp_version':LIB.packed_gmp_version().decode(),'counts':dict(COUNTS)}
if __name__=='__main__':
 import json; print(json.dumps(tests(),indent=2))
