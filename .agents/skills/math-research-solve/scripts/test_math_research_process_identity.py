#!/usr/bin/env python3
from __future__ import annotations

import copy
import subprocess
import sys
import time
import unittest

from math_research_process_identity import _DarwinBsdInfo, process_identity_matches, snapshot_process


class ProcessIdentityTests(unittest.TestCase):
    def test_darwin_contract_structure_size(self) -> None:
        import ctypes
        self.assertEqual(136, ctypes.sizeof(_DarwinBsdInfo))

    def setUp(self) -> None:
        self.child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        time.sleep(0.05)

    def tearDown(self) -> None:
        if self.child.poll() is None:
            self.child.terminate()
        try:
            self.child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.child.kill(); self.child.wait(timeout=5)

    def test_live_identity_matches(self) -> None:
        self.assertTrue(process_identity_matches(snapshot_process(self.child.pid)))

    def test_tampered_start_token_is_blocked(self) -> None:
        record = snapshot_process(self.child.pid); record["start_token"] += "-tampered"
        self.assertFalse(process_identity_matches(record))

    def test_tampered_executable_hash_is_blocked(self) -> None:
        record = snapshot_process(self.child.pid); record["executable_sha256"] = "0" * 64
        self.assertFalse(process_identity_matches(record))

    def test_exited_process_is_blocked(self) -> None:
        record = snapshot_process(self.child.pid)
        self.child.terminate(); self.child.wait(timeout=5)
        self.assertFalse(process_identity_matches(record))


if __name__ == "__main__":
    unittest.main()
