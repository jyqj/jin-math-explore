# A-RH-DISP-0014 — squared-depth covariance and anchor-free equality

Status: **proof_candidate**, not independently verified. Issue #86.
Sequential parent: A-RH-HOLE-0013, commit
`d344b72c6c8f4e1d0057a295675f5b1637c5f5ce`, proof blob
`802f8f01fd3d1178064b43109aa59b28ce5b0401`.
The older exact-grid operator inequality used below was already recorded in
A-RH-WTP-0004, commit `340d6c4a3f2101d2cd08834ee3fe9cc9aed8f202`, README blob
`49c16fe11d858345ecfbe1f351f694bb41a4d116`. It is not claimed as this round's
new result. The new steps extract a positive depth-covariance quantity and
classify anchor-free equality at all occupancy densities.

## 1. Normalization: allow a hole to have mean mass other than one

Let Q>=1, m_p in {0,1,2}, t_p=p+tau_p, 0<=tau_p<1, and 0<=a_p<=A.
Require a_p=0 whenever m_p!=2. Mark two represents a real double if a_p=0,
or the conjugate pair t_p +/- i a_p/(2 pi) otherwise. Put

    N=sum_p m_p, rho=N/Q, n=#{p:m_p=1}, s=n/Q,
    u_j=(j-(Q-1)/2)/Q, j=0,...,Q-1,
    f_t(j)=Q^(-1/2) exp(2 pi i t u_j).

Let G,H have columns sqrt(m_p) f_(t_p) cosh(a_p u) and
sqrt(m_p) f_(t_p) sinh(a_p u). Define T=GG*-HH*, and

    B(v)=sum_p m_p exp(2 pi i t_p v) cosh(a_p v),
    b_j=B(j/Q)/Q,
    E_alpha=rho^2/alpha+(2/alpha^2) sum_(1<=j<alpha Q)
                                      (alpha-j/Q)|b_j|^2,
    delta=(n+||T||_F^2-2N)/Q=s+E_1-2rho.                       (1)

Then T(j,k)=B((j-k)/Q)/Q, diag(T)=rho, and ||T||_F^2/Q=E_1,
by Toeplitz diagonal counting. E_alpha is the continuous normalized-box energy
per supplied cell in the fixed-pattern infinite-repetition limit. The proof is
the Fejer periodization in the parent, with B(0)=N rather than Q; the zero mode
is therefore rho^2/alpha. At rho=1 these are exactly the preceding L_alpha and
delta. At rho=2, delta is still **per cell**, not per zero.

The finite signed Hilbert slack proves delta>=0, as in the parent. No finite
repetition error uniform in growing Q is asserted. We will separately use
exact-lattice hypotheses in Sections 2-5 and arbitrary phases in Sections 6-7.

## 2. A positive Dirichlet form for squared depths

For a real field x on the Q-cycle define

    xhat_j=Q^(-1)sum_p x_p exp(2 pi i p j/Q),
    D_Q(x)=sum_(j=1)^(Q-1) (j/Q)(1-j/Q)|xhat_j|^2.              (2)

For Q=1 set D_1=0. The exact spatial formula is

    D_Q(x)=1/(4Q^3) sum_(p!=r)
                   (x_p-x_r)^2 / sin(pi(p-r)/Q)^2.             (3)

All pairs in (3) are ordered. This form vanishes on constants; it does not
control a field's global mean.

Proof. For w_j=j(Q-j)/Q^2, its cyclic second difference equals -2/Q^2 off
j=0 and 2(Q-1)/Q^2 at zero. Fourier transforming this recurrence yields,
for 1<=r<Q, the Fourier coefficient

    Q^(-1)sum_j w_j exp(2 pi i j r/Q)
                         =-1/[2Q^2 sin(pi r/Q)^2].

The coefficients of the circulant operator sum to w_0=0. Expanding its
quadratic form into pair differences, including the 1/Q in Parseval, gives
(3). This is also valid at Q=2, where the single opposite lag must not be
double-counted a second time.

A useful consequence is a composition bound: whenever x_p in [0,M] and k>=1,

    sqrt(D_Q(x^k)) <= k M^(k-1) sqrt(D_Q(x)).                   (4)

It follows directly from |x^k-y^k|<=k M^(k-1)|x-y| in each positive term of
(3). More generally any Lipschitz real function contracts this seminorm by
its Lipschitz constant. Equation (3) is what makes (4) valid; a generic
positive Fourier multiplier would not suffice for this composition argument.

## 3. Nonlinear covariance versus the signed correction

