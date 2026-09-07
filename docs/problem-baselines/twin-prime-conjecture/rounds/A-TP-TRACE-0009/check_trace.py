#!/usr/bin/env python3
"""Stdlib-only exact certificate replay and distinct symbolic-integration tests."""
from __future__ import annotations
import argparse
import copy
from fractions import Fraction as Q
from itertools import product
from math import factorial as fac, comb, prod
from pathlib import Path
import hashlib
import json
import sys
import trace_forms as tf

NAMES = {'README.md','proof.md','trace_forms.py','check_trace.py','inputs.json',
         'certificates.json','results.json','source-lock.json','computation-record.json',
         'computation-handoff.json','verification-ticket.md'}


def verify_case(c: dict, M: dict) -> dict:
    d=c['degree']; n=len(tf.basis(d)); cols=tf.null_columns(d)
    tf.require(set(c)=={'degree','dimension','trace_rank','nullity','matrix_sha256','bounds'},'case fields')
    tf.require((c['dimension'],c['trace_rank'],c['nullity'])==(n,d+1,n-d-1),'trace dimensions')
    tf.require(c['matrix_sha256']==tf.digest(M),'matrix digest mismatch')
    tf.require(all(sum(row[i]*q for i,q in col.items())==0 for row in tf.trace_map(d) for col in cols),'kernel columns')
    tf.require(all(q==0 for row in tf.restrict(M['K'],cols) for q in row),'kernel matrix identity')
    tf.require(set(c['bounds'])==({'ordinary','penalized','trace_null'} if d else {'ordinary','penalized'}),'objective coverage')
    row={'degree':d,'dimension':n,'trace_rank':d+1,'nullity':n-d-1}
    for name,b in c['bounds'].items():
        tf.require(set(b)=={'lower','upper','vector','pivot_sha256','positive_pivots'},'bound fields')
        I=tf.restrict(M['I'],cols) if name=='trace_null' else M['I']
        B=tf.restrict(M['J'],cols) if name=='trace_null' else M['J' if name=='ordinary' else 'B']
        v=b['vector']; lo,hi=Q(b['lower']),Q(b['upper'])
        tf.require(len(v)==len(I) and all(type(x) is int for x in v) and any(v),'invalid witness')
        tf.require(0<=lo<hi<4 and hi-lo<=Q(1,10**6),'bound interval')
        den=tf.quadratic(I,v)
        tf.require(den>0 and tf.quadratic(B,v)>=lo*den,'lower witness fails')
        piv=tf.ldl_positive(tf.upper_matrix(I,B,hi))
        tf.require(b['positive_pivots']==len(piv) and b['pivot_sha256']==tf.digest(piv),'upper pivot commitment')
        if name=='trace_null':
            lifted=tf.lift(list(map(Q,v)),cols,n)
            tf.require(all(sum(x*y for x,y in zip(r,lifted))==0 for r in tf.trace_map(d)),'trace witness')
            tf.require(tf.quadratic(M['K'],lifted)==0,'null energy')
        row[name]=[str(lo),str(hi)]
    return row


