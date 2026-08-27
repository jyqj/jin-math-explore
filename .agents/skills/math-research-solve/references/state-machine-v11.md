# Math Research v11 state machine

v11 makes the project, not a product Goal invocation, the durable mathematical unit.

## Identity layers

- `project_objective` is immutable. It freezes the problem, domain, quantifier order, assumptions, evidence standard, and terminal completion condition. A semantic change creates a new project or an explicitly authorized fork.
- The current product Goal is sole mutation authority for the current task. Its text must hash-bind the existing objective; it never replaces it.
- A persistent `task` records only a request that creates durable project changes. Kinds are `research`, `external_intake`, `verification`, `strategy_review`, `project_maintenance`, and `export`. Read-only questions create no task record.
- Runs live only at `runs/<run_id>/` under the same project. A new budget or invocation starts a Run, not a successor project.
- Internal attempts belong only to a research task and active Run.

## Attempt and review cadence

`ATTEMPT_START` and `ATTEMPT_END` count internal research. Intake, verification, maintenance, export, checkpoints, and route review never increment attempts. After three completed internal attempts, set `route_review_due=true`; `ATTEMPT_START` then fails closed. `ROUTE_REVIEW_COMPLETE` must summarize existing evidence only, sets the count since review to zero, and creates no mathematics.

Periodic route review is not a terminal audit. A terminal audit is allowed only for a candidate that covers the immutable objective and is the only transition that may set `project_complete=true`.

## Publication

Prepare is read-only against the project and emits an immutable plan. Commit requires a fresh active Goal, exact plan hash, expected head hash, and all verifier bindings. Write immutable artifacts first and replace `project.json` last. On any failure after activation, restore the prior head and remove only transaction-created paths. v3-v10 heads remain byte-compatible and are delegated to their versioned startup unless an explicit migration is prepared.
