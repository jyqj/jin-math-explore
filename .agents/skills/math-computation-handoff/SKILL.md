---
name: math-computation-handoff
description: Prepare and validate a hash-bound computation request and result bridge between a jin-math-explore attempt and $math-science-computation. Use whenever a Project claim depends on nontrivial CAS, exact, numerical, simulation, optimization, or search evidence.
---

# Math Computation Handoff

## Prepare

Freeze `jin-math-computation-handoff/v1` identity and intent fields before execution:

- Project/window/attempt/claim IDs;
- objective SHA-256;
- exact computational question;
- domain and assumptions;
- requested evidence grade;
- exact input and acceptance checks.

Then invoke `$math-science-computation`. That Skill owns feasibility, backend selection, execution, proportional verification and `computation-record.json`.

## Finalize

After execution, fill backend/version, reproduction command, code/result artifact pointers and hashes, computation-record pointer/hash, actual evidence grade, and nonempty `cannot_imply`.

Run:

```bash
python scripts/validate_computation_handoff.py <handoff.json> --root <PROJECT_ROOT>
```

PASS proves only byte/path closure and required fields. It does not prove model fidelity, mathematical semantics, coverage, or the claim; send the frozen bundle to `$math-independent-verifier`.
