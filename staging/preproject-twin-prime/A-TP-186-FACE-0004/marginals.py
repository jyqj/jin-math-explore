"""Certified shell marginal coefficients by exact finite-difference sliding.

No FFT. Signed centers use exact integers; uncertainty is accumulated separately
with an absolute polynomial bound. See marginal-proof.md for the physical h.
"""
from fractions import Fraction as F
from collections import Counter,defaultdict
from math import comb
from pathlib import Path
import json,sys,time,zlib,hashlib,struct,argparse
from exact_backend import require,ceildiv,floorf,ceilf,load_inputs,HERE

def log_increment(j,bits):
    """Exact atanh-series enclosure of log((j+1)/j), j>=2."""
    require(isinstance(j,int) and j>=2 and bits>=64,'log domain')
    z=F(1,2*j+1);z2=z*z;power=z;partial=F(0);scale=1<<bits
    for n in range(256):
        partial+=2*power/(2*n+1);power*=z2
        tail=2*power/((2*n+3)*(1-z2))
        if tail<F(1,scale*64):
            return floorf(partial*scale),ceilf((partial+tail)*scale)
    raise ArithmeticError('log series budget')

def master_logs(first,last,bits):
    require(2<=first<=last,'log table domain')
    lo=[0]*(last+1);hi=[0]*(last+1)
    for j in range(first,last):
        a,b=log_increment(j,bits);lo[j+1]=lo[j]+a;hi[j+1]=hi[j]+b
    return lo,hi

def delay_coefficients(terms=80):
    b=F(0);out=[]
    for n in range(1,terms+1):
        b=b/2+F(1,2*n)
        out.append(((-1)**(n+1))*b/(n+1))
    return out

GCO=delay_coefficients()

def extra_delay(y,bits):
    """G(2+y)=integral_0^y log(1+s)/(2+s) ds, 0<=y<=1/8.
    All coefficient magnitudes <=1. The omitted series tail is bounded
    by y^(82)/(82*(1-y)); this implementation uses the universal y<=1/8.
    """
    require(F(0)<=y<=F(1,8),'second-delay domain')
    if not y:return 0,0
    scale=1<<bits;lo=hi=0
    for c in reversed(GCO):
        lo=floorf(y*lo)+floorf(c*scale)
        hi=ceilf(y*hi)+ceilf(c*scale)
    lo=floorf(y*y*lo);hi=ceilf(y*y*hi)
    tail=ceilf(F(1,8)**82/F(82)/F(7,8)*scale)
    return max(0,lo-tail),hi+tail

def cap_cells(cap,count,bits,logs,log_first):
    """Integral of rho(t/(cap*h)) on cell j, divided by h, in units 2^-bits.
    Exact primitive on [0,3), evaluated by outward rational log/delay series.
    """
    require(log_first<=cap and count<3*cap and F(max(0,count-2*cap),cap)<=F(1,8),'cap primitive range')
    scale=1<<bits;ll,lh=logs
    def logx(j):return ll[j]-lh[cap],lh[j]-ll[cap]
    def primitive(j):
        if j<=cap:return j*scale,j*scale
        l,u=logx(j)
        if j<=2*cap:
            return (2*j-cap)*scale-j*u,(2*j-cap)*scale-j*l
        l1,u1=logx(j-cap);gl,gu=extra_delay(F(j-2*cap,cap),bits)
        return ((3*j-3*cap)*scale-j*u-(j-cap)*u1+j*gl,
                (3*j-3*cap)*scale-j*l-(j-cap)*l1+j*gu)
    lo=[];hi=[];prev=primitive(0)
    for j in range(count):
        nxt=primitive(j+1)
        a=max(0,nxt[0]-prev[1]);b=min(scale,nxt[1]-prev[0])
        require(0<=a<=b<=scale,'cap mass enclosure crossed')
        lo.append(a);hi.append(b);prev=nxt
    return lo,hi

def fibers(signature):
    """Expand the labeled angular occurrences after erasing one coordinate."""
    out=Counter()
    for mask in range(1<<len(signature)):
        rem=tuple(signature[i] for i in range(len(signature)) if not mask>>i&1)
        e=sum(signature[i] for i in range(len(signature)) if mask>>i&1)
        out[(rem,e)]+=1
    return out

def grouped_polynomials(data):
    groups=defaultdict(lambda:[0]*7)
    for sig,coeffs in zip(data['signatures'],data['coefficients']):
        for key,multiplicity in fibers(tuple(sig)).items():
            for d,c in enumerate(coeffs):groups[key][d]+=multiplicity*c
    return dict(groups)

