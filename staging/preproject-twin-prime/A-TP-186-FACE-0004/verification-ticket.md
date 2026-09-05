# Independent review request: fourth-round face candidate

Parent solver Issue #53. A new execution context/run with role independent_verifier is required.
Do not inherit the solver conversation or repair candidate files while verifying them.
This file is a queued task specification, not an executed independent review.

## Candidate statement

For the pinned Challenge.lean definition and Iref=23685317816/10^24,

    physicalSourceOuterFace 0 0 / Iref <= 2.52164329e-18 < 10e-18.

This is an upper envelope, not an integral equality or lower bound.
The original physical_integral_bounds axiom and Iref<=trialIH are NOT permitted premises.
The complete result is an unreviewed solver candidate using the explicit Poisson/Dickman/Mecke imports.

## Frozen core-file hashes

- `README.md`: `eb0aef0b025a4493f4dec59161b6d69e267e90679ff72d0d3f864e9123e6e5ce`
- `marginal-proof.md`: `e20147c00a871485e52c88ec5e4935bf1dc6155256d5e9c7c47a929d0b730628`
- `inputs.json`: `2d22687c4842fa19b742a5dc4991cdbfdecbc12392d7eb0be938f6db222a5fbd`
- `exact_backend.py`: `88d13057bfdf0ce3f123d428ec949d052dbc35f76fa34965ac99531632ed4a59`
- `marginals.py`: `fff9738a3d752e6d73d5507a12fdc7a3bbee5c3de2bdd3953c630e5d96d72e26`
- `compute_face.py`: `4c83991e9f2832d5d3df091f13bc5857cac38e02fe11a3659cfd3766dd13d4c9`
- `check_face.py`: `c3443cf03b023242640da1ae1a0e3a6fcd3ec16603bae0b29c196739e0b092fe`
- `results.json`: `a8fa366b59b1f776e87c1468d8bce6ea8d3c6bb6fbdae43289d86d950834b648`
- `source-lock.json`: `dcd19d971ac5638ac8851c312922eeb566e4b14303b64f4545d7e6d6a8897131`
- `computation-record.json`: `814137e1a2d9ea1e37ff6d03d14869c930f9dcf54a220ce432a3feea4f0dcc2a`

## Verification scope

V1. Reconstruct all77 coefficients,11 signatures, shell/cap boundaries, grid endpoints and profile normalization against openai/PrimeGaps186@61340d0b74163003b32756bb16e91d9209a5e330. Do not use a later upstream version. Distinguish the14-file local attempt03 from the9-file remote cec587a86e attempt03; #52 is a separate root review.

V2. Prove the erasure identity (1)-(2), including labeled repeated-signature multiplicities, full midpoint offset20, physical h and dependence on the retained fragment cap. Prove that only prefixes2/3 are needed on this source support and that their squared sum is a valid pointwise upper bound.

V3. Prove the exact sliding finite-difference recurrence, including the deleted boundary P(U+1), the new boundary P(L), clipped windows, degree truncation and ascending in-place update. Audit the common integer denominator. Error radii must be bounded from the same fixed weight enclosures, not reset independently at each update.

V4. Re-derive the Dickman primitive on [0,17/8], both joins, log telescoping and80-term second-delay series with a rigorous remainder. Verify all three cap ranges, mass/h convention, positivity clamps, downward/upward directions and224->160-bit conversion. Separate work precision from actual interval widths.

V5. Re-derive the positive source renewal majorant and both rolling windows. Verify denominator j-1, exponent lag k-1, small-cell initialization and m<=1. Audit the frozen upper mark density and the two1/2 carry weights in D. Confirm a common positive measure is fixed before signed-square expansion.

V6. Re-derive formula(6) and independently check both mark locations. In particular check the outer factor40, inner39 and falling(38)_b, h^2 from two physical marginals, q0^40, Z^40, the distinction between the source erased coordinate and marginal integration variable, and the absence of an extra rho_star factor. Check radial W(r), the40-versus20 mesh corrections and all720 retained total-radius cells.

V7. Audit exact C/GMP Kronecker multiplication, coefficient-slot bound, linear truncation, little-endian encoding, unsigned input checks and memory bounds. Inspect every outward rounding and complete-square nonnegative clamp. Do not silently replace exact arithmetic with ordinary FFT values.

V8. Reproduce finite tests in normal and -O mode. Regenerate genuine marginal files from inputs and run the complete source/face computation using a new output path. Compare input/array/density hashes and mathematical fields; timing fields and hashes including timing may differ. The --check-result command only verifies saved final rational factors, not the integral.

    python3 -B check_face.py --self-test
    python3 -O -B check_face.py --self-test
    python3 -B marginals.py --output-dir fresh-generated
    python3 -B compute_face.py --generated fresh-generated --output fresh-face.json
    python3 -B check_face.py --check-result fresh-face.json

The solver observed55.352s for marginals,526.933s for the full contraction and3276636KiB peakRSS with CPython3.13.5/GMP6.3.0/gcc14.2.0. These are observations, not runtime guarantees. Large arrays are local-delivery-only; their exact hashes are in computation-record.json and regeneration is part of review.

V9. Return separate results for the physical measure identity, marginal arrays, recurrence majorant, signed contraction and final scalar. Recompute final rounding to252164329/10^8 in units1e-18. Assess novelty narrowly; finite differences, Dickman delay equations and Kronecker encoding are not claimed new mathematical theories.

## Required output

PASS, FAIL or INCONCLUSIVE with fresh reviewer identity/isolation, frozen commit and hashes,
per-check findings, earliest error/unresolved input, actual commands and cannot_imply.
Any repair belongs to a new solver candidate and new review cycle.

A PASS covers at most the single G0:R00 face scalar and checked supporting statements.
It does not verify the other151 numerical targets, the separate root candidate, an original Lean build,
the complete186 proof, a smaller prime-gap bound, Project authority, or the twin-prime conjecture.
