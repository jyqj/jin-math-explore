# Platform Runtime Routing

The Windows versioned entry points remain authoritative. On Linux or macOS,
use `scripts/math_research.sh`; it selects the shared Python v10 or v9 engine
directly and invokes the same installed PowerShell v8 implementation
through `pwsh` only when a v8 or delegated legacy operation requires it.

## Requirements

- Windows: the existing PowerShell entry points and Python available as before.
- Linux/macOS: Python 3.12+ and PowerShell 7.5+ (`pwsh`).
- User-owned install and project directories. The installer never runs `sudo`,
  downloads a runtime, or changes a package manager.

Run the fail-closed preflight after installation:

```sh
sh scripts/math_research.sh doctor --json
```

Exit codes are `0` usable, `10` runtime missing, `11` runtime too old, `31`
unsupported OS, `40` permission/process failure, and `50` validation failure.

## Production command mapping

Use these POSIX commands wherever another protocol names the corresponding
PowerShell script:

```sh
sh scripts/math_research.sh startup --project PROJECT --audit-mode Auto --goal-status active
python -B scripts/math_research_worker_dispatch_preflight.py --project PROJECT --ticket TICKET --host-workspace-root HOST_ROOT --transport project-root-exec --execution-workspace-root PROJECT
python -B scripts/math_research_execution_topology.py access-prepare --project PROJECT --ticket TICKET --worker-topology WORKER_TOPOLOGY --publisher-topology PUBLISHER_TOPOLOGY --consumer-topology CONSUMER_TOPOLOGY --expected-consumer-principal PRINCIPAL --receipt RECEIPT
python -B scripts/math_research_execution_topology.py validate-readback --project PROJECT --receipt RECEIPT --publisher-topology PUBLISHER_TOPOLOGY
python -B scripts/math_research_execution_topology.py validate-consumer --project PROJECT --receipt RECEIPT --consumer-topology CONSUMER_TOPOLOGY
python -B scripts/math_research_execution_topology.py validate-project-consumer --project PROJECT --consumer-topology CONSUMER_TOPOLOGY --expected-consumer-principal PRINCIPAL --expected-project-head-sha256 SHA256
python -B scripts/math_research_execution_topology.py go-check --project PROJECT --receipt RECEIPT --expected-receipt-sha256 SHA256
sh scripts/math_research.sh ticket-preflight-v8 --project PROJECT --ticket TICKET --source-requirements REQUIREMENTS
sh scripts/math_research.sh build-legacy-successor-v8 --project-directory PROJECT --goal-objective-raw TEXT --goal-objective-sha256 SHA256
sh scripts/math_research.sh migrate-v8-to-v10 inspect --predecessor OLD
sh scripts/math_research.sh migrate-v8-to-v10 prepare --predecessor OLD --successor NEW --bootstrap BOOTSTRAP --output PLAN
sh scripts/math_research.sh migrate-v8-to-v10 freeze --predecessor OLD --plan PLAN
sh scripts/math_research.sh migrate-v8-to-v10 verify --predecessor OLD --successor NEW --plan PLAN
sh scripts/math_research.sh commit-head-v8 --project-directory PROJECT --candidate-head-file HEAD --expected-old-sha256 SHA256 --expected-old-control-generation N --expected-new-control-generation N
sh scripts/math_research.sh prepare-successor-v9 --predecessor-project OLD --successor-project NEW --spec SPEC --output PLAN
sh scripts/math_research.sh prepare-transition-v9 --project PROJECT --transition ATTEMPT_START --payload PAYLOAD --output PLAN --audit-mode Auto
sh scripts/math_research.sh commit-transition-v9 --plan PLAN --goal-status active
sh scripts/math_research.sh ticket-preflight-v10 --project PROJECT --ticket TICKET --access-log ACCESS_LOG
sh scripts/math_research.sh prepare-successor-v10 --predecessor-project OLD --successor-project NEW --spec SPEC --output PLAN
sh scripts/math_research.sh prepare-transition-v10 --project PROJECT --transition RESEARCH_CHECKPOINT --payload PAYLOAD --output PLAN --audit-mode Auto
sh scripts/math_research.sh commit-transition-v10 --plan PLAN --goal-status active

# research asset discovery, validation, and private export (all platforms)
python3 -B scripts/math_research_assets.py scan --project PROJECT --index INDEX
python3 -B scripts/math_research_assets.py validate --project PROJECT --index INDEX
python3 -B scripts/math_research_assets.py export-plan --project PROJECT --index INDEX --output PLAN
python3 -B scripts/math_research_assets.py export --project PROJECT --index INDEX --output NEW_DIRECTORY
```

The dispatcher does not alter result schemas, Goal gates, counters, hashes, or
authority. v10 and v9 operations use their versioned Python engines directly.
Startup invokes frozen Startup v4 through PowerShell only when the v10 engine
returns `delegate_startup_v4`; Startup v4 continues the older delegation chain.
The v8 builder and head commit always use their original
PowerShell implementations. If either runtime is unavailable, stop rather than
substituting a weaker implementation.

For observed POSIX execution, run `scripts/observer_run.py` with the same
registered phase label and put `--` before the `sh scripts/math_research.sh ...`
command. Observation remains local, quiet, fail-open, and non-authoritative.
