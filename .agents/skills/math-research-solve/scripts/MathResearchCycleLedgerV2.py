#!/usr/bin/env python3
"""Native immutable cycle ledger for policy schemas 1, 2, and 3."""

from __future__ import annotations

import hashlib
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from math_research_control_primitives import (
    ControlIntegrityError, FileLease, assert_no_symlink_chain, canonical_json,
    read_signed_json, strict_json_loads, write_signed_json,
)

LEDGER = "cycle-ledger"; POLICY = "cycle-policy.json"; INITIAL = "cycle-tickets-000.json"
AUDIT_ROLES = ["skeptic_quantifiers", "skeptic_strategy", "theory_tool_scout"]
NEGATIVE = {"route_refuted", "bounded_negative", "method_failed", "substantive_inconclusive", "aborted"}
CLAIMS = {"candidate_found", "proved_subclaim", "route_refuted", "bounded_negative"}
OUTCOMES = CLAIMS | {"portfolio_proposed", "method_failed", "substantive_inconclusive", "aborted"}
ATTEMPT_KINDS = {"route_discovery", "route_execution", "candidate_revision", "candidate_synthesis"}


class CycleLedgerError(RuntimeError): pass


def now() -> str: return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
def sha_bytes(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def sha_file(path: Path) -> str: return sha_bytes(path.read_bytes())
def sha_value(value: Any) -> str: return sha_bytes(canonical_json(value).encode("utf-8"))
def require(condition: bool, message: str) -> None:
    if not condition: raise CycleLedgerError(message)
def is_hash(value: Any) -> bool: return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None
def exact(value: Any, required: set[str], optional: set[str] = set(), label: str = "object") -> dict[str, Any]:
    require(isinstance(value, dict), f"{label} must be an object")
    require(set(value) == required | (set(value) & optional) and required <= set(value), f"{label} keys are invalid")
    return value


def run_path(value: Path) -> Path:
    path = assert_no_symlink_chain(value)
    require(path.is_dir(), "run directory does not exist")
    return path


def run_file(run: Path, value: Path, label: str) -> Path:
    path = assert_no_symlink_chain(value if value.is_absolute() else run / value)
    try: path.relative_to(run)
    except ValueError: raise CycleLedgerError(f"{label} is outside the run directory")
    require(path.is_file(), f"{label} is missing")
    return path


def relative(run: Path, path: Path) -> str: return path.relative_to(run).as_posix()


def read_json(path: Path, label: str) -> dict[str, Any]:
    require(path.stat().st_size <= 4 * 1024 * 1024, f"{label} is too large")
    try: value = strict_json_loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeError, ControlIntegrityError) as exc: raise CycleLedgerError(f"{label} is not strict JSON") from exc
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def validate_policy(policy: Any) -> dict[str, Any]:
    required = {"schema_version", "protocol", "total_round_budget", "attempt_budget", "audit_interval_attempts", "max_route_family_attempts_per_cycle", "max_repair_batches_per_attempt", "audit_roles"}
    value = exact(policy, required, label="cycle policy")
    schema = value["schema_version"]
    require(type(schema) is int and schema in {1, 2, 3} and value["protocol"] == f"math-research-cycle-policy/v{schema}", "cycle policy protocol is invalid")
    total, attempts, interval = value["total_round_budget"], value["attempt_budget"], value["audit_interval_attempts"]
    require(all(type(x) is int for x in (total, attempts, interval)) and total >= 2 and 1 <= attempts <= total and interval >= 1, "cycle policy budgets are invalid")
    require(total >= attempts + math.ceil(attempts / interval), "total round budget cannot accommodate required audits")
    require(value["max_route_family_attempts_per_cycle"] == 2 and value["max_repair_batches_per_attempt"] == 1, "cycle hard caps are invalid")
    require(value["audit_roles"] == AUDIT_ROLES, "cycle audit roles are invalid")
    return value


def resource_caps(value: Any, label: str) -> None:
    require(isinstance(value, dict) and bool(value), f"{label} resource caps are invalid")
    for key, number in value.items(): require(re.fullmatch(r"[a-z][a-z0-9_]{0,63}", key) is not None and type(number) is int and number >= 1, f"{label} resource cap is invalid")