def payload_check(inp: dict, cert: dict, result: dict) -> dict:
    expected={'schema':'twin-trace-inputs/v1','attempt':'A-TP-TRACE-0009','k':40,'degrees':list(range(7)),
              'basis':'s^a t^b u^c v^e; a+b+c+e=d; u=sum(y_1,...,y_38); v=1-s-t-u',
              'domain':'s,t,y_i>=0; s+t+sum(y_i)<=1','matrix_scale':'40!',
              'rho_comparison':'1/4','endpoint_pair':[0,186],'actual_186_trial_imported':False,
              'arithmetic_bridge':'conditional on the same-weight trace match and the stated single-prime asymptotic'}
    tf.require(inp==expected,'input contract mismatch')
    tf.require(set(cert)=={'schema','k','max_degree','cases'} and cert['schema']=='twin-trace-certificates/v1','certificate schema')
    tf.require(cert['k']==40 and cert['max_degree']==6 and len(cert['cases'])==7,'degree coverage')
    rows=[]; pivots=0
    for d,c in enumerate(cert['cases']):
        tf.require(type(c['degree']) is int and c['degree']==d,'degree identity')
        M=tf.matrices(40,d)
        rows.append(verify_case(c,M))
        pivots += sum(b['positive_pivots'] for b in c['bounds'].values())
    expected_result={'schema':'twin-trace-results/v1','status':'solver_candidate','rows':rows,
        'basis_family':'polynomials in two endpoints and the sum of38 interior coordinates; degree<=6',
        'classical_endpoint_rho':'1/4','penalized_score_upper':str(Q(rows[-1]['penalized'][1])/4),
        'ordinary_score_upper':str(Q(rows[-1]['ordinary'][1])/4),
        'trace_null_score_upper':str(Q(rows[-1]['trace_null'][1])/4),
        'finite_family_positive_detector':False,'actual_186_trial_evaluated':False,
        'new_prime_gap_bound':False,'independently_verified':False,
        'cannot_imply':['all40-variable functions fail','enlarged186-support failure','a new prime-gap bound','the twin-prime conjecture']}
    tf.require(result==expected_result,'result or evidence-boundary mismatch')
    return {'degrees':7,'certified_objectives':20,'exact_positive_pivots':pivots,
            'terminal_dimension':84,'terminal_trace_rank':7,'terminal_nullity':77}


# Separate full-coordinate polynomial integration; no use of tf.entry formulas.
def add(p: dict, q: dict) -> dict:
    z=p.copy()
    for e,c in q.items():
        z[e]=z.get(e,Q(0))+c
    return {e:c for e,c in z.items() if c}


def mul(p: dict, q: dict) -> dict:
    z={}
    for e,c in p.items():
        for f,d in q.items():
            h=tuple(a+b for a,b in zip(e,f)); z[h]=z.get(h,Q(0))+c*d
    return {e:c for e,c in z.items() if c}


def power(p: dict, n: int, dim: int) -> dict:
    z={(0,)*dim:Q(1)}
    for _ in range(n):
        z=mul(z,p)
    return z


def linear(dim: int, indices: list[int], constant: int=0, sign: int=1) -> dict:
    z={(0,)*dim:Q(constant)} if constant else {}
    for i in indices:
        e=[0]*dim; e[i]=1; z[tuple(e)]=Q(sign)
    return z


def polynomial(k: int, exps: tuple) -> dict:
    a,b,c,e=exps
    z={(0,)*k:Q(1)}
    for p,n in [(linear(k,[0]),a),(linear(k,[1]),b),(linear(k,list(range(2,k))),c),
                (linear(k,list(range(k)),1,-1),e)]:
        z=mul(z,power(p,n,k))
    return z


def marginal(p: dict, index: int) -> dict:
    if not p:
        return {}
    dim=len(next(iter(p)))-1; L=linear(dim,list(range(dim)),1,-1)
    z={}; powers={}
    for exp,coeff in p.items():
        r=exp[index]; rest=exp[:index]+exp[index+1:]
        if r+1 not in powers:
            powers[r+1]=power(L,r+1,dim)
        z=add(z,mul({rest:coeff/Q(r+1)},powers[r+1]))
    return z


def integral(p: dict) -> Q:
    return sum((c*Q(prod(fac(a) for a in e),fac(sum(e)+len(e))) for e,c in p.items()),Q(0))


def divide_L(p: dict) -> dict:
    dim=len(next(iter(p))); L=linear(dim,list(range(dim)),1,-1)
    lead=max(L); z={}; rem=p.copy()
    while rem:
        exp=max(rem)
        tf.require(all(a>=b for a,b in zip(exp,lead)),'nondivisible trace polynomial')
        t=tuple(a-b for a,b in zip(exp,lead)); c=rem[exp]/L[lead]
        z=add(z,{t:c}); rem=add(rem,{e:-q for e,q in mul({t:c},L).items()})
    return z


