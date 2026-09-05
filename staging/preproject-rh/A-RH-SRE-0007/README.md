# A-RH-SRE-0007 — from a signed defect to positive simple-real energy

Status: `solver_proof_candidate`; not independently verified.
Issue: #54. Actor/run: `openai-gpt-6-pro / run-20260905-rh-simple-energy-07`.
Read-only parent: #48 / A-RH-CWR-0006 at
`2577c7769b806075e2e3dc5d3b298e9d56458a46`.
Date: 2026-09-05. This successor does not edit any predecessor.

## 0. Outcome and limits

The parent supplied a local matching lemma **assuming** positive real-atom
sinc energy was available. This checkpoint supplies that input for a large
subfamily of the **simple real sector**, starting from a signed finite
Hilbert-space defect. It does not supply it for every atom.

For a finite conjugation-invariant multiset, use the normalized box profile
on [-1/2,1/2]. Let n be the number of simple real elements, N the total mass,
A its signed Hermitian exponential operator, and

\[
D=n+\|A\|_{HS}^2-2N.
\]

There is a subfamily of the simple real elements obtained by deleting at most
6D elements, with separation at least 1/2 and positive ordered-pair energy

\[
\boxed{\sum_{i\ne j\ {m retained}}\operatorname{sinc}(x_i-x_j)^2\le7D.}
\tag{0.1}
\]

Constants do not depend on the number, multiplicities or imaginary depths of
the non-simple/non-real elements. No finite depth alphabet is assumed.
The stronger explicit constants derived below are approximately 5.12782 for
deletion and 6.14573 for energy. They are not asserted optimal.

The key new step is a coefficient-Gram error decomposition into a
Hilbert--Schmidt-controlled part and a trace-controlled part. Matching and
Bessel estimates then give O(D), rather than O(sqrt(nD)), losses.

This is a finite stability result near equality, not a proof that actual zeta
zeros satisfy D=o(N). It controls neither the missing non-simple mass nor the
Hilbert--Schmidt energy of all discarded atoms. No unconditional zero
proportion or RH claim is made. Analytic proofs below remain candidates
pending an isolated audit; numerical checks do not certify them.

## 1. Exact slack in the signed Hilbert-space inequality

Work first in an arbitrary Hilbert space with a finite atom family. Its finite
span suffices for every trace. There are:

- n simple unit vectors f_i;
- unit vectors v_j with weights m_j>=2;
- pairs (g_p,h_p) with integer weights b_p>=1 and
  ||g_p||^2-||h_p||^2=1.

Define the positive operators

\[
S=\sum_{i=1}^n f_if_i^*,\quad
P=\sum_jm_jv_jv_j^*+2\sum_pb_pg_pg_p^*,\quad
N_-=2\sum_pb_ph_ph_p^*,\quad A=S+P-N_-.
\]

Put nu=sum_j m_j+2 sum_p b_p and N=n+nu=tr(A). Let U=ran(P),
let E be the span of the projected vectors (I-P_U)f_i, and let F=(U+E)^perp.
Write u=dim U, e=dim E, Q=2P_U+P_E, and

\[
a=\operatorname{tr}(P_U S),\quad
b=\operatorname{tr}((I-P_U)N_-),\quad
b_F=\operatorname{tr}(P_FN_-).
\]

Since U is spanned by one v_j or g_p per non-simple orbit,
nu>=2u. Also e<=n, and a,b,b_F>=0. Direct calculation gives
tr(P_U A)=nu+a+b and tr(P_F A)=-b_F. Expanding ||A-Q||^2 gives

\[
\boxed{D=\|A-Q\|_{HS}^2+2(\nu-2u)+2a+2b+2b_F+(n-e).}
\tag{1.1}
\]

In particular,

\[
D\ge0,\qquad
\|A-Q\|_{HS}^2+2a+2b+(n-e)\le D.                 \tag{1.2}
\]

This re-derives the required remainder rather than assuming that the parent
verification queue has passed. The construction is the one suggested by
Lamzouri Proposition 2.1; retaining its quantitative slack is our solver
calculation. No literature-wide novelty is asserted.

## 2. Coefficient-Gram decomposition

Let V:C^n->H have columns f_i and let Gamma=V*V. Every diagonal entry of
Gamma is one. Put V_E=P_E V and S_E=V_E V_E* as an operator on E. It is
positive definite on E by the definition of E. Its polar factorization is

\[
V_E=S_E^{1/2}W,\qquad WW^*=I_E.
\]

