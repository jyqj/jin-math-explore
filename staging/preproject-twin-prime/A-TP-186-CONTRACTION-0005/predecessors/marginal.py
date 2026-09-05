"""Certified finite-difference marginal arrays; standard library only.

The enclosure proof is in marginal-proof.md. No floating-point acceptance,
FFT, original FLINT run, or original Lean build is performed. Source identities
(Dickman density and physical cap restriction) remain explicit imported inputs.
"""
from __future__ import annotations
from collections import defaultdict, Counter
from fractions import Fraction as F
from math import comb,lcm
from pathlib import Path
import hashlib,json,struct,zlib


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def ceildiv(n: int, d: int) -> int:
    require(d > 0, 'positive denominator required')
    return -((-n)//d)


def mul_const(lo: int, hi: int, c: int) -> tuple[int,int]:
    return (lo*c,hi*c) if c>=0 else (hi*c,lo*c)


def cap_cells(m: int, n: int, bits: int=256, order: int=18) -> dict:
    """Enclose rho(j/m) and int_j^(j+1) rho(s/m) ds, n<=3m.

    Taylor even/odd integrated bounds on -R'(j+x). Directed integer
    recurrences contain both the local truncation remainder and roundoff.
    `order` is the even Taylor degree; the odd degree is order+1.
    """
    require(type(m) is int and m>=2 and type(n) is int and 1<=n<=3*m,
            'cap engine requires m>=2 and 1<=n<=3m')
    require(type(bits) is int and bits>=64 and type(order) is int and order>=2 and order%2==0,
            'bits>=64 and positive even Taylor order required')
    Q=1<<bits
    rl=[Q]*(min(m,n)+1); ru=rl.copy()
    ml=[Q]*min(m,n); mu=ml.copy()
    dmax=0
    for j in range(m,n):
        delayed=j>=2*m
        dl,du=(rl[j-m],ru[j-m]) if delayed else (Q,Q)
        al,au=dl//j,ceildiv(du,j)
        elo=ehi=klo=khi=0
        power=1; d=j-m
        for t in range(order+2):
            if t:
                al,au=al//j,ceildiv(au,j)
                if delayed:
                    power*=d
                    den=t*power*j
                    al+=Q//den; au+=ceildiv(Q,den)
            il,iu=al//(t+1),ceildiv(au,t+1)
            jl,ju=al//((t+1)*(t+2)),ceildiv(au,(t+1)*(t+2))
            if t%2==0:
                elo+=il; ehi+=iu; klo+=jl; khi+=ju
            else:
                elo-=iu; ehi-=il; klo-=ju; khi-=jl
            if t==order:
                decrease_upper=ehi
                moment_upper=khi
        decrease_lower=max(0,elo)
        moment_lower=max(0,klo)
        require(decrease_lower<=decrease_upper and moment_lower<=moment_upper,
                'Taylor endpoint inversion')
        ml.append(max(0,rl[j]-moment_upper)); mu.append(min(Q,ru[j]-moment_lower))
        rl.append(max(0,rl[j]-decrease_upper)); ru.append(min(Q,ru[j]-decrease_lower))
        require(0<=ml[-1]<=mu[-1]<=Q and 0<=rl[-1]<=ru[-1]<=Q,'invalid cap enclosure')
        dmax=max(dmax,mu[-1]-ml[-1])
    return dict(m=m,n=n,bits=bits,order=order,node_lower=rl,node_upper=ru,
                mass_lower=ml,mass_upper=mu,max_mass_width_units=dmax)


def fiber_groups(signatures: list[list[int]], matrix: list[list[int]]) -> dict:
    """Expand product_e (p_e(Y)+t^e); duplicate exponents retain multiplicity."""
    require(len(signatures)==len(matrix) and all(len(row)==7 for row in matrix), 'bad coefficient shape')
    out=defaultdict(lambda:[0]*7)
    for sig,coeff in zip(signatures,matrix):
        for mask in range(1<<len(sig)):
            e=sum(v for i,v in enumerate(sig) if mask>>i&1)
            rem=tuple(sorted(v for i,v in enumerate(sig) if not(mask>>i&1)))
            for degree,c in enumerate(coeff):
                out[(rem,e)][degree]+=c
    return dict(sorted(out.items()))


def profile_weights(h: F, masses: dict, max_e: int, bits: int) -> list[tuple[list[int],list[int]]]:
    """Common point-mass intervals for g(t_j)*mu_j/h*t_j^e, e=0..max_e."""
    require(masses['bits']==bits and h>0, 'normalization/precision mismatch')
    Q=1<<bits; a=h.numerator; b=2*h.denominator
    result=[([],[]) for _ in range(max_e+1)]
    for j,(ml,mh) in enumerate(zip(masses['mass_lower'],masses['mass_upper'])):
        t=a*(2*j+1)
        # g(t/b)=(21/200)/(1+t/(100b))+(179/200)/(1+907t/(5b)).
        d1=100*b+t; d2=5*b+907*t
        gn=21*100*b*d2+179*5*b*d1; gd=200*d1*d2
        gl=gn*Q//gd; gu=ceildiv(gn*Q,gd)
        lo=ml*gl//Q; hi=ceildiv(mh*gu,Q)
        for e in range(max_e+1):
            result[e][0].append(lo); result[e][1].append(hi)
            lo=lo*t//b; hi=ceildiv(hi*t,b)
    return result


def polynomial_scale(h: F, coeff_den: int=10**10) -> tuple[int,int,int,int]:
    """P(n)=sum c_d ((n+20)h-9/10)^d/coeff_den; one integer numerator scale."""
    B=lcm(h.denominator,10)
    A=h.numerator*(B//h.denominator)
    c=20*A-9*(B//10)
    return A,B,c,coeff_den*B**6


def polynomial_value_num(coeff: list[int], n: int, scale: tuple[int,int,int,int]) -> int:
    A,B,c,_=scale; x=A*n+c
    # Exact Horner with homogeneous denominator B^6.
    y=coeff[6]; power=B
    for d in range(5,-1,-1):
        y=y*x+coeff[d]*power
        power*=B
    return y


def backward_differences(coeff: list[int], n: int, scale: tuple[int,int,int,int]) -> list[int]:
    vals=[polynomial_value_num(coeff,n-i,scale) for i in range(7)]
    return [sum((-1)**i*comb(k,i)*vals[i] for i in range(k+1)) for k in range(7)]


def correlate_scan(weights: tuple[list[int],list[int]], coeff: list[int], L: int,U: int,
                   scale: tuple[int,int,int,int], lower: list[int]|None=None,
                   upper: list[int]|None=None) -> tuple[list[int],list[int]]:
    """Accumulate interval bounds for sum_j w_j P(r+j) 1_{L<=r+j<=U}.

    Denominator is Q*scale[3]. `weights` endpoints are integer units Q^-1.
    Degrees 0..6 are propagated simultaneously with exact integer arithmetic.
    """
    wl,wu=weights; n=len(wl)
    require(len(wu)==n and 0<=L<=U<n and all(0<=a<=b for a,b in zip(wl,wu)), 'bad scan inputs')
    lo=[0]*n if lower is None else lower
    hi=[0]*n if upper is None else upper
    require(len(lo)==len(hi)==n,'output length mismatch')
    pU=backward_differences(coeff,U,scale)
    pL=backward_differences(coeff,L-1,scale)
    a=[0]*8; b=[0]*8
    for r in range(U,-1,-1):
        enter=U-r; leave=L-r-1
        el,eu=wl[enter],wu[enter]
        ll,lu=(wl[leave],wu[leave]) if leave>=0 else (0,0)
        # Ascending k means a[k+1],b[k+1] still refer to the previous r.
        for k in range(7):
            enlo,enhi=(el*pU[k],eu*pU[k]) if pU[k]>=0 else (eu*pU[k],el*pU[k])
            outlo,outhi=(ll*pL[k],lu*pL[k]) if pL[k]>=0 else (lu*pL[k],ll*pL[k])
            a[k],b[k]=a[k]-b[k+1]+enlo-outhi,b[k]-a[k+1]+enhi-outlo
        lo[r]+=a[0]; hi[r]+=b[0]
    require(all(a<=b for a,b in zip(lo,hi)),'scan enclosure inversion')
    return lo,hi


def correlate_direct(weights: tuple[list[int],list[int]], coeff: list[int],L:int,U:int,
                     r:int,scale:tuple[int,int,int,int])->tuple[int,int]:
    wl,wu=weights; lo=hi=0
    for j in range(max(0,L-r),min(len(wl)-1,U-r)+1):
        p=polynomial_value_num(coeff,r+j,scale)
        a,b=mul_const(wl[j],wu[j],p);lo+=a;hi+=b
    return lo,hi


def write_column(path:Path, lo:list[int],hi:list[int],den:int,outbits:int,
                 metadata:dict, delta_order:int=7) -> dict:
    """Lossless zlib file. Both stored endpoints are outward dyadic roundings.

    Header is JSON preceded by a 4-byte length. Payload: for each r,
    signed little-endian backward difference of the lower endpoint
    (lower_bytes), then unsigned width (width_bytes). The delta_order-fold
    difference uses zero padding before index 0 and is exactly reversible.
    """
    require(den>0 and len(lo)==len(hi),'bad output scaling')
    low=[(a<<outbits)//den for a in lo]
    high=[ceildiv(b<<outbits,den) for b in hi]
    widths=[b-a for a,b in zip(low,high)]
    require(min(widths,default=0)>=0,'stored endpoints crossed')
    require(type(delta_order) is int and 0<=delta_order<=12, 'invalid lossless delta order')
    dc=[(-1)**i*comb(delta_order,i) for i in range(delta_order+1)]
    encoded=[sum(dc[i]*low[j-i] for i in range(min(delta_order,j)+1)) for j in range(len(low))]
    signed_bits=max((abs(x).bit_length()+1 for x in encoded),default=1)
    lb=max(1,(signed_bits+7)//8); wb=max(1,(max(widths,default=0).bit_length()+7)//8)
    header=dict(format='tp-signed-dyadic-column/v1',count=len(lo),bits=outbits,
                lower_bytes=lb,width_bytes=wb,delta_order=delta_order,**metadata)
    head=json.dumps(header,sort_keys=True,separators=(',',':')).encode()
    enc=zlib.compressobj(9); sha=hashlib.sha256();tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('wb') as f:
        buf=struct.pack('<I',len(head))+head
        sha.update(buf);f.write(enc.compress(buf))
        for off in range(0,len(low),1024):
            buf=b''.join(a.to_bytes(lb,'little',signed=True)+w.to_bytes(wb,'little') for a,w in zip(encoded[off:off+1024],widths[off:off+1024]))
            sha.update(buf);f.write(enc.compress(buf))
        f.write(enc.flush())
    tmp.replace(path)
    return dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),raw_sha256=sha.hexdigest(),bytes=path.stat().st_size,count=len(lo),bits=outbits,max_width_units=max(widths),nonzero_widths=sum(w>0 for w in widths),exact_zero_count=sum(a==b==0 for a,b in zip(low,high)),max_abs_endpoint_units=max(max(map(abs,low),default=0),max(map(abs,high),default=0)))


def read_column(path:Path) -> tuple[dict,list[int],list[int]]:
    raw=zlib.decompress(path.read_bytes()); sz=struct.unpack('<I',raw[:4])[0]
    head=json.loads(raw[4:4+sz]); data=memoryview(raw)[4+sz:]
    lb,wb,n=head['lower_bytes'],head['width_bytes'],head['count']; stride=lb+wb
    require(len(data)==n*stride,'bad column payload length')
    lo=[];hi=[]
    order=head.get('delta_order',0)
    require(type(order) is int and 0<=order<=12, 'invalid delta order')
    dc=[(-1)**i*comb(order,i) for i in range(order+1)]
    for p in range(0,len(data),stride):
        value=int.from_bytes(data[p:p+lb],'little',signed=True); w=int.from_bytes(data[p+lb:p+stride],'little')
        j=len(lo)
        l=value-sum(dc[i]*lo[j-i] for i in range(1,min(order,j)+1))
        lo.append(l);hi.append(l+w)
    return head,lo,hi
