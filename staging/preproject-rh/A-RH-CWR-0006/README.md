# A-RH-CWR-0006: cyclic-wrap obstruction, spectral rounding, and local matching

Status: `solver_proof_candidate`; no independent verification.
Issue: #48. Read-only parent: #45 / A-RH-CTP-0005 at
`75ad472d97ed52b0fa8978b177fbe3ed98b592b7`.
Actor/run: `openai-gpt-6-pro / run-20260905-rh-cyclic-wrap-06`.
Date: 2026-09-05. This additive successor preserves every predecessor file.

## 0. Outcome and scope

The parent's projection remainder does not, by itself, recover the arithmetic
structure needed for the short-window occupancy floor. We give an exact
countermodel which is already Hermitian Toeplitz, has constant diagonal one
and spectrum in {0,1,2}, has zero projection remainder, and meets **every**
rectangular scalar second-moment budget. Its eigenvalue-one multiplicity is
exactly 2P/3. This refutes a relaxed projection-compression implication, not
Lamzouri's proposition, the parent's grid theorem, or RH.

The missing structure is quantified by cyclic-wrap consistency. An explicit
circulantization and spectrum-preserving rounding lemma repairs the relaxed
implication when this additional error is controlled. We also obtain a finite,
quantitative all-real local phase/matching lemma with collision cleanup. Its
input is a positive local sinc energy, not the global signed zero defect.

No actual-zeta matching, high-depth estimate, source normalization, or
unconditional zero proportion is established here. No literature-wide novelty
is asserted. All universal statements below have analytic arguments; finite
tests supplement those arguments but do not independently verify them.

## 1. Exact far-lag countermodel: even Toeplitz and all scales are insufficient

Let P=6k with k>=1 and n=5k. Define the real symmetric Toeplitz matrix

\[
T_{ij}=\mathbf 1_{\{|i-j|=n\}},\qquad Q=I_P+T,
\quad 0\le i,j<P.                                           \tag{1}
\]

Because n>P/2, T consists of k disjoint two-vertex edges, plus P-2k isolated
vertices. On each edge its eigenvalues are +1 and -1. Consequently

\[
\operatorname{spec}(Q)=\{0^{[k]},1^{[4k]},2^{[k]}\},\quad
\operatorname{tr}Q=P,\quad \|Q\|_F^2=4P/3,
\quad Q(Q-I)(Q-2I)=0.                                      \tag{2}
\]

It has constant physical diagonal one and 0<=Q<=2I. Let U,E,F be its 2-, 1-,
0-eigenspaces and set N_1=dim(E)=4k. With A=Q, every hypothesis of the parent's
finite projection remainder is satisfied, with

\[
N_1+\|A\|_F^2-2\operatorname{tr}A=0,\qquad A=2P_U+P_E.      \tag{3}
\]

It also has an abstract positive unit-atom representation: one atom of weight
two on (e_j+e_(j+n))/sqrt(2) for each edge, and one simple unit atom on each
isolated coordinate. These atoms are **not** asserted to be exponential
vectors from a zeta configuration.

Let R select any d consecutive coordinates, alpha=d/P. The exact unit-atom
normalized compression satisfies

\[
\frac{\|\alpha^{-1}RQR^*\|_F^2}{P}
=\frac1\alpha+\frac{2(\alpha-5/6)_+}{\alpha^2}.              \tag{4}
\]

For alpha<=5/6 the centered compression is zero. For 5/6<=alpha<=1,

\[
6\alpha-5\le\alpha^3,
\quad \alpha^3-6\alpha+5=(1-\alpha)(5-\alpha-\alpha^2)\ge0.
\]

Thus, for **all integer d=1,...,P**, and indeed for the continuous expression,

\[
\boxed{\frac{\|\alpha^{-1}RQR^*\|_F^2}{P}
\le\frac1\alpha+\frac\alpha3.}                            \tag{5}
\]

For P divisible by 12 and alpha=3/4, RQR*=I_d. In particular, the ordinary
integer-occupancy lower bound

\[
\frac{\|\alpha^{-1}RQR^*-I_d/\alpha\|_F^2}{P}
\ge\frac{2\alpha-1}{\alpha^2}(1-N_1/P)
\]

