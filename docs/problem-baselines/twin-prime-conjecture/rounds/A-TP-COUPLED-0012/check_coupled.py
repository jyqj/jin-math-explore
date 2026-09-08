#!/usr/bin/env python3
"""Exact replay plus distinct literal-residue/capacity/interval checks, not an isolated review."""
from __future__ import annotations
import argparse
import copy
from collections import Counter
from fractions import Fraction as Q
from itertools import product
from math import gcd, isqrt, lcm, prod
from pathlib import Path
import hashlib
import json
import sys
import coupled_sieve as g


def need(ok: bool,message: str) -> None:
    if not ok:raise ValueError(message)


def factors(n: int) -> list[int]:
    out=[];p=2
    while p*p<=n:
        while n%p==0:out.append(p);n//=p
        p+=1
    if n>1:out.append(n)
    return out


def totient(n: int) -> int:
    return sum(gcd(n,a)==1 for a in range(1,n+1))


def sf(n: int) -> bool:
    f=factors(n);return len(f)==len(set(f))


def mu(n: int) -> int:
    return (-1)**len(factors(n)) if sf(n) else 0


def literal_kernels() -> dict:
    entries=residues=0
    for m,ps in ((0,(5,7)),(1,(5,7)),(2,(5,7,11)),(5,(7,11)),(38,(41,43,47))):
        ss=[tuple(sorted(e+r)) for e in ((),(0,),(1,)) for r in [()]+[(j+2,) for j in range(m)]]
        masks=[sum(1<<i for i in s) for s in ss]
        need(masks==g.states(m),'independent state enumeration')
        cc=Counter()
        for s in ss:
            for t in ss:cc[(len(s),len(t),len(set(s)|set(t)),len(set(s)&set(t)),int(s==t))]+=1
        need([list(key)+[cc[key]] for key in sorted(cc)]==g.census(m),'independent census')
        for p in ps:
            numerators=[[prod(1-p*int((n+i)%p==0) for i in s) for n in range(p)] for s in ss]
            distance=Q(0)
            for i,s in enumerate(ss):
                for j,t in enumerate(ss):
                    v=Q(sum(a*b for a,b in zip(numerators[i],numerators[j])),p*(p-1)**(len(s)+len(t)))
                    need(v==g.kernel(p,masks[i],masks[j]),'literal kernel')
                    dv=Q(1,(p-1)**len(s)) if i==j else Q(0)
                    distance+=abs(v-dv);entries+=1;residues+=p
            need(str(distance)==str(g.local_record(m,p)['delta']),'literal L1 error')
    return {'literal_kernel_entries':entries,'literal_residue_products':residues}


def capacities() -> dict:
    cases=0;minimizations=0;collisions=0
    for W in (2,6,30):
        for Z in range(1,61):
            ns=[a for a in range(1,Z+1) if sf(a) and gcd(a,W)==1]
            weights={n:Q(1,totient(n)) for n in ns}
            pairs=[(a,b) for a in ns for b in ns if a*b<=Z and gcd(a,b)==1]
            G=sum((weights[a]*weights[b] for a,b in pairs),Q(0))
            collapsed=sum((Q(2**len(factors(n)),totient(n)) for n in ns),Q(0))
            need(G==collapsed,'pair capacity versus unlabelled product')
            unrestricted=sum((weights[a]*weights[b] for a in ns for b in ns if a*b<=Z),Q(0))
            H=sum(weights.values(),Q(0));ps=[p for p in range(2,Z+1) if factors(p)==[p] and W%p]
            bound=H*H*sum((Q(1,(p-1)**2) for p in ps),Q(0))
            need(0<=unrestricted-G<=bound,'collision-deletion bound')
            if unrestricted>G:collisions+=1
            # Project a signed perturbation to the exact trace-zero hyperplane.
            q=[Q((2*a+3*b)%7-3,11) for a,b in pairs];ww=[weights[a]*weights[b] for a,b in pairs]
            mean=sum((w*x for w,x in zip(ww,q)),Q(0))/G
            vals=[1/G+x-mean for x in q]
            need(sum((w*v for w,v in zip(ww,vals)),Q(0))==1,'trace-one perturbation')
            energy=sum((w*v*v for w,v in zip(ww,vals)),Q(0))
            gap=sum((w*(v-1/G)**2 for w,v in zip(ww,vals)),Q(0))
            need(energy-1/G==gap>=0,'all-coefficient square completion')
            minimizations+=1;cases+=1
    return {'capacity_cases':cases,'strict_collision_cases':collisions,'auxiliary_minimum_identities':minimizations}


