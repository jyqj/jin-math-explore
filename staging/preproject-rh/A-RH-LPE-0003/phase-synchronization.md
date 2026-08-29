# Local phase synchronization, random-block extraction, and finite-section control

Status: `proof_candidate` — finite deterministic mathematics, not independently verified

Attempt: `A-RH-LPE-0003`

Parent: `A-RH-RTD-0002@698d28d4e074f09fdb7dfdaffc65df1cdc94727b`

This note attacks the first unresolved bridge in the two-scale route: how a small long-scale sinc/Gram off-diagonal energy can force a local critical-lattice description without assuming an integer labelling in advance.

All statements below concern finite real configurations, weighted graphs, ideal sinc kernels, or explicit finite-section corrections. They do not establish that the actual Zeta23 zero-side matrices satisfy the hypotheses.

## 1. Conventions

For `t in R`, write

\[
\operatorname{sinc}(t)=
\begin{cases}
\dfrac{\sin(\pi t)}{\pi t},&t\ne0,\\
1,&t=0.
\end{cases}
\]

For `t in R`, let

\[
d_{\mathbb T}(t)=\operatorname{dist}(t,\mathbb Z)\in[0,1/2].
\]

Let `x_1,...,x_n in R`, let vertex weights `w_i>0`, and let symmetric edge weights

\[
a_{ij}=a_{ji}\ge0,
\qquad a_{ii}=0.
\]

Set

\[
W=\sum_iw_i,
\qquad
\overline f_w=\frac1W\sum_iw_if_i.
\]

The weighted graph Poincaré constant `lambda_G` is normalized by

\[
\sum_iw_i|f_i-\overline f_w|^2
\le
\frac1{\lambda_G}
\sum_{i<j}a_{ij}|f_i-f_j|^2
\tag{1.1}
\]

for every complex vector `f`. Equivalently, `lambda_G` is the smallest positive eigenvalue of `W^{-1/2}LW^{-1/2}` when the graph is connected.

Assume every positive-weight edge satisfies

\[
|x_i-x_j|\le R.
\tag{1.2}
\]

Define the local sinc energy

\[
E_{\rm sinc}
=
\sum_{i<j}a_{ij}\operatorname{sinc}^2(x_i-x_j).
\tag{1.3}
\]

## 2. Weighted local phase-synchronization theorem

### Theorem 2.1

Under (1.1)--(1.3), if `lambda_G>0`, there exists `tau in R/Z` such that

\[
\boxed{
\sum_iw_i d_{\mathbb T}(x_i-\tau)^2
\le
\frac{\pi^2R^2}{2\lambda_G}E_{\rm sinc}.}
\tag{2.1}
\]

Consequently, for every `0<eta<=1/2`,

\[
\boxed{
\sum_{d_{\mathbb T}(x_i-\tau)>\eta}w_i
\le
\frac{\pi^2R^2}{2\lambda_G\eta^2}E_{\rm sinc}.}
\tag{2.2}
\]

### Proof

Put

\[
z_i=e^{2\pi i x_i}.
\]

For `d=x_i-x_j`,

\[
|z_i-z_j|^2
=4\sin^2(\pi d)
=4\pi^2d^2\operatorname{sinc}^2(d)
\le
4\pi^2R^2\operatorname{sinc}^2(d).
\tag{2.3}
\]

Therefore the graph Dirichlet energy of `z` obeys

\[
\sum_{i<j}a_{ij}|z_i-z_j|^2
\le4\pi^2R^2E_{\rm sinc}.
\tag{2.4}
\]

Let

\[
\overline z=\frac1W\sum_iw_iz_i.
\]

By (1.1),

\[
V_z:=\sum_iw_i|z_i-\overline z|^2
\le
\frac{4\pi^2R^2}{\lambda_G}E_{\rm sinc}.
\tag{2.5}
\]

If `r=|\overline z|>0`, choose `zeta=\overline z/r`; if `r=0`, choose an arbitrary unit complex number. Since every `|z_i|=1`,

\[
\sum_iw_i|z_i-\zeta|^2
=2W(1-r)
\le2W(1-r^2)
=2V_z.
\tag{2.6}
\]

