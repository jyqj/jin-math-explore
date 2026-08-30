# A-RH-LCI-0003 — period-six confluent clock angle theorem

Status: `solver_proof_candidate` (not independently verified)

Issue/run: `#32`, `run-20260829-rh-local-compactness-03`

This checkpoint tests the quantitative principal-angle route on the exact
period-six occupancy law already retained by the earlier attempts:

\[
(1,1,1,1,2,0).
\]

A load-two site is now interpreted as an off-line reflection pair with common
ordinate, and the empty site supplies the missing Fourier degree of freedom.
The result is positive: in the ideal clock model the pair's normalized
negative/confluent direction stays uniformly transverse to the positive span
for every bounded normalized depth. Thus the abstract hyperbolic-swap
countermodel is not realized by the canonical clock extremizer.

## 1. Fiberization of the period-six marked clock

Normalize the physical interval to

\[
I=[-1/2,1/2]
\]

and put

\[
I_0=[-1/2,-1/3).
\]

Choose distinct residues `p,e in Z/6Z`. The residue `p` is the load-two pair
site, `e` is the empty site, and the remaining four residues are simple
on-line sites. For normalized horizontal depth `a >= 0`, use the six
generators

\[
\{e^{2\pi i r s}:r\notin\{p,e\}\},
\quad
e^{2\pi i p s}\cosh(as),
\quad
e^{2\pi i p s}\frac{\sinh(as)}a,
\tag{1.1}
\]

where the last generator is interpreted as `s e^{2 pi i p s}` at `a=0`.
Their translates by the sublattice `6Z` are obtained by multiplying by
`e^{2 pi i 6m s}`.

Under the standard six-fiber unitary

\[
f(s)\mapsto(f(x+j/6))_{j=0}^5,
\qquad x\in I_0,
\]

the system is controlled by a `6 x 6` matrix `M_{a,p,e}(x)`. Its first four
columns are discrete Fourier columns. The last two are

\[
\omega^{pj}e^{2\pi i p x}\cosh(a(x+j/6)),
\quad
\omega^{pj}e^{2\pi i p x}\frac{\sinh(a(x+j/6))}a,
\qquad
\omega=e^{2\pi i/6}.
\tag{1.2}
\]

Therefore the infinite marked clock is a Riesz system exactly when the fiber
matrices are uniformly invertible.

## 2. Exact determinant reduction

Let

\[
r=e^{a/6},
\qquad
A_q(r)=\sum_{j=0}^5(r\omega^{-q})^j,
\qquad
q=e-p\pmod 6.
\]

After eliminating the four simple Fourier columns, the determinant reduces to

\[
\Delta_q(r)
=\frac12\left[
A_0(r^{-1})A_q(r)-A_0(r)A_q(r^{-1})
\right].
\tag{2.1}
\]

The dependence on the fiber phase `x` cancels. For the unnormalized `sinh`
column,

\[
|\det M_{a,p,e}(x)|^2=36|\Delta_q(r)|^2.
\tag{2.2}
\]

The three symmetry classes are

\[
|\Delta_q(r)|^2=
\begin{cases}
\displaystyle
\frac{(r-1)^2(r+1)^6(r^2-r+1)^2(r^2+r+1)^4}{4r^{10}},
&q=1,5,\\[1.1em]
\displaystyle
\frac{3(r-1)^2(r+1)^6(r^2-r+1)^4(r^2+r+1)^2}{4r^{10}},
&q=2,4,\\[1.1em]
\displaystyle
\frac{(r-1)^2(r+1)^2(r^2-r+1)^4(r^2+r+1)^4}{r^{10}},
&q=3.
\end{cases}
\tag{2.3}
\]

Every factor is strictly positive for `r>1`. Hence every positive-depth
period-six pair/empty placement is fiberwise invertible.

For the normalized confluent column `sinh(as)/a`, divide the determinant in
(2.2) by `a`. The three limits of the determinant magnitude as `a -> 0` are

\[
36,\qquad 12\sqrt3,\qquad18
\tag{2.4}
\]

for `q=1/5`, `q=2/4`, and `q=3`, respectively. Thus the normalized fiber
matrix extends continuously and invertibly through `a=0`.