Thus W:C^n->E is a coisometry. When E=0 use W=0. The compressed source
identity is S_E-I_E=P_E(A-Q)P_E+P_EN_-P_E. Define

\[
Z=W^*P_E(A-Q)P_EW,
\]
\[
B=V^*P_UV+W^*P_EN_-P_EW\succeq0,\qquad
C=I_n-W^*W\succeq0.
\]

C is a projection of rank n-e. The exact decomposition is

\[
\boxed{\Gamma-I_n=Z+B-C,\quad
\|Z\|_{HS}^2\le D,\quad \operatorname{tr}(B+C)\le D.}
\tag{2.1}
\]

Indeed, V*V=V*P_UV+W*S_EW. Moreover
tr(B+C)=a+tr(P_E N_-)+(n-e)<=a+b+n-e<=D by (1.2).
Compression and the coisometry preserve the required HS bound.

A weaker useful consequence is ||Gamma-I||_1<=sqrt(nD)+D, where ||.||_1
means trace norm, not entrywise norm. Using that consequence alone loses a
square root. Sections 3-4 instead retain the separate controls in (2.1).
For every coefficient principal submatrix the same decomposition holds,
with HS norm of Z and positive traces no larger than their original values.

## 3. Extraction by maximal matching

Specialize the simple vectors to f_x(u)=exp(2*pi*i*x*u) in
L^2([-1/2,1/2]). Then

\[
\langle f_x,f_y\rangle=\operatorname{sinc}(x-y),\quad
\operatorname{sinc}(t)=\sin(\pi t)/(\pi t),\quad\operatorname{sinc}(0)=1.
\]

Create an edge between simple points whose distance is less than q=1/2.
Choose any maximal matching and remove its endpoints. The remaining set is
q-separated. Let L be the number of removed endpoints (twice the number of
matched edges). Let T have off-diagonal entries 1 on these disjoint matched
pairs and zero elsewhere. Then ||T||op=1 and ||T||HS=sqrt(L). On every edge,
sinc(x_i-x_j)>=c=2/pi. Trace pairing with (2.1) therefore yields

\[
\boxed{cL\le\operatorname{tr}(T(\Gamma-I))
\le\sqrt{LD}+D.}                                           \tag{3.1}
\]

For D=0 this forces L=0. Otherwise solving the quadratic in sqrt(L/D) gives

\[
L\le C_{\rm del}D,\qquad
C_{\rm del}=\left(\frac{1+\sqrt{1+4c}}{2c}\right)^2
=5.12781382311894\ldots<6.                                  \tag{3.2}
\]

An elementary conservative certificate is c>3/5 (pi<10/3). At L/D=6,
(3/5)*6-1=13/5>sqrt(6), and the left side of the resulting scalar inequality
is increasing thereafter. This proves L<=6D without relying on a decimal.
Deletion is by simple elements of unit mass only. This is not a deletion
bound for the non-simple or non-real sector.

## 4. A proved Bessel bound and O(D) positive energy

For any q-separated real set, the box exponential Gram matrix has operator
norm at most

\[
B_q=2+\frac2{3q^2}.                                        \tag{4.1}
\]

Proof. The majorant w(u)=2(1-|u|)_+ is at least one on [-1/2,1/2]. Its
Fourier transform is 2 sinc(t)^2. Thus the box quadratic form is bounded by
a matrix with entries 2 sinc(x_i-x_j)^2. The entries are nonnegative; its
row sum is at most
2+(2/pi^2) sum_(j!=i)|x_i-x_j|^-2 <= 2+2/(3q^2),
since the k-th neighbor on either side is at distance at least kq and
sum_(k>=1)k^-2=pi^2/6. The row-sum bound proves (4.1).

For q=1/2, B_q=14/3. Let Gamma_R be the retained Gram matrix and
X=Gamma_R-I. Its eigenvalues lie between -1 and B_q-1, so
||X||op<=B_q-1. Using (2.1) restricted to R,

\[
\|X\|_{HS}^2
=\operatorname{tr}(XZ_R)+\operatorname{tr}(XB_R)-\operatorname{tr}(XC_R)
\le\|X\|_{HS}\sqrt D+(B_q-1)D.                           \tag{4.2}
\]

Consequently

\[
\boxed{\|X\|_{HS}^2\le C_{\rm en}D,
\quad C_{\rm en}=\frac{25+\sqrt{141}}6=6.14572368117298\ldots<7.}
\tag{4.3}
\]

Gamma_R has diagonal one, so its HS error is exactly the positive ordered
sinc energy in (0.1). This proves the advertised 6D/7D theorem. Any subsequent
removal of retained simple elements can only decrease this positive energy.
No sign claim was made for individual complex-zero correlation terms.

