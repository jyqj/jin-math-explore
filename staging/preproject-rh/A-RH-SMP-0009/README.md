# A-RH-SMP-0009 — sparse phase mosaics and slow-modulation energy

Status: `solver_proof_candidate`; not independently verified.
Issue #63. Actor/run: `openai-gpt-6-pro / run-20260906-rh-phase-mosaic-09`.
Read-only parent: #58 / A-RH-AOC-0008 at
`1af426358ff62e540e1fdb5702c6dabd8d920dd9`. Date: 2026-09-06.
This is a resumed sequential solver continuation with inherited context.

## 0. Outcome and scope

We extend the parent's single hole-block example to arbitrary touching blocks,
each with its own real phase and bounded imaginary depth. Cross-block
interference is bounded in absolute value; no favorable sign or large gap is
assumed. If the number of blocks J is o(P), then at fixed 0<alpha<=1,

    E_alpha/P = (1/(alpha P)) sum_p m_p^2 + o(1).

The same holds for continuous phase/depth fields with discrete total variation
o(P). At mean mass one and simple fraction s this is (2-s)/alpha+o(1).
For s->2/3, alpha=3/4, the excess over the targeted short budget 19/12 is
7/36+o(1). Thus a whole class of bounded-depth, slowly modulated hole models
is excluded, rather than just one example.

No theorem here says that all near-extremizers have such a representation.
One orbit per unit cell, bounded depth, and sparse interfaces/low variation
are explicit hypotheses. Rapid tangent interlacing has D=0 without low
variation. Three blocks with one growing-depth pair violate the bounded-depth
conclusion. The restricted-class consequence s>=13/16 is not a zeta-zero
bound, a literature record or an RH result. All proofs remain candidates.

## 1. Continuous box model

For p=0,...,P-1 choose

\[
m_p\in\{0,1,2\},\quad 0\le\tau_p<1,\quad 0\le a_p\le A,
\qquad a_p=0\text{ whenever }m_p\ne2.                       \tag{1}
\]

A zero mark means vacancy; mark one is a simple real point at p+tau_p;
mark two is a real double point if a_p=0 and otherwise the multiplicity-one
conjugate pair p+tau_p +/- i a_p/(2pi). These are genuine finite exponential
families. Different cells have different centers, but neighboring centers
may be arbitrarily close. Put N=sum m_p and n=#{p:m_p=1}.

On L2([-alpha/2,alpha/2]) use atoms alpha^(-1/2)exp(2pi i z u). The signed
Hermitian operator has kernel alpha^(-1)K(u-v), where

\[
K(t)=\sum_pm_pe^{2\pi i(p+\tau_p)t}\cosh(a_pt).
\]

Consequently its squared Hilbert--Schmidt norm is exactly

\[
\boxed{E_\alpha=\|\mathsf A_\alpha\|_{HS}^2
=\alpha^{-2}\int_{-\alpha}^{\alpha}(\alpha-|t|)|K(t)|^2dt.} \tag{2}
\]

It is also the finite multiplicity-weighted sum of sinc(alpha(z-w))^2.
Individual terms need not be positive; the entire sum is nonnegative.
Changing alpha restricts an actual continuous support and rescales by alpha;
it does not introduce an artificial independent depth-response channel.

## 2. Single-block finite error

A block of ell consecutive cells with constant (m,tau,a) has kernel
m cosh(at)D_ell(t) times a unimodular phase, where
D_ell(t)=sum_{j=0}^{ell-1}exp(2pi i j t). Define

\[
L_{\alpha,A}=\cosh^2(\alpha A)+\alpha A\sinh(2\alpha A).
\]

For every ell>=1, 0<alpha<=1 and 0<=a<=A,

\[
\boxed{\left|E_\alpha^{\rm block}-\frac{m^2\ell}{\alpha}\right|
\le\frac{m^2L_{\alpha,A}}{\alpha^2}
       \left(\frac12+\log\ell\right).}                    \tag{3}
\]

