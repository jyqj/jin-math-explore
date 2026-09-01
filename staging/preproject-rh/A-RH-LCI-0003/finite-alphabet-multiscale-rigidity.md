# A-RH-LCI-0003 — finite-alphabet multiscale depth rigidity and channel-rank barrier

Status: `solver_proof_candidate` (not independently verified)

Issue/run: `#32`, `run-20260829-rh-local-compactness-03`

This checkpoint continues `all-depth-and-two-depth-rigidity.md` without
rewriting it. The preceding note solved the ideal common-depth sector for every
fixed depth and obtained an exact binary two-depth symbol. The next question is
whether that binary symbol extends to a finite or continuous field of
site-dependent reflection-pair depths.

The answer has two parts.

1. For a finite depth alphabet, the ideal aligned multiscale problem has an
   exact matrix-valued Fourier symbol. With `M-1` distinct aligned scales, an
   `M`-depth alphabet has a positive first-order interface gap. Consequently a
   stationary zero-defect component is a homogeneous, but possibly randomly
   chosen, depth phase.
2. A finite bank of `q` scales has only `2q` hyperbolic moment channels per
   spatial frequency. If the alphabet has at least `2q+2` depths, an exact
   invisible tangent direction exists at every frequency. More sharply, if
   `q<M-1`, no symbol-level lower bound proportional to spatial frequency can
   hold near frequency zero. Thus `M-1` scales are necessary and sufficient for
   the robust nearest-neighbor interface mechanism proved here.

This is an aligned ideal pair-lattice theorem. Different Zeta23 compression
scales do not automatically share one residue labelling, and no simultaneous
prime-side small-defect statement is proved here.

---

## 1. Arbitrary finite depth alphabet at one aligned scale

Fix a period `P>=2`. On `C^P`, let

\[
f_p(j)=P^{-1/2}e^{2\pi i p j/P},
\qquad
U_p=|f_p\rangle\langle f_p|,
\tag{1.1}
\]

and use the centered physical points

\[
s_j=\frac{j-(P-1)/2}{P},
\qquad 0\le j<P.
\tag{1.2}
\]

Let the distinct normalized depths be

\[
0\le a_1<a_2<\cdots<a_M.
\tag{1.3}
\]

Each residue `p` receives one label

\[
\ell_p\in\{1,\ldots,M\}.
\tag{1.4}
\]

For an aligned scale factor `alpha>0`, put

\[
C_{\alpha a}=\operatorname{diag}(\cosh(\alpha a s_j)),
\qquad
S_{\alpha a}=\operatorname{diag}(\sinh(\alpha a s_j)),
\tag{1.5}
\]

and define the reflection-pair atom

\[
B^{(\alpha)}_{p,a}
=2\left(C_{\alpha a}U_pC_{\alpha a}
       -S_{\alpha a}U_pS_{\alpha a}\right).
\tag{1.6}
\]

The total signed pair operator is

\[
G_\alpha=\sum_{p=0}^{P-1}B^{(\alpha)}_{p,a_{\ell_p}}.
\tag{1.7}
\]

Each pair atom has trace two. Since a homogeneous pair lattice has operator
`2I` at every depth and every scale, the all-pair `c=2` count defect is exactly

\[
\boxed{
\Delta_\alpha
=\|G_\alpha-2I\|_F^2.
}
\tag{1.8}
\]

The physical matrix entries are

\[
\boxed{
(G_\alpha)_{jk}
=\frac2P\sum_{p=0}^{P-1}
 e^{2\pi i p(j-k)/P}
 \cosh\!\left(\alpha a_{\ell_p}\frac{j-k}{P}\right).
}
\tag{1.9}
\]

For each depth class define the indicator and normalized DFT

\[
m_r(p)=\mathbf1_{\{\ell_p=r\}},
\qquad
\widehat m_r(n)
=\frac1P\sum_{p=0}^{P-1}m_r(p)e^{2\pi i pn/P}.
\tag{1.10}
\]

For nonzero `n`, the partition identity gives

\[
\sum_{r=1}^M\widehat m_r(n)=0.
\tag{1.11}
\]

Write

\[
\theta_n=\frac nP,
\qquad
z_n=(\widehat m_1(n),\ldots,\widehat m_M(n)).
\tag{1.12}
\]

### Theorem A — exact one-scale finite-alphabet symbol

For `0<theta<1` and `z in C^M`, define

\[
\boxed{
q_{\alpha,\theta}(z)
=4\left[
(1-\theta)
\left|\sum_{r=1}^Mz_r\cosh(\alpha\theta a_r)\right|^2
+\theta
\left|\sum_{r=1}^Mz_r\cosh(\alpha(1-\theta)a_r)\right|^2
\right].
}
\tag{1.13}
\]

