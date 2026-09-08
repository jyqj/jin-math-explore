"""Finite trigonometric-profile formulas for A-RH-PROFILE-0019.

Binary64 utilities, not interval arithmetic or a proof kernel. Profiles are
real even sums of exponentials with symmetric real coefficients. Global
positivity must follow from the construction, not from sampled values.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np


@dataclass(frozen=True)
class Profile:
    terms: tuple[tuple[float, float], ...]

    def __post_init__(self) -> None:
        if not self.terms or not all(math.isfinite(x) and math.isfinite(a)
                                     for x, a in self.terms):
            raise ValueError('A nonempty finite coefficient list is required')
        total: dict[float, float] = {}
        for x, a in self.terms:
            total[x] = total.get(x, 0.0) + a
        if any(abs(a-total.get(-x, 0.0)) > 1e-12 for x, a in total.items()):
            raise ValueError('Coefficients must be real and frequency-symmetric')

    @property
    def radius(self) -> float:
        return max(abs(x) for x, _ in self.terms)

    @property
    def coefficient_norm(self) -> float:
        return sum(abs(a) for _, a in self.terms)

    def value(self, u):
        u = np.asarray(u)
        return sum(a*np.cos(2*np.pi*x*u) for x, a in self.terms)

    def integral(self) -> float:
        return float(sum(a*np.sinc(x) for x, a in self.terms))

    def transform(self, z):
        z = np.asarray(z, dtype=complex)
        return sum(a*np.sinc(z+x) for x, a in self.terms)

    def sampled_transform(self, z, q: int):
        if q < 1:
            raise ValueError('q must be positive')
        u = (np.arange(q)-(q-1)/2)/q
        z = np.asarray(z, dtype=complex)
        # Direct entire sum also handles resonant removable singularities.
        return np.mean(self.value(u)*np.exp(2j*np.pi*z[..., None]*u), axis=-1)

    def multiply(self, other: Profile) -> Profile:
        return Profile(tuple((x+y, a*b) for x, a in self.terms
                             for y, b in other.terms))

    def potential(self, u):
        """Integral |u-v| p(v) dv, evaluated without subtracting close cosines."""
        u = np.asarray(u)
        return sum(a*(0.5*np.sinc(x)-(0.25-u*u)*np.sinc(x*(0.5+u))
                      *np.sinc(x*(0.5-u))) for x, a in self.terms)


def cosine_profile(omega: float) -> Profile:
    if not 0 <= omega <= math.pi:
        raise ValueError('Positive cosine family requires 0<=omega<=pi')
    if omega == 0:
        return Profile(((0.0, 1.0),))
    a = omega/(2*math.sin(omega/2))
    x = omega/(2*math.pi)
    return Profile(((-x, a/2), (x, a/2)))


def mixture(profiles: list[Profile], weights: list[float]) -> Profile:
    if len(profiles) != len(weights) or not weights or min(weights) < 0:
        raise ValueError('Nonnegative matching weights required')
    total = sum(weights)
    if total <= 0:
        raise ValueError('Positive total weight required')
    return Profile(tuple((x, a*w/total) for p, w in zip(profiles, weights)
                         for x, a in p.terms))


def test_weight(frequency: float, amplitude: float, offset: float = 1.0) -> Profile:
    if frequency < 0 or offset < abs(amplitude):
        raise ValueError('offset>=abs(amplitude) certifies nonnegativity')
    return Profile(((0.0, offset), (-frequency, amplitude/2),
                    (frequency, amplitude/2)))


def functional(f: Profile, g: Profile, theta: float, nodes: int = 96) -> float:
    if not 0 < theta <= 1:
        raise ValueError('0<theta<=1 required')
    u, w = np.polynomial.legendre.leggauss(nodes)
    u, w = u/2, w/2
    return float(np.dot(w, f.value(u)*(g.value(u)/theta+theta*g.potential(u))))


def profile_matrix(q: int, t, m, a, p: Profile):
    """Return T,S,H, sampled profile normalizer and original simple count."""
    if q < 1:
        raise ValueError('q must be positive')
    t, m, a = np.asarray(t), np.asarray(m), np.asarray(a)
    if not (t.ndim == m.ndim == a.ndim == 1 and len(t) == len(m) == len(a)):
        raise ValueError('Orbit arrays must have the same one-dimensional shape')
    if (not len(m) or np.any(m < 1) or np.any(m != np.floor(m)) or np.any(a < 0)
            or np.any((a > 0) & (m % 2 != 0))):
        raise ValueError('Integer masses and even nonreal orbit masses required')
    if len(set(zip(t.tolist(), a.tolist()))) != len(t):
        raise ValueError('Combine repeated orbit points before counting simples')
    u = (np.arange(q)-(q-1)/2)/q
    v = p.value(u)
    if np.min(v) < -1e-13 or np.sum(v) <= 0:
        raise ValueError('Profile must have positive sampled total and no negative sample')
    prob = np.maximum(v, 0)/np.sum(v)
    e = np.sqrt(prob[:, None])*np.exp(2j*np.pi*u[:, None]*t)
    simple = (m == 1)
    V = e[:, simple]
    G = e[:, ~simple]*np.sqrt(m[~simple])*np.cosh(u[:, None]*a[~simple])
    H = e[:, ~simple]*np.sqrt(m[~simple])*np.sinh(u[:, None]*a[~simple])
    S = V@V.conj().T
    T = S+G@G.conj().T-H@H.conj().T
    return T, S, H, float(np.mean(v)), int(simple.sum())


def atomic_list(t, m, a):
    z, w = [], []
    for x, mass, depth in zip(t, m, a):
        if depth == 0:
            z.append(complex(x)); w.append(float(mass))
        else:
            z.extend([x+1j*depth/(2*np.pi), x-1j*depth/(2*np.pi)])
            w.extend([mass/2, mass/2])
    return np.asarray(z), np.asarray(w)


def pair_moment(f: Profile, g: Profile, z, weights, q: int | None = None) -> complex:
    z, weights = np.asarray(z), np.asarray(weights)
    if len(z) == 0 or len(z) != len(weights) or np.min(weights) <= 0:
        raise ValueError('Nonempty positive-mass atomic list required')
    d = z[:, None]-z[None, :]
    F = f.transform(d) if q is None else f.sampled_transform(d, q)
    G = g.transform(d) if q is None else g.sampled_transform(d, q)
    return complex(np.sum(weights[:, None]*weights[None, :]*F*G)/weights.sum())


def alias_bound(f: Profile, g: Profile, z, weights, q: int, margin: float) -> float:
    if q < 1 or not 0 <= margin < 1:
        raise ValueError('Positive q and 0<=margin<1 required')
    z, weights = np.asarray(z), np.asarray(weights)
    lam = max(f.radius, g.radius)
    if float(np.ptp(z.real))+lam > margin*q+1e-12:
        raise ValueError('Shifted real-diameter margin is not satisfied')
    c = float(np.sinc(margin))
    Y = float(np.ptp(z.imag))
    load = float(np.dot(weights, np.exp(2*np.pi*abs(z.imag))))
    constant = (np.pi**2*math.cosh(np.pi*Y/q)*(1+2*lam)
                *f.coefficient_norm*g.coefficient_norm/(3*c*c))
    return constant*load*load/(float(weights.sum())*q*q)


def normalization_bound(p: Profile, q: int, margin: float) -> float:
    if q < 1 or not 0 <= margin < 1 or p.radius > margin*q:
        raise ValueError('Invalid profile-frequency margin')
    return np.pi**2*sum(abs(a)*x*x for x, a in p.terms)/(6*np.sinc(margin)*q*q)
