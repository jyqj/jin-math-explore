#!/usr/bin/env python3
"""Exact direct-marginal and spectral regression; not an isolated verifier."""
from __future__ import annotations
import argparse
import copy
from fractions import Fraction as Q
from itertools import combinations, product
from math import comb, prod
from pathlib import Path
import hashlib
import json
import sys
import spectral_gate as g


def need(ok, message):
    if not ok:
        raise ValueError(message)


def direct_forms(k, p, mass, values):
    points = list(product((0,1), repeat=k))
    weight = lambda x: prod((mass*p if b else mass*(1-p) for b in x), start=Q(1))
    I = sum((weight(x)*values[x]**2 for x in points), Q(0))
    forms = {}
    for r in (1,2):
        for erased in combinations(range(k), r):
            retained = [i for i in range(k) if i not in erased]
            totals = {}
            for x in points:
                key = tuple(x[i] for i in retained)
                totals[key] = totals.get(key,Q(0)) + weight(tuple(x[i] for i in erased))*values[x]
            forms[erased] = sum((weight(y)*v*v for y,v in totals.items()), Q(0))
    return I, forms


def independent_constant_check(inp, cert):
    rho = Q(2624989,10**7); I = Q(23685317890,10**24); J = Q(90248755123,10**24)
    zeta = Q(68225*2742997,2624989*98304)
    H5 = Q(137,60)
    loglower = sum((Q(2*9**(2*j+1), (2*j+1)*11**(2*j+1)) for j in range(7)),Q(0))
    need(loglower > H5 and Q(1,2)<zeta<Q(3,4), "mass witness")
    L = Q(194022333770747849,7800000000000000000000000000000000)
    U = Q(48810561568647,10000000000000000000000000000000)
    need(L == rho*(4*J-9*I)/1560 and U == rho*J-I and L>5*U>0, "independent fractions")
    c = cert["constants"]
    need(Q(c["cost_lower"])==L and Q(c["lossless_frozen_margin"])==U, "constant mismatch")
    need(Q(c["cost_to_margin_ratio"])==L/U, "ratio mismatch")
    need(Q(c["adaptive_penalty_lower_strict"])*zeta>rho, "adaptive penalty condition")
    need(c["unknown_true_margin_has_been_upper_bounded"] is False, "inequality-direction boundary")


def verify_payload(inp, cert, result):
    need(inp==g.INPUTS, "input contract")
    c,r=g.build(inp)
    need(cert==c and result==r, "frozen certificate replay")
    independent_constant_check(inp,cert)


