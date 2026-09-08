#!/usr/bin/env python3
"""Reproduce bounded checks for A-RH-PROFILE-0019; no independent verification."""
from __future__ import annotations
import argparse
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import platform
import mpmath as mp
import numpy as np
import sympy as sp
from profile_tools import (Profile, cosine_profile, mixture, test_weight, functional,
                           profile_matrix, atomic_list, pair_moment, alias_bound,
                           normalization_bound)

SEED = 2026090819


def exact_checks() -> dict:
    count = 0
    for q in range(1, 49):
        for kind in range(3):
            w = [1+min(i, q-1-i)**kind for i in range(q)]
            for d in range((q+1)//2, q+1):
                h = q-d
                for k in range(q):
                    if k == 0:
                        lhs = sum(x*x for x in w[:d])-sum(x*x for x in w[:h])
                        rhs = sum(w[i]**2 for i in range(h, d))
                    else:
                        lhs = 2*(sum(w[i]*w[i+k] for i in range(max(0,d-k)))
                                 -sum(w[i]*w[i+k] for i in range(max(0,h-k))))
                        rhs = sum(w[i]*w[j] for i in range(h, d)
                                  for j in (i-k, i+k) if 0 <= j < q)
                    assert lhs == rhs
                    count += 1
    x, y, th, a = sp.symbols('x y th a', real=True)
    half = sp.Rational(1,2)
    def integ(p):
        return sp.integrate(p, (x,-half,half))
    def K(p):
        py = p.subs(x,y)
        return sp.expand(sp.integrate((x-y)*py,(y,-half,x))
                         +sp.integrate((y-x)*py,(y,x,half)))
    zero_mean = 0
    for k in range(1, 11):
        g = x**k-integ(x**k)
        G = sp.integrate(g.subs(x,y),(y,-half,x))
        assert sp.simplify(integ(g*K(g))+2*integ(G*G)) == 0
        zero_mean += 1
    polynomial_cases = 0
    for j in range(4):
        c = (sp.Rational(1,4)-x*x)**j
        p = 1+a*(sp.Rational(1,12)-x*x)
        f = sp.expand(c*p)
        norm = integ(c*c)
        bform = sp.expand(integ(f*f)/th+th*integ(f*K(f)))
        for aval in range(7):
            for theta in (sp.Rational(9,10),sp.Rational(19,20),sp.Integer(1)):
                value = bform.subs({a:aval,th:theta})
                upper = (1/theta+theta/2)*sp.Rational(64,25)*norm
                assert value <= upper
                polynomial_cases += 1
    coeffs = [F(1), F(0), F(-1)]
    multipliers = 0
    for i in range(3):
        for j in range(3):
            b = coeffs[i]+coeffs[j]+int(i==j==1)
            assert b*b <= 4
            multipliers += 1
    rational = {
        'near_endpoint_coefficient': str(F(64,25)*(F(10,9)+F(9,20))),
        'margin_below_four': str(4-F(64,25)*(F(10,9)+F(9,20))),
        'endpoint_coefficient': str(F(3,2)*F(64,25)),
        'cosine_sup_margin_using_pi_lt_22_over_7': str(F(8,5)-F(11,7)),
        'nonreflection_lhs': str(F(5,6)**2-F(1,2)**2),
        'nonreflection_rhs': str(F(1,3)),
        'nonreflection_error': str(F(5,6)**2-F(1,2)**2-F(1,3))}
    assert F(rational['near_endpoint_coefficient']) == F(4496,1125)
    assert F(rational['margin_below_four']) == F(4,1125) > 0
    assert F(rational['endpoint_coefficient']) < 4
    assert F(rational['cosine_sup_margin_using_pi_lt_22_over_7']) > 0
    assert F(rational['nonreflection_error']) == F(1,9) > 0
    return {'reflection_coefficients':count,'zero_mean_polynomial_identities':zero_mean,
            'polynomial_norm_bounds':polynomial_cases,'block_multipliers':multipliers,
            'rational_comparisons':5,'rational_values':rational}


def run(samples: int) -> dict:
    rng = np.random.default_rng(SEED)
    max_res, min_slack, counts = {}, {}, {}
    def tick(name, number=1):
        counts[name] = counts.get(name,0)+number
    def close(name, left, right):
        left, right = np.asarray(left), np.asarray(right)
        err = float(np.max(abs(left-right)))
        scale = 1+float(np.max(abs(left)))+float(np.max(abs(right)))
        max_res[name] = max(max_res.get(name,0.0),err)
        max_res[name+'_relative'] = max(max_res.get(name+'_relative',0.0),err/scale)
        if err > 3e-9*scale:
            raise AssertionError((name,err,scale))
    def bound(name, left, right):
        left,right = float(left),float(right)
        slack = right-left
        min_slack[name] = min(min_slack.get(name,math.inf),slack)
        if slack < -3e-9*(1+abs(left)+abs(right)):
            raise AssertionError((name,left,right))
    def make_profile():
        return mixture([cosine_profile(float(rng.uniform(0.12,np.pi))) for _ in range(3)],
                       rng.uniform(0.1,1,3).tolist())
    cases = []
    for _ in range(samples):
        q = int(rng.choice([3,4,8,12,16,24,32]))
        k = int(rng.integers(1,13))
        t = np.sort(rng.uniform(-3,3,k))
        m = rng.choice([1,1,2,3,4,6],k)
        a = np.where(m%2 == 0,rng.uniform(0,4,k),0)
        cases.append((q,t,m,a,make_profile()))
    flat = cosine_profile(0)
    opt = cosine_profile(math.sqrt(2))
    cases += [(1,np.array([0]),np.array([1]),np.array([0]),flat),
              (1,np.array([0]),np.array([8]),np.array([5]),opt),
              (8,np.arange(8),np.ones(8,int),np.zeros(8),flat),
              (8,np.arange(8),np.ones(8,int),np.zeros(8),opt),
              (4,np.array([0,1e-5,0.4]),np.array([1,1,4]),np.array([0,0,6]),opt),
              (4,np.arange(4),np.full(4,2),np.full(4,4),opt)]
    for q,t,m,a,p in cases:
        T,S,H,Z,n = profile_matrix(q,t,m,a,p)
        N = int(sum(m)); u = (np.arange(q)-(q-1)/2)/q
        D = float(n+np.linalg.norm(T,'fro')**2-2*N)
        bound('signed_defect',0,D)
        close('trace_mass',np.trace(T),N)
        close('profile_diagonal',np.diag(T),N*p.value(u)/(q*Z))
        close('reflection_symmetry',T[::-1,::-1],T.conj())
        for d in range((q+1)//2,q+1):
            h = q-d
            left = np.linalg.norm(T[:d,:d],'fro')**2-np.linalg.norm(T[:h,:h],'fro')**2
            right = float(np.real(np.trace((T@T)[h:d,h:d])))
            close('central_rows',left,right); tick('central_row_checks')
        tests = [test_weight(1,0,0),test_weight(1,0.7,1),test_weight(2,-0.5,0.5)]
        for c in tests:
            vals = c.value(u); C = np.diag(vals)
            lhs = float(np.trace(C@(T@T-2*T+S)).real)
            rhs = math.sqrt((4*np.dot(vals,vals)+2*n*max(abs(vals))**2)*max(D,0))
            bound('weighted_row',-rhs,lhs); tick('diagonal_weight_checks')
            z, mass = atomic_list(t,m,a)
            row_energy = float(np.trace(C@T@T).real/N)
            raw = pair_moment(c.multiply(p),p,z,mass,q)/(Z*Z)
            close('weighted_kernel_dictionary',raw,row_energy)
        # General positive matrix C, not just a coordinate/diagonal test.
        X = rng.normal(size=(q,3))+1j*rng.normal(size=(q,3))
        C = X@X.conj().T; C /= np.linalg.norm(C,2)
        lhs = float(np.trace(C@(T@T-2*T+S)).real)
        rhs = math.sqrt((4*np.linalg.norm(C,'fro')**2+2*n*np.linalg.norm(C,2)**2)*max(D,0))
        bound('positive_matrix_row',-rhs,lhs); tick('positive_matrix_checks')
        close('unweighted_kernel_dictionary',pair_moment(p,p,z,mass,q)/(Z*Z),
              np.linalg.norm(T,'fro')**2/N)
    alias_ratios = []
    for i in range(samples):
        q = int(rng.choice([16,24,32,48,64]))
        p = make_profile(); c = test_weight(1.25,0.5,1)
        f = c.multiply(p)
        k = int(rng.integers(1,7)); t = rng.uniform(-0.2*q,0.2*q,k)
        m = rng.choice([1,2,4],k)
        a = np.where(m==1,0,rng.uniform(0,2,k))
        z,mass = atomic_list(t,m,a)
        for g in (p,flat):
            raw = pair_moment(f,g,z,mass,q)
            cont = pair_moment(f,g,z,mass)
            upper = alias_bound(f,g,z,mass,q,0.8)
            error = abs(raw-cont)
            bound('profile_alias',error,upper)
            alias_ratios.append(float(error/upper)); tick('alias_pair_checks')
        sample_norm = float(np.mean(p.value((np.arange(q)-(q-1)/2)/q)))
        bound('normalizer_error',abs(sample_norm-p.integral()),normalization_bound(p,q,0.8))
        tick('normalizer_checks')
        if i < 12:
            # Alternate smooth 2D integral, not a separate verifier context.
            v,w = np.polynomial.legendre.leggauss(128); v,w=v/2,w/2
            diff = v[:,None]-v[None,:]
            B = sum(massj*np.exp(2j*np.pi*x*diff)*np.cosh(dep*diff)
                    for x,massj,dep in zip(t,m,a))
            integral = np.sum((w*f.value(v))[:,None]*(w*p.value(v))[None,:]*abs(B)**2)/sum(m)
            close('continuous_integral',integral,pair_moment(f,p,z,mass))
            tick('alternative_integrals')
        # Scalar shifted-kernel primitive, including complex differences.
        lam,mu = rng.uniform(-1.5,1.5,2)
        zz = complex(rng.uniform(-0.45*q,0.45*q),rng.uniform(-2,2))
        Dq = lambda zz: flat.sampled_transform(zz,q)
        error = abs(Dq(zz+lam)*Dq(zz+mu)-np.sinc(zz+lam)*np.sinc(zz+mu))
        R = max(abs(lam),abs(mu)); theta=0.8; cc=np.sinc(theta)
        upper = (np.pi**2*math.cosh(np.pi*abs(zz.imag)/q)*(1+2*R)
                 *math.exp(2*np.pi*abs(zz.imag))/(3*cc*cc*q*q))
        bound('shifted_product',error,upper); tick('shifted_product_checks')
    mp.mp.dps = 80
    lam1 = mp.mpf('0.5')+mp.cot(1/mp.sqrt(2))/mp.sqrt(2)
    sigma0 = 2-lam1
    lambda_float = float(lam1)
    theta_values = (0.9,0.95,0.99,1.0)
    no_go_positive_tests = 0
    for _ in range(samples):
        p = make_profile()
        for theta in theta_values:
            ct = test_weight(float(rng.uniform(0,3)),float(rng.uniform(-1,1)),1)
            cp = ct.multiply(p)
            optimum = cosine_profile(math.sqrt(2)*theta)
            lam = theta/2+1/math.sqrt(2)/math.tan(theta/math.sqrt(2))
            energies = functional(p,p,theta)
            d = max(0,energies-lambda_float)
            lhs = functional(cp,p,theta); t = cp.integral()
            n2 = ct.multiply(ct).integral()
            rhs = lambda_float*t-2*math.sqrt(max(0,n2*d))
            bound('strong_scalar_no_go',rhs,lhs)
            no_go_positive_tests += int(rhs > 0)
            tick('no_go_constraints')
            g_terms = Profile(p.terms+tuple((x,-aa) for x,aa in optimum.terms))
            gap = functional(g_terms,g_terms,theta)
            close('variational_identity',energies-lam,gap)
            grid = np.linspace(-0.5,0.5,65)
            close('stationarity',optimum.value(grid)/theta+theta*optimum.potential(grid),
                  np.full(65,lam))
            bound('quadratic_Cauchy_bound',functional(cp,cp,theta),
                  (1/theta+theta/2)*(64/25)*n2)
    stationarity_weights = []
    for f in (test_weight(1,0),test_weight(1,1),test_weight(2,-1)):
        t = f.multiply(opt).integral()
        value = functional(f.multiply(opt),opt,1)
        close('optimal_profile_cancellation',value,lambda_float*t)
        stationarity_weights.append({'weight':f.terms,'mass':t,'value':value,
                                     'predicted':lambda_float*t})
    guards = []
    for q in (4,8,16,32):
        z=np.array([0+0j,q+0j]); mass=np.ones(2)
        ds=pair_moment(flat,flat,z,mass,q); dc=pair_moment(flat,flat,z,mass)
        close('alias_guard_sampled',ds,2); close('alias_guard_continuous',dc,1)
        try:
            alias_bound(flat,flat,z,mass,q,0.9)
        except ValueError:
            tick('invalid_margin_rejections')
        else:
            raise AssertionError('missing margin was accepted')
        guards.append({'q':q,'discrepancy':float((ds-dc).real)})
    # Exact rank-one non-reflection obstruction evaluated separately in rationals.
    pvec=np.array([0.5,1/3,1/6]); T=np.sqrt(pvec[:,None]*pvec[None,:])
    close('nonreflection_guard',np.linalg.norm(T[:2,:2])**2-T[0,0]**2-(T@T)[1,1],1/9)
    rates=[]
    for theta in (0.9,0.99):
        for logT in (10,20,40,80):
            rates.append({'theta':theta,'log_T':logT,
                          'rate_without_fixed_constant':math.exp((theta-1)*logT)/logT})
    ex=exact_checks()
    return {'ok':True,'attempt':'A-RH-PROFILE-0019','seed':SEED,'random_samples':samples,
            'mixed_model_count':len(cases),'boundary_cases':6,'counts':counts,
            'exact_checks':ex,'exact_case_total':sum(v for v in ex.values() if isinstance(v,int)),
            'maximum_residuals':max_res,'minimum_slacks':min_slack,
            'maximum_alias_to_bound_ratio':max(alias_ratios),'positive_no_go_lower_tests':no_go_positive_tests,
            'optimal_profile_cancellation':stationarity_weights,'alias_guards':guards,
            'source_rate_scalars_only':rates,
            'benchmark':{'C_MT':mp.nstr(lam1,65),'simple_fraction':mp.nstr(sigma0,65),
                         'status':'recovered known constant; not a new record'},
            'backend':{'python':platform.python_version(),'numpy':np.__version__,
                       'mpmath':mp.__version__,'sympy':sp.__version__},
            'independent_verification':False,'actual_zeta_zero_computation':False,
            'mathematical_truth_verified':False,
            'scope':'Exact finite checks and numerical regressions; universal statements remain proof candidates.'}


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--samples',type=int,default=120)
    ap.add_argument('--output',type=Path,default=Path('validation.json'))
    ap.add_argument('--check-package',action='store_true')
    args=ap.parse_args()
    if args.check_package:
        root=Path(__file__).resolve().parent
        data=json.loads((root/'checkpoint.json').read_text())
        for name,digest in data['sha256'].items():
            path=root/name
            if path.parent!=root or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
                raise ValueError('hash mismatch: '+name)
        claims=json.loads((root/'claims.json').read_text())['claims']
        assert all(c['evidence_grade']=='proof_candidate' and c['cannot_imply'] for c in claims)
        assert len({c['id'] for c in claims})==len(claims)
        print(json.dumps({'ok':True,'hashes':len(data['sha256']),'claims':len(claims),
                          'scope':'integrity, not mathematical verification'}))
        return 0
    if not 1<=args.samples<=1000:
        ap.error('samples must be between 1 and 1000')
    result=run(args.samples)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'samples':args.samples,'models':result['mixed_model_count'],
                      'counts':result['counts'],'exact_cases':result['exact_case_total'],
                      'output':str(args.output)},sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
