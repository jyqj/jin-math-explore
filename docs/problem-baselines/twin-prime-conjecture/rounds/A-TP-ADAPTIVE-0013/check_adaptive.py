#!/usr/bin/env python3
"""Frozen replay and separately coded finite oracles, not independent mathematical review."""
from __future__ import annotations
import argparse
import copy
from fractions import Fraction as Q
from functools import lru_cache
from itertools import product
from math import gcd, prod, isqrt
from pathlib import Path
import hashlib
import json
import sys
import adaptive_sieve as g


def need(ok: bool,message: str) -> None:
    if not ok:raise ValueError(message)


@lru_cache(None)
def prime_factors(n: int) -> tuple[int,...]:
    out=[]
    for p in range(2,n+1):
        while n%p==0:out.append(p);n//=p
        if n==1:break
    return tuple(out)


@lru_cache(None)
def phi(n: int) -> int:
    return sum(gcd(n,a)==1 for a in range(1,n+1))


def mu(n: int) -> int:
    f=prime_factors(n)
    return (-1)**len(f) if len(f)==len(set(f)) else 0


def independent_raw(cfg: dict,adaptive: bool) -> tuple[dict,dict]:
    sf=[n for n in range(1,prod(cfg['primes'])+1) if mu(n) and set(prime_factors(n))<=set(cfg['primes'])]
    B=Q(cfg['B']);T=cfg['root_max']*cfg['fixed_Z'];raw={};caps={}
    for r,s in product(sf,repeat=2):
        if gcd(r,s)!=1 or r*s>cfg['root_max']:continue
        Z=T//(r*s) if adaptive else cfg['fixed_Z']
        pairs=[q for q in product(sf,repeat=2) if gcd(*q)==1 and prod(q)<=Z]
        G=sum((Q(1,phi(a)*phi(b)) for a,b in pairs),Q(0));caps[(r,s)]=G
        for a,b in pairs:raw[(a,r,s,b)]=Q((3*r+5*s)%11-5,7)/(B*B*G)
    return raw,caps


def independent_coefficients(raw: dict) -> dict:
    # Direct divisibility inversion, as opposed to distributing divisors of each root.
    out={};scaled=[(r,v/prod(phi(a) for a in r)) for r,v in raw.items()]
    for ds in raw:
        val=sum((v for r,v in scaled if all(a%d==0 for a,d in zip(r,ds))),Q(0))
        out[ds]=val*prod(mu(d)*d for d in ds)
    return out