def oracle() -> int:
    checks=0
    for k,d in [(4,0),(4,1),(4,2),(4,3),(5,1),(5,2),(6,2)]:
        bs=tf.basis(d); polys=[polynomial(k,x) for x in bs]
        marg=[[marginal(p,i) for p in polys] for i in range(3)]
        traces=[marginal(marginal(p,0),0) for p in polys]
        div=[divide_L(p) for p in traces]
        for i,x in enumerate(bs):
            for j in range(i+1):
                actual=(integral(mul(polys[i],polys[j])),
                        *(integral(mul(mm[i],mm[j])) for mm in marg),integral(mul(traces[i],div[j])))
                tf.require(tuple(fac(k)*q for q in actual)==tf.entry(k,x,bs[j]),'symbolic integration mismatch')
                checks+=5
    for k in (4,5,10,40,80):
        I,Js,Jt,Ji,K=tf.entry(k,(0,0,0,0),(0,0,0,0))
        tf.require((I,Js,Jt,Ji,K)==(1,Q(2,k+1),Q(2,k+1),Q(2,k+1),Q(3,2*(k+1))),'constant boundary')
        checks+=5
    return checks


def finite_tests() -> dict:
    fibre=0
    for q in product((1,2,3),repeat=3):
        widths=[Q(1,2),Q(1,3),Q(1,6)]; g=[Q(2),Q(-1),Q(3)]
        h=sum(w/Q(a) for w,a in zip(widths,q)); A=sum(w*t for w,t in zip(widths,g))
        E=sum(w*a*t*t for w,a,t in zip(widths,q,g))
        rem=sum(w*a*(t-A/(a*h))**2 for w,a,t in zip(widths,q,g))
        tf.require(E-A*A/h==rem and rem>=0,'weighted projection')
        fibre+=1
    kappas=[]
    for M in (1,2,4,8,16,64,256):
        f=lambda r:sum((Q((-1)**j*comb(r,j),M*j+1) for j in range(r+1)),Q(0))
        kap=f(4)/f(2)**2
        tf.require(kap>=1 and (not kappas or kap<kappas[-1]),'recovery energy')
        kappas.append(kap)
    eps=Q(1,50000); p=(1+eps)/40
    weights=[eps]+[p-eps]*2+[p]*38
    tf.require(sum(weights)==1 and min(weights)>=0,'Boolean bad-law normalization')
    states=[(0,39),(0,),(39,)]+[(i,) for i in range(1,39)]
    tf.require(all(sum(w for w,S in zip(weights,states) if i in S)==p for i in range(40)),'equal one-point moments')
    tf.require(all(len(S)-1-int(0 in S and 39 in S)==0 for S in states),'bad-law endpoint score')
    tf.require(40*p-1-eps==0 and p-eps>=0,'first moment obstruction')
    tf.require((1+Q(1,39))/40-Q(1,39)==0,'sharp endpoint threshold')
    # All primality below208; only exact integer divisibility is used.
    prime=lambda n:n>=2 and all(n%a for a in range(2,n) if a*a<=n)
    ds=list(product((1,2,3),repeat=4)); H=(0,2,6,8)
    lam={d:prod(-1 if v>1 else 1 for v in d)*(1+sum((i+1)*(v>1) for i,v in enumerate(d))) for d in ds}
    alt={d:c if d[0]==d[-1]==1 else c+2 for d,c in lam.items()}
    S=lambda n,L:sum(c for d,c in L.items() if all((n+h)%v==0 for h,v in zip(H,d)))
    C=U=0; matched=0
    for n in range(11,200):
        a,b=prime(n),prime(n+8); old,new=S(n,lam),S(n,alt)
        if a and b:
            tf.require(old==new,'finite trace identity'); matched+=1
        C+=a*b*old*old; U+=a*new*new
    tf.require(0<C<U and matched>0,'nonvacuous trace upper direction')
    first=next(n for n in range(11,200) if prime(n) and prime(n+8))
    bad=alt.copy(); bad[(1,1,1,1)]+=1
    tf.require(S(first,bad)!=S(first,lam),'changed-trace counterexample')
    # When a prime endpoint itself is an allowed divisor, trace equality is insufficient.
    old=sum(c for ds_,c in { (2,1):1 }.items() if all(v%q==0 for v,q in zip((2,5),ds_)))
    tf.require(prime(2) and prime(5) and old==1,'cutoff counterexample')
    return {'weighted_fibre_cases':fibre,'recovery_shapes':len(kappas),'last_recovery_energy':str(kappas[-1]),
            'bad_first_moment_law_states':41,'finite_trace_integers':189,'prime_pair_equalities':matched,
            'finite_pair_sum':C,'finite_replacement_upper':U}