def ticket_records(manifest: Any, label: str = "ticket manifest") -> dict[str, Any]:
    value = exact(manifest, {"schema_version", "cycle_id", "tickets"}, {"source_audit_id"}, label)
    schema = value["schema_version"]
    require(type(schema) is int and schema in {1, 2, 3} and re.fullmatch(r"cycle-[1-9]\d*", str(value["cycle_id"])) is not None, f"{label} identity is invalid")
    require(isinstance(value["tickets"], list) and bool(value["tickets"]), f"{label} is empty")
    base = {"ticket_id", "route_family_id", "mechanism_id", "bottleneck_id", "decision_question", "search_domain", "success_signal", "stop_signal", "resource_caps", "reopen_condition"}
    if schema >= 2: base |= {"route_id", "route_fingerprint_sha256"}
    if schema == 3: base |= {"attempt_kind"}
    result = []; seen = set()
    for ticket in value["tickets"]:
        optional = ({"reopen_evidence"} if schema >= 2 else set()) | ({"source_route_card", "source_claims"} if schema == 3 else set())
        ticket = exact(ticket, base, optional, f"{label} ticket")
        for key in base - {"resource_caps"}: require(isinstance(ticket[key], str) and bool(ticket[key].strip()), f"ticket {key} is empty")
        require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", ticket["ticket_id"]) is not None and ticket["ticket_id"] not in seen, "ticket ID is unsafe or duplicated")
        seen.add(ticket["ticket_id"]); resource_caps(ticket["resource_caps"], "ticket")
        if schema >= 2: require(is_hash(ticket["route_fingerprint_sha256"]), "route fingerprint is invalid")
        if schema == 3:
            require(ticket["attempt_kind"] in ATTEMPT_KINDS, "attempt kind is invalid")
            claims = ticket.get("source_claims", [])
            require(isinstance(claims, list) and all(is_hash(x) for x in claims), "source claims are invalid")
            if ticket["attempt_kind"] in {"candidate_revision", "candidate_synthesis"}: require(bool(claims), "revision/synthesis requires source claims")
            if "source_route_card" in ticket:
                card = exact(ticket["source_route_card"], {"source_attempt_id", "card_sha256"}, label="source route card")
                require(re.fullmatch(r"attempt-\d{4}", str(card["source_attempt_id"])) is not None and is_hash(card["card_sha256"]) and "source_audit_id" in value, "source route card is invalid")
        result.append({"ticket_id": ticket["ticket_id"], "ticket_sha256": sha_value(ticket), "ticket": ticket})
    return {"cycle_id": value["cycle_id"], "records": result, "value": value}


def read_ticket_manifest(run: Path, path: Path, expected_hash: str | None, label: str) -> dict[str, Any]:
    path = run_file(run, path, label); value = read_json(path, label); digest = sha_file(path)
    if expected_hash is not None: require(digest == expected_hash, f"{label} hash differs from ledger")
    records = ticket_records(value, label)
    return {"path": path, "file": relative(run, path), "sha256": digest, **records}


def project_directory(run: Path, required: bool) -> Path | None:
    project = run.parent.parent
    if run.parent.name != "runs" or not (project / "project.json").is_file():
        if required: raise CycleLedgerError("project-aware protocol requires <project>/runs/<run-id>")
        return None
    assert_no_symlink_chain(project)
    return project


def route_fingerprint(ticket: dict[str, Any]) -> str:
    material = {key: ticket[key] for key in ("route_id", "route_family_id", "mechanism_id", "decision_problem", "frozen_domain", "resource_caps")}
    return sha_value(material)


def validate_route_start(project: Path, ticket: dict[str, Any]) -> None:
    for key in ("route_id", "route_fingerprint_sha256", "mechanism_id", "decision_problem", "frozen_domain"): require(isinstance(ticket.get(key), str) and bool(ticket[key]), f"route ticket {key} is missing")
    require(is_hash(ticket["route_fingerprint_sha256"]) and route_fingerprint(ticket) == ticket["route_fingerprint_sha256"], "route ticket fingerprint mismatches")
    registry = read_json(run_file(project, project / "state" / "route-registry.json", "route registry"), "route registry")
    routes = registry.get("routes"); require(isinstance(routes, list), "route registry is invalid")
    matches = [x for x in routes if isinstance(x, dict) and ((x.get("route_id") == ticket["route_id"] and x.get("retry_fingerprint_sha256") == ticket["route_fingerprint_sha256"]) or (x.get("route_family_id") == ticket["route_family_id"] and x.get("status") in {"frozen", "closed"}))]
    exact_matches = [x for x in matches if x.get("route_id") == ticket["route_id"] and x.get("retry_fingerprint_sha256") == ticket["route_fingerprint_sha256"]]
    if len(matches) > 1: require(len(exact_matches) == 1, "route family is frozen by multiple records"); matches = exact_matches
    if len(matches) == 1 and matches[0].get("status") in {"frozen", "closed"}:
        evidence = ticket.get("reopen_evidence"); require(isinstance(evidence, dict) and set(evidence) == {"condition_id", "evidence_sha256"} and is_hash(evidence["evidence_sha256"]), "duplicate frozen route requires reopen evidence")
        require(evidence["condition_id"] in matches[0].get("reopen_condition_ids", []) and evidence["evidence_sha256"] not in matches[0].get("seen_evidence_sha256", []), "reopen evidence is not new and allowed")


def validate_source_claims(project: Path, claims: list[str]) -> None:
    require(bool(claims) and all(is_hash(x) for x in claims), "source claim hashes are invalid")
    found = set()
    for root_name in ("evidence", "attempts"):
        root = project / root_name
        if root.is_dir():
            for item in root.rglob("*"):
                if item.is_file() and not item.is_symlink():
                    digest = sha_file(item)
                    if digest in claims: found.add(digest)
    require(set(claims) <= found, "source claim hashes are absent from project archive")


def artifact(run: Path, value: Path, label: str) -> dict[str, str]:
    path = run_file(run, value, label); return {"file": relative(run, path), "sha256": sha_file(path)}