Then

\[
\boxed{
\frac{\Delta_\alpha}{P}
=\sum_{n=1}^{P-1}q_{\alpha,\theta_n}(z_n).
}
\tag{1.14}
\]

Proof: use (1.9), group matrix entries by the ordinary difference
`d=j-k`, and pair the contributions at `d=n` and `d=-(P-n)`. The factors
`1-theta` and `theta` are the proportions of matrix entries on the two
corresponding diagonals. No asymptotic or random model is used.

For `M=2`, writing `z=(u,-u)` reduces (1.13) to the exact binary symbol in
`all-depth-and-two-depth-rigidity.md`.

---

## 2. A bank of aligned scales

Take distinct positive scales

\[
\alpha_1,\ldots,\alpha_q>0
\tag{2.1}
\]

and positive weights `w_j`. Define

\[
\Delta_{\mathcal A}
=\sum_{j=1}^qw_j\Delta_{\alpha_j}
\tag{2.2}
\]

and

\[
\boxed{
Q_\theta(z)
=\sum_{j=1}^qw_jq_{\alpha_j,\theta}(z).
}
\tag{2.3}
\]

The combined channel map is

\[
z\longmapsto
\left(
\begin{array}{c}
\sqrt{4w_j(1-\theta)}
 \sum_rz_r\cosh(\alpha_j\theta a_r)\\
\sqrt{4w_j\theta}
 \sum_rz_r\cosh(\alpha_j(1-\theta)a_r)
\end{array}
\right)_{j=1}^q.
\tag{2.4}
\]

It has at most `2q` complex output channels at each fixed spatial frequency.
The partition constraint restricts `z` to

\[
\mathcal H=\left\{z\in\mathbb C^M:\sum_rz_r=0\right\},
\qquad
\dim\mathcal H=M-1.
\tag{2.5}
\]

---

## 3. Exact finite-channel rank barrier

### Theorem B — pointwise rank obstruction

If

\[
M-1>2q,
\tag{3.1}
\]

then for every fixed `0<theta<1` there is a nonzero

\[
z_\theta\in\mathcal H
\]

such that

\[
\boxed{Q_\theta(z_\theta)=0.}
\tag{3.2}
\]

This is immediate from (2.4): after adjoining the one partition row, the
channel matrix has at most `2q+1` rows and `M` columns.

Thus, for

\[
M\ge2q+2,
\]

no proof based only on pointwise positive definiteness of these `q` zeroth-order
scale defects can distinguish all depth-class tangent directions. The null
vector may depend on `theta`; this is a symbol-level proof obstruction, not by
itself a deterministic depth-labelled zero-defect configuration.

### Stronger low-frequency obstruction

Suppose instead that

\[
q<M-1.
\tag{3.3}
\]

The `(q+1) x M` endpoint matrix

\[
\mathcal C_0=
\begin{pmatrix}
1&\cdots&1\\
\cosh(\alpha_1a_1)&\cdots&\cosh(\alpha_1a_M)\\
\vdots&&\vdots\\
\cosh(\alpha_qa_1)&\cdots&\cosh(\alpha_qa_M)
\end{pmatrix}
\tag{3.4}
\]

has a nonzero null vector `z in H`. For this vector, as `theta downarrow 0`,

\[
\sum_rz_r\cosh(\alpha_j\theta a_r)=O(\theta^2)
\tag{3.5}
\]

because `sum z_r=0`, while

\[
\sum_rz_r\cosh(\alpha_j(1-\theta)a_r)=O(\theta)
\tag{3.6}
\]

because the value at `theta=0` vanishes by (3.4). Hence

\[
\boxed{
Q_\theta(z)=O(\theta^3),
\qquad
\frac{Q_\theta(z)}{\theta}\longrightarrow0.
}
\tag{3.7}
\]

Therefore no constant `c>0` can satisfy

\[
Q_\theta(z)
\ge c\min(\theta,1-\theta)\|z\|^2
\tag{3.8}
\]

for all `theta` and all `z in H` when `q<M-1`.

This is sharper than the raw `2q` rank count. Even where the interior symbol is
pointwise injective, too few scales cannot supply the first-order low-frequency
coercivity needed to control nearest-neighbor depth interfaces.

---

## 4. Strict total positivity of the cosh moment matrix

The positive theorem uses the following finite-dimensional lemma.

### Lemma C — generalized cosh-Vandermonde determinant

Let

\[
0\le t_0<t_1<\cdots<t_{M-1},
\qquad
0\le a_1<a_2<\cdots<a_M.
\tag{4.1}
\]

Then

\[
\boxed{
\det\left[\cosh(t_i a_r)\right]_{
0\le i\le M-1,\ 1\le r\le M}>0.
}
\tag{4.2}
\]

