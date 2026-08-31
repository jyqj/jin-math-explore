# A-RH-LCI-0003 — mixed tangent states and moderate-depth pair rigidity

Status: `solver_proof_candidate` (not independently verified)

Issue/run: `#32`, `run-20260829-rh-local-compactness-03`

The preceding note classified zero-defect fixed-depth pair/vacancy laws. This
checkpoint allows every non-pair lattice site to carry an arbitrary tangent
load

\[
0,\quad1,\quad\text{or}\quad2,
\]

representing vacancy, a simple on-line point, or a tangent double/load-two
cell. For normalized pair depth

\[
0<a<2\pi,
\]

the pair indicator still has an explicit positive spectral lower bound.
Consequently, a stationary zero-defect mixed law has only two possibilities:

1. there are no positive-depth pairs, and the tangent `0/1/2` mark process may
   remain arbitrary;
2. every site is the same positive-depth reflection pair, which is exactly a
   tangent load-two phase at every scale by the previous frame identity.

This closes the ideal fixed-moderate-depth mixed-state classification. The
restriction `a<2pi` is genuine in the present argument: it is the range where
all finite-period off-diagonal pair-versus-tangent interactions have one
favorable sign.

---

## 1. Mixed finite periodic model

Let `P >= 2`, let `(f_p)` be the normalized Fourier basis of `C^P`, and put

\[
U_p=|f_p\rangle\langle f_p|.
\tag{1.1}
\]

Choose a pair set

\[
\mathcal A\subset\mathbb Z/P\mathbb Z.
\]

For every `q notin A`, choose a tangent load

\[
r_q\in\{0,1,2\}.
\tag{1.2}
\]

The tangent comparison configuration assigns load two to every pair site and
load `r_q` elsewhere:

\[
G_0
=2\sum_{p\in\mathcal A}U_p
+
\sum_{q\notin\mathcal A}r_qU_q.
\tag{1.3}
\]

Because every load is at most two, the `c=2` scalar certificate is saturated
sitewise by `G_0`.

Choose the centered fiber points

\[
s_j=\frac{j-(P-1)/2}{P},
\qquad0\le j<P,
\tag{1.4}
\]

and define

\[
C_a=\operatorname{diag}(\cosh(as_j)),
\qquad
S_a=\operatorname{diag}(\sinh(as_j)).
\tag{1.5}
\]

The genuine pair contribution at `p` is

\[
B_{p,a}=2(C_aU_pC_a-S_aU_pS_a).
\tag{1.6}
\]

Write its departure from the tangent load-two atom as

\[
K_{p,a}=B_{p,a}-2U_p,
\qquad
\operatorname{tr}K_{p,a}=0.
\tag{1.7}
\]

The mixed signed matrix is

\[
G=G_0+K_{\mathcal A,a},
\qquad
K_{\mathcal A,a}=\sum_{p\in\mathcal A}K_{p,a}.
\tag{1.8}
\]

Since `G_0` saturates the tangent count budget and `K` has trace zero, the
exact count defect is

\[
\boxed{
\Delta_{P,a}(\mathcal A,r)
=
\|K_{\mathcal A,a}\|_F^2
+2\langle G_0,K_{\mathcal A,a}\rangle_F.
}
\tag{1.9}
\]

---

## 2. Exact finite-period interaction and the `2pi` sign range

Put

\[
\omega=e^{2\pi i/P},
\qquad
\rho=e^{a/P}.
\]

For a nonzero residue difference `n mod P`, define

\[
\vartheta_n=\frac{2\pi n}{P}
\]

and

\[
A_{P,a}
=
\frac{\rho^{-(P-1)/2}(\rho^P-1)}{P}.
\tag{2.1}
\]

The sampled exponential Fourier coefficients are geometric sums. Splitting
`cosh` and `sinh` into the exponentials `e^{as}` and `e^{-as}` gives the exact
finite-period pair-versus-tangent interaction

\[
\boxed{
J_{P,a}(n)
:=\langle U_0,K_{n,a}\rangle_F
=
2A_{P,a}^2
\frac{(1+\rho^2)\cos\vartheta_n-2\rho}
     {(1+\rho^2-2\rho\cos\vartheta_n)^2},
\qquad n\not\equiv0\pmod P.
}
\tag{2.2}
\]

Indeed, if `E_+(n)` and `E_-(n)` are the normalized DFT coefficients of
`e^{as_j}` and `e^{-as_j}`, then

\[
J_{P,a}(n)=2\operatorname{Re}(E_+(n)\overline{E_-(n)}),
\]

and the numerator in (2.2) is obtained by rationalizing the two geometric
sums.

Since

\[
1+\rho^2=2\rho\cosh(a/P),
\]

the sign is the sign of

\[
\cosh(a/P)\cos\vartheta_n-1.
\tag{2.3}
\]

