#!/usr/bin/env python3
import hashlib,json,tempfile,unittest
from pathlib import Path
from math_research_head_v8 import HeadV8Error,build_legacy_successor,commit_head,sha_file

def put(path:Path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,separators=(",",":"))+"\n" if isinstance(value,dict) else value,encoding="utf-8")

class NativeHeadV8Tests(unittest.TestCase):
    def fixture(self,base:Path)->Path:
        root=base/"legacy";root.mkdir()
        put(root/"contracts"/"legacy.md","# Legacy Contract\n\n## target\nProve the fixed objective.\n")
        put(root/"project.json",{"schema":"math-research-project/v6","project_id":"fixture-project","control_generation":0,
                                 "active_contract":{"path":"contracts/legacy.md","version":"v6"},"active_run":{"id":"legacy-run","path":"runs/legacy-run"}})
        return root
    def test_staging_is_deterministic_and_preserves_old_head(self):
        with tempfile.TemporaryDirectory() as td:
            root=self.fixture(Path(td)); old=sha_file(root/"project.json"); raw="fixed goal"; h=hashlib.sha256(raw.encode()).hexdigest()
            first=build_legacy_successor(root,raw,h); second=build_legacy_successor(root,raw,h)
            self.assertEqual(old,sha_file(root/"project.json"));self.assertEqual(first["candidate_head_sha256"],second["candidate_head_sha256"])
    def test_bad_goal_and_stale_hash_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=self.fixture(Path(td));raw="fixed goal";h=hashlib.sha256(raw.encode()).hexdigest()
            with self.assertRaises(HeadV8Error):build_legacy_successor(root,raw,"0"*64)
            built=build_legacy_successor(root,raw,h)
            with self.assertRaises(HeadV8Error):commit_head(root,Path(built["candidate_head_file"]),"0"*64,"0",1)
    def test_atomic_commit_and_post_commit_chain_validation(self):
        with tempfile.TemporaryDirectory() as td:
            root=self.fixture(Path(td));raw="fixed goal";h=hashlib.sha256(raw.encode()).hexdigest();built=build_legacy_successor(root,raw,h)
            result=commit_head(root,Path(built["candidate_head_file"]),built["expected_old_sha256"],"0",1)
            self.assertTrue(result["committed"]);self.assertEqual(result["new_sha256"],sha_file(root/"project.json"))
            self.assertTrue((root/".project.json.g0000.bak").is_file())
    def test_tampered_pointer_rejected_without_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root=self.fixture(Path(td));raw="fixed goal";h=hashlib.sha256(raw.encode()).hexdigest();built=build_legacy_successor(root,raw,h)
            old=sha_file(root/"project.json"); candidate=Path(built["candidate_head_file"]);value=json.loads(candidate.read_text())
            value["active_checkpoint"]["sha256"]="0"*64;put(candidate,value)
            with self.assertRaises(HeadV8Error):commit_head(root,candidate,old,"0",1)
            self.assertEqual(old,sha_file(root/"project.json"))

if __name__=="__main__":unittest.main()