## 5. Actual local matching of the retained simple sector

Partition the real axis into intervals of a prescribed length R>0. Fix
0<h<1/4. In each nonempty block of k retained simple points, use the parent's
pivot averaging argument, reproduced here: torus distance obeys

\[
\operatorname{dist}(t,\mathbb Z)^2\le\tfrac14\sin^2(\pi t).
\]

Every difference in the block has magnitude at most R, so some pivot phase
tau has squared phase cost at most pi^2 R^2 E_block/(4k). Delete points
farther than h from tau+Z. Their number is at most that cost divided by h^2.
The remaining nearest-integer labels are distinct: two equal labels would
have distance at most 2h<1/2, contradicting prior separation.
Summing over the disjoint blocks, and using k>=1 and (0.1), proves

\[
\boxed{n_{\rm deleted,total}\le
\left(6+\frac{7\pi^2R^2}{4h^2}\right)D,}                    \tag{5.1}
\]
\[
\boxed{\sum_{\rm final\ simple} |x_i-(\tau_{B(i)}+z_i)|^2
\le\frac{7\pi^2R^2}{4}D.}                                 \tag{5.2}
\]

The integer labels are injective **within each block**. Phases may differ
between blocks; this is not a global matching, and exact total mean mass one
has not been recovered. No joining of block boundaries is claimed.

For a sequence of finite source objects, put delta=D/N. Conditionally on
delta->0, fixed R,h give o(N) deletion and squared displacement. One may
also let R grow and h shrink if R^2 delta/h^2->0. For example for 0<delta<1,
R=delta^-1/8 and h=delta^1/8/8 give deleted fraction at most
6 delta+112 pi^2 sqrt(delta) and squared displacement/N at most
(7 pi^2/4)delta^3/4. These are conservative asymptotic rates, not a claim of
useful numerical error tolerance for genuine zeta data.

## 6. A simple-anchor exclusion bound involving the other sector

The slack also controls a=sum_simple ||P_U f_i||^2<=D/2. Fix an ordinate
radius 0<q<1/2 and a normalized depth cap A0>=0. For a non-real pair at
center t and depth a<=A0, g(u)=exp(2*pi*i*t*u)cosh(a*u) lies in U. If
|x-t|<=q, then

\[
|\langle f_x,g\rangle|\ge\cos(\pi q)\int_{-1/2}^{1/2}\cosh(au)\,du.
\]

Since integral(cosh^2)<=cosh(a/2) integral(cosh),

\[
\frac{|\langle f_x,g\rangle|^2}{\|g\|^2}
\ge\cos^2(\pi q)\frac{2\tanh(a/2)}a
\ge c(A_0,q):=\cos^2(\pi q)\frac{2\tanh(A_0/2)}{A_0}.      \tag{6.1}
\]

The last quotient is defined as one at A0=0; it decreases with A0 because
tanh(x)-x sech(x)^2>=0 for x>=0. The same lower bound covers a non-simple
real unit exponential at t (the a=0 case).
Thus the number of **simple anchors** within distance q of at least one
such non-simple center is at most

\[
\boxed{\frac{D}{2c(A_0,q)}.}                               \tag{6.2}
\]

This requires no bound on how many centers witness the same bad anchor.
It consequently does **not** bound the number or mass of those centers.
The constant grows only linearly for large A0, but still loses uniformity
if A0 grows while D/N has no corresponding rate. Pair centers can hide in
holes between simple anchors; no coverage theorem has been supplied.

## 7. Exact equality, and why it is not uniform near equality

For the genuine finite box exponential multiset with distinct locations
after multiplicities are aggregated,

\[
\boxed{D=0\ \Longleftrightarrow\
\text{all elements are real, all multiplicities are 1 or 2, and all distinct}
\ \text{locations belong to one translate of }\mathbb Z.}   \tag{7.1}
\]

Proof. Equation (1.1) forces b=0, A=Q and nu=2u. If a non-real pair were
present, b=0 would put each h_p in U. But the distinct complex exponential
functions are linearly independent on an interval: an exponential polynomial
vanishing there is identically zero, and its derivatives give a Vandermonde
system. The invertible change from each (f_z,f_bar-z) to (g,h) shows that no
such h_p lies in the span of the non-simple real vectors and all g vectors.
Therefore no non-real pair is present. The remaining v_j are independent,
so nu=2u makes every non-simple multiplicity exactly two. The a=0 slack
makes simple vectors orthogonal to U. On U, A=Q states sum_j v_jv_j*=P_U;
the number of unit columns equals dim U, so they are orthonormal. The same
argument holds for simple columns on E. Hence all distinct real exponentials
are mutually orthogonal, which is precisely sinc(x_i-x_j)=0 for i!=j, or
nonzero integer differences. The converse follows by substituting this
orthogonal weighted family. The empty family may be handled separately.

