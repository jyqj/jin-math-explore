# A-RH-PER-0010 — periodic rigidity and quantitative phase locking

Status: `solver_proof_candidate`; not independently verified.
Issue #67. Actor/run: `openai-gpt-6-pro / run-20260906-rh-periodic-rigidity-10`.
Date: 2026-09-06. Read-only parent: #63 / A-RH-SMP-0009 at
`a97c80778bda2c5a337be978ccc9afec36b750ea`.

## 0. Outcome and scope

This successor treats exactly repeated finite patterns, including positive
interface density and arbitrary within-period phase/depth changes. It does
not assume the parent's low-variation condition. The representation still
has one aggregate orbit per supplied unit cell, marks 0/1/2 and mean mass one. Quantitative anchor estimates additionally need a positive
simple fraction. A finite depth cap is used quantitatively.

We derive an exact finite spectral formula for infinite repetition, then
obtain a period-dependent phase/depth locking estimate from signed-defect
slack. No separate minimum center gap is assumed: parity coloring of the
supplied cells gives a Bessel bound. Rounding collisions are aggregated,
not discarded or silently assumed absent. A direct Q-by-Q reconstruction also proves that at zero long-scale defect
every fixed-period pattern is a real common-coset pattern, even if s=0.
Its short moment has the integer-occupancy floor, excluding the near-2/3
zero-defect configuration at alpha=3/4 by at least 5/108.

The quantitative estimate degrades with period Q. At fixed depth cap it
excludes sequences with simple fraction tending to 2/3, short budget error
vanishing, and Q^2 times long defect tending to zero. It is not a theorem
for arbitrary growing periods, aperiodic interlacing, actual zeta zeros, or
an unconditional zero-proportion improvement. No literature-wide novelty is
asserted. Tests do not independently verify the proofs.

## 1. Model and exact periodic moment

Fix integer Q>=1. For r=0,...,Q-1 let

    m_r in {0,1,2}, 0<=tau_r<1, 0<=a_r<=A,
    a_r=0 if m_r!=2, sum_r m_r=Q.

A zero mark is vacant, mark one is a simple real point, and mark two is a
real double point when a_r=0 or a multiplicity-one conjugate pair otherwise.
Repeat this pattern at centers lQ+r+tau_r, l=0,...,M-1. The pair members are
at center +/- i a_r/(2pi). Distinct cells have distinct centers. Put
n0=#{r:m_r=1}, s=n0/Q, and assume s>0 whenever an anchor is used.

On the continuous interval [-alpha/2,alpha/2], 0<alpha<=1, normalize atoms by
alpha^(-1/2). Define

\[
B(t)=\sum_{r=0}^{Q-1}m_r e^{2\pi i(r+\tau_r)t}\cosh(a_rt),
\qquad b_j=B(j/Q)/Q.
\]

The finite signed operator has kernel alpha^(-1)B(u-v)D_M(Q(u-v)), where
D_M(v)=sum_{l=0}^{M-1}exp(2pi i l v). Consequently

\[
E_{\alpha,M}=\alpha^{-2}\int_{-\alpha}^{\alpha}
 (\alpha-|t|)|B(t)|^2|D_M(Qt)|^2\,dt.                    \tag{1}
\]

The exact limiting moment per total mass is

\[
\boxed{\mathcal L_\alpha:=\lim_{M\to\infty}\frac{E_{\alpha,M}}{MQ}
=\frac1\alpha+\frac2{\alpha^2}\sum_{1\le j<\alpha Q}
 (\alpha-j/Q)|b_j|^2.}                                  \tag{2}
\]

An integer endpoint j=alpha Q has zero weight and may be included. The
formula is not a quadrature or a sampled approximation to the limit.
To prove it, set w(t)=(alpha-|t|)_+|B(t)|^2 and periodize
W(v)=sum_{k in Z} w((v+k)/Q). Changing variables in (1) gives
E/(MQ)=(alpha^2 M Q^2)^(-1) integral_0^1 W(v)|D_M(v)|^2 dv.
The Fejer kernel |D_M|^2/M converges to a point mass on the circle, so the
limit is W(0)/(alpha^2 Q^2). Use B(0)=Q and |B(-t)|=|B(t)|.