def interval_checks(cert: dict,cfg: dict) -> dict:
    B=Q(cfg['B']);period=prod(cfg['primes']);h=cfg['shifts'];outputs={};allco={};caps_ad={}
    for mode in ('fixed','adaptive'):
        raw,caps=independent_raw(cfg,mode=='adaptive');co=independent_coefficients(raw)
        need(raw==g.arrays(cfg,mode=='adaptive')[1],'raw array definition')
        need(co==g.coefficients(raw),'direct coefficient transform')
        need(len(co)==cert['finite'][mode]['coefficient_count'],'coefficient coverage')
        need(all(prod(d)<=cfg['root_max']*cfg['fixed_Z'] for d in co),'joint product budget')
        allco[mode]=co
        if mode=='adaptive':caps_ad=caps
        out=[]
        for n in range(period):
            dsum=sum((v for ds,v in co.items() if all((n+hi)%d==0 for hi,d in zip(h,ds))),Q(0))
            usum=Q(0)
            for rs,v in raw.items():
                num=den=1
                for ri,hi in zip(rs,h):
                    for p in prime_factors(ri):num*=1-p*int((n+hi)%p==0);den*=p-1
                usum+=v*Q(num,den)
            need(dsum==usum,'divisor vs U expansion')
            out.append(dsum)
        mean=sum((x*x for x in out),Q(0))/period
        need(mean==Q(cert['finite'][mode]['mean']),'complete-period CRT mean')
        diag=sum((v*v/prod(phi(t) for t in r) for r,v in raw.items()),Q(0))
        need(diag==Q(cert['finite'][mode]['independent_mean']),'independent comparison norm')
        outputs[mode]=out
    need(caps_ad[(1,1)]>caps_ad[(5,77)],'capacity genuinely depends on retained roots')
    nonfactor=[n for n in range(period) if outputs['fixed'][n]!=outputs['adaptive'][n]]
    need(bool(nonfactor),'adaptive construction differs from common fixed multiplier')
    def endpoint_multiplier(r):
        allowed=[key for key in raw if key[1:3]==r]
        return sum((Q(1,phi(key[0])*phi(key[-1])) * prod((1-p if 273%p==0 else 1) for p in prime_factors(key[0])) * prod((1-p if (273+8)%p==0 else 1) for p in prime_factors(key[-1])) for key in allowed),Q(0))/caps_ad[r]
    need(endpoint_multiplier((1,1))==Q(1,8) and endpoint_multiplier((5,77))==Q(23,142),'no common multiplier for all residual arrays')
    increases=[n for n in range(period) if outputs['adaptive'][n]**2>outputs['fixed'][n]**2]
    need(bool(increases),'finite pointwise increase control')
    badco={d:v for d,v in allco['adaptive'].items() if mu(prod(d))}
    bad=[sum((v for d,v in badco.items() if all((n+hi)%di==0 for hi,di in zip(h,d))),Q(0)) for n in range(period)]
    need(bad==outputs['adaptive'],'incompatible divisor terms contribute zero')
    raw,_=independent_raw(cfg,True)
    wrongly_filtered={r:v for r,v in raw.items() if mu(prod(r))}
    wrongco=independent_coefficients(wrongly_filtered)
    wrong=[sum((v for d,v in wrongco.items() if all((n+hi)%di==0 for hi,di in zip(h,d))),Q(0)) for n in range(period)]
    need(wrong!=outputs['adaptive'],'deleting shared primes before transform is invalid')
    N=cfg['start'];end=N+cfg['length'];prime=[True]*(end+max(h)+1);prime[:2]=[False,False]
    for p in range(2,isqrt(len(prime)-1)+1):
        if prime[p]:
            for j in range(p*p,len(prime),p):prime[j]=False
    sums={mode:Q(0) for mode in outputs};pair=Q(0);hits=integers=0
    roots,_raw,_rows=g.arrays(cfg,True)
    residual_co=independent_coefficients({r:u/B**2 for r,u in roots.items()})
    for n in range(N,end):
        if n%cfg['W']!=cfg['residue']:continue
        integers+=1
        for mode in sums:sums[mode]+=outputs[mode][n%period]**2
        if prime[n+h[0]] and prime[n+h[-1]]:
            d=sum((u for r,u in residual_co.items() if (n+h[1])%r[0]==0 and (n+h[2])%r[1]==0),Q(0))
            need(outputs['adaptive'][n%period]==d==outputs['fixed'][n%period],'endpoint event equality')
            pair+=d*d;hits+=1
    for mode,total in sums.items():
        need(total==Q(cert['finite'][mode]['interval_sum']) and total>=pair,'interval majorant')
    need(pair==Q(868665843,752953600),'preserved residual model')
    n=increases[0]
    return {'periodic_transform_checks':2*period,'interval_integers':integers,'endpoint_pairs':hits,
            'residual_pair_sum':str(pair),'nonfactor_positions':len(nonfactor),'pointwise_increases':len(increases),
            'first_increase':{'n_mod_period':n,'W_class_representative':next(v for v in range(N,end) if v%period==n and v%cfg['W']==cfg['residue']),'adaptive':str(outputs['adaptive'][n]),'fixed':str(outputs['fixed'][n])},
            'raw_shared_prime_states':sum(not mu(prod(r)) for r in _raw),
            'raw_shared_prime_deletion_rejected':True,'incompatible_divisor_deletion_validated':True}


def local_checks() -> dict:
    entries=products=0
    for m,p in ((0,5),(2,5),(38,41)):
        states=[e+r for e in ((),(0,),(1,)) for r in [()]+[(j+2,) for j in range(m)]]
        delta=Q(0)
        for S in states:
            for T in states:
                val=Q(sum(prod(1-p*int((n+i)%p==0) for i in S+T) for n in range(p)),p*(p-1)**(len(S)+len(T)))
                closed=Q(1-len(set(S)|set(T))+(p-1)*len(set(S)&set(T)),(p-1)**(len(S)+len(T)))
                need(val==closed,'literal local kernel')
                diag=Q(1,(p-1)**len(S)) if S==T else Q(0)
                delta+=abs(val-diag);entries+=1;products+=p
        t=Q(1,p-1)
        need(delta==(m*m+17*m+2)*t*t+(10*m*m-12*m)*t**3+(2*m*m-4*m)*t**4,'local error census')
    return {'local_kernel_entries':entries,'literal_residue_products':products}


