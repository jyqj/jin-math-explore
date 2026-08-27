# Startup-cost audit

## Why this run was exceptional

The session combined work that should never repeat on an ordinary Resume:

1. A one-time semantic migration and verification of 569 imported legacy files.
2. A production controller defect repair, Skill Registry transaction, dual-target synchronization, and 14 regression tests.
3. Redesign of Approve-for-me boundaries: semantic authority, hash receipts, sandbox escalation, Goal control, and persistent instructions.
4. First construction and hardening of a campaign dispatcher, mutex, receipt, heartbeat, launch saga, and rollback behavior.
5. Several newly exposed recovery defects: duplicate Verify, `File.Replace` incompatibility, prelaunch extra files rejected by New launcher, and a registered `preparing` state that must not be mistaken for a fresh contract.

During the expensive setup interval the Goal control plane was paused, so no substantial mathematics could start. The later v1 launch then exposed execution-path defects below. These are incident costs, not the normal price of reopening a verified run.

## Repeatable waste found

The installed Skill says to run `Verify` and then `ResumePlan`, although ResumePlan calls Verify internally. On the current project, read-only measurement gave `Verify = 7.283 s` and `ResumePlan = 7.055 s`, for `14.338 s` total. One ResumePlan retains the same authoritative verification and removes a measured `7.283 s` duplicate pass.

The Skill body plus its four detailed required references total 57,277 characters (rough estimate 16.4k tokens). A same-run Resume needs the Skill core, startup reference, three state files, and the active contract/ticket—not the legacy and contract-generation protocols.

## Compatibility solution

Add a versioned router rather than edit any live-run-pinned script. It calls the existing controller once, performs a closed classification over exact returned fields, distinguishes absent/partial project slots, and recognizes only receipt-bound registered/preparing recovery. Campaign authorization moves to a normative protocol; the unsafe executable template was removed.

The execution path is also versioned. New runs use Prompt v7 plus an additive v2 startup/launcher/canary/cycle/project/stop bundle; every component is pinned in the signed manifest. The original v1 bytes stay unchanged for legacy Resume, and v2 rejects legacy manifests with `versioned_migration_required` instead of silently rewriting thread, contract, counters, or approval policy.

## Execution-path defects found after launch

16. The child launcher hard-coded `-a never` even when the campaign authorized Approve-for-me. Prompt v7 now binds `approval_mode`; v2 emits literal `--approve-for-me` under workspace-write, or explicit `-a never`, and probes the selected attested executable rather than a stale `codex` on `PATH`.
17. PowerShell 7.6 auto-parsed ISO timestamps as `DateTime`, dropping trailing fractional zeros on re-serialization and falsely rejecting valid HMAC payloads. Every v2 strict/cryptographic JSON read uses `-DateKind String`; signed writes normalize before hashing/embedding and immediately verify the primary file.
18. A manifest write could succeed syntactically but not be usable on its next read. `Write-SignedJsonPayload` now performs mandatory primary read-back after every write and fails before any following action if bytes, SHA, or HMAC do not round-trip.
19. A stated approval mode did not prove the mandatory shell/controller path worked. Before Goal bootstrap/research, v2 passes or reuses a signed canary that reads run-local signed state, invokes exact read-only cycle `Status`, and creates/reads/removes one scratch artifact without consuming an attempt or round.
20. Re-running a model canary on every Resume would recreate startup cost. The receipt is reusable only while CLI path/hash/version, v2 launcher/canary hashes, approval/sandbox/rules fingerprint, exact protocol, and Windows user/OS boundary are unchanged; otherwise it is rerun.
21. The first canary draft placed an executable probe in the agent-writable run directory. The corrected design executes a hash-pinned installed `invoke_math_research_canary_v2.ps1` and supplies only a run-local challenge whose exact SHA is pinned in argv and rechecked.
22. A canary using research xhigh reasoning and child agents would add needless cost. The operational canary uses the contract model with fixed low reasoning, no web, no child agents, and an ephemeral session while retaining the same attested binary, workspace-write, approval, rules and user/OS boundary.
23. Copying only the launcher left other JSON readers and controller paths exposed to the same DateKind defect or mixed-version imports. The candidate adds a complete v2 cycle module/CLI and project module/CLI plus stop/startup entries, pins the complete tuple, and rejects mixed or changed bundles.
24. Describing Approve-for-me only as a manifest/CLI value still left agents asking the user to copy commands or approve technical steps. The corrected authority rule requires direct submission of every necessary narrow in-envelope escalation to managed auto-review, forbids command/hash relay, and allows only a materially safer alternative or a stop after rejection. `never` remains distinct and can use only an exact hash-pinned rule.
25. Retained required references and the default agent prompt still described Prompt v6 as the New path, so a future startup could reintroduce the retired flow even after the launcher was fixed. The candidate replaces every required cycle/archive/legacy compatibility reference and `agents/openai.yaml`: v7/v2 is New, v3-v6 is signed v1 Resume-only, and the old runnable template paths are inspection-only tombstones.
26. A blanket paused-state “zero-write before observer” claim contradicted the mandatory first-action fail-open Observer hook. The corrected boundary forbids project/controller/dispatcher/research mutation while explicitly allowing content-free fail-open telemetry and read-only Goal/state checks.
27. The heartbeat said a missing Goal never launches, while the initial authorization flow creates and launches in one turn. The corrected distinction is temporal: only the initial explicitly authorized launch turn may create the Goal, freshly verify active state, and launch; a later heartbeat never recreates a missing Goal.
28. A hard-coded current Codex version/SHA in production regression would make a legitimate signed CLI upgrade look like a defect. The regression now checks official bin-root containment, OpenAI Authenticode identity, actual file/SHA/version self-consistency, and both approval capabilities on the same selected attestation; the exact current version/hash remains a freeze receipt, not a future allowlist.

## Expected steady state

- Same-attempt/signed Resume: one ResumePlan, three base state files plus active contract/ticket, no user round trip, then one fixed dispatch.
- Due audit: same preflight, then the required audit.
- New contract inside an unchanged authorized campaign: one preflight plus one package render/validate/register saga; the hash is recorded automatically.
- Fresh project: moderate one-time initialization and contract work.
- Legacy migration: potentially large but one-time; subsequent starts use the verified project state.
- Mandatory canary: one operational low-reasoning turn on first v2 New or after a binding change; ordinary Resume reuses the signed receipt.

Token totals remain workload- and platform-dependent. The enforceable target is structural: one authoritative preflight, no recursive history read, no duplicate registration, no unchanged contract regeneration, and no hash relay.

Target `SKILL.md` size review: **acceptable**, 17,377 bytes / 118 lines after the map-review maintenance edits. The main file still concentrates invocation routing, Goal/authority/budget boundaries, and common launch/Resume invariants; the complete independent map-review protocol and detailed archive, cycle, campaign, and templates remain selectively loaded references, so no decomposition is proposed in this maintenance candidate.

Harness decision: **implemented**. The risky paths are machine-observable and now fail closed through Prompt v7 authority parsing, exact argv generation, signed JSON read-back, complete bundle validation, mandatory canary verification, legacy-version rejection, and deterministic success/blocked-path tests. Residual limits remain managed-review decisions, mathematical correctness, and same-user compromise.

This release is maintenance/reliability hardening, not a controlled B0/B1 claim about proof success or total token reduction. Promotion still requires all old v1 regressions plus v2 startup/project/cycle differential fixtures, timestamp, authority, argv, bundle, canary, retained-reference, and default-prompt checks.