is false for this projection: its two sides are 0 and 8/27 at alpha=3/4.
The parent's theorem assumed a much narrower Fourier-atom occupancy model;
there is no contradiction with that theorem.

**Retained no-go:** constant diagonal, bounded integral spectrum, exact
Toeplitz structure, zero projection remainder and all rectangular moment
budgets do not by themselves improve N_1/P=2/3. More geometry is necessary.

## 2. Measure the missing wrap relation exactly

Let S be the cyclic coordinate shift and define the Hilbert--Schmidt
orthogonal projection onto circulant matrices

\[
\mathcal C(A)=\frac1P\sum_{r=0}^{P-1}S^rAS^{-r}.
\]

For Hermitian Toeplitz A with lower-diagonal coefficients t_n, its circulant
coefficient on residue n is

\[
c_n=\frac{(P-n)t_n+n\overline{t_{P-n}}}{P},\quad1\le n<P.
\]

Taking the weighted variance on each cyclic diagonal gives the exact identity

\[
\boxed{\|A-\mathcal C(A)\|_F^2
=\sum_{n=1}^{P-1}\frac{n(P-n)}P
 |t_n-\overline{t_{P-n}}|^2.}                              \tag{6}
\]

Write w(A)=||A-C(A)||_F/sqrt(P). An integer Fourier occupancy matrix satisfies
these wrap identities exactly, whereas an arbitrary Toeplitz matrix need not.
For the countermodel (1),

\[
\boxed{w(Q)^2=5/18.}                                      \tag{7}
\]

There are two nonzero mismatches, at residues k and P-k. This value is
unchanged by a global lattice phase: after conjugation by
D_tau=diag(exp(2*pi*i*tau*j/P)), (6) replaces its gap by

\[
t_n-e^{2\pi i\tau}\overline{t_{P-n}}.
\]

One member of each mismatched pair is zero in (1), so no tau repairs it.
This phase version describes twisted circulants and Fourier atoms on a
translated lattice. We do not require a global phase for actual zeros.

### One small normalized commutator is insufficient

Direct boundary calculation for Toeplitz A gives

\[
\|SA-AS\|_F^2=2\sum_{n=1}^{P-1}|t_n-\overline{t_{P-n}}|^2,
\qquad w(A)^2\le\tfrac18\|SA-AS\|_F^2.                    \tag{8}
\]

The norm on the right is **unnormalized**. In (1), it equals 4, so its division
by P tends to zero while w(Q)^2 stays 5/18. Thus a rank-small boundary
commutator, or normalized one-step shift error o(1), does not establish the
needed cyclicity. The exact averaged-shift identity is

\[
\boxed{w(A)^2=\frac1{2P^2}
\sum_{r=0}^{P-1}\|A-S^rAS^{-r}\|_F^2.}                    \tag{9}
\]

Equations (6),(8),(9) give three precise versions of the missing input.

## 3. Spectrum-preserving repair: from near-cyclic projections to occupancy

Let Q be Hermitian with eigenvalues in {0,1,2}. There is a Hermitian circulant
matrix M with exactly the **same eigenvalue multiset** such that

\[
\boxed{\|Q-M\|_F^2\le2\|Q-\mathcal C(Q)\|_F^2.}           \tag{10}
\]

Proof. In the Fourier basis, C(Q) is diagonal with real entries beta_j. Assign
the eigenvalues lambda_j of Q to these positions in the same sorted order and
let M be the resulting Fourier-diagonal matrix. The Hermitian spectral
matching inequality gives

\[
\|\mathcal C(Q)-M\|_F^2
=\sum_j(\beta_j-\lambda_{\pi(j)})^2
\le\|\mathcal C(Q)-Q\|_F^2.
\]

For completeness, this inequality follows from a short rearrangement
argument: squared overlaps of two orthonormal eigenbases form a doubly
stochastic matrix; its linear trace pairing is at most the largest
permutation pairing. Expand ||B-Q||_F^2 and choose the maximizing permutation.
This is the classical Hermitian Hoffman--Wielandt mechanism, not a new
spectral inequality. Finally Q-C(Q) is orthogonal to every circulant matrix,
so Pythagoras proves (10).