Here is an explicit finite error. Write c=cosh(alpha A), h=sinh(alpha A),

\[
H=c^2+2\alpha c(2\pi Qc+Ah),\qquad
F_{Q,\alpha,A}=\frac{(2\lceil\alpha Q\rceil+2)H}{\alpha^2Q}.
\]

Then

\[
\boxed{\left|\frac{E_{\alpha,M}}{MQ}-\mathcal L_\alpha\right|
\le F_{Q,\alpha,A}\frac{1/4+(\log M)/2}{M}.}             \tag{3}
\]

Indeed |B|<=Qc, |B'|<=Q(2pi Qc+Ah), and w is globally Lipschitz with
constant Q^2 H. At any circle point at most 2 ceil(alpha Q)+2 translates
contribute to W', giving Lip(W)<=(2 ceil(alpha Q)+2)QH. Finally
integral_{-1/2}^{1/2}|v||D_M(v)|^2 dv<=1/4+(log M)/2, by splitting
|D_M(v)|<=min(M,1/(2|v|)) at 1/(2M). This proves (3), including alpha=1.
The bound is deliberately coarse and not uniform when Q or A grows.

The finite signed Hilbert inequality gives D_M=Mn0+E_{1,M}-2MQ>=0.
Therefore

\[
\boxed{\delta:=\lim_{M\to\infty}D_M/(MQ)=s+\mathcal L_1-2\ge0.} \tag{4}
\]

## 2. One-cell geometry supplies the Bessel input

A finite set with one center p+tau_p in every occupied integer cell can be
split by the parity of p into two 1-separated sets. Each q-separated real
exponential family on [-1/2,1/2] has Bessel bound 2+2/(3q^2): majorize the
box indicator by 2(1-|u|)_+, whose Fourier transform is 2 sinc(x)^2, and
bound row sums using sum_{k>=1}k^(-2)=pi^2/6. Thus every subset of these
cell centers has real synthesis squared operator norm at most

\[
B_*=2(2+2/3)=16/3.                                       \tag{5}
\]

Neighboring centers may be arbitrarily close. No q-separated-pair assumption
is imported from the parent anchor theorem. The supplied one-cell indexing,
however, is indispensable in this argument.

We recall and justify precisely the finite signed slack used next. Let S be
the sum of simple unit atoms, P_+ the positive part supplied by non-simple
real atoms and pair g vectors, N_- the sum of the negative pair h atoms,
and Aop=S+P_+-N_-. Let U=ran(P_+), E=span((I-P_U)f_i), and F=(U+E)^perp.
Set Qop=2P_U+P_E, nu=total non-simple mass,
xi=tr(P_U S), zeta=tr((I-P_U)N_-), zeta_F=tr(P_FN_-).
Expansion of the square gives

\[
D=\|Aop-Qop\|_{HS}^2+2(\nu-2\dim U)+2\xi+2\zeta
 +2\zeta_F+(n-\dim E).                                  \tag{6}
\]

All terms on the right are nonnegative. For the simple coefficient Gram
matrix Gamma, polar-factor V_E=(V_EV_E^*)^(1/2)W with WW*=I_E gives

    Gamma-I = Z+B-C,
    ||Z||_HS^2<=D, B,C>=0, tr(B+C)<=D.

In detail Z=W*P_E(Aop-Qop)P_EW,
B=V*P_UV+W*P_EN_-P_EW, C=I-W*W. Compression and (6) prove the bounds.
Since Gamma<=B_* I, X=Gamma-I obeys ||X||op<=B_*-1=13/3. Trace pairing
with the displayed decomposition yields
||X||HS^2<=||X||HS sqrt(D)+(13/3)D. Thus

\[
\boxed{E_{ss}:=\sum_{i\ne j\ {\rm simple}}
 \operatorname{sinc}(x_i-x_j)^2\le7D.}                  \tag{7}
\]

