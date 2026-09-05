# G7 legal-domain repair candidate — CP-G7-0001

Status: **solver proof candidate; independent verification pending**.
Issue #41; base `70484b065fc3b6a64f06955a5f9c895531750891`.
This is not a proof of the Li–Liu main theorem or binary Goldbach.

## 0. Inputs, notation, and inherited obligations

Source keys and access boundaries are in `source-lock.json`.
`LLv2` denotes Li–Liu arXiv:2606.05224v2, specifically Lemmas 2.2 and 2.5,
the definition of G7, and (5.31)–(5.32). `BV-Vaughan` is Vaughan's proof
notes, Main Theorem, pp. 1–3. The lower-sieve theorem and classical
Bombieri–Vinogradov/PNT are imported mathematical inputs, not reproved here.
No unverified result of the sibling L35 attempt is used.

The old v0.3 interface audit already identified the illegal rectangle and
proposed truncation (`GB-D035`, `GB-D037`, `GB-D038`,
`ISS-G7-LEMMA2.5-DOMAIN`). The extra 1/v in (5.31) was already recorded as
`GB-A009`; it is not a new discovery. The old 1D slice reduction is reused.
This attempt adds explicit losses, a missing-cap diagnosis, a new comparison
certificate, and a classical-BV aggregation argument. No literature novelty
claim is made. Legacy file hashes are reported commitments, not rehashed bytes.

Write

\[
a=4/53,\quad b=4/33,\quad g=3/11,\quad
c=1/2-2a=37/106,\quad R=[a,b]\times[b,g].
\]

Here a is the sieve exponent, NOT the paper's parameter 1.9; g is NOT Euler's
constant gamma_E. Let 0<eps0<1/2 be fixed, Y=(1-eps0)N, N even, and
A={N-p: p prime, p<Y}. P_N(z) is the product of primes p<z not dividing N.
With m=p1*p2, G7 is the sum of S(A_m,P(N),N^a) over
N^a<=p1<=N^b<=p2<=N^g and (m,N)=1. It is an unweighted nonnegative sum.
The singular factor is the C(N) of LLv2 (1.3).

To eliminate the possible common endpoint p1=p2=N^b, work first with
p1<N^b<=p2; discarded original terms are nonnegative. The integral endpoint
is unchanged, and endpoint changes in reciprocal-prime sums are O(N^-a).

## 1. Restrict before invoking the lower sieve

Fix an error-saving exponent A0>2. Classical BV in prime-counting form gives,
for some B0=B0(A0),

\[
\sum_{d\le Y^{1/2}/(\log Y)^{B0}}
\max_{(r,d)=1}|\pi(Y;d,r)-\operatorname{Li}(Y)/\varphi(d)|
\ll_{A0}Y/(\log Y)^{A0}.
\tag{BV}
\]

Use the strict prime-count convention at Y; equivalently use the left limit
in the maximal-endpoint form of BV. This avoids assigning an O(1) endpoint
error to every modulus. Choose B=B0+1, D=N^(1/2)/(log N)^B, z=N^a,
Q_m=D/m, and

\[
h=h_N=B\log\log N/\log N.
\]

For fixed eps0 and sufficiently large N the BV modulus cutoff contains D.
The exact lower-sieve condition is

\[
z\le Q_m^{1/2}
\quad\Longleftrightarrow\quad
u+v\le c-h,\qquad u=\log p1/\log N,\ v=\log p2/\log N.
\tag{1}
\]

Consequently restrict the original sum to R_h=R intersect {u+v<=c-h}.
Every summand dropped from G7 is nonnegative, so this is a valid lower bound.
No lower-sieve theorem is invoked outside its domain. The fixed illegal part
u+v>c is NOT described as a thin moving layer.

The parameter actually supplied to f is

\[
s_h(u,v)=(1/2-u-v-h)/a=s_0(u,v)-h/a,
\quad s_0=(1/2-u-v)/a.
\tag{2}
\]

It is not s_0. Ignoring this shift over the whole retained region loses a
first-order error, even after the moving domain itself is handled.

## 2. Normalized kernel and two different losses