Assume now the **exact critical lattice** t_p=p+theta, with a single theta.
Let T0 be T with every depth zero, K=T-T0, and q_p=a_p^2 (zero off pair sites).
The m_p<=2 assumption and a_p=0 off pair sites give the exact coefficient
formula, with a harmless unit phase removed,

    c_j=2 Q^(-1)sum_p exp(2 pi i p j/Q)[cosh(a_p j/Q)-1]
       =sum_(k>=1) [2(j/Q)^(2k)/(2k)!] (q^k)hat_j,
    ||K||_F^2/Q=2 sum_(j=1)^(Q-1)(1-j/Q)|c_j|^2.               (5)

Define gamma_A=sinh(A)/A, gamma_0=1, and kappa_A=3/2-gamma_A.
For every finite A the upper bound below holds. If kappa_A>0 the lower bound
also holds:

    kappa_A^2 D_Q(q) <= ||K||_F^2/Q <= gamma_A^2 D_Q(q).         (6)

The lower bound is not claimed when kappa_A<=0.

Proof. Write ||z||_w^2=2 sum_(j!=0)(1-j/Q)|z_j|^2. Since q^k is real,
its conjugate Fourier frequencies have equal modulus. Pairing j and Q-j gives

    || (j/Q)^(2k) (q^k)hat_j ||_w^2
     =sum_(j!=0) t(1-t)[t^(4k-1)+(1-t)^(4k-1)] |(q^k)hat_j|^2,
     t=j/Q.                                                   (7)

For k=1, 1/4<=t^3+(1-t)^3<=1. Thus the leading term t^2 qhat_j in (5)
has norm between (1/2)sqrt(D_Q(q)) and sqrt(D_Q(q)). For k>=2,
t^(4k-1)+(1-t)^(4k-1)<=1. Equation (4) bounds the sum of the higher-order norms by

    sum_(k>=2) [2k A^(2k-2)/(2k)!] sqrt(D_Q(q))
                     =(gamma_A-1)sqrt(D_Q(q)).                 (8)

The power series converges absolutely in these finite norms, uniformly for
a_p<=A. The reverse triangle inequality gives the lower bound in (6), and
the triangle inequality gives the upper bound. At A=0 all quantities vanish.
No cancellation between signed pair summands is incorrectly declared positive.
The positivity used here is in (3), not in the original complex sinc squares.

### The already-known exact-grid signed-defect input

On this lattice T0 has eigenvalues m_p in an orthonormal Fourier basis, and
tr(K)=0. Since sum m_p^2=2N-n,

    Q delta=||K||_F^2-2 tr((2I-T0)K).                          (9)

For a pair of depth a at residue p, its correction K_p satisfies, at q!=p,

    tr(U_q K_p)= [4 sinh(a/2)^2/Q^2]
       [cosh(a/Q)cos(2 pi(p-q)/Q)-1]
       /[cosh(a/Q)-cos(2 pi(p-q)/Q)]^2.                        (10)

Here U_q is the rank-one real Fourier projection. Formula (10) follows by
summing the centered geometric series and taking twice its real square.
If 0<a<=2 pi this is nonpositive. Indeed, let
vartheta=2 pi min(|p-q|,Q-|p-q|)/Q. For cos(vartheta)<=0 the sign is immediate.
Otherwise a/Q<=vartheta<pi/2 and
cosh(a/Q)cos(vartheta)<=cosh(vartheta)cos(vartheta)<1; differentiate
log(cosh x cos x) to get tanh x-tan x<0. The a=0 term vanishes.

The coefficient of 2I-T0 at a pair site is zero; at every other site it is
nonnegative. Thus (9)-(10) give ||K||_F^2/Q<=delta for A<=2 pi. This is the
finite covariance input already in A-RH-WTP-0004, re-derived for (1), not a
new independent verification of that archive.

Combining with (6), for A<=2 pi and kappa_A>0,

    D_Q(a^2) <= delta/kappa_A^2.                               (11)

A particularly simple exact consequence is

    A<=log 2  ==>  kappa_A>=3/8,
    D_Q(a^2) <= (64/9)delta.                                  (12)

Indeed gamma_A is increasing, sinh(log 2)=3/4 and log 2>2/3, the latter from
2 sum_(k>=0) 1/[(2k+1)3^(2k+1)]. Thus gamma_A<9/8. No floating evaluation
of log or pi is used to establish the rational constant in (12).

## 4. Local depth coherence is now a conclusion on the lattice

For an integer R>=1, repeat to P=lcm(Q,R), partition into R-cell blocks at
any fixed integer starting shift, and define

    V_R=(1/P)sum_b sum_(p in b)m_p(a_p-abar_b)^2,
    abar_b=(sum_(p in b)m_p a_p)/(sum_(p in b)m_p).               (13)

