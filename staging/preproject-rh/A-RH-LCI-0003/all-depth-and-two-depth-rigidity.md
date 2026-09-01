# A-RH-LCI-0003 — all-depth common-phase rigidity and two-depth local mixtures

Status: `solver_proof_candidate` (not independently verified)

Issue/run: `#32`, `run-20260829-rh-local-compactness-03`

This checkpoint continues `mixed-state-moderate-depth.md`. That note proved
mixed tangent/pair interface rigidity only for one common normalized pair depth

\[
0<a<2\pi,
\]

because its comparison with the all-load-two tangent background used a
pointwise sign. The sign does change at larger depth, but the positive part is
short range and can be absorbed by the exact all-load-two Fourier energy. The
absorption estimate becomes valid before the old sign interval ends. Their
overlap removes the depth restriction completely:

> In the ideal finite-periodic box model, for every fixed common depth
> `a>0`, vanishing `c=2` defect forces the pair indicator to have vanishing
> interface density. A stationary zero-defect component is therefore either
> pair-free or a homogeneous pair phase; the latter is exactly a tangent
> load-two phase at every scale.

A second exact result treats two distinct pair depths. Every finite binary
depth interface has a positive Fourier cost. Nevertheless two macroscopic
depth domains have defect density `O(log P/P)`, so the correct compactness
statement is again local: the random root may select a random homogeneous
depth, and no global single-depth conclusion is available.

Nothing here transfers the ideal statement through the actual Zeta23 smooth
taper, finite section, tails or prime side.

---

## 1. Recalled common-depth model

Let `P>=2`, let `A` be the set of reflection-pair residues and let every
`q notin A` carry a tangent load

\[
r_q\in\{0,1,2\}.
\]

Use the centered points

\[
s_j=\frac{j-(P-1)/2}{P}
\]

and the normalized Fourier rank-one projections `U_p`. For one pair depth
`a>0`, put

\[
B_{p,a}=2(C_aU_pC_a-S_aU_pS_a),
\qquad
K_{p,a}=B_{p,a}-2U_p,
\]

where `C_a=diag(cosh(a s_j))` and `S_a=diag(sinh(a s_j))`. Write

\[
K_{\mathcal A,a}=\sum_{p\in\mathcal A}K_{p,a}.
\]

The tangent comparison matrix is

\[
G_0=2\sum_{p\in\mathcal A}U_p+
\sum_{q\notin\mathcal A}r_qU_q.
\]

Every tangent load at most two saturates the scalar site budget and
`tr K_{p,a}=0`; hence the exact count defect is

\[
\Delta_{P,a}(\mathcal A,r)
=\|K_{\mathcal A,a}\|_F^2+
2\langle G_0,K_{\mathcal A,a}\rangle_F.
\tag{1.1}
\]

Let `m_p=1_A(p)` and let

\[
B_P(\mathcal A)=\sum_{p=0}^{P-1}|m_{p+1}-m_p|^2
\tag{1.2}
\]

be the number of oriented nearest-neighbor interfaces on the cycle.

---

## 2. A stronger all-load-two interface inequality

The exact all-load-two symbol from the preceding checkpoint is

\[
L_a(\theta)=4\left[
\theta(\cosh(a(1-\theta))-1)^2+
(1-\theta)(\cosh(a\theta)-1)^2
\right].
\tag{2.1}
\]

Put

\[
c_a=\cosh(a/2)-1.
\]

### Lemma A — trigonometric lower bound

For every `a>0` and `0<=theta<=1`,

\[
\boxed{
L_a(\theta)\ge 2c_a^2\sin^2(\pi\theta).
}
\tag{2.2}
\]

It is enough to take `0<=theta<=1/2`. Since `sinh x/x` is increasing,

\[
\cosh(a(1-\theta))-1
=2\sinh^2\!\left(\frac{a(1-\theta)}2\right)
\ge4(1-\theta)^2c_a.
\tag{2.3}
\]

Thus the first term of (2.1) is at least

\[
64\theta(1-\theta)^4c_a^2.
\]

The elementary inequality

\[
\sin^2(\pi\theta)\le4\theta(1-\theta)
\le32\theta(1-\theta)^4,
\qquad 0\le\theta\le\frac12,
\tag{2.4}
\]

