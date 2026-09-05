#!/usr/bin/env python3
"""Fresh full-grid G0:R01 run using an immutable, hash-checked predecessor.

Python standard library and system GMP only. Archive extraction and outputs are
confined to a new working directory. No network, no Project authority mutation.
"""
from __future__ import annotations
import argparse, hashlib, importlib, json, math, os, struct, sys, time, zipfile, zlib
from fractions import Fraction as F
from pathlib import Path

ARCHIVE_SHA = '8e6827feed5d06a9ec49552fa863b7c389ee502e23dbb8040b2bcd3b06f14f38'
UPSTREAM = '61340d0b74163003b32756bb16e91d9209a5e330'
N = 98264
BITS = 320

def need(test, message):
    if not test: raise ValueError(message)

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path, value): Path(path).write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')
def exact(x):
    if isinstance(x,F): return str(x)
    if isinstance(x,dict): return {k:exact(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [exact(v) for v in x]
    return x

def reconstruct_row(index=1):
    """Independent exact evaluation of source-row recurrence and low clipping."""
    need(type(index) is int and index in (0,1),'only rows 0 and 1 are scoped')
    h=F(2742997,258046918656);rho=F(262499,10**6);gap=F(1,10**7)
    S=98304*h;T0=2-F(3,1000)-S;T1=F(2510000,2624989)
    ladders=[]
    for family,T in enumerate((T0,T1)):
        sigma=F(100001,10**6) if family==0 else F(1,2)-F(40481,10**5)+F(1,10**10)
        eps=F(1,10**6) if family==0 else gap
        limit=F(12499,10**6) if family==0 else F(253,20000)
        previous=F(0); rows=[]
        for i in range(25):
            order=min(i//12+1,3)
            cs=((1-5*sigma)/15,F(18,5)) if order==1 else ((1-4*sigma)/16,F(7,2)) if order==2 else ((F(3,80),F(3)) if family==0 else ((1-2*sigma)/20,F(16,5)))
            c,slope=cs; E=rho*(S+T)-F(1,2)
            omega=min(limit,(c-eps-E+2*previous-gap)/slope)
            B=(F(1,2)+2*previous)/rho;xi=(c-slope*omega-eps)/rho
            eta=xi if order<=2 else (xi+S+T-B)/2
            need(previous<omega<=limit and xi>0,'source recurrence failure')
            rows.append(dict(a=B-T,A=B-T+eta,xi=xi,order=order))
            previous=omega
        ladders.append(rows)
    xi=ladders[0][23]['xi'];lo,hi=((xi,3*xi/2) if index==0 else (3*xi/2,F(1,20)))
    theta=math.ceil(7/hi);eligible=[r for rows in ladders for r in rows[:24] if r['xi']<hi]
    cutoff=max(ladders[1][0]['a'],min(max(r['a'],r['A']-hi) for r in eligible))
    L=max(89197,cutoff//h-39);U=min(N-1,ladders[1][24]['a']//h)
    M=lo//h;B=math.ceil(hi/h);cap=49152;threshold=S+gap/rho
    need(0<lo<hi and 2<=M<B<=cap and B*h<=threshold/2,'row domain failure')
    return exact(dict(format='tp-186-source-row/v6',attempt_id='A-TP-186-ROW1-0006',row_id=f'G0:R{index:02}',
        upstream_commit=UPSTREAM,h=h,cells=98304,n=N,source_dimension=40,low=lo,high=hi,slope=theta,
        threshold=threshold,hard_cap=cap*h,first_index=M,last_index=B,cap_index=cap,
        low_rounded=M*h,high_rounded=B*h,cap_rounded=cap*h,radial_cutoff=cutoff,
        radial_first=L,radial_last=U,background_max_count=(N-1)//M,
        designated_max_unmarked=(N-1-M)//M,relative_targets={'root':11 if index==0 else 2285,'face':10 if index==0 else 577},
        young_numerator=961904 if index==0 else 502424,young_denominator=10**6,
        old_rounded_budget=1,I0=F(23685317816,10**24),source_scale=10**18))

def error_budget(inp,row):
    h=F(row['h']);S=98304*h;T=(row['radial_last']+40)*h
    eps=h*F(1,2**128)*sum(S**sum(sig) for sig in inp['signatures'])
    gmin=F(21,200)/(1+S/100)
    count=math.ceil(T/F(row['low_rounded']))
    arg=row['slope']*(T+F(row['high_rounded'])-F(row['threshold']))
    exp_integer=max(0,math.ceil(arg));C=count*3**exp_integer  # e<3, proved bound not float exp
    energy=40*3*C*eps**2/gmin**2
    return exact(dict(format='tp-row1-marginal-error/v1',scope=row['row_id'],epsilon_V=eps,g_min=gmin,
        max_source_total=T,witness_count_bound=count,exponential_argument_bound=arg,
        exponential_integer_bound=exp_integer,cover_weight_upper=C,energy_error_upper=energy,
        explanation='e<3 and positive profile bound; three-prefix error sum; not a physical integral value'))

def extract(archive,target):
    target.mkdir(parents=True)
    with zipfile.ZipFile(archive) as z:
        need(z.testzip() is None,'archive CRC failure')
        for i in z.infolist():
            need((target/i.filename).resolve().is_relative_to(target.resolve()),'unsafe archive path')
            need((i.external_attr>>16)&0o170000 != 0o120000,'archive symlink forbidden')
        z.extractall(target)

def verify_manifest(root):
    hs=json.loads((root/'artifact-sha256.json').read_text())
    for name,digest in hs.items():
        need((root/name).resolve().is_relative_to(root.resolve()),'unsafe manifest path')
        need(sha(root/name)==digest,'dependency bytes changed: '+name)
    return len(hs)

def prepare(archive,work):
    need(sha(archive)==ARCHIVE_SHA,'wrong predecessor archive: labels are not identity')
    extract(archive,work/'predecessor05'); p5=work/'predecessor05/A-TP-186-CONTRACTION-0005'
    counts={'05':verify_manifest(p5)};wp=json.loads((p5/'work-packet.json').read_text());ps=[]
    for v,folder in [(3,'A-TP-186-LOW-0003'),(4,'A-TP-186-MARGINAL-0004')]:
        arc=p5/f'dependencies/attempt0{v}.zip'
        need(sha(arc)==wp['dependencies'][f'attempt0{v}_archive_sha256'],'nested archive mismatch')
        extract(arc,work/f'predecessor0{v}');p=work/f'predecessor0{v}'/folder
        counts[str(v)]='entire_archive_sha256_and_CRC_verified' if v==3 else verify_manifest(p);ps.append(p)
    sys.path[:0]=list(map(str,[p5,*ps]));c=importlib.import_module('contraction');low=importlib.import_module('low_kernel')
    c.PREV3,c.PREV4=ps;c.SCRATCH=work/'scratch';c.SCRATCH.mkdir()
    need((c.N,c.P)==(N,BITS),'unexpected inherited precision/grid')
    return c,low,ps,p5,counts

def build_kernels(c,low,row,out):
    seed=low.seed_cells(row['first_index'],98304,row['slope']*F(row['h']),640)
    arrays=[seed['seed_lower'],seed['seed_upper']]
    w=max(1,(max(map(max,arrays)).bit_length()+7)//8)
    raw=struct.pack('>8sIII',b'TPSEED06',640,98304,w)+b''.join(x.to_bytes(w,'big') for pair in zip(*arrays) for x in pair)
    (out/'seed-enclosures.bin.zlib').write_bytes(zlib.compress(raw,6))
    c.emit('FRESH_SEED_READY',cells=98304,sha256=sha(out/'seed-enclosures.bin.zlib'))
    Q=c.Q; n=N;M,B,Z=(row[k] for k in ['first_index','last_index','cap_index'])
    seed_upper=[c.ceildiv(v,1<<(640-BITS)) for v in arrays[1][:n]]
    del seed,arrays,raw
    H=[0]*M+[c.ceildiv(Q,j) for j in range(M,Z)]+[0]*(n-Z);mark=H[:B]+[0]*(n-B)
    term=[Q]+[0]*(n-1);e0=[0]*n;e1=[0]*n
    for k in range((n-1)//M+1):
        for extra,E in [(0,e0),(1,e1)]:
            coeff=low.eulerian_integers(k+extra+1)
            v=c.gp.convolution(term,coeff,n,divisor=math.factorial(k+extra+1),upper=True)
            for j in range(k*M,n):E[j]+=v[j]
        c.emit('KERNEL_COUNT',count=k,maximum=(n-1)//M)
        if (k+1)*M<n:term=c.gp.convolution(term,H,n,divisor=Q*(k+1),upper=True)
    aa=c.gp.convolution(e0,seed_upper,n,divisor=Q,upper=True)
    bb=c.gp.convolution(c.gp.convolution(e1,mark,n,divisor=Q,upper=True),seed_upper,n,divisor=Q,upper=True)
    c.pack(out/'kernels.zlib',[aa,bb],{'kind':'row1-all-feasible-counts','source_row_sha256':sha(out/'source-row.json')})
    return aa,bb

def aggregate(c,calc,terms,row,budget):
    rlo=sum(int(t['root_lower_numerator']) for t in terms);rhi=sum(int(t['root_upper_numerator']) for t in terms)
    den=c.Q**2*calc.poly_scale**2
    rl,rh=F(40*rlo,den),F(40*rhi,den)
    factor=40*calc.h**2/calc.Zl/(c.Q**2*2**256*calc.Wden)
    fl=[factor*sum(int(t['face_prefix_lower_numerators'][i]) for t in terms) for i in range(3)]
    fu=[factor*sum(int(t['face_prefix_upper_numerators'][i]) for t in terms) for i in range(3)]
    E=F(budget['energy_error_upper']);tau=F(1,10**23)
    fh=(1+tau)*sum(fu[1:])+(1+1/tau)*E
    allh=(1+tau)*sum(fu)+(1+1/tau)*E
    I0=F(row['I0']);unit=I0/10**18
    return exact(dict(kind='actual_full_grid_row1_contraction',row_id=row['row_id'],n=N,bits=BITS,signature_count=len(terms),
        root={'majorant_lower':rl,'upper':rh,'relative_upper':rh/unit,'target_integer':row['relative_targets']['root'],'pass':rh<=row['relative_targets']['root']*unit},
        face={'majorant_approx_lower':sum(fl[1:]),'majorant_approx_upper':sum(fu[1:]),'upper_including_error':fh,'relative_upper':fh/unit,
              'target_integer':row['relative_targets']['face'],'pass':fh<=row['relative_targets']['face']*unit,'all_prefix_upper':allh,'all_prefix_relative':allh/unit,'all_prefix_pass':allh<=row['relative_targets']['face']*unit},
        face_prefix_energies=[{'lower':a,'upper':b} for a,b in zip(fl,fu)],
        aggregation={'root_denominator':str(den),'face_factor':str(factor),'Z_lower':calc.Zl,'Z_upper':calc.Zu,'W_denominator':calc.Wden,'tau':tau,'I0':I0,'error':E},
        semantics='conditional physical-upper-bound candidate; finite-model lower endpoints are not physical lower bounds',
        independent_verification=False,full_152_verified=False,prime_gap_bound_improved=False))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--predecessor',type=Path,required=True);ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--preflight-only',action='store_true');args=ap.parse_args()
    need(not args.work.exists(),'use a new work directory; frozen outputs are never overwritten')
    args.work.mkdir(parents=True);t=time.monotonic();c,low,ps,p5,counts=prepare(args.predecessor,args.work)
    out=args.work/'output';out.mkdir();row=reconstruct_row();inp=json.loads((ps[1]/'inputs.json').read_text());budget=error_budget(inp,row)
    save(out/'source-row.json',row);save(out/'rounding-budget.json',budget)
    locks={'predecessor_archive_sha256':ARCHIVE_SHA,'code_sha256':sha(__file__),'row_sha256':sha(out/'source-row.json'),
           'gmp_sha256':sha(p5/'gmp_poly.py'),'contraction_sha256':sha(p5/'contraction.py'),'marginal_manifest_sha256':sha(ps[1]/'artifact-sha256.json'),'pid':os.getpid(),'dependency_files_checked':counts}
    save(out/'run-lock.json',locks)
    c.emit('ROW1_PREFLIGHT',row=row,dependency_files_checked=counts,gmp=c.gp.version)
    save(out/'backend-tests.json',c.gp.self_test())
    if args.preflight_only:return
    c.gp.stats.update(calls=0,seconds=0.0,max_slot_bytes=0)
    aa,bb=build_kernels(c,low,row,out);calc=c.Calculation(inp,row,aa,bb)
    terms=[calc.contract_one(sig,i) for i,sig in enumerate(calc.squares)]
    result=aggregate(c,calc,terms,row,budget);save(out/'results.json',result)
    save(out/'execution-record.json',dict(pid=os.getpid(),seconds=time.monotonic()-t,python=sys.version,gmp=c.gp.version,gmp_stats=c.gp.stats,code_sha256=sha(__file__),status='completed',numerical_targets_pass=all(result[k]['pass'] for k in ['root','face'])))
    c.emit('FINAL',root_relative_display=float(F(result['root']['relative_upper'])),face_relative_display=float(F(result['face']['relative_upper'])),root_pass=result['root']['pass'],face_pass=result['face']['pass'])

if __name__=='__main__':main()