If tr Q=P and the multiplicity of eigenvalue one is N_1, M is exactly a
Fourier occupancy matrix with marks m_j in {0,1,2}, sum m_j=P, and N_1 simple
marks. Independent rounding to the closest of {0,1,2} would not preserve
these counts; the sorted assignment above does.

### More general source-to-occupancy estimate

Suppose A is Hermitian, Q has the stated target spectrum, and

\[
r=\|A-Q\|_F/\sqrt P,\qquad w=\|A-\mathcal C(A)\|_F/\sqrt P.
\]

Apply the same sorted assignment to C(A) and the eigenvalues of Q. Then

\[
\boxed{\frac{\|A-M\|_F^2}P\le w^2+(r+w)^2.}              \tag{11}
\]

Indeed, ||C(A)-M||_F<=||C(A)-Q||_F<=(r+w)sqrt(P), and the other orthogonal
component has squared norm P w^2. If A is Toeplitz with diagonal one and
tr Q=P, both A and M have diagonal one, so A-M is zero-diagonal Toeplitz.
The parent's sharp consecutive-compression bound is therefore applicable:

\[
\frac{\|\alpha^{-1}R(A-M)R^*\|_F}{\sqrt P}
\le\frac{\sqrt{(d-1)/(P-1)}}\alpha
       \sqrt{w^2+(r+w)^2}
\le\frac1{\sqrt\alpha}\sqrt{w^2+(r+w)^2}.                 \tag{12}
\]

A single global phase may be added by the diagonal-unitary conjugation in
Section 2. The source-dependent choice of local phases is not solved here.

## 4. Conditional two-scale ledger with the new cyclicity term

Assume precisely the finite hypotheses just stated, tr Q=P, and write
s=N_1/P, x=s-2/3. Suppose in addition that a projection comparison has given

\[
r^2\le x+u_1,\qquad u_1\ge0,
\]

and the centered short moment satisfies

\[
\|\alpha^{-1}RAR^*-I_d/\alpha\|_F^2/P\le\alpha/3+u_2,
\qquad u_2\ge0.
\]

These are conditional inputs. In particular, the parent's source projection
need not automatically have tr Q=P or eigenvalue-one multiplicity equal to
the original number of simple zeros. Rank and trace deficits must be charged
before applying this exact version.

The Fourier occupancy floor for M and (12) imply

\[
\boxed{\sqrt{f_\alpha(1/3-x)}
\le\sqrt{\alpha/3+u_2}
 +\frac{\sqrt{w^2+(\sqrt{x+u_1}+w)^2}}{\sqrt\alpha},
\quad f_\alpha=\frac{2\alpha-1}{\alpha^2},\quad\alpha>1/2.} \tag{13}
\]

No nonnegative-x assumption is made when errors are nonzero; x+u_1>=0 is
part of the preceding bound and s<=1 makes the left square root legitimate.
At w=0 and zero budget errors, this recovers the parent's sufficient gain
(sqrt(106)-9)^2/1200 for alpha=3/4. We claim no new numerical zero bound.

At s=2/3, r=0, alpha=3/4 and u_2=0, a necessary condition is

\[
\boxed{w^2\ge\omega_*=\frac{59-24\sqrt6}{288}
=0.000736965879179602928\ldots.}                           \tag{14}
\]

This follows from sqrt(8/27)<=1/2+sqrt(8/3)w. It quantifies the additional
cyclicity input which would exclude a zero-remainder 2/3 configuration.
The explicit countermodel has w^2=5/18, far above this threshold.

## 5. An actual local extraction lemma, restricted to real atoms

Let x_i be a nonempty finite family of real points in an interval of diameter
R. Give each point a mass m_i in {1,2}, with W=sum m_i. Repeated locations
may be represented by distinct atoms; their cross energy is retained. Put

\[
E_B=\sum_{i\ne j}m_i m_j\operatorname{sinc}(x_i-x_j)^2,
\qquad\operatorname{sinc}(t)=\frac{\sin\pi t}{\pi t},
\quad\operatorname{sinc}(0)=1.                            \tag{15}
\]