Proof. Periodize w(t)=(alpha-|t|)_+ cosh^2(at). Its unperiodized Lipschitz
constant is at most L_(alpha,A). At almost every point at most two translates
contribute, so the periodization W is circle-Lipschitz with constant 2L.
Also W(0)=alpha, even when alpha=1, because w(+-1)=0. Orthogonality gives
integral over one period of |D_ell|^2 equal to ell. On [-1/2,1/2],

\[
|D_\ell(t)|\le\min(\ell,(2|t|)^{-1}),\qquad
\int_{-1/2}^{1/2}|t||D_\ell(t)|^2dt\le\frac14+\frac12\log\ell.
\]

The second estimate follows by splitting at 1/(2ell). Multiplying this by
2L m^2/alpha^2 proves (3). The m=0 case is exactly zero. No limiting numerical
fit is used.

## 3. Cross-block cancellation without separation between blocks

Partition the P cells into J nonempty consecutive blocks with constant
(m,tau,a) on each block. Let B=J-1 and

\[
C_{\alpha,A}=\max\{e^{2\alpha A},
              4\cosh^2(\alpha A)/(\pi^2\alpha^2)\}.
\]

For different cells with integer lag r=|p-q|>=1, every individual pair of
multiset members satisfies

\[
|\operatorname{sinc}(\alpha(z-w))|^2\le C_{\alpha,A}/r^2.   \tag{4}
\]

For r=1 use the integral representation of sinc and |Im(z-w)|<=A/pi.
For r>=2, |Re(z-w)|>r-1>=r/2 and |sin(x+iy)|^2<=cosh^2(y), proving (4).
This includes arbitrarily close centers on opposite sides of a cell boundary.

At lag r the number c_r of unordered cell pairs in different blocks obeys
c_r<=min(P-r,Br): at most r pairs cross any specified boundary. When B>=1,
put ell0=ceil(P/B). Harmonic-sum and integral-tail bounds give

\[
\sum_{r=1}^{P-1}\frac{c_r}{r^2}
\le B H_{\ell_0}+P\sum_{r>\ell_0}r^{-2}
\le B\left(2+\log\frac{2P}{B}\right).                     \tag{5}
\]

We used H_ell<=1+log ell, ell0>=P/B and ell0<=2P/B. A cell pair has mass
product at most four; the ordered expansion contributes another factor two.
Therefore

\[
\boxed{\left|E_\alpha-\sum_bE_\alpha^{(b)}\right|
\le8C_{\alpha,A}B\left(2+\log\frac{2P}{B}\right).}         \tag{6}
\]

The right side is zero when B=0. This is an absolute interference bound;
no sign condition, positive gap, common phase or common depth is imposed.

## 4. Sparse-interface theorem

For block lengths ell_b summing to P, Jensen gives sum log ell_b<=J log(P/J).
Define

\[
\begin{split}
\mathcal R_{\alpha,A}(P,J)={}&
\frac{4L_{\alpha,A}}{\alpha^2}J\left(\frac12+\log\frac PJ\right)\\
&+8C_{\alpha,A}(J-1)\left(2+\log\frac{2P}{J-1}\right),
\end{split}                                               \tag{7}
\]

with the second term zero for J=1. Equations (3),(6) prove

\[
\boxed{\left|E_\alpha-\alpha^{-1}\sum_pm_p^2\right|
\le\mathcal R_{\alpha,A}(P,J).}                           \tag{8}
\]

For fixed alpha,A and J/P->0, R/P->0 since x log(1/x)->0. J may tend to
infinity: J=o(P) suffices, not merely J log P=o(P). A growing depth cap can
be inserted in (7), but its actual remainder must then be shown to vanish.

At mean mass N=P, the pointwise identity m^2=2m-1_{m=1} yields, with s=n/P,

\[
\boxed{E_\alpha/P=(2-s)/\alpha+o(1).}                     \tag{9}
\]