def direct_coeff(arr: dict[tuple[int,...],Q],B: Q) -> dict[tuple[int,...],Q]:
    options=sorted(set(a for r in arr for a in r));m=len(next(iter(arr)));out={}
    for ds in product(options,repeat=m):
        if not sf(prod(ds)):continue
        value=sum((u/Q(prod(totient(a) for a in r)) for r,u in arr.items()
                   if all(a%d==0 for a,d in zip(r,ds))),Q(0))
        # Only retain divisor support, including any zero-valued coefficient there.
        if any(all(a%d==0 for a,d in zip(r,ds)) for r in arr):
            out[ds]=Q(prod(mu(d)*d for d in ds),1)/B**m*value
    return out


def direct_finite(cert: dict,cfg: dict) -> dict:
    ps=cfg['primes'];sfns=[n for n in range(1,prod(ps)+1) if sf(n) and all(p in ps for p in factors(n))]
    arr={(a,b):Q((3*a+5*b)%11-5,7) for a in sfns for b in sfns if gcd(a,b)==1}
    B=Q(cfg['B']);lam=direct_coeff(arr,B)
    need(lam==g.transform(g.roots(ps,2),B),'independent diagonal transform')
    auxpairs=[(a,b) for a in sfns for b in sfns if gcd(a,b)==1 and a*b<=cfg['Z']]
    G=sum((Q(1,totient(a)*totient(b)) for a,b in auxpairs),Q(0))
    aux=direct_coeff({r:1/G for r in auxpairs},Q(1))
    need(str(G)==cert['G2'] and sorted(auxpairs)==[tuple(r) for r in cert['auxiliary_pairs']],'finite auxiliary geometry')
    def sieve(n,co,shifts):
        return sum((v for ds,v in co.items() if all((n+h)%d==0 for h,d in zip(shifts,ds))),Q(0))
    def direct_u(n,r,shifts):
        return prod((Q(1-p*int((n+h)%p==0),p-1) for a,h in zip(r,shifts) for p in factors(a)),start=Q(1))
    period=prod(ps);pm=Q(0);diagonal_checks=0
    for n in range(period):
        d=sieve(n,lam,cfg['shifts'][1:3]);a=sieve(n,aux,[cfg['shifts'][0],cfg['shifts'][-1]])
        need(d==sum((u*direct_u(n,r,cfg['shifts'][1:3]) for r,u in arr.items()),Q(0))/B**2,'residual U expansion')
        need(a==sum((direct_u(n,r,[cfg['shifts'][0],cfg['shifts'][-1]]) for r in auxpairs),Q(0))/G,'coupled U expansion')
        pm+=d*d*a*a;diagonal_checks+=1
    need(pm/period==Q(cert['coupled']['CRT_mean']),'CRT mean versus complete literal period')
    end=cfg['start']+cfg['length'];maxn=end+max(cfg['shifts']);prime=[True]*(maxn+1);prime[:2]=[False,False]
    for p in range(2,isqrt(maxn)+1):
        if prime[p]:
            for j in range(p*p,maxn+1,p):prime[j]=False
    total=pair=Q(0);integers=hits=0
    for n in range(cfg['start'],end):
        if n%cfg['W']!=cfg['residue']:continue
        d=sieve(n,lam,cfg['shifts'][1:3]);a=sieve(n,aux,[cfg['shifts'][0],cfg['shifts'][-1]])
        total+=d*d*a*a;integers+=1
        if prime[n+cfg['shifts'][0]] and prime[n+cfg['shifts'][-1]]:
            need(a==1,'coupled sieve equals one on endpoint pair');pair+=d*d;hits+=1
    need(total==Q(cert['coupled']['interval_sum']) and pair<=total,'finite interval comparison')
    need(pair==Q(868665843,752953600),'same T11 residual model')
    crt_cases=0
    for q in range(1,9):
        for r in range(1,9):
            for a in range(q):
                for b in range(r):
                    literal=[n for n in range(lcm(q,r)) if n%q==a and n%r==b]
                    sol=g.crt(((a,q),(b,r)))
                    need((sol is None and not literal) or (sol is not None and literal==[sol[0]] and sol[1]==lcm(q,r)),'noncoprime CRT')
                    crt_cases+=1
    return {'periodic_diagonal_checks':diagonal_checks,'direct_interval_integers':integers,
            'endpoint_prime_pairs':hits,'residual_pair_sum':str(pair),'noncoprime_CRT_cases':crt_cases}