For 0<h<1/4, there is a phase tau and a retained subfamily with distinct
nearest-integer labels in tau+Z, each at displacement at most h, such that

\[
\boxed{W_{\rm discarded}
\le\left(\frac{\pi^2 R^2}{4Wh^2}
          +\frac1{2\operatorname{sinc}(2h)^2}\right)E_B,}  \tag{16}
\]

and the retained displacement sum is at most

\[
\boxed{\sum_{i\rm\ retained}m_i
 |x_i-(\tau+n_i)|^2\le\frac{\pi^2R^2}{4W}E_B.}            \tag{17}
\]

Proof. With d_T the circle distance to Z, sin(pi*d_T)>=2*d_T gives

\[
d_T(x_i-x_j)^2\le\tfrac14\sin^2(\pi(x_i-x_j))
\le\tfrac{\pi^2R^2}4\operatorname{sinc}(x_i-x_j)^2.
\]

Average the weighted phase cost sum_i m_i d_T(x_i-x_j)^2 over pivot j with
probability m_j/W. Some pivot tau=x_j has cost at most pi^2 R^2 E_B/(4W).
Remove points farther than h; their mass is at most this cost divided by h^2.

Among the remaining points, those with the same nearest lattice label differ
by at most 2h. On this interval sinc^2 is at least sinc(2h)^2. For each cell
retain one atom of maximum mass M_c and remove the others. Since M_c>=1, the
ordered cross mass involving this retained atom is at least twice the removed
mass. Thus total collision-removal mass is at most E_B/[2 sinc(2h)^2]. This
proves (16), while retaining a subfamily can only decrease the phase cost,
which proves (17). At R=0 the phase cost is zero and the collision estimate
still applies.

This supplies the all-real *local* matching hypothesis needed by the parent's
perturbation lemma after suitable embedding in a local finite model. It does
not select one global phase; does not preserve exact mean mass one by itself;
and does not infer E_B from a global signed off-line defect. Those are genuine
remaining steps, not tacit assumptions.

### Discarded count versus discarded operator energy

For a positive discarded atom operator H=sum_i m_i v_i v_i* with ||v_i||=1,
if a Bessel upper bound H<=B I has actually been proved, then

\[
\boxed{\|H\|_F^2\le B\operatorname{tr}H=B W_{\rm discarded}.}\tag{18}
\]

The bound follows eigenvalue by eigenvalue. Without uniform B, small mass
fraction alone is insufficient: in ambient dimension P=k^2, discard k
collinear unit atoms. Their fraction is 1/k but ||H||_F^2/P=1. Signed atoms
require separate positive/negative energy control. This prevents silently
turning the deletion estimate (16) into a negligible source matrix error.

## 6. What was advanced, and what remains

The relaxed lattice-free branch now has an exact obstruction even after adding
Toeplitz and all rectangular scalar budgets. Its repair is no longer phrased
as an unspecified projection-compression principle: it is the measurable
cyclic-wrap error (6), plus the explicitly stated spectrum/rank bookkeeping.
The elementary local matching lemma gives a quantitative positive result for
real positive atoms, including collisions. Neither result proves actual zero
lattice extraction.

The next source obligations are to derive a local cyclic-wrap or positive
sinc-energy estimate from the true signed zero form; handle loss of rank,
trace, multiplicity and exceptional Bessel control; and transfer through the
actual windows with all normalizations. Counting these obligations is not a
measure of distance to a proof of RH. No previously reported conditional
constant is promoted to an unconditional record.

## 7. Reproduction

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python check_cyclic_wrap.py --samples 120 --max-period 120 --output validation.json
```

The checker separates exact integer/rational finite tests from floating-point
regression. Its output is captured in validation.json. The all-P and all-alpha
countermodel proof is Section 1, not extrapolation from the finite checks.
All analytic statements remain candidates pending a context-isolated audit.
The parent's hashes were checked. No full repository CI, upstream Lean build,
independent verifier or source theorem reconstruction was run. Direct git
access failed DNS resolution; GitHub persistence uses the connected API.
