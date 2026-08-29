# Normalized two-scale certificate and analytic error budget

Status: `proof_candidate` for the finite ideal model; not independently verified

Parent attempt: `A-RH-RTD-0002`

This note corrects one normalization ambiguity in the earlier `23/32` calculation. The earlier `lambda=3/4` calculation is the **relative subscale** of a reference compression whose absolute scale tends to one. For a fixed Zeta23 reference parameter below one, two parameters must be kept separate.

## 1. Parameters

Let

\[
\theta=\frac dN\in(0,1]
\]

be the asymptotic reference-cell density, corresponding in the Zeta23 normalization to the fixed long/reference scale. Let

\[
\alpha\in[1/2,1]
\]

be the short scale relative to the reference scale. The short absolute scale is therefore

\[
\lambda_{\rm short}=\alpha\theta.
\]

Let \(m_1,\ldots,m_d\in\mathbb Z_{\ge0}\) be integer cell occupancies with

\[
\sum_{j=1}^d m_j=N,
\qquad
\mu=\frac Nd=\frac1\theta,
\]

and put

\[
V=\sum_{j=1}^d(m_j-\mu)^2.
\]

The quantity \(s_1\) denotes the number of cells with occupancy exactly one.

## 2. Short-scale spectral lower bound

For the ideal box kernel on the reference lattice, define

\[
s_\alpha(n)=\operatorname{sinc}^2(\alpha n).
\]

For \(1/2\le\alpha\le1\), the discrete Fourier symbol is

\[
S_\alpha(\xi)
=
\frac1\alpha
\sum_{k\in\mathbb Z}
\left(1-\frac{|\xi+k|}{\alpha}\right)_+,
\]

so

\[
S_\alpha(0)=\frac1\alpha,
\qquad
\omega_\alpha:=\min_\xi S_\alpha(\xi)
=\frac{2\alpha-1}{\alpha^2}.
\]

For the corresponding periodic/infinite quadratic form

\[
F_\alpha
=
\sum_{j,k=1}^d
m_jm_k\,s_\alpha(j-k),
\]

the constant Fourier mode and the mean-zero spectral gap give

\[
\boxed{
F_\alpha
\ge
\frac{N^2}{\alpha d}+\omega_\alpha V
=
\frac{N}{\alpha\theta}+\omega_\alpha V.}
\tag{2.1}
\]

## 3. Integer occupancy to simple cells

For every integer \(m\ge0\),

\[
\mathbf 1_{\{m=1\}}\ge1-(m-1)^2.
\]

Consequently,

\[
s_1
\ge
d-\sum_j(m_j-1)^2.
\]

Because the cross term vanishes around the mean \(\mu=1/\theta\),

\[
\sum_j(m_j-1)^2
=
V+d(\mu-1)^2
=
V+\frac{(1-\theta)^2}{\theta}N.
\]

Hence

\[
\boxed{
\frac{s_1}{N}
\ge
\theta-\frac{(1-\theta)^2}{\theta}-\frac VN.}
\tag{3.1}
\]

## 4. Conditional normalized theorem

The Zeta23 second-moment constant at the short absolute scale \(\alpha\theta\) is

\[
\kappa(\alpha\theta)
=
\frac1{\alpha\theta}+\frac{\alpha\theta}{3}.
\]

Assume that all losses required to compare the actual short-scale on-line quadratic form with the ideal occupancy form have been collected into a single normalized error \(\varepsilon\ge0\), and that

\[
F_\alpha
\le
\left(
\frac1{\alpha\theta}+\frac{\alpha\theta}{3}
+\varepsilon
\right)N.
\tag{4.1}
\]

Combining (2.1) and (4.1) gives

\[
\frac VN
\le
\frac{\alpha\theta}{3\omega_\alpha}
+\frac{\varepsilon}{\omega_\alpha}.
\]

Substitution into (3.1) proves

\[
\boxed{
\frac{s_1}{N}
\ge
\theta-\frac{(1-\theta)^2}{\theta}
-\frac{\alpha\theta}{3\omega_\alpha}
-\frac{\varepsilon}{\omega_\alpha}.}
\tag{4.2}
\]

This theorem is finite/ideal. Equation (4.1) is the unresolved analytic transfer hypothesis.

## 5. Optimal relative scale

The zero-error \(\alpha\)-dependent penalty is

\[
\frac{\alpha}{3\omega_\alpha}
=
\frac{\alpha^3}{3(2\alpha-1)}.
\]

Its derivative has the sign of \(4\alpha-3\). Thus the unique minimizer on \([1/2,1]\) is

\[
\alpha=\frac34,
\qquad
\omega_{3/4}=\frac89.
\]

At this scale, (4.2) becomes

\[
\boxed{
\frac{s_1}{N}
\ge
\frac{23\theta}{32}
-\frac{(1-\theta)^2}{\theta}
-\frac98\varepsilon.}
\tag{5.1}
\]

