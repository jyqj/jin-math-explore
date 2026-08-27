---
name: math-science-computation
description: Plan, implement, execute, verify, and deliver mathematical or scientific computations with local Mathematica, SageMath, Python, or specialist exact tools. Use when Codex needs symbolic or numerical calculation, especially very large exact-integer evaluation, computer algebra, simulation, optimization, computational experiments, reproducible scientific code, a computation requested by another mathematics or science Skill, or external-tool, CAS, or MCP verification explicitly requested by the user. Estimate feasibility first; when an allowed callable backend has reasonable resources, actual computation and result delivery are mandatory. For exact prime-counting, try Wolfram MCP first and fall back to a verified local primecount executable when MCP evaluation is unavailable, fails, or remains unevaluated.
---

## Skill Run Observation

<!-- codex-skill-observer:v2 -->
- As the first execution action after selecting this Skill, run `& $env:CODEX_SKILL_OBSERVER_CLI begin --skill math-science-computation --quiet --fail-open; & $env:CODEX_SKILL_OBSERVER_CLI phase set --skill math-science-computation --phase workflow.startup --quiet --fail-open` when `CODEX_SKILL_OBSERVER_CLI` is available.
- At each actual workflow transition, append the matching fail-open `phase set --skill math-science-computation` call to the same PowerShell tool invocation that starts the next business action. Use only `retrieve`, `verify_live`, `plan_change`, `mutate`, `validate`, `version_control`, and `final_response`; do not add a model-tool round trip only to mark a phase.
- When invoking a bundled production script from this Skill, use the matching `scripts/observer_run.py`, `observer_run.ps1`, or `observer_run.mjs` wrapper when that wrapper exists, and record the matching production-entry phase from `references/observer-phases.json`; use `math-science-computation.script.run` only when the target entry is not listed. Wrappers must preserve the child process output and exit code.
- In the final business-tool invocation, set `final_response`; then, before the final response, run `& $env:CODEX_SKILL_OBSERVER_CLI end --skill math-science-computation --status success --quiet --fail-open`. Use `failed` or `cancelled` instead of `success` when that outcome is known.
- Observation is fail-open and silent: never ask the user to repair it, never expose routine telemetry in the response, and never let an observer failure block the Skill.
- Do not pass prompts, file contents, tool inputs, tool outputs, secrets, or personal data to the observer. Codex Stop and SessionEnd hooks close runs left open by interruption.
- Phase definitions and allowed fields live in [references/observer-data-dictionary.md](references/observer-data-dictionary.md); load it only when instrumenting or analyzing this Skill.

# Math & Science Computation

## Role

Own the computation portion of a mathematics or science task. Select an appropriate callable local backend, produce reproducible code or exact input, verify the output at the strength the evidence supports, and deliver the requested files.

Do not replace mathematical reasoning with a computer-algebra response. A successful CAS evaluation is not automatically a proof.

## Execution Profiles

Choose the least expensive profile that still supports the user's requested claim:

- `chat` is the default when the user asks only for an answer and does not request files, reproducibility, certificates, or unusually strong independent verification. Use one primary computation and the cheapest sufficient check.
- `reproducible` applies when the user requests code, data, saved files, rerunnable results, or a handoff. Produce the requested artifacts and a validated computation record.
- `high-assurance` applies when the user explicitly requests strong independent verification, certificates, audit material, or when the claim's risk requires it. Use additional implementations or full-range reruns only when they materially strengthen the evidence.

Do not ask which profile to use when the request makes the default clear. A faster profile never licenses a stronger claim than the evidence supports.

## Backend Readiness Gate

Apply this gate after the computation object and mathematical structure are clear but before committing to a backend-dependent implementation. The gate must be fast enough that capability discovery does not dominate an ordinary computation request.