Put Fhat(s)=f(s)/(2 exp(gamma_E)), extended by zero for s<=2.
For 2<=s<=4, Fhat(s)=log(s-1)/s. For 4<=s<=6,

\[
\widehat f(s)=[\log(s-1)+T(s)]/s,\quad
T(s)=\int_3^{s-1}\frac{dt}{t}\int_2^{t-1}\frac{\log(x-1)}x\,dx\ge0.
\]

Only s<=smax=1061/264<5 occurs. On [2,smax], Fhat is nonnegative,
nondecreasing, and 1-Lipschitz. Here are explicit elementary bounds:
for 2<=s<=4, the derivative numerator is s/(s-1)-log(s-1)>4/3-6/5>0
and the derivative is at most 1/2. For 4<=s<=smax,
0<=T'(s)<=1/6 and 0<=T(s)<=(s-4)/6<=5/1584. Also
log(s-1)<=log(797/264)<6/5. Thus the derivative numerator is at least
1061/797-6/5-5/1584>0, and its upper bound is no larger than
(1/(s-1)+T'(s))/s<=1/8. The exponential-series checks for these log bounds
are exact rational tests in `check_g7.py`. The zero extension is Lipschitz.

Define the corrected asymptotic coefficient and its finite-level analogue:

\[
g_R=\frac4a\iint_R\widehat f(s_0)\frac{du\,dv}{uv},\qquad
 g_h=\frac4a\iint_{R_h}\widehat f(s_h)\frac{du\,dv}{uv}.
\tag{3}
\]

For 0<=h<=a split g_R-g_h into the omitted strip and the retained-kernel shift.
In the strip c-h<u+v<=c, put w=c-u-v. Then s_0=2+w/a<=3, and
Fhat(s_0)<=w/(2a). Therefore

\[
0\le\frac4a\iint_{R\cap\{c-h<u+v\le c\}}\widehat f(s_0)\frac{du\,dv}{uv}
\le\frac{b-a}{a^3 b}h^2=\frac{14045}{16}h^2.
\tag{4}
\]

The proof integrates w from 0 to h, enlarges the u-projection to [a,b],
and uses uv>=ab. This only enlarges the nonnegative upper bound.
On R_h the 1-Lipschitz estimate instead gives

\[
0\le\frac4a\iint_{R_h}[\widehat f(s_0)-\widehat f(s_h)]\frac{du\,dv}{uv}
\le\frac4{a^2}\log(b/a)\log(g/b)h
\le\frac{70225}{132}h.
\tag{5}
\]

The last inequality uses log x<=x-1. Hence the explicit safe result is

\[
\boxed{0\le g_R-g_h\le (70225/132)h+(14045/16)h^2.}
\tag{6}
\]

The O(h^2) bound applies to the strip only, NOT to total finite-level loss.

## 3. New source diagnosis: the missing gamma cap in (5.32)

In the rendered v2 PDF, printed p.37, the first integral in (5.32) is over
v<=g, but the next equality expands its base term up to v=c-u without a min.
Since

\[
c-a-g=1/1166>0,
\]

this inserts a positive triangle

\[
\mathcal T=\{a<u<c-g,\quad g<v<c-u\}
\]

which is not part of G7's original rectangle. The required upper limit is
min(g,c-u). This is a local false equality in the displayed expansion; it
is not a refutation of the underlying theorem.

Let Delta be the normalized base-term integral over this triangle. Its kernel
has s_0 near 2, so the T(s) correction is zero there. Set d=c-a-g=1/1166.
The same bound Fhat(s_0)<=w/(2a), now with uv>=a*g, gives

\[
\boxed{0<\Delta\le\frac{d^3}{3a^3g}=\frac1{557568}
<1.794\cdot10^{-6}.}
\tag{7}
\]

Indeed the triangle integral of w=c-u-v is d^3/6. Nonempty interior and
strictly positive kernel prove Delta>0. This is registered as
`ISS-G7-CAP-5.32`. It refines the source audit without overwriting GB-A009.
We do NOT infer what the authors' unpublished numerical code calculated.
The old project reported a rectangle-compatible value, but its full original
numerical scripts have not been rerun in this attempt.

## 4. A comparison integral that avoids the positive higher correction

For t=u+v, define

\[
l(t)=\max(a,t-g),\quad r(t)=\min(b,t-b),\quad
 W(t)=\frac1t\log\frac{r(t)(t-l(t))}{l(t)(t-r(t))}.
\]

This is the exact integral of 1/[u(t-u)] over the rectangle slice. The three
pieces, with endpoints a+b,2b,a+g,c, are respectively
(l,r)=(a,t-b),(a,b),(t-g,b).

Omit T(s)>=0 rather than approximating it. Then

\[
g_R\ge I_0:=\int_{a+b}^{c}H(t)W(t)\,dt,\quad
H(t)=\frac{4\log((1/2-a-t)/a)}{1/2-t}.
\tag{8}
\]

The normalization follows from (4/a)*[log(s_0-1)/s_0]. The inequality,
not equality, is crucial near the small s_0>4 part of the region.
The upper endpoint of an I0 certificate is NOT an upper bound for g_R.

## 5. Piecewise quadrature certificate

Use composite midpoint quadrature independently on the three smooth pieces.
Put y=1/2-t and L0(t)=log((y-a)/a). Direct differentiation gives

\[
H'=4[L0/y^2-1/(y(y-a))],
\]
\[
H''=4[2L0/y^3-2/(y^2(y-a))-1/(y(y-a)^2)].
\]

Throughout the range,
t>=19/100, y>=3/20, y-a>=3/40, and 0<=L0<=6/5.
Set A(t)=log r+log(t-l)-log l-log(t-r). Every log argument is affine
with slope 0 or 1 and lies in [3/40,1]. Thus
|A|<=12, |A'|<=4/(3/40), |A''|<=4/(3/40)^2.
For W=A/t use

\[
|W|\le A_0/t_0,\quad |W'|\le A_1/t_0+A_0/t_0^2,\quad
|W''|\le A_2/t_0+2A_1/t_0^2+2A_0/t_0^3.
\]

Combine these with the above H derivative bounds via
|(HW)''|<=H2*W0+2*H1*W1+H0*W2. The exact rational envelope evaluates to

\[
333783040000/185193<2,000,000.
\tag{9}
\]

Breakpoints are integration boundaries, so no global C2 assertion at those
breakpoints is needed. With n=8192 intervals per piece, total quadrature error
is bounded by

\[
\frac{2,000,000}{24n^2}\sum_i(t_{i+1}-t_i)^3
=\frac{855453546875}{538568036349640704}
<1.588385291\cdot10^{-6}.
\tag{10}
\]

`mpmath.iv` at 50 decimal digits encloses all midpoint arithmetic and logarithms.
Exact Fraction arithmetic expands the interval by (10), and decimal output is
rounded outward using integer division, without an intermediate binary float.
The ACTUAL executed result is

\[
I_0\in[3.790296429629882382,\ 3.790299606400463397].
\tag{11}
\]

Therefore g_R>3.79029 even after restoring the gamma cap and discarding T(s).
The proof of (9) and I0<=g_R is manual solver mathematics; the script checks
its rational envelope, evaluates the intervals, and verifies hashes. This is
not a theorem-prover kernel certificate or an independent mathematical audit.

## 6. Aggregating the discrete remainder using classical BV

For retained m=p1*p2 and q|P_N(z), all prime factors of q are <z, whereas
p1,p2>=z. Hence (m,q)=1, and with (m,N)=(q,N)=1,

\[
|A_{mq}|=\pi(Y;mq,N),\quad X_m=\operatorname{Li}(Y)/\varphi(m),\quad
r_m(q)=\pi(Y;mq,N)-\operatorname{Li}(Y)/\varphi(mq).
\tag{12}
\]

These are exact under the strict prime-count convention. The local sieve
density is 1/(q-1) at each sieving prime q (here q prime); the product-density
condition (2.6) has a uniform absolute K: removing primes dividing N only
reduces the interval product ratio, which is bounded by the full odd-prime
product and the classical Mertens estimate. Finite small endpoints are absorbed
in K. No prime 2 occurs because N is even.

Lemma 2.5 supplies at most L=exp(8 eta^-3) weights for each m, with
|lambda^-_{m,l}(q)|<=1 and support q<Q_m. Map (p1,p2,q) to d=p1*p2*q.
This map is injective in the half-open p1,p2 ranges: the two prime factors of d
at least z determine m and its unique p1<p2 ordering, and q=d/m contains only
smaller primes. Also d<D. Thus, allowing a harmless factor 2 for endpoint
conventions, the aggregate lower-sieve remainder is bounded in absolute value by

\[
2L\sum_{d<D}\max_{(r,d)=1}
|\pi(Y;d,r)-\operatorname{Li}(Y)/\varphi(d)|
\ll_{A0,eta,eps0} N/(\log N)^{A0}.
\tag{13}
\]

In particular, no uncontrolled divisor multiplicity and no L35/Fouvry input
are needed for this G7 branch. The absolute-value bound is safe here because
ordinary BV already controls the absolute sum at the smaller level D.

On R_h, log Q_m>=2a log N, so the lower-sieve error is uniform:

\[
E_*\ll\eta+\eta^{-8}e^K(2a\log N)^{-1/3}.
\]

For the prime sum to integral transfer, the reciprocal-prime measures in fixed
positive exponent ranges have cumulative distribution
log(t/t_min)+O_a(1/log N). The kernel Fhat((1/2-u-v-h)/a), zero-extended,
is bounded and uniformly Lipschitz in each variable by Section 2. Apply
Stieltjes partial summation first in v and then in u; the total variations and
endpoint bounds are uniform in 0<=h<=a, giving O_a(1/log N). This establishes
an asymptotic with error, NOT the paper's unqualified termwise sum>=integral.
Primes dividing N remove reciprocal mass O_a(N^-a); replacing 1/phi(m) by
1/(p1*p2) and changing shared endpoints costs O_a(N^-a).

Finally

\[
V_N(N^a)=\frac{2e^{-\gamma_E}C(N)}{a\log N}
 [1+O_a(1/\log N+N^{-a})].
\]

For primes dividing N above N^a, there are at most 1/a of them and each tail
factor differs from 1 by O(N^-a); this checks uniformity in the even integer N.
Also Li((1-eps0)N)=(1-eps0)N/log N*[1+O_eps0(1/log N)]. Therefore

\[
\frac{G7}{C(N)N/\log^2N}
\ge(1-eps0)g_h
-O_{a,eps0}\bigl(\eta+\eta^{-8}e^K(2a\log N)^{-1/3}+1/\log N+N^{-a}\bigr)
-O_{A0,eta,eps0}\bigl((\log N)^{2-A0}/C(N)\bigr).
\tag{14}
\]

Combining (6), (8) and the certified lower value in (11), one may replace the
first term by

\[
(1-eps0)\bigl[3.790296429629882382-(70225/132)h-(14045/16)h^2\bigr].
\tag{15}
\]

All harmful terms are exported in `error-handoff.json`. First choose desired
slack, then sufficiently small fixed eps0 and eta, then A0>2 and B from BV,
and only then N0(eps0,eta,A0,B). L may be enormous but is fixed before N.
This yields a local asymptotic G7 lower-bound candidate and preserves the
working coefficient 3.79029 for suitable choices. It gives neither a numerical
N0 nor the common N0 for all twelve terms.

## 7. Verdict and review frontier

Solver verdict: PASS, scoped to the candidate (1)–(15) under the declared
standard sieve/BV/PNT inputs. Source-byte integrity, independent mathematical
verification, and global reconciliation remain open. The new cap defect is
locally repairable and its correction does not exhaust the certified main-term
margin. This says nothing about the truth of the remaining Li–Liu proof.

A fresh verifier should check the domain and sign; the fhat bounds and separation
of O(h) from O(h^2); the positive cap triangle; 1D reduction and derivative bound;
actual interval trust basis; injectivity in (13); uniform sieve density and
Stieltjes transfer in (14); and the exact quantifier/order of every handoff.
No frozen sibling candidate or main authority was modified.
