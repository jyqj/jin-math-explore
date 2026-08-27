from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_terminology.py"


def run_validator(root: Path) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--skill-root", str(root), "--json"],
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    return result.returncode, json.loads(result.stdout)


class TerminologyValidatorTests(unittest.TestCase):
    def test_current_window_model_passes(self) -> None:
        code, body = run_validator(ROOT)
        self.assertEqual(0, code, body)
        self.assertEqual("terminology_valid", body["code"])
        registry = json.loads((ROOT / "references" / "terminology-registry.json").read_text(encoding="utf-8"))
        self.assertEqual(len(registry["terms"]), body["term_count"])
        self.assertIn("terminal_sufficient_condition_register", {
            term["canonical_id"] for term in registry["terms"]
        })

    def test_missing_window_term_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            (stage / "references").mkdir()
            (stage / "scripts").mkdir()
            shutil.copy2(ROOT / "SKILL.md", stage / "SKILL.md")
            shutil.copy2(ROOT / "references" / "terminology.md", stage / "references" / "terminology.md")
            registry_path = ROOT / "references" / "terminology-registry.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["terms"] = [term for term in registry["terms"] if term["canonical_id"] != "window"]
            (stage / "references" / "terminology-registry.json").write_text(
                json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            code, body = run_validator(stage)
            self.assertNotEqual(0, code)
            self.assertEqual("terminology_current_model_incomplete", body["code"])
            self.assertIn("window", body["details"])


if __name__ == "__main__":
    unittest.main()