For D=0 the conclusion is immediate. For D>0, 7-sqrt(7)-13/3>0
because (8/3)^2>7, so the positive quadratic root is below sqrt(7).
This is raw simple energy, without deletion, under the one-cell Bessel input.

All non-simple marks here have mass two. Combine real doubles (depth zero)
and pairs as columns sqrt(2)g and sqrt(2)h. The varying-depth power series
bound, using (5), gives

    C_g=2B_* cosh(A/2)^2, C_h=2B_* sinh(A/2)^2.

For simple synthesis V and these maps G,H, splitting H into U and its
orthogonal complement gives

    ||V*G||HS^2+||V*H||HS^2
      <=(C_g+C_h)xi+B_*zeta+2sqrt(C_h B_* xi zeta).

Use xi+zeta<=D/2 from (6). The largest two-by-two eigenvalue is

\[
\Lambda_A=\frac{B_*}{2}
 [2\cosh A+1+\sqrt{4\cosh^2 A-3}],\qquad C_A=7+\Lambda_A/2.
\]

Hence the sum T of (7) and the positive simple-to-non-simple cross energy
obeys

\[
\boxed{T\le C_A D.}                                     \tag{8}
\]

Every non-simple target has mass two in this cross energy. This is not a
pointwise positivity assertion for the original complex squared-kernel sum.

## 3. Quantitative locking of an entire period

For any real separation d and target depth a,

\[
\kappa(d,a)=|\operatorname{sinc}(d+ia/(2\pi))|^2
=\frac{\sin^2(\pi d)+\sinh^2(a/2)}{\pi^2d^2+a^2/4}.       \tag{9}
\]

This equals the sum of the squared simple-to-g and simple-to-h correlations;
for a=0 it is the real sinc square. Interpret the removable origin by one.
For two centers within one period, |d|<Q. Set

\[
D_0=\pi^2Q^2+A^2/4,\qquad
\eta=\frac{C_A D_0}{sQ}\,\delta.
\]

Since sin(pi d)^2>=4 dist(d,Z)^2 and sinh(a/2)^2>=a^2/4, summing only
same-period terms in the positive energy (8), then dividing by the number
of repetitions and using (4), gives

\[
\sum_{i\ {\rm simple\ in\ one\ period}}\sum_p m_p
 [4\operatorname{dist}(t_p-t_i,\mathbb Z)^2+a_p^2/4]
 \le D_0 C_A Q\delta.                                   \tag{10}
\]

The self simple term has zero cost. Positivity justifies discarding all
other-period contributions; no cancellation is discarded from a signed sum.
Choose an anchor i whose cost is no more than the average of the n0=sQ
anchors. Let theta=t_i mod 1, and round each center t_p=p+tau_p to a nearest
point theta+k_p of this coset. Let e_p=t_p-theta-k_p. Then

\[
E_{\rm ph}=Q^{-1}\sum_p m_pe_p^2,\quad
E_{\rm dep}=Q^{-1}\sum_p m_pa_p^2,
\qquad
\boxed{4E_{\rm ph}+E_{\rm dep}/4\le\eta.}                \tag{11}
\]

The bound accounts for every occupied cell, not merely selected covered
pairs. The gain over the predecessor is exact periodic repetition: each
period contains an anchor, and its diameter Q bounds the distance. The cost
therefore deteriorates with Q. At bounded A and s bounded away from zero,
eta=O_A(Q delta).

## 4. Collision-safe rounding and the short comparison

Round all depths to zero as well. Several rounded centers may coincide
modulo Q. Aggregate, rather than delete, their nonnegative integer masses:

    M_j=sum_{p:k_p=j mod Q} m_p,  j=0,...,Q-1.

Then sum M_j=Q and sum M_j^2>=sum m_p^2=(2-s)Q. We do not assume M_j<=2 or
that the original simple count is preserved after rounding. The inequality
for squared masses is the only count fact needed below.

Put k_A=(cosh A-1)/A^2 for A>0 and k_0=1/2. For 0<=t<=1,
cosh(a t)-1<=k_A a^2 by the nonnegative power series. Let b_j^0 be the
sampled coefficient of the rounded real configuration. Equations (11) and
|exp(ix)-exp(iy)|<=|x-y| imply

