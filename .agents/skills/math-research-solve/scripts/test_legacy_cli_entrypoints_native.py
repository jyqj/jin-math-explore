#!/usr/bin/env python3
from __future__ import annotations

import json, os, subprocess, sys
from pathlib import Path

from math_research_control_primitives import read_signed_json
from test_legacy_v1_compat_migration_native import LegacyCompatibilityMigrationTests


class LegacyCliTests(LegacyCompatibilityMigrationTests):
    def run_cli(self, name: str, *args: str) -> dict:
        completed=subprocess.run([sys.executable,"-B",str(Path(__file__).with_name(name)),*args],capture_output=True,text=True,env=os.environ.copy())
        self.assertEqual(0,completed.returncode,completed.stderr); return json.loads(completed.stdout)

    def test_both_native_clis_analyze_apply_and_verify(self) -> None:
        root=Path(__file__).resolve().parent
        self.paths={"launcher_entry":root/"launch_math_research_legacy_v1_compat.py","launcher_module":root/"MathResearchLauncherV2.py","cycle_module":root/"MathResearchCycleLedgerV2.py","cycle_cli":root/"invoke_math_research_cycle_legacy_v1_compat.py","project_module":root/"MathResearchProjectArchiveV2.py","canary_host":root/"invoke_math_research_legacy_v1_compat_canary_host.py","canary_entry":root/"invoke_math_research_canary_v2.py"}; self.receipt["target"]={name:self.binding(path) for name,path in self.paths.items()}; self.write_receipt(self.receipt_path,self.receipt)
        common=("--run-directory",str(self.run),"--receipt-file",str(self.receipt_path)); self.assertEqual("ready_to_apply",self.run_cli("invoke_math_research_legacy_v1_compat_migration.py","--action","Analyze",*common)["Status"]); self.assertEqual("applied",self.run_cli("invoke_math_research_legacy_v1_compat_migration.py","--action","Apply",*common)["Status"]); self.assertEqual("already_applied",self.run_cli("invoke_math_research_legacy_v1_compat_migration.py","--action","Verify",*common)["Status"])
        manifest=read_signed_json(self.manifest_path)["payload"]; control_paths={"launcher_entry":root/"launch_math_research_legacy_v1_compat_v2.py","launcher_module":root/"MathResearchLauncherV2.py","argv_compat_module":root/"MathResearchApproveForMeArgvCompatV2.py","canary_host":root/"invoke_math_research_legacy_v1_compat_canary_host_v2.py","canary_module":root/"MathResearchLauncherV2.py","canary_entry":root/"invoke_math_research_canary_v2.py","cycle_cli":root/"invoke_math_research_cycle_legacy_v1_compat.py","amendment_module":root/"MathResearchLegacyV1ControlPathAmendmentV2.py","amendment_cli":root/"invoke_math_research_legacy_v1_control_path_amendment_v2.py"}
        receipt={"schema_version":1,"protocol":"math-research-legacy-v1-control-path-amendment/v2","amendment_id":"cli-control-v2","action":"omit_explicit_sandbox_with_approve_for_me","archive_directory_name":"cli-control-v2","project":{"project_id":"project-1","directory":str(self.root)},"run":{"id":"run-1","directory":str(self.run),"thread_id":"thread-1"},"contract":{"version":"v1","binding_sha256":"a"*64},"goal":{"objective_sha256":"b"*64},"prior_migration":{"receipt_sha256":self.binding(self.receipt_path)["sha256"]},"source":{"status":manifest["status"],"manifest_primary_sha256":self.binding(self.manifest_path)["sha256"],"manifest_backup_sha256":self.binding(Path(f"{self.manifest_path}.bak"))["sha256"],"counters":manifest["cycle_ledger"]["checkpoint"]},"target":{name:self.binding(path) for name,path in control_paths.items()},"authorization":{"approval_mode":"approve_for_me","effective_sandbox":"workspace-write","explicit_sandbox_argument_omitted":True,"objective_changed":False,"quantifiers_changed":False,"counters_reset":False,"permission_scope_expanded":False}}; control=self.root/"control-receipt.json"; self.write_receipt(control,receipt); args=("--run-directory",str(self.run),"--receipt-file",str(control),"--prior-migration-receipt-file",str(self.receipt_path)); self.assertEqual("ready_to_apply",self.run_cli("invoke_math_research_legacy_v1_control_path_amendment_v2.py","--action","Analyze",*args)["Status"]); self.assertEqual("applied",self.run_cli("invoke_math_research_legacy_v1_control_path_amendment_v2.py","--action","Apply",*args)["Status"]); self.assertEqual("already_applied",self.run_cli("invoke_math_research_legacy_v1_control_path_amendment_v2.py","--action","Verify",*args)["Status"])


if __name__=="__main__": import unittest; unittest.main()
