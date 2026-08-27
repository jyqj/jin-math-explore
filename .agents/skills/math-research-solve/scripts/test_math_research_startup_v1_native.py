#!/usr/bin/env python3
import hashlib, json, os, tempfile, unittest
from pathlib import Path
from MathResearchProjectArchiveV2 import initialize_project, read_json, register_contract
from math_research_startup_v1 import classify, sha_file, sha_text

class StartupV1NativeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name); self.vault=self.root/"vault"; (self.vault/"笔记草稿/公开问题的尝试").mkdir(parents=True); self.old=os.environ.get("MATH_RESEARCH_CONTROL_HOME"); control=self.root/"control"; control.mkdir(mode=0o700); os.chmod(control,0o700); os.environ["MATH_RESEARCH_CONTROL_HOME"]=str(control)
    def tearDown(self):
        if self.old is None:os.environ.pop("MATH_RESEARCH_CONTROL_HOME",None)
        else:os.environ["MATH_RESEARCH_CONTROL_HOME"]=self.old
        self.temp.cleanup()
    def project(self,name="project-one",legacy=False):
        legacy_dirs=[]
        if legacy:
            old=self.root/"old"; old.mkdir(); (old/"note.md").write_text("old",encoding="utf-8"); legacy_dirs=[old]
        return Path(initialize_project(self.vault/"笔记草稿/公开问题的尝试",name,"project-0001","Prove T",legacy_run_directories=legacy_dirs)["ProjectDirectory"])
    def test_fresh_and_partial_slots_are_read_only(self):
        fresh=classify(version=1,goal_status="none",vault_root=self.vault,project_directory_name="fresh"); self.assertEqual(("fresh_project_slot",0,"pre_goal_preparation_only_research_forbidden"),(fresh["startup_class"],fresh["controller_call_count"],fresh["goal_gate"])); partial=self.vault/"笔记草稿/公开问题的尝试/partial"; partial.mkdir(); result=classify(version=2,goal_status="none",vault_root=self.vault,project_directory_name="partial"); self.assertEqual(("partial_project_tree_recovery","inspect_partial_tree_without_initializing_over_it"),(result["startup_class"],result["next_action"]))
    def test_first_contract_and_goal_gates(self):
        project=self.project(); result=classify(version=1,goal_status="none",project_directory=project); self.assertEqual(("existing_project_first_contract","ResumePlan",1),(result["startup_class"],result["controller_action"],result["controller_call_count"])); paused=classify(version=1,goal_status="paused",project_directory=project); self.assertEqual(("wait_for_goal_control","goal_control_paused"),(paused["next_action"],paused["recovery_reason"]))
    def test_resume_precedence(self):
        project=self.project(); checkpoint=project/"state/checkpoint.json"; value=read_json(checkpoint,"checkpoint"); value["contract"]={"status":"confirmed","path":"contracts/c.md","sha256":"a"*64,"version":"v1"}; value["run"]={"status":"active","id":"run-1","path":"runs/run-1"}; checkpoint.write_text(json.dumps(value),encoding="utf-8"); result=classify(version=2,goal_status="active",project_directory=project); self.assertEqual("resume_signed_run",result["next_action"]); value["audit_due"]=True; checkpoint.write_text(json.dumps(value),encoding="utf-8"); self.assertEqual("run_due_audit",classify(version=2,goal_status="active",project_directory=project)["next_action"])
    def test_registered_preparing_and_extra_file_recovery(self):
        project=self.project(); run=project/"runs/run-1"; run.mkdir(); prompt=run/"prompt.md"; goal=run/"goal.md"; prompt.write_text("fixed\n",encoding="utf-8"); goal.write_text("goal\n",encoding="utf-8"); contract=self.root/"contract.md"; contract.write_text("fixed\n",encoding="utf-8"); registered=register_contract(project,contract,sha_text("fixed\n"),"v1",run); expected={"project_id":"project-0001","contract_version":"v1","contract_sha":sha_text("fixed\n"),"run_id":"run-1","prompt_name":"prompt.md","prompt_sha":sha_file(prompt),"goal_name":"goal.md","goal_sha":sha_file(goal)}; result=classify(version=2,goal_status="active",project_directory=project,expected=expected); self.assertEqual(("registered_preparing_recovery","registered_before_launcher"),(result["startup_class"],result["preparing_phase"])); (run/"extra").write_text("x",encoding="utf-8"); blocked=classify(version=2,goal_status="active",project_directory=project,expected=expected); self.assertEqual(("recovery_only","prelauncher_directory_must_contain_only_prompt_and_goal"),(blocked["startup_class"],blocked["recovery_reason"]))
    def test_legacy_migration_routes_structurally(self):
        project=self.project("legacy",True); before=sha_file(project/"project.json"); result=classify(version=2,goal_status="none",project_directory=project); self.assertEqual(("first_legacy_migration","StructuralOnly",1),(result["startup_class"],result["controller_action"],result["controller_call_count"])); self.assertEqual(before,sha_file(project/"project.json"))

if __name__=="__main__":unittest.main()