1. Run `python scripts/backend_inventory.py --mode ReadOrCreate` for nontrivial work that still needs a computational backend. This is the platform-neutral Windows, macOS, and Linux entry. If Python is unavailable but PowerShell 7 is callable, use `scripts/backend_inventory.ps1 -Mode ReadOrCreate` as the compatibility entry. Use the current host's callable launcher; do not require or install PowerShell merely for inventory. Both entries read the same persistent capability snapshot and create it with one local scan when missing, invalid, expired, recorded for another host, or contradicted by a recorded path.
2. On a cache hit, do not start Mathematica, SageMath, Python, primecount, or any MCP tool. The script checks only recorded executable paths, performs no state-file write, and should normally complete its internal work within 250 ms. Treat a cache-hit inventory operation above two seconds as a performance fault to diagnose, not normal preflight cost.
3. Treat the persistent snapshot as authoritative only for the recorded local facts at its stated time. Build a current-session MCP overlay from the tools advertised to the agent. A historical MCP result never proves current callability; live-check only the selected MCP backend when the route requires it.
4. Use the snapshot and current-session overlay to choose one primary route and a concrete fallback before writing backend-specific code. Do not probe every installed backend or MCP server merely to populate the table.
5. Immediately before a material run, live-check the selected local executable or MCP evaluator. If its path is missing, its version materially changed, or execution fails, invalidate that local record through the same inventory entry (`backend_inventory.py --mode Invalidate --backend <name> --reason-code <code>`, or the PowerShell-equivalent parameters), or mark the MCP session overlay `degraded` or `unavailable`; then re-plan from the corrected state.
6. Read [backend-inventory.md](references/backend-inventory.md) for the state-file contract, authority boundary, refresh rules, and schema link. The snapshot is mutable runtime state outside the Skill package; do not edit or version it as a Skill reference.

## Mandatory Feasibility and Completion Gate

Apply this gate to every computation problem, especially unusually large exact-integer calculations, to determine what “enough to answer” means for the user's requested deliverable. It complements the execution profiles and ordinary early-stop rule: when the user explicitly asks for a concrete computed value, that value is part of the minimum sufficient answer; when the user asks only for a method, proof, estimate, or bound, do not calculate an unrelated exact value.

1. Estimate feasibility first. Consider input magnitude, algorithm and implementation, time complexity, expected wall time, memory, disk, precision, intermediate-expression growth, output size, and the current task's available resources. A guess that a number merely “looks too large” is not a feasibility estimate.
2. Apply the Backend Readiness Gate before committing to a backend-dependent plan. Use the Mandatory Wolfram MCP Gate to discover and, when callable, query the Mathematica MCP tools for relevant function support and actual evaluation. Distinguish a cached local fact, a currently advertised MCP tool, a successfully live-checked backend, and an estimate that the current computation will fit available resources.
3. If the requested deliverable includes a concrete value and the estimate shows that local Wolfram Mathematica, its callable MCP evaluator, or another allowed exact backend can reasonably complete the task with the available resources, execute the computation. The model has no discretion to omit it, return only code, say that it is computable, substitute an unevaluated expression, or provide an approximation when an exact result was requested and feasible.
4. Return the actual computed result in the conversation or the requested deliverable. Include the full exact integer or decimal expansion when its own output size is reasonable; if result size makes inline delivery unreasonable, save or provide it through an authorized result artifact and state exactly where the complete value is available. This required primary calculation does not authorize unrequested cross-validation, alternative full-range reruns, extra backends, or optional artifacts.
5. If expected runtime is long, warn the user with the estimate and continue the authorized computation. Do not cancel, time-limit, downgrade, or abandon it solely because it is slow. The user retains the right to terminate it. A platform failure, exhausted hard resource limit, or explicit user cancellation may stop execution; report that event and any recoverable progress honestly.
6. If the estimate shows that the task is not feasible with available resources, report the concrete limiting resource and estimate. Do not present model judgment, an unevaluated expression, or an approximation as the requested computed result.

## Workflow

1. State the mathematical object, domain, assumptions, exact-versus-numerical intent, precision requirements, requested deliverables, and selected execution profile. Ask only when an unresolved choice would materially change the computation.
2. Before building the computational pipeline, run one bounded mathematical-structure precheck. Look for a direct proof, factorization, symmetry, recurrence, monotonicity, closed form, or specialist reduction that could remove most or all computation. A complete structural solution may remove unnecessary pipeline work, but it does not replace actual evaluation and result delivery when the user requested a feasible computed value.
3. For nontrivial work that still needs computation, apply the Backend Readiness Gate and the Mandatory Feasibility and Completion Gate. Distinguish:
   - whether Mathematica or SageMath has a suitable documented implementation;
   - whether the persistent snapshot records a compatible local implementation;
   - whether the selected local or MCP implementation passes a current live check.