def helper_checks(cert: dict,cfg: dict,rho: Q) -> dict:
    raw,caps=independent_raw(cfg,True);B=Q(cfg['B']);sf=sorted(set(t for r in raw for t in r));data=[];fixed=[];count=0
    for r,G in sorted(caps.items()):
        A=Q((3*r[0]+5*r[1])%11-5,7);weight=Q(1,B**2*prod(phi(t) for t in r))
        allowed=[t for t in sf if t<=cfg['helper_root_max'] and t*prod(r)<=cfg['helper_total_max'] and gcd(t,prod(r))==1]
        v=[Q(1,B*phi(t)) for t in allowed];c=sum(v,Q(0));k=B*B/G
        data.append((weight*A*A,c,k));fixed.append((weight*A*A,c,B*B/min(caps.values())))
        for tau in (Q(1,4),Q(1),Q(4)):
            alpha=rho*(1+tau);beta=k*(1+1/tau);star=beta*A/(alpha+beta*c)
            z=[star+Q((t%5)-2,7) for t in allowed];trace=sum((w*y for w,y in zip(v,z)),Q(0))
            objective=alpha*sum((w*y*y for w,y in zip(v,z)),Q(0))+beta*(A-trace)**2
            target=alpha*beta*A*A/(alpha+beta*c)
            err=alpha*sum((w*(y-star)**2 for w,y in zip(v,z)),Q(0))+beta*(trace-c*star)**2
            need(objective-target==err>=0,'variable-penalty square completion');count+=1
    need(g.encode(data)==cert['helper']['data'] and g.encode(fixed)==cert['helper']['fixed_data'],'helper model rebuilt')
    for key,values in (('adaptive_optimum',data),('fixed_optimum',fixed)):
        opt=cert['helper'][key];lo=Q(opt['theta_lower']);hi=Q(opt['theta_upper'])
        def f(t):return sum((w*rho*k/(rho*t+k*c*(1-t)) for w,c,k in values),Q(0))
        def df(t):return sum((-w*rho*k*(rho-k*c)/(rho*t+k*c*(1-t))**2 for w,c,k in values),Q(0))
        need(0<lo<hi<1 and df(lo)<0<df(hi),'convex bracket')
        low=max(f(lo)+df(lo)*(hi-lo),f(hi)+df(hi)*(lo-hi))
        need(Q(opt['minimum_lower'])<=low<=f((lo+hi)/2)<=Q(opt['minimum_upper']),'rational optimum')
    need(Q(cert['helper']['adaptive_optimum']['minimum_upper'])<Q(cert['helper']['fixed_optimum']['minimum_lower']),'strict finite quadratic improvement')
    return {'variable_helper_completions':count,'convex_brackets':2,'zero_capacity_fibres':sum(c==0 for _,c,_ in data)}


def restoration_checks(pars: dict) -> dict:
    rho,gamma,ell,S=(Q(pars[k]) for k in ('rho','gamma','ell','S'));h=S/12;checks=fibres=0
    for theta in (Q(1,4),Q(1,2),Q(3,4)):
        old=gamma**2/(theta*(ell-gamma)**2);new=gamma**2/(theta*ell**2)
        need(new/old==Q(pars['bound_ratio']) and new<old,'coarse constant ratio')
        ph=pf=ee=wd=Q(0)
        for r in range(12):
            s=r*h;c=Q(0) if r%2 else Q(1,3);k=2*rho*rho/(ell-rho*s)**2
            w=rho*k/(rho*theta+k*c*(1-theta));pairs=[(a,b) for a in range(11-r) for b in range(11-r-a)]
            weights=[h*h/Q(1+(a+b)%2) for a,b in pairs]
            H=[Q((3*a+5*b+r)%11-5,9) for a,b in pairs]
            F=[v if (a+2*b+r)%3 else Q(0) for (a,b),v in zip(pairs,H)]
            mass=sum(weights,Q(0));A=sum((v*x for v,x in zip(weights,H)),Q(0));Af=sum((v*x for v,x in zip(weights,F)),Q(0))
            norm=sum((v*(x-y)**2 for v,x,y in zip(weights,H,F)),Q(0));qY=Q(r+1,30)
            need(mass<=(S-s)**2/2 and w*mass<=new,'radial weighted mass bound')
            need(w*(A-Af)**2<=w*mass*norm,'weighted trace inequality')
            ph+=qY*w*A*A;pf+=qY*w*Af*Af;ee+=qY*norm;wd+=qY*w*(A-Af)**2;fibres+=1
        need(wd<=new*ee,'integrated error')
        for eps in (Q(1,4),Q(1),Q(4)):
            need(pf<=(1+eps)*ph+(1+1/eps)*new*ee,'restoration cost');checks+=1
    # The maximum-root penalty really is unchanged, and the restoration cross term cannot be omitted.
    need(2*rho*rho/(ell-gamma)**2==Q(pars['fixed_penalty']),'worst-root equality')
    need(Q(4)>Q(1)+Q(1),'missing-cross-term counterexample')
    return {'restoration_fibres':fibres,'restoration_transfer_checks':checks,'worst_root_equality_checked':True}