def helper_checks(cert: dict,cfg: dict,rho: Q) -> dict:
    B=Q(cfg['B']);data=[]
    for rs,A in cert['finite']['root_array']:
        A=Q(A);R=prod(rs)
        allowed=[n for n in range(1,cfg['helper_new_root_cutoff']+1) if sf(n) and gcd(n,R*cfg['W'])==1
                 and all(p in cfg['primes'] for p in factors(n)) and n*R<=cfg['helper_product_cutoff']]
        c=sum((Q(1,B*totient(t)) for t in allowed),Q(0))
        data.append((A*A/(B**2*prod(totient(n) for n in rs)),c))
    need([[str(w),str(c)] for w,c in data]==cert['helper']['finite_data'],'helper data direct reassembly')
    old=Q(cert['helper']['old_kappa']);new=Q(cert['helper']['new_kappa']);count=0
    need(new*2==old,'exact half coefficient')
    for t in (Q(1,8),Q(1,4),Q(1,2),Q(3,4),Q(7,8)):
        for w,c in data:
            vo=w*rho*old/(rho*t+old*c*(1-t));vn=w*rho*new/(rho*t+new*c*(1-t))
            need(vo/2<=vn<=vo,'soft improvement is between half and whole')
            if c==0:need(vn==vo/2,'zero-capacity term halves')
            count+=1
    for tag,k in [('old',old),('new',new)]:
        opt=cert['helper'][tag+'_optimum'];lo=Q(opt['theta_lower']);hi=Q(opt['theta_upper'])
        f=lambda t:sum((w*rho*k/(rho*t+k*c*(1-t)) for w,c in data),Q(0))
        df=lambda t:sum((-w*rho*k*(rho-k*c)/(rho*t+k*c*(1-t))**2 for w,c in data),Q(0))
        need(0<lo<hi<1 and df(lo)<0<df(hi),'global convex optimizer bracket')
        lower=max(f(lo)+df(lo)*(hi-lo),f(hi)+df(hi)*(lo-hi))
        need(Q(opt['minimum_lower'])<=lower<=f((lo+hi)/2)<=Q(opt['minimum_upper']),'rational tangent certificate')
    need(Q(cert['helper']['new_optimum']['minimum_upper'])<Q(cert['helper']['old_optimum']['minimum_lower']),'certified finite cost decrease')
    return {'soft_coefficient_comparisons':count,'global_helper_brackets':2,'zero_capacity_fibres':sum(c==0 for w,c in data)}


def stability_checks() -> dict:
    # Rational sub-probability cell densities, explicit triangular pair support.
    tests=0;completions=0
    for grid in (3,5,7):
        h=Q(1,10);S=(grid+3)*h
        for t in (Q(1,4),Q(1,2),Q(3,4)):
            rho=Q(2624989,10**7);kappa=Q(2)*rho*rho/Q(1,5)**2
            ph=pf=norm=weighted_error=Q(0);upper=Q(0)
            for r in range(grid+1):
                pairs=[(a,b) for a in range(grid-r+1) for b in range(grid-r-a+1)]
                ws=[h*h*Q((a%2)+1,2)*Q((b%2)+1,2) for a,b in pairs]
                Hv=[Q((3*a+5*b+r)%9-4,7) for a,b in pairs]
                Fv=[v if (a+2*b+r)%3 else Q(0) for (a,b),v in zip(pairs,Hv)]
                mass=sum(ws,Q(0));A=sum((w*v for w,v in zip(ws,Hv)),Q(0));Af=sum((w*v for w,v in zip(ws,Fv)),Q(0))
                ee=sum((w*(v-u)**2 for w,v,u in zip(ws,Hv,Fv)),Q(0));c=Q(0) if r%2 else Q(grid-r+1,10)
                weight=rho*kappa/(rho*t+kappa*c*(1-t));muY=Q(r+1,20)
                need(mass<=(S-r*h)**2/2,'physical-density pair area bound')
                need((A-Af)**2<=mass*ee,'double-trace Cauchy-Schwarz')
                ph+=muY*weight*A*A;pf+=muY*weight*Af*Af;norm+=muY*ee
                weighted_error+=muY*weight*(A-Af)**2;upper=max(upper,weight*mass)
                completions+=1
            coarse=kappa*S*S/(2*t)
            need(upper<=coarse and weighted_error<=upper*norm,'weighted trace operator bound')
            for eps in (Q(1,4),Q(1),Q(4)):
                need(pf<=(1+eps)*ph+(1+1/eps)*coarse*norm,'restored objective Young bound')
                tests+=1
    need(Q(4)**2>Q(4),'unit norm false for nonprobability measure')
    need(Q(2)**2>Q(1)**2+Q(1)**2,'missing cross term is false')
    return {'double_trace_fibres':completions,'restoration_transfer_checks':tests,'analytic_negative_examples':2}


