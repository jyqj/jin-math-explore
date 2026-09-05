# Independent verification specification: first-row contraction candidate

Candidate: A-TP-186-CONTRACTION-0005. Solver issue #59. The Git commit and full
artifact digest are fixed by the separate verifier Issue after upload. This file
is a ticket specification, NOT a completed verifier receipt.

Use a NEW run/context with role independent_verifier. Receive only the frozen
source package, full artifact or its deterministic rebuild, pinned primary
sources, and this ticket. Do not inherit solver conversation, repair candidate
files, or infer correctness from a solver PASS. #39 and #47 remain separate.

## Exact target and allowed assumptions

For the fixed Challenge.lean source functions at upstream commit
61340d0b74163003b32756bb16e91d9209a5e330, audit the two claims

```
physicalSourceOuterRoot 0 0 <= (10.396041) * I0 / 10^18 < 11*I0/10^18
physicalSourceOuterFace 0 0 <= (2.513205) * I0 / 10^18 < 10*I0/10^18
I0 = 23685317816 / 10^24
```

External physical density/cap/Mecke identities must be explicitly accepted or
verified from the main manuscript (3.15),(3.16),(3.24),(3.25). The frozen low-kernel
and marginal-enclosure derivations are candidates to inspect, not admitted
independent results. The current proof does not reprove the deep distribution
inputs or the final sieve-to-DHL theorem.

## Verification matrix

V1 — Source and geometry. Match the 77 coefficient integers, 11 signatures,
profile, h, radial center, source row, theta189, indices2331/3498/49152,
radial94919..95638, unitsI0 and actual two Lean targets. Check strict endpoints,
row clipping, cap domination and 40 versus39 coordinates. Match all source hashes.

V2 — Continuous low kernel. Reprove the tilted physical decomposition, the
mark-count/Palm identity, and why flooring the low cutoff and ceiling the mark
cutoff increases the nonnegative integrand. Verify no missing Poisson prefactor,
no use of a cell-mass bound as an unjustified pointwise density bound, and the
correct retained/erased coordinate meanings.

V3 — Seed and full Eulerian counts. Verify the renewal rectangle recurrences and
exp enclosure. Check the Eulerian carry convention C_(n+1)/C_(n+2), all0..42
unmarked terms, effective41 after a mark, support-based truncation, factorials,
and exact positive rounding. No tail approximation is used in this candidate.

V4 — Exact backend. Verify Kronecker radix headroom including zeros, scalar
fallbacks, truncation and unequal array lengths. Review the small C++ GMP
import/mul/export wrapper and Python interval rounding. Rebuild rather than use
a distributed shared object. Confirm no negative coefficients reach this
nonnegative multiplication interface.

V5 — Fixed-measure signed algebra. Reconstruct set partitions with labeled
repeated exponents, multiplicities, falling factorials, all53 signatures/77
block tuples, and the dual-number derivative. Demonstrate every ordinary/marked
moment refers to the same fixed alpha/beta arrays. Check negative coefficients
select the correct interval endpoint and no signed contribution is discarded.

V6 — Root. Reconstruct the radial exponential including40h correction and its
interval recursion. Check the face-count40 outside the marked40-coordinate
moment and the cancellation of h^40 against (hZ)^40. Re-sum all77 contribution
numerators and compare the resulting upper bound to 11*I0/10^18.

V7 — Marginal arrays. Independently review the Taylor cap-cell bounds and signed
finite-difference recurrence or replace them with an equally strong checked
method. Rebuild all columns. Check the stored coefficients exclude h, the39
profiles and angular monomials; their lower endpoints define an approximation,
not a pointwise upper bound on the signed marginal.

V8 — Face and error. Justify prefixes2,3 only at this source cap, the radial W
upper envelope, both erased/retained witness terms FB*M39 + FA*D39, and the factor
40*h^2/Z_lower. Re-derive the inherited E<10^-78 in the physical measure. Distinguish
the selected-prefix error from a sum over prefixes. Check the Minkowski transfer
Q+E+2sqrt(QE), exact sqrt outward rounding, and the final10-target comparison.

V9 — Reproducibility and scope. Verify all20 source files, full artifact hashes,
seed and all marginal/kernel arrays. Run run_pipeline.py in normal and -O mode,
compare exact scientific results including77 contributions (not runtime fields).
Inspect tests:110 convolution/headroom cases,98264 production coefficients,
144 finite kernel-channel coefficients beyond32 counts,920 direct configurations,
48 ordinary/marked square comparisons,120 fiber identities and990 carry values.
Tests alone cannot replace V1–V8 proof review. Record any numerical failure as a
failure of the particular certificate until a true-integral contradiction exists.

## Required output

Return PASS, FAIL or INCONCLUSIVE with per-check verdicts, all exact hashes,
assumptions, earliest error/unresolved dependency, actual commands and outputs,
and cannot_imply. Repairs require a new solver candidate, not edits here.
A scoped PASS verifies only these two first-row claims under the stated imported
identities. It does not certify the remaining150 scalar inputs, run the original
Lean/FLINT proof, eliminate the finite-field axioms, establish a new prime-gap
bound, or prove twin primes. Assess novelty only in a bounded scope: an executable
certificate implementation is not automatically a new number-theory theorem.