def validate(inp: dict,cert: dict,res: dict,expected: tuple) -> None:
    need(inp==g.INPUTS,'input identity');need((cert,res)==expected,'certificate/result mismatch')


def negative_checks(inp: dict,cert: dict,res: dict,expected: tuple) -> int:
    changes=[(0,lambda x:x.update(budget='1/2')),(0,lambda x:x.update(rho='262499/1000000')),
      (0,lambda x:x['finite'].update(W=1)),(0,lambda x:x['finite'].update(fixed_Z=78)),
      (1,lambda x:x['capacity_rows'].pop()),(1,lambda x:x['capacity_rows'][0].update(capacity='1')),
      (1,lambda x:x['finite']['adaptive'].update(mean=x['finite']['adaptive']['independent_mean'])),
      (1,lambda x:x['finite']['adaptive'].update(interval_sum='0')),
      (1,lambda x:x['finite']['adaptive'].update(TV_squared='0')),
      (1,lambda x:x['finite']['adaptive'].update(tensor_error_bound='0')),
      (1,lambda x:x['parameters'].update(restoration_theta_times_new_bound='0')),
      (1,lambda x:x['parameters'].update(bound_ratio='1/10')),
      (1,lambda x:x['helper']['adaptive_optimum'].update(minimum_upper='0')),
      (2,lambda x:x.update(worst_root_constant_improved=True)),
      (2,lambda x:x.update(actual_restored_trace_evaluated=True)),
      (2,lambda x:x.update(helper_prime_contract_verified=True)),
      (2,lambda x:x.update(independently_verified=True)),(2,lambda x:x.update(new_prime_gap_bound=True)),
      (2,lambda x:x.update(cannot_imply=[]))]
    for i,change in changes:
        args=copy.deepcopy([inp,cert,res]);change(args[i])
        try:validate(*args,expected)
        except ValueError:pass
        else:raise ValueError('corruption accepted')
    rho,gamma=Q(inp['rho']),Q(inp['gamma'])
    for ell in (Q(0),gamma,Q(1,2),Q(1)):
        try:g.parameters(rho,gamma,ell)
        except ValueError:pass
        else:raise ValueError('invalid support accepted')
    for theta in (Q(0),Q(1)):
        try:g.soft([(Q(1),Q(0),Q(1))],theta,rho)
        except ValueError:pass
        else:raise ValueError('invalid theta accepted')
    return len(changes)+6


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument('--self-test',action='store_true');ap.add_argument('--check-hashes',action='store_true');ap.add_argument('--require-global',action='store_true')
    args=ap.parse_args()
    try:
        need(not args.require_global,'refused: actual restored data, prime helper contract and detection positivity are absent')
        read=lambda name:json.loads((args.root/name).read_text(encoding='utf-8'))
        inp,cert,res=(read(n) for n in ('inputs.json','certificates.json','results.json'))
        expected=g.build(inp);validate(inp,cert,res,expected);report={'certificate_replay':True}
        if args.self_test:
            report.update(interval_checks(cert,inp['finite']));report.update(local_checks())
            report.update(helper_checks(cert,inp['finite'],Q(inp['rho'])));report.update(restoration_checks(cert['parameters']))
            report['corruptions_rejected']=negative_checks(inp,cert,res,expected)
        if args.check_hashes:
            hashes=read('artifact-sha256.json');names={'README.md','proof.md','adaptive_sieve.py','check_adaptive.py','inputs.json',
                'certificates.json','results.json','source-lock.json','computation-record.json','computation-handoff.json','verification-ticket.md'}
            need(set(hashes)==names,'manifest scope')
            for n,v in hashes.items():need(hashlib.sha256((args.root/n).read_bytes()).hexdigest()==v,'hash mismatch '+n)
            report['hashes_verified']=len(hashes)
        report.update(ok=True,independently_verified=False,new_prime_gap_bound=False)
        print(json.dumps(report,sort_keys=True));return 0
    except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as exc:
        print(json.dumps({'ok':False,'error':str(exc)}),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