def validate(cert: dict,res: dict,inp: dict,expected=None) -> None:
    need(inp==g.INPUTS,'input contract')
    if expected is None:expected=g.build(inp)
    need((cert,res)==expected,'certificate or result mismatch')


def corruptions(cert: dict,res: dict,inp: dict,expected) -> int:
    mutations=[(0,lambda x:x['kernel']['census'].pop()),
               (0,lambda x:x['kernel']['delta_coefficients'].__setitem__(2,2099)),
               (0,lambda x:x['kernel'].update(uniform_L1_constant=1)),
               (0,lambda x:x['finite'].update(G2='1')),
               (0,lambda x:x['finite']['auxiliary_pairs'].append([5,5])),
               (0,lambda x:x['finite']['auxiliary_pairs'].pop()),
               (0,lambda x:x['finite']['coupled'].update(CRT_mean=x['finite']['independent_mean'])),
               (0,lambda x:x['finite']['coupled'].update(interval_sum='0')),
               (0,lambda x:x['finite'].update(deleted_collision_capacity='0')),
               (0,lambda x:x['finite'].update(tensor_error_bound='0')),
               (0,lambda x:x['exponents'].update(infimum_attained=True)),
               (0,lambda x:x['exponents'].update(same_total_budget_factor='1/4')),
               (0,lambda x:x['helper'].update(new_kappa=x['helper']['old_kappa'])),
               (0,lambda x:x['helper']['new_optimum'].update(minimum_upper='0')),
               (0,lambda x:x['stability'][0].update(weighted_error_multiplier='0')),
               (1,lambda x:x.update(actual_restored_trace_evaluated=True)),
               (1,lambda x:x.update(restoration_error_numerically_supplied=True)),
               (1,lambda x:x.update(helper_prime_contract_verified=True)),
               (1,lambda x:x.update(independently_verified=True)),
               (1,lambda x:x.update(new_prime_gap_bound=True)),
               (1,lambda x:x.update(cannot_imply=[])),
               (2,lambda x:x.update(rho='262499/1000000')),
               (2,lambda x:x['finite'].update(W=1))]
    for i,mutate in mutations:
        payload=copy.deepcopy([cert,res,inp]);mutate(payload[i])
        try:validate(*payload,expected=expected)
        except ValueError:pass
        else:raise ValueError('corrupt payload accepted')
    for z in ('0','-1',str(Q(1,2)-Q(inp['gamma']))):
        try:g.exponent_certificate(Q(inp['rho']),Q(inp['gamma']),[z])
        except ValueError:pass
        else:raise ValueError('illegal cutoff accepted')
    return len(mutations)+3


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument('--self-test',action='store_true');ap.add_argument('--check-hashes',action='store_true');ap.add_argument('--require-global',action='store_true')
    args=ap.parse_args()
    try:
        need(not args.require_global,'refused: no actual restored-trace positivity or global prime-gap certification')
        read=lambda n:json.loads((args.root/n).read_text())
        cert,res,inp=(read(n) for n in ('certificates.json','results.json','inputs.json'))
        expected=g.build(inp);validate(cert,res,inp,expected);report={'certificate_replay':True}
        if args.self_test:
            report.update(literal_kernels());report.update(capacities());report.update(direct_finite(cert['finite'],inp['finite']))
            report.update(helper_checks(cert,inp['finite'],Q(inp['rho'])));report.update(stability_checks())
            report['corruptions_rejected']=corruptions(cert,res,inp,expected)
        if args.check_hashes:
            hs=read('artifact-sha256.json');names={'README.md','proof.md','coupled_sieve.py','check_coupled.py','inputs.json',
                'certificates.json','results.json','source-lock.json','computation-record.json','computation-handoff.json','verification-ticket.md'}
            need(set(hs)==names,'manifest exact scope')
            for n,v in hs.items():need(hashlib.sha256((args.root/n).read_bytes()).hexdigest()==v,'hash mismatch '+n)
            report['hashes_verified']=len(hs)
        report.update(ok=True,independently_verified=False,new_prime_gap_bound=False)
        print(json.dumps(report,sort_keys=True));return 0
    except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as exc:
        print(json.dumps({'ok':False,'error':str(exc)}),file=sys.stderr);return 1


if __name__=='__main__':
    raise SystemExit(main())
