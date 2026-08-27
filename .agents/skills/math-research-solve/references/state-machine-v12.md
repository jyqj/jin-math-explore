# State machine v12

The immutable objective is a hash-bound object containing the statement, domain, quantifier order, assumptions, evidence standard, and completion standard. Every task, Run, route, intake, and export binds that hash. A mismatch fails closed; semantic change requires genesis or an explicit fork.

Persistent task kinds are `research`, `external_intake`, `verification`, `strategy_review`, `project_maintenance`, and `export`. Pure queries create no task. A product Goal is only mutation authority for the current task; it is never the mathematical objective.

Internal attempts occur only inside a research task and same-root Run. Intake, verification, review, maintenance, and export do not consume attempts. After three completed internal attempts, set `route_review_due=true` and reject a fourth start. `ROUTE_REVIEW_COMPLETE` is non-counting, loads all unified memory, creates no mathematics, resets the cycle counter, and ranks the next routes.

Set `project_complete=true` only when one immutable candidate covers all objective quantifiers, an independent verifier passes it, a terminal quantifier/strategy/tool audit passes, and a fresh active Goal authorizes publication. A milestone or finite negative is nonterminal.

Authoritative writes are prepare/validate/commit operations. Write immutable objects first, update the manifest and generated views, then replace the compact head last with expected-head and expected-plan checks.