A single genuine pair z=+-i*a/(2*pi) illustrates the nonuniformity:

\[
D=2[(\sinh a/a)^2-1]=\tfrac23a^2+O(a^4)\to0,
\]

while its entire mass is off the real axis for every a>0. Exact equality
classification does not turn small D into a depth-free off-real count bound.

## 8. An exact no-trimming countermodel to the relaxed Hilbert inference

The following is an **abstract** signed unit-vector family, not a set of
exponential vectors with repeated simple real locations. For k>=2 put
r=k^2, n=4r. Take r orthonormal u_j and another orthogonal space containing
k copies of one simple unit vector e0, plus n-k other orthonormal simple
vectors. Let each of r pairs have

\[
g_j=\sqrt{1+t}\,u_j,\quad h_j=\sqrt t\,e_0,
\qquad t=(k-1)/(2r).
\]

The norm-difference hypothesis is exact. A has eigenvalue 2+(k-1)/r on U
and eigenvalue one on the simple span of dimension n-k+1. Thus

\[
N=6k^2,\quad D=3(k-1)+(k-1)^2/k^2,\quad
E_{\rm simple,raw}=k(k-1).                                 \tag{8.1}
\]

In particular D/N->0 while E_raw/N->1/6, and E_raw/D is unbounded. In the
cluster coefficient block the decomposition is exact with Z=0,
B=((k-1)/k)J_k and C=I_k-J_k/k. The nonzero projection remainder lies on U.
This shows why raw simple Gram **Frobenius** control cannot be deduced from
the abstract signed hypotheses alone. It does not refute a stronger theorem
that explicitly uses distinct genuine exponentials. The extraction theorem
retains that geometry in its separation and Bessel steps.

Small deletion count still need not mean small deleted operator HS energy;
the parent's collinear-atom obstruction remains in force. The 7D energy
bound concerns the **retained** simple subfamily.

## 9. Source dictionary and remaining obligations

For a finite conjugation-invariant multiset Z, take f_z(u)=exp(2*pi*i*z*u)
and g=(f_z+f_bar-z)/2, h=(f_z-f_bar-z)/(2i), on the box interval.
Then ||g||^2-||h||^2=1, and the finite signed operator has kernel
sum_z m_z exp(2*pi*i*z*(u-v)). Direct finite summation gives

\[
\|A\|_{HS}^2=\sum_{z,w}m_zm_w\operatorname{sinc}(z-w)^2.    \tag{9.1}
\]

The sum is real and nonnegative as a whole; individual summands need not be.
This is the box-profile specialization of the Hilbert setup in Lamzouri,
arXiv:2609.02882v1, Proposition 2.1. The Gram-decomposition argument in
Sections 1-2 is profile-independent when its normalization hypotheses hold;
the separation-to-lattice conclusions specifically use the box sinc kernel.
They cannot be imported unchanged into an optimized profile.

Remaining source obligations include actual arithmetic control of D, the
relation between weighted and unweighted zero sums, spatial localization,
and bringing the non-simple/non-real mass into the same local model with
correct total intensity. One also needs operator-energy control of discarded
atoms and short-source normalization/tail estimates. Neither all-zero wrap
consistency nor the earlier 5/108 budget has been proved here.

The earlier statement "positive energy cannot be obtained from a signed
defect" is now narrowed: it can be obtained after controlled deletion for
the simple real sector. It remains unproved for the full multiset.

## 10. Reproduction and evidence

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python check_simple_energy.py --samples 120 --output validation.json
```

The checker constructs finite signed exponential families using 160-point
Gauss-Legendre integration, compares their HS norm with the separate complex
sinc formula, verifies the exact slack/decomposition numerically, implements
maximal matching and blockwise matching, and checks the retained bounds.
It also checks 99 exact rational cluster identities and evaluates scalar
constants at 70 digits. The quadrature is not interval-certified. Scale-aware
floating tolerances and the tested ranges are in the code. The all-depth
and all-size assertions rely on the analytic arguments, not sampled tests.

The local Python backend was live checked. No upstream Lean build, full
repository CI/test suite, bundled computation inventory/record runner or
independent verifier was executed. Hashes and package-local handoff structure
are checked separately. The source was reread, not formally rebuilt.