proves (2.2). The first inequality follows by setting
`u=1-2theta` and using `sin(pi u/2)>=u` on `[0,1]`.

With the normalization

\[
\widehat m(\ell)=\frac1P\sum_pm_pe^{-2\pi i\ell p/P},
\]

Parseval gives

\[
\frac{B_P(\mathcal A)}P
=\sum_{\ell=0}^{P-1}4\sin^2(\pi\ell/P)
|\widehat m(\ell)|^2.
\tag{2.5}
\]

Combining (2.2) with the exact symbol identity,

\[
\boxed{
\|K_{\mathcal A,a}\|_F^2
\ge\frac{c_a^2}{2}B_P(\mathcal A).
}
\tag{2.6}
\]

This improves the earlier coarse `min(theta,1-theta)` interface constant and
will absorb the high-depth sign changes.

---

## 3. Total positive part of the high-depth interaction

For a nonzero residue offset `n`, write

\[
d(n)=\min(n,P-n),\qquad
x=\frac aP,\qquad
\vartheta_n=\frac{2\pi d(n)}P.
\]

The exact pair-versus-tangent kernel in the preceding note simplifies to

\[
\boxed{
J_{P,a}(n)
=\frac{4\sinh^2(a/2)}{P^2}
\frac{\cosh x\cos\vartheta_n-1}
     {(\cosh x-\cos\vartheta_n)^2}.
}
\tag{3.1}
\]

Define the distance-weighted positive mass

\[
S_{P,a}=\sum_{n=1}^{P-1}d(n)(J_{P,a}(n))_+.
\tag{3.2}
\]

### Lemma B — uniform positive-kernel moment

For every `P>=2` and `a>0`,

\[
\boxed{
S_{P,a}\le\frac{2}{\pi^2}\sinh^2(a/2).
}
\tag{3.3}
\]

To see this, set

\[
F_x(\vartheta)=
\frac{\sin\vartheta}{\cosh x-\cos\vartheta}.
\]

Then

\[
F_x'(\vartheta)=
\frac{\cosh x\cos\vartheta-1}
     {(\cosh x-\cos\vartheta)^2}.
\tag{3.4}
\]

The positive interval ends at

\[
\vartheta_x=\arccos(\operatorname{sech}x)<x.
\tag{3.5}
\]

For `x<pi/2`, (3.5) follows from
`cosh(x)cos(x)<1`, equivalently `tan x>tanh x`; for larger `x` it follows from
`vartheta_x<pi/2<=x`. On `[0,vartheta_x]`,

\[
F_x''(\vartheta)=
-\frac{\sin\vartheta
(\cosh^2x+\cosh x\cos\vartheta-2)}
{(\cosh x-\cos\vartheta)^3}\le0.
\tag{3.6}
\]

Let `h=2pi/P` and let `M` be the largest integer with `Mh<vartheta_x`.
Monotonicity of `F_x'` gives

\[
hF_x'(dh)\le F_x(dh)-F_x((d-1)h).
\]

Summation by parts, `Mh<x`, and
`F_x(vartheta_x)=1/sinh x` yield

\[
\sum_{d=1}^M dF_x'(dh)
\le\frac{x}{h^2\sinh x}.
\tag{3.7}
\]

Using the two symmetric residue directions in (3.1),

\[
S_{P,a}
\le\frac{2\sinh^2(a/2)}{\pi^2}
\frac{x}{\sinh x}
\le\frac{2\sinh^2(a/2)}{\pi^2}.
\]

---

## 4. Absorbing arbitrary tangent loads at high depth

Put

\[
d_q=\langle U_q,K_{\mathcal A,a}\rangle_F
=\sum_{p\in\mathcal A}J_{P,a}(p-q).
\tag{4.1}
\]

Because

\[
G_0=2I-\sum_{q\notin\mathcal A}(2-r_q)U_q
\]

and `tr K=0`, (1.1) becomes

\[
\Delta_{P,a}(\mathcal A,r)
=\|K_{\mathcal A,a}\|_F^2
-2\sum_{q\notin\mathcal A}(2-r_q)d_q.
\tag{4.2}
\]

Hence

