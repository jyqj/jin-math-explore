from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED_TEXT = {
    "external verification trigger": "external-tool, CAS, or MCP verification explicitly requested by the user",
    "mandatory gate heading": "## Mandatory Wolfram MCP Gate",
    "context tool": "`WolframLanguageContext`",
    "evaluator tool": "`WolframLanguageEvaluator`",
    "actual evaluator return": "the evaluator call itself must return",
    "no local-script substitution": "Do not substitute `wolfram.exe`, `wolframscript`",
    "MCP-specific failure rule": "a non-MCP fallback does not fulfill the request",
    "exact prime-counting route": "## Exact Prime-Counting Route",
    "unevaluated PrimePi rejection": "An unchanged expression such as `PrimePi[largeInteger]`",
    "primecount verified fallback": "use its verified `local.primecount.path`",
    "primecount exact cross-check": "add `--double-check`",
    "execution profiles": "## Execution Profiles",
    "default chat profile": "`chat` is the default",
    "mathematical precheck": "run one bounded mathematical-structure precheck",
    "single full-range default": "Run at most one full-range primary computation by default",
    "second full-range justification": "A second full-range run requires",
    "explicit stop rule": "Stop as soon as",
    "local artifact preflight": "Before asking MCP to inspect a generated local artifact",
    "call-window heading": "## MCP Call-Window and Long-Run Routing",
    "outer deadline separation": "A larger evaluator `timeConstraint` does not extend an outer tool deadline",
    "representative calibration": "benchmark representative slices from the low, middle, and high-cost regions",
    "call-window safety margin": "target no more than one third of the shortest known call window",
    "durable local route": "use an actually callable local executable or monitorable process for the full run",
    "coverage checkpoints": "prove complete non-overlapping coverage",
    "health-based waiting": "Continue waiting while progress advances, resource use remains safe",
    "timeout duplicate prevention": "Do not launch a duplicate full-range computation while cancellation is uncertain",
    "probabilistic filter boundary": "A probabilistic filter may reduce exact-verifier work but cannot support an exact final claim by itself",
    "prime-route exclusion": "does not cover counting prime values of an arbitrary polynomial or sequence",
    "compact progress output": "Keep long progress output out of the conversation",
    "chat record scope": "A `chat` task does not require `computation-record.json` solely because the computation is long",
    "feasibility gate": "## Mandatory Feasibility and Completion Gate",
    "estimate first": "Estimate feasibility first",
    "large exact integers": "especially unusually large exact-integer calculations",
    "mandatory execution": "The model has no discretion to omit it",
    "actual result delivery": "Return the actual computed result",
    "no extra verification": "does not require unrequested cross-validation",
    "long runtime warning": "If expected runtime is long, warn the user",
    "user termination authority": "The user retains the right to terminate it",
    "duration not stop condition": "duration alone is not a stopping condition",
    "fastest-completion heading": "## User-Requested Fastest-Completion Mode",
    "explicit speed trigger": "only when the user explicitly asks to finish the computation as fast as possible",
    "parallel overhead gate": "safely decomposable and large enough to repay process, kernel-launch, data-transfer, synchronization, and memory overhead",
    "Wolfram capacity probe": "`$ProcessorCount` and `$KernelCount`",
    "bounded parallel attempt": "attempt an appropriate bounded parallel implementation",
    "serial fallback": "return to the best serial implementation",
    "parallel correctness boundary": "Preserve exactness, precision, deterministic seeds where applicable",
    "exclusive computation scope": "This Skill handles only mathematics-related computation tasks. Do not route any other task to it, and do not perform work outside this scope.",
    "backend readiness heading": "## Backend Readiness Gate",
    "inventory read-or-create": "`python scripts/backend_inventory.py --mode ReadOrCreate`",
    "PowerShell inventory compatibility": "`scripts/backend_inventory.ps1 -Mode ReadOrCreate`",
    "cache-hit no-start rule": "On a cache hit, do not start Mathematica, SageMath, Python, primecount, or any MCP tool",
    "session MCP overlay": "Build a current-session MCP overlay",
    "historical MCP boundary": "A historical MCP result never proves current callability",
    "primary and fallback readiness": "choose one primary route and a concrete fallback",
    "targeted invalidation": "`backend_inventory.py --mode Invalidate --backend <name> --reason-code <code>`",
    "cache-hit performance threshold": "above two seconds as a performance fault",
    "English Skill heading": "# Math & Science Computation",
}

FORBIDDEN_TEXT = {
    "Vault task enumeration": "Vault writes",
    "PDF task enumeration": "PDF source verification",
    "Math Coach task enumeration": "Math Coach route selection",
    "research task enumeration": "research-contract approval",
    "Manim task enumeration": "Manim rendering",
}

REQUIRED_OPENAI_TEXT = {
    "English display name": 'display_name: "Math & Science Computation"',
    "English short description": 'short_description: "Route computations efficiently and verify proportionately"',
    "chat efficiency prompt": "Stop after the requested result and proportionate verification are secure",
    "primecount fallback prompt": "For exact prime-counting, try Wolfram MCP first",
    "feasibility prompt": "estimate feasibility first",
    "mandatory computation prompt": "actual execution and delivery of the computed result are mandatory",
    "user termination prompt": "only the user may choose to terminate",
    "fastest-completion prompt": "explicitly requests the fastest possible completion or minimum wall time",
    "multicore fallback prompt": "fall back to the best serial route when parallelism is unavailable, unsafe, or slower",
    "call-window prompt": "Treat the evaluator timeConstraint and the outer MCP tool-call deadline as separate limits",
    "local monitor prompt": "route a workload that cannot fit MCP call windows to a monitorable local process",
    "timeout inspection prompt": "inspect whether work is still running before retrying after a timeout",
    "exclusive scope prompt": "only for mathematics-related computation tasks; do not route unrelated work to it or perform work outside that scope",
    "inventory prompt": "read or create the persistent local backend inventory first",
    "cache-hit no-start prompt": "A valid cache hit must not start Mathematica, SageMath, Python, primecount, or any MCP tool",
    "session MCP authority prompt": "Treat persisted MCP information as historical only",
    "targeted refresh prompt": "Refresh or invalidate only the affected local record",
}


def validate(skill_text: str, openai_text: str) -> list[str]:
    errors = [
        f"missing: {label}"
        for label, required in REQUIRED_TEXT.items()
        if required not in skill_text
    ]
    errors.extend(
        f"missing: {label}"
        for label, required in REQUIRED_OPENAI_TEXT.items()
        if required not in openai_text
    )
    errors.extend(
        f"forbidden: {label}"
        for label, forbidden in FORBIDDEN_TEXT.items()
        if forbidden in skill_text
    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-file", required=True)
    parser.add_argument("--openai-file", required=True)
    args = parser.parse_args()

    skill_path = Path(args.skill_file)
    openai_path = Path(args.openai_file)
    errors = validate(
        skill_path.read_text(encoding="utf-8"),
        openai_path.read_text(encoding="utf-8"),
    )
    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"mcp_policy_ok skill={skill_path} openai={openai_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
