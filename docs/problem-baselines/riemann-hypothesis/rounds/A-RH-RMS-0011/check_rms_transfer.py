#!/usr/bin/env python3
"""Reproduce A-RH-RMS-0011 finite checks; no universal/formal verification."""
from __future__ import annotations
import argparse
from fractions import Fraction as F
import hashlib
import itertools
import json
import math
from pathlib import Path
import platform
import sys
import mpmath as mp
import numpy as np

SEED = 2026090611

def constants(A: float) -> tuple[float, ...]:
    U = math.sqrt(2)*math.exp(math.pi/2)*math.cosh(A/2)
    V = math.sqrt(2)*math.exp(math.pi/2)*math.sinh(A/2)
    c = (math.cosh(A/2)-1)/A if A else 0.0
    z = math.sinh(A/2)/A if A else 0.5
    X, Y = math.pi*(U+2), (U+2)*c+V*z
    R = math.hypot(X/2, 2*Y)
    C = 7+(4/3)*(2*math.cosh(A)+1+math.sqrt(4*math.cosh(A)**2-3))
    return U, V, X, Y, R, C

def coefficients(m: np.ndarray, t: np.ndarray, a: np.ndarray) -> np.ndarray:
    Q = len(m)
    v = np.arange(Q)/Q
    return (np.exp(2j*np.pi*v[:, None]*t)*np.cosh(v[:, None]*a))@m/Q

def energy(b: np.ndarray, alpha: float) -> float:
    x = np.arange(1, len(b))/len(b)
    return float(1/alpha+2/alpha**2*np.dot(np.maximum(alpha-x, 0), abs(b[1:])**2))

def rounding(m: np.ndarray, t: np.ndarray, theta: float):
    Q = len(m)
    k = np.floor(t-theta+0.5).astype(int)
    M = np.zeros(Q, dtype=int)
    np.add.at(M, k % Q, m)
    return theta+k, M, float(np.dot(m, (t-theta-k)**2)/Q)

