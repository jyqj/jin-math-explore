#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("math_research_state_v9.py")
SPEC = importlib.util.spec_from_file_location("math_research_state_v9", MODULE)
mr = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mr)


def write_json(path: Path, value: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(mr.canonical_bytes(value))
    return mr.sha_file(path)


class TicketPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "inputs").mkdir()
        (self.root / "contracts").mkdir()
        (self.root / "inputs/problem.md").write_text("synthetic\n", encoding="utf-8")
        (self.root / "contracts/contract.md").write_text("contract\n", encoding="utf-8")
        self.req = self.root / "inputs/requirements.json"
        write_json(self.req, {"schema":"math-research-source-requirements/v1","requirements":[{"id":"problem","role":"task_contract","path":"inputs/problem.md","sha256":mr.sha_file(self.root/"inputs/problem.md"),"required":True}]})
        self.ticket = self.root / "ticket.json"
        self._write_ticket()

    def tearDown(self):
        self.temp.cleanup()

    def _write_ticket(self, extra_read: str | None = None, include_manifest: bool = True):
        artifacts=[{"path":"inputs/problem.md","sha256":mr.sha_file(self.root/"inputs/problem.md")}]
        if include_manifest: artifacts.append({"path":"inputs/requirements.json","sha256":mr.sha_file(self.req)})
        reads=[item["path"] for item in artifacts]+["contracts/contract.md"]
        if extra_read: reads.append(extra_read)
        write_json(self.ticket,{"contract":{"path":"contracts/contract.md","version":8,"binding_sha256":"1"*64},"ticket":{"ticket_id":"t1","input_artifacts":artifacts,"filesystem_scope":{"read_paths":reads,"writable_staging_path":"runs/r1/staging/t1/solver"}}})

    def test_closed_ticket_passes_and_requires_context_free_fork(self):
        result=mr.preflight_v8(self.root,self.ticket,self.req,None)
        self.assertEqual("none",result["worker_capsule"]["required_fork_turns"])

    def test_manifest_must_be_ticket_bound(self):
        self._write_ticket(include_manifest=False)
        with self.assertRaises(mr.ResearchError) as ctx: mr.preflight_v8(self.root,self.ticket,self.req,None)
        self.assertIn(ctx.exception.code,{"ticket_input_incomplete","ticket_read_closure_failed"})

    def test_unbound_read_is_rejected(self):
        self._write_ticket(extra_read="notes/unbound.md")
        with self.assertRaises(mr.ResearchError) as ctx: mr.preflight_v8(self.root,self.ticket,self.req,None)
        self.assertEqual("ticket_read_closure_failed",ctx.exception.code)

    def test_out_of_scope_access_log_invalidates_return(self):
        log=self.root/"access.json";write_json(log,{"schema":"math-research-worker-access-log/v1","reads":["notes/unbound.md"]})
        with self.assertRaises(mr.ResearchError) as ctx: mr.preflight_v8(self.root,self.ticket,self.req,log)
        self.assertEqual("worker_access_out_of_scope",ctx.exception.code)


if __name__ == "__main__": unittest.main(verbosity=2)
