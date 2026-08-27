# Prompt v7 compatibility tombstone

> [!CAUTION]
> **Superseded and inspection-only.** This filename is retained so historical references resolve. It must never generate, confirm, launch, Resume, migrate, or repair a run, and it must never create or recover a Goal.

Prompt v7 used the retired `Startup Router v2` and launcher/canary bundle. That design placed Goal ownership in an isolated child and is not an execution backend for Contract v8. Existing Prompt v7 artifacts remain frozen in their original project archives; this template is not authority for them.

New contracts use [Contract v8](contract-and-prompt-template-v8.md) with the [direct-current-Goal-task protocol](goal-host-protocol-v8.md). Startup v3 may classify a legacy record read-only. It never infers New or Resume authority from this file.

For historical interpretation only:

- preserve the original Prompt, manifest, thread history, contract, counters, approval policy, and receipt chain;
- do not rewrite a legacy run as v8 or treat a caller Goal status as child continuity evidence;
- if the archive records Goal-continuity failure, preserve it as terminal/no-retry;
- an explicitly user-created new Goal may use the v8 `LEGACY_SUCCESSOR` protocol to add a new run in the same project while preserving every old byte and cumulative record.
- legacy `rollover=false` / `rollover=never` blocks automatic or same-run rollover only, not a user-explicit new Goal plus the prescribed additive v8 successor under the normalized same-target/nonexpanded research envelope whose counters inherit all old consumption; mandatory retirement of old child-Goal/launcher/dispatcher/lease/control-receipt authority in favor of the v8 current-Goal path is a safe contraction, while any other envelope difference remains read-only pending an implemented `RUN_SUCCESSOR` and is not activated by confirmation alone.

The strings `scheduler host`, `child`, and `manifest` describe legacy record types only; they grant no dispatcher or launcher authority. This tombstone authorizes no command, approval submission, escalation, or project mutation.