def validate_failure(run: Path, path: Path, attempt_id: str) -> dict[str, Any]:
    path = run_file(run, path, "failure record"); value = read_json(path, "failure record")
    required = {"schema", "attempt_id", "route_id", "decision_problem", "failed_step", "failure_reason", "excluded_scope", "not_excluded_scope", "retry_fingerprint_sha256", "reopen_conditions", "artifacts"}
    require(required <= set(value) and value["schema"] == 1 and value["attempt_id"] == attempt_id, "failure record identity is invalid")
    require(all(isinstance(value[k], str) and bool(value[k]) for k in required - {"schema", "reopen_conditions", "artifacts"}), "failure record text is incomplete")
    require(is_hash(value["retry_fingerprint_sha256"]) and isinstance(value["reopen_conditions"], list) and bool(value["reopen_conditions"]) and all(isinstance(x, str) and bool(x) for x in value["reopen_conditions"]), "failure record reopen contract is invalid")
    require(isinstance(value["artifacts"], list) and bool(value["artifacts"]), "failure record artifacts are empty")
    for item in value["artifacts"]:
        require(isinstance(item, dict) and set(item) >= {"file", "sha256"} and is_hash(item["sha256"]), "failure artifact binding is invalid")
        bound = artifact(run, Path(item["file"]), "failure artifact"); require(bound == {"file": Path(item["file"]).as_posix(), "sha256": item["sha256"]}, "failure artifact hash mismatches")
    return {"path": path, "file": relative(run, path), "sha256": sha_file(path), "value": value}


def route_portfolio(run: Path, path: Path, attempt_id: str) -> dict[str, Any]:
    path = run_file(run, path, "route portfolio"); value = exact(read_json(path, "route portfolio"), {"schema_version", "source_attempt_id", "routes"}, label="route portfolio")
    require(value["schema_version"] == 1 and value["source_attempt_id"] == attempt_id and isinstance(value["routes"], list) and bool(value["routes"]), "route portfolio identity is invalid")
    required = {"card_id", "route_id", "route_family_id", "mechanism_id", "bottleneck_id", "decision_question", "search_domain", "success_signal", "stop_signal", "reopen_condition"}; seen = set(); cards = []
    for card in value["routes"]:
        card = exact(card, required, label="route card"); require(all(isinstance(card[k], str) and bool(card[k]) for k in required), "route card text is empty")
        require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", card["card_id"]) is not None and card["card_id"] not in seen, "route card ID is unsafe or duplicate")
        seen.add(card["card_id"]); cards.append({"card_sha256": sha_value(card), "card": card})
    return {"path": path, "file": relative(run, path), "sha256": sha_file(path), "value": value, "cards": cards}


def attempt_record(run: Path, path: Path, active: dict[str, Any], outcome: str, result_artifact: dict[str, str], repairs: int) -> dict[str, Any]:
    path = run_file(run, path, "attempt record"); value = exact(read_json(path, "attempt record"), {"schema_version", "attempt_id", "ticket_id", "attempt_kind", "decision_question", "solver_reports", "verification_reports", "repair_batches", "result_artifact", "route_portfolio", "source_claims"}, label="attempt record")
    require(value["schema_version"] == 1 and value["attempt_id"] == active["attempt_id"] and value["ticket_id"] == active["ticket_id"] and value["attempt_kind"] == active["attempt_kind"] and value["decision_question"] == active["decision_question"] and value["repair_batches"] == repairs <= 1, "attempt record identity or repair count is invalid")
    require(value["result_artifact"] == result_artifact, "attempt result artifact mismatches")
    solvers = value["solver_reports"]; require(isinstance(solvers, list) and (outcome == "aborted" or bool(solvers)), "solver reports are missing")
    solver_hashes = set()
    for report in solvers:
        report = exact(report, {"file", "sha256"}, label="solver report"); bound = artifact(run, Path(report["file"]), "solver report")
        require(bound == report and report["sha256"] not in solver_hashes, "solver report hash mismatches or repeats"); solver_hashes.add(report["sha256"])
    verifications = value["verification_reports"]; require(isinstance(verifications, list), "verification reports are invalid")
    for report in verifications:
        report = exact(report, {"candidate_sha256", "verdict", "artifact_file", "artifact_sha256", "new_math_performed"}, label="verification report")
        require(is_hash(report["candidate_sha256"]) and report["verdict"] in {"PASS", "FAIL", "INCONCLUSIVE"} and report["new_math_performed"] is False, "verification report contract is invalid")
        bound = artifact(run, Path(report["artifact_file"]), "verification report"); require(bound == {"file": report["artifact_file"], "sha256": report["artifact_sha256"]} and report["artifact_sha256"] not in solver_hashes, "verification artifact is invalid or not independent")
    if outcome in CLAIMS:
        require(active["attempt_kind"] != "route_discovery" and bool(verifications) and verifications[-1]["verdict"] == "PASS" and verifications[-1]["candidate_sha256"] == result_artifact["sha256"], "claim outcome lacks exact final PASS")
        if repairs == 1: require(len(verifications) >= 2 and any(x["verdict"] != "PASS" for x in verifications[:-1]), "repair lacks pre-repair non-PASS")
    claims = value["source_claims"]; require(isinstance(claims, list) and all(is_hash(x) for x in claims) and claims == active.get("source_claims", []), "attempt source claims changed")
    if active["attempt_kind"] in {"candidate_revision", "candidate_synthesis"}: require(bool(claims), "revision/synthesis requires source claims")
    cards = []
    if outcome == "portfolio_proposed":
        require(active["attempt_kind"] == "route_discovery" and isinstance(value["route_portfolio"], dict) and set(value["route_portfolio"]) == {"file", "sha256"}, "portfolio outcome is invalid")
        portfolio = route_portfolio(run, Path(value["route_portfolio"]["file"]), active["attempt_id"]); require(portfolio["file"] == value["route_portfolio"]["file"] and portfolio["sha256"] == value["route_portfolio"]["sha256"], "route portfolio hash mismatches"); cards = portfolio["cards"]
    else: require(value["route_portfolio"] is None, "only portfolio outcome may bind route portfolio")
    return {"path": path, "file": relative(run, path), "sha256": sha_file(path), "value": value, "cards": cards}