def negative_tests(cert: dict) -> int:
    c=cert['cases'][1]; M=tf.matrices(40,1); mutations=[]
    def bad(fn):
        z=copy.deepcopy(c); fn(z); mutations.append(z)
    bad(lambda z:z.update(matrix_sha256='0'*64))
    bad(lambda z:z.update(dimension=5))
    bad(lambda z:z.update(trace_rank=1))
    bad(lambda z:z.update(nullity=3))
    bad(lambda z:z['bounds'].pop('trace_null'))
    bad(lambda z:z['bounds']['penalized']['vector'].pop())
    bad(lambda z:z['bounds']['penalized'].update(vector=[0]*4))
    bad(lambda z:z['bounds']['penalized'].update(vector=[True]*4))
    bad(lambda z:z['bounds']['penalized'].update(lower='3'))
    bad(lambda z:z['bounds']['penalized'].update(upper='2'))
    bad(lambda z:z['bounds']['penalized'].update(pivot_sha256='f'*64))
    bad(lambda z:z['bounds']['penalized'].update(positive_pivots=3))
    bad(lambda z:z['bounds']['trace_null']['vector'].append(1))
    bad(lambda z:z['bounds']['trace_null'].update(lower='2'))
    for i,z in enumerate(mutations):
        try:
            verify_case(z,M)
        except (ValueError,KeyError,TypeError):
            continue
        raise ValueError(f'corruption accepted: {i}')
    # An invalid upper must fail the algebraic criterion, not merely a cached hash.
    try:
        tf.ldl_positive([[Q(1),Q(2)],[Q(2),Q(1)]])
    except ValueError:
        return len(mutations)+1
    raise ValueError('indefinite matrix accepted')


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--progress',action='store_true',help='emit deterministic stage markers to stderr')
    ap.add_argument('--check-hashes',action='store_true')
    ap.add_argument('--require-global',action='store_true')
    args=ap.parse_args()
    try:
        tf.require(not args.require_global,'refused: no actual186 trial, new prime-gap bound or global proof is certified')
        read=lambda name:json.loads((args.root/name).read_text(encoding='utf-8'))
        inp,cert,result=(read(n) for n in ('inputs.json','certificates.json','results.json'))
        if args.progress: print('stage: exact_certificates',file=sys.stderr,flush=True)
        report=payload_check(inp,cert,result)
        if args.progress: print('stage: exact_certificates_complete',file=sys.stderr,flush=True)
        if args.self_test:
            if args.progress: print('stage: symbolic_oracle',file=sys.stderr,flush=True)
            report['symbolic_entry_comparisons']=oracle()
            if args.progress: print('stage: symbolic_oracle_complete',file=sys.stderr,flush=True)
            report.update(finite_tests())
            report['corruptions_rejected']=negative_tests(cert)
        if args.check_hashes:
            manifest=read('artifact-sha256.json')
            tf.require(set(manifest)==NAMES,'manifest exact scope')
            for name,h in manifest.items():
                tf.require(hashlib.sha256((args.root/name).read_bytes()).hexdigest()==h,'hash mismatch: '+name)
            report['hashes_checked']=len(manifest)
        report.update(ok=True,evidence='exact_check',independently_verified=False,new_prime_gap_bound=False)
        print(json.dumps(report,sort_keys=True)); return 0
    except (ValueError,KeyError,TypeError,OSError,ZeroDivisionError) as exc:
        print(json.dumps({'ok':False,'error':str(exc)}),file=sys.stderr); return 1


if __name__=='__main__':
    sys.exit(main())
