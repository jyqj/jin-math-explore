# A-RH-LCI-0003 — quantitative angle and weighted-depth checkpoint

Status: `solver_proof_candidate` (not independently verified)

Issue/run: `#32`, `run-20260829-rh-local-compactness-03`

This checkpoint is additive. It does not rewrite the earlier slow-strain,
local-compactness, or hyperbolic-swap records. It addresses the exact remaining
gap: the full Fourier frame forbids perfect positive/negative-span
cancellation for a finite genuine configuration, but the previous record gave
no quantitative modulus for growing finite sections.

## 1. Riesz lower bound -> principal angle

Let `A : C^r -> H` and `B : C^s -> H` be synthesis operators, with

\[
U=\operatorname{ran}A,\qquad V=\operatorname{ran}B.
\]

Assume

\[
\|Aa+Bb\|^2\ge\gamma(\|a\|^2+\|b\|^2),
\qquad
\|Bb\|^2\le\Gamma\|b\|^2,
\tag{1.1}
\]

for `0 < gamma <= Gamma`. For `y=Bb` and arbitrary `u=Aa`,

\[
\|y-u\|^2=\|A(-a)+Bb\|^2
\ge\gamma\|b\|^2
\ge\frac\gamma\Gamma\|y\|^2.
\]

Hence

\[
\boxed{
\operatorname{dist}(y,U)^2\ge\eta\|y\|^2,
\qquad \eta=\gamma/\Gamma,
\qquad y\in V.
}
\tag{1.2}
\]

The exact squared principal-angle parameter is computable from Gram blocks.
Writing

\[
G_A=A^*A,\quad G_B=B^*B,\quad C=A^*B,
\]

one has

\[
\boxed{
\eta_*=\lambda_{\min}\!\left(
G_B^{-1/2}
[G_B-C^*G_A^{-1}C]
G_B^{-1/2}
\right).
}
\tag{1.3}
\]

This Schur complement is the finite-matrix object that future numerical and
formal checks should target.

## 2. Principal angle -> collapsed defect

Let `Pi_U` be the orthogonal projection onto `U`. Suppose `R >= 0` has range in
`V`, and `S=Pi_U S Pi_U` is any self-adjoint operator supported on `U`.
The Hilbert--Schmidt projection of `R` onto operators supported on `U` is
`Pi_U R Pi_U`. Since

\[
\|\Pi_U|_V\|^2=1-\eta_*,
\qquad
\|\Pi_U R\Pi_U\|_F\le(1-\eta_*)\|R\|_F,
\]

orthogonal projection gives

\[
\boxed{
\|R-S\|_F^2
\ge(2\eta_*-\eta_*^2)\|R\|_F^2.
}
\tag{2.1}
\]

Using only (1.1),

\[
\boxed{
\|R-S\|_F^2
\ge
\left(2\frac\gamma\Gamma-rac{\gamma^2}{\Gamma^2}\right)
\|R\|_F^2.
}
\tag{2.2}
\]

The exact coefficient is sharp for two lines: if
`U=span(e1)`, `V=span(c e1+sqrt(1-c^2)e2)`, and `R=r vv*`, then the best
positive `S=s e1e1*` has `s=rc^2` and

\[
\min_S\|R-S\|_F^2=r^2(1-c^4)
=(2\eta_*-\eta_*^2)\|R\|_F^2.
\tag{2.3}
\]

Apply this to the parent collapsed-orbit decomposition. Let `A` synthesize the
on-line vectors and real parts of off-line pair vectors, let `B` synthesize
their imaginary parts, and write

\[
P^\sharp=AA^*,\qquad R^\sharp=BB^*.
\]

Because `(P^sharp-2I)_+` is supported on `ran A`, the nonnegative defect
identity from the parent record implies

\[
\boxed{
\Delta_2^{\rm count}
\ge(2\eta_*-\eta_*^2)\|R^\sharp\|_F^2.
}
\tag{2.4}
\]

Thus a growing genuine configuration can imitate the abstract hyperbolic swap
only by making either `||Rsharp||_F^2=o(N)` or the positive/negative principal
angle collapse.

## 3. Conditional depth consequence

For a physical off-line pair write

\[
y_p(u)=-i\phi(u)e^{it_pu}\sinh(\delta_pu),
\qquad
R^\sharp=\sum_p2n_py_py_p^*.
\]

Then

\[
\|R^\sharp\|_F^2
=4\sum_{p,q}n_pn_q|\langle y_p,y_q\rangle|^2
\ge4\sum_pn_p^2\|y_p\|^4.
\tag{3.1}
\]

With

\[
M_2(\phi)=\int u^2\phi(u)^2\,du,
\]

`sinh^2(x) >= x^2` gives

\[
\|y_p\|^2\ge\delta_p^2M_2(\phi).
\]

Therefore

\[
\boxed{
\Delta_2^{\rm count}
\ge4(2\eta_*-\eta_*^2)M_2(\phi)^2
\sum_pn_p^2\delta_p^4.
}
\tag{3.2}
\]

This is not yet asymptotic progress on zeta: it needs a uniform or averaged
lower bound for `eta_*`. It does isolate the exact failure mode as quantitative
span collapse rather than pair interaction alone.

## 4. Centered frequency-square trace

