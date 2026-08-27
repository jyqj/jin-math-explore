#!/usr/bin/env python3
import hashlib, json, tempfile, unittest
from pathlib import Path
from math_research_startup_v3 import classify
from math_research_state_v10 import sha_file

def write(path:Path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,separators=(",",":")),encoding="utf-8")
def ptr(root:Path,rel:str,generation=True):
    value={"path":rel,"sha256":sha_file(root/rel)}
    if generation:value["control_generation"]=1
    return value

class StartupV3NativeTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def fixture(self,status="preparing",completion=False):
        root=self.root/"project"; root.mkdir(); contract_rel="contracts/c.md"; contract=root/contract_rel; contract.parent.mkdir(); policy={"schema_version":3,"protocol":"math-research-cycle-policy/v3","total_round_budget":4,"attempt_budget":3,"audit_interval_attempts":2,"max_route_family_attempts_per_cycle":2,"max_repair_batches_per_attempt":1,"allowed_worker_tools":["apply_patch"],"max_ticket_tool_calls":10,"max_ticket_output_bytes":1000,"audit_roles":["skeptic_quantifiers","skeptic_strategy","theory_tool_scout"]}; contract_text="<!-- math-research-cycle-policy\n"+json.dumps(policy,separators=(",",":"))+"\n-->\n"; contract.write_text(contract_text,encoding="utf-8"); contract_pointer={"path":contract_rel,"version":"v8","binding_sha256":hashlib.sha256(contract_text.encode()).hexdigest()}; run={"id":"run-1","path":"runs/run-1","status":status}; (root/"runs/run-1").mkdir(parents=True); counters={"attempt_count":0,"audit_count":0,"total_round_count":0,"attempts_since_last_audit":0,"audit_due":False}; host={"thread_id_available":False,"thread_id":None,"objective_raw_sha256":"a"*64}; lifecycle=None; ticket=None
        if not completion:
            ticket_rel="runs/run-1/tickets/t1.json"; write(root/ticket_rel,{"ticket":"t1"}); ticket={"id":"t1","path":ticket_rel,"sha256":sha_file(root/ticket_rel),"status":"ready","contract_initial_tickets_sha256":"b"*64,"counter_snapshot":{"attempt_count":0,"audit_count":0,"total_round_count":0},"source_event":None}; lifecycle={"kind":"initial_ticket","id":"t1","path":ticket_rel,"sha256":ticket["sha256"]}
        event_rel="state/project-events/g0001.json"; write(root/event_rel,{"schema":"event","referenced_artifacts":[]}); checkpoint_rel="state/generations/g0001/checkpoint.json"; checkpoint={"schema":"math-research-checkpoint/v8","project_id":"project-1","control_generation":1,"contract":contract_pointer,"run":run,"problem_statement_sha256":"c"*64,"host_goal":host,"host_binding_head":{"path":"runs/run-1/host.json","sha256":"d"*64,"control_generation":1},"counters":counters,"current_lifecycle":lifecycle,"successor":None,"completion_ready":completion,"pending_goal_update":completion,"last_run_event":None,"updated_at_utc":"2030-01-01T00:00:00Z"}; write(root/checkpoint_rel,checkpoint); state_rel="state/generations/g0001/goal-host-v8.json"; state={"schema":"math-research-goal-host-state/v8","project_id":"project-1","control_generation":1,"contract":contract_pointer,"run":run,"host_goal":host,"problem_statement_sha256":"c"*64,"successor":None,"counters":counters,"current_ticket":ticket,"updated_at_utc":"2030-01-01T00:00:00Z"}; write(root/state_rel,state); head={"schema":"math-research-project/v8","project_id":"project-1","project_identity_sha256":"e"*64,"problem_statement_sha256":"c"*64,"control_generation":1,"active_checkpoint":ptr(root,checkpoint_rel),"goal_host_state":ptr(root,state_rel),"project_event_head":ptr(root,event_rel),"host_binding_head":{"path":"runs/run-1/host.json","sha256":"d"*64,"control_generation":1},"active_contract":contract_pointer,"active_run":run,"legacy_successor":None}; write(root/"project.json",head); return root
    def test_valid_ready_and_goal_gate(self):
        root=self.fixture(); result=classify(project_directory=root,goal_status="active"); self.assertEqual(("goal_host_ready","verify_current_goal_then_begin_model_managed_attempt",True),(result["startup_class"],result["next_action"],result["requires_current_goal_control_check"])); self.assertEqual("research_forbidden_no_current_goal",classify(project_directory=root,goal_status="none")["goal_gate"])
    def test_tamper_fails_closed(self):
        root=self.fixture(); state=root/"state/generations/g0001/goal-host-v8.json"; value=json.loads(state.read_text()); value["counters"]["attempt_count"]=1; write(state,value); result=classify(project_directory=root,goal_status="active"); self.assertEqual(("goal_host_state_invalid","fail_closed_read_only_diagnosis"),(result["startup_class"],result["next_action"]))
    def test_completion_goal_routes(self):
        root=self.fixture("closed",True); active=classify(project_directory=root,goal_status="active"); self.assertEqual("fresh_get_goal_then_update_goal_complete_no_project_write",active["next_action"]); complete=classify(project_directory=root,goal_status="complete"); self.assertEqual(("goal_host_closed_review","durable_completion_closed_read_only"),(complete["startup_class"],complete["goal_gate"]))
    def test_legacy_and_partial_are_read_only(self):
        root=self.root/"legacy"; (root/"state").mkdir(parents=True); write(root/"project.json",{"schema":1,"project_id":"p","active_run":{"id":"old"}}); write(root/"state/checkpoint.json",{"project_id":"p","run":{"id":"old"}}); result=classify(project_directory=root,goal_status="none"); self.assertEqual("legacy_execution_unsupported",result["startup_class"]); vault=self.root/"vault"; (vault/"笔记草稿/公开问题的尝试/partial").mkdir(parents=True); self.assertEqual("partial_project_tree_recovery",classify(vault_root=vault,project_directory_name="partial",goal_status="none")["startup_class"])

if __name__=="__main__":unittest.main()
