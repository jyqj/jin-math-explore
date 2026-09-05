"""Real G0:R00, full finite Eulerian coordinate majorants.

Uses authenticated predecessor data. Never substitutes per-moment upper bounds
into a signed square: the returned coordinate arrays are fixed dyadic measures.
"""
from __future__ import annotations
import sys,json,hashlib,zlib,struct,math,time
from pathlib import Path
from fractions import Fraction as F
import exact_poly as ep

ROOT=Path(__file__).resolve().parent
P3=ROOT/'predecessors'
P4=ROOT/'predecessors'
sys.path.insert(0,str(P3));import low_kernel as lk
BITS=320;Q=1<<BITS;N=98264

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(b,m):ep.require(b,m)
def emit(event,**kw):print(json.dumps(dict(event=event,**kw),sort_keys=True),flush=True)
def save(path,arr,**meta):
    require(all(type(v) is int and v>=0 for v in arr),'unsigned array')
    width=max(1,(max(arr,default=0).bit_length()+7)//8)
    hd=json.dumps(dict(format='tp-positive-dyadic-array/v1',n=len(arr),width=width,bits=BITS,**meta),sort_keys=True).encode()
    data=struct.pack('<I',len(hd))+hd+b''.join(v.to_bytes(width,'little') for v in arr)
    path.write_bytes(zlib.compress(data,9));return dict(file=path.name,sha256=digest(path),raw_sha256=hashlib.sha256(data).hexdigest(),count=len(arr),bits=BITS)
def load(path):
    raw=zlib.decompress(path.read_bytes());sz=struct.unpack('<I',raw[:4])[0];hd=json.loads(raw[4:4+sz]);v=memoryview(raw)[4+sz:];w=hd['width']
    require(len(v)==w*hd['n'],'array length mismatch')
    return hd,[int.from_bytes(v[i:i+w],'little') for i in range(0,len(v),w)]
def exp_iv(x,bits=BITS):
    x=F(x);k=0;y=abs(x)
    while y>1:y/=2;k+=1
    l,u,_=lk.exp_negative_enclosure(y,bits);s=1<<bits
    for _ in range(k):l=l*l//s;u=ep.ceildiv(u*u,s)
    if x>0:l,u=s*s//u,ep.ceildiv(s*s,l)
    return l,u

def build(out):
    require(not out.exists(),'fresh output required');out.mkdir(parents=True)
    tx=(P4/'inputs.json').read_bytes();sx=(P4/'source-row.json').read_bytes()
    require(hashlib.sha256(tx).hexdigest()=='10f1b1cd8df483d49e30974c07595a0fbe57d13e560d3e99a5b88238bccadadc','trial lock mismatch')
    require(hashlib.sha256(sx).hexdigest()=='22425b898aa326e4a2bd9d46d6d4363d2d8e8930586c3a5de92138b94f4b4158','row lock mismatch')
    x=json.loads(tx);s=json.loads(sx);h=F(x['h']);require(s['first_index']==2331 and s['last_index']==3498 and x['n']==N,'row mismatch')
    seed_path=P3/'seed-enclosures.bin.zlib'
    require(digest(seed_path)=='7d4ca048cd34981def5e16c8d0ce0af366b8b2154a7b9c53aa1932ba6aed7a1c','seed hash mismatch')
    raw=zlib.decompress(seed_path.read_bytes());magic,bits,count,width=struct.unpack('>8sIII',raw[:20]);require(magic==b'TPSEED03' and bits==640 and count>=N,'seed format')
    mv=memoryview(raw)[20:];seed=[ep.ceildiv(int.from_bytes(mv[(2*j+1)*width:(2*j+2)*width],'big'),1<<(bits-BITS)) for j in range(N)]
    m=s['first_index'];cap=s['cap_index'];b=s['last_index']
    high=[0]*m+[ep.ceildiv(Q,j) for j in range(m,cap)]+[0]*(N-cap)
    mark=high[:b]+[0]*(N-b)
    term=[Q]+[0]*(N-1);acc=[0]*N;dacc=[0]*N;start=time.monotonic()
    counts=[]
    for n in range((N-1)//m+1):
        for extra,target in [(0,acc),(1,dacc)]:
            C=lk.eulerian_integers(n+extra+1);den=math.factorial(n+extra+1)
            # Short carry polynomial normalized in the same dyadic unit.
            carry=[ep.ceildiv(c*Q,den) for c in C]
            vals=ep.mul_up(term,carry,N,BITS)
            for j,v in enumerate(vals):target[j]+=v
        counts.append(n)
        if n<(N-1)//m:
            vals=ep.mul_up(term,high,N,BITS)
            term=[ep.ceildiv(v,n+1) for v in vals]
        if n%5==0:emit('EULERIAN_COUNT',n=n,elapsed=time.monotonic()-start)
    a=ep.mul_up(acc,seed,N,BITS)
    barray=ep.mul_up(ep.mul_up(dacc,mark,N,BITS),seed,N,BITS)
    # Z interval from exact rational profile values.
    gl=[];gu=[];gns=[];gds=[]
    for j in range(N):
        t=h*(2*j+1)/2
        g=F(21,200)/(1+t/100)+F(179,200)/(1+F(907,5)*t)
        g2=g*g;gl.append(g2.numerator*Q//g2.denominator);gu.append(ep.ceildiv(g2.numerator*Q,g2.denominator))
        gns.append(g2.numerator);gds.append(g2.denominator)
    Zl=sum(gl);Zu=sum(gu);require(Zl>0,'positive normalization')
    alpha=[ep.ceildiv(v*gn*Q,gd*Zl) for v,gn,gd in zip(a,gns,gds)]
    beta=[ep.ceildiv(v*gn*Q,gd*Zl) for v,gn,gd in zip(barray,gns,gds)]
    L,U=s['radial_first'],s['radial_last'];theta=s['slope'];threshold=F(s['threshold'])
    l,u=exp_iv(theta*((L+40)*h+F(s['high_rounded'])-threshold));el,eu=exp_iv(theta*h)
    rlo=[];rhi=[]
    for j in range(L,U+1):
        rlo.append(l);rhi.append(u);l=l*el//Q;u=ep.ceildiv(u*eu,Q)
    # Correlation with source radial envelope: index U-r of a*reverse(R).
    ra=ep.mul_up(a,list(reversed(rhi)),U+1,BITS)
    rb=ep.mul_up(barray,list(reversed(rhi)),U+1,BITS)
    fa=list(reversed(ra))+[0]*(N-U-1);fb=list(reversed(rb))+[0]*(N-U-1)
    records=[]
    for name,arr in [('a',a),('b',barray),('alpha',alpha),('beta',beta),('fiber_a',fa),('fiber_b',fb),('radial_lower',rlo),('radial_upper',rhi)]:records.append(save(out/f'{name}.zlib',arr,kind=name))
    report=dict(format='tp-full-finite-kernel/v1',bits=BITS,n=N,row=s,trial_sha256=hashlib.sha256(tx).hexdigest(),seed_sha256=digest(seed_path),full_unmarked_counts=counts,designated_effective_max_count=(N-m-1)//m,tail_approximation_used=False,Z_lower=str(F(Zl,Q)),Z_upper=str(F(Zu,Q)),alpha_total=str(F(sum(alpha),Q)),beta_total=str(F(sum(beta),Q)),arrays=records,gmp_version=ep.LIB.packed_gmp_version().decode(),arithmetic='Nonnegative GMP integer products; all coefficient divisions rounded upward; fixed common coordinate measures',convolutions=dict(ep.COUNTS),seconds=time.monotonic()-start,final_targets_certified=False)
    (out/'kernel.json').write_text(json.dumps(report,indent=2)+'\n');emit('KERNEL_COMPLETE',seconds=report['seconds'],alpha_total=float(F(sum(alpha),Q)),beta_total=float(F(sum(beta),Q)),convolutions=ep.COUNTS)
if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();build(args.output)