In particular D=n+E_1-2N=o(P) for every such sparse bounded-depth mosaic.
If s->2/3 and alpha<1 is fixed, the difference from the *targeted ideal*
short budget 1/alpha+alpha/3 tends to

\[
\boxed{(1-\alpha^2)/(3\alpha);\quad
\alpha=3/4:\ E_\alpha/P\to16/9,\quad\text{excess}=7/36.}   \tag{10}
\]

If that budget is additionally assumed with o(1) error on this restricted
class, it forces liminf s>=1-alpha^2/3, or 13/16 at alpha=3/4. This is not an
actual-zeta bound. The intended use is exclusion of near-2/3 sparse-mosaic
models satisfying the short budget, not promotion of a conditional number.

## 5. Continuous phase/depth perturbation

Consider two fields (tau,a),(tau',a') with identical marks and satisfying
(1), both with cap A. Put

\[
\epsilon_2=P^{-1}\sum_pm_p[(a_p-a_p')^2+4\pi^2(\tau_p-\tau_p')^2].
\]

Then

\[
\boxed{\|\mathsf A_\alpha-\mathsf A_\alpha'\|_{HS}/\sqrt P
\le K_{\alpha,A}\sqrt{\epsilon_2},\qquad
K_{\alpha,A}=\sqrt{2\alpha}\,e^{\alpha(A+\pi)}.}             \tag{11}
\]

Proof. Let V_+,V_- have columns sqrt(m_p/alpha) times
exp(2pi i(p+tau_p)u +/- a_pu). The real integer synthesis map, restricted to
the alpha interval and normalized by alpha^(-1/2), has norm <=alpha^(-1/2).
Expand exp((+-a_p+2pi i tau_p)u) in its norm-convergent power series. Since
|u|<=alpha/2, 0<=tau_p<1 and m_p<=2,

\[
\|V_\pm\|_{op},\|V_\pm'\|_{op}
\le\sqrt{2/\alpha}\,e^{\alpha A/2+\pi\alpha}.
\]

The scalar exponential derivative along the line segment between parameters
gives

\[
\|V_\pm-V_\pm'\|_{HS}
\le(\alpha/2)e^{\alpha A/2}\sqrt{P\epsilon_2}.
\]

The complex parameter difference has squared magnitude (delta a)^2+
4pi^2(delta tau)^2; its real part along the segment is bounded by A|u|.
Finally A_alpha=(V_+V_-^*+V_-V_+^*)/2. Expand the four product differences,
placing one factor in HS norm and the other in operator norm. This proves
(11), with no P-dependent constant. Supplied cell indexing and bounded depth
remain hypotheses; no matching is extracted here.

## 6. Low-total-variation theorem

Using the supplied representatives tau_p in [0,1), define ordinary variation

\[
\mathcal V_P=\sum_{p=0}^{P-2}
 [\mathbf1_{m_{p+1}\ne m_p}+|a_{p+1}-a_p|
                         +2\pi|\tau_{p+1}-\tau_p|].       \tag{12}
\]

This is not a minimization over hidden matchings or arbitrary permutations.
For any 0<eta<1, a greedy partition gives a step field with unchanged marks,
J<=min(P,1+V_P/eta), and within-block distance |delta a|+2pi|delta tau|<=eta.
Start a new block whenever the next edge would make accumulated variation
exceed eta. Each cut consumes a disjoint amount >eta, while a mark change
has cost at least one and forces a cut. This proves the block count and
within-block bound, including jump edges.

Let rho=N/P<=2 and E_alpha^0 be the step-field energy. Then epsilon_2<=rho eta^2.
Write r=K_(alpha,A)sqrt(rho)eta, e=R_(alpha,A)(P,J)/P, and
t=(alpha P)^(-1)sum m_p^2. Equation (8) and the norm difference estimate imply

\[
\boxed{|E_\alpha/P-t|\le e+2r\sqrt{t+e}+r^2.}             \tag{13}
\]

