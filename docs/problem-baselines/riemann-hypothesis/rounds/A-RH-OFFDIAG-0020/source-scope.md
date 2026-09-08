# Source and recovery boundary

## Frozen repository input actually read

Immediate parent: PR #123 / A-RH-PROFILE-0019, commit
`0017c5895a91327adc18e0964a25f365cd60e4a3`, path
`docs/problem-baselines/riemann-hypothesis/rounds/A-RH-PROFILE-0019/proof.md`,
Git blob `65b686c2dd56958a88daf9d35b3fecc7835f1d5b`, SHA-256
`4d8bb96ff597c19fd0e4ca6bac70a3a38abab8eec589bf40bbabd567da9e0742`.

The complete proof was read in two ranges, along with fresh main, PR #123 and
review #124. The PR was open/unmerged and #124 had no comments on that read.
Governance/evidence policies remain at the already-read main commit
`39002c5a6af8c7b7f093589e6a76cfd218fcbb99`; its tree is
`d6ac23dc843e26ba123ae167228e3a0c1ff6b750`.
Earlier history is inherited through these pinned archives, not claimed fully
re-audited or re-executed. This run has solver context and is NOT independent.
The finite positive-test inequality and needed sampling mechanism are re-derived;
restatement does not promote a previous candidate or substitute for a receipt.

## Primary mathematical inputs

[L] Youness Lamzouri, *A new proof that more than 2/3 of the zeros of the
Riemann zeta function are simple and on the critical line*, arXiv:2609.02882v1,
2026-09-02. HTML reread 2026-09-08:
https://arxiv.org/html/2609.02882v1

The explicit external PC input is Lemma 3.1, attributed there to Baluyot,
Goldston, Suriajaya and Turnage-Butterbaugh. Its test is fixed, real, even,
L1, supported in [-1,1] and Lipschitz at zero. The two-fixed-test deweighting
and classical Montgomery–Taylor normalization are in Lemma 3.2 and its proof;
Theorem 1.1 already gives the benchmark used in this archive. This round does
not claim a better published result, a new variational optimizer, an audit of
PC, or an upstream Lean build. No actual source zero list was evaluated.

[R] Classical Riemann-von Mangoldt counting formula with O(log T) remainder,
as stated in the introduction of Jesús Guillera, *Some sums over the non-trivial
zeros of the Riemann zeta function*, arXiv:1307.5723v7 (2014), HTML reread:
https://arxiv.org/html/1307.5723v7

Only that classical counting statement, not the paper's other identities, is
used. Taking differences yields the uniform upper bound O(log(T+2)) for the
number of zeros in unit ordinate intervals below T. No assertion of a uniform
local asymptotic or zero simplicity is extracted from it. The critical strip
and conjugation symmetry are standard inputs also explicitly stated in [L].

Only HTML was analyzed. No PDF analysis, frozen raw web SHA-256 or source-wide
novelty search is claimed. Online sources can be revised; the versions above
are the exact declared theorem inputs. Repository artifacts are separately
frozen by their hashes and final commit.

## New scope versus previously accumulated work

Round19 supplied arbitrary finite PSD tests but only evaluated diagonal source
observables. This round evaluates a fixed-band, diagonally weighted Toeplitz
class by explicitly deriving a height-resolved pair moment. Its scalar
consistency proof uses a SINGLE admissible simple-height measure across all
tests. It does not assert that measure is the actual zero distribution, that
it extends to a full joint operator moment state, or that general nonseparable
PSD tests cannot do better. Fixed-band constants are not uniform in H(T).