The previous \(23/32\) formula is precisely the limit \(\theta\to1\), \(\varepsilon\to0\).

## 6. Exact comparison with the one-scale Zeta23 certificate

At the reference scale \(\theta\), the flat rank--trace certificate has constant

\[
H(\theta)
=2-\frac1\theta-\frac{\theta}{3}.
\]

A direct simplification gives

\[
\boxed{
\left[
\frac{23\theta}{32}
-\frac{(1-\theta)^2}{\theta}
-\frac98\varepsilon
\right]
-H(\theta)
=
\frac{5\theta}{96}-\frac98\varepsilon.}
\tag{6.1}
\]

Therefore the two-scale route gives a strict improvement over the same-scale scalar certificate whenever

\[
\boxed{
\varepsilon<\frac{5\theta}{108}.}
\tag{6.2}
\]

Every unit of normalized transfer error costs exactly \(9/8\) in the simple-cell proportion.

For zero transfer error, (5.1) is greater than \(2/3\) exactly when

\[
27\theta^2-128\theta+96<0.
\]

In the relevant interval \(0<\theta\le1\), this is

\[
\boxed{
\theta>
\theta_*=
\frac{64-4\sqrt{94}}{27}
=
0.934020782987\ldots.}
\tag{6.3}
\]

More generally, to beat \(2/3\) at fixed \(\theta\), the total error must satisfy

\[
\varepsilon
<
\frac{-27\theta^2+128\theta-96}{108\theta}.
\tag{6.4}
\]

The right side tends to \(5/108\) as \(\theta\to1\).

## 7. Exact Nyquist-extremizer margin

At \(\theta=1\), the \(0/1/2\) extremal occupancy law has \(V/N=1/3\). Equation (2.1) at \(\alpha=3/4\) gives

\[
\frac{F_{3/4}}N
\ge
\frac43+\frac89\cdot\frac13
=\frac{44}{27}.
\]

The short-scale prime-side constant is

\[
\kappa(3/4)=\frac{19}{12}.
\]

Thus the exact ideal excess is

\[
\boxed{
\frac{44}{27}-\frac{19}{12}
=\frac5{108}.}
\tag{7.1}
\]

This is independent of the arrangement of empty, simple and double cells.

## 8. What must enter the error \(\varepsilon\)

A valid zeta application may use one total error ledger

\[
\varepsilon_{\rm total}
=
\varepsilon_{\rm extraction}
+\varepsilon_{\rm kernel}
+\varepsilon_{\rm finite\ section}
+\varepsilon_{\rm tail}
+\varepsilon_{\rm off-line}
+\varepsilon_{\rm normalization}.
\]

Each term needs an explicit theorem:

1. **extraction:** long-scale near equality produces a marked lattice occupancy model outside a controlled exceptional set;
2. **kernel:** the smooth taper's sampled squared kernel is close enough to the ideal \(s_\alpha\);
3. **finite section:** truncation and boundary rows preserve the lower quadratic bound;
4. **tail:** Zeta23's \(E\)-matrix and seam losses remain within the allocated budget;
5. **off-line:** the on-line positive-semidefinite form is isolated from the indefinite pair form without assuming away cancellation;
6. **normalization:** \(d/N\), \(\lambda_1\), taper constants and Riemann--von Mangoldt errors are tracked uniformly.

The full-matrix estimate

\[
\|P+Q\|_F^2\le(\kappa+o(1))N
\]

does **not** imply

\[
\|P\|_F^2\le(\kappa+o(1))N
\]

when \(Q\) is indefinite. The parent defect decomposition and the complete-frame pair-inertia note identify the exact additional structure required here.

## 9. Decisive next lemma

A sufficient next result is the following dichotomy.

> **Critical-lattice extraction/transfer dichotomy.** Fix
> \(\theta\in(\theta_*,1)\). For all sufficiently large height windows, either the long-scale \(c=2\) certificate has a positive normalized defect that already improves \(H(\theta)\), or there exists an integer occupancy representation of the effective on-line modes for which (4.1) holds at relative scale \(3/4\) with
> \[
> \varepsilon_{\rm total}
> <
> \frac{-27\theta^2+128\theta-96}{108\theta}.
> \]

Either branch would force a simple-zero proportion strictly above \(2/3\). The current package proves only the finite ideal consequence, not this dichotomy.

## 10. Deterministic checks and authority boundary

`check_clock_model.py` verifies the exact rational identities, the optimizer, the threshold \(\theta_*\), finite-circulant instances and the clock margin.

This note cannot imply:

- an unconditional improvement in the proportion of zeta zeros on the line;
- that actual zeta zeros admit the required occupancy representation;
- that off-line pair cancellation is negligible;
- that the \(5\theta/108\) budget can be met;
- any proof or refutation of the Riemann hypothesis.

Independent verification must rederive the finite theorem and bind the exact frozen artifact hashes.