Indeed | ||A||^2-||A0||^2 |<=2||A0||||A-A0||+||A-A0||^2.
If V_P/P->0 at fixed A,alpha, choose eta->0 with V_P/(P eta)->0; for example
eta=(V_P/P)^(1/3) when 0<V_P/P<1. Zero variation is handled as one block.
Then J/P,e,r all tend to zero, proving (9)-(10) for continuous bounded
phase/depth fields, without a finite alphabet assumption.

A finite residual form is also useful. If an observed normalized operator
is at HS distance <=r sqrt(P) from a step-field comparison and has energy
budget B=1/alpha+alpha/3+u, then

\[
\boxed{\sqrt{\max(0,t-e)}\le\sqrt B+r.}                  \tag{14}
\]

This separates geometric approximation from an observed moment bound.
Other fitting, deleted-energy, smooth-profile or arithmetic errors require
separate estimates. Small long-scale defect is not a substitute for (12).

## 7. Essential scope guards

### 7.1 Long-scale equality does not imply low modulation

Repeat the real tangent word (1,1,1,1,2,0) on the integer lattice with
P divisible by six and a=tau=0. Orthogonality gives E_1=4P/3, n=2P/3 and
D=0 exactly. But the ordinary mark variation is P/2-1, of positive density.
Thus the extra hypothesis V_P/P->0 does not follow from long-scale equality.
The checker records its finite short moment; it is not offered as satisfying
the short budget. Dense microscopic interlacing remains a distinct frontier.

### 7.2 Three blocks do not suffice without a depth cap

Take P-2 simple integer sites 0,...,P-3, a vacancy at P-2, and a single pair
at P-1 with depth a_P=log P. It has only three blocks and total mass P.
The pair alone has exact short energy

\[
E_\alpha^{\rm pair}=2+2[\sinh(\alpha a_P)/(\alpha a_P)]^2.
\]

The simple integer block has 0<=A_simple<=I/alpha and trace P-2, because its
full synthesis map is an isometry and restriction is a contraction. Hence
||A_simple||^2<=(P-2)/alpha. The reverse triangle inequality gives

\[
E_\alpha/P\ge P^{-1}
 [\sqrt{E_\alpha^{\rm pair}}-\sqrt{(P-2)/\alpha}]_+^2.
\]

For fixed alpha>1/2 this tends to infinity: sqrt(E_pair) is asymptotic to
P^alpha/(sqrt(2)alpha log P), dominating sqrt(P). Yet sum m_p^2/(alpha P)
tends to 1/alpha. The bounded-depth asymptotic cannot be extended merely
because the number of blocks is small. Small exceptional pair count also
fails to control exceptional HS energy. This is a finite exponential example,
not a zeta-zero multiset.

## 8. Source boundary and reproduction

Lamzouri arXiv:2609.02882v1 Proposition 2.1 supplies the finite signed-form
context, not the cell representation, depth cap or low variation assumed
here. The proofs are elementary Fourier/Fejer and operator estimates; no
literature-wide novelty is asserted. No general decomposition of near
extremizers into these phases has been proved. Extensive microscopic
interlacing, multiple orbits per cell, unbounded depths, exceptional operator
energy and source localization remain outside the result.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python check_phase_mosaic.py --samples 120 --output validation.json
```

The checker uses exact integer/Fraction lag counts for all partitions of
2..9 cells, 120 seeded finite mosaics/perturbations, separate continuous-kernel
quadrature, varying-depth and growing-block families, and high-precision
scope guards. Floating quadrature is not interval certification. All-size
claims rely on the proofs above, not sampled extrapolation.

The first execution completed before a runtime reset, but its uncommitted
local files did not survive. The source and proofs were recovered from the
retained record, then the complete checker was re-executed in the restored
runtime; validation.json is that actual recovery output. This is a justified
recovery rerun, not independent verification. Parent hashes were rechecked.
No full repository CI, bundled inventory/record runner or upstream Lean build
was executed. Local Python, NumPy and mpmath were live checked; Mathematica
and Sage command-line executables were not on PATH. Package-local integrity
checks are separate from proof verification.
