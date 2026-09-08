# Sources, recovered input, and evidence boundary

## Frozen repository input actually read

- Parent: #114 / PR #116, still open and unmerged at this read.
- Commit: `92863a42864927d2a3a7a3c93aa87941d5c3150b`.
- Path: `docs/problem-baselines/riemann-hypothesis/rounds/A-RH-CONGEST-0018/proof.md`.
- Git blob: `c27af2a5abe5a87c0f35e417fce35d8f147e169c`.
- Reported proof SHA-256: `38125cbcd95257ac0e6a04b493cd786fe51801287af97c5cc3bdb87bd0760a22`.
- URL: https://github.com/jyqj/jin-math-explore/blob/92863a42864927d2a3a7a3c93aa87941d5c3150b/docs/problem-baselines/riemann-hypothesis/rounds/A-RH-CONGEST-0018/proof.md

The proof text was read through the connected GitHub API. Its entire artifact
package was not downloaded or hash-verified locally. Parent review queue #117
had no comments/receipt. The parent requested an isolated audit; this inherited
solver context cannot perform that role. The new finite input is re-derived,
not promoted through a fictional verifier receipt. No full parent checker rerun
or reliance on old cell-assignment/optimization results is needed for this round.

## External source [L]

Youness Lamzouri, arXiv:2609.02882v1, submitted September 2, 2026.
The abstract/version page and v1 HTML were reread September 8, 2026:

- https://arxiv.org/abs/2609.02882
- https://arxiv.org/html/2609.02882v1

Lemma 3.1 is the external fixed-test pair-correlation input PC. The finite
Hilbert-space setting is related to Proposition 2.1. The nonconstant cosine
extremizer and benchmark are attributed to Montgomery–Taylor, as identified in
Lemma 3.2 and Remark 3.4. This archive recovers that known constant; it does not
claim a new best zero proportion or a new extremizer. The polynomial-envelope
deweighting principle also has a predecessor in this source and round 16.

Only HTML and the abstract page were analyzed. No PDF analysis, raw-source hash,
upstream Lean build or independent audit of PC is claimed. The critical strip,
reflection symmetry and zero-count asymptotic enter the source bridge separately
from the finite linear algebra. All bandwidths and profiles are fixed before
taking height to infinity; the endpoint appears only as a later scalar limit.

## What is and is not a new candidate in this archive

The positive-matrix row inequality, reflection formulation, shifted-product
sampling bound and quantified scalar saturation range are the present candidate
extensions. Their proofs do not invoke a literature-wide novelty claim. The
variational calculation is an attributed reconstruction of a classical result.
The no-go concerns exactly proof.md (10),(15), not all possible profile methods,
all nonnegative matrices, higher moments or the Riemann hypothesis.

Main was read at `39002c5a6af8c7b7f093589e6a76cfd218fcbb99`; the new branch only
adds its own ten-file archive. Governance and predecessor files are unchanged.
Direct git failed DNS. Attempts to fetch a raw inventory script into the runtime
also failed; selected Python/library imports and executable paths were checked
directly instead. The full repository, its inventory/record runners and CI were
not executed locally. Observed remote CI must be reported separately from the
mathematical self-checks and cannot supply mathematical authority.