def audit_ticket(run: Path, path: Path, state: dict[str, Any]) -> dict[str, Any]:
    path = run_file(run, path, "audit ticket"); value = exact(read_json(path, "audit ticket"), {"schema_version", "audit_id", "trigger", "snapshot_head_sha256", "contract_binding_sha256", "read_only", "roles", "resource_caps"}, label="audit ticket")
    require(value["schema_version"] == 1 and re.fullmatch(r"audit-[1-9]\d*", str(value["audit_id"])) and value["trigger"] in {"scheduled", "early", "completion", "closing"}, "audit ticket identity is invalid")
    require(value["snapshot_head_sha256"] == state["HeadPayloadSha256"] and value["contract_binding_sha256"] == state["ContractBindingSha256"] and value["read_only"] is True and value["roles"] == AUDIT_ROLES, "audit ticket binding is invalid")
    resource_caps(value["resource_caps"], "audit ticket")
    return {"path": path, "file": relative(run, path), "sha256": sha_file(path), "value": value}


def audit_result(run: Path, path: Path, state: dict[str, Any]) -> dict[str, Any]:
    path = run_file(run, path, "audit result"); value = exact(read_json(path, "audit result"), {"schema_version", "audit_id", "snapshot_head_sha256", "contract_binding_sha256", "new_math_performed", "reports", "synthesis"}, label="audit result")
    expected = 2 if state["Policy"]["schema_version"] == 3 else 1
    require(value["schema_version"] == expected and value["audit_id"] == state["ActiveAudit"]["audit_id"] and value["snapshot_head_sha256"] == state["ActiveAudit"]["snapshot_head_sha256"] and value["contract_binding_sha256"] == state["ContractBindingSha256"] and value["new_math_performed"] is False, "audit result binding is invalid")
    require(isinstance(value["reports"], list) and len(value["reports"]) == 3, "audit requires three reports"); seen = set(); all_pass = True
    for report in value["reports"]:
        report = exact(report, {"role", "verdict", "artifact_file", "artifact_sha256"}, label="audit report")
        require(report["role"] in AUDIT_ROLES and report["role"] not in seen and report["verdict"] in {"PASS", "FAIL", "INCONCLUSIVE"}, "audit report role/verdict is invalid"); seen.add(report["role"]); all_pass &= report["verdict"] == "PASS"
        require(artifact(run, Path(report["artifact_file"]), "audit report") == {"file": report["artifact_file"], "sha256": report["artifact_sha256"]}, "audit report artifact mismatches")
    required = {"action", "blocking_findings", "quarantined_leads"} | ({"accepted_route_cards"} if expected == 2 else set()); synthesis = exact(value["synthesis"], required, label="audit synthesis")
    action = synthesis["action"]; require(action in {"continue", "pivot-within-contract", "pause", "amendment-required", "reject-completion", "approve-completion"}, "audit action is invalid")
    if action == "approve-completion": require(all_pass and state["CompletionCandidate"], "completion requires candidate and three PASS reports")
    accepted = []; seen_cards = set()
    if expected == 2:
        require(isinstance(synthesis["accepted_route_cards"], list), "accepted route cards are invalid")
        for item in synthesis["accepted_route_cards"]:
            item = exact(item, {"source_attempt_id", "card_sha256"}, label="accepted route card")
            require(re.fullmatch(r"attempt-\d{4}", str(item["source_attempt_id"])) and is_hash(item["card_sha256"]) and item["card_sha256"] not in seen_cards and item["card_sha256"] in state["PendingRouteCards"] and state["PendingRouteCards"][item["card_sha256"]]["source_attempt_id"] == item["source_attempt_id"], "accepted route card is invalid"); seen_cards.add(item["card_sha256"]); accepted.append(item)
    return {"path": path, "file": relative(run, path), "sha256": sha_file(path), "value": value, "all_pass": all_pass, "action": action, "accepted": accepted}


def new_state() -> dict[str, Any]:
    return {"RunId": None, "ContractBindingSha256": None, "Policy": None, "HeadSequence": -1, "HeadPayloadSha256": None, "LastEventType": None, "AttemptCount": 0, "AuditCount": 0, "TotalRoundCount": 0, "AttemptsSinceLastAudit": 0, "AuditDue": False, "ActiveAttempt": None, "ActiveAudit": None, "CompletionCandidate": False, "CompletionAuthorized": False, "CurrentTicketsFile": None, "CurrentTicketsSha256": None, "CurrentCycleId": None, "ConsumedTicketIds": set(), "RouteCounts": {}, "PendingRouteCards": {}, "CleanReturn": False, "LastReturnCheckSequence": None}


def add_event(run: Path, sequence: int, run_id: str, event_type: str, previous: str | None, data: dict[str, Any]) -> None:
    path = run / LEDGER / f"{sequence:08d}.json"; require(not path.exists(), "cycle event already exists")
    payload = {"ledger_schema_version": 1, "sequence": sequence, "run_id": run_id, "event_type": event_type, "previous_payload_sha256": None if sequence == 0 else previous, "recorded_at_utc": now(), "data": data}
    write_signed_json(path, payload, create_key=True)


def _event_files(run: Path) -> list[Path]: return sorted((run / LEDGER).glob("*.json"))


