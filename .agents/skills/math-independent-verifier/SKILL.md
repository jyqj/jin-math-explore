---
name: math-independent-verifier
description: Independently verify an exact frozen mathematical claim, proof candidate, dependencies, and computation evidence in jin-math-explore. Use for Project attempt verification, shared-result admission, map semantic review support, and terminal audits; never edit the candidate or perform hidden repair.
---

# Math Independent Verifier

## Input boundary

Require an exact ticket containing:

- Project/objective/window/attempt/claim IDs;
- candidate path and SHA-256;
- dependency paths and SHA-256 values;
- definitions and allowed source packet;
- evidence standard and checked scope;
- computation handoffs, if any.

Reject mutable, unhashed, truncated, ambiguous, or post-ticket-modified candidates.

## Review

1. Reconstruct the statement, domain, assumptions and quantifier order.
2. Check every dependency is applicable under the exact hypotheses.
3. Locate the earliest unsupported inference, circular dependency, missing case, hidden regularity assumption, or unjustified limit/interchange.
4. For computation evidence, verify input/model fidelity, exact-versus-numerical scope, reproducibility record, hashes, and coverage bridge.
5. Check that `cannot_imply` includes every material non-implication exposed by the evidence.
6. Return exactly `PASS`, `FAIL`, or `INCONCLUSIVE` with checked scope, earliest error for FAIL, unresolved items, and context-isolation statement.

Save the exact receipt as `jin-math-verification.json` and run:

```bash
python scripts/validate_verification.py <receipt.json> --root <PROJECT_ROOT>
```

The mechanical validator recomputes candidate/dependency hashes but does not judge proof semantics.

## Isolation

Do not read solver chat or sibling staging unless the ticket explicitly binds specific bytes. Do not modify or repair the candidate. A repair creates new bytes and requires a new verification ticket.
