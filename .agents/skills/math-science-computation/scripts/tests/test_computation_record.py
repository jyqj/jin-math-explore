from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "computation_record.py"
SPEC = importlib.util.spec_from_file_location("computation_record", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ComputationRecordTests(unittest.TestCase):
    def make_record(
        self,
        root: Path,
        *,
        selected_backend: str = "python",
        mode: str = "exact",
        evidence_level: str = "exact-check",
    ) -> Path:
        task = root / "task.md"
        code = root / "compute.py"
        result = root / "result.json"
        record_path = root / "computation-record.json"
        task.write_text("Compute a synthetic invariant.\n", encoding="utf-8")
        code.write_text("print(6 * 7)\n", encoding="utf-8")
        result.write_text('{"value": 42}\n', encoding="utf-8")

        process = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "init",
                "--task-file",
                str(task),
                "--record",
                str(record_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["task"]["object"] = "synthetic exact invariant"
        record["task"]["deliverables"] = ["compute.py", "result.json"]
        record["mathematical_context"]["assumptions"] = ["integer arithmetic"]
        record["mathematical_context"]["domain"] = "integers"
        record["mathematical_context"]["precision"] = {
            "mode": mode,
            "working_digits": 80 if mode != "exact" else None,
            "target_tolerance": "1e-60" if mode != "exact" else "",
        }
        availability = {
            "mathematica": "available" if selected_backend == "mathematica" else "unavailable",
            "sagemath": "available" if selected_backend == "sagemath" else "unavailable",
            "python": "available",
        }
        for backend in ("mathematica", "sagemath", "python"):
            record["implementation_discovery"][backend] = {
                "candidate_implementations": (
                    ["SyntheticBuiltIn"] if backend == selected_backend else []
                ),
                "existence_evidence": (
                    "documented synthetic candidate"
                    if backend == selected_backend
                    else "targeted check found no suitable synthetic candidate"
                ),
                "local_availability": availability[backend],
                "availability_evidence": f"synthetic {backend} probe",
            }
        record["decision"] = {
            "selected_backend": selected_backend,
            "backend_version": "test-version",
            "selection_reason": "selected for the synthetic fixture",
            "fallback_reason": (
                "Mathematica and SageMath were unsuitable in this fixture"
                if selected_backend == "python"
                else "not-required"
            ),
        }
        record["execution"] = {
            "status": "complete",
            "interface": "local process",
            "command_or_input": "python compute.py",
            "code_artifact": "compute.py",
        }
        record["artifacts"] = [
            {"role": "code", "path": "compute.py", "sha256": file_hash(code)},
            {"role": "result", "path": "result.json", "sha256": file_hash(result)},
        ]
        record["result"] = {
            "status": "complete",
            "summary": "The synthetic result is 42.",
            "result_artifact": "result.json",
        }
        record["verification"] = {
            "methods": ["independent integer multiplication"],
            "evidence_level": evidence_level,
            "residual_or_error": "absolute residual < 1e-70" if mode != "exact" else "",
            "limitations": ["synthetic fixture"],
        }
        record_path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return record_path

    def test_valid_python_fallback_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            record_path = self.make_record(Path(temporary))
            result = MODULE.validate_record(record_path, None)
            self.assertTrue(result["ok"])
            self.assertEqual(result["selected_backend"], "python")
            self.assertEqual(len(result["verified_artifacts"]), 2)

    def test_valid_numerical_record_requires_precision_and_residual(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            record_path = self.make_record(
                Path(temporary), mode="arbitrary", evidence_level="numerical-evidence"
            )
            result = MODULE.validate_record(record_path, None)
            self.assertEqual(result["evidence_level"], "numerical-evidence")

    def test_rejects_bad_artifact_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            record_path = self.make_record(Path(temporary))
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["artifacts"][0]["sha256"] = "0" * 64
            record_path.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.RecordError, "does not match"):
                MODULE.validate_record(record_path, None)

    def test_rejects_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            record_path = self.make_record(root)
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["artifacts"][0]["path"] = "../outside.py"
            record_path.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.RecordError, "escapes"):
                MODULE.validate_record(record_path, None)

    def test_rejects_python_fallback_without_reason(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            record_path = self.make_record(Path(temporary))
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["decision"]["fallback_reason"] = ""
            record_path.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.RecordError, "fallback_reason"):
                MODULE.validate_record(record_path, None)

    def test_rejects_numerical_record_without_residual(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            record_path = self.make_record(
                Path(temporary), mode="machine", evidence_level="numerical-evidence"
            )
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["verification"]["residual_or_error"] = ""
            record_path.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.RecordError, "residual_or_error"):
                MODULE.validate_record(record_path, None)


if __name__ == "__main__":
    unittest.main()
