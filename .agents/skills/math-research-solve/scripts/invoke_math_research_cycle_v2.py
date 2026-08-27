#!/usr/bin/env python3
"""Native cross-platform CLI for the immutable math-research cycle ledger."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from MathResearchCycleLedgerV2 import CycleLedgerError, invoke_action, verify
from math_research_control_primitives import ControlIntegrityError


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--action", "-Action", required=True, choices=["Status", "Verify", "AttemptStart", "AttemptEnd", "AuditStart", "AuditEnd", "ReturnCheck"])
    result.add_argument("--run-directory", "-RunDirectory", required=True, type=Path)
    result.add_argument("--ticket-id", "-TicketId")
    result.add_argument("--outcome", "-Outcome")
    result.add_argument("--artifact-file", "-ArtifactFile", type=Path)
    result.add_argument("--attempt-record-file", "-AttemptRecordFile", type=Path)
    result.add_argument("--failure-record-file", "-FailureRecordFile", type=Path)
    result.add_argument("--structure-signal", "-StructureSignal", choices=["present", "absent", "unknown"], default="unknown")
    result.add_argument("--repair-batches", "-RepairBatches", type=int, default=0)
    result.add_argument("--audit-ticket-file", "-AuditTicketFile", type=Path)
    result.add_argument("--audit-result-file", "-AuditResultFile", type=Path)
    result.add_argument("--next-tickets-file", "-NextTicketsFile", type=Path)
    result.add_argument("--completion", "-Completion", action="store_true")
    return result


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    try:
        if arguments.action in {"Status", "Verify"}:
            value = verify(arguments.run_directory)
        else:
            value = invoke_action(
                arguments.action, arguments.run_directory,
                ticket_id=arguments.ticket_id, outcome=arguments.outcome,
                artifact_file=arguments.artifact_file, attempt_record_file=arguments.attempt_record_file,
                failure_record_file=arguments.failure_record_file, structure_signal=arguments.structure_signal,
                repair_batches=arguments.repair_batches, audit_ticket_file=arguments.audit_ticket_file,
                audit_result_file=arguments.audit_result_file, next_tickets_file=arguments.next_tickets_file,
                completion=arguments.completion,
            )
        print(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0
    except (CycleLedgerError, ControlIntegrityError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc), "ok": False}, ensure_ascii=False, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