Write `zeta=e^{2\pi i\tau}`. For `u=d_T(x_i-tau) in [0,1/2]`, concavity of sine gives

\[
|z_i-\zeta|=2\sin(\pi u)\ge4u.
\tag{2.7}
\]

Thus

\[
\sum_iw_i d_{\mathbb T}(x_i-\tau)^2
\le
\frac1{16}\sum_iw_i|z_i-\zeta|^2
\le
\frac18V_z.
\]

Combining this with (2.5) proves (2.1). Equation (2.2) is Markov's inequality.

## 3. Complete-block specialization

Suppose all points lie in one interval of diameter at most `R`. Choose the complete weighted graph

\[
a_{ij}=w_iw_j
\qquad(i\ne j).
\]

Then the exact variance identity is

\[
\sum_{i<j}w_iw_j|f_i-f_j|^2
=W\sum_iw_i|f_i-\overline f_w|^2.
\tag{3.1}
\]

Hence `lambda_G=W`, and Theorem 2.1 becomes:

### Corollary 3.1

There exists `tau in R/Z` such that

\[
\boxed{
\sum_iw_i d_{\mathbb T}(x_i-\tau)^2
\le
\frac{\pi^2R^2}{2W}
\sum_{i<j}w_iw_j\operatorname{sinc}^2(x_i-x_j).}
\tag{3.2}
\]

If the right side is zero, every positive-mass point has the same phase modulo one. After coincident atoms are aggregated, the support lies in one translate `tau+Z`.

This complete-block corollary removes the need to prove a separate spectral-gap theorem inside each bounded block: the complete weighted graph has the exact gap `W`.

## 4. Random-partition local extraction

Let `x_1,...,x_n` be distinct real points carrying positive integer masses `m_i`, and put

\[
N=\sum_im_i.
\]

Define the global ideal long-scale energy

\[
E=\sum_{i<j}m_im_j\operatorname{sinc}^2(x_i-x_j).
\tag{4.1}
\]

Fix a block length `R>0` and a shift `u in [0,R)`. Partition the line into

\[
B_k(u)=[u+kR,u+(k+1)R).
\]

For every nonempty block, let `W_B` and `E_B` be its mass and internal energy. Corollary 3.1 gives a phase `tau_B` and a block loss

\[
L_B:=\sum_{x_i\in B}m_i d_{\mathbb T}(x_i-\tau_B)^2
\le
\frac{\pi^2R^2}{2W_B}E_B.
\]

Because `W_B>=1` and the block pair sets are disjoint,

\[
\boxed{
\sum_BL_B
\le
\frac{\pi^2R^2}{2}E.}
\tag{4.2}
\]

Therefore the total mass farther than `eta` from its block phase is at most

\[
\boxed{
M_{\rm phase-bad}
\le
\frac{\pi^2R^2}{2\eta^2}E.}
\tag{4.3}
\]

Now fix a local observation radius `0<r<=R/2`. Averaging the partition shift `u` over `[0,R)`, every atom lies within distance `r` of a block boundary for exactly a proportion `2r/R` of shifts. Hence some shift satisfies

\[
\boxed{
M_{\rm boundary}
\le
\frac{2r}{R}N.}
\tag{4.4}
\]

Delete the phase-bad mass and the boundary mass. Every retained point has a uniquely assigned local block phase, and its entire retained `r`-neighborhood lies in the same block.

### Theorem 4.1: quantitative local extraction

Let

\[
e=E/N.
\]

For every `R>2r` and `0<eta<1/2`, there is a shifted block partition and a deleted set of total mass at most

\[
\boxed{
N\left(
\frac{\pi^2R^2e}{2\eta^2}
+
\frac{2r}{R}
\right)}
\tag{4.5}
\]

such that every retained point is within `eta` of one blockwise translate of `Z`, and every retained radius-`r` neighborhood uses a single translate.

If `e->0`, the balanced choice

\[
R=e^{-1/5},
\qquad
\eta=e^{1/5}
\tag{4.6}
\]

gives, for every fixed `r` and sufficiently small `e`,

