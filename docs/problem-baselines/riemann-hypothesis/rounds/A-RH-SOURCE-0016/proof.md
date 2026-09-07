# A-RH-SOURCE-0016 — fixed-bandwidth source moments and charged cell transfer

Date: 2026-09-07. Issue #101. Status: **proof_candidate**, no independent receipt.
Mathematical parent: A-RH-HSTAB-0015 at
`bea93a0308a7ddfd6bacc35c547ffd4ab6d5cee9`, proof blob
`3daba85264af382ae65dbae2924be4e1d74f9160`.
The source-moment result below uses an external pair-correlation theorem, NOT
an assumption that actual zeros already satisfy the parent's cell model.
The finite transfer inequality separately depends on that parent's candidate.

## 1. The actual source observable and the one external analytic input

Write ell=log T, V_T=T ell/(2 pi), and let N_T count zeta zeros with
0<Im(rho)<=T, including multiplicity. Use

    z_rho=-i(rho-1/2)ell/(2 pi).

The multiset is invariant under complex conjugation. Its real coordinates
are gamma ell/(2 pi); a reflection pair has normalized depth
`a=|Re(rho)-1/2|ell`, since its imaginary displacement is a/(2 pi).
These identities do not impose any uniform cap on a or any cell occupancy.
Changing all z signs makes no difference to the even kernels below.

The external input **PC** is Lemma 3.1 of Lamzouri, arXiv:2609.02882v1,
as transcribed from the unconditional pair-correlation theorem of Baluyot,
Goldston, Suriajaya and Turnage-Butterbaugh. For EACH FIXED real even test f,
supported in [-1,1] and Lipschitz at zero,

    sum_(rho,rho') fhat(i(rho-rho')ell/(2 pi)) w(rho-rho')/V_T
        = C(f)+O_f(ell^(-1/2)),
    C(f)=f(0)+2 int_0^1 v f(v)dv, w(s)=4/(4-s^2).               (1)

Also use the source's N_T/V_T -> 1. These are cited mathematical inputs, not
independently proved or formally checked in this run. See source-scope.md.
The fixed-test qualifier in (1) is retained throughout.

For a fixed 0<b<1 define the unweighted rectangular moment

    M_b(T)=N_T^(-1) sum_(rho,rho') sinc(b(z_rho-z_rho'))^2,
    sinc(z)=sin(pi z)/(pi z), sinc(0)=1.                        (2)

This is a complex square, not an absolute square of each summand. Nevertheless
its complete sum is real and nonnegative. For ANY finite conjugation-invariant
multiset, set B(v)=sum_z exp(2 pi i z v). For real even r>=0,

    sum_(z,z') rhat(z-z')^2 = int (r*r)(v)|B(v)|^2 dv.           (3)

To prove it, expand |B|^2, use conjugation invariance to relabel conjugate z',
and Fourier convolution. With r_b=1_[−b/2,b/2], (3) gives the numerator of
(2) as b^(-2) int (b-|v|)_+ |B(v)|^2 dv. Only the full integral is positive;
no sign is assumed for the original off-diagonal complex squares.

## 2. Fixed-test deweighting and an explicit compact envelope

