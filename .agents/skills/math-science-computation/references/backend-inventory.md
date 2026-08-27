# Backend Inventory Contract

Use this reference when reading, refreshing, or diagnosing the local backend capability snapshot.

## Authority layers

The capability model has two layers that must not be conflated:

1. The persistent local snapshot records installed executable paths, versions, selected Python modules, and the time of the last successful local probe.
2. The current-session overlay records which MCP tools the agent can discover now and whether the selected MCP call actually succeeds now.

An MCP result in a prior run is historical evidence only. The persistent file never proves that an MCP server is installed, exposed, authenticated, healthy, or callable in the current session.

## State location

`scripts/backend_inventory.py` is the platform-neutral entry. Use it with the current Python 3 interpreter on Windows, macOS, or Linux. If Python is unavailable but PowerShell 7 is callable, use `scripts/backend_inventory.ps1`; it implements the same cache contract. Do not require PowerShell merely to discover whether a mathematical backend exists.

Both entries resolve the state file in this order:

1. explicit `--state-file` or `-StateFile`;
2. `MATH_SCIENCE_BACKEND_INVENTORY`;
3. `<platform temporary directory>/Codex/math-science-computation/backend-inventory.json` through the platform temporary-directory API.

The fixed temporary-directory path is reused across tasks but may be removed by operating-system cleanup; absence is therefore a normal cache miss, not an error. Set `MATH_SCIENCE_BACKEND_INVENTORY` when a more durable writable location is available. The snapshot is runtime state, not a versioned file inside the Skill package. Writes use a temporary file in the destination directory followed by atomic replacement.

The local snapshot records the operating-system family and normalized architecture. A snapshot with missing or different host identity is refreshed instead of being trusted across machines. OS-specific discovery is bounded: PATH and explicit overrides work on every platform; Windows also checks known per-machine locations, macOS checks known application bundles, and Linux checks known Wolfram installation roots. WSL probing is Windows-only and runs only when the caller names a distribution.

## Fast path and refresh rules

- `--mode ReadOrCreate` (PowerShell: `-Mode ReadOrCreate`) reads a valid snapshot, checks only its recorded local executable paths and host identity, and returns immediately when the snapshot is unexpired. It must not start Mathematica, SageMath, Python, primecount, or any MCP tool on this cache-hit path.
- A missing file, invalid schema, expired snapshot, or missing recorded path triggers a local probe. Missing paths refresh only the affected records in the stored snapshot; expiry and invalid schema refresh all records.
- `--mode Refresh --backend <name>` (PowerShell: `-Mode Refresh -Backend <name>`) explicitly refreshes one or more records. `all` refreshes every local record.
- `--mode Invalidate --backend <name> --reason-code <code>` (PowerShell: `-Mode Invalidate -Backend <name> -ReasonCode <code>`) records a bounded failure reason and immediately refreshes the selected local record. Use it after a selected executable fails, changes version unexpectedly, or disappears.
- A failed atomic write does not erase a successful probe result. The command returns the live result with `cache.status = write_failed`; the next run may retry persistence.

The default maximum age is seven days. Set `--max-age-hours 0` (PowerShell: `-MaxAgeHours 0`) only for a controlled run that must disable age-based refresh.

## Planning rule

Read the snapshot before committing to a backend-dependent implementation. Merge it with the current turn's advertised tool list, choose a primary route and a concrete fallback, then live-check only the selected backend. If that live check contradicts the snapshot, invalidate or refresh the affected local record and re-plan from the corrected state.

For MCP, tool discovery supplies an `advertised` state and an actual selected tool call supplies `live`, `degraded`, or `unavailable`. Do not probe every MCP server merely to populate an inventory.

After a selected Mathematica MCP has both completed its `initialize` handshake and returned a live evaluator result, record the observation with `--mode RecordMcp`. Supply the negotiated `--mcp-protocol-version` separately from the MCP server implementation version and the Wolfram Language kernel version. The protocol value must be the handshake's date-form version; never infer it from an Agent Tools, server, client, or Mathematica version. `RecordMcp` also requires `--mcp-server-name`, `--mcp-server-version`, and `--mcp-wolfram-language-version`; partial records fail closed. The stored observation remains `historical_only` and cannot establish current callability.

## Performance budget

On a valid cache hit, internal inventory work should normally stay below 250 ms, with no backend startup and no state-file write. Treat two seconds as a hard diagnostic threshold for the inventory operation itself: if a cache hit exceeds it, inspect filesystem or endpoint-security latency before allowing the readiness gate to dominate a computation request. Backend startup and a cache-miss scan are outside the cache-hit budget and should occur only under the refresh rules above.
