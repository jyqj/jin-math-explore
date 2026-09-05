"""Certified real-grid symmetric-square contraction of a fixed positive majorant.

The coordinates are exact dyadic upper measures from kernel_stage. Each signed
square is algebraically expanded but EVERY moment is evaluated as an interval
for those SAME measures. A lower endpoint here concerns the majorant, not the
physical integral. Physical domination remains an explicitly stated theorem.
"""
from __future__ import annotations
import sys,json,math,time,hashlib,gc,resource
from pathlib import Path
from fractions import Fraction as F
from collections import Counter,defaultdict
from functools import lru_cache
import exact_poly as ep
from kernel_stage import load,save,emit,ROOT,P4,BITS,Q,N,digest
sys.path.insert(0,str(P4));import marginal as mar

@lru_cache(None)
def partitions(sig):
    if not sig:return {():1}
    out=Counter()
    for row,mult in partitions(sig[1:]).items():
        out[tuple(sorted(row+(sig[0],)))]+=mult
        for j,e in enumerate(row):out[tuple(sorted(row[:j]+(e+sig[0],)+row[j+1:]))]+=mult
    return dict(out)
def falling(d,b):return math.prod(range(d-b+1,d+1))

def dual_mul(x,y,n,bits):
    a=ep.mul_interval(x[0],y[0],n,bits)
    if x is y:
        b=ep.scale_int(ep.mul_interval(x[0],x[1],n,bits),2)
    else:
        b=ep.add_interval(ep.mul_interval(x[0],y[1],n,bits),ep.mul_interval(x[1],y[0],n,bits))
    return a,b