### Consequence

For every fixed `a_0 < infinity`, compactness of

\[
[0,a_0]\times I_0\times\{(p,e):p\ne e\}
\]

gives a constant

\[
\gamma(a_0)>0
\]

such that every normalized period-six confluent fiber satisfies

\[
\|M_{a,p,e}(x)c\|^2\ge\gamma(a_0)\|c\|^2,
\qquad0\le a\le a_0.
\tag{2.5}
\]

This is an existence statement with an explicit determinant certificate. A
usable source-level proof would still need a quantitative lower bound rather
than compactness alone.

## 3. Exact shallow principal-angle constant

At `a=0`, the positive span is the span of all standard Fourier residue
vectors except the empty residue `e`. The normalized negative direction is

\[
v_{p,x}(j)=(x+j/6)\omega^{pj}.
\]

Let `q=e-p mod 6`. Its component in the missing residue has squared norm

\[
\frac1{6|1-\omega^q|^2}.
\tag{3.1}
\]

Moreover

\[
\sum_{j=0}^5(x+j/6)^2
=6x^2+5x+\frac{55}{36}
\le\frac{19}{36},
\qquad x\in I_0.
\tag{3.2}
\]

Since

\[
|1-\omega^q|^2\in\{1,3,4,3,1\},
\]

the exact squared principal angle obeys

\[
\boxed{
\eta_{0,p,e}(x)
\ge\frac3{38}
}
\tag{3.3}
\]

for every placement and phase. Equality occurs when the pair and empty sites
are opposite residues (`q=3`) and `x` is an endpoint of the fundamental cell.
For adjacent pair/empty residues the stronger bound is `6/19`.

Thus the normalized negative direction of a shallow pair does not approach
the positive span in the canonical extremal clock law. The only small factor
in the physical negative vector is its amplitude `a`, already captured by the
quartic depth factor in the parent angle-defect estimate.

## 4. Fixed-width taper edges give an exceptional-fiber error

The source taper is not the ideal box, but it equals one on

\[
[-L/2+w,L/2-w].
\]

After rescaling by `L`, the total edge-ramp length is `2w/L`. In the six-fiber
partition, the set of base phases for which at least one row meets a ramp has
measure at most `2w/L`, hence relative measure at most

\[
12w/L
\tag{4.1}
\]

inside the fundamental interval of length `1/6`.

On all other fibers the tapered matrix is exactly the box matrix. For
`0 <= a <= a_0`, the generator entries are uniformly bounded, so the negative
energy carried by the exceptional fibers is `O_{a_0}(w/L)`. Consequently the
box-model angle lower bound transfers to an **averaged** bounded-depth estimate
with an `O_{a_0}(w/L)` loss.

This is not a uniform pointwise Riesz bound for the tapered system: all
columns share a taper that vanishes at the endpoints, so the essential
pointwise minimum can be zero on ramp fibers. The correct source target is an
averaged Schur-complement estimate plus an explicit exceptional-energy charge.

## 5. What this rules out and what survives

Ruled out in the ideal period-six model:

- realization of the exact hyperbolic-swap cancellation by the canonical
  `(1,1,1,1,2,0)` clock extremizer;
- shallow-depth angle collapse after divided-difference normalization;
- the claim that a fixed-width taper destroys all angle information in bulk.

Still open:

- arbitrary stationary/random-coset mark laws rather than one period-six law;
- clusters with several pair sites and several empty sites in a long block;
- quantitative control of exceptional ramp fibers for unbounded normalized
  depth;
- transfer from local-compactness limits to a positive-density averaged angle;
- integration with the `5/108` budget and the source tail/prime seams.

The most focused next countermodel search is now: find a stationary critical-
density marked lattice law with simple density at most `2/3` whose positive
and normalized-negative polyphase spans have zero averaged Schur gap. The
period-six extremizer does not provide one.

## 6. Authority boundary

Equations (2.1)--(2.4) and (3.1)--(3.3) are finite algebraic proof candidates
with deterministic checks. Equation (2.5) follows by compactness once those
identities are verified. The taper statement is an averaged perturbative
reduction, not a completed source theorem.

No unconditional zeta-zero proportion is improved and no RH claim is made.
