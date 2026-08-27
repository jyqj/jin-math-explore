# Proof-search continuity and semantic reset

## Contents

- Purpose
- Continuous campaign model
- Continuity capsule
- Persistent lead and specialist handoff
- Research checkpoints
- Promotion and verification
- Semantic route fingerprint
- Reset triggers and portfolio rules
- Strategy audit
- Failure and stopping rules

## Purpose

Use this protocol to preserve mathematical continuity without weakening evidence gates. The principal failure it prevents is replacing one sustained proof search with many isolated tickets whose workers see only summaries. The second failure is a surface route reset: changing vocabulary, coordinates, software, or a local lemma while keeping the same underlying proof object and quantifier mechanism.

## Continuous campaign model

Define one attempt inside one window by a frozen bottleneck campaign:

- canonical target hash;
- semantic mechanism family;
- proof object;
- quantifier strategy;
- evidence standard;
- resource and permission envelope;
- lead solver identity.
- window ID, source map/head, and route decision.

Auxiliary lemmas, bridge derivations, in-family synthesis, counterexample searches, and route-internal repairs stay in that attempt while these fields remain fixed. Do not end an attempt merely because a new local lemma is needed.

End the attempt when at least one frozen field changes materially. A new ticket alone does not prove that a new attempt is warranted. A renamed route alone does not prove a semantic change. `semantic_reset` records the boundary and closes the attempt; it never auto-starts a successor or replaces another member of the current window portfolio.

The lead may work through several conversation turns and checkpoints. Preserve the existing attempt and prefer `followup_task` to the same lead when the collaboration session remains available. A new agent is not a substitute for restoring the lead's complete context.

## Continuity capsule

The current `math-research-continuity-capsule/v1` is the authoritative compact entry point. It contains:

- project/run/generation and target hash;
- proof spine claims;
- open bottlenecks;
- live, rejected, quarantined, and forbidden route families;
- synthesis candidates;
- pointers to complete required artifacts;
- the current route-reset directive.

Claim status is exactly:

- `verified`: bound to independently verified evidence;
- `working`: a live derivation not yet promoted;
- `conditional`: correct only under an explicit unresolved premise;
- `refuted`: bound to verified counterevidence or a verified failure boundary.

`working` and `conditional` claims never support completion, verified partial publication, or the premise of a later verified claim. A checkpoint cannot relabel them as `verified` or `refuted` unless the artifact is already present in state as PASS-verifier-bound evidence. Once a claim is `verified` or `refuted`, later checkpoints must retain its complete claim record byte-for-byte; deletion, downgrade, artifact removal, statement rewrite, or dependency rewrite is a regression.

Every item in `required_full_artifacts` is a `{path,sha256}` pointer. The next solver ticket must include each pointer in `input_artifacts` and `allowed_reads`. A summary, index row, capsule statement, or verified-result JSON cannot replace a named complete proof artifact.

Read the capsule first at startup. Load only the complete artifacts it names. This keeps startup bounded without discarding the mathematical spine.

## Persistent lead and specialist handoff

Each attempt has one `lead_id`. Lead, verifier, and specialist are logical `research_role` values, not a fixed physical-agent roster. A ticket records `persistent_lead.mode` as:

- `new`: the attempt starts a fresh lead session;
- `resume`: continue the named lead and bind `previous_ticket_id`.

Resume the same lead whenever the frozen campaign is unchanged. A specialist is appropriate only for a bounded, independent subproblem that can proceed in parallel. Give the specialist a minimal ticket and require a complete artifact plus access log. The specialist does not own route choice, attempt disposition, evidence promotion, or Goal control.

The Host validates and binds the specialist artifact, updates the capsule, then returns it to the lead. Do not form a daisy chain in which each specialist sees only the prior specialist's summary. If no subagent is available, the lead executes the same bounded specialist ticket serially; absence of a subagent is not an error and does not change the ticket's scope.

## Research checkpoints

Publish `RESEARCH_CHECKPOINT` when any of the following occurs:

- a material local result or counterexample is obtained;
- the lead or a specialist hands off work;
- context compaction is expected;
- the route is revised without changing its semantic family;
- approximately 30 minutes of active work has elapsed.

A checkpoint binds:

- the new capsule;
- typed artifact references;
- one reason code;
- an immutable timestamp.

It must preserve project, run, target, active attempt, ticket, lead, scope fingerprint, permission envelope, and resource envelope. It increments `checkpoint_count` only. It does not consume an attempt or round and does not require a verifier when it records only working material.

If the checkpoint discovers that the proof object, quantifier strategy, mechanism family, evidence standard, or envelope must change, record the reason and use the semantic-reset or new-authority path. Do not mutate scope inside a checkpoint, and do not close and reopen an identical `attempt_scope` merely to create a fresh local ticket.