\[
\frac{M_{\rm deleted}}N
\le
\left(\frac{\pi^2}{2}+2r\right)e^{1/5},
\tag{4.7}
\]

while the positional phase error is at most `e^{1/5}` and the block length tends to infinity.

### Stationary-limit consequence

Suppose a sequence of integer-weighted configurations has `E/N->0` and admits a locally finite mass-rooted subsequential limit after the usual normalization. Applying Theorem 4.1 for each fixed observation radius and taking a diagonal subsequence shows that, after deleting vanishing mass, every such rooted limit is supported on a random translate

\[
\tau+\mathbb Z.
\]

This is the precise finite extraction mechanism behind the stationary-lattice assertion in `A-RH-RTD-0002`. It remains conditional on obtaining the ideal long-scale energy `E=o(N)` for the effective on-line Zeta23 modes.

## 5. Overlap stitching

Let an overlap carry weights `q_i>0`, total mass `Q`, and real points `y_i`. Suppose two candidate phases are `tau` and `sigma`, with overlap errors

\[
E_\tau=\sum_iq_i d_{\mathbb T}(y_i-\tau)^2,
\qquad
E_\sigma=\sum_iq_i d_{\mathbb T}(y_i-\sigma)^2.
\]

The torus triangle inequality and `(a+b)^2<=2a^2+2b^2` give:

### Lemma 5.1

\[
\boxed{
Qd_{\mathbb T}(\tau-\sigma)^2
\le2(E_\tau+E_\sigma).}
\tag{5.1}
\]

In particular, exact positive-mass overlap forces exact agreement of zero-error block phases.

For a connected graph of blocks, give block `b` mass `W_b`, and give edge `{b,c}` the overlap mass `Q_bc`. Let `lambda_B` be the corresponding weighted block-graph Poincaré constant. Summing (5.1), applying the chord estimate to `e^{2πi tau_b}`, and repeating the unit-phase projection in Theorem 2.1 gives:

### Theorem 5.2: block-graph phase stitching

There exists a global phase `tau` such that

\[
\boxed{
\sum_bW_b d_{\mathbb T}(\tau_b-\tau)^2
\le
\frac{\pi^2}{\lambda_B}
\sum_{\{b,c\}}
\left(E_{b|bc}+E_{c|bc}\right).}
\tag{5.2}
\]

A long path of blocks has `lambda_B` of order the inverse square of its length, so naive sequential stitching is not uniform. The random-partition local-limit route avoids requiring one phase across the entire finite height window; Theorem 5.2 remains useful for mesoscopic or hierarchical blocks.

## 6. Blockwise two-scale occupancy inequality

The phase may vary from block to block. This does not destroy the ideal two-scale counting argument because the shorter-scale kernel is nonnegative and cross-block terms may be discarded.

Let block `b` carry a cyclic ideal occupancy array

\[
m_{b,1},\ldots,m_{b,d_b}\in\mathbb Z_{\ge0},
\qquad
N_b=\sum_nm_{b,n}.
\]

Set

\[
N=\sum_bN_b,
\qquad
d=\sum_bd_b,
\qquad
\theta=d/N.
\]

For `1/2<=alpha<=1`, put

\[
s_\alpha(n)=\operatorname{sinc}^2(\alpha n),
\qquad
\omega_\alpha=\frac{2\alpha-1}{\alpha^2}.
\]

The periodized cyclic form in block `b` obeys

\[
F_b
\ge
\omega_\alpha\sum_nm_{b,n}^2
+
\left(\frac1\alpha-\omega_\alpha\right)
\frac{N_b^2}{d_b}.
\tag{6.1}
\]

Since `1/alpha-omega_alpha>=0`, Cauchy--Schwarz gives

\[
\sum_b\frac{N_b^2}{d_b}
\ge\frac{N^2}{d}=rac N\theta.
\]

Thus

\[
\boxed{
\sum_bF_b
\ge
\omega_\alpha\sum_{b,n}m_{b,n}^2
+
\left(\frac1\alpha-\omega_\alpha\right)
\frac N\theta.}
\tag{6.2}
\]

For integer occupancies,

\[
\mathbf1_{\{m=1\}}\ge2m-m^2.
\]