One direct proof uses

\[
\cosh(ta)=
\sum_{k=0}^{\infty}\frac{t^{2k}a^{2k}}{(2k)!}.
\tag{4.3}
\]

Apply Cauchy--Binet first to a finite truncation. Each minor is a sum over

\[
0\le k_0<\cdots<k_{M-1}
\]

of

\[
\frac{
 \det[(t_i^2)^{k_j}]
 \det[(a_r^2)^{k_j}]
}{\prod_j(2k_j)!}.
\tag{4.4}
\]

The two generalized Vandermonde determinants have the same positive sign for
strictly increasing nonnegative nodes. The term `k_j=j` is strictly positive.
Passing through the absolutely convergent truncations proves (4.2).

This proof also covers `t_0=0` and `a_1=0` because the ordinary Vandermonde
term remains nonzero for distinct squared nodes.

---

## 5. `M-1` scales give a first-order interface gap

Assume now

\[
q=M-1
\tag{5.1}
\]

and that the scales `alpha_j` are pairwise distinct.

### Interior positivity

Fix `0<theta<1`. If `z in H` and `Q_theta(z)=0`, then in particular

\[
\sum_{r=1}^Mz_r\cosh(\alpha_j\theta a_r)=0,
\qquad1\le j\le M-1.
\tag{5.2}
\]

Together with `sum z_r=0`, this is the square cosh moment matrix with

\[
t_0=0,
\qquad
t_j=\alpha_j\theta.
\]

After ordering the distinct `t_j`, Lemma C implies `z=0`. Thus `Q_theta` is
positive definite on `H` for every interior frequency.

### Endpoint limits

For a unit vector `z in H`, Taylor expansion gives

\[
\lim_{\theta\downarrow0}
\frac{Q_\theta(z)}\theta
=4\sum_{j=1}^{M-1}w_j
\left|\sum_{r=1}^Mz_r\cosh(\alpha_ja_r)\right|^2.
\tag{5.3}
\]

The right side is positive on `H` by Lemma C with
`{0,alpha_1,...,alpha_(M-1)}`. The limit at `theta upward 1` is the same after
reflection.

Compactness of the unit sphere in `H` and of the compactified frequency
interval therefore gives a constant

\[
\boxed{
c_*=c_*(a_1,\ldots,a_M;
             \alpha_1,\ldots,\alpha_{M-1};
             w_1,\ldots,w_{M-1})>0
}
\tag{5.4}
\]

such that

\[
\boxed{
Q_\theta(z)
\ge c_*\min(\theta,1-\theta)\|z\|^2
}
\tag{5.5}
\]

for every `0<theta<1` and every `z in H`.

### Theorem D — finite-alphabet multiscale interface rigidity

Let

\[
e_p=(m_1(p),\ldots,m_M(p))\in\{e_1,\ldots,e_M\}
\tag{5.6}
\]

be the one-hot depth label vector, and define

\[
B_P^{\rm depth}
=\sum_{p=0}^{P-1}\|e_{p+1}-e_p\|^2.
\tag{5.7}
\]

Thus each change of depth label contributes two.

Parseval gives

\[
\frac{B_P^{\rm depth}}P
=\sum_{n=1}^{P-1}
 4\sin^2(\pi\theta_n)\|z_n\|^2.
\tag{5.8}
\]

Using the elementary bound

\[
\sin^2(\pi\theta)
\le\pi\min(\theta,1-\theta),
\tag{5.9}
\]

(1.14), (2.2), and (5.5) yield

\[
\boxed{
\Delta_{\mathcal A}
\ge\frac{c_*}{4\pi}B_P^{\rm depth}.
}
\tag{5.10}
\]

Consequences:

1. simultaneous zero defect at the `M-1` aligned scales forces one constant
   depth label on the entire finite cycle;
2. for a stationary finite-alphabet depth process, zero combined defect density
   forces `ell_(n+1)=ell_n` almost surely;
3. every ergodic zero-defect component is one homogeneous depth phase;
4. a general stationary zero-defect law may be a mixture of homogeneous phases,
   exactly as required by the earlier macroscopic phase-separation examples.

Together with the homogeneous pair/load-two identity, every such component is
operator-equivalent to tangent mark two at every subsequent occupancy scale.

---

## 6. Scale-count criterion

Within the exact symbol mechanism above:

\[
\boxed{
q=M-1
}
\tag{6.1}
\]

is necessary and sufficient for a robust first-order interface estimate for an
arbitrary fixed `M`-depth alphabet:

- sufficiency is Theorem D;
- necessity is the endpoint-null construction (3.4)--(3.7).

The weaker interior pointwise rank count only requires