## Promotion and verification

Use an independent verifier role only when promoting:

- a full candidate;
- a verified partial result;
- a mathematical failure boundary.

The verifier receives the exact immutable candidate and complete dependencies, checks the frozen quantifiers, and returns one `verification_result`: `PASS`, `FAIL`, or `INCONCLUSIVE`. Prefer an actor who did not generate the candidate. If no subagent exists, the lead executes a fresh context-isolated verifier ticket serially and records `single_agent_fallback`; never claim distinct physical-agent independence. A repaired candidate needs a new immutable hash and a new verification. If the frozen project evidence standard requires a distinct identity, remain awaiting verification instead of weakening it.

A negative attempt with no proposed mathematical promotion may close directly from the active or solver-completed state. Record the failed step, excluded scope, non-entailment boundary, artifact hashes, retry fingerprint, and falsifiable reopen condition. Do not spend a verifier round only to confirm that the solver found nothing. Every attempt ends with an `attempt_reconciliation_package`; promotion and map mutation wait for window reconciliation.

## Semantic route fingerprint

Every `math-research-route-card/v10` declares:

- core proof object;
- proof direction: `primal_extremizer`, `dual_separation`, `explicit_construction`, `induction`, `counterexample`, `computation`, or `other`;
- quantifier strategy;
- mechanism-family ID and route ancestry;
- coverage bridge;
- relationship to forbidden families;
- a concrete non-renaming reason;
- whether it treats only a special family.

Names, coordinates, notational changes, a different CAS, a different paper, or a new local lemma are not by themselves semantic changes. The route card must say what mathematical object and quantifier mechanism changed.

An active or accepted special-family route needs a nonempty bridge statement and a falsifiable bridge test. `working` is allowed while the test is being pursued; `none` cannot remain primary.

## Reset triggers and window portfolio rules

Run `route-reset-assess` after every update that can change a trigger input, including a user instruction, checkpoint, attempt result, or strategy audit. Freeze a matching directive in the capsule. A semantic reset is required when the objective-preserving attempt must change its proof object, mechanism family, quantifier strategy, evidence standard, selected route, or causal interpretation. Repeated lack of progress may force attempt closure, but it does not by itself prove a route false.

An explicit user ban is semantic. Expand it only to the underlying mechanism actually stated by the user, while preserving independently verified facts that do not depend on continued use of that mechanism.

Reset ends the current attempt, records the changed fields, surviving artifacts, precise non-implication boundary, and reopen condition in its reconciliation package, and leaves the current window portfolio unchanged. It never accepts a successor route, capsule, ticket, or attempt as the next control step. After all window members become ready, window reconciliation updates route status and the research map. A later window independently generates route proposals and freezes one new three-member portfolio from the then-current map.

Every window portfolio must contain exactly three semantically differentiated work items. The Host deduplicates proposals by `(core_proof_object, mechanism_family, quantifier_strategy)`. If ordinary proposals do not cover three regions, route discovery supplies a work item aimed at an unrepresented method region; it must not rename an existing route. Machine checks operate on declared fields and cannot prove that sophisticated mechanisms are equivalent, so the Host records dedup evidence and any residual semantic uncertainty.

The attempt control identity is `(window_id, attempt_id, ticket_id, lead_id, route_id)`. A continuation preserves the tuple. A future-window attempt always receives a fresh tuple and a fresh decision derived from that future window's source map; no partial carry-over creates current authority.

## Strategy audit

The strategy auditor reads:

- current capsule;
- active route card;
- every complete artifact named by the capsule;
- failure and route records relevant to the bottleneck.

It returns `math-research-strategy-action/v1` with one action:

- `continue`: same campaign has credible progress;
- `synthesize`: existing verified/working artifacts should be combined by a later solver;
- `semantic_reset`: reset trigger is satisfied;
- `quarantine`: an artifact or route is unsafe to reuse;
- `await_input`: progress requires user authority or missing external material.

The report includes bottleneck progress, surface-reset risk, missing complete artifacts, a synthesis map, route-status observations, and required inputs. `new_math_performed` must be `false`. It may recommend that the current attempt close, but it must not select a successor or construct the next window portfolio. If the auditor discovers a mathematical idea, quarantine it as a lead; a later window proposal must reconstruct and verify it.

## Failure and stopping rules

Do not continue the same family after a required reset. Do not reset early merely because a local lemma is difficult. Do not promote a special-family computation as a global result without a verified coverage bridge.

Stop and preserve state when:

- the Goal is not active;
- the frozen budget is exhausted;
- a required complete artifact is missing or hash-mismatched;
- the active window portfolio or its source binding fails preflight;
- a worker reports an unbound read or staging escape;
- a verifier or terminal audit is non-PASS;
- completion would rely on a working or conditional claim.