Let `d=min(n,P-n)`. If `cos vartheta_n<=0`, negativity is immediate. Otherwise

\[
0<\frac aP<\frac{2\pi}{P}\le\frac{2\pi d}{P}\le\frac\pi2
\]

whenever `0<a<2pi`, and

\[
\cosh(a/P)\cos\vartheta_n
<
\cosh(\vartheta_n)\cos(\vartheta_n)<1.
\]

The last inequality follows from
`tan x>tanh x` on `(0,pi/2]`. Therefore

\[
\boxed{
J_{P,a}(n)<0
\quad\text{for every }P\ge2,\ n\not\equiv0,
\quad0<a<2\pi.
}
\tag{2.4}
\]

This sign has a concrete extremal meaning. Compare an arbitrary tangent
background `(r_q)` with the all-load-two background. Since

\[
r_q-2\le0
\]

and `J_{P,a}(p-q)<0`,

\[
\begin{aligned}
\Delta_{P,a}(\mathcal A,r)
-
\Delta_{P,a}(\mathcal A,2)
&=
2\sum_{p\in\mathcal A}
\sum_{q\notin\mathcal A}
(r_q-2)J_{P,a}(p-q)\\
&\ge0.
\end{aligned}
\tag{2.5}
\]

Thus the smallest defect for a fixed pair set is obtained by filling every
other site with tangent load two.

For fixed nonzero integer `n`, (2.2) tends as `P -> infinity` to

\[
8\sinh^2(a/2)
\frac{a^2-4\pi^2n^2}
     {(a^2+4\pi^2n^2)^2},
\tag{2.6}
\]

which explains the same `2pi` threshold in the continuum limit. Equation
(2.6) is not used as the finite-period identity.

---

## 3. Exact extremal symbol

In the all-load-two comparison background,

\[
G_0=2I.
\]

Since `tr K=0`, the cross term in (1.9) vanishes and

\[
\Delta_{P,a}(\mathcal A,2)
=
\|K_{\mathcal A,a}\|_F^2.
\tag{3.1}
\]

Let

\[
\widehat m(\ell)
=
\frac1P\sum_{p=0}^{P-1}
\mathbf1_{\mathcal A}(p)e^{-2\pi i\ell p/P}.
\tag{3.2}
\]

For `0 <= theta <= 1`, define

\[
\boxed{
L_a(\theta)
=4\left[
\theta\bigl(\cosh(a(1-\theta))-1\bigr)^2
+(1-\theta)\bigl(\cosh(a\theta)-1\bigr)^2
\right].
}
\tag{3.3}
\]

### Theorem A — mixed-state lower spectrum

The translation autocorrelation of the difference atoms `K_{p,a}` gives

\[
\boxed{
\frac{\|K_{\mathcal A,a}\|_F^2}{P}
=
\sum_{\ell=0}^{P-1}
L_a(\ell/P)|\widehat m(\ell)|^2.
}
\tag{3.4}
\]

Combining (2.5) and (3.4), for every tangent background
`r_q in {0,1,2}` and every `0<a<2pi`,

\[
\boxed{
\frac{\Delta_{P,a}(\mathcal A,r)}P
\ge
\sum_{\ell=0}^{P-1}
L_a(\ell/P)|\widehat m(\ell)|^2.
}
\tag{3.5}
\]

The symbol can also be obtained from the pair-pair and pair-simple symbols. If

\[
R_a(\theta)
=
\theta\cosh(a(1-\theta))
+(1-\theta)\cosh(a\theta),
\]

then

\[
L_a(\theta)
=2\bigl[3+R_{2a}(\theta)-4R_a(\theta)\bigr],
\tag{3.6}
\]

and the identity `cosh(2x)=2cosh^2(x)-1` reduces this to (3.3).

---

## 4. Positivity and pair-interface control

Let

\[
d(\theta)=\min(\theta,1-\theta).
\]

For `0 <= theta <= 1/2`, the first term of (3.3) gives

\[
L_a(\theta)
\ge
4\theta\bigl(\cosh(a/2)-1\bigr)^2.
\]

By symmetry,

\[
\boxed{
L_a(\theta)
\ge
4\bigl(\cosh(a/2)-1\bigr)^2d(\theta).
}
\tag{4.1}
\]

For every `a>0`, `L_a` is strictly positive away from the constant mode.

Define the cyclic pair-indicator boundary density

\[
b_P(\mathcal A)
=
\frac1P\sum_p
|\mathbf1_{\mathcal A}(p+1)-\mathbf1_{\mathcal A}(p)|^2.
\tag{4.2}
\]

Using

\[
4\sin^2(\pi\theta)\le4\pi d(\theta),
\]

(3.5) and (4.1) imply