def finite_tests():
    report={"integer_spectral_levels":0,"cube_models":0,"cube_points":0,
            "direct_marginal_forms":0,"mobius_energy_components":0,"soft_weight_checks":0,
            "supported_projection_fibres":0,"projection_pythagoras_checks":0}
    # These finite checks supplement, rather than prove, the universal integer factorization.
    for k in range(2,61):
        for ell in range(k):
            for s in range(k+1):
                need(s*(s-1)-2*ell*s+ell*(ell+1)==(s-ell)*(s-ell-1)>=0,"integer spectrum")
                report["integer_spectral_levels"]+=1
    for k in range(2,8):
        for p in (Q(1,2),Q(1,3)):
            for mass in (Q(2,3),Q(3,2)):
                points=list(product((0,1),repeat=k))
                fv=[Q(((j*j+3*j+2*k)%11)-5,7) for j in range(k+1)]
                values={x:fv[sum(x)] for x in points}
                I,forms=direct_forms(k,p,mass,values)
                J=sum((v for pair,v in forms.items() if len(pair)==1),Q(0))
                pairvals=[v for pair,v in forms.items() if len(pair)==2]
                need(len(set(pairvals))==1,"symmetric equality of pair energies")
                K=pairvals[0]
                fast=g.orbit_forms(k,p,mass,fv)
                need((I,J,K)==(fast["I"],fast["J_all"],fast["K_pair"]),"direct versus orbit")
                need(k*(k-1)*K>=4*mass*J-6*mass*mass*I,"direct spectral inequality")
                report["cube_models"]+=1;report["cube_points"]+=len(points)
                report["direct_marginal_forms"]+=len(forms)
                # Mobius path uses conditional averages, independent of the literal erasure loop.
                if k<=5:
                    norms,energies=g.projected_energies(k,p,values)
                    need(I==mass**k*sum(energies),"norm spectrum")
                    need(J==mass**(k+1)*sum(mask.bit_count()*e for mask,e in enumerate(energies)),"first spectrum")
                    need(sum(pairvals)==mass**(k+2)*sum(mask.bit_count()*(mask.bit_count()-1)*e for mask,e in enumerate(energies))/2,"second spectrum")
                    report["mobius_energy_components"]+=len(energies)
                rho=Q(2,7)
                for cap in (Q(0),mass/2,mass):
                    for theta in (Q(1,8),Q(1,2),Q(7,8)):
                        for penalty in (rho/mass,2*rho/mass,5*rho/mass):
                            w=1/(theta/penalty+(1-theta)*cap/rho)
                            need(w>=rho/mass and w*K>=rho*(4*J-6*mass*I)/(k*(k-1)),"soft lower bound")
                            report["soft_weight_checks"]+=1
    # Without symmetry only the average-pair conclusion is valid.
    k=4;p=Q(1,3);mass=Q(3,2)
    f={x:Q(2 if x[0] else -1) for x in product((0,1),repeat=k)}
    I,forms=direct_forms(k,p,mass,f);J=sum(v for key,v in forms.items() if len(key)==1)
    lower=(4*mass*J-6*mass**2*I)/12
    need(forms[(0,1)]==0<lower,"asymmetric counterexample absent")
    need(sum(v for key,v in forms.items() if len(key)==2)/6==lower,"averaged-pair equality")
    # Supported trace-null projection is the unique closest correction, including empty fibres.
    for n in range(0,7):
        for seed in range(1,7):
            weights=[Q(seed+j+1,seed+2*j+3) for j in range(n)]
            vals=[Q((-1)**j*(j+seed),j+seed+2) for j in range(n)]
            row=g.projection_certificate(weights,vals)
            if n:
                cap=sum(weights);A=sum(w*v for w,v in zip(weights,vals));flat=[v-A/cap for v in vals]
                need(row["distance_squared"]==A*A/cap,"projection cost")
                need(max(map(abs,flat))<=2*max(map(abs,vals)),"boundedness")
                for shift in (Q(-2,3),Q(0),Q(5,7)):
                    e=[shift*Q(j+1) for j in range(n)]
                    average=sum(w*x for w,x in zip(weights,e))/cap;e=[x-average for x in e]
                    competitor=[a+b for a,b in zip(flat,e)]
                    distance=sum(w*(v-z)**2 for w,v,z in zip(weights,vals,competitor))
                    need(distance-A*A/cap==sum(w*x*x for w,x in zip(weights,e)),"Pythagoras")
                    report["projection_pythagoras_checks"]+=1
            report["supported_projection_fibres"]+=1
    need(Q(1,2)*1+Q(1,2)*(-1)==0 and Q(1,2)*1!=0,"deletion must reintroduce trace")
    # A larger hypothetical true J margin can escape; J_minus is NOT an upper bound.
    rho=Q(g.INPUTS["rho"]);r=Q(4)
    need(rho*r-1 > rho*(4*r-9)/1560,"future stronger margin boundary")
    # Common normalization scales both margins and all norms by exactly the same factor.
    c=g.margin_certificate(g.INPUTS);L=c["cost_lower"];U=c["lossless_frozen_margin"]
    for scale in (Q(1,17),Q(1),Q(13,7)):
        need((L/scale)/(U/scale)==L/U,"common normalization")
    report.update(asymmetry_counterexamples=1,deletion_noncommutation_counterexamples=1,
                  future_margin_escape_examples=1,common_normalization_checks=3)
    return report