\[
\Delta_{P,a}(\mathcal A,r)
\ge\|K_{\mathcal A,a}\|_F^2
-4\sum_{q\notin\mathcal A}(d_q)_+.
\tag{4.3}
\]

For a shift `n`, let

\[
C_n=\#\{q:m_q=0,\ m_{q+n}=1\}.
\]

Cyclic telescoping gives

\[
C_n=\frac12\sum_q|m_{q+n}-m_q|
\le\frac{d(n)}2B_P(\mathcal A).
\tag{4.4}
\]

Consequently

\[
\sum_{q\notin\mathcal A}(d_q)_+
\le\sum_n(J_{P,a}(n))_+C_n
\le\frac{B_P(\mathcal A)}2S_{P,a}.
\tag{4.5}
\]

Equations (2.6), (3.3), and (4.3)--(4.5) give the high-depth estimate

\[
\boxed{
\Delta_{P,a}(\mathcal A,r)
\ge\Gamma(a)B_P(\mathcal A),
}
\tag{4.6}
\]

where

\[
\boxed{
\Gamma(a)=
\frac12(\cosh(a/2)-1)^2
-\frac4{\pi^2}\sinh^2(a/2).
}
\tag{4.7}
\]

Since

\[
\frac{\sinh(a/2)}{\cosh(a/2)-1}=\coth(a/4),
\]

`Gamma(a)>0` exactly when

\[
\coth(a/4)<\frac{\pi}{2\sqrt2}.
\]

Define

\[
\boxed{
a_*=
4\operatorname{arccoth}\!\left(\frac{\pi}{2\sqrt2}\right)
=5.895547244878\ldots .
}
\tag{4.8}
\]

Then `Gamma(a)>0` for `a>a_*`, and crucially

\[
a_*<2\pi.
\tag{4.9}
\]

---

## 5. All fixed common depths are covered

The previous checkpoint proves, by the favorable sign of every off-diagonal
`J_{P,a}`, that for

\[
0<a<2\pi
\]

one has

\[
\Delta_{P,a}(\mathcal A,r)
\ge\|K_{\mathcal A,a}\|_F^2
\ge\frac{c_a^2}{2}B_P(\mathcal A).
\tag{5.1}
\]

The new estimate (4.6) holds with a positive coefficient for every
`a>a_*`. Since `a_*<2pi`, the two ranges overlap and cover every `a>0`.

### Theorem A — all-depth common-phase interface rigidity

For each fixed `a>0` there is an explicit `gamma(a)>0` such that every finite
periodic ideal mixed configuration satisfies

\[
\boxed{
\Delta_{P,a}(\mathcal A,r)
\ge\gamma(a)B_P(\mathcal A).
}
\tag{5.2}
\]

One valid choice is

\[
\gamma(a)=
\begin{cases}
\frac12(\cosh(a/2)-1)^2,&0<a<2\pi,\\[0.4em]
\Gamma(a),&a\ge2\pi.
\end{cases}
\tag{5.3}
\]

Thus the stationary zero-defect dichotomy in
`mixed-state-moderate-depth.md` extends to every common fixed depth:

1. the pair indicator is absent everywhere, leaving a tangent `0/1/2` law; or
2. every site is the same depth-`a` pair, which is exactly a tangent load-two
   phase at every taper and scale.

The previous `2pi` scope guard remains a correct statement about the old
pointwise comparison, but it is no longer a limitation of the combined ideal
argument.

---

## 6. Exact binary two-depth symbol

Now put a reflection pair at every residue, with depth `a` on `A` and depth
`b` on its complement, where

\[
a>b\ge0.
\]

A homogeneous depth-`b` pair lattice is exactly `2I`. Therefore the departure
from `2I` is

\[
\sum_{p\in\mathcal A}(K_{p,a}-K_{p,b}).
\]

Define

\[
\boxed{
\begin{aligned}
L_{a,b}(\theta)=4\big[&
\theta(\cosh(a(1-\theta))-\cosh(b(1-\theta)))^2\\
&+(1-\theta)(\cosh(a\theta)-\cosh(b\theta))^2
\big].
\end{aligned}
}
\tag{6.1}
\]

### Theorem B — exact two-depth Fourier energy

For every finite period,