An empty block contributes zero. This includes **all** blocks, not only
anchor-free blocks. The following bound does not require a simple mark:

    V_R <=4 pi R^2 sqrt(D_Q(a^2))
         <=(4 pi R^2/kappa_A)sqrt(delta).                      (14)

For A<=log 2 the last constant is at most (32 pi/3)R^2.

Proof. From the single directed nearest-neighbor contribution in (3),

    Q^(-1)sum_p(q_(p+1)-q_p)^2
                 <=4Q^2 sin(pi/Q)^2 D_Q(q)<=4 pi^2 D_Q(q).     (15)

For Q=1 the left side is zero. As a,b>=0, (a-b)^2<=|a^2-b^2|.
Cauchy-Schwarz in the cell average therefore bounds the average adjacent
squared depth difference by 2 pi sqrt(D_Q(q)). In each R-block, use its
unweighted mean as a trial weighted mean and m_p<=2. The elementary path
Poincare estimate

    sum_(p in b)(a_p-mean_b a)^2
                       <=R^2 sum_(internal edges)(a_(p+1)-a_p)^2

follows by the pairwise variance formula and telescoping along each path.
Summing and bounding internal edges by all edges proves (14). Repeating the
period changes neither D_Q nor the cell-averaged adjacent differences, so
there is no assumption R divides Q.

For any exact-lattice sequence at a common cap A<=log 2 and delta_n->0,
V_(n,R)->0 for every fixed R. Consequently the parent's hole-only variance
Omega_(n,R)<=V_(n,R) satisfies

    liminf_(R->infinity) limsup_(n->infinity) Omega_(n,R)=0.      (16)

Thus the previous depth-coherence hypothesis is **derived**, not assumed, on
this specified class. With rho_n=1 and s_n->2/3, the parent's conditional
realification/local-energy theorem can then be applied. It gives the same
44/27 short floor, not a new zeta proportion. Exact-lattice two-budget exclusion
was already possible by the older operator route; the new result here is the
positive depth-covariance control and (14)-(16), not that old exclusion itself.

### A finite cell-preserving phase-error interface

For arbitrary tau_p, compare with t_p^g=p+theta, retaining m_p and a_p, and put
Phi=Q^(-1)sum_p m_p(tau_p-theta)^2, with theta in [0,1). This is a supplied,
ordinary representative error: **no torus rounding, collision deletion or
extracted matching is claimed**. Write delta_g for the grid defect. Then

    delta_g <= delta + C_(A,rho) sqrt(Phi),
    C_(A,rho)=2 pi sqrt(rho)(exp(pi/2)+1)^2 cosh(A)^2.            (17)

Indeed expand the actual synthesis relative to the unitary p+1/2 basis.
Its G/H operator norms are at most sqrt(2)exp(pi/2)cosh/sinh(A/2), whereas
the grid norms omit exp(pi/2). Column phase differences have norms at most
pi cosh(A/2)|tau-theta| and pi sinh(A/2)|tau-theta|. Hence

    ||T-Tg||_F/sqrt(Q)
        <=pi sqrt(2)(exp(pi/2)+1)cosh(A)sqrt(Phi),
    (||T||_F+||Tg||_F)/sqrt(Q)
        <=sqrt(2rho)(exp(pi/2)+1)cosh(A).

Multiplication proves (17); traces and counts agree. Thus (11) and (14) also
hold with delta replaced by delta+C_(A,rho)sqrt(Phi). This makes the missing
phase control explicit. It does not prove Phi is small in arbitrary holes,
and a local application would still have to account for block boundaries.

## 5. Why neither a linear depth-variance rate nor global coherence follows

**Quartic shallow-depth scale.** Take Q=2, both marks two, exact phases,
a=(0,epsilon). This has rho=2, not the target mean-one normalization. Directly,

    delta=[cosh(epsilon/2)-1]^2=epsilon^4/64+O(epsilon^6),
    V_2=epsilon^2/2,   D_2(a^2)=epsilon^4/16.                   (18)

Thus V_2/sqrt(delta)->4, while V_2/delta diverges. The square-root dependence
in this general local depth-variance mechanism cannot be replaced by a uniform
linear-in-delta estimate. This is not a mean-one two-budget escape model.

**Slow depth wave.** For Q>=3, put every mark two and

    q_p=a_p^2=1/4+(1/8)cos(2 pi p/Q).

Then Var(q)=1/128 exactly and

    D_Q(q)=(1/128)(1/Q)(1-1/Q),
    delta=||K||_F^2/Q<=gamma_(sqrt(3/8))^2 D_Q(q)->0.            (19)