Hence, if the blockwise shorter-scale form satisfies

\[
\sum_bF_b
\le
\left(
\frac1{\alpha\theta}
+
\frac{\alpha\theta}{3}
+\varepsilon
\right)N,
\tag{6.3}
\]

then

\[
\boxed{
\frac{s_1}{N}
\ge
2-\frac1\theta
-\frac{\alpha\theta}{3\omega_\alpha}
-\frac\varepsilon{\omega_\alpha}.}
\tag{6.4}
\]

This equals the normalized formula in `A-RH-RTD-0002`; it shows that one global phase and equal block densities are not needed in the cyclic ideal model.

At `alpha=3/4`,

\[
\frac{s_1}{N}
\ge
2-\frac1\theta-\frac{9\theta}{32}-\frac98\varepsilon.
\tag{6.5}
\]

Its gain over the one-scale certificate is again

\[
\frac{5\theta}{96}-\frac98\varepsilon.
\]

## 7. Finite Toeplitz boundary correction

A finite interval is not a cyclic block. This section isolates the exact correction.

Let

\[
K_\alpha(i-j)=\operatorname{sinc}^2(\alpha(i-j))
\]

on indices `1,...,d`, and let `T_d` be the resulting Toeplitz matrix. For an occupancy vector `m`, put

\[
N=\sum_im_i,
\qquad
\mu=N/d,
\qquad
x=m-\mu\mathbf1,
\qquad
V=\|x\|_2^2.
\]

Define the missing row-sum vector

\[
b_i=\frac1\alpha-\sum_{j=1}^dK_\alpha(i-j),
\]

and

\[
B_d=\sum_ib_i,
\qquad
C_d=\sum_ib_i^2.
\]

The full-line convolution symbol is at least `omega_alpha`, so

\[
\langle x,T_dx\rangle\ge\omega_\alpha V.
\]

Expanding `m=mu*1+x` and using `sum x_i=0` gives

\[
\langle m,T_dm\rangle
\ge
\omega_\alpha V
+
\frac{N^2}{\alpha d}
-
\mu^2B_d
-
2\mu\sqrt{C_dV}.
\tag{7.1}
\]

For every `0<rho<omega_alpha`, Young's inequality yields

\[
\boxed{
\langle m,T_dm\rangle
\ge
(\omega_\alpha-\rho)V
+
\frac{N^2}{\alpha d}
-
\mu^2\left(B_d+\frac{C_d}{\rho}\right).}
\tag{7.2}
\]

Using `sinc^2(alpha n)<=1/(pi^2 alpha^2 n^2)` for `n!=0`, for `d>=2` one has the explicit bounds

\[
B_d
\le
\frac{2}{\pi^2\alpha^2}
\left(3+\log(d-1)\right),
\tag{7.3}
\]

\[
C_d
\le
\frac1{9\alpha^4}
+
\frac{2}{3\pi^2\alpha^4}.
\tag{7.4}
\]

Thus fixed-density blocks of length tending to infinity recover the cyclic lower bound with a total boundary loss of order `number_of_blocks * log(block_length)`, provided local block densities are controlled.

## 8. Kernel perturbation from approximate cells

Let

\[
K_\alpha(t)=\operatorname{sinc}^2(\alpha t)
\]

and fix `0<eta<=1/4`. Define

\[
H_{\alpha,\eta}(n)
=
\sup_{|u-n|\le2\eta}|K_\alpha'(u)|.
\]

The derivative decays quadratically, so

\[
H_{\alpha,\eta}\in\ell^1(\mathbb Z).
\]

Suppose, inside one block, every atom has the form

\[
x_a=\tau+n_a+\delta_a,
\qquad
n_a\in\mathbb Z,
\qquad
|\delta_a|\le\eta,
\]

and let `m_n` be the total integer mass assigned to cell `n`. The mean-value theorem and Young's convolution inequality give

\[
\boxed{
\left|
\sum_{a,c}q_aq_cK_\alpha(x_a-x_c)
-
\sum_{n,k}m_nm_kK_\alpha(n-k)
\right|
\le
2\eta\|H_{\alpha,\eta}\|_{\ell^1}
\sum_nm_n^2.}
\tag{8.1}
\]

