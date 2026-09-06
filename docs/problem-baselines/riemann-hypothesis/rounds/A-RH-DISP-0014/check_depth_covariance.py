#!/usr/bin/env python3
"""A-RH-DISP-0014: finite exact checks and numerical self-checks, not a proof."""
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

SEED = 2026090714
TOL = 3e-9


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def field_norm(q: np.ndarray) -> float:
    size = len(q)
    t = np.arange(size) / size
    return float(np.dot(t * (1 - t), np.abs(np.fft.fft(q) / size) ** 2))


def spatial_norm(q: np.ndarray) -> float:
    size = len(q)
    if size == 1:
        return 0.0
    p = np.arange(size)
    diff = p[:, None] - p[None, :]
    weights = np.zeros((size, size))
    nz = diff != 0
    weights[nz] = 1 / np.sin(np.pi * diff[nz] / size) ** 2
    return float(np.sum((q[:, None] - q[None, :]) ** 2 * weights) / (4 * size**3))


def matrix(m: np.ndarray, tau: np.ndarray, a: np.ndarray):
    size = len(m)
    u = (np.arange(size) - (size - 1) / 2) / size
    t = np.arange(size) + tau
    v = np.exp(2j * np.pi * u[:, None] * t) / math.sqrt(size)
    g = v * np.sqrt(m) * np.cosh(u[:, None] * a)
    h = v * np.sqrt(m) * np.sinh(u[:, None] * a)
    return g @ g.conj().T - h @ h.conj().T, g, h


def correction_spectrum(a: np.ndarray) -> np.ndarray:
    """No cancellation of the constant term; unused cells must have a=0."""
    size = len(a)
    t = np.arange(size) / size
    # cosh(z)-1 = 2*sinh(z/2)^2 is stable at shallow depth.
    return 4 * np.sum(
        np.exp(2j * np.pi * t[:, None] * np.arange(size))
        * np.sinh(t[:, None] * a / 2) ** 2, axis=1
    ) / size


def covariance_energy(a: np.ndarray) -> float:
    c = correction_spectrum(a)
    t = np.arange(len(a)) / len(a)
    return float(2 * np.dot(1 - t[1:], np.abs(c[1:]) ** 2))