\[
\boxed{
 b_P(\mathcal A)
\le
\frac{\pi}{(\cosh(a/2)-1)^2}
\frac{\Delta_{P,a}(\mathcal A,r)}P,
\qquad0<a<2\pi.
}
\tag{4.3}
\]

Thus arbitrary tangent marks cannot hide a positive density of interfaces
between moderate-depth pair sites and non-pair sites.

---

## 5. Stationary mixed-state classification

Consider a stationary lattice law with:

- a pair indicator `A_n in {0,1}`;
- on every site with `A_n=0`, a tangent load in `{0,1,2}`;
- one common pair depth `0<a<2pi`.

Let `sigma_A` be the spectral measure of the centered pair indicator. The
finite lower bound passes to stationary limits as

\[
\boxed{
\mathcal D_a
\ge
\int_{\mathbb T}L_a(\theta)\,d\sigma_A(\theta).
}
\tag{5.1}
\]

Consequently

\[
\boxed{
\mathbb P(A_1\ne A_0)
\le
\frac{\pi}{(\cosh(a/2)-1)^2}\mathcal D_a.
}
\tag{5.2}
\]

### Theorem B — zero-defect dichotomy

If the mixed-state defect density is zero, then

\[
A_{n+1}=A_n
\quad\text{almost surely for every }n.
\tag{5.3}
\]

Therefore every ergodic zero-defect component is exactly one of:

1. **no positive-depth pairs:** `A_n=0` everywhere; the remaining tangent
   `0/1/2` mark process is unrestricted by this theorem;
2. **homogeneous pair phase:** `A_n=1` everywhere; every lattice site is the
   same depth-`a` reflection pair.

By the scale-invariance identity of the previous checkpoint, case 2 is
operator-identical to a tangent load-two phase for every taper and every
scale.

This is the ideal mixed-state collapsed-orbit classification for one fixed
moderate depth.

---

## 6. Why the depth restriction is retained

The exact finite numerator in (2.2) changes sign when

\[
\cosh(a/P)\cos(2\pi n/P)=1.
\]

For depths above the uniform `2pi` range, nearest-residue interactions need not
stay negative for every period. The all-load-two tangent background therefore
need not be the extremal comparison used in (2.5). The spectral symbol `L_a`
itself remains nonnegative for every depth, but the reduction from an arbitrary
mixed tangent background to that symbol is not justified by this argument.

The unresolved high-depth alternatives are:

1. find the correct extremal tangent background and a replacement matrix
   symbol;
2. use the centered frequency-square trace to charge the high-depth mass;
3. decompose high depth across a shorter scale where the normalized depth
   falls below the sign threshold;
4. construct a genuine countermodel showing that mixed high-depth phases can
   evade both scalar and two-scale observables.

No choice is silently assumed here.

---

## 7. Deterministic checker

Run

```bash
python3 staging/preproject-rh/A-RH-LCI-0003/check_mixed_state_depth.py
```

The checker verifies:

- the exact finite kernel formula (2.2);
- negativity of all tested off-diagonal interactions below `2pi`;
- the exact mixed finite matrix defect;
- the all-load-two extremal comparison (2.5) on random `0/1/2` backgrounds;
- the spectral identity (3.4);
- symbol positivity and the lower bound (4.1);
- the boundary inequality (4.3);
- explicit failure of the favorable-sign premise at sufficiently large depth.

The final high-depth check is a scope guard, not a claim that the theorem fails
immediately above `2pi`.

---

## 8. Research consequence

The ideal local-compactness route now has a sharper decision tree.

For pair mass whose normalized depth stays in a compact subinterval of
`(0,2pi)`:

1. vanishing long-scale defect forces the pair indicator to be locally
   constant;
2. pair-free components reduce to the existing tangent `0/1/2` process;
3. all-pair components become tangent mark two at the short scale;
4. the `lambda=3/4` Fourier-variance inequality applies without a new depth
   correction.

Only shallow depth tending to zero, variable depth, and high normalized depth
remain outside this classification. Those are now the correct targets for the
weighted trace and exceptional-mass machinery.

---

## 9. Authority boundary

Proof candidates/exact identities in this checkpoint:

- the exact finite pair-versus-tangent kernel (2.2);
- the favorable-sign reduction (2.5) for `0<a<2pi`;
- the exact difference-atom symbol (3.3)--(3.4);
- the mixed-state spectral lower bound (3.5);
- interface control (4.3);
- stationary zero-defect dichotomy (5.3).

Still open:

- depths at or above `2pi`;
- multiple positive depths in one configuration;
- depths tending to zero with `T`;
- actual smooth-taper, finite-section, tail and normalization transfer;
- the final `5/108` source-level budget.

This remains ideal-model mathematics. It does not establish any new
unconditional theorem about zeta zeros and does not prove RH.