\[
|b_j-b_j^0|\le2\pi\sqrt{E_{\rm ph}}+k_AE_{\rm dep}
\le\pi\sqrt\eta+4k_A\eta,\qquad 1\le j<Q.              \tag{12}
\]

No factor cosh(A) is needed in the phase term: first subtract the unshifted
real exponential, then remove depth. The total mass divided by Q is one.
The nonzero spectral weights in (2) have sum at most Q, since their sum is
bounded by the integral of the decreasing triangular weight. Both the
original and rounded zero modes contribute 1/alpha. Therefore

\[
\boxed{\left|\sqrt{\mathcal L_\alpha-1/\alpha}
 -\sqrt{\mathcal L_\alpha^0-1/\alpha}\right|
\le r_Q:=\sqrt Q(\pi\sqrt\eta+4k_A\eta).}               \tag{13}
\]

For alpha>1/2, the real integer occupancy Fourier formula gives

\[
\mathcal L_\alpha^0=\frac1\alpha+
 \sum_{j=1}^{Q-1}F_\alpha(j/Q)|\widehat M(j)|^2,
\quad F_\alpha(t)=\frac{(\alpha-t)_++(\alpha-1+t)_+}{\alpha^2}.
\]

Here Mhat(j)=Q^(-1)sum_p M_p exp(2pi i pj/Q). Pairing conjugate frequencies
proves the formula even when alpha Q is not an integer. Since
F_alpha>=f_alpha=(2alpha-1)/alpha^2, Parseval and the squared-mass inequality
imply

\[
\boxed{\sqrt{f_\alpha(1-s)}
\le\sqrt{\mathcal L_\alpha-1/\alpha}+r_Q.}               \tag{14}
\]

This tolerates rounding collisions exactly. For bounded A,s>=s0>0,

    r_Q=O_A,s0(Q sqrt(delta)+Q^(3/2)delta).

Thus Q^2 delta -> 0 implies r_Q -> 0. Merely delta -> 0 with unrestricted
Q is insufficient for this estimate.

## 5. Equality rigidity and an explicit fixed-period obstruction

There is a sharper qualitative argument which does not need an anchor.
Let u_j=(j-(Q-1)/2)/Q, j=0,...,Q-1, and form Q-dimensional normalized
vectors v_t(j)=Q^(-1/2)exp(2pi i t u_j), with pair g/h columns obtained by
multiplying by cosh(a u_j) and -i sinh(a u_j). Their signed finite matrix is

\[
T_Q(j,k)=B((j-k)/Q)/Q,\qquad
\|T_Q\|_F^2/Q=\mathcal L_1,\qquad
n0+\|T_Q\|_F^2-2Q=Q\delta.                              \tag{15a}
\]

The second identity is direct Toeplitz diagonal counting. Thus the limiting
long defect is exactly a finite signed-Hilbert defect, not an approximation.
Every real vector has norm one; every pair has ||g||^2-||h||^2=1, so (6)
applies to this finite matrix.

All distinct complex-node columns involved are linearly independent. Up to
nonzero column factors they are Vandermonde columns with nodes
exp(2pi i t/Q) for real atoms and exp((2pi i t +/- a)/Q) for pair members.
The centers lie in [0,Q) and are distinct, so these nodes are distinct.
If there are n_d real double sites, their number is Q-n_d<=Q; take the first
Q-n_d rows to obtain a nonsingular Vandermonde minor.

If delta=0, the term zeta=tr((I-P_U)N_-) in (6) is zero. This forces each h column into the
span of the non-simple real columns and the pair g columns. The independence
just proved forbids this for any positive-depth pair. Hence all depths vanish.
For the remaining real vectors the exact defect is the positive sum
sum_{p!=r} m_p m_r |<v_p,v_r>|^2, since n0+sum m_p^2-2Q=0. It can vanish only
when every pair of occupied vectors is orthogonal. The finite geometric sum
vanishes exactly when their distinct real centers differ by an integer not
in QZ. Thus their occupied phases in [0,1) coincide. The converse is immediate.
We have proved, including s=0,