def local_variance(m: np.ndarray, a: np.ndarray, length: int) -> float:
    period = math.lcm(len(m), length)
    mm = np.tile(m, period // len(m))
    aa = np.tile(a, period // len(a))
    total = 0.0
    for start in range(0, period, length):
        w = mm[start:start + length]
        x = aa[start:start + length]
        mass = int(w.sum())
        if mass:
            center = float(np.dot(w, x) / mass)
            total += float(np.dot(w, (x - center) ** 2))
    return total / period


def exact_checks() -> dict:
    # The cyclic second difference determines the Fourier coefficients of w.
    difference_checks = symbol_checks = 0
    for size in range(2, 129):
        w = [F(j * (size - j), size**2) for j in range(size)]
        for j in range(size):
            target = F(2 * (size - 1), size**2) if j == 0 else F(-2, size**2)
            require(w[(j + 1) % size] - 2 * w[j] + w[(j - 1) % size] == target,
                    'cyclic weight recurrence')
            difference_checks += 1
            t = F(j, size)
            require(F(1, 4) <= t**3 + (1-t)**3 <= 1, 'symbol sandwich')
            symbol_checks += 1
    composition_checks = 0
    for x in [F(j, 8) for j in range(9)]:
        for y in [F(j, 8) for j in range(9)]:
            for power in range(1, 7):
                require(abs(x**power-y**power) <= power*abs(x-y), 'composition bound')
                composition_checks += 1
    # Real symmetric integer data is enough to test this algebraic identity
    # exactly; complex Hermitian cases are tested numerically below.
    displacement_checks = 0
    for size in range(2, 25):
        t = [((j*j + 3*j) % 11) - 5 for j in range(size)]
        T = [[t[abs(i-j)] for j in range(size)] for i in range(size)]
        T2 = [[sum(T[i][k]*T[k][j] for k in range(size))
               for j in range(size)] for i in range(size)]
        for i in range(size-1):
            for j in range(size-1):
                target = t[i+1]*t[j+1] - t[size-i-1]*t[size-j-1]
                require(T2[i+1][j+1]-T2[i][j] == target, 'Toeplitz displacement')
                displacement_checks += 1
    newton_checks = 0
    for size in range(1, 25):
        coeff = [F(0)] * (2*size+1)
        coeff[0], coeff[size], coeff[2*size] = F(1), F(-5, 2), F(1)
        sums = [F(0)] * (2*size+1)
        for k in range(1, 2*size+1):
            sums[k] = -sum(coeff[j]*sums[k-j] for j in range(1, k)) - k*coeff[k]
            if k < size:
                require(sums[k] == 0, 'Newton low moments')
            elif k == size:
                require(sums[k] == F(5*size, 2), 'Newton middle moment')
            elif k == 2*size:
                require(sums[k] == F(17*size, 4), 'Newton top moment')
            else:
                require(sums[k] == 0, 'Newton intervening moment')
            newton_checks += 1
    require(F(3,2)-F(3,4)/F(2,3) == F(3,8), 'rational kappa')
    require(F(64,9)*F(9,64) == 1, 'rational inverse')
    require(F(17,4)**2 - 18 == F(1,16), 'phase counterexample positivity')
    h, beta = F(1,3), F(2,9)
    repaired = F(8,9)*(2-F(2,3))+F(4,9)*((1-h)**2/(1-beta)+h*h/beta)
    require(repaired == F(314,189), 'exact-hole repaired scalar point')
    require(repaired-F(19,12) == F(59,756), 'repaired scalar gap')
    require(F(44,27)-F(19,12) == F(5,108), 'universal exact-hole mixture gap')
    return dict(cyclic_weight_recurrences=difference_checks,
                rational_symbol_bounds=symbol_checks,
                rational_composition_bounds=composition_checks,
                integer_toeplitz_displacements=displacement_checks,
                rational_newton_checks=newton_checks,
                rational_constant_checks=6)


def run(samples: int) -> dict:
    rng = np.random.default_rng(SEED)
    residuals: dict[str, float] = {}
    slacks: dict[str, float] = {}
    counts = dict(grid_models=0, local_variances=0, compositions=0,
                  arbitrary_phase_models=0, exact_equality_models=0,
                  reciprocal_polynomials=0, toeplitz_projection_cases=0, equality_short_floors=0, phase_perturbations=0)

    def equal(name, left, right):
        left, right = np.asarray(left), np.asarray(right)
        error = float(np.max(np.abs(left-right))) if left.size else 0.0
        scale = 1 + (float(np.max(np.abs(right))) if right.size else 0.0)
        residuals[name] = max(residuals.get(name, 0), error)
        require(error <= TOL*scale, f'{name}: residual {error}')

    def bound(name: str, left: float, right: float):
        slack = float(right-left)
        slacks[name] = min(slacks.get(name, math.inf), slack)
        require(slack >= -TOL*(1+abs(left)+abs(right)), f'{name}: {left} > {right}')

    grid_cases = []
    for i in range(samples):
        size = int(rng.choice([2,3,4,6,8,12,18,24,36,48]))
        if i % 4 == 0:
            m = np.full(size, 2)
        elif i % 4 == 1:
            doubles = int(rng.integers(0, size//2+1))
            m = np.array([2]*doubles+[0]*doubles+[1]*(size-2*doubles))
            rng.shuffle(m)
        elif i % 4 == 2:
            m = 2*rng.integers(0, 2, size)
        else:
            m = rng.integers(0, 3, size)
        A = [0.0, math.log(2), 1.0, 1.5, 3.0][i % 5]
        a = np.where(m == 2, rng.uniform(0, A, size), 0.0)
        if i % 9 == 0:
            a *= 0.01
        grid_cases.append((m, a, A))
    grid_cases.extend([
        (np.array([0]), np.array([0.0]), 0.0),
        (np.array([1]), np.array([0.0]), 0.0),
        (np.array([2]), np.array([0.7]), 0.7),
        (np.full(2, 2), np.full(2, 0.7), 0.7),
        (np.full(3, 2), np.array([0.0,0.01,0.0]), 0.01),
        (np.array([2,0,0,2]), np.array([0.5,0,0,0.2]), 0.5),
    ])
    for m, a, A in grid_cases:
        size = len(m)
        tau = np.full(size, 0.37)
        T, _, _ = matrix(m, tau, a)
        T0, _, _ = matrix(m, tau, np.zeros(size))
        K = T-T0
        E = covariance_energy(a)
        D = field_norm(a*a)
        equal('Dirichlet_spatial_Fourier', D, spatial_norm(a*a))
        equal('correction_matrix_spectrum', np.linalg.norm(K,'fro')**2/size, E)
        rho = float(m.sum()/size)
        simple = float(np.count_nonzero(m==1)/size)
        delta = float(simple+np.linalg.norm(T,'fro')**2/size-2*rho)
        trace = float(np.trace((2*np.eye(size)-T0)@K).real / size)
        equal('signed_defect_identity', delta, E-2*trace)
        gamma = math.sinh(A)/A if A else 1.0
        kappa = 1.5-gamma
        bound('nonlinear_upper', E, gamma**2*D)
        if kappa > 0:
            bound('nonlinear_lower', kappa**2*D, E)
        bound('moderate_depth_coercivity', E, delta)
        if A <= math.log(2):
            bound('rational_covariance_coercivity', (9/64)*D, delta)
        adjacent_q = float(np.mean((a*a-np.roll(a*a,1))**2))
        bound('neighbor_covariance', adjacent_q, 4*math.pi**2*D)
        for power in range(1,5):
            bound('Dirichlet_composition', math.sqrt(max(0,field_norm(a**(2*power)))),
                  power*A**(2*power-2)*math.sqrt(max(0,D)))
            counts['compositions'] += 1
        for length in (1,2,3,7,16):
            omega = local_variance(m,a,length)
            bound('local_variance_Dirichlet', omega, 4*math.pi*length**2*math.sqrt(max(0,D)))
            if kappa>0:
                bound('local_variance_defect',omega,4*math.pi*length**2/kappa*math.sqrt(max(0,delta)))
            counts['local_variances'] += 1
        # Cell-preserving phase perturbation; depths and marks are not rounded.
        pert_tau = np.clip(tau + rng.normal(0,0.04,size),0,1-1e-10)
        Tpert,_,_ = matrix(m,pert_tau,a)
        phi = float(np.dot(m,(pert_tau-0.37)**2)/size)
        delta_pert = float(simple+np.linalg.norm(Tpert,'fro')**2/size-2*rho)
        Cp = 2*math.pi*math.sqrt(rho)*(math.exp(math.pi/2)+1)**2*math.cosh(A)**2
        bound('phase_defect_transfer',delta,delta_pert+Cp*math.sqrt(phi))
        if kappa>0:
            bound('phase_covariance_interface',kappa**2*D,delta_pert+Cp*math.sqrt(phi))
        counts['phase_perturbations'] += 1
        counts['grid_models'] += 1

    # Arbitrary phases: test signed slack and reciprocal root identities,
    # but do NOT apply the critical-lattice covariance upper bound.
    for i in range(samples):
        size = int(rng.choice([2,3,4,6,8,12]))
        occupied = rng.random(size) < (0.85 if i%2 else 0.5)
        m = 2*occupied.astype(int)
        a = np.where(occupied,rng.uniform(0,1.0,size),0)
        tau = rng.uniform(0,1,size)
        T,g,h = matrix(m,tau,a)
        columns = g[:,occupied]
        if columns.size:
            left, singular, _ = np.linalg.svd(columns,full_matrices=False)
            rank = int(np.sum(singular > 1e-11))
            U = left[:,:rank]
            P = U@U.conj().T
        else:
            rank = 0; P = np.zeros_like(T)
        r = int(occupied.sum())
        zeta = float(np.linalg.norm((np.eye(size)-P)@h,'fro')**2)
        defect = float(np.linalg.norm(T,'fro')**2-4*r)
        equal('anchor_free_signed_slack',defect,
              np.linalg.norm(T-2*P,'fro')**2+4*(r-rank)+4*zeta)
        bound('anchor_free_nonnegative',0,defect)
        counts['arbitrary_phase_models'] += 1
        # Include full occupancy for exact degree-2Q self-inversive identity.
        depth = rng.uniform(0,0.8,size)
        centers = np.arange(size)+tau
        roots = np.concatenate([np.exp((2j*np.pi*centers+depth)/size),
                                np.exp((2j*np.pi*centers-depth)/size)])
        coeff = np.poly(roots)
        equal('self_inversive_coefficients',coeff,coeff[-1]*np.conj(coeff[::-1]))
        counts['reciprocal_polynomials'] += 1

    # Exact equality constructions: sparse real cosets, full constant-depth,
    # and empty models. Numerically check both trace and projection structure.
    for size in range(1,25):
        tau = np.full(size,0.23)
        for case in range(3):
            m = np.zeros(size,dtype=int) if case==0 else (
                2*(np.arange(size)%2==0).astype(int) if case==1 else np.full(size,2))
            a = np.full(size,0.6) if case==2 else np.zeros(size)
            T,_,_ = matrix(m,tau,a)
            equal('equality_defect',np.linalg.norm(T,'fro')**2,2*m.sum())
            equal('equality_idempotence',T@T,2*T)
            rho=float(m.sum()/size)
            tj=np.arange(size)/size
            bb=np.sum(m[None,:]*np.exp(2j*np.pi*tj[:,None]*(np.arange(size)+tau))
                      *np.cosh(tj[:,None]*a),axis=1)/size
            for alpha in (0.625,0.75,1.0):
                energy=rho*rho/alpha+2/alpha**2*float(np.dot(np.maximum(alpha-tj[1:],0),abs(bb[1:])**2))
                f=(2*alpha-1)/alpha**2
                bound('exact_hole_short_floor',2*f*rho+(1/alpha-f)*rho*rho,energy)
                counts['equality_short_floors'] += 1
            counts['exact_equality_models'] += 1
        # Generic twisted Fourier projections (all subset sizes).
        Fmat = np.exp(2j*np.pi*np.arange(size)[:,None]*(np.arange(size)+0.23)/size)/math.sqrt(size)
        selector = (np.arange(size)%3 != 1)
        P = Fmat[:,selector]@Fmat[:,selector].conj().T
        equal('projection_idempotence',P@P,P)
        if size>1:
            u = P[1:,0]; v = np.conj(u[::-1])
            equal('projection_rank_one_boundary',np.outer(u,u.conj()),np.outer(v,v.conj()))
            equal('projection_twist',v,np.exp(-2j*np.pi*0.23)*u)
        counts['toeplitz_projection_cases'] += 1

    # Counterexample: a common depth does not make K vanish at arbitrary phases.
    m=np.full(2,2); a=np.full(2,math.log(2)); tau=np.array([0.25,0.75])
    T,_,_=matrix(m,tau,a); T0,_,_=matrix(m,tau,np.zeros(2))
    phase_loss=float(np.linalg.norm(T-T0,'fro')**2/2)
    equal('off_grid_counterexample',phase_loss,17/4-3*math.sqrt(2))
    require(phase_loss>0 and field_norm(a*a)==0,'off-grid counterexample')

    # High-depth sign guard: one vacant residue sees a positive atomwise leakage.
    size=32; m=np.full(size,2); m[1]=0; a=np.zeros(size); a[0]=8
    tau=np.zeros(size); T,_,_=matrix(m,tau,a); T0,_,_=matrix(m,tau,np.zeros(size))
    K=T-T0
    high_gap=float((np.linalg.norm(K,'fro')**2-(np.linalg.norm(T,'fro')**2-2*m.sum()))/size)
    require(high_gap>0,'the moderate-depth guard must fail beyond its stated range')

    # Pure-pair slow squared-depth wave: D -> 0 but global variance is fixed.
    slow=[]
    for size in (8,16,32,64,128,256,512):
        p=np.arange(size); q=0.25+0.125*np.cos(2*np.pi*p/size); a=np.sqrt(q)
        D=field_norm(q); E=covariance_energy(a)
        exact_D=(1/128)*(1/size)*(1-1/size)
        equal('slow_wave_Dirichlet',D,exact_D)
        equal('slow_wave_global_variance',np.var(q),1/128)
        gamma=math.sinh(math.sqrt(3/8))/math.sqrt(3/8)
        bound('slow_wave_upper',E,gamma**2*D)
        slow.append(dict(Q=size,delta_cell=E,Q_delta=size*E,
                         squared_depth_global_variance=float(np.var(q)),
                         Dirichlet=D,local_variance_R4=local_variance(np.full(size,2),a,4)))

    mp.mp.dps=80
    shallow=[]
    for denominator in (2,4,8,16,32,64,128):
        eps=mp.mpf(1)/denominator
        delta=4*mp.sinh(eps/4)**4  # (cosh(eps/2)-1)^2
        omega=eps**2/2
        shallow.append(dict(epsilon=str(eps),delta_cell=mp.nstr(delta,30),
                            variance=mp.nstr(omega,30),
                            variance_over_sqrt_delta=mp.nstr(omega/mp.sqrt(delta),30),
                            variance_over_delta=mp.nstr(omega/delta,30)))
    require(mp.mpf(shallow[-1]['variance_over_sqrt_delta'])>mp.mpf('3.999'),
            'quartic small-depth asymptotic')
    gamma_log2=mp.sinh(mp.log(2))/mp.log(2)
    return dict(ok=True,attempt='A-RH-DISP-0014',seed=SEED,random_samples=samples,
                counts=counts,exact_checks=exact_checks(),maximum_residuals=residuals,
                minimum_slacks=slacks,phase_scope_counterexample=phase_loss,
                high_depth_scope_counterexample_gap=high_gap,slow_depth_wave=slow,
                shallow_depth_boundary=shallow,
                kappa_log2=mp.nstr(mp.mpf(3)/2-gamma_log2,40),
                backend=dict(python=platform.python_version(),numpy=np.__version__,mpmath=mp.__version__),
                evidence='finite exact subchecks and numerical evidence; analytic statements are proof candidates',
                mathematical_truth_verified=False,independent_verification=False)


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples',type=int,default=120)
    parser.add_argument('--output',type=Path,default=Path('validation.json'))
    parser.add_argument('--check-package',action='store_true')
    args=parser.parse_args()
    if not 1<=args.samples<=1000:
        parser.error('--samples must be in [1,1000]')
    if args.check_package:
        root=Path(__file__).resolve().parent
        checkpoint=json.loads((root/'checkpoint.json').read_text(encoding='utf-8'))
        for name,expected in checkpoint['sha256'].items():
            require(Path(name).name==name,'nonlocal hash target')
            require(hashlib.sha256((root/name).read_bytes()).hexdigest()==expected,'hash mismatch '+name)
        claims=json.loads((root/'claims.json').read_text(encoding='utf-8'))['claims']
        require(len({c['id'] for c in claims})==len(claims),'duplicate claim')
        require(all(c['evidence_grade']=='proof_candidate' and c['cannot_imply'] for c in claims),'claim scope')
        print(json.dumps(dict(ok=True,hashes=len(checkpoint['sha256']),claims=len(claims),scope='integrity only')))
        return 0
    result=run(args.samples)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(dict(ok=True,counts=result['counts'],exact_checks=result['exact_checks'],output=str(args.output)),sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
