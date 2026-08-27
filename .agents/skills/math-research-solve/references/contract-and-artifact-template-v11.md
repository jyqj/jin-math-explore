# v11 contract and artifact minimums

## Project objective

Use `math-research-project-objective/v1` with exact keys: schema, project_id, statement, domain, quantifier_order, assumptions, evidence_standard, completion_standard, created_at_utc. The head and every task bind its SHA-256.

## Persistent task

Use `math-research-task-record/v1`: task_id, task_kind, objective hash, current-Goal authority role, persistent outputs, status, and timestamps. Do not create one for read-only queries.

## Project memory

Use `math-research-project-memory/v1`. Each entry has `memory_id`, `classification`, `statement`, `origin`, `trust_state`, `evidence`, `permits`, `does_not_imply`, and `reopen_condition`.

## External verifier claim

Every promoted claim has exactly `claim_id`, `classification`, `statement`, `scope`, `evidence`, `does_not_imply`, and `reopen_condition`. The completion binds the frozen reproduction hash and a distinct verifier identity. A PASS may promote only the listed claims.

## Route review

Use `math-research-route-review/v1`. Bind the covered internal-attempt count, all external intakes considered, ranked next routes, known dead ends, tool requirements, and `new_math_performed:false`.

## Completion

Milestones never set completion. Completion requires one immutable candidate covering the project objective, independent verifier PASS, terminal audit PASS, and a fresh active Goal at the guarded commit.
