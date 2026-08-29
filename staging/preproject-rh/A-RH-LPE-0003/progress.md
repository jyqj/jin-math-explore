# A-RH-LPE-0003 progress ledger

Append-only solver record. Claims remain unverified until a fresh independent-verifier run checks frozen hashes.

## 2026-08-29 — checkpoint 1: local phase synchronization

Derived the weighted theorem

```text
sum_i w_i dist_T(x_i-tau,Z)^2
  <= pi^2 R^2 E_sinc / (2 lambda_G)
```

from four exact steps:

1. `|exp(2pi i x)-exp(2pi i y)|^2 = 4 pi^2 (x-y)^2 sinc(x-y)^2`;
2. the weighted graph Poincaré inequality;
3. projection of the weighted phase mean to the unit circle with at most a factor two loss;
4. `dist_T(u,Z)^2 <= |exp(2pi i u)-1|^2/16`.

No Zeta23 graph or spectral gap was assumed.

## 2026-08-29 — checkpoint 2: complete blocks remove the local-gap conjecture

For one bounded block, chose complete edge weights `a_ij=w_i w_j`. The exact identity

```text
sum_{i<j} w_i w_j |f_i-f_j|^2
  = W sum_i w_i |f_i-fbar|^2
```

shows `lambda_G=W`. Therefore local sinc energy alone controls distance to a blockwise lattice phase. This is materially stronger than the initial plan: no separate local expander or spectral-gap theorem is needed inside a complete bounded block.

## 2026-08-29 — checkpoint 3: random-partition extraction

For global ideal energy `E=eN`, partitioned the line into shifted blocks of length `R`. The complete-block theorem gives total phase loss at most `(pi^2 R^2/2)E`, uniformly in the shift. Averaging the shift makes boundary mass at most `(2r/R)N` for fixed local radius `r`.

After deleting phase-bad and boundary mass, the deleted fraction is at most

```text
(pi^2/2) R^2 e / eta^2 + 2r/R.
```

Balancing all three convergence scales with

```text
R=e^(-1/5), eta=e^(1/5)
```

gives deleted fraction `O_r(e^(1/5))`, positional error `e^(1/5)`, and block length tending to infinity. This supplies a finite quantitative route from `E=o(N)` to blockwise local lattice support.

## 2026-08-29 — checkpoint 4: global phase not required

Extended the ideal two-scale occupancy inequality to multiple cyclic blocks with different phases and different local densities. Nonnegativity of the short sinc-squared kernel permits deletion of cross-block terms. The block constant-mode contributions combine by Cauchy--Schwarz, recovering exactly

```text
s1/N >= 2 - 1/theta - alpha*theta/(3 omega_alpha) - epsilon/omega_alpha.
```

Thus the parent `alpha=3/4` gain does not require one global phase across the whole height window.

## 2026-08-29 — checkpoint 5: finite-section corrections

Derived two finite corrections.

1. **Toeplitz boundary:** with missing row sums `b_i`,

   ```text
   <m,T_d m> >= (omega-rho)V + N^2/(alpha d)
                 - mu^2(B_d+C_d/rho),
   ```

   with explicit `B_d=O(log d)` and `C_d=O(1)` bounds.

2. **Approximate cells:** for `alpha=3/4` and cell displacement at most `eta<=1/4`,

   ```text
   |Q_actual-Q_lattice| <= 25.226 eta sum_n m_n^2.
   ```

   The coefficient comes from an explicit `ell^1` bound on sampled derivatives of `sinc^2(3t/4)`.

## 2026-08-29 — checkpoint 6: deterministic checks

Command:

```bash
python3 check_phase_synchronization.py \
  --trials 250 \
  --size 24 \
  --overlap-points 16 \
  --seed 20260829 \
  --max-power 9
```

Observed locally on the exact script content committed to the branch:

```text
PASS local phase synchronization; worst loss-bound=-3.766e+02
PASS complete-block specialization; gap error=9.237e-14; worst loss-bound=-8.637e+00
PASS overlap phase stitching; worst lhs-rhs=-4.192e-01
PASS Toeplitz boundary correction; worst lower-form=-5.100e+00
PASS approximate-cell kernel stability; C=25.225491563; worst |delta Q|-bound=-9.270e-01
PASS random-partition extraction; worst loss=-2.697e+00; worst bad-mass=-6.915e+01
PASS disconnected two-coset model; best global loss=0.250000000625
PASS low-gap path scaling; n=512; gap=3.765e-05; energy=1.942e-03; loss=4.267e+01; bound=2.555e+02
```

The negative margins only show that sampled finite cases satisfy the proved inequalities. They do not measure sharpness and do not replace proof.

## Current frontier

The first extraction subproblem is closed **conditionally on an effective on-line ideal energy `E=o(N)`**. The next decisive question is now:

```text
Does near equality of the full Zeta23 indefinite P+Q certificate
force the effective on-line complete sinc/taper energy to be o(N),
after charging normalization leakage, pair negative spectrum and tails?
```

If yes, this attempt supplies a quantitative local-lattice reduction and the finite short-kernel corrections. If no, the required output is an admissible `P+Q` countermodel respecting complete-frame pair inertia, not merely an abstract hyperbolic cancellation example.

## Cannot imply

- The parent rank--trace defect decomposition is not yet independently verified.
- The full indefinite certificate has not been separated into the required on-line energy estimate.
- The actual smooth taper and finite section have not been shown to meet the parent error budget.
- No unconditional zeta-zero proportion has been improved.
- This ledger does not prove or refute RH.