\[
\boxed{\delta=0\ \Longleftrightarrow\
 \text{all occupied depths vanish and occupied phases coincide}.} \tag{15}
\]

No low-variation hypothesis or prespecified small depth cap is used in this
qualitative result. Positive s remains necessary for the quantitative proof
(10)-(14); no quantitative s=0 extension is asserted. The finite Vandermonde
may become very ill-conditioned as period or clustering grows, so (15) alone
is not uniform stability.

At s=2/3 and delta=0, (14) gives

\[
\mathcal L_{3/4}\ge\frac43+\frac89\frac13=\frac{44}{27}
 =\frac{19}{12}+\frac5{108}.                             \tag{16}
\]

Hence no exactly repeated fixed pattern at this simple fraction can have
zero long deficit and satisfy the targeted short budget. This is a model
exclusion, not an actual zeta proportion. It covers the rapid tangent word
which was explicitly outside the parent's low-variation theorem.

A finite positive long-error threshold is also available. At s=2/3 write
h_Q=C_A D_0/((2/3)Q), g=sqrt(8/27)-1/2,
p_Q=pi sqrt(Q h_Q), q_Q=4 k_A h_Q sqrt(Q). If the short budget
L_(3/4)<=19/12 holds, (14) requires

    p_Q sqrt(delta)+q_Q delta >= g.

Thus

\[
\boxed{\delta\ge d_*(Q,A):=
 \left[\frac{2g}{p_Q+\sqrt{p_Q^2+4q_Qg}}\right]^2>0.}   \tag{17}
\]

For Q=6,A=log(2), this conservative threshold is about 2.63e-8. It is not an
optimized bound. As Q grows at fixed A it is of order Q^(-2), showing
explicitly why fixed-period rigidity is not uniform period-free rigidity.
When s=2/3 and a long upper budget is 4/3+u1, delta<=u1, so u1<d_* rules
out the two budgets in this class. Add a short budget error u2 by replacing
g with max(0,sqrt(8/27)-sqrt(1/4+u2)). For general s use (14) directly.

The sequential consequence is useful: for bounded A, s->2/3,
Q^2 delta->0 and u2->0, a short bound L_(3/4)<=19/12+u2 is impossible.
This statement allows Q to grow but imposes an explicit growth/defect tradeoff.
It does not assert the tradeoff for any source configuration.

## 6. Checks and limits of the next step

The checker evaluates (2) against actual finite repetitions and an independent
continuous integral, and tests (10)-(14) including clustered adjacent centers
and rounding collisions. It also scans a stated finite rational phase grid
for period six. Feasible grid samples are not an optimization certificate or
a universal proof. Exact tangent period-six values are computed with
rational cosine values; different pair/vacancy distances yield different
short constants. In particular the original adjacent word has L_(3/4)=398/243,
not 44/27: the latter is a uniform lower bound, not its exact energy.

Growing-period hole mosaics retain a positive fraction of fixed-depth pairs
while their long defect tends to zero. Such examples do not satisfy the
small-Q^2-delta condition, and their short energy remains too large. They
prevent extrapolating (15) to arbitrary period growth without a new estimate.

Still unproved: a repeating or bounded-cell approximation for actual zeta
zeros, a period-independent rigidity mechanism, arbitrary aperiodic dense
interlacing, exceptional operator-energy control, source weights/localization,
and arithmetic moment bounds in exactly this normalized model. Ordinary
nested supports are not independent artificial depth channels. Existing
conditional constants and review queues are not mathematical authority.

## 7. Reproduction and evidence

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python check_periodic_rigidity.py --samples 120 --output validation.json
```

The code records rational subchecks, finite period formulas, a specified
972-point numerical grid, seeded patterns, finite-repetition comparisons,
quadrature and high-precision scalar constants. Quadrature and mpmath are
not interval certificates. The analytic all-size claims rely on the proofs
above, not numerical extrapolation. No independent-verifier context, source
Lean build or full repository CI was run. Local backend readiness and
package hashes were checked; the bundled repository inventory/record runner
was not run in this connector-only package. Parent and main are unchanged.
