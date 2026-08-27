#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from math_research_control_primitives import (
    ControlIntegrityError,
    FileLease,
    read_signed_json,
    strict_json_loads,
    write_signed_json,
)


class ControlPrimitiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.old_home = os.environ.get("MATH_RESEARCH_CONTROL_HOME")
        os.environ["MATH_RESEARCH_CONTROL_HOME"] = str(Path(self.temp.name) / "control")

    def tearDown(self) -> None:
        if self.old_home is None:
            os.environ.pop("MATH_RESEARCH_CONTROL_HOME", None)
        else:
            os.environ["MATH_RESEARCH_CONTROL_HOME"] = self.old_home
        self.temp.cleanup()

    def test_signed_round_trip_and_no_embedded_secret(self) -> None:
        path = Path(self.temp.name) / "state.json"
        write_signed_json(path, {"schema": "fixture/v1", "count": 3}, create_key=True)
        result = read_signed_json(path)
        self.assertEqual({"schema": "fixture/v1", "count": 3}, result["payload"])
        envelope = json.loads(path.read_text(encoding="utf-8"))
        self.assertNotIn("key", envelope)
        self.assertNotIn("secret", path.read_text(encoding="utf-8").casefold())

    def test_tamper_fails_closed(self) -> None:
        path = Path(self.temp.name) / "state.json"
        write_signed_json(path, {"count": 3}, create_key=True)
        envelope = json.loads(path.read_text(encoding="utf-8")); envelope["payload"]["count"] = 4
        path.write_text(json.dumps(envelope), encoding="utf-8")
        with self.assertRaises(ControlIntegrityError):
            read_signed_json(path)

    def test_backup_recovery(self) -> None:
        path = Path(self.temp.name) / "state.json"
        write_signed_json(path, {"generation": 1}, create_key=True)
        write_signed_json(path, {"generation": 2})
        path.write_text("corrupt", encoding="utf-8")
        result = read_signed_json(path)
        self.assertTrue(result["recovered_from_backup"])
        self.assertEqual(1, result["payload"]["generation"])

    def test_duplicate_json_is_blocked(self) -> None:
        with self.assertRaises(ControlIntegrityError):
            strict_json_loads('{"a":1,"a":2}')

    def test_key_permissions_are_private_on_posix(self) -> None:
        path = Path(self.temp.name) / "state.json"
        write_signed_json(path, {"ok": True}, create_key=True)
        if os.name != "nt":
            key = Path(os.environ["MATH_RESEARCH_CONTROL_HOME"]) / "manifest-key.v2"
            self.assertEqual(0, stat.S_IMODE(key.stat().st_mode) & 0o077)

    def test_lease_exclusion_and_release(self) -> None:
        with FileLease("run", "fixture"):
            with self.assertRaises(ControlIntegrityError):
                with FileLease("run", "fixture"):
                    pass
        with FileLease("run", "fixture"):
            pass


if __name__ == "__main__":
    unittest.main()