def read_state(run: Path) -> dict[str, Any]:
    ledger = assert_no_symlink_chain(run / LEDGER); require(ledger.is_dir(), "cycle ledger is not initialized")
    files = _event_files(run); require(bool(files), "cycle ledger contains no genesis")
    state = new_state(); previous = None
    for index, path in enumerate(files):
        require(path.name == f"{index:08d}.json", "cycle ledger sequence has a gap or unexpected file")
        read = read_signed_json(path); require(not read["recovered_from_backup"], "immutable cycle event may not use backup"); event = read["payload"]
        require(isinstance(event, dict) and event.get("ledger_schema_version") == 1 and event.get("sequence") == index, "cycle event schema/sequence is invalid")
        if index == 0:
            require(event.get("event_type") == "GENESIS" and event.get("previous_payload_sha256") is None, "event zero must be genesis")
            state["RunId"] = event["run_id"]; state["ContractBindingSha256"] = event["data"]["contract_binding_sha256"]; state["Policy"] = validate_policy(event["data"]["policy"])
            state["CurrentTicketsFile"] = event["data"]["initial_tickets_file"]; state["CurrentTicketsSha256"] = event["data"]["initial_tickets_sha256"]; state["CurrentCycleId"] = event["data"]["initial_cycle_id"]
        else:
            require(event.get("run_id") == state["RunId"] and event.get("previous_payload_sha256") == previous, "cycle event identity/hash chain is invalid")
            data, kind, policy = event["data"], event["event_type"], state["Policy"]
            if kind == "ATTEMPT_START":
                require(state["ActiveAttempt"] is None and state["ActiveAudit"] is None and not state["AuditDue"] and not state["CompletionAuthorized"], "attempt starts from illegal state")
                require(state["AttemptCount"] < policy["attempt_budget"] and state["TotalRoundCount"] + 2 <= policy["total_round_budget"] and data["ticket_id"] not in state["ConsumedTicketIds"], "attempt violates budget or ticket uniqueness")
                manifest = read_ticket_manifest(run, Path(data["ticket_manifest_file"]), data["ticket_manifest_sha256"], "bound ticket manifest"); matches = [x for x in manifest["records"] if x["ticket_id"] == data["ticket_id"]]
                require(len(matches) == 1 and matches[0]["ticket_sha256"] == data["ticket_sha256"] and manifest["cycle_id"] == data["cycle_id"] and matches[0]["ticket"]["route_family_id"] == data["route_family_id"] and matches[0]["ticket"]["mechanism_id"] == data["mechanism_id"], "attempt changed ticket binding")
                if policy["schema_version"] >= 2: require(matches[0]["ticket"]["route_id"] == data["route_id"] and matches[0]["ticket"]["route_fingerprint_sha256"] == data["route_fingerprint_sha256"], "attempt changed route identity")
                if policy["schema_version"] == 3: require(matches[0]["ticket"]["attempt_kind"] == data["attempt_kind"] and matches[0]["ticket"]["decision_question"] == data["decision_question"], "attempt changed kind/question")
                route = data["route_family_id"]; require(state["RouteCounts"].get(route, 0) < policy["max_route_family_attempts_per_cycle"], "route-family cap exceeded")
                state["AttemptCount"] += 1; state["TotalRoundCount"] += 1; state["AttemptsSinceLastAudit"] += 1; state["ActiveAttempt"] = data; state["ConsumedTicketIds"].add(data["ticket_id"]); state["RouteCounts"][route] = state["RouteCounts"].get(route, 0) + 1
                if state["AttemptsSinceLastAudit"] >= policy["audit_interval_attempts"]: state["AuditDue"] = True
            elif kind == "ATTEMPT_END":
                require(state["ActiveAttempt"] is not None and data["attempt_id"] == state["ActiveAttempt"]["attempt_id"], "attempt end has no matching start")
                bound = artifact(run, Path(data["artifact_file"]), "attempt artifact"); require(bound == {"file": data["artifact_file"], "sha256": data["artifact_sha256"]}, "attempt artifact changed")
                if policy["schema_version"] >= 2 and data["outcome"] in NEGATIVE:
                    failure = validate_failure(run, Path(data["failure_record_file"]), state["ActiveAttempt"]["attempt_id"]); require(failure["sha256"] == data["failure_record_sha256"] and failure["value"]["retry_fingerprint_sha256"] == state["ActiveAttempt"]["route_fingerprint_sha256"], "failure record changed")
                if policy["schema_version"] == 3:
                    record = attempt_record(run, Path(data["attempt_record_file"]), state["ActiveAttempt"], data["outcome"], bound, data["repair_batches"]); require(record["sha256"] == data["attempt_record_sha256"], "attempt record changed")
                    for card in record["cards"]: require(card["card_sha256"] not in state["PendingRouteCards"], "route card repeats"); state["PendingRouteCards"][card["card_sha256"]] = {"source_attempt_id": state["ActiveAttempt"]["attempt_id"], "card": card["card"]}
                require(data["repair_batches"] <= policy["max_repair_batches_per_attempt"], "repair cap exceeded"); state["ActiveAttempt"] = None
                if data["outcome"] == "candidate_found": state["CompletionCandidate"] = True; state["AuditDue"] = True
                if data["outcome"] == "portfolio_proposed": state["AuditDue"] = True
            elif kind == "AUDIT_START":
                require(state["ActiveAttempt"] is None and state["ActiveAudit"] is None and state["AttemptsSinceLastAudit"] >= 1 and state["TotalRoundCount"] + 1 <= policy["total_round_budget"], "audit starts from illegal state")
                bound = audit_ticket(run, Path(data["audit_ticket_file"]), state); require(bound["sha256"] == data["audit_ticket_sha256"] and bound["value"]["audit_id"] == data["audit_id"], "audit ticket changed")
                state["AuditCount"] += 1; state["TotalRoundCount"] += 1; state["ActiveAudit"] = data
            elif kind == "AUDIT_END":
                require(state["ActiveAudit"] is not None and data["audit_id"] == state["ActiveAudit"]["audit_id"], "audit end has no matching start")
                result = audit_result(run, Path(data["audit_result_file"]), state); require(result["sha256"] == data["audit_result_sha256"] and result["action"] == data["action"] and result["all_pass"] == data["all_reports_pass"], "audit result changed")
                if data.get("next_tickets_file"):
                    nxt = read_ticket_manifest(run, Path(data["next_tickets_file"]), data["next_tickets_sha256"], "next tickets"); require(nxt["cycle_id"] == data["next_cycle_id"], "next cycle changed")
                state["ActiveAudit"] = None; state["AttemptsSinceLastAudit"] = 0; state["AuditDue"] = False; state["RouteCounts"] = {}; state["PendingRouteCards"] = {}
                if data["completion_authorized"]: state["CompletionAuthorized"] = True
                elif state["CompletionCandidate"]: state["CompletionCandidate"] = False
                state["CurrentTicketsFile"] = data.get("next_tickets_file"); state["CurrentTicketsSha256"] = data.get("next_tickets_sha256"); state["CurrentCycleId"] = data.get("next_cycle_id")
            elif kind == "RETURN_CHECKED": state["LastReturnCheckSequence"] = index
            else: raise CycleLedgerError("unknown cycle event type")
        require(state["AttemptCount"] <= state["Policy"]["attempt_budget"] and state["TotalRoundCount"] <= state["Policy"]["total_round_budget"] and state["AttemptsSinceLastAudit"] <= state["Policy"]["audit_interval_attempts"], "frozen budget violated")
        previous = sha_value(event); state["HeadSequence"] = index; state["HeadPayloadSha256"] = previous; state["LastEventType"] = event["event_type"]
    policy_live = read_json(run_file(run, run / POLICY, "cycle policy"), "cycle policy"); require(sha_value(policy_live) == sha_value(state["Policy"]), "cycle policy content differs from genesis")
    if state["CurrentTicketsFile"]: read_ticket_manifest(run, Path(state["CurrentTicketsFile"]), state["CurrentTicketsSha256"], "current tickets")
    state["CleanReturn"] = state["ActiveAttempt"] is None and state["ActiveAudit"] is None and not state["AuditDue"] and state["AttemptsSinceLastAudit"] == 0
    return state


