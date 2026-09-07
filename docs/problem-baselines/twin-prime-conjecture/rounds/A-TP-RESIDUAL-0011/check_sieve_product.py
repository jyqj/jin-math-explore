#!/usr/bin/env python3
"""Replay certificates and use separate literal residue/divisor/interval oracles."""
from __future__ import annotations
import argparse
import copy
from fractions import Fraction as F
from functools import lru_cache
from itertools import product
from math import prod, isqrt, gcd
from pathlib import Path
import hashlib
import json
import sys
import sieve_product as candidate

NAMES={"README.md","proof.md","sieve_product.py","check_sieve_product.py","inputs.json","certificates.json",
       "results.json","source-lock.json","computation-record.json","computation-handoff.json","verification-ticket.md"}


def require(ok: bool,message: str) -> None:
    if not ok:raise ValueError(message)


@lru_cache(None)
def reference() -> tuple[dict,dict]:
    return candidate.build(candidate.INPUTS)


def validate(cert: dict,res: dict,inp: dict) -> None:
    require(inp==candidate.INPUTS,"input contract changed")
    ec,er=reference()
    require(cert==ec,"certificate replay mismatch")
    require(res==er,"result scope or numbers changed")


def literal_kernel_checks() -> dict:
    checked=0;residue_products=0
    for m,ps in [(0,[5,7]),(1,[5,7]),(2,[5,7,11]),(5,[7,11]),(38,[41,43,47])]:
        choices=[tuple(j for j,b in enumerate(bits) if b) for bits in product((False,True),repeat=2)]
        sets=[s+extra for s in choices for extra in [()]+[(j,) for j in range(2,m+2)]]
        for p in ps:
            features=[[prod(1-p if n==j else 1 for j in s) for n in range(p)] for s in sets]
            delta=F(0);dd=F(0)
            for i,s in enumerate(sets):
                for j,t in enumerate(sets):
                    numerator=sum(x*y for x,y in zip(features[i],features[j]))
                    val=F(numerator,p*(p-1)**(len(s)+len(t)))
                    bit_s=sum(2**r for r in s);bit_t=sum(2**r for r in t)
                    require(val==candidate.kernel(p,bit_s,bit_t),"literal local moment")
                    diag=F(1,(p-1)**len(s)) if s==t else F(0)
                    delta+=abs(val-diag);dd+=diag
                    checked+=1;residue_products+=p
            rec=candidate.local_record(m,p)
            require(delta==rec['delta'] and dd==rec['independent_mass'],"literal local L1 census")
    return {"literal_local_entries":checked,"literal_residue_products":residue_products}


def factors(n: int) -> list[int]:
    out=[];d=2
    while d*d<=n:
        if n%d==0:
            out.append(d)
            while n%d==0:n//=d
        d+=1
    if n>1:out.append(n)
    return out


def totient(n: int) -> int:
    for p in factors(n):n=n//p*(p-1)
    return n


def isprime(n: int) -> bool:
    return n>=2 and all(n%d for d in range(2,isqrt(n)+1))