class Moments:
    def __init__(self,alpha,beta,h,n=N,bits=BITS,parents=None):
        self.n,self.bits,self.h=n,bits,h
        self.alpha,self.beta=alpha,beta
        self.weighted_cache={0:((alpha,alpha),(beta,beta))}
        self.power_cache={1:self.weighted_cache[0]}
        one=[1<<bits]+[0]*(n-1);zero=[0]*n
        self.unit=((one,one),(zero,zero));self.power_cache[0]=self.unit
        self.block_cache={():self.unit};self.parents=parents
    def weighted(self,e):
        if e not in self.weighted_cache:
            den=(2*self.h.denominator)**e;hn=self.h.numerator**e
            a,b=[],[];au,bu=[],[]
            for j,(x,y) in enumerate(zip(self.alpha,self.beta)):
                num=hn*(2*j+1)**e
                a.append(x*num//den);au.append(ep.ceildiv(x*num,den))
                b.append(y*num//den);bu.append(ep.ceildiv(y*num,den))
            self.weighted_cache[e]=((a,au),(b,bu))
        return self.weighted_cache[e]
    def power(self,k):
        if k not in self.power_cache:
            half=self.power(k//2);a=dual_mul(half,half,self.n,self.bits)
            if k%2:a=dual_mul(a,self.weighted(0),self.n,self.bits)
            self.power_cache[k]=a
        return self.power_cache[k]
    def block(self,t):
        if t in self.block_cache:return self.block_cache[t]
        if len(t)==1:v=self.weighted(t[0])
        else:v=dual_mul(self.block(t[:-1]),self.weighted(t[-1]),self.n,self.bits)
        if self.parents is None or t in self.parents:self.block_cache[t]=v
        return v


def coefficient_data(x):
    sigs=[tuple(s) for s in x['signatures']];matrix=x['coefficient_integer_matrix']
    roots=defaultdict(lambda:[0]*13);faces=defaultdict(list)
    for i,s in enumerate(sigs):
      for j in range(i,len(sigs)):
        sig=tuple(sorted(s+sigs[j]));factor=1 if i==j else 2
        poly=[sum(matrix[i][u]*matrix[j][v] for u in range(7) for v in range(7) if u+v==k) for k in range(13)]
        for block,c in partitions(sig).items():
            c*=factor
            for k,a in enumerate(poly):roots[block][k]+=c*a
            faces[block].append((i,j,c))
    return sigs,dict(roots),dict(faces)

def polynomial_radial_num(poly,r,h):
    den=math.lcm(h.denominator,10);a=h.numerator*(den//h.denominator)
    z=(r+20)*a-9*(den//10)
    y=poly[12];p=den
    for k in range(11,-1,-1):y=y*z+poly[k]*p;p*=den
    return y

def contract(kernel_dir,out):
    ep.require(not out.exists(),'fresh contraction output required');out.mkdir(parents=True)
    x=json.loads((P4/'inputs.json').read_text());h=F(x['h'])
    k=json.loads((kernel_dir/'kernel.json').read_text());ep.require(digest(P4/'inputs.json')==k['trial_sha256'],'trial hash mismatch');ep.require(k['bits']==BITS and k['n']==N,'kernel precision mismatch')
    for rec in k['arrays']:ep.require(digest(kernel_dir/rec['file'])==rec['sha256'],'kernel array hash')
    _,alpha=load(kernel_dir/'alpha.zlib');_,beta=load(kernel_dir/'beta.zlib')
    _,fa=load(kernel_dir/'fiber_a.zlib');_,fb=load(kernel_dir/'fiber_b.zlib')
    _,radial=load(kernel_dir/'radial_upper.zlib')
    sigs,roots,faces=coefficient_data(x);blocks=sorted(roots,key=lambda v:(len(v),v))
    ep.require(len(blocks)==77,'unexpected symmetric block inventory')
    parents={v[:-1] for v in blocks if len(v)>1}
    engine=Moments(alpha,beta,h,parents=parents)
    marginal_sigs=sorted(sigs);coeffs={}
    gp=P4/'arrays'/'generation.json'
    ep.require(digest(gp)=='6806eb35348db6792d3ebdcab5a0d0159123790aef013c418242e4ac7002e115','marginal generation lock')
    gr=json.loads(gp.read_text()); expected={v['file']:v['sha256'] for v in gr['columns']}
    # With source cap 49152h, shell 0 and 1 are both always allowed.
    # Thus the only nonzero physical marginal prefixes are p=2 and p=3.
    for p in [2,3]:
      cols=[]
      for sig in sigs:
        si=marginal_sigs.index(sig);path=P4/'arrays'/f'prefix-{p}-sig-{si:02d}.zlib'
        ep.require(digest(path)==expected[path.name],'marginal column hash mismatch')
        hd,l,u=mar.read_column(path)
        ep.require(hd['bits']==128 and hd['signature']==list(sig) and hd['prefix_shell_count']==p,'marginal binding')
        cols.append(l)
      coeffs[p]=cols
    W=[];a=F(2479900401,2500000000);b=-F(843183,10**9)
    for r in range(N):W.append(ep.ceildiv(Q*(1 if r<=89524 else a+b if r<=89914 else abs(b)).numerator,(1 if r<=89524 else a+b if r<=89914 else abs(b)).denominator))
    source=k['row'];L,U=source['radial_first'],source['radial_last']
    den=math.lcm(h.denominator,10);Rden=x['coefficient_denominator']**2*den**12
    rootlo=roothi=facelo=facehi=0;rows=[];begin=time.monotonic()
    # Integrand-channel ledger avoids treating cancellation among blocks as independent upper bounds.
    for ix,block in enumerate(blocks):
        tick=time.monotonic();bc=engine.block(block);base=engine.power(39-len(block))
        un,mark=dual_mul(base,bc,N,BITS)
        # 40-coordinate witness derivative: beta * ordinary39 + alpha * witness39.
        m40=ep.add_interval(ep.mul_interval((beta,beta),un,N,BITS),ep.mul_interval((alpha,alpha),mark,N,BITS))
        rl=rh=fl=fh=0;f40=falling(40,len(block));f39=falling(39,len(block))
        for r in range(L,U+1):
            c=polynomial_radial_num(roots[block],r,h)*f40*radial[r-L]
            if c>=0:rl+=c*m40[0][r];rh+=c*m40[1][r]
            else:rl+=c*m40[1][r];rh+=c*m40[0][r]
        del m40
        for r in range(U+1):
            if not fa[r] and not fb[r]:continue
            c=0
            for p in [2,3]:
                arow=coeffs[p]
                c+=sum(mult*arow[i][r]*arow[j][r] for i,j,mult in faces[block])
            c*=f39*W[r]
            tl=fb[r]*un[0][r]+fa[r]*mark[0][r]
            th=fb[r]*un[1][r]+fa[r]*mark[1][r]
            if c>=0:fl+=c*tl;fh+=c*th
            else:fl+=c*th;fh+=c*tl
        rootlo+=rl;roothi+=rh;facelo+=fl;facehi+=fh
        record=dict(block=list(block),root_lower_numerator=str(rl),root_upper_numerator=str(rh),face_lower_numerator=str(fl),face_upper_numerator=str(fh))
        rows.append(record)
        (out/'partial.json').write_text(json.dumps(dict(completed=len(rows),total=len(blocks),contributions=rows),indent=2)+'\n')
        emit('BLOCK',index=ix+1,total=len(blocks),block=block,seconds=time.monotonic()-tick,elapsed=time.monotonic()-begin,rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,conv=ep.COUNTS['multiplications'])
        del un,mark,bc,base;gc.collect()
    Zlo=F(k['Z_lower'])
    root_interval=[F(40*rootlo,Rden*Q*Q),F(40*roothi,Rden*Q*Q)]
    prefactor=40*h*h/Zlo
    face_interval=[prefactor*F(facelo,(1<<256)*Q**3),prefactor*F(facehi,(1<<256)*Q**3)]
    I0=F(source['I0']);targets=[11*I0/10**18,10*I0/10**18]
    E=F(json.loads((P4/'rounding-budget.json').read_text())['energy_error_upper'])
    # Exact rational square-root enclosure avoids any float acceptance.
    def sqrt_up(v,bits=320):
        ep.require(v>=0,'negative sqrt')
        n=math.isqrt((v.numerator<<(2*bits))//v.denominator)
        return F(n+1,1<<bits)
    faceU=max(F(0),face_interval[1]);corrected=faceU+E+2*sqrt_up(faceU*E)
    result=dict(format='tp-first-row-square-contraction/v1',bits=BITS,n=N,common_measure='fixed positive dyadic upper coordinate arrays',root_majorant_interval=[str(v) for v in root_interval],face_approx_majorant_interval=[str(v) for v in face_interval],root_target=str(targets[0]),face_target=str(targets[1]),root_ratio_interval=[str(v/targets[0]) for v in root_interval],face_ratio_interval=[str(v/targets[1]) for v in face_interval],marginal_energy_error=str(E),face_with_marginal_error_upper=str(corrected),root_11_certified=root_interval[1]<=targets[0],face_10_certified=corrected<=targets[1],root_majorant_excludes_target=root_interval[0]>targets[0],face_majorant_excludes_target=face_interval[0]>targets[1],convolution_counts=dict(ep.COUNTS),seconds=time.monotonic()-begin,block_count=len(rows),prefixes=[2,3],contributions=rows,physical_integral_lower_bounds_claimed=False,full_152_certified=False,independent_verification=False)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    emit('CONTRACTION_COMPLETE',root_ratio=[float(v/targets[0]) for v in root_interval],face_ratio=[float(v/targets[1]) for v in face_interval],root_pass=result['root_11_certified'],face_pass=result['face_10_certified'],seconds=result['seconds'])
if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--kernel',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();contract(a.kernel,a.output)