def output(state: dict[str, Any]) -> dict[str, Any]:
    keys = ["RunId", "ContractBindingSha256", "HeadSequence", "HeadPayloadSha256", "LastEventType", "AttemptCount", "AuditCount", "TotalRoundCount", "AttemptsSinceLastAudit", "AuditDue", "ActiveAttempt", "ActiveAudit", "CompletionCandidate", "CompletionAuthorized", "CurrentTicketsFile", "CurrentTicketsSha256", "CurrentCycleId", "CleanReturn"]
    result = {key: state[key] for key in keys}; result.update({"TotalRoundBudget": state["Policy"]["total_round_budget"], "AttemptBudget": state["Policy"]["attempt_budget"], "AuditIntervalAttempts": state["Policy"]["audit_interval_attempts"]}); return result


def initialize(run_directory: Path, run_id: str, contract_sha256: str, policy_file: Path, tickets_file: Path) -> dict[str, Any]:
    run = run_path(run_directory)
    with FileLease("run", f"cycle:{run}"):
        require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", run_id) is not None and is_hash(contract_sha256), "run ID or contract hash is invalid")
        policy_path = run_file(run, policy_file, "cycle policy"); tickets_path = run_file(run, tickets_file, "initial tickets")
        require(policy_path.name == POLICY and tickets_path.name == INITIAL, "cycle input filenames are not canonical")
        policy = validate_policy(read_json(policy_path, "cycle policy")); tickets = read_ticket_manifest(run, tickets_path, None, "initial tickets")
        require(policy["schema_version"] == tickets["value"]["schema_version"] and tickets["cycle_id"] == "cycle-1", "cycle policy/ticket schema or cycle ID mismatches")
        if policy["schema_version"] >= 2: project_directory(run, True)
        ledger = run / LEDGER; require(not ledger.exists(), "cycle ledger already exists"); ledger.mkdir()
        data = {"contract_binding_sha256": contract_sha256, "policy_file": POLICY, "policy_sha256": sha_file(policy_path), "policy": policy, "baseline_audit_id": "audit-0", "baseline_completed": True, "baseline_counts_toward_budget": False, "baseline_user_ratified": True, "baseline_snapshot_manifest_sha256": tickets["sha256"], "initial_tickets_file": INITIAL, "initial_tickets_sha256": tickets["sha256"], "initial_cycle_id": tickets["cycle_id"], "initial_ticket_hashes": [{"ticket_id": x["ticket_id"], "ticket_sha256": x["ticket_sha256"]} for x in tickets["records"]]}
        add_event(run, 0, run_id, "GENESIS", None, data); return output(read_state(run))


def verify(run_directory: Path) -> dict[str, Any]:
    run = run_path(run_directory)
    with FileLease("run", f"cycle:{run}"): return output(read_state(run))