def finite_oracle(cert: dict,inp: dict) -> dict:
    cfg=inp['finite'];ps=cfg['primes'];B=F(cfg['B']);W=cfg['W'];hs=cfg['shifts'];N=cfg['start'];L=cfg['length']
    roots={tuple(r):F(v) for r,v in cert['finite']['roots']}
    # Invert the loop order: each divisor tuple sums its multiples directly.
    ret_coeff={d:(-1)**sum(len(factors(v)) for v in d)*prod(d)/B**2*
               sum((u/F(prod(totient(v) for v in r)) for r,u in roots.items() if all(ri%di==0 for ri,di in zip(r,d))),F(0))
               for d in roots}
    av=[n for n in range(1,cfg['Za']+1) if gcd(n,W)==1 and all(n%(p*p) for p in factors(n))]
    bv=[n for n in range(1,cfg['Zb']+1) if gcd(n,W)==1 and all(n%(p*p) for p in factors(n))]
    Ga=sum((F(1,totient(n)) for n in av),F(0));Gb=sum((F(1,totient(n)) for n in bv),F(0))
    require(str(Ga)==cert['finite']['Ga'] and str(Gb)==cert['finite']['Gb'],"independent Selberg normalizers")
    def aux_coeff(v,G):
        return {d:F((-1)**len(factors(d))*d,G)*sum((F(1,totient(a)) for a in v if a%d==0),F(0)) for d in v}
    alpha=aux_coeff(av,Ga);beta=aux_coeff(bv,Gb)
    def div_sum(n):
        D=sum((c for d,c in ret_coeff.items() if all((n+h)%di==0 for h,di in zip(hs[1:-1],d))),F(0))
        La=sum((c for d,c in alpha.items() if (n+hs[0])%d==0),F(0))
        Lb=sum((c for d,c in beta.items() if (n+hs[-1])%d==0),F(0))
        return D,La,Lb
    def U(n,p,h):return F(1-p*int((n+h)%p==0),p-1)
    def raw_sum(n):
        D=sum((u*prod(U(n,p,h) for h,rj in zip(hs[1:-1],r) for p in factors(rj)) for r,u in roots.items()),F(0))/B**2
        La=sum((prod(U(n,p,hs[0]) for p in factors(a)) for a in av),F(0))/Ga
        Lb=sum((prod(U(n,p,hs[-1]) for p in factors(b)) for b in bv),F(0))/Gb
        return D,La,Lb
    period=prod(ps);s=F(0)
    for j in range(period):
        n=cfg['residue']+W*j;values=div_sum(n)
        require(values==raw_sum(n),"coefficient/diagonal values")
        s+=prod(values)**2
    mean=s/period
    require(mean==F(cert['finite']['CRT_mean']),"period versus CRT mean")
    interval=F(0);pair=F(0);pairs=0;integers=0
    for n in range(N,N+L):
        if n%W!=cfg['residue']:continue
        D,La,Lb=div_sum(n);interval+=(D*La*Lb)**2;integers+=1
        if isprime(n+hs[0]) and isprime(n+hs[-1]):
            require(La==1 and Lb==1,"prime endpoint weights")
            pair+=D*D;pairs+=1
    require(interval==F(cert['finite']['interval_sum']),"interval versus CRT")
    require(pair<=interval and pair>0,"nonzero residual majorization")
    require(mean!=F(cert['finite']['independent_mean']),"cross-coordinate correction is nonzero")
    # Independent arithmetic checks of each fibre's completing-square identity.
    completions=0
    for case in cert['soft_helper']['cases']:
        a=F(case['a']);b=F(case['b']);total=F(0)
        for row in case['fibres']:
            A=F(row['target']);cap=F(row['capacity']);v=F(row['helper_value']);r=row['root']
            weights=[F(1,B*totient(t)) for t in row['allowed']]
            require(cap==sum(weights,F(0)),"fibre capacity")
            pert=[v+F((-1)**i*(i+1),11) for i in range(len(weights))]
            norm=lambda xs:sum((w*x*x for w,x in zip(weights,xs)),F(0))
            trace=lambda xs:sum((w*x for w,x in zip(weights,xs)),F(0))
            cost=a*norm(pert)+b*(A-trace(pert))**2
            minimum=a*b*A*A/(a+b*cap)
            diff=[x-v for x in pert]
            require(cost-minimum==a*norm(diff)+b*trace(diff)**2,"quadratic completion")
            require(v==b*A/(a+b*cap) and F(row['residual'])==A-cap*v,"soft minimizer")
            total+=minimum/(B**2*prod(totient(x) for x in r));completions+=1
        require(total==F(case['soft_cost']),"helper full norm")
    opt=cert['soft_helper']['optimized'];lo=F(opt['theta_lower']);hi=F(opt['theta_upper'])
    rho=F(inp['rho']);kap=rho*rho/F(1,10)**2
    data=[(F(row['target'])**2/(B**2*prod(totient(x) for x in row['root'])),F(row['capacity']))
          for row in cert['soft_helper']['cases'][0]['fibres']]
    value=lambda t:sum((weight/(t/kap+(1-t)*cap/rho) for weight,cap in data),F(0))
    deriv=lambda t:sum((-weight*(1/kap-cap/rho)/(t/kap+(1-t)*cap/rho)**2 for weight,cap in data),F(0))
    require(0<lo<hi<1 and deriv(lo)<0<deriv(hi),'convex optimizer bracket')
    tangent=max(value(lo)+deriv(lo)*(hi-lo),value(hi)+deriv(hi)*(lo-hi))
    require(F(opt['minimum_lower'])<=tangent<=value((lo+hi)/2)<=F(opt['minimum_upper']),'optimizer certificate')
    require(F(opt['tau_lower'])==lo/(1-lo) and F(opt['tau_upper'])==hi/(1-hi),'Young parameter conversion')
    return {"periodic_diagonal_checks":period,"direct_interval_integers":integers,"endpoint_prime_pairs":pairs,
            "pair_square_sum":str(pair),"product_majorant":str(interval),"fibre_completions":completions,
            "finite_cross_correction":str(mean-F(cert['finite']['independent_mean']))}