def negative_tests(inp,cert,res):
    cases=[]
    def add(which,change):
        data=[copy.deepcopy(inp),copy.deepcopy(cert),copy.deepcopy(res)];change(data[which]);cases.append(data)
    add(0,lambda x:x.update(k=39))
    add(0,lambda x:x.update(rho="262499/1000000"))
    add(0,lambda x:x.update(mass_upper="1"))
    add(0,lambda x:x.update(cap_cells=68226))
    add(0,lambda x:x.update(input_brackets_independently_verified=True))
    add(1,lambda x:x["constants"].update(cost_lower="0"))
    add(1,lambda x:x["constants"].update(lossless_frozen_margin="1"))
    add(1,lambda x:x["constants"].update(unknown_true_margin_has_been_upper_bounded=True))
    add(1,lambda x:x["constants"].update(adaptive_penalty_lower_strict="0"))
    add(1,lambda x:x["constants"].update(cost_to_margin_ratio="10"))
    add(1,lambda x:x["spectrum40"].pop())
    add(1,lambda x:x["spectrum40"][2].__setitem__(1,1))
    add(1,lambda x:x["asymmetry_counterexample"].update(chosen_K_over_I="1"))
    add(1,lambda x:x["supported_projection_example"].update(distance_squared="0"))
    add(1,lambda x:x["zero_fibre"].update(trace="1"))
    add(1,lambda x:x["deletion_noncommutation"].update(trace_after_keep_first="0"))
    add(2,lambda x:x.update(independently_verified=True))
    add(2,lambda x:x.update(new_prime_gap_bound=True))
    add(2,lambda x:x.update(actual_true_margin_upper_bound=True))
    add(2,lambda x:x.update(cannot_imply=[]))
    for j,args in enumerate(cases):
        try:verify_payload(*args)
        except (ValueError,KeyError,TypeError):pass
        else:raise ValueError(f"corruption {j} accepted")
    for args in (([Q(0)],[Q(1)]),([Q(-1)],[Q(1)]),([Q(1)],[])):
        try:g.projection_certificate(*args)
        except ValueError:pass
        else:raise ValueError("invalid fibre accepted")
    # Missing the penalty or capacity hypothesis really makes the lower bound fail.
    rho=Q(1,4);T=Q(1);theta=Q(1,2)
    need(1/(theta/(rho/10)+(1-theta)*T/rho)<rho/T,"small penalty countermodel")
    need(1/(theta/rho+(1-theta)*(2*T)/rho)<rho/T,"oversized capacity countermodel")
    return {"corruptions_rejected":len(cases),"invalid_fibres_rejected":3,"hypothesis_countermodels":2}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parent)
    ap.add_argument("--self-test",action="store_true");ap.add_argument("--check-hashes",action="store_true")
    ap.add_argument("--require-global",action="store_true")
    args=ap.parse_args()
    try:
        if args.require_global:raise ValueError("refused: this conditional certificate does not prove a prime-gap theorem")
        load=lambda fn:json.loads((args.root/fn).read_text(encoding="utf-8"))
        inp,cert,res=(load(f) for f in ("inputs.json","certificates.json","results.json"))
        verify_payload(inp,cert,res);report={"certificate_replay":True}
        if args.self_test:report.update(finite_tests());report.update(negative_tests(inp,cert,res))
        if args.check_hashes:
            manifest=load("artifact-sha256.json")
            names={"README.md","proof.md","spectral_gate.py","check_spectral_gate.py","inputs.json",
                   "certificates.json","results.json","source-lock.json","computation-record.json",
                   "computation-handoff.json","verification-ticket.md"}
            need(set(manifest)==names,"manifest scope")
            for fn,sha in manifest.items():need(hashlib.sha256((args.root/fn).read_bytes()).hexdigest()==sha,"hash "+fn)
            report["hashes_verified"]=len(manifest)
        report.update(ok=True,conditional_source_brackets=True,independently_verified=False,new_prime_gap_bound=False)
        print(json.dumps(report,sort_keys=True));return 0
    except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as ex:
        print(json.dumps({"ok":False,"error":str(ex)}),file=sys.stderr);return 1


if __name__=="__main__":
    raise SystemExit(main())
