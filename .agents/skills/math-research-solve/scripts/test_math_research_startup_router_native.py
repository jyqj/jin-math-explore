#!/usr/bin/env python3
import json,tempfile,unittest
from pathlib import Path
from math_research_startup_router import invoke
class Done:
    returncode=0;stderr=""
    def __init__(self,schema):self.stdout=json.dumps({"ok":True,"data":{"classification":"ready","schema":schema}})
class StartupRouterTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def test_each_exact_schema_uses_native_engine(self):
        for version,target in ((4,9),(5,10),(6,11),(7,12),(8,13)):
            project=self.root/f"p{version}";project.mkdir();(project/"project.json").write_text(json.dumps({"schema":f"math-research-project/v{target}"}),encoding="utf-8");seen=[]
            def runner(argv,**kwargs):seen.append(argv);return Done(target)
            result=invoke(version,project,"Full","active",runner);self.assertEqual(target,result["schema"]);self.assertIn(f"math_research_state_v{target}.py"," ".join(seen[0]));self.assertNotIn("pw" + "sh"," ".join(seen[0]).lower())
    def test_v8_fallback_reaches_v9_router_without_shell(self):
        project=self.root/"legacy";project.mkdir();(project/"project.json").write_text(json.dumps({"schema":"math-research-project/v9"}),encoding="utf-8");seen=[]
        def runner(argv,**kwargs):seen.append(argv);return Done(9)
        result=invoke(8,project,"Auto","none",runner);self.assertEqual(9,result["schema"]);self.assertEqual(1,len(seen))
if __name__=="__main__":unittest.main()
