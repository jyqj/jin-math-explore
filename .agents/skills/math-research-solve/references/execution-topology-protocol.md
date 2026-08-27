# Execution Topology Protocol

Use this protocol before dispatching an attempt, verifier, specialist, or audit worker. It proves a short-lived data path; it never grants authority, replaces a ticket or `window_queue_item`, creates a lease, or proves mathematics.

Physical agent count is not part of the mathematical state. A multi-agent Host may dispatch independent window queue items concurrently after each topology gate passes. When no subagent is available, the lead processes the same queue serially through separately frozen tickets and staging; this must not return an unsupported-multi-agent error. Do not occupy idle subagent slots merely to match a nominal roster.

## Required order

1. Run the read-free dispatch planner. Classify the project as `host_workspace_shared` or `project_root_rebind_required`.
2. Freeze three `math-research-execution-topology-descriptor/v1` objects: the exact worker topology, ingest/publisher topology, and long-lived desktop/application consumer topology. Bind runner, cwd/project root, sandbox mode, runner arguments, and the expected consumer OS principal.
3. In the actual future worker topology, run `access-prepare`. It reopens and hashes the ticket and every input, creates a nonce probe inside the exact ticket staging root, flushes and reopens it, and writes a short-lived worker receipt.
4. In the actual future ingest/publisher topology, run `validate-readback`. It independently reopens the head, ticket, inputs, worker receipt, and worker probe, then creates a fresh directory-and-file inheritance probe directly under the project root. The intermediate receipt remains `publisher_ready_for_consumer` and cannot start an attempt.
5. In the actual long-lived consumer topology, run `validate-consumer`. It requires the expected OS principal, recursively scans and hashes the whole project, reopens both worker- and publisher-owned probes, removes only those named probes, and atomically promotes the receipt to `ready_for_attempt_start`.
6. Put that ready receipt pointer in the queue item's `ATTEMPT_START` payload. The attempt-local state engine rejects a missing consumer observation, wrong principal, expired or mismatched receipt, invalid traversal counts, replayed generation, topology change, or staging escape before changing counters.
7. Fresh-check the product Goal, prepare and commit `ATTEMPT_START`, and read back startup state. Before `GO`, run `validate-project-consumer` from the same consumer boundary against the newly published `project.json` hash.
8. Prefer keeping the same worker session idle between `ACCESS_PREPARE` and `GO`. Send `GO(ticket_hash, head_hash, receipt_hash)` only after both committed and consumer readbacks. Run `go-check` in that session before mathematics.

If the platform cannot preserve one worker session, use the exact descriptor-bound project-root process and dispatch immediately after commit. Report this as best-effort topology continuity: the receipt proves the tested process boundaries, not an unobservable identity relation between two later processes. Requeueing after such a break is a Host state transition, never “lease recovery.”

## Descriptor schema

```json
{
  "schema": "math-research-execution-topology-descriptor/v1",
  "role": "worker|ingest|publisher|consumer",
  "transport": "collaboration|project-root-exec|another explicit transport",
  "execution_workspace_root": "<absolute project root>",
  "runner": "<fixed runner identity>",
  "sandbox_mode": "<exact mode>",
  "runner_arguments": ["<exact non-secret flags>"]
}
```

Do not put prompts, credentials, private content, or approval text in a descriptor.

The consumer descriptor is data-plane metadata, not authorization. On a Vault project it must describe the process identity used by Obsidian. A successful check under `CodexSandboxOffline`, an administrator, or the publisher does not substitute for the desktop user.

## Post-publication gate

Run `validate-project-consumer` after every canonical or auxiliary publication that creates or replaces project bytes. It must execute under the frozen consumer principal, recursively `scandir` every directory, hash every ordinary file, and match the exact published head hash. Its `math-research-consumer-readback-result/v1` output binds principal, head hash, aggregate tree hash, and traversal counts.

Failure is operational. Preserve bytes and the active attempt identity, stop further writes, and restore stable inherited consumer access from the object-owner topology. Retry the consumer gate once. Never count an ACL repair as mathematics, a negative route, or a semantic-reset trigger.

## Routing and recovery

- A project inside a Host workspace may use direct collaboration only after the same round trip passes.
- A project outside all Host workspaces defaults to a project-root controlled process. Do not treat ordinary or elevated PowerShell as a capability superset.
- A live v8-to-v10 migration is the only two-root exception. The predecessor and successor must be plain siblings. Read-only preparation may use one controlled process whose execution root is their canonical parent and whose fixed helper accepts only those two exact siblings. Freeze is then written/read back from the v8 boundary and publication from the v10 boundary. A parent-root receipt is migration-scoped and cannot authorize ordinary research workers, tickets, or later writes elsewhere under that parent.
- After `worker_input_unreadable`, `worker_staging_unwritable`, `host_or_ingest_readback_unavailable`, `publisher_topology_unavailable`, `consumer_scandir_unavailable`, `consumer_file_unreadable`, `consumer_principal_mismatch`, `consumer_readback_unavailable`, or `acl_authority_not_propagated`, preserve bytes and reroute at most once to the exact owner or consumer topology named by the error.
- Do not repeat the same failing topology, relay an authorization sentence to a child, mirror hash-bound inputs, or ask the user to copy commands or hashes.
- Before `ATTEMPT_START` or `AUDIT_START`, topology failure is operational and consumes no attempt, audit, or total round. After a start, never refund counters; keep the same attempt while attempting one operational ingest reroute, and never count that failure as mathematical evidence or a semantic-reset trigger.
- Worker, verifier, preflight, and publisher processes are Goal-agnostic data-plane actors. Only the current Goal Host calls `get_goal`, decides publication, and supplies the final active assertion to an official commit helper.

## Commands

Windows:

```powershell
scripts/invoke_math_research_execution_topology.ps1 -Action access-prepare ...
scripts/invoke_math_research_execution_topology.ps1 -Action validate-readback ...
scripts/invoke_math_research_execution_topology.ps1 -Action validate-consumer ...
scripts/invoke_math_research_execution_topology.ps1 -Action validate-project-consumer ...
scripts/invoke_math_research_execution_topology.ps1 -Action go-check ...
```

POSIX uses the same Python entry directly:

```sh
python -B scripts/math_research_execution_topology.py access-prepare ...
python -B scripts/math_research_execution_topology.py validate-readback ...
python -B scripts/math_research_execution_topology.py validate-consumer ...
python -B scripts/math_research_execution_topology.py validate-project-consumer ...
python -B scripts/math_research_execution_topology.py go-check ...
```