def poly_setup(coeffs,h):
    """P(n) = P_int(n)/(10^10*(10*den(h))^6)."""
    den=10*h.denominator;a=10*h.numerator;b=200*h.numerator-9*h.denominator
    cp=[c*den**(6-d) for d,c in enumerate(coeffs)]
    def value(n):
        x=a*n+b;y=0
        for c in reversed(cp):y=y*x+c
        return y
    def differences(n):
        row=[value(n+j) for j in range(7)];out=[]
        while row:
            out.append(row[0]);row=[y-x for x,y in zip(row,row[1:])]
        return out
    return value,differences,den**6*10**10,(a,b,den)

def slide(coeffs,mid,errors,h,left,right,rmax):
    """Exact signed center correlation and rigorous uncertainty numerator.
    Window is left<=r+q<=right. The denominator is poly_den*2^work_bits.
    """
    require(len(mid)==len(errors) and 0<=left<=right and rmax>=0,'sliding domain')
    value,diffs,poly_den,(a,b,den)=poly_setup(coeffs,h)
    count=len(mid);maxx=max(abs(a*left+b),abs(a*right+b))
    bound=sum(abs(c)*maxx**d*den**(6-d) for d,c in enumerate(coeffs))
    ep=[0]
    for x in errors:require(x>=0,'negative weight radius');ep.append(ep[-1]+x)
    qlo=max(0,left);qhi=min(count-1,right)
    state=[0]*7
    if qlo<=qhi:
        vals=diffs(qlo)
        for q in range(qlo,qhi+1):
            w=mid[q]
            for d in range(7):state[d]+=w*vals[d]
            for d in range(6):vals[d]+=vals[d+1]
    dl,du=diffs(left),diffs(right+1)
    centers=[];radii=[]
    for r in range(rmax+1):
        centers.append(state[0]);l=max(0,left-r);u=min(count-1,right-r)
        radii.append(bound*(ep[u+1]-ep[l]) if l<=u else 0)
        out=right-r;into=left-r-1
        wo=mid[out] if 0<=out<count else 0
        wi=mid[into] if 0<=into<count else 0
        for d in range(7):
            state[d]+= (state[d+1] if d<6 else 0) + wi*dl[d]-wo*du[d]
    return centers,radii,poly_den

def weights_for_powers(data,cells,bits):
    h=F(data['h']);count=data['count'];scale=1<<bits
    mids=[[] for _ in range(7)];errors=[[] for _ in range(7)]
    for j in range(count):
        t=(F(j)+F(1,2))*h
        g=F(21,200)/(1+t/100)+F(179,200)/(1+F(907,5)*t)
        power=F(1)
        for e in range(7):
            gl=g*power
            lo=floorf(gl*cells[0][j]);hi=ceilf(gl*cells[1][j])
            mid=(lo+hi)//2;radius=max(mid-lo,hi-mid)
            mids[e].append(mid);errors[e].append(radius)
            power*=t
    return mids,errors

