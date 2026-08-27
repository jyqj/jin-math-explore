# Unified memory and intake v12

Load the complete current memory index before every route choice. Each item records origin/trust, exact statement and scope, what it permits, what it does not imply, evidence pointers, reopen condition, and tool requirements.

Mutually exclusive classes are:

- `verified_fact`
- `verified_refutation`
- `verified_impossibility_boundary`
- `bounded_negative`
- `unresolved_obstacle`
- `reproduction_blocked`
- `conditional_result`
- `open_bridge`
- `known_pitfall`

Only an independently verified counterexample may become `verified_refutation`. Only an independently verified proof that a mechanism cannot succeed in an exact scope may become `verified_impossibility_boundary`. Both require promoted trust, PASS evidence, and a nonempty exclusion scope.

`bounded_negative` excludes only its frozen finite domain. Timeout, an unfinished scan, missing lemma, weak estimate, expense, unavailable dependency, or failure to find a proof is never a mathematical failure. Record it as `unresolved_obstacle` or `reproduction_blocked`; these may affect route order and tool requirements but carry no exclusion authority.

External material follows `registered_unverified -> reproduced -> independently_verified -> promoted`. Promote claims individually. An external route history is not an internal attempt. Preserve rejected, blocked, and unverified claims with explicit limitations.
