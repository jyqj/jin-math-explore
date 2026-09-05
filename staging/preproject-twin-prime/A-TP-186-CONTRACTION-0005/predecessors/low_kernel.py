"""Exact low-fragment primitives and finite carry envelopes.

No third-party packages, no floating point acceptance, no external processes.
This is an independent implementation, not a byte copy of upstream code.
It does not compute the complete 40-dimensional prime-gap integrals.
"""
from __future__ import annotations
from fractions import Fraction as F
from math import factorial
from collections import deque
from typing import Sequence


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def ceil_div(n: int, d: int) -> int:
    require(d > 0, 'positive denominator required')
    return -((-n) // d)


def rounded(x: F, bits: int, upper: bool) -> int:
    n = x.numerator << bits
    return ceil_div(n, x.denominator) if upper else n // x.denominator


def exp_negative_enclosure(x: F, bits: int) -> tuple[int, int, int]:
    """For 0<=x<=1 enclose exp(-x) by alternating Taylor and dyadic rounding."""
    require(isinstance(x, F) and 0 <= x <= 1, 'Taylor routine requires rational x in [0,1]')
    require(isinstance(bits, int) and not isinstance(bits, bool) and bits >= 32, 'bits>=32 required')
    if x == 0:
        return 1 << bits, 1 << bits, 0
    term, total, lower, upper = F(1), F(1), F(0), F(1)
    for n in range(1, 4097):
        term *= -x / n
        total += term
        if n % 2:
            lower = total
        else:
            upper = total
        if upper - lower < F(1, 1 << (bits + 24)):
            return rounded(lower, bits, False), rounded(upper, bits, True), n
    raise ArithmeticError('Taylor budget exceeded')


def log_enclosure(x: F, bits: int) -> tuple[F, F]:
    """Enclose log(x) for 1<=x<=2 using an atanh series and geometric tail."""
    require(isinstance(x, F) and 1 <= x <= 2, 'log domain is [1,2]')
    if x == 1:
        return F(0), F(0)
    z = (x - 1) / (x + 1)
    power, partial = z, F(0)
    for n in range(4096):
        partial += 2 * power / (2*n + 1)
        power *= z*z
        remainder = 2 * power / ((2*n + 3) * (1-z*z))
        if remainder < F(1, 1 << bits):
            return partial, partial + remainder
    raise ArithmeticError('log series budget exceeded')


def dickman_nodes(m: int, last: int, bits: int) -> tuple[list[int], list[int]]:
    """Bounds for rho(i/m), i=0..last, in units 2^-bits.

Derived from the renewal equation and left/right rectangles, NOT a
floating-point delay-ODE solver. See low-kernel-proof.md for the induction.
"""
    require(isinstance(m, int) and not isinstance(m, bool) and m >= 2, 'm>=2 required')
    require(isinstance(last, int) and last >= m and bits >= 32, 'invalid mesh/precision')
    one = 1 << bits
    lower, upper = [one] * (m+1), [one] * (m+1)
    su, sl = m * one, (m-1) * one
    for i in range(m+1, last+1):
        u, l = ceil_div(su, i), sl // (i-1)
        require(0 <= l <= u <= upper[-1] <= one, 'Dickman enclosure/monotonicity invariant')
        lower.append(l)
        upper.append(u)
        su += u - upper[i-m]
        sl += l - lower[i-m+1]
    return lower, upper


def seed_cells(m: int, cells: int, delta: F, bits: int) -> dict:
    """Bounds for cell mass / h of exp(-lambda*s)rho(s/(m*h)) ds.

Here delta=lambda*h. Arrays are fixed dyadic endpoints for a common
positive cell measure. They are not independently rounded moment bounds.
"""
    lower, upper = dickman_nodes(m, cells, bits)
    el, eu, terms = exp_negative_enclosure(delta, bits)
    one, pl, pu = 1 << bits, 1 << bits, 1 << bits
    low_mass, high_mass = [], []
    for j in range(cells):
        nl = (pl * el) >> bits
        nu = ceil_div(pu * eu, one)
        lo = (lower[j+1] * nl) >> bits
        hi = ceil_div(upper[j] * pu, one)
        require(0 <= lo <= hi, 'seed endpoints crossed')
        low_mass.append(lo)
        high_mass.append(hi)
        pl, pu = nl, nu
    return dict(rho_lower=lower, rho_upper=upper, seed_lower=low_mass,
                seed_upper=high_mass, exp_step_lower=el, exp_step_upper=eu,
                taylor_terms=terms, exp_last_lower=pl, exp_last_upper=pu)


def eulerian_integers(n: int) -> list[int]:
    """A(n,k), k=0..n-1. A(n,k)/n! is P(floor(sum of n U[0,1])=k)."""
    require(isinstance(n, int) and n >= 1, 'positive variable count required')
    a = [1]
    for r in range(2, n+1):
        b = [0] * r
        for k in range(r):
            if k < len(a):
                b[k] += (k+1) * a[k]
            if k:
                b[k] += (r-k) * a[k-1]
        a = b
    require(sum(a) == factorial(n), 'Eulerian normalization failed')
    return a


def carry(n: int) -> list[F]:
    return [F(a, factorial(n)) for a in eulerian_integers(n)]


def tail_factor(first_tail: int, max_count: int, extra: int) -> dict:
    """Smallest scalar beta bounding ALL relevant Eulerian carry coefficients.

extra=0: seed+n unmarked fragments; extra=1: also one designated fragment.
Scope is a finite count range; no monotonicity in the variable count is assumed.
"""
    require(0 <= first_tail <= max_count and extra in (0,1), 'invalid tail count range')
    beta, where, rows = F(0), [], []
    for n in range(first_tail, max_count+1):
        c = carry(n+extra+1)
        value = max(c)
        ks = [i for i,x in enumerate(c) if x == value]
        rows.append(dict(unmarked_count=n,uniform_variables=n+extra+1,
                         maximum=str(value),at=ks))
        if value > beta:
            beta, where = value, []
        if value == beta:
            where.extend([[n,k] for k in ks])
    require(0 < beta <= 1, 'invalid tail factor')
    return dict(beta=str(beta),attained_at=where,rows=rows)


def add(a: Sequence[F], b: Sequence[F], length: int) -> list[F]:
    return [(a[i] if i < len(a) else F(0)) + (b[i] if i < len(b) else F(0))
            for i in range(length)]


def conv(a: Sequence[F], b: Sequence[F], length: int) -> list[F]:
    require(length > 0, 'positive truncation required')
    out = [F(0)] * length
    for i,x in enumerate(a[:length]):
        if x:
            for j,y in enumerate(b[:length-i]):
                if y:
                    out[i+j] += x*y
    return out


def scale(a: Sequence[F], x: F) -> list[F]:
    return [x*v for v in a]


def exp_series(h: Sequence[F], length: int) -> list[F]:
    require(len(h) > 0 and h[0] == 0, 'formal exponential requires H(0)=0')
    e = [F(1)] + [F(0)] * (length-1)
    for r in range(1, length):
        e[r] = sum((i*h[i]*e[r-i] for i in range(1,min(r+1,len(h)))),F(0))/r
    return e


def carry_tail_formula(h: Sequence[F], length: int, cutoff: int, extra: int) -> list[F]:
    """All-carry remainder [exp(H)-x^(extra+1)exp(xH)]/(1-x) minus prefix."""
    e0, e1 = exp_series(h,length), exp_series([F(0)]+list(h),length)
    total, running = [], F(0)
    for j in range(length):
        running += e0[j]
        if j >= extra+1:
            running -= e1[j-extra-1]
        total.append(running)
    term = [F(1)] + [F(0)] * (length-1)
    for n in range(cutoff+1):
        subtract = conv(term,[F(1)]*(n+extra+1),length)
        total = [a-b for a,b in zip(total,subtract)]
        term = scale(conv(term,h,length),F(1,n+1))
    require(all(x >= 0 for x in total), 'formal carry tail must be nonnegative')
    return total


def kernels_exact(h: Sequence[F], low: Sequence[F], mark: Sequence[F], length: int,
                  minimum: int, cutoff: int) -> dict:
    """Small-grid exact oracle for full Eulerian kernels, old and tightened tails.

Quadratic reference convolution; deliberately not used at the 98,304-cell
production size. Input arrays represent dominating cell densities/masses.
"""
    require(2 <= minimum < length and 0 <= cutoff, 'invalid kernel grid')
    require(all(x >= 0 for a in (h,low,mark) for x in a), 'positive arrays required')
    require(all(x == 0 for x in h[:minimum]) and all(x == 0 for x in mark[:minimum]),
            'support below positive minimum')
    maximum = (length-1)//minimum
    require(cutoff < maximum, 'test must exercise a nonempty tail')
    channels = []
    for extra in (0,1):
        full, prefix, tail_explicit = [F(0)]*length,[F(0)]*length,[F(0)]*length
        term = [F(1)] + [F(0)]*(length-1)
        for n in range(maximum+1):
            true_part = conv(term,carry(n+extra+1),length)
            full = add(full,true_part,length)
            if n <= cutoff:
                prefix = add(prefix,true_part,length)
            else:
                tail_explicit = add(tail_explicit,conv(term,[F(1)]*(n+extra+1),length),length)
            term = scale(conv(term,h,length),F(1,n+1))
        tail = carry_tail_formula(h,length,cutoff,extra)
        require(tail == tail_explicit,'formal-exponential/all-count identity mismatch')
        beta = F(tail_factor(cutoff+1,maximum,extra)['beta'])
        old, new = add(prefix,tail,length), add(prefix,scale(tail,beta),length)
        for name, v in [('full',full),('old',old),('new',new)]:
            v = conv(v,low,length)
            if extra:
                v = conv(v,mark,length)
            if name == 'full': full_out = v
            elif name == 'old': old_out = v
            else: new_out = v
        require(all(t <= n <= o for t,n,o in zip(full_out,new_out,old_out)),
                'tightened kernel failed coefficientwise domination')
        channels.append(dict(full=full_out,old=old_out,new=new_out,beta=beta))
    return dict(background=channels[0],designated=channels[1])


def spline_density(order: int, x: F) -> F:
    """Cardinal B-spline density of a sum of order independent U[0,1]."""
    from math import comb
    require(order >= 2 and isinstance(x,F), 'spline order>=2 and rational point required')
    return sum(((-1)**j * comb(order,j) * max(F(0),x-j)**(order-1)
                for j in range(order+1)),F(0))/factorial(order-1)


def global_tail_factor() -> dict:
    """Sharp max carry probability for ALL uniform-variable counts >=34.

Proof: C_m(k)=f_(m+1)(k+1). Symmetry/unimodality gives
||f_36||_infinity=f_36(18)=C_35(17). Convolution contracts L-infinity,
so every m>=35 is covered. The sole m=34 case is checked exactly here.
Thus this does not rely on extrapolating a finite scan to all m.
"""
    beta = carry(35)[17]
    require(spline_density(36,F(18)) == beta, 'independent spline formula mismatch')
    require(max(carry(34)) <= beta < F(23,100), 'base/universal factor failed')
    return dict(beta=str(beta),worst_case={'uniform_variables':35,'carry':17},
                exceptional_base_34=str(max(carry(34))),
                remainder_reduction_fraction=str(1-beta),
                covers_all_uniform_variables_at_least=34,
                proof_bridge='unimodal symmetric B-spline and L-infinity contraction',
                improvement_scope='all-carry remainder only; not entire kernel or integral')
