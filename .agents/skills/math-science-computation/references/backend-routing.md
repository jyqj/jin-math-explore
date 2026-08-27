# Backend routing

Use this file only for a nontrivial computation that still needs a backend. First identify the closest task class, then read that route and combine it with the current backend inventory. Do not inspect every installed system before each calculation.

## How to use the catalog

Keep task fit and availability separate:

1. Find the matching task class and its preferred implementation strategy.
2. Check whether the required backend is callable on the current machine and in the current session.
3. Use the fallback when the primary route is unavailable or its stated conditions do not hold.
4. If no row matches, apply the general principles below and record the missing category for later evaluation.

`heuristic` means the route reflects current engineering judgment and practice, not a controlled benchmark. `benchmarked` is allowed only when `evidence_ids` cites an entry in [backend-routing-evidence.md](backend-routing-evidence.md).

## Routing catalog

| route_id | task_class | conditions | primary | fallback | decision_metrics | evidence_status | evidence_ids |
| --- | --- | --- | --- | --- | --- | --- | --- |
| general-cas | General symbolic, numerical, optimization, differential-equation, and scientific computation | A documented direct CAS implementation exists and its semantics fit the requested domain and precision | Mathematica | Compare SageMath, then use Python when neither callable CAS route is suitable | correctness, exactness, wall time, memory, stability | heuristic | none |
| exact-algebra | Finite fields, polynomial rings, ideals, modules, Gröbner bases, elimination, algebraic structures, and group computation | Object model, coefficient domain, and specialist implementation materially affect correctness or efficiency | Compare SageMath and Mathematica; choose the better documented callable implementation | Use the other callable CAS, then Python only with a suitable verified library | correctness, domain fidelity, wall time, memory, stability | heuristic | none |
| python-deliverable | Computations whose required artifact or surrounding system is Python-native | The user requires Python code, library integration, or neither CAS offers a suitable callable implementation | Python with explicitly verified interpreter and modules | Use a callable CAS and export an interoperable result when the deliverable permits | correctness, integration cost, wall time, memory, reproducibility | heuristic | none |
| exact-prime-counting | Exact `PrimePi`, inclusive prime-count intervals, or large nth-prime calculations | Exact integer output is required and the specialist operation is directly supported | Follow the SKILL.md Exact Prime-Counting Route | Stop or use another exact authorized implementation; never substitute an asymptotic estimate for an exact request | exactness, wall time, memory, recoverability | heuristic | none |

## General selection principles

- Prefer a documented direct implementation over rebuilding the algorithm.
- Verify function semantics, mathematical domain, exactness, branch conventions, and required modules only for the selected route.
- Do not infer callability from model memory, an installation directory, or an old inventory record.
- If the preferred implementation is unavailable, state the limitation and why the fallback is adequate.
- Prefer exact arithmetic for exact tasks. Use numerical methods only at a precision and with an error check suitable for the requested claim.

## Verification guide

- Exact symbolic output: substitution, normalization, a checkable certificate, or an independently derived identity.
- Numerical equations: residuals, backward error, precision escalation, or certified bounds.
- Simulations: invariants, dimensional consistency, convergence checks, and fixed seeds when applicable.
- Discrete algorithms: boundary cases and independently checked small cases.

Use a second implementation only when it materially strengthens the requested evidence. Two calls to the same underlying algorithm are not independent.

## Maintaining the catalog

Do not promote anecdotes, one-off timings, or model preference into a `benchmarked` rule. Run controlled comparisons through the Skill evaluation workflow, keep raw artifacts in the evaluation archive, and add only the promoted conclusion and its limitations to [backend-routing-evidence.md](backend-routing-evidence.md). Update the matching catalog row only after that evidence entry exists.

Do not install software, start a network service, use a cloud kernel, or transmit local inputs without explicit authorization.