The equality for delta follows from T0=2I. Since
|a^2-b^2|<=2A|a-b|, Var(a)>=Var(q)/(4A^2)>0 as well. Thus fixed-period
equality does not give period-free *global* depth coherence. Local variance still vanishes by
(14); these are different quantifiers. The example has mean two and is used
only for this scope obstruction, not as a claimed global RH model.

**The grid cannot be silently removed.** For Q=2, m=(2,2),
tau=(1/4,3/4), a=(log 2,log 2), the squared-depth field is constant, so D_Q=0.
Nevertheless

    ||T-T0||_F^2/Q = 17/4-3 sqrt(2)>0.                         (20)

Indeed the nonzero real-reference coefficient has squared modulus two, and
cosh(log(2)/2)=3/(2sqrt(2)). The positivity follows by squaring 17/4 and
3sqrt(2): their squares differ by 1/16. This refutes applying the upper
covariance bound (6) to arbitrary phases with no extra charge. It does not
refute (17). Similarly, A<=2pi in (10) cannot be dropped: at Q=32, a=8 and
nearest-residue separation, cosh(1/4)cos(pi/16)>1. A numerical guard is retained
for that high-depth sign failure; it is not needed by the positive theorems.

## 6. Exact anchor-free equality at arbitrary phases and densities

Assume only m_p in {0,2}; let r be the number of occupied cells, so rho=2r/Q.
No exact-lattice or small-depth assumption is made in this section; each a_p
is finite. Let D=Q delta=||T||_F^2-4r and U=range(G). Put u=dim U<=r,
Pi=P_U and zeta=||(I-Pi)H||_F^2. Direct trace expansion gives

    D=||T-2Pi||_F^2+4(r-u)+4zeta.                             (21)

In fact tr T=2r and tr(Pi T)=2r+zeta. Thus D=0 forces
dim U=r, T=2Pi and every G,H column to lie in U. The two individual complex
exponential columns at each pair center therefore lie in U as well.
Here the symbol `u` denotes dim U; no dimensional bound 2r<=Q is imposed.

### Hermitian Toeplitz projection lemma

Every nontrivial Hermitian Toeplitz orthogonal projection on C^Q is diagonal
in a phase-twisted Fourier basis. This elementary lemma is proved here; no
literature-wide novelty is claimed for it.

Write Pi(i,j)=t_(i-j), t_-k=conj(t_k), and z=(t_1,...,t_(Q-1)),
y=(conj(t_(Q-1)),...,conj(t_1)). The difference between adjacent entries of
Pi^2 on the same diagonal is

    (Pi^2)_(i+1,j+1)-(Pi^2)_(i,j)
                  = z_i conj(z_j)-y_i conj(y_j).               (22)

Since Pi^2=Pi is Toeplitz, zz*=yy*. If z=0 the projection is 0 or I.
Otherwise y=lambda z with |lambda|=1. Choose theta such that
lambda=exp(-2 pi i theta). Then

    t_(k-Q)=lambda t_k,  1<=k<Q.

Conjugating Pi by diag(exp(2 pi i theta j/Q)) removes the twist and yields
a circulant matrix. Its orthonormal eigenbasis is f_(ell+theta), ell=0,...,Q-1.
The range of Pi is a subset of those Q modes.

If 0<r<Q, at least one such mode is omitted. Any exponential column with a
nonzero imaginary frequency has nonzero inner product with EVERY real Fourier
mode: its finite geometric series has ratio with modulus different from one,
so neither its numerator 1-ratio^Q nor its denominator vanishes. It cannot
belong to this proper Fourier subspace. Therefore every depth is zero.
For a real frequency t, the same geometric series can vanish against an
omitted mode only if t-theta is an integer (the coincident mode gives a
nonzero value instead). Thus all occupied phases coincide modulo one.
Given the supplied distinct cells, this means the occupied tau_p are equal.

### Fully occupied cells require a different argument

If r=Q, Pi=I and the omitted-mode argument is unavailable. Here D=0 means
T=2I, or B(j/Q)=0 for j=1,...,Q-1. Form the 2Q nodes

    z_(p,+/-)=exp((2 pi i t_p +/- a_p)/Q)

with multiplicity, and their monic polynomial P(z). The nodes are closed under
z -> 1/conj(z), and the constant term d has modulus one. Hence

    P(z)=d z^(2Q) conjugate(P(1/conj(z))).                     (23)

Newton identities applied to the vanishing power sums B(j/Q) show that the
first Q-1 coefficients after the leading coefficient vanish. Equation (23)
forces the corresponding last Q-1 to vanish as well. Thus

    P(z)=z^(2Q)+c z^Q+d.                                      (24)