def checkpoint(run_directory: Path) -> dict[str, Any]:
    state = verify(run_directory)
    return {"ledger_schema_version": 1, "head_sequence": state["HeadSequence"], "head_payload_sha256": state["HeadPayloadSha256"], "attempt_count": state["AttemptCount"], "audit_count": state["AuditCount"], "total_round_count": state["TotalRoundCount"], "attempts_since_last_audit": state["AttemptsSinceLastAudit"], "audit_due": state["AuditDue"], "clean_return": state["CleanReturn"], "completion_authorized": state["CompletionAuthorized"]}


def invoke_action(
    action: str,
    run_directory: Path,
    *,
    ticket_id: str | None = None,
    outcome: str | None = None,
    artifact_file: Path | None = None,
    attempt_record_file: Path | None = None,
    failure_record_file: Path | None = None,
    structure_signal: str = "unknown",
    repair_batches: int = 0,
    audit_ticket_file: Path | None = None,
    audit_result_file: Path | None = None,
    next_tickets_file: Path | None = None,
    completion: bool = False,
) -> dict[str, Any]:
    """Validate and append one state-machine action, then replay it fail closed."""
    require(action in {"AttemptStart", "AttemptEnd", "AuditStart", "AuditEnd", "ReturnCheck"}, "cycle action is invalid")
    require(structure_signal in {"present", "absent", "unknown"}, "structure signal is invalid")
    require(type(repair_batches) is int and repair_batches >= 0, "repair batch count is invalid")
    run = run_path(run_directory)
    with FileLease("run", f"cycle:{run}"):
        state = read_state(run); policy = state["Policy"]
        sequence = state["HeadSequence"] + 1; data: dict[str, Any]

        if action == "AttemptStart":
            require(isinstance(ticket_id, str) and bool(ticket_id.strip()), "AttemptStart requires TicketId")
            require(state["ActiveAttempt"] is None and state["ActiveAudit"] is None and not state["AuditDue"] and not state["CompletionAuthorized"], "AttemptStart is blocked by current state")
            require(state["AttemptCount"] < policy["attempt_budget"], "attempt budget is exhausted")
            require(state["TotalRoundCount"] + 2 <= policy["total_round_budget"], "AttemptStart would consume the required audit round")
            require(state["CurrentTicketsFile"], "no approved ticket manifest is active")
            manifest = read_ticket_manifest(run, Path(state["CurrentTicketsFile"]), state["CurrentTicketsSha256"], "current ticket manifest")
            matches = [x for x in manifest["records"] if x["ticket_id"] == ticket_id]
            require(len(matches) == 1 and ticket_id not in state["ConsumedTicketIds"], "ticket is absent, duplicated, or consumed")
            record = matches[0]; ticket = record["ticket"]; route = ticket["route_family_id"]
            require(state["RouteCounts"].get(route, 0) < policy["max_route_family_attempts_per_cycle"], "route-family cap is reached")
            data = {
                "attempt_id": f"attempt-{state['AttemptCount'] + 1:04d}", "ticket_id": ticket_id,
                "ticket_sha256": record["ticket_sha256"], "ticket_manifest_file": manifest["file"],
                "ticket_manifest_sha256": manifest["sha256"], "cycle_id": manifest["cycle_id"],
                "route_family_id": route, "mechanism_id": ticket["mechanism_id"], "bottleneck_id": ticket["bottleneck_id"],
            }
            if policy["schema_version"] >= 2:
                project = project_directory(run, True)
                project_ticket = {
                    "route_id": ticket["route_id"], "route_family_id": ticket["route_family_id"],
                    "route_fingerprint_sha256": ticket["route_fingerprint_sha256"], "mechanism_id": ticket["mechanism_id"],
                    "decision_problem": ticket["decision_question"], "frozen_domain": ticket["search_domain"],
                    "resource_caps": ticket["resource_caps"],
                }
                if "reopen_evidence" in ticket: project_ticket["reopen_evidence"] = ticket["reopen_evidence"]
                validate_route_start(project, project_ticket)
                data.update({"route_id": ticket["route_id"], "route_fingerprint_sha256": ticket["route_fingerprint_sha256"]})
            if policy["schema_version"] == 3:
                claims = ticket.get("source_claims", [])
                data.update({"attempt_kind": ticket["attempt_kind"], "decision_question": ticket["decision_question"], "source_claims": claims})
                if ticket["attempt_kind"] in {"candidate_revision", "candidate_synthesis"}: validate_source_claims(project, claims)
            event_type = "ATTEMPT_START"

        elif action == "AttemptEnd":
            require(state["ActiveAttempt"] is not None and outcome in OUTCOMES and artifact_file is not None, "AttemptEnd requires active attempt, valid outcome, and artifact")
            require(repair_batches <= policy["max_repair_batches_per_attempt"], "repair-batch cap is exceeded")
            bound = artifact(run, artifact_file, "attempt artifact")
            data = {"attempt_id": state["ActiveAttempt"]["attempt_id"], "ticket_id": state["ActiveAttempt"]["ticket_id"], "outcome": outcome, "artifact_file": bound["file"], "artifact_sha256": bound["sha256"], "structure_signal": structure_signal, "repair_batches": repair_batches}
            if policy["schema_version"] == 3:
                require(attempt_record_file is not None, "schema-3 AttemptEnd requires attempt record")
                record = attempt_record(run, attempt_record_file, state["ActiveAttempt"], outcome, bound, repair_batches)
                data.update({"attempt_record_file": record["file"], "attempt_record_sha256": record["sha256"]})
                if outcome == "portfolio_proposed":
                    data.update({"route_portfolio_file": record["value"]["route_portfolio"]["file"], "route_portfolio_sha256": record["value"]["route_portfolio"]["sha256"], "route_card_hashes": [x["card_sha256"] for x in record["cards"]]})
            if policy["schema_version"] >= 2 and outcome in NEGATIVE:
                require(failure_record_file is not None, "negative AttemptEnd requires failure record")
                failure = validate_failure(run, failure_record_file, state["ActiveAttempt"]["attempt_id"])
                require(failure["value"]["retry_fingerprint_sha256"] == state["ActiveAttempt"]["route_fingerprint_sha256"], "failure retry fingerprint changed")
                data.update({"failure_record_file": failure["file"], "failure_record_sha256": failure["sha256"]})
            event_type = "ATTEMPT_END"

        elif action == "AuditStart":
            require(state["ActiveAttempt"] is None and state["ActiveAudit"] is None and state["AttemptsSinceLastAudit"] >= 1, "AuditStart requires completed attempts and no active work")
            require(state["TotalRoundCount"] + 1 <= policy["total_round_budget"] and audit_ticket_file is not None, "AuditStart lacks budget or ticket")
            bound = audit_ticket(run, audit_ticket_file, state); expected = f"audit-{state['AuditCount'] + 1}"
            require(bound["value"]["audit_id"] == expected, "audit ID is not monotone")
            data = {"audit_id": expected, "trigger": bound["value"]["trigger"], "snapshot_head_sha256": bound["value"]["snapshot_head_sha256"], "audit_ticket_file": bound["file"], "audit_ticket_sha256": bound["sha256"], "contract_binding_sha256": state["ContractBindingSha256"]}
            event_type = "AUDIT_START"

        elif action == "AuditEnd":
            require(state["ActiveAudit"] is not None and audit_result_file is not None, "AuditEnd requires active audit and result")
            result = audit_result(run, audit_result_file, state)
            next_file = next_sha = next_cycle = None; next_hashes: list[dict[str, str]] = []
            if next_tickets_file is not None:
                require(result["action"] not in {"approve-completion", "pause", "amendment-required"}, "audit action may not bind next tickets")
                nxt = read_ticket_manifest(run, next_tickets_file, None, "next ticket manifest")
                require(nxt["value"].get("source_audit_id") == state["ActiveAudit"]["audit_id"], "next tickets do not bind active audit")
                expected_cycle = int(state["CurrentCycleId"][6:]) + 1
                require(nxt["cycle_id"] == f"cycle-{expected_cycle}" and (policy["schema_version"] != 3 or nxt["value"]["schema_version"] == 3), "next ticket cycle/schema is invalid")
                if policy["schema_version"] == 3:
                    accepted = {x["card_sha256"] for x in result["accepted"]}
                    for entry in nxt["records"]:
                        ticket = entry["ticket"]; source = ticket.get("source_route_card")
                        matching = [x for x in state["PendingRouteCards"].values() if x["card"]["route_id"] == ticket["route_id"]]
                        require(not matching or source is not None, "discovered route lacks accepted card binding")
                        if source is not None:
                            card_hash = source["card_sha256"]
                            require(card_hash in accepted and card_hash in state["PendingRouteCards"], "next ticket references unaccepted route card")
                            stored = state["PendingRouteCards"][card_hash]; card = stored["card"]
                            require(source["source_attempt_id"] == stored["source_attempt_id"], "source attempt changed")
                            mapping = {"route_id":"route_id", "route_family_id":"route_family_id", "mechanism_id":"mechanism_id", "bottleneck_id":"bottleneck_id", "decision_question":"decision_question", "search_domain":"search_domain", "success_signal":"success_signal", "stop_signal":"stop_signal", "reopen_condition":"reopen_condition"}
                            require(all(ticket[k] == card[v] for k, v in mapping.items()), "next ticket changed accepted route card")
                next_file, next_sha, next_cycle = nxt["file"], nxt["sha256"], nxt["cycle_id"]
                next_hashes = [{"ticket_id": x["ticket_id"], "ticket_sha256": x["ticket_sha256"]} for x in nxt["records"]]
            else:
                require(result["action"] not in {"continue", "pivot-within-contract", "reject-completion"}, "continuing audit requires next tickets")
            authorized = result["action"] == "approve-completion" and result["all_pass"]
            data = {"audit_id": state["ActiveAudit"]["audit_id"], "audit_result_file": result["file"], "audit_result_sha256": result["sha256"], "action": result["action"], "all_reports_pass": result["all_pass"], "completion_authorized": authorized, "next_tickets_file": next_file, "next_tickets_sha256": next_sha, "next_cycle_id": next_cycle, "next_ticket_hashes": next_hashes}
            if policy["schema_version"] == 3: data["accepted_route_cards"] = result["accepted"]
            event_type = "AUDIT_END"

        else:
            require(state["ActiveAttempt"] is None and state["ActiveAudit"] is None and not state["AuditDue"] and state["AttemptsSinceLastAudit"] == 0, "ReturnCheck requires a completed audit and no active work")
            require(not completion or state["CompletionAuthorized"], "completion requires unanimous completion audit")
            data = {"completion": completion, "completion_authorized": state["CompletionAuthorized"]}; event_type = "RETURN_CHECKED"

        add_event(run, sequence, state["RunId"], event_type, state["HeadPayloadSha256"], data)
        return output(read_state(run))