def save_intervals(path,arrays,bits,metadata):
    """Public deterministic format: JSON header; signed 32-byte low + unsigned
    16-byte width, little endian, zlib compressed. No pickle/object execution.
    """
    keys=list(arrays);header=dict(metadata,bits=bits,keys=keys,lengths=[len(arrays[k][0]) for k in keys],encoding='i256_low_u128_width_le')
    text=json.dumps(header,sort_keys=True,separators=(',',':')).encode()
    compressor=zlib.compressobj(6);dig=hashlib.sha256()
    with Path(path).open('wb') as f:
        head=b'TPMARG04'+len(text).to_bytes(8,'little')+text
        f.write(head);dig.update(head)
        for k in keys:
            low,high=arrays[k];require(len(low)==len(high),'output shape')
            buf=bytearray()
            for a,b in zip(low,high):
                require(a<=b,'negative output interval width')
                buf+=a.to_bytes(32,'little',signed=True)+(b-a).to_bytes(16,'little')
                if len(buf)>=1<<20:
                    raw=bytes(buf);dig.update(raw);f.write(compressor.compress(raw));buf.clear()
            raw=bytes(buf);dig.update(raw);f.write(compressor.compress(raw))
        f.write(compressor.flush())
    return {'path':Path(path).name,'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'decoded_sha256':dig.hexdigest(),'bytes':Path(path).stat().st_size,'header':header}

def read_intervals(path):
    with Path(path).open('rb') as f:
        require(f.read(8)==b'TPMARG04','array magic')
        n=int.from_bytes(f.read(8),'little');require(n<1<<20,'array header too large')
        header=json.loads(f.read(n));raw=zlib.decompress(f.read())
    require(header['encoding']=='i256_low_u128_width_le','array encoding')
    require(len(raw)==sum(header['lengths'])*48,'array payload size')
    arrays={};offset=0
    for key,n in zip(header['keys'],header['lengths']):
        lo=[];hi=[]
        for _ in range(n):
            a=int.from_bytes(raw[offset:offset+32],'little',signed=True);w=int.from_bytes(raw[offset+32:offset+48],'little');offset+=48
            lo.append(a);hi.append(a+w)
        arrays[key]=lo,hi
    return header,arrays

def run(output_dir):
    output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    data=load_inputs();h=F(data['h']);count=data['count'];rmax=data['rmax'];wp=data['marginal_work_bits'];op=data['marginal_output_bits']
    require(wp>op>=64,'marginal precisions')
    started=time.monotonic();first=min(s[2] for s in data['shells']);logs=master_logs(first,count,wp)
    print('LOG_TABLE',count-first,'seconds',round(time.monotonic()-started,3),file=sys.stderr,flush=True)
    groups=grouped_polynomials(data);signatures=[tuple(s) for s in data['signatures']]
    cumulative={str(i):([0]*(rmax+1),[0]*(rmax+1)) for i in range(11)}
    records=[];maxmasswidth=0;checks=[]
    for si,(left,right,cap) in enumerate(data['shells']):
        cells=cap_cells(cap,count,wp,logs,first)
        maxmasswidth=max(maxmasswidth,max(b-a for a,b in zip(*cells)))
        massrecord=save_intervals(output_dir/f'cap-{cap}.bin.zlib',{'mass_over_h':cells},wp,{'kind':'genuine_cap_cell_mass','cap_cells':cap,'count':count})
        mids,errs=weights_for_powers(data,cells,wp);del cells
        print('WEIGHTS',si,'seconds',round(time.monotonic()-started,3),file=sys.stderr,flush=True)
        widths=[]
        for ti,sig in enumerate(signatures):
            center=[0]*(rmax+1);radius=[0]*(rmax+1)
            for (rem,e),coeffs in groups.items():
                if rem!=sig:continue
                c,d,den=slide(coeffs,mids[e],errs[e],h,left,right,rmax)
                center=[x+y for x,y in zip(center,c)];radius=[x+y for x,y in zip(radius,d)]
                # Direct exact dot-product at seven production-grid radii.
                value=poly_setup(coeffs,h)[0]
                for r in (0,left,max(0,left-1),right,min(rmax,89524),min(rmax,89914),rmax):
                    if not 0<=r<=rmax:continue
                    l=max(0,left-r);u=min(count-1,right-r)
                    direct=sum(mids[e][q]*value(r+q) for q in range(l,u+1))
                    require(direct==c[r],'production direct-dot mismatch')
                    checks.append([si,ti,e,r])
            divisor=den*(1<<(wp-op));lo=[(c-e)//divisor for c,e in zip(center,radius)];hi=[ceildiv(c+e,divisor) for c,e in zip(center,radius)]
            oldlo,oldhi=cumulative[str(ti)];cumulative[str(ti)]=[a+b for a,b in zip(oldlo,lo)],[a+b for a,b in zip(oldhi,hi)]
            widths.append(max(b-a for a,b in zip(lo,hi)))
            print('MARGINAL',si,ti,'width_units',widths[-1],'seconds',round(time.monotonic()-started,2),file=sys.stderr,flush=True)
        del mids,errs
        record={'shell':si,'cap_mass':massrecord,'max_shell_width_units':max(widths)}
        if si+1 in data['needed_prefixes']:
            record['prefix']=save_intervals(output_dir/f'prefix-{si+1}.bin.zlib',cumulative,op,{'kind':'genuine_marginal_coefficient','physical_h_omitted':True,'retained_profile_product_omitted':True,'prefix':si+1,'rmin':0,'rmax':rmax,'signatures':data['signatures']})
        records.append(record)
    result={'status':'CERTIFIED_MARGINAL_ARRAY_CANDIDATE','input_sha256':hashlib.sha256((HERE/'inputs.json').read_bytes()).hexdigest(),'work_bits':wp,'output_bits':op,'radii':rmax+1,'signatures':11,'stored_prefixes':2,'stored_coefficient_intervals':2*11*(rmax+1),'cap_cell_intervals':3*count,'max_cap_mass_width_units':maxmasswidth,'direct_exact_checks':len(checks),'direct_check_scope':'signed-center exact dot equality at seven selected production radii per fiber polynomial; not an independent integral proof','records':records,'wall_seconds':round(time.monotonic()-started,3),'full_face_evaluated':False,'independent_verification':False}
    (output_dir/'marginal-result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=HERE/'generated');args=parser.parse_args()
    print(json.dumps(run(args.output_dir),indent=2))
