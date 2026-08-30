# A-RH-LCI-0003 — weighted finite-section tail scaling

Status: `solver_proof_candidate` (not independently verified)

Issue/run: `#32`, `run-20260829-rh-local-compactness-03`

This checkpoint refines the centered frequency-square route in
`principal-angle-and-depth.md`. It records a scale distinction that is easy to
miss: the existing complex-argument decay in Zeta23 is strong enough to make a
frequency-square weighted tail negligible at every fixed `lambda < 1`, but not
at the endpoint `lambda = 1` for arbitrary off-line depth.

## 1. Abstract grid-tail estimate

Let the complete frequency grid have spacing

\[
q=\frac{2\pi}{L}.
\]

Fix a zero ordinate `t`, a block center `c`, and suppose

\[
|t-c|\le H.
\]

Assume the Fourier coefficient obeys

\[
|\widehat\phi(t-\tau_k)|
\le\frac{K}{|t-\tau_k|^2}.
\tag{1.1}
\]

Suppose `t` is at distance at least `D` from the endpoints of the finite grid
interval and `D >= 2q`. Every omitted grid point then has distance at least

\[
D/2+jq,
\qquad j\ge0,
\]

on one of the two sides. Since

\[
|\tau_k-c|^2
\le2|\tau_k-t|^2+2H^2,
\]

the omitted weighted energy satisfies

\[
E_{\rm wt,tail}
\le2K^2\left(\Sigma_2+H^2\Sigma_4\right),
\tag{1.2}
\]

where the two-sided sums obey

\[
\Sigma_2
\le\frac8{D^2}+\frac4{qD},
\qquad
\Sigma_4
\le\frac{32}{D^4}+\frac{16}{3qD^3}.
\tag{1.3}
\]

Indeed, for `a=D/2`,

\[
\sum_{j\ge0}(a+jq)^{-p}
\le a^{-p}+\int_0^\infty(a+qx)^{-p}dx,
\]

and there are two tails. Combining (1.2)--(1.3),

\[
\boxed{
E_{\rm wt,tail}
\le
2K^2\left[
\frac8{D^2}+\frac4{qD}
+H^2\left(
\frac{32}{D^4}+\frac{16}{3qD^3}
\right)
\right].
}
\tag{1.4}
\]

For `H=o(D)`, the leading term is `O(K^2/(qD))`.

## 2. Substitution of the Zeta23 scales

For the Zeta23 grid,

\[
L=\lambda\log(T/2\pi),
\qquad
q=2\pi/L,
\qquad
D_0=T^{1/2}.
\]

The complex-argument tail estimate used by `Zeta23/Tail.lean` has

\[
K=e^{L/4}C_1=X^{1/4}C_1,
\qquad
K^2=X^{1/2}C_1^2,
\qquad
X=(T/2\pi)^\lambda.
\tag{2.1}
\]

Therefore (1.4) gives, per interior evaluation vector,

\[
\boxed{
E_{\rm wt,tail}
\ll C_1^2\frac{LX^{1/2}}{D_0}
\asymp
C_1^2\log T\,T^{(\lambda-1)/2},
}
\tag{2.2}
\]

up to fixed powers of `2*pi` and lower-order `H/D_0` terms.

Consequences:

- if `lambda < 1`, the existing decay proves a vanishing weighted tail;
- at `lambda=3/4`,
  \[
  E_{\rm wt,tail}=O(\log T\,T^{-1/8});
  \]
- at `lambda=1`, the same argument gives only `O(log T)`, so it does not
  justify discarding the weighted tail for arbitrary off-line zeros.

For on-line zeros the Fourier argument is real and the taper bound has no
`e^{L/4}` loss. Then `K=O(C_1)` and the weighted tail is

\[
O(L/D_0)=O(\log T\,T^{-1/2})
\]

even at `lambda=1`. The endpoint obstruction is specifically the worst-case
complex horizontal displacement.

## 3. Boundary mass

The estimate applies to ordinates at distance `D_0` from the finite-grid
endpoints. The source already treats the boundary layer separately and records
that its zero multiplicity is `O(D_0 log T)`, which is `o(N(T,2T))`.
Therefore a future weighted-trace proof may:

1. discard or charge the boundary layer;
2. use (2.2) on the interior;
3. restore the discarded mass in the final error budget.

This does not yet prove that the weighted observable itself has the required
prime-side lower bound.

## 4. Refined hybrid architecture

The scale calculation changes the preferred topology of the argument.

- Use `lambda=1` only for the original scalar defect and local random-coset
  compactness, where the existing unweighted tail estimate is strongest.
- Use `lambda=3/4` for both:
  1. the `5/108` sub-Nyquist aliasing gap;
  2. the centered frequency-square depth observable.

Thus the same short-scale compression can potentially certify both integer
occupancy variance and small mean squared off-line depth. No separate endpoint
weighted matrix is required.

A fallback split is also possible: use the endpoint weighted trace only for a
priori shallow pairs, where `e^{|delta|L/2}` is bounded, and route deeper pairs
to the principal-angle defect.

## 5. New exact bottleneck

After this tail calculation, the weighted route is no longer blocked by a
vague finite-section concern at `lambda=3/4`. Its main unresolved obligation is
now the prime-side centered trace estimate

\[
\mathfrak M_c
\ge B_\phi N-A_\phi\varepsilon N
\]

on mesoscopic ordinate blocks, with enough uniformity to make `epsilon -> 0`.
The current Zeta23 `LocalHyps` already contains the real second-frequency
moment `integral phiHat(r)^2 r^2`, but the required complex weighted Poisson
identity and prime-side assembly are not present as headline source results.

## 6. Boundary

Exact in this checkpoint: the grid-sum inequalities (1.3), the weighted tail
bound (1.4), and the asymptotic scale substitution (2.2) under the stated decay
hypothesis.

Open: source-normalized constants, complex weighted Poisson formalization,
prime-side centered trace, interaction with the tail matrix rather than single
vectors, and the final `5/108` budget. No zeta-zero proportion or RH claim is
made.