The angle route gives a quartic depth penalty. A second observable detects
squared depth additively.

Assume `phi` is real, even, compactly supported, and in `H^1_0`. Put

\[
D=-i\,d/du,
\qquad A_\phi=\|\phi\|_2^2,
\qquad B_\phi=\|\phi'\|_2^2.
\]

For an on-line atom and one off-line pair set

\[
u_s=\phi e^{isu},
\quad
x_{t,\delta}=\phi e^{itu}\cosh(\delta u),
\quad
y_{t,\delta}=-i\phi e^{itu}\sinh(\delta u).
\]

For every real center `c`, direct differentiation gives

\[
\|(D-c)u_s\|_2^2=A_\phi(s-c)^2+B_\phi,
\tag{4.1}
\]

\[
\boxed{
\|(D-c)x_{t,\delta}\|_2^2
-
\|(D-c)y_{t,\delta}\|_2^2
=A_\phi[(t-c)^2-\delta^2]+B_\phi.
}
\tag{4.2}
\]

The cross terms cancel pointwise because

\[
(\phi'\cosh+\delta\phi\sinh)^2
-(\phi'\sinh+\delta\phi\cosh)^2
=(\phi')^2-\delta^2\phi^2.
\]

For on-line atoms `(s_i,m_i)` and pairs `(t_p,delta_p,n_p)`, define

\[
N=\sum_i m_i+2\sum_pn_p
\]

and

\[
\mathfrak M_c
=\sum_im_i\|(D-c)u_{s_i}\|_2^2
+2\sum_pn_p
(\|(D-c)x_p\|_2^2-\|(D-c)y_p\|_2^2).
\]

Then

\[
\boxed{
\frac{\mathfrak M_c-B_\phi N}{A_\phi}
=\sum_im_i(s_i-c)^2
+2\sum_pn_p(t_p-c)^2
-2\sum_pn_p\delta_p^2.
}
\tag{4.3}
\]

If all ordinates in a block are within `h` of `c` and a source-side argument
proves

\[
\mathfrak M_c\ge B_\phi N-A_\phi\varepsilon N,
\tag{4.4}
\]

then

\[
\boxed{
\frac1N\sum_pn_p\delta_p^2
\le\frac{h^2+\varepsilon}{2}.
}
\tag{4.5}
\]

Unlike the isolated-pair scalar penalty, (4.3) is linear in the signed
zero-side operator. Pair interactions cannot remove the `-delta^2` term; they
can only hide it behind horizontal variance or failure of (4.4).

## 5. Weighted Parseval and source alignment

For the complete grid

\[
\tau_k=T+2\pi k/L,
\qquad e_k(u)=L^{-1/2}e^{i\tau_ku},
\]

and endpoint-vanishing functions,

\[
\boxed{
\sum_k(\tau_k-c)^2
\langle f,e_k\rangle
\overline{\langle g,e_k\rangle}
=\langle(D-c)f,(D-c)g\rangle.
}
\tag{5.1}
\]

With Zeta23's unnormalized coefficients both sides acquire the same factor
`L`. Thus `M_c` is a diagonal weighted trace of the complete zero-side matrix,
not an external nonlinear statistic.

The pinned source already proves the unweighted real-argument Poisson identity,
and its `LocalHyps` package contains integrability plus an explicit bound for

\[
\int\widehat\phi(r)^2r^2\,dr.
\]

That gives a starting point for weighted-tail control. The source currently
formalizes only the unweighted real-argument identity, so the complex weighted
extension, finite-section error, and prime-side lower bound (4.4) remain new
proof obligations.

## 6. Updated highest-priority frontier

Two routes are now separated rather than conflated:

1. **Angle route:** lower-bound the Schur complement in (1.3), perhaps after
   deleting a small exceptional mass, and feed it into (2.4)--(3.2).
2. **Weighted-trace route:** prove (4.4) on mesoscopic ordinate blocks, forcing
   mean squared depth to vanish by (4.5).
3. **Hybrid:** use the weighted trace to remove deep pairs; collapse the
   remaining shallow pairs into tangent load-two cells; use the angle route on
   exceptional ill-conditioned clusters; then spend the losses against the
   surviving `5/108` cross-scale margin.

A useful countermodel search must now satisfy the genuine exponential/Gabor
structure while simultaneously exhibiting positive deep-pair density,
vanishing scalar defect, collapsing principal angle, and no violation of the
prospective weighted trace bound. Failure to construct such a model is not a
proof, but any successful model would decisively refute this hybrid route and
must be retained.

## 7. Authority boundary

Exact identities/proof candidates recorded here:

- Riesz-to-angle inequality (1.2);
- exact Gram/Schur parameter (1.3);
- sharp operator-distance inequality (2.1);
- collapsed defect consequence (2.4), conditional on the parent exact
  decomposition;
- physical depth inequality (3.2);
- centered derivative identities (4.1)--(4.3);
- local conditional depth bound (4.5);
- full-grid weighted Parseval identity (5.1) under the stated domain
  assumptions.

Still open: a growing-section angle lower bound, the precise weighted complex
Poisson statement, a prime-side proof of (4.4), tail and normalization control,
and integration into the `5/108` budget. Nothing here proves RH or
unconditionally improves the critical-line proportion.