4. For a nontrivial task, classify the computation using [backend-routing.md](references/backend-routing.md), then read only the matching route. Combine that rule with the backend inventory and current live-check; a good task fit does not prove local callability. If no route matches, use the general selection principles, record the uncovered task class, and do not invent a benchmark-backed preference.
5. Apply the mandatory Wolfram MCP gate below when Wolfram is the selected primary backend, the user explicitly requests Wolfram/MCP/external CAS execution, or before selecting a Mathematica command-line fallback. When the user explicitly requests external-tool, CAS, or MCP verification, actual external execution is required; reasoning alone does not satisfy the request.
6. Use `scripts/backend_inventory.py` as the normal cross-platform local readiness entry. Use `scripts/backend_inventory.ps1` only when Python is unavailable and PowerShell 7 is callable. Run the matching `probe_backends.py` or `probe_backends.ps1` directly only for explicit diagnostics or when bypassing the cache is justified. None of these scripts can certify MCP callability.
7. Select one primary implementation and one concrete fallback that match the task and the readiness evidence:
   - normally consider Mathematica first for general symbolic, numerical, optimization, differential-equation, and scientific computation;
   - compare SageMath with Mathematica for algebraic structures, finite fields, ideals, Gröbner bases, elimination, and related exact algebra;
   - write Python only when neither system has a suitable implementation, the suitable system is unavailable, or an explicit engineering constraint makes Python the better deliverable. Record the reason.
8. Execute with explicit assumptions, domains, coefficient fields, precision, seeds, tolerances, and resource limits as applicable. Run at most one full-range primary computation by default.
9. Check special and boundary cases with the cheapest method sufficient for the intended evidence level: exact substitution, residuals, independent small cases, invariants, precision escalation, error bounds, or a second backend when it materially increases confidence. A second full-range run requires a discrepancy, inadequate first-run evidence, explicit user request, or the `high-assurance` profile; record that reason. Changing parameters while calling the same underlying algorithm is not an independent implementation.
10. Classify the evidence as `proof-certificate`, `formal-verification`, `exact-check`, `bounded-check`, or `numerical-evidence`. Never promote a bounded or numerical check into a universal proof.
11. Stop as soon as the requested computed result or deliverable exists, the selected verification has passed, the evidence level is stated honestly, and no unresolved discrepancy remains. Do not add another backend or rerun merely for reassurance. For a long feasible computation already authorized by the user, duration alone is not a stopping condition.
12. Return the result at the requested level. Produce code, result files, and a validated `computation-record.json` for `reproducible` and `high-assurance` work when the requested deliverable needs them; keep `chat` results in the conversation unless the user asks to save them.

## Mandatory Wolfram MCP Gate

Apply this gate when Wolfram is the selected primary backend, when the user explicitly requests Wolfram/MCP/external CAS execution, or before choosing a Mathematica command-line fallback. Do not invoke Wolfram merely because it could be an optional extra verifier after a non-Wolfram primary route already supports the intended claim.

1. Discover the current turn's callable tools. If Wolfram tools are not already visible, use the platform's tool-discovery mechanism to search for them.
2. If `WolframLanguageContext` is callable and the task needs Wolfram Language function selection or documentation, call it before writing or evaluating nontrivial Wolfram Language code.
3. If `WolframLanguageEvaluator` is callable, execute the requested computation through that MCP tool. A server entry, installed paclet, successful backend probe, or MCP handshake does not satisfy this step; the evaluator call itself must return.
4. Do not substitute `wolfram.exe`, `wolframscript`, a generated `.wl`/`.wls` file, Python, or mental calculation for a callable Wolfram MCP evaluator. Those are fallbacks only after tool discovery or an actual MCP call establishes that the evaluator is unavailable or failed.
5. Record the MCP tool used, the negotiated MCP `protocolVersion` from the `initialize` handshake or trusted runtime metadata, the MCP server name/version, and the returned Wolfram Language version or result. Keep these version fields distinct; never infer the protocol version from Agent Tools, server, client, or Mathematica versions. After both the handshake and evaluator succeed, persist the observation through `backend_inventory.py --mode RecordMcp` (or the PowerShell equivalent). The persisted observation remains historical-only and never proves current callability. When falling back, record the discovery or call failure and why the fallback is adequate.
6. If the user specifically required MCP rather than merely external verification, a non-MCP fallback does not fulfill the request. Stop and report the MCP failure unless the user already authorized a fallback.
7. Before asking MCP to inspect a generated local artifact, determine whether that artifact may be transmitted and whether the callable evaluator can read it. If transmission is not authorized or supported, do not make a doomed file-read attempt; use an allowed local verifier, or stop when the user required MCP-only execution.