def negative_checks(cert: dict,res: dict,inp: dict) -> int:
    bad=[]
    def add(j,fn):
        v=[copy.deepcopy(cert),copy.deepcopy(res),copy.deepcopy(inp)];fn(v[j]);bad.append(v)
    add(0,lambda c:c['kernel']['census'].pop())
    add(0,lambda c:c['kernel']['delta_polynomial'].__setitem__(2,2098))
    add(0,lambda c:c['kernel'].__setitem__('triple_diagonal_at43',c['kernel']['false_independent_triple']))
    add(0,lambda c:c['kernel']['records'][0].__setitem__('delta','0'))
    add(0,lambda c:c['finite'].__setitem__('CRT_mean',c['finite']['independent_mean']))
    add(0,lambda c:c['finite'].__setitem__('CRT_error_bound','0'))
    add(0,lambda c:c['finite'].__setitem__('Ga',c['finite']['Gb']))
    add(0,lambda c:c['finite'].__setitem__('interval_sum','0'))
    add(0,lambda c:c['exponents'].__setitem__('boundary_admissible',True))
    add(0,lambda c:c['exponents']['admissible'][0].__setitem__('penalty','1'))
    add(0,lambda c:c['soft_helper']['cases'][0]['fibres'][0].__setitem__('helper_value','0'))
    add(0,lambda c:c['soft_helper']['cases'][0].__setitem__('zero_capacity_fibres',0))
    add(0,lambda c:c['soft_helper']['optimized'].__setitem__('minimum_upper','0'))
    add(0,lambda c:c['soft_helper']['optimized'].__setitem__('theta_lower','1'))
    add(1,lambda c:c.__setitem__('independently_verified',True))
    add(1,lambda c:c.__setitem__('new_prime_gap_bound',True))
    add(1,lambda c:c.__setitem__('arithmetic_bridge_to_actual_restored_trial',True))
    add(1,lambda c:c.__setitem__('cannot_imply',[]))
    add(2,lambda c:c.__setitem__('rho','262499/1000000'))
    add(2,lambda c:c['finite'].__setitem__('W',1))
    for i,case in enumerate(bad):
        try:validate(*case)
        except (ValueError,TypeError,KeyError):continue
        raise ValueError('corruption accepted '+str(i))
    rho=F(inp['rho']);gamma=F(inp['gamma']);star=(1-2*gamma)/4
    for bad_z in (F(0),star,star+F(1,10**6)):
        try:candidate.exponents(rho,gamma,[str(bad_z)])
        except ValueError:continue
        raise ValueError('non-strict exponent accepted')
    return len(bad)+3


def hashes(root: Path) -> int:
    manifest=json.loads((root/'artifact-sha256.json').read_text())
    require(set(manifest)==NAMES,"manifest scope")
    for name,sha in manifest.items():
        require(hashlib.sha256((root/name).read_bytes()).hexdigest()==sha,'hash '+name)
    return len(manifest)


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument('--self-test',action='store_true');ap.add_argument('--check-hashes',action='store_true')
    ap.add_argument('--require-global',action='store_true');args=ap.parse_args()
    try:
        if args.require_global:raise ValueError('refused: no actual restored residual bound or new prime-gap theorem is certified')
        cert,res,inp=(json.loads((args.root/n).read_text()) for n in ('certificates.json','results.json','inputs.json'))
        validate(cert,res,inp);out={'certificate_replay':True}
        if args.self_test:
            out.update(literal_kernel_checks());out.update(finite_oracle(cert,inp));out['corruptions_rejected']=negative_checks(cert,res,inp)
        if args.check_hashes:out['hashes_verified']=hashes(args.root)
        out.update(ok=True,independently_verified=False,new_prime_gap_bound=False)
        print(json.dumps(out,sort_keys=True));return 0
    except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as exc:
        print(json.dumps({'ok':False,'error':str(exc)}),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