\[
\boxed{
\frac{\Delta_{P;a,b}(\mathcal A)}P
=\sum_{\ell=0}^{P-1}
L_{a,b}(\ell/P)|\widehat m(\ell)|^2.
}
\tag{6.2}
\]

The symbol is strictly positive away from the constant mode when `a!=b`.
Put

\[
c_{a,b}=|\cosh(a/2)-\cosh(b/2)|.
\]

The factorization

\[
\cosh(at)-\cosh(bt)
=2\sinh((a+b)t/2)\sinh((a-b)t/2)
\]

and the proof of Lemma A give

\[
L_{a,b}(\theta)
\ge2c_{a,b}^2\sin^2(\pi\theta).
\tag{6.3}
\]

Hence

\[
\boxed{
\Delta_{P;a,b}(\mathcal A)
\ge\frac{c_{a,b}^2}{2}B_P(\mathcal A).
}
\tag{6.4}
\]

Every stationary binary-depth zero-defect law is therefore a mixture of the
two homogeneous phases. Taking `b=0` includes the tangent load-two phase.

---

## 7. Macroscopic depth separation is locally invisible

The binary theorem controls interface density, not global proximity to one
depth. Let `P` be even and let `A` be one contiguous half-cycle. Then
`B_P(A)=2`, while half the sites have depth `a` and half have depth `b`.

For `0<=theta<=1/2`, set

\[
D_1=|\cosh a-\cosh b|,
\qquad
D_2=|a-b|\sinh(\max(a,b)/2).
\]

The mean-value theorem gives

\[
L_{a,b}(\theta)\le4\theta(D_1^2+D_2^2),
\tag{7.1}
\]

and the same bound with `theta` replaced by `1-theta` on the other half of the
circle. The normalized DFT of a contiguous block satisfies

\[
|\widehat m(\ell)|
\le\frac1{P|\sin(\pi\ell/P)|}
\le\frac1{2P\,d(\ell/P)},
\]

where `d(theta)=min(theta,1-theta)`. Therefore

\[
\boxed{
\frac{\Delta_{P;a,b}(\mathcal A)}P
\le
\frac{2(D_1^2+D_2^2)}P
\left(1+\log(P/2)\right).
}
\tag{7.2}
\]

Thus

\[
\frac{\Delta_{P;a,b}}P\longrightarrow0
\]

although no single global depth describes most sites. Randomly rooted local
limits select a homogeneous depth-`a` or depth-`b` phase. This is the exact
depth analogue of the earlier slow-strain obstruction and confirms that a
future variable-depth theorem must be stated in local-weak, phase-mixture
language.

---

## 8. Consequences for the research route

This checkpoint removes one branch from the frontier:

- **closed in the ideal model:** one common fixed pair depth, including all
  depths above `2pi`;
- **closed for binary pair phases:** two distinct depths cannot coexist with
  positive stationary interface density;
- **still open:** a continuum or growing alphabet of depths, where several
  depth increments might interact before local compactness is established.

The preferred next theorem is now a variable-depth local compactness result:
small defect should force the depth field, after a random root, to converge to
a spatially constant but randomly distributed depth. A global deterministic
depth is false by (7.2).

For actual Zeta23, the remaining transfer obligations are unchanged:

1. smooth taper and exceptional ramp fibers;
2. finite grid, tail matrix and boundary layer;
3. normalization leakage;
4. passage from the finite signed defect to a stationary marked local limit;
5. a treatment of continuously varying depth, potentially using the centered
   frequency-square trace;
6. closure of every loss inside the `5/108` second-scale margin.

---

## 9. Authority boundary

Exact/proof-candidate statements recorded here:

- the strengthened symbol lower bound (2.2);
- the positive-kernel moment estimate (3.3);
- the high-depth absorption inequality (4.6);
- the overlap threshold `a_*<2pi` and all-depth common-phase theorem (5.2);
- the exact binary two-depth symbol (6.2) and interface bound (6.4);
- the phase-separated `O(log P/P)` obstruction (7.2).

Still open:

- arbitrary continuously varying depths;
- source-normalized smooth/finite/tail transfer;
- any unconditional improvement of a zeta-zero proportion.

No statement in this file proves or refutes the Riemann hypothesis.