If some depth is positive, the two roots y_+,y_- of y^2+c y+d are off the
unit circle and are paired by y_-=1/conj(y_+). (A root off the circle cannot
be fixed by this involution.) The roots of (24) are two regular Q-gons with
reciprocal radii and the SAME arguments. Therefore every occupied center has
the same phase and every depth has the same value |log|y_+||.

If all depths are zero, all Q distinct cell nodes occur with multiplicity two.
If the two roots of the quadratic in (24) were different, all 2Q roots of P
would be simple, since those quadratic roots are nonzero. Thus they coincide
at a unit number, and again the phases are common. This covers zero depth,
repeated nodes and Q=1. No conclusion is drawn from numerical root fitting.

We have the exact dichotomy:

    r=0: the empty model;
    0<r<Q and delta=0: all occupied depths zero, one common phase;
    r=Q and delta=0: one common phase and one common depth.      (25)

Conversely every listed configuration has delta=0: sparse real Fourier
columns give T=2Pi, and in the full common-depth case the nonzero Fourier
sums cancel so T=2I. The full positive-depth class was absent from the earlier
mean-one equality statement. It is precisely the class that an anchor-free
high-density region can approach locally.

## 7. The missing hole floor holds at exact equality

For 1/2<alpha<=1 define f_alpha=(2alpha-1)/alpha^2 and
c_alpha=1/alpha-f_alpha. Every model in (25) satisfies

    E_alpha >= 2 f_alpha rho + c_alpha rho^2.                  (26)

For the real sparse class, let mhat_j be its normalized DFT. Pairing the
conjugate coefficients in (1) gives

    E_alpha=rho^2/alpha+sum_(j!=0) F_alpha(j/Q)|mhat_j|^2,
    F_alpha(t)=[(alpha-t)_++(alpha-1+t)_+]/alpha^2 >= f_alpha.

Parseval says sum_(j!=0)|mhat_j|^2=sum m_p^2/Q-rho^2. Thus
E_alpha>=f_alpha sum m_p^2/Q+c_alpha rho^2, and sum m_p^2/Q=2rho.
For full common depth, all sampled nonzero coefficients vanish and
E_alpha=4/alpha; since rho=2, this is exactly (26). The empty class is trivial.

This is a genuine additional constraint on EXACT saturated periodic holes,
not a uniform stability theorem for nearly saturated holes.

For clarity, it repairs the parent's explicit scalar escape point only in
that exact class. At alpha=3/4, s=2/3, hole mass h=1/3 and cell fraction
beta=2/9, substituting (26) instead of the former crude hole floor gives

    (8/9)(2-s)+(4/9)[(1-h)^2/(1-beta)+h^2/beta]
                     =314/189=19/12+59/756,                    (27)

where the parent relaxation gave 286/189<19/12. More generally, for 0<beta<1, the bracket
is at least one by Cauchy-Schwarz, yielding 44/27=19/12+5/108. Empty-side
endpoint terms are interpreted by their zero-mass limits.
This scalar calculation does NOT license applying (26) to actual finite
blocks or to arbitrary sequences with delta->0. A block-periodization and
uniform approximate-equality bridge is still missing.

## 8. Precise next problem and evidence boundary

A-RH-HSTAB-0015: for each fixed A, prove or refute the existence of a modulus
omega_A(t)->0 as t->0+ such that every anchor-free supplied periodic model,
all Q and all 0<=rho<=2, satisfies

    E_(3/4) >= (16/9)rho+(4/9)rho^2 - omega_A(delta).            (28)

Equation (25) and (26) establish the zero-defect endpoint, NOT such a uniform
modulus. Sections 2-4 control one class of depth fluctuations on exact/near
lattices; they do not establish small phase error in arbitrary holes.
A proposed proof of (28) must survive slow depth/phase waves, sparse cells,
collisions in any attempted matching, and the finite versus periodic boundary
charge. A proposed counterexample must meet the actual moment requirements,
not merely a relaxed scalar inequality.

Under a usable (28), the parent's signed block localization and good-block
bounds suggest an all-hole-mass route to the original model gap; that
implication still requires the stated boundary/averaging details. No actual
zeta cell representation, source weights/localization, exceptional operator
energy estimate or arithmetic moment transfer is supplied by this round.

The checker tests exact rational/integer identities, sampled finite matrices,
constructed equality cases and explicit scope examples. It does not test all
possible equality configurations or establish the analytic universal claims.
The new proof is a solver candidate; no isolated verifier, Lean build or
mathematical-authority promotion has occurred. No originality claim beyond
the bounded repository comparison is made.