\[
2q\ge M-1,
\tag{6.2}
\]

but this is not enough for local-interface compactness because the coercivity
can disappear faster than spatial frequency near zero.

For the currently preferred scale pair

\[
\{1,3/4\},
\tag{6.3}
\]

this theorem can robustly classify at most three prescribed depth classes.
A four-bin or finer depth quantization cannot obtain a nearest-neighbor
interface gap from only these two zeroth-order scale defects by this route.

This gives an exact resource-allocation rule rather than a vague suggestion to
"add more scales."

---

## 7. Continuum-depth implication and the role of the weighted trace

A finite scale bank cannot have a uniform finite-channel coercivity theorem for
an unrestricted continuum of depths. There is, however, an exact injective
continuum-scale moment map.

Let `I` be a nontrivial compact interval of positive scales and let `w(alpha)`
be positive almost everywhere. For a finite signed measure `nu` on a compact
interval `[0,A]`, define

\[
\Phi_\nu(\alpha)
=\int_0^A\cosh(\alpha a)\,d\nu(a).
\tag{7.1}
\]

If

\[
\nu([0,A])=0
\]

and

\[
\int_I|\Phi_\nu(\alpha)|^2w(\alpha)\,d\alpha=0,
\tag{7.2}
\]

then `Phi_nu` vanishes on an interval. It is entire in `alpha`, so every even
moment of `nu` vanishes. Polynomials in `a^2` are dense in `C([0,A])`; hence

\[
\boxed{\nu=0.}
\tag{7.3}
\]

Thus an interval of aligned scales is characteristic for compactly supported
depth distributions. It offers an exact continuum analogue of Lemma C, but not
a uniform finite-dimensional coercivity constant. Turning it into a useful
near-equality theorem would require:

- simultaneous prime-side control uniform in the scale parameter;
- an integrated error budget rather than separate pointwise asymptotics;
- transfer of one residue/depth field across the scale family;
- tightness or a quantitative moment-determinacy modulus.

The centered frequency-square observable remains the more economical finite
certificate: it adds a genuinely new depth moment instead of spending one new
compression scale per extra depth class.

---

## 8. Deterministic checks

Run

```bash
python3 staging/preproject-rh/A-RH-LCI-0003/check_multiscale_depth_alphabet.py
```

The checker verifies:

1. the exact direct-matrix/symbol identity (1.14) for random finite alphabets;
2. numerical generalized cosh-Vandermonde positivity samples;
3. an exact one-scale/four-depth channel null vector;
4. the two-scale/four-depth low-frequency failure `Q_theta/theta -> 0`;
5. a three-depth/two-scale first-order coercivity regression and the resulting
   interface inequality on random label configurations.

The numerical determinant and eigenvalue checks detect algebraic or
implementation regressions. Lemma C and Theorem D require independent proof
audit; floating-point positivity is not their proof.

---

## 9. Updated research architecture

The ideal variable-depth program now separates into three regimes.

### Finite, prescribed alphabet

Use one fewer aligned scale than the number of depth classes. The exact
matrix-valued symbol and cosh total positivity give local phase rigidity.

### Growing or continuum alphabet

A fixed finite scale bank has an intrinsic rank/endpoint obstruction. Options
are:

1. increase the number of aligned scales with the quantization complexity;
2. integrate over a scale interval, provided uniform prime-side control can be
   proved;
3. add the centered weighted trace, which observes squared horizontal depth
   additively;
4. combine a coarse three-bin/two-scale classification with weighted control
   of within-bin spread.

### Actual Zeta23 transfer

Before any of these ideal conclusions affect zeta zeros, one still needs:

- a common random-root/residue description across scales;
- smooth-taper comparison;
- finite-section and tail control;
- normalization leakage control;
- simultaneous prime-side bounds and covariance of their errors;
- closure inside the surviving `5/108` short-scale margin.

---

## 10. Authority boundary

Exact identities/proof candidates recorded here:

- the finite-alphabet one-scale symbol (1.13)--(1.14);
- the pointwise `2q` channel-rank obstruction;
- the low-frequency necessity `q>=M-1` for first-order symbol coercivity;
- strict cosh-moment total positivity;
- existence of the multiscale constant `c_*>0` for `q=M-1`;
- the interface inequality (5.10);
- continuum-scale injectivity on compact depth support.

Open:

- a source-compatible aligned scale field for actual zero configurations;
- explicit useful lower bounds for `c_*` as `M` or the depth range grows;
- a finite-scale theorem for a continuum of depths;
- integrated or simultaneous prime-side estimates;
- all smooth/tail/finite-section errors and the final `5/108` budget.

This checkpoint does not improve an unconditional zeta-zero proportion and
does not prove or refute the Riemann hypothesis.