For `alpha=3/4` and `eta<=1/4`, put `c=3pi/4`. The elementary bounds

\[
|K_\alpha'|\le c
\]

globally and, away from zero,

\[
|K_\alpha'(t)|
\le
\frac2{c t^2}+
\frac2{c^2|t|^3}
\]

give

\[
\|H_{3/4,\eta}\|_1
\le
3c+
\frac{16}{c}\left(\frac{\pi^2}{6}-1\right)
+
\frac{32}{c^2}\left(\zeta(3)-1\right)
<12.613.
\tag{8.2}
\]

Consequently, the coefficient in (8.1) is less than

\[
25.226\,\eta.
\tag{8.3}
\]

If the cell second moment is `O(N)` and the extraction error `eta` tends to zero, the short-scale kernel replacement costs `o(N)`. Combining (7.2) and (8.1) is the finite non-cyclic replacement for the exact periodic calculation.

## 9. Necessary hypotheses and countermodels

### 9.1 Disconnected two-coset model

Take four equal-weight points

\[
0,1,\frac12,\frac32
\]

and connect only `0` to `1` and `1/2` to `3/2`. Every edge difference is an integer, so `E_sinc=0`, but the graph is disconnected and has `lambda_G=0`. The best common phase has squared loss `1/4`.

Thus local zero energy does not produce a global phase without connectedness, overlap, or a local-block interpretation.

### 9.2 Low-gap path model

For `j=0,...,n-1`, take

\[
x_j=j+\frac jn
\]

and connect consecutive vertices. Then

\[
E_{\rm sinc}
=(n-1)\operatorname{sinc}^2(1+1/n)
\asymp n^{-1},
\]

while the path gap is

\[
\lambda_G=2(1-\cos(\pi/n))\asymp n^{-2}.
\]

The phases `j/n` wind around the circle and have best common-phase loss of order `n`. This shows that the factor `1/lambda_G`, or an alternative block-overlap mechanism, is necessary in order.

## 10. Mapping to the Zeta23 route

The finite results now suggest the following narrower contradiction chain.

```text
simple-zero proportion approaches the one-scale lower bound
  => parent rank-trace defect and normalization leakage are o(N)
  => effective on-line long-scale off-diagonal sinc/taper energy is o(N)
  => Theorem 4.1: after deleting o(N) mass, growing blocks are locally close to blockwise lattice cosets
  => assign integer occupancies; block phases need not be globally equal
  => (7.2)+(8.1): finite Toeplitz and positional errors are o(N)
  => blockwise alpha=3/4 lower bound
  => contradiction with the short-scale prime-side upper bound if every remaining loss fits the parent budget
```

The exact unresolved obligations are:

1. derive the **effective on-line** ideal sinc/taper energy `E=o(N)` from the full indefinite `P+Q` near-equality statement;
2. show off-line pair contributions cannot hide a macroscopic on-line short-scale form, using the complete-frame pair inertia and a finite-section stability argument;
3. transfer the smooth Zeta23 taper to the ideal sinc kernel with a quantified loss;
4. control local block densities or charge high-density blocks when summing the Toeplitz boundary term;
5. account for deleted mass, contaminated cells, finite grid, tail, seam and Riemann--von Mangoldt normalization;
6. keep the total normalized loss below
   \[
   \frac{-27\theta^2+128\theta-96}{108\theta}
   \]
   for a fixed reference parameter `theta>(64-4sqrt(94))/27`.

## 11. Authority boundary

This note establishes proof candidates for finite weighted phase synchronization, complete-block extraction, overlap stitching, a blockwise ideal occupancy inequality, a finite Toeplitz correction, and approximate-cell kernel stability.

It does **not** establish:

- the required long-scale on-line energy estimate for actual zeta zeros;
- a uniform lower Riesz bound for growing off-line pair finite sections;
- the short-scale on-line upper bound after separating the indefinite pair term;
- closure of the parent error budget;
- any unconditional improvement in the known zeta-zero proportion;
- a proof or refutation of the Riemann hypothesis.