Let r be fixed, real, even and C^2 with compact support of length less than one,
and put q=r*r. Then q and q'' satisfy PC: q'''=r''*r' is bounded, so q'' is
Lipschitz, and the supports are contained in [-1,1]. Integrating by parts gives
qhat''(z)=-4 pi^2 z^2 rhat(z)^2. Consequently the following is an EXACT finite
identity, before applying any asymptotic formula:

    sum rhat(z_rho-z_rho')^2
       = sum qhat(z_rho-z_rho') w(rho-rho')
          -(4ell^2)^(-1) sum qhat''(z_rho-z_rho') w(rho-rho').   (4)

Here qhat'' denotes the Fourier transform of q'', not differentiation in z.
The sign follows from w=(1+pi^2(z_rho-z_rho')^2/ell^2)^(-1).
Apply PC separately to the TWO FIXED tests q,q''. With

    I_r=int r^2, J_r=int (r')^2,
    A(r)=I_r+int int |u+v|r(u)r(v)du dv,

one obtains

    sum rhat(z_rho-z_rho')^2/V_T
      = A(r)+(J_r-2I_r)/(4ell^2)
         +O_q(ell^(-1/2))+O_(q'')(ell^(-5/2)).                  (5)

Indeed q''(0)=-J_r, and integration by parts yields
2 int_0^1 v q''(v)dv=2q(0)=2I_r. The displayed second-order term is normalized
by V_T; replacing V_T by N_T is licensed only for the leading limit here.
Equation (4) is the source's fixed-test mechanism, not claimed as a new method.

For the envelope make everything explicit. For 0<=t<=1 put

    S(t)=1-10t^3+15t^4-6t^5=(1-t)^3(1+3t+6t^2).

For p>=0 and e>0 with p+2e<1, define r_(p,e)(x) to be one on |x|<=p/2,
S((|x|-p/2)/e) on the two transition intervals, and zero outside
|x|<p/2+e. It is nonnegative, at most one and C^2 across its joins. Exact
polynomial integration gives

    int r=p+e, I_r=p+181e/231, J_r=20/(7e),
    A(r)=p+181e/231+p^3/3+p^2 e+15p e^2/14+3559e^3/9009.       (6)

For example int_0^1 S^2=181/462 and int_0^1 (S')^2=10/7. To check the absolute
moment in (6), let H(x)=int_0^x r and M=int r. Evenness gives
int int |u+v|r(u)r(v)=int_0^(p/2+e)[M^2-4H(x)^2]dx.
The checker evaluates the underlying polynomials with exact rational arithmetic.
No smoothstep is advertised as C-infinity; C^2 and the verified regularity of
q,q'' are all the input (1) needs.

## 3. Closing the rectangular arithmetic input BELOW the endpoint

Fix b in (0,1), and next fix 0<e<min(b/2,(1-b)/2). Choose

    r_-=r_(b-2e,e), r_+=r_(b,e).

Pointwise r_-<=r_b<=r_+. Nonnegative convolution therefore gives
r_-*r_- <= r_b*r_b <= r_+*r_+. Applying this to the nonnegative density |B_T|^2
in (3), for EVERY finite T,

    sum rhat_-(z-z')^2 <= b^2 N_T M_b(T)
                               <= sum rhat_+(z-z')^2.          (7)

Use (5) with fixed b,e first. Then let e decrease to zero in (6). This proves
the source-conditional candidate theorem

    for EVERY FIXED 0<b<1:
    M_b(T) -> kappa(b):=1/b+b/3 as T->infinity.                 (8)

No cell hypothesis, depth truncation, RH, positive off-diagonal terms or
uniform moving-test error is used. It is an interior-bandwidth corollary of PC,
not a new unconditional simple-zero proportion or a novelty claim.

There is an explicit envelope for the intermediate limits. Since r_(p,e)
lies between interval indicators of lengths p and p+2e, positivity in A(r) gives

    [(b-2e)+(b-2e)^3/3]/b^2 <= liminf M_b
     <= limsup M_b <= [(b+2e)+(b+2e)^3/3]/b^2.                  (9)

This also proves convergence without invoking numerical integration of A(r).
All source remainder constants depend on the FIXED envelope; (6) alone does
not control the full PC remainder when e or b depends on T.

For the model's two relative boxes fix theta in (0,1), set x=theta z, and let
alpha be either 1 or 3/4. The same ACTUAL finite multiset satisfies

    N_T^(-1) sum sinc(alpha(x-x'))^2 -> kappa(alpha theta).      (10)

The long budget is kappa(theta), NOT exactly 4/3. Precisely,

    kappa(theta)-4/3=(1-theta)(3-theta)/(3theta),
    kappa(alpha theta)-kappa(alpha)
                    =(1-theta)[1/(alpha theta)-alpha/3].       (11)

The constants approach the ideal ones by choosing a fixed theta close to one.
Taking theta=theta(T) without a new uniform estimate is not proved by (8).
Spatial span and mass also differ: x occupies a span approximately theta V_T,
whereas mass is N_T approximately V_T. Mean mass per spatial unit is therefore
approximately 1/theta, not automatically one. Section 6 keeps that normalization.

### Endpoint guard

Equations (7)-(8) give no upper bound at b=1. They do give liminf M_1>=4/3,
by monotonicity of b^2 times the rectangular energy and then b increasing to one.
A purely positive-measure countermodel explains the missing direction: let
mu_n=(n/2)(delta_(1-1/n)+delta_(-1+1/n)), and
H_b(n)=b^(-2)int (b-|v|)_+ dmu_n. For each fixed b<1 it is eventually zero,
while H_1(n)=1. This is not a zero configuration; it refutes the LIMIT
INTERCHANGE inference from interior bounds alone. No claim is made here about
the truth or falsity of the actual critical-endpoint asymptotic.

## 4. A deletion charge that controls operator energy, even at unbounded depth

A finite conjugation-symmetric orbit list has real centers t_j, depths a_j>=0
and total orbit masses c_j: real atoms have a_j=0, a pair is encoded by cosh.
Allow real signed coefficients in this lemma (use |c_j| in the charge). On the
unit-normalized alpha-box, 0<alpha<=1, let A_E have kernel
alpha^(-1)sum c_j exp(2 pi i t_j(u-v))cosh(a_j(u-v)).

For each INTEGER cell k define the depth-weighted local load

    W_k(alpha)=sum_(k<=t_j<k+1) |c_j| cosh(alpha a_j).

Then, with NO depth cap, NO cell capacity bound and NO gap assumption,

    ||A_E||_HS^2 <= (3+1/(3alpha^2)) sum_k W_k(alpha)^2.         (12)

Proof. The four-sign sinc-square kernel for two orbits satisfies

    |K_alpha(d,a,a')| <= cosh(alpha a)cosh(alpha a'),
    |K_alpha(d,a,a')| <= cosh(alpha a)cosh(alpha a')
                                      /(pi^2 alpha^2 d^2), d!=0.

The first bound follows from the triangular integral. For the second, use
|sin(x+iy)|^2<=cosh(y)^2 and
cosh((u+v)/2)^2<=cosh(u)cosh(v). For cell separation r>=2, |d|>=r-1.
Thus the absolute double sum is bounded by the convolution with h_0=h_1=1
and h_r=1/[pi^2 alpha^2(r-1)^2] for r>=2. Its two-sided sum is
3+1/(3alpha^2). For each shift r, sum W_k W_(k+r)<=sum W_k^2, by
Cauchy-Schwarz; this proves (12). Finite occupied cells suffice, and integer
boundaries use the half-open convention. No cancellation is discarded for free.

For deletions from a source of reference normalization Q, define
Xi_alpha=Q^(-1)sum W_k(alpha)^2. Their normalized HS cost is at most
sqrt((3+1/(3alpha^2))Xi_alpha). This is the explicit tail/cluster obligation;
a small deleted COUNT is not a substitute.

## 5. Supplied transport into cells, without claiming it can be extracted

Suppose a retained core has marks m_j in {1,2}, total mass Q, distinct assigned
integer cells k_j, target centers y_j=k_j+tau_j with 0<=tau_j<1, and source
centers x_j satisfying |x_j-y_j|<=h. Source and target depths a_j,a'_j lie in
[0,A], and are zero at simple marks. Write

    P=Q^(-1)sum m_j(x_j-y_j)^2, Z=Q^(-1)sum m_j(a_j-a'_j)^2,
    L_(alpha,h)=sqrt(2/alpha)
                    [exp(pi alpha(h+1/2))+exp(pi alpha/2)].

The signed alpha-box operators of these two cores obey

    ||A_core-A_target||_HS/sqrt(Q)
       <= pi alpha L_(alpha,h)cosh(alpha A)sqrt(P)
            +(alpha/2)L_(alpha,h)sinh(alpha A)sqrt(Z).          (13)

Proof. Real integer exponentials are orthonormal on the long unit box. On the
unit-normalized alpha-box their synthesis norm is at most alpha^(-1/2).
Expand exponentials about k_j+1/2 and hyperbolic factors in norm-convergent
power series. The source displacements from k_j+1/2 are at most h+1/2; the
target displacements are at most 1/2. Hence the sums of their G synthesis
norms and H synthesis norms are bounded respectively by L cosh(alpha A/2)
and L sinh(alpha A/2), with weights sqrt(m_j)<=sqrt(2).
Column differences are bounded by pi alpha times the corresponding cosh/sinh
factor times |x-y|, plus alpha/2 times the opposite factor times |a-a'|.
Expand GG*-G'G'* and HH*-H'H'*, sum the HS products and apply
cosh^2+sinh^2=cosh(2x), 2sinh cosh=sinh(2x). This gives (13).

The assignment must be injective at the ORBIT level, not at the individual
member level of a reflection pair. No torus rounding, favorable matching,
small P, cell occupancy bound for the original untrimmed list, or simple-count
preservation under arbitrary merging is inferred by this lemma.

## 6. An explicit source-to-periodic-model feasibility inequality

Here all quantities are finite. Let a source multiset have mass N and simple
real count n. Clip nonsimple REAL multiplicities to two and pair multiplicities
to one per member, optionally delete whole retained orbits, and obtain a core
of mass Q>=2. No nonsimple orbit may be converted to a simple one. Let n_del
count deleted ORIGINAL simple real atoms; the core simple count is n-n_del.
Choose a supplied injection of the core into cells 0,...,Q-1 as in section 5,
with target cap A. The target period-Q model has mean mass one, and

    r=N/Q, sigma=n/N, d=n_del/Q, s_model=r sigma-d.             (14)

This is exact; mass normalization may not be replaced by r=1 without evidence.
The total deleted coefficient at each source orbit is what enters (12).
Let eps_alpha be the sum of the normalized costs (12) and (13). Define
S_alpha=||A_source,alpha||_HS^2/N and

    b_(alpha,A)(Q)=cosh(alpha A)^2/Q
                          [8+32(2+log Q)/(pi^2 alpha^2)],
    U_alpha=(sqrt(r S_alpha)+eps_alpha)^2+b_(alpha,A)(Q).       (15)

The target PERIODIC energy obeys E_model,alpha<=U_alpha. Indeed the HS triangle
inequality compares the two FINITE operators; the last term is the parent's
signed finite-to-periodic boundary estimate applied to the target's Q cells.
Thus this step neither periodizes actual zeros silently nor estimates discarded
cross terms by their signs. A measured source upper bound may replace S_alpha.

Put Delta=r sigma-d+U_1-2. If Delta<0 the claimed assignment and input bounds
are inconsistent, since the target defect is nonnegative. Otherwise the parent
mixed-model inequality, for every integer L>=2 and 1/2<alpha<=1, gives

    U_alpha+Err_(alpha,A)(L,Delta)
                          >= f_alpha(2-r sigma+d)+c_alpha,    (16)
    f_alpha=(2alpha-1)/alpha^2, c_alpha=(1-alpha)/alpha^2.

The error Err is EXACTLY equations (18),(21) of the pinned round-15 proof;
its arguments and monotonicity in Delta are unchanged. No new authority is
claimed for that dependency. Equation (16) is a checkable necessary condition
for a proposed source representation. It is not a construction of one.
For ACTUAL source coordinates x=theta z, (10) supplies the asymptotic S_alpha
input at fixed theta. Xi_alpha, P, Z, A and the injection remain separate debts.

### Multiplicity count is partially controlled, but energy is not automatic

The earlier signed slack extends to arbitrary integer multiplicities. Let nu
be nonsimple mass and R_ns the number of nonsimple real or conjugate-pair
orbits. In the continuous-box finite source let D=n+||A||_HS^2-2N. The exact
slack gives D>=2(nu-2dim U)>=2(nu-2R_ns). Consequently clipping as above
removes exactly nu-2R_ns<=D/2 mass and creates no new simple atoms. This is an
inherited multiplicity consequence, not claimed as a new discovery. It supplies
no bound on Xi_alpha: depth weights and local clustering are missing from a
count statement. Additional whole-orbit deletions must be charged separately.

## 7. Two genuine finite deletion obstructions

**Distinct shallow clusters.** Take k distinct simple real points
x_j=j/(4k), j=0,...,k-1, and reference normalization N=k^2. Their mass ratio
is 1/k. All pair separations have magnitude <1/4; sin(pi d)>=2d for
0<=d<=1/2 gives sinc(d)^2>=4/pi^2. Hence their deleted operator satisfies

    ||A_E||_HS^2/N >=4/pi^2>2/5, while mass(E)/N ->0.           (17)

The unused mass can be supplied by any other distinct real atoms far away;
it does not change the residual operator. These are genuine distinct
exponentials, not repeated abstract 'simple' vectors. They disprove count-only
HS deletion control even with depth zero. They are not asserted to be zeta zeros
or near-extremizers, and violate a retained one-orbit-per-cell assumption.

**A single deep pair.** A mass-two pair at depth a on the alpha-box has

    ||A_pair||_HS^2=2+2[sinh(alpha a)/(alpha a)]^2.              (18)

This follows by integrating 4cosh(a v)^2 against the triangular probability
weight. With alpha=1, a=log N, its deleted fraction is 2/N, but (18)/N is
asymptotic to N/[2(log N)^2], which diverges. This is an abstract finite-family
obstruction, not a configuration respecting all arithmetic restrictions on
zeta zeros. It explains why unbounded depth needs its own charge in (12).
Neither obstruction disproves a future tail bound using additional zeta input.

## 8. What has moved, and what has not

The previously unestablished rectangular arithmetic input is now reduced to
PC by a concrete, signed-safe sandwich at every fixed SUBCRITICAL bandwidth.
This does not independently validate PC, give a new zero proportion beyond the
source's existing optimized result, or establish the endpoint b=1. The finite
geometric transfer is no longer an unnamed 'small error': (12)-(16) list its
normalized quantities and the exact way they affect the model budgets.

Proposed next attempt A-RH-MATCH-0017: produce, or obstruct, an orbit-level
cell assignment with simultaneous small depth-weighted local deletion charge
and weighted displacement, preserving the simple-count ledger. Mean density,
small multiplicity-excess mass, or source pair-correlation alone must not be
silently promoted to such a matching. A fixed retained depth cap or a controlled
replacement for it remains necessary for the current mixed-model theorem.

All new universal claims remain solver proof candidates. Tests below exercise
finite formulas, not actual zero enumeration, source asymptotics, unknown PC
remainder constants, independent verification, Lean, or RH. Independent review
should separate C01-C03's external-PC dependency from C06's round-15 dependency.