## MCP Call-Window and Long-Run Routing

Treat backend capability and transport suitability as separate questions. A Wolfram evaluator can be callable and mathematically suitable while a complete computation is too long for one MCP tool call.

1. Distinguish the Wolfram kernel's computation limit, the evaluator's `timeConstraint`, the outer MCP or host tool-call deadline, and the agent's process-monitoring window. A larger evaluator `timeConstraint` does not extend an outer tool deadline. Discover documented limits when available; otherwise infer a conservative effective call window from bounded calls, never by sacrificing the full computation to a timeout.
2. Before a material full-range run, benchmark representative slices from the low, middle, and high-cost regions when cost varies with input size or candidate type. Include enough difficult survivors, large integers, or slow branches to reflect the dominant work. Do not extrapolate only from tiny, easy, low-end inputs. Compare serial and parallel routes on the same representative slice when parallelism may matter.
3. Put a safety margin between the conservative worst-case chunk estimate and every known inner or outer deadline. Normally target no more than one third of the shortest known call window, and never intentionally size a chunk above one half. Reduce the chunk further when runtime variance, startup cost, prime density, expression growth, or service load is uncertain.
4. Route by duration and recoverability:
   - use one MCP evaluation for work that comfortably fits the safety budget;
   - use bounded MCP chunks when each chunk fits, every completed chunk is checkpointed, and the final aggregation can prove complete non-overlapping coverage;
   - after the mandatory actual MCP capability or prototype evaluation, use an actually callable local executable or monitorable process for the full run when the calibrated workload cannot reasonably fit MCP call windows. The MCP gate validates semantics and availability; it does not require using MCP as the transport for an unsuitable long-running job.
5. The agent owns and reviews generated source code. Use MCP context and evaluation to confirm functions, semantics, boundary cases, and representative outputs; do not rely on an MCP call as a durable source editor or background-process supervisor.
6. A long local run must expose a process or cell identifier, compact progress or heartbeat, bounded resource use, and atomic or otherwise validated checkpoints. Prefer a yielded foreground process that the agent can resume waiting on; detach only when a durable monitor can unambiguously identify the process, progress, result, and failure state. Make resumed execution idempotent and prevent gaps, overlaps, or double counting.
7. Continue waiting while progress advances, resource use remains safe, and no correctness invariant fails, even when the original ETA was optimistic. Duration or ETA deviation alone is not a stopping condition. Diagnose a missing process, stagnant heartbeat, repeated errors, invalid checkpoints, or uncontrolled memory growth before deciding whether to resume, shrink chunks, or change route.
8. After any MCP timeout or interrupted tool call, determine whether the backend evaluation or local process is still running before retrying. Do not launch a duplicate full-range computation while cancellation is uncertain. Preserve and validate any completed checkpoints before recovery.
9. Preserve the requested evidence level across the route change. A probabilistic filter may reduce exact-verifier work but cannot support an exact final claim by itself; retain every true candidate, handle equality and boundary exceptions explicitly, and send survivors to an exact or certificate-producing verifier when exactness requires it.

## Exact Prime-Counting Route

For an exact prime-counting function calculation such as `PrimePi[x]`, an inclusive interval count, or a large nth-prime computation:

1. Apply the Mandatory Wolfram MCP Gate first. Use `WolframLanguageContext` to confirm the current function and method semantics, then call `WolframLanguageEvaluator` with exact integer input.
2. Accept a Wolfram result only when the evaluator returns a concrete exact integer. An unchanged expression such as `PrimePi[largeInteger]`, a timeout, a tool failure, or an implementation-range message is a failed numerical evaluation, not an answer.
3. If Wolfram MCP cannot produce the exact integer and the user did not require MCP-only execution, read or refresh the backend inventory and use its verified `local.primecount.path` when `local.primecount.status` is `available`.
4. For a closed integer interval `[a,b]`, compute `pi(b) - pi(a - 1)`. With primecount, invoke the exact default Gourdon algorithm for both endpoints; do not substitute the `--Li`, `--RiemannR`, or other approximation options.
5. For a nontrivial large computation, add `--double-check` so primecount recomputes with alternative alpha tuning factors. Classify agreement as an `exact-check`, not a proof certificate or a fully independent second implementation.
6. Record the Wolfram attempt, the reason it was inadequate, the resolved primecount executable and version, the exact endpoint commands, and the subtraction. If primecount is missing, do not download or install it without explicit user authorization.

This route is a specialist exception to the ordinary Mathematica/SageMath/Python comparison: use primecount only for operations it directly implements, and keep the Mandatory Wolfram MCP Gate first.

This route does not cover counting prime values of an arbitrary polynomial or sequence; those tasks use the ordinary workflow and an implementation suited to that predicate.

## Execution Efficiency

- Batch related availability checks, compilation, calibration, and result summarization into as few tool calls as practical without hiding failures.
- Keep long progress output out of the conversation. Write detailed block or iteration logs to a file when needed and return compact status and final summaries.
- Reuse a backend or executable already verified during the current run. Do not try equivalent command-line front ends in sequence without a concrete failure or compatibility reason.
- Do not generate optional binary hit lists, large tables, hashes, or delivery metadata for a `chat` request. Generate them only when they support the requested evidence or deliverable.
- Efficiency rules reduce avoidable work; they never authorize skipping a feasible requested computation or terminating a long run without the user's decision. Conversely, the completion gate does not require unrequested cross-validation, alternative full-range reruns, extra backends, or optional artifacts after the requested result is secure.

## User-Requested Fastest-Completion Mode

Activate this mode only when the user explicitly asks to finish the computation as fast as possible, minimize wall time, maximize speed, or gives an equivalent instruction. It changes implementation strategy, not the requested result, evidence level, correctness requirements, or completion gate.

1. Estimate whether the dominant work is safely decomposable and large enough to repay process, kernel-launch, data-transfer, synchronization, and memory overhead. Prefer a better algorithm or a backend's proven internal multithreading when it is likely faster. Do not blindly parallelize dependent, stateful, memory-bound, or very small work.
2. When Wolfram MCP is the selected primary backend, keep the Mandatory Wolfram MCP Gate and use the evaluator to inspect relevant session capacity such as `$ProcessorCount` and `$KernelCount`. For independent workloads, attempt an appropriate bounded parallel implementation such as `ParallelMap`, `ParallelTable`, `ParallelSubmit`, or `Parallelize`, launching kernels when needed and allowed. Use `DistributeDefinitions` or `ParallelNeeds` when worker kernels require definitions or packages.
3. When parallel overhead or MCP kernel availability is uncertain and the full computation is expected to be long, compare serial and parallel execution on the same representative bounded slice selected under the MCP call-window rules. Use the faster valid route for the full computation. Skip calibration for short jobs or when it would duplicate a material fraction of the requested work.
4. Treat failed kernel launch, license or server limits, insufficient memory, unsafe decomposition, or a slower calibration as reasons to keep or return to the best serial implementation. State the limitation briefly; do not present the number of launched kernels as evidence of speedup.
5. Preserve exactness, precision, deterministic seeds where applicable, assumptions, and verification. Run only the requested primary computation and proportionate checks; fastest-completion mode does not authorize redundant full-range runs.

## Backend Probe

Run with Python 3 on Windows, macOS, or Linux:

```text
python "<SKILL_ROOT>/scripts/probe_backends.py"
```

