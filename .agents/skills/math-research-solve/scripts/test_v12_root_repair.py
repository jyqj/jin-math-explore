#!/usr/bin/env python3

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("repair", Path(__file__).with_name("repair_v12_root_layout.py"))
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RootRepairTests(unittest.TestCase):
    def test_unarchived_extra_blocks_repair(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            (project / ".research/objects/sha256").mkdir(parents=True)
            (project / "project.json").write_text('{"project_id":"synthetic"}\n', encoding="utf-8")
            extra = project / "legacy.txt"
            extra.write_text("changed bytes\n", encoding="utf-8")
            tree = project / ".research/imported-projects/source.json"
            tree.parent.mkdir(parents=True)
            wrong = "0" * 64
            tree.write_text(json.dumps({"entries": [{"path": "legacy.txt", "sha256": wrong, "size": extra.stat().st_size}]}) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "uncovered or changed extra file"):
                MODULE.inspect(project, tree)


if __name__ == "__main__":
    unittest.main()