def run(samples: int) -> dict:
    rng = np.random.default_rng(SEED)
    exact_weights = 0
    for Q in range(1, 65):
        for alpha in (F(1,2), F(3,4), F(7,8), F(1), F(51,100)):
            for j in range(1, Q):
                x = F(j,Q)
                assert max(alpha-x,F(0)) <= alpha*(1-x)
                exact_weights += 1
    exact_roundings = 0
    for Q in range(1, 5):
        for tau in itertools.product((F(0),F(1,2),F(3,4)), repeat=Q):
            for theta in (F(0),F(1,4),F(1,2),F(3,4)):
                slots = [0]*Q
                for p in range(Q):
                    slots[math.floor(p+tau[p]-theta+F(1,2)) % Q] += 2
                assert max(slots) <= (2 if Q == 1 else 4)
                assert sum(slots) == 2*Q
                exact_roundings += 1
    # Exact period-six word energy using rational sixth-root cosines.
    m6 = [1,1,1,1,2,0]
    cos6 = [F(1),F(1,2),F(-1,2),F(-1),F(-1,2),F(1,2)]
    word = F(4,3)
    for j in range(1,5):
        power = sum(F(m6[p]*m6[q],36)*cos6[((p-q)*j)%6]
                    for p in range(6) for q in range(6))
        word += F(32,9)*(F(3,4)-F(j,6))*power
    assert word == F(398,243)
    exact_variance, exact_short_excess = F(1,128), word-F(19,12)
    assert exact_short_excess == F(53,972)
    minimum_slack: dict[str,float] = {}
    maximum_residual: dict[str,float] = {}
    def bound(name: str, left: float, right: float):
        slack = float(right-left)
        minimum_slack[name] = min(minimum_slack.get(name, math.inf), slack)
        if slack < -2e-9*(1+abs(left)+abs(right)):
            raise AssertionError((name,left,right,slack))
    def equal(name: str, left, right):
        residual = float(np.max(np.abs(np.asarray(left)-np.asarray(right))))
        maximum_residual[name] = max(maximum_residual.get(name,0),residual)
        if residual > 2e-9*(1+float(np.max(np.abs(right)))):
            raise AssertionError((name,residual))
    collisions = anchor_cases = cases = 0
    configurations = []
    for i in range(samples):
        Q = int(rng.choice([3,4,6,9,12,18,24,36,48]))
        d = int(rng.integers(0,(Q-1)//2+1))
        m = np.array([2]*d+[0]*d+[1]*(Q-2*d))
        rng.shuffle(m)
        A = [0.0,math.log(2),1.5][i%3]
        if i%3 == 0:
            tau = np.clip(0.5+rng.normal(0,1e-3,Q),0,1-1e-10)
            a = np.where(m==2,rng.uniform(0,1e-3,Q)*A,0)
        else:
            tau = rng.uniform(0,1,Q)
            a = np.where(m==2,rng.uniform(0,A,Q),0)
        configurations.append((m,tau,a,A))
    configurations += [(np.array([1]),np.array([0.5]),np.array([0.0]),0.0),
        (np.array([2,2,0,0]),np.array([0.99,0.01,0.5,0.5]),np.zeros(4),0.0),
        (np.array([2,0]),np.array([0.1,0.5]),np.array([0.7,0]),0.7),
        (np.array(m6),np.full(6,0.5),np.zeros(6),0.0)]
    for m,tau,a,A in configurations:
        Q = len(m); t = np.arange(Q)+tau; s = float(np.count_nonzero(m==1)/Q)
        u = (np.arange(Q)-(Q-1)/2)/Q
        v = np.exp(2j*np.pi*u[:,None]*t)/math.sqrt(Q)
        G = v*np.sqrt(m)*np.cosh(u[:,None]*a)
        H = v*np.sqrt(m)*np.sinh(u[:,None]*a)
        T = G@G.conj().T-H@H.conj().T
        b = coefficients(m,t,a)
        idx = np.arange(Q)[:,None]-np.arange(Q)[None,:]
        Tb = np.where(idx>=0,b[abs(idx)],np.conj(b[abs(idx)]))
        equal('finite_reconstruction',T,Tb)
        equal('long_moment',np.linalg.norm(T,'fro')**2/Q,energy(b,1))
        delta = s+energy(b,1)-2
        bound('signed_defect_nonnegative',0,delta)
        Edep = float(np.dot(m,a*a)/Q)
        U,V,X,Y,R,C = constants(A)
        bound('G_operator',np.linalg.norm(G,2),U)
        bound('H_operator',np.linalg.norm(H,2),V)
        phases = [0.0,0.37]
        if s:
            theta = min(tau[m==1],key=lambda th:rounding(m,t,float(th))[2])
            phases.append(float(theta)); anchor_cases += 1
            eta = C*(math.pi**2*Q**2+A*A/4)*max(delta,0)/(s*Q)
            bound('inherited_anchor',4*rounding(m,t,float(theta))[2]+Edep/4,eta)
        for ntheta,theta in enumerate(phases):
            t0,M,Eph = rounding(m,t,theta)
            collisions += int(np.max(M)>2)
            assert M.max()<=4 and M.sum()==Q and np.dot(M,M)>=np.dot(m,m)
            G0 = np.exp(2j*np.pi*u[:,None]*t0)*np.sqrt(m)/math.sqrt(Q)
            T0 = G0@G0.conj().T
            b0 = coefficients(m,t0,np.zeros(Q))
            equal('rounded_operator',np.linalg.norm(G0,2)**2,float(M.max()))
            diff = float(np.linalg.norm(T-T0,'fro')/math.sqrt(Q))
            estimate = X*math.sqrt(Eph)+Y*math.sqrt(Edep)
            bound('RMS_transfer',diff,estimate)
            bound('elliptic_RMS',estimate,R*math.sqrt(4*Eph+Edep/4))
            equal('trace_cancel',np.diag(T-T0),np.zeros(Q))
            for alpha in (0.51,0.625,0.75,0.9,1.0):
                L,L0 = energy(b,alpha),energy(b0,alpha)
                gap = abs(math.sqrt(max(0,L-1/alpha))-math.sqrt(max(0,L0-1/alpha)))
                f = (2*alpha-1)/alpha**2
                bound('weighted_contraction',gap,diff/math.sqrt(alpha))
                bound('integer_floor',1/alpha+f*(1-s),L0)
                bound('short_RMS_floor',math.sqrt(f*(1-s)),math.sqrt(max(0,L-1/alpha))+estimate/math.sqrt(alpha))
                if s and ntheta == 2:
                    bound('conditional_new_floor',math.sqrt(f*(1-s)),math.sqrt(max(0,L-1/alpha))+R*math.sqrt(eta/alpha))
            cases += 1
    strain = []
    for Q in (18,36,72,144,288,576):
        m = np.tile(m6,Q//6); p = np.arange(Q); h = 1/8
        tau = 0.5+h*np.sin(2*np.pi*p/Q)
        b = coefficients(m,p+tau,np.zeros(Q))
        delta = 2/3+energy(b,1)-2
        var = float(np.dot(m,(tau-0.5)**2)/Q)
        equal('strain_variance',var,float(exact_variance))
        bound('strain_delta',delta,4*math.pi**4*h*h/Q)
        # A finite grid is a regression, not the proof of phase minimization.
        for theta in np.linspace(0,1,257,endpoint=False):
            d = (tau-theta+0.5)%1-0.5
            bound('strain_phase_grid',var,float(np.dot(m,d*d)/Q))
        strain.append({'Q':Q,'delta':delta,'Q_delta':Q*delta,
            'phase_variance':var,'short_energy':energy(b,0.75)})
    mp.mp.dps = 70
    A = mp.log(2); B = mp.mpf(16)/3
    C = 7+B/4*(2*mp.cosh(A)+1+mp.sqrt(4*mp.cosh(A)**2-3))
    U = mp.sqrt(2)*mp.exp(mp.pi/2)*mp.cosh(A/2)
    V = mp.sqrt(2)*mp.exp(mp.pi/2)*mp.sinh(A/2)
    X = mp.pi*(U+2); Y = (U+2)*(mp.cosh(A/2)-1)/A+V*mp.sinh(A/2)/A
    R2 = (X/2)**2+(2*Y)**2; g = mp.sqrt(mp.mpf(8)/27)-mp.mpf(1)/2
    thresholds = []
    for Q in (6,12,24,48,96,384):
        hQ = C*(mp.pi**2*Q**2+A*A/4)/(mp.mpf(2)/3*Q)
        pQ = mp.pi*mp.sqrt(Q*hQ)
        qQ = 4*(mp.cosh(A)-1)/A**2*hQ*mp.sqrt(Q)
        old = (2*g/(pQ+mp.sqrt(pQ*pQ+4*qQ*g)))**2
        new = mp.mpf(3)/4*g*g/(R2*hQ)
        thresholds.append({'Q':Q,'old':mp.nstr(old,30),'new':mp.nstr(new,30),
                           'new_over_old':mp.nstr(new/old,20)})
    return {'ok':True,'attempt':'A-RH-RMS-0011','seed':SEED,'random_samples':samples,
        'boundary_configurations':4,'phase_comparisons':cases,'anchor_configurations':anchor_cases,
        'comparisons_with_mass_above_two':collisions,
        'exact_checks':{'weight_inequalities':exact_weights,'rounding_assignments':exact_roundings,
            'period_six_short_energy':str(word),'strain_variance':str(exact_variance),
            'period_six_short_excess':str(exact_short_excess)},
        'maximum_residuals':maximum_residual,'minimum_slacks':minimum_slack,
        'strain':strain,'thresholds_A_log2':thresholds,
        'backend':{'python':platform.python_version(),'numpy':np.__version__,'mpmath':mp.__version__},
        'scope':'exact finite subchecks and numerical regressions; proofs are separately stated candidates',
        'independent_verification':False,'mathematical_truth_verified':False}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples',type=int,default=120)
    parser.add_argument('--output',type=Path,default=Path('validation.json'))
    parser.add_argument('--check-package',action='store_true')
    args = parser.parse_args()
    if not 1 <= args.samples <= 10000:
        parser.error('--samples must be between 1 and 10000')
    if args.check_package:
        root = Path(__file__).resolve().parent
        checkpoint = json.loads((root/'checkpoint.json').read_text())
        for name,digest in checkpoint['sha256'].items():
            path = root/name
            if path.parent != root or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError('artifact hash mismatch: '+name)
        claims = json.loads((root/'claims.json').read_text())['claims']
        assert len({c['id'] for c in claims}) == len(claims)
        assert all(c['evidence_grade']=='proof_candidate' and c['cannot_imply'] for c in claims)
        print(json.dumps({'ok':True,'hashes':len(checkpoint['sha256']),'claims':len(claims),
                          'scope':'package integrity only'}))
        return 0
    result = run(args.samples)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'ok':result['ok'],'samples':args.samples,'exact_checks':result['exact_checks'],
                      'phase_comparisons':result['phase_comparisons'],'output':str(args.output)},sort_keys=True))
    return 0

if __name__ == '__main__':
    sys.exit(main())