If Python is unavailable and PowerShell 7 is callable, use the compatibility entry:

```powershell
pwsh -NoLogo -NoProfile -File "<SKILL_ROOT>\scripts\probe_backends.ps1"
```

Pass `--sage-command` (PowerShell: `-SageCommand`) only for a known native Sage executable. On Windows, pass `--wsl-distro` and, if needed, `--wsl-sage-command` to inspect one explicitly chosen WSL distribution. WSL is not attempted on macOS or Linux. Do not start or enumerate every WSL distribution merely to search for SageMath.

For primecount, the probe resolves `--primecount-command` (PowerShell: `-PrimecountCommand`) first, then `PRIMECOUNT_EXE`, then `primecount` on `PATH`, then the verified Windows per-user portable location when applicable. An explicit command or environment override is authoritative and does not silently fall through to another executable.

The command emits one JSON object. Preserve probe failures as availability evidence; do not turn them into installation actions.

## Policy Harness

Before synchronizing or packaging this Skill, run:

```powershell
python "<SKILL_ROOT>\scripts\check_mcp_policy.py" --skill-file "<SKILL_ROOT>\SKILL.md" --openai-file "<SKILL_ROOT>\agents\openai.yaml"
python "<SKILL_ROOT>\scripts\check_backend_routing.py" --routing-file "<SKILL_ROOT>\references\backend-routing.md" --evidence-file "<SKILL_ROOT>\references\backend-routing-evidence.md"
```

The first checker prevents accidental removal of the trigger and mandatory MCP gate. The routing checker requires every route to state its task class, conditions, primary route, fallback, decision metrics, and evidence status; a rule cannot be labeled `benchmarked` unless it cites a registered evidence entry. These checks validate policy structure, not backend performance or actual MCP execution.

## Computation Record

Read [computation-record.md](references/computation-record.md), then initialize a record beside the deliverables:

```powershell
python "<SKILL_ROOT>\scripts\computation_record.py" init --task-file "<DELIVERY_DIR>\task.md" --record "<DELIVERY_DIR>\computation-record.json"
```

Fill the record after execution, compute the artifact hashes, and validate it:

```powershell
python "<SKILL_ROOT>\scripts\computation_record.py" validate --record "<DELIVERY_DIR>\computation-record.json"
```

Validation checks the task, backend decision, candidate implementations, domain and assumptions, precision, fallback reason, verification method and evidence level, and the paths and SHA-256 hashes of code and result artifacts. It does not rerun the computation or prove the mathematical claim.

A `chat` task does not require `computation-record.json` solely because the computation is long or uses a temporary program. Require the record when the user requests reproducible/file delivery, when artifacts are handed off, or under the `high-assurance` profile. Still name the backend and distinguish exact calculation from numerical evidence when that distinction matters.

## Boundaries

- Do not install software, enable a network service, use a cloud calculator, or transmit local data merely to satisfy backend preference.
- Do not invent backend availability from an installation path alone. Confirm executable availability with the probe and Mathematica MCP availability with an actual tool call.
- Do not use Wolfram Alpha or other remote services as an implicit substitute for local Mathematica.
- Do not report a model-derived function name as verified documentation.
- Do not hide a Python fallback. State why Mathematica and SageMath were unsuitable or unavailable.
- Do not claim that residual checks, random tests, plots, or finite enumeration prove a general theorem.
- This Skill handles only mathematics-related computation tasks. Do not route any other task to it, and do not perform work outside this scope.

## Skill Maintenance Note

- Update/rationale note: `AI工具/数学与科学计算技能.md`

## Canonical terminology

Read [canonical terminology](references/terminology.md) before changing a persistent object, schema, lifecycle, authority/evidence rule, stable interface, specialized behavior term, or hash-bound identity. Do not introduce synonyms, rename canonical terms, change constitutive fields, or reuse deprecated/reserved names without updating the terminology registry, version history, migration rule, and validator first.

`computation_job` means a reproducible mathematical or scientific computation with frozen inputs and acceptance checks.; `backend_snapshot` means a mutable local inventory of available computation backends and their verified capabilities.. These core distinctions are mandatory; the linked glossary is normative.
