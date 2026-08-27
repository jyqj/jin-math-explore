#!/usr/bin/env python3
"""Native cross-platform launcher primitives and Prompt v4-v7 contract parser."""

from __future__ import annotations
import hashlib, hmac, json, math, os, platform, re, secrets, shlex, shutil, subprocess, sys, tempfile, time
from pathlib import Path
from typing import Any

from MathResearchApproveForMeArgvCompatV2 import new_features_arguments, new_global_arguments, toml_basic_string
from math_research_control_primitives import FileLease, assert_no_symlink_chain, canonical_json, read_signed_json, strict_json_loads, write_signed_json
from math_research_process_identity import snapshot_process as capture_process_identity, process_identity_matches


class LauncherError(RuntimeError): pass
def require(value: bool, message: str) -> None:
    if not value: raise LauncherError(message)
def sha_bytes(value: bytes) -> str: return hashlib.sha256(value).hexdigest()
def sha_text(value: str) -> str: return sha_bytes(value.encode("utf-8"))
def sha_file(path: Path) -> str: return sha_bytes(path.read_bytes())
def fixed_equal(left: str,right: str) -> bool: return hmac.compare_digest(left,right)
def agent_stages(max_child_agents: int) -> list[int]: require(1<=max_child_agents<=16,"child cap is invalid"); return sorted(set((min(4,max_child_agents),min(8,max_child_agents),min(12,max_child_agents),max_child_agents)))


def sanitized_environment() -> dict[str,str]:
    blocked=("OPENAI_API_KEY","OPENAI_BASE_URL","AZURE_OPENAI_API_KEY","HTTP_PROXY","HTTPS_PROXY","ALL_PROXY","NO_PROXY","CODEX_API_KEY","CODEX_HOME")
    environment={key:value for key,value in os.environ.items() if key.upper() not in blocked and not key.upper().endswith(("_TOKEN","_SECRET","_PASSWORD"))}; environment.update({"PYTHONUTF8":"1","PYTHONIOENCODING":"utf-8"}); return environment


def research_run_context(run_directory: Path, operation: str) -> dict[str,Any]:
    require(operation in {"New","Resume"},"operation is invalid"); run=assert_no_symlink_chain(run_directory); require(run.is_dir(),"run directory is missing")
    if run.parent.name=="runs" and (run.parent.parent/"project.json").is_file():
        project=read_json_file(run.parent.parent/"project.json"); require(project.get("project_directory_name")==run.parent.parent.name,"project directory identity mismatches"); return {"Layout":"project","RunDirectory":str(run),"RunId":run.name,"ProjectDirectory":str(run.parent.parent),"ProjectId":project["project_id"],"ProjectDirectoryName":project["project_directory_name"],"ProjectArchiveSchema":project["schema"]}
    require(operation=="Resume","legacy root is Resume-only"); require("history" not in {x.casefold() for x in run.parts},"historical copied run is not active"); return {"Layout":"legacy","RunDirectory":str(run),"RunId":run.name}


def resolve_run_input(path: Path, run_directory: Path) -> Path:
    value=assert_no_symlink_chain(path); run=assert_no_symlink_chain(run_directory); require(value.is_file(),"run input is missing")
    try: value.relative_to(run)
    except ValueError: raise LauncherError("run input is outside run directory")
    return value


def assert_fresh_run(run_directory: Path, allowed: list[Path]) -> bool:
    run=assert_no_symlink_chain(run_directory); allowed_set={x.resolve() for x in allowed}; unexpected=[]
    for item in run.iterdir():
        if item.resolve() not in allowed_set: unexpected.append(item.name)
    require(not unexpected,"fresh run directory contains unexpected entries: "+", ".join(unexpected)); return True


def read_json_file(path: Path) -> dict[str,Any]:
    value=strict_json_loads(assert_no_symlink_chain(path).read_text(encoding="utf-8",errors="strict")); require(isinstance(value,dict),"JSON root must be object"); return value


def _json_block(prompt: str,name: str) -> str:
    tag=f"<!-- {name}"; pattern=re.compile(re.escape(f"<!-- {name}\n")+r"(?P<body>.*?)"+re.escape("\n-->"),re.S); matches=list(pattern.finditer(prompt)); require(prompt.count(tag)==1 and len(matches)==1,f"prompt requires exactly one {name} JSON block"); body=matches[0].group("body"); require(bool(body.strip()),"prompt JSON block is empty"); strict_json_loads(body); return body


V4_KEYS=("schema","contract_version","model","reasoning_effort","web_search","total_round_budget","attempt_budget","audit_interval_attempts","max_child_agents","max_total_agents","max_runtime_minutes","goal_objective_sha256","cycle_policy_sha256","initial_tickets_sha256")
V4_HEADINGS=("## Launch intent","## Goal continuity and bootstrap gate","## Immutable Research Contract {contract_version}","## State, events, and budget gate","## Research execution","## Three-role audit","## Sources, computation, and isolation","## Pause, Resume, and return")
V4_SENTINELS=("Before every substantive mathematical attempt, register ATTEMPT_START","attempts_since_last_audit == audit_interval_attempts","global `attempt_count` never resets.","Spawn exactly `skeptic_quantifiers`, `skeptic_strategy`, and `theory_tool_scout`","They inspect only existing evidence","Completion requires all three PASS on the same frozen completion candidate","Resume only the signed run with the pinned thread/executable and same contract","A pending audit remains first after Resume.","Never silently amend the theorem or contract.")
V6_SENTINELS=("有可靠的开放路线时，从档案中选择一条与近期失败路线原理不同的路线继续。","没有可用路线时，登记一次范围明确、停止条件明确的路线发现尝试。","每次尝试只回答一个已经冻结的数学问题。","只要结局声称产生数学结论，就必须由另一份核验报告逐步检查最终候选。","每次尝试最多使用一次预先登记的定向修订；修订后的版本必须重新核验。","如果需要新的引理、桥梁或跨路线综合，必须另行登记 ATTEMPT_START。","审计只能整理既有路线卡，不能现场发明路线或补证明。")


def _metadata(prompt: str,version: int) -> tuple[str,dict[str,str],re.Match[str]]:
    normalized=prompt.replace("\r\n","\n"); require("\r" not in normalized,f"Prompt v{version} contains isolated CR"); match=re.match(rf"\A# Math Research Orchestration Prompt v{version}\n<!-- math-research-launcher\n(?P<body>.*?)\n-->\n",normalized,re.S); require(match is not None,f"New mode accepts only Prompt v{version} metadata"); values={}
    for line in match.group("body").splitlines():
        item=re.fullmatch(r"(?P<key>[a-z][a-z0-9_]*):\s*(?P<value>\S(?:.*\S)?)",line); require(item is not None,f"invalid metadata line: {line}"); key=item.group("key"); require(key not in values,f"duplicate metadata key: {key}"); values[key]=item.group("value")
    return normalized,values,match


def parse_prompt_v4(prompt: str) -> dict[str,Any]:
    normalized,raw,_=_metadata(prompt,4); require(set(raw)==set(V4_KEYS),"Prompt v4 metadata keys are incomplete or unknown"); require(raw["schema"]=="4" and re.fullmatch(r"v[1-9]\d*",raw["contract_version"]) is not None,"Prompt v4 schema/contract is invalid"); require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}",raw["model"]) is not None and raw["reasoning_effort"] in {"minimal","low","medium","high","xhigh","max","ultra"} and raw["web_search"] in {"allowed","denied"},"model, effort, or search metadata is invalid")
    for key in ("goal_objective_sha256","cycle_policy_sha256","initial_tickets_sha256"): require(re.fullmatch(r"[0-9a-f]{64}",raw[key]) is not None,f"{key} is invalid")
    values:dict[str,Any]=dict(raw)
    for key in ("total_round_budget","attempt_budget","audit_interval_attempts","max_child_agents","max_total_agents","max_runtime_minutes"):
        try: values[key]=int(raw[key])
        except ValueError as exc: raise LauncherError(f"{key} must be integer") from exc
    require(values["total_round_budget"]>=1 and 1<=values["attempt_budget"]<=values["total_round_budget"] and values["audit_interval_attempts"]>=1,"cycle budgets are invalid"); require(values["total_round_budget"]>=values["attempt_budget"]+math.ceil(values["attempt_budget"]/values["audit_interval_attempts"]),"total budget cannot accommodate audits"); require(1<=values["max_child_agents"]<=16 and values["max_total_agents"]==values["max_child_agents"]+1 and values["max_runtime_minutes"]>=0,"agent/runtime envelope is invalid")
    policy=_json_block(normalized,"math-research-cycle-policy"); tickets=_json_block(normalized,"math-research-initial-tickets"); require(fixed_equal(sha_text(policy),values["cycle_policy_sha256"]) and fixed_equal(sha_text(tickets),values["initial_tickets_sha256"]),"machine block hash mismatches"); values.update({"cycle_policy_json":policy,"initial_tickets_json":tickets})
    for heading in V4_HEADINGS: require(len(re.findall(rf"(?m)^{re.escape(heading.format(**values))}\s*$",normalized))==1,f"required heading differs: {heading}")
    for sentinel in V4_SENTINELS: require(normalized.count(sentinel)==1,f"required collaboration rule differs: {sentinel}")
    return values


def project_identity_sha256(schema: int,project_id: str,directory_name: str) -> str: return sha_text(canonical_json({"project_archive_schema":schema,"project_id":project_id,"project_directory_name":directory_name}))


def _downgrade_prompt(normalized: str,match: re.Match[str],from_version: int,to_version: int,drop: set[str]=set()) -> str:
    lines=[]
    for line in match.group("body").splitlines():
        key=line.split(":",1)[0]
        if key in drop: continue
        lines.append(f"schema: {to_version}" if key=="schema" else line)
    prefix=f"# Math Research Orchestration Prompt v{to_version}"+normalized[len(f"# Math Research Orchestration Prompt v{from_version}"):]
    start=match.start("body"); end=match.end("body"); return prefix[:start]+"\n".join(lines)+prefix[end:]


def parse_prompt_v5(prompt: str) -> dict[str,Any]:
    normalized,raw,match=_metadata(prompt,5); keys={"project_archive_schema","project_id","project_directory_name","project_identity_sha256"}; require(keys<=set(raw),"Prompt v5 project keys are missing"); schema=int(raw["project_archive_schema"]); require(schema>=1 and re.fullmatch(r"[a-z0-9][a-z0-9._-]{7,127}",raw["project_id"]) and not re.search(r'[<>:"/\\|?*]',raw["project_directory_name"]),"project identity is unsafe"); require(raw["project_identity_sha256"]==project_identity_sha256(schema,raw["project_id"],raw["project_directory_name"]),"project identity hash mismatches"); base=parse_prompt_v4(_downgrade_prompt(normalized,match,5,4,keys)); base.update({"schema":5,"project_archive_schema":schema,"project_id":raw["project_id"],"project_directory_name":raw["project_directory_name"],"project_identity_sha256":raw["project_identity_sha256"]}); return base


def parse_prompt_v6(prompt: str) -> dict[str,Any]:
    normalized,raw,match=_metadata(prompt,6); require(raw.get("schema")=="6","Prompt v6 schema is invalid"); base=parse_prompt_v5(_downgrade_prompt(normalized,match,6,5)); policy=strict_json_loads(base["cycle_policy_json"]); tickets=strict_json_loads(base["initial_tickets_json"]); require(policy.get("schema_version")==3 and policy.get("protocol")=="math-research-cycle-policy/v3" and tickets.get("schema_version")==3,"Prompt v6 requires machine schema 3"); require(all(x.get("attempt_kind") in {"route_discovery","route_execution","candidate_revision","candidate_synthesis"} for x in tickets.get("tickets",[])),"Prompt v6 ticket kind is invalid"); [require(normalized.count(x)==1,f"Prompt v6 rule differs: {x}") for x in V6_SENTINELS]; base["schema"]=6; return base


def parse_prompt_v7(prompt: str) -> dict[str,Any]:
    normalized,raw,match=_metadata(prompt,7); require(raw.get("schema")=="7" and raw.get("approval_mode") in {"approve_for_me","never"},"Prompt v7 approval authority is missing or invalid"); base=parse_prompt_v6(_downgrade_prompt(normalized,match,7,6,{"approval_mode"})); base.update({"schema":7,"approval_mode":raw["approval_mode"]}); return base


def assert_metadata(metadata:dict[str,Any],*,max_child_agents:int,model:str,reasoning_effort:str,approval_mode:str,max_runtime_minutes:int,goal_objective_sha256:str,run_context:dict[str,Any]|None=None)->bool:
    require(metadata["max_child_agents"]==max_child_agents and metadata["max_total_agents"]==max_child_agents+1,"agent cap mismatches"); require(metadata["model"]==model and metadata["reasoning_effort"]==reasoning_effort and metadata.get("approval_mode")==approval_mode,"model/effort/approval mismatches"); require(metadata["max_runtime_minutes"]==max_runtime_minutes and metadata["goal_objective_sha256"]==goal_objective_sha256,"runtime/objective mismatches")
    if run_context is not None: require(run_context["Layout"]=="project" and metadata["project_archive_schema"]==run_context["ProjectArchiveSchema"] and metadata["project_id"]==run_context["ProjectId"] and metadata["project_directory_name"]==run_context["ProjectDirectoryName"] and metadata["project_identity_sha256"]==project_identity_sha256(run_context["ProjectArchiveSchema"],run_context["ProjectId"],run_context["ProjectDirectoryName"]),"live project identity mismatches")
    return True


def feature_preflight_output(text: str) -> bool:
    for name in ("goals","multi_agent"): require(re.search(rf"(?m)^{name}\s+\S+\s+true\s*$",text) is not None,f"feature {name} is not enabled")
    require(re.search(r"(?m)^multi_agent_v2\s+\S+\s+true\s*$",text) is None,"multi_agent_v2 must be disabled"); return True


def read_codex_json_log(path: Path,expected_thread_id: str|None=None) -> dict[str,Any]:
    ids=[]; last=None; terminal=None; terminal_count=0; top=[]; item_errors=[]; unknown=set(); usage={key:0 for key in ("input_tokens","cached_input_tokens","output_tokens","reasoning_output_tokens")}; known={"thread.started","turn.started","item.started","item.updated","item.completed","turn.completed","turn.failed","error"}
    for number,line in enumerate(path.read_text(encoding="utf-8",errors="strict").splitlines(),1):
        require(len(line)<=10*1024*1024,f"JSONL line {number} exceeds 10 MiB")
        if not line.strip(): continue
        try: event=strict_json_loads(line)
        except Exception as exc: raise LauncherError(f"invalid JSONL line {number}") from exc
        kind=event.get("type")
        if kind=="thread.started":
            identity=event.get("thread_id",""); require(re.fullmatch(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}",identity) is not None,"thread id is not UUID"); ids.append(identity.casefold())
        elif kind=="item.completed":
            item=event.get("item",{}); last=item.get("text") if item.get("type")=="agent_message" else last
            if item.get("type")=="error": item_errors.append(str(item.get("message","")))
        elif kind in {"turn.completed","turn.failed"}:
            terminal=kind; terminal_count+=1
            if kind=="turn.completed":
                for key in usage: usage[key]+=int(event.get("usage",{}).get(key) or 0)
        elif kind=="error": top.append(compact_json(event))
        elif kind and kind not in known: unknown.add(kind)
    require(len(ids)==1,"JSONL requires exactly one thread.started"); require(expected_thread_id is None or ids[0]==expected_thread_id.casefold(),"resume thread id mismatches"); require(terminal_count==1 and terminal in {"turn.completed","turn.failed"},"JSONL requires exactly one terminal event")
    return {"ThreadId":ids[0],"LastAgentMessage":last,"TerminalType":terminal,"TerminalCount":terminal_count,"TopLevelErrors":top,"ItemErrors":item_errors,"UnknownTypes":sorted(unknown),"Usage":usage}


def compact_json(value: Any) -> str: return json.dumps(value,ensure_ascii=False,separators=(",",":"))


def goal_output_schema(objective_sha256: str,nonce: str) -> dict[str,Any]: return {"type":"object","additionalProperties":False,"required":["marker","nonce","objective_sha256","observed_status"],"properties":{"marker":{"type":"string","enum":["MATH_RESEARCH_GOAL_READY","MATH_RESEARCH_GOAL_FAILED"]},"nonce":{"type":"string","enum":[nonce]},"objective_sha256":{"type":"string","enum":[objective_sha256]},"observed_status":{"type":"string"}}}


def goal_ready_marker(message: str,objective_sha256: str,nonce: str) -> dict[str,Any]:
    try: value=strict_json_loads(message)
    except Exception as exc: raise LauncherError("Goal marker is not strict JSON") from exc
    require(isinstance(value,dict) and set(value)=={"marker","nonce","objective_sha256","observed_status"} and value["marker"]=="MATH_RESEARCH_GOAL_READY" and value["nonce"]==nonce and value["objective_sha256"]==objective_sha256 and value["observed_status"]=="active","Goal bootstrap marker differs"); return value


def goal_bootstrap_prompt(objective: str,objective_sha256: str,nonce: str) -> str:
    return f"""# Goal Mode bootstrap

This turn establishes a durable Goal and performs no mathematical research.

1. Call `create_goal` with exactly the objective encoded in the JSON string below.
2. Do not pass `token_budget`.
3. Call `get_goal` after creation.
4. Return ready only when the objective is identical and status is active.
5. Stop after the JSON response.

Objective JSON string:

```json
{compact_json(objective)}
```

- nonce: `{nonce}`
- objective_sha256: `{objective_sha256}`
"""


def assert_continuation(text: str,sha256: str,original_prompt_sha256: str) -> bool:
    require(sha_text(text)==sha256,"continuation instruction hash mismatches"); require(original_prompt_sha256 in text,"continuation instruction omits original prompt binding"); forbidden=("amend the objective","change the theorem","reset attempt_count"); require(not any(x in text.casefold() for x in forbidden),"continuation attempts to amend frozen authority"); return True


def executable_attestation(path: Path,trusted_root: Path|None=None) -> dict[str,Any]:
    executable=assert_no_symlink_chain(path); require(executable.is_file(),"Codex executable is missing")
    if trusted_root is not None:
        root=assert_no_symlink_chain(trusted_root); require(executable.parent.resolve()==root.resolve(),"executable is outside trusted root")
    if os.name!="nt":
        metadata=executable.stat(); require(metadata.st_uid in {os.getuid(),0} and metadata.st_mode&0o022==0,"executable ownership or write permissions are unsafe"); require(os.access(executable,os.X_OK),"executable is not executable")
    completed=subprocess.run([str(executable),"--version"],capture_output=True,text=True,env=sanitized_environment(),timeout=10); require(completed.returncode==0,"Codex version probe failed"); version=(completed.stdout or completed.stderr).strip(); match=re.search(r"\d+\.\d+(?:\.\d+)?",version); require(match is not None,"Codex semantic version is absent")
    return {"path":str(executable.resolve()),"sha256":sha_file(executable),"version":match.group(0),"size":metadata.st_size if os.name!="nt" else executable.stat().st_size,"platform":sys.platform}


def assert_attestation(attestation: dict[str,Any]) -> bool:
    path=assert_no_symlink_chain(Path(attestation["path"])); require(path.is_file() and sha_file(path)==attestation["sha256"] and path.stat().st_size==attestation["size"],"executable attestation changed"); return True


def select_codex_executable(candidates: list[Path]|None=None,trusted_root: Path|None=None) -> dict[str,Any]:
    values=candidates or ([Path(found)] if (found:=shutil.which("codex")) else []); attestations=[]
    for item in values:
        try: attestations.append(executable_attestation(item,trusted_root))
        except (LauncherError,OSError,subprocess.SubprocessError): continue
    require(bool(attestations),"no trusted Codex executable found"); return sorted(attestations,key=lambda x:tuple(int(y) for y in x["version"].split(".")),reverse=True)[0]


def run_attested(attestation:dict[str,Any],arguments:list[str],working_directory:Path,standard_input:str,stdout_path:Path,stderr_path:Path,timeout_seconds:float)->dict[str,Any]:
    assert_attestation(attestation); environment=sanitized_environment(); flags=0 if os.name!="nt" else getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0)
    with stdout_path.open("wb") as stdout,stderr_path.open("wb") as stderr:
        process=subprocess.Popen([attestation["path"],*arguments],cwd=working_directory,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,env=environment,start_new_session=os.name!="nt",creationflags=flags); identity=capture_process_identity(process.pid)
        try: process.communicate(standard_input.encode("utf-8"),timeout=timeout_seconds); timed_out=False
        except subprocess.TimeoutExpired:
            timed_out=True
            if os.name!="nt": import signal; os.killpg(process.pid,signal.SIGKILL)
            else: process.kill()
            process.wait(timeout=10)
    return {"ExitCode":process.returncode,"TimedOut":timed_out,"ProcessId":process.pid,"Identity":identity,"TerminationScope":{"kind":"posix-process-group","id":process.pid} if os.name!="nt" else {"kind":"windows-process-group","id":process.pid}}


def codex_global_arguments(*,run_directory:Path,model:str,reasoning_effort:str,sandbox:str,approval_mode:str,allow_web_search:bool,enable_multi_agent:bool,max_child_agents:int=1)->list[str]:
    require(sandbox in {"read-only","workspace-write"} and approval_mode in {"approve_for_me","never"} and 1<=max_child_agents<=16,"Codex execution envelope is invalid"); require(approval_mode!="approve_for_me" or sandbox=="workspace-write","approve_for_me requires workspace-write")
    result=["--strict-config","-C",str(run_directory),"-m",model,"-s",sandbox]
    result += ["--approve-for-me"] if approval_mode=="approve_for_me" else ["-a","never"]
    result += ["-c",f"model_reasoning_effort={toml_basic_string(reasoning_effort)}","-c","sandbox_workspace_write.network_access=false","--enable","goals","--disable","plugins","--disable","apps","--disable","enable_mcp_apps","--disable","multi_agent_v2"]
    result += ["--enable","multi_agent","-c",f"agents.max_threads={max_child_agents}"] if enable_multi_agent else ["--disable","multi_agent"]
    if allow_web_search: result.append("--search")
    return result


def codex_exec_arguments(*,run_directory:Path,model:str,reasoning_effort:str,sandbox:str,approval_mode:str,allow_web_search:bool,enable_multi_agent:bool,max_child_agents:int,last_message_path:Path,output_schema_path:Path|None=None,resume_thread_id:str|None=None,ephemeral:bool=False)->list[str]:
    result=codex_global_arguments(run_directory=run_directory,model=model,reasoning_effort=reasoning_effort,sandbox=sandbox,approval_mode=approval_mode,allow_web_search=allow_web_search,enable_multi_agent=enable_multi_agent,max_child_agents=max_child_agents)+["exec"]
    if ephemeral: result.append("--ephemeral")
    result += ["--color","never"]
    if resume_thread_id:
        require(re.fullmatch(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}",resume_thread_id) is not None,"resume thread id is not canonical UUID"); result.append("resume")
    result += ["--ignore-user-config","--json","--skip-git-repo-check","-o",str(last_message_path)]
    if output_schema_path: result += ["--output-schema",str(output_schema_path)]
    if resume_thread_id: result += ["--",resume_thread_id.casefold()]
    result.append("-"); return result


def execution_rules_fingerprint(run_directory: Path) -> dict[str,Any]:
    directories={Path.home()/".codex/rules"}; cursor=run_directory.resolve()
    while True:
        directories.add(cursor/".codex/rules")
        if cursor.parent==cursor: break
        cursor=cursor.parent
    files=[]
    for directory in sorted(directories,key=str):
        if not directory.is_dir(): continue
        assert_no_symlink_chain(directory)
        for path in sorted(directory.glob("*.rules"),key=str): assert_no_symlink_chain(path); files.append({"path":str(path.resolve()),"bytes":path.stat().st_size,"sha256":sha_file(path)})
    payload={"schema_version":2,"discovery":"codex_home_rules_plus_run_ancestor_project_rules","files":files}; return {"Payload":payload,"Sha256":sha_text(canonical_json(payload))}


def canary_binding(*,attestation:dict[str,Any],run_directory:Path,launcher_entry_path:Path,launcher_module_path:Path,canary_entry_path:Path,cycle_cli_path:Path,approval_mode:str,model:str,reasoning_effort:str,web_search:str,max_child_agents:int,rules_fingerprint:dict[str,Any])->dict[str,Any]:
    paths=(launcher_entry_path,launcher_module_path,canary_entry_path,cycle_cli_path)
    for path in paths: require(assert_no_symlink_chain(path).is_file(),f"canary binding file is missing: {path}")
    payload={"schema_version":2,"protocol":"math-research-launcher-canary/v2","run_directory":str(run_directory.resolve()),"executable":{"path":attestation["path"],"sha256":attestation["sha256"],"version":attestation["version"],"platform":attestation.get("platform")},"launcher":{"entry_path":str(launcher_entry_path.resolve()),"entry_sha256":sha_file(launcher_entry_path),"module_path":str(launcher_module_path.resolve()),"module_sha256":sha_file(launcher_module_path)},"canary_entry":{"path":str(canary_entry_path.resolve()),"sha256":sha_file(canary_entry_path)},"cycle_cli":{"path":str(cycle_cli_path.resolve()),"sha256":sha_file(cycle_cli_path),"action":"Status"},"policy":{"approval_mode":approval_mode,"sandbox":"workspace-write","rules_fingerprint_sha256":rules_fingerprint["Sha256"],"ignore_user_config":True,"ignore_rules":False,"plugins_apps_mcp_disabled":True,"shell_network_access":False,"ephemeral_session":True},"canary_execution":{"model":model,"reasoning_effort":"low","web_search":"denied","multi_agent_enabled":False,"max_child_agents":1},"research_envelope":{"reasoning_effort":reasoning_effort,"web_search":web_search,"max_child_agents":max_child_agents},"boundary":{"user_scope":str(os.getuid()) if hasattr(os,"getuid") else os.environ.get("USERNAME","unknown"),"machine_name":platform.node(),"platform":sys.platform},"exact_protocol":{"prompt_template":"pinned_native_entry_exact_argv_with_challenge_sha256","challenge_file":"launcher-canary-challenge-v2.json","evidence_file":"launcher-canary-evidence-v2.json","scratch_file":"launcher-canary-scratch-v2.tmp","effects":["read_signed_run_manifest","read_cycle_ledger","invoke_exact_cycle_status","create_read_remove_run_local_scratch"],"consumes_attempts":False,"consumes_rounds":False}}
    return {"Payload":payload,"Sha256":sha_text(canonical_json(payload))}


def assert_bundle_receipt(bundle:dict[str,Any],manifest:dict[str,Any])->bool:
    require(manifest.get("launcher_protocol")=="math-research-launcher/v2" and manifest.get("prompt_version")=="v7","versioned_migration_required: v2 accepts only v2/v7 bundle")
    require(isinstance(manifest.get("cycle_ledger"),dict) and isinstance(manifest.get("launcher_bundle"),dict),"complete launcher bundle is missing")
    items=(("ModulePath","ModuleSha256",manifest["cycle_ledger"]["module"]),("CliPath","CliSha256",manifest["cycle_ledger"]["cli"]),("ProjectModulePath","ProjectModuleSha256",manifest["cycle_ledger"]["project_module"]),("ModulePath","ModuleSha256",manifest["launcher_bundle"]["cycle_module"]),("CliPath","CliSha256",manifest["launcher_bundle"]["cycle_cli"]),("ProjectModulePath","ProjectModuleSha256",manifest["launcher_bundle"]["project_module"]),("ProjectCliPath","ProjectCliSha256",manifest["launcher_bundle"]["project_cli"]),("LauncherModulePath","LauncherModuleSha256",manifest["launcher_bundle"]["launcher_module"]),("LauncherEntryPath","LauncherEntrySha256",manifest["launcher_bundle"]["launcher_entry"]),("CanaryEntryPath","CanaryEntrySha256",manifest["launcher_bundle"]["canary_entry"]),("StopCliPath","StopCliSha256",manifest["launcher_bundle"]["stop_cli"]))
    for path_key,hash_key,binding in items: require(Path(bundle[path_key]).resolve()==Path(binding["path"]).resolve(),f"bundle {path_key} path differs"); require(fixed_equal(bundle[hash_key],binding["sha256"]),f"bundle {hash_key} SHA-256 differs")
    return True


def launcher_canary_prompt(canary_entry:Path,run_directory:Path,challenge_file:Path,challenge_sha256:str)->str:
    argv=[sys.executable,"-B",str(canary_entry),"--run-directory",str(run_directory),"--challenge-file",str(challenge_file),"--expected-challenge-sha256",challenge_sha256]
    command=subprocess.list2cmdline(argv) if os.name=="nt" else shlex.join(argv)
    return f"""# Math Research Launcher control-path canary v2

This is a pre-launch control-path test, not mathematical research. Run exactly this one native command from the current run directory:

`{command}`

Do not start or end an attempt or audit. Do not modify any other file. The pinned canary entry must read the signed run state, invoke the exact cycle controller Status action, create/read/remove the fixed run-local scratch artifact, and write the fixed evidence file. If it succeeds, return exactly {{\"marker\":\"MATH_RESEARCH_LAUNCHER_CANARY_V2_OK\"}}.
"""


def invoke_launcher_canary(*,attestation:dict[str,Any],run_directory:Path,manifest_path:Path,launcher_entry_path:Path,launcher_module_path:Path,canary_entry_path:Path,cycle_cli_path:Path,approval_mode:str,model:str,reasoning_effort:str,web_search:str,max_child_agents:int,invoker=None)->dict[str,Any]:
    run=assert_no_symlink_chain(run_directory); require(run.is_dir(),"run directory is missing"); manifest=assert_no_symlink_chain(manifest_path); require(manifest.parent.resolve()==run.resolve(),"manifest must be run-local")
    rules=execution_rules_fingerprint(run); binding=canary_binding(attestation=attestation,run_directory=run,launcher_entry_path=launcher_entry_path,launcher_module_path=launcher_module_path,canary_entry_path=canary_entry_path,cycle_cli_path=cycle_cli_path,approval_mode=approval_mode,model=model,reasoning_effort=reasoning_effort,web_search=web_search,max_child_agents=max_child_agents,rules_fingerprint=rules); receipt=run/"launcher-canary-v2.json"
    if receipt.is_file():
        try:
            existing=read_signed_json(receipt); payload=existing["payload"]
            if not existing["recovered_from_backup"] and payload.get("schema_version")==2 and payload.get("protocol")=="math-research-launcher-canary/v2" and payload.get("status")=="passed" and fixed_equal(str(payload.get("binding_sha256","")),binding["Sha256"]):
                return {"Passed":True,"Reused":True,"ReceiptPath":str(receipt),"BindingSha256":binding["Sha256"]}
        except Exception: pass
    names=("launcher-canary-challenge-v2.json","launcher-canary-evidence-v2.json","launcher-canary-events-v2.jsonl","launcher-canary-stderr-v2.log","launcher-canary-last-message-v2.json","launcher-canary-scratch-v2.tmp")
    for name in names: (run/name).unlink(missing_ok=True)
    nonce=secrets.token_hex(32); manifest_sha=sha_file(manifest); challenge_path=run/names[0]; evidence_path=run/names[1]; events_path=run/names[2]; stderr_path=run/names[3]; last_path=run/names[4]
    challenge={"schema_version":2,"protocol":"math-research-launcher-canary/v2","nonce":nonce,"run_directory":str(run.resolve()),"manifest_path":str(manifest.resolve()),"manifest_sha256":manifest_sha,"canary_entry_path":str(canary_entry_path.resolve()),"canary_entry_sha256":sha_file(canary_entry_path),"cycle_cli_path":str(cycle_cli_path.resolve()),"cycle_cli_sha256":sha_file(cycle_cli_path)}
    try:
        challenge_path.write_text(json.dumps(challenge,ensure_ascii=False,indent=2),encoding="utf-8"); require(read_json_file(challenge_path)["nonce"]==nonce,"challenge write verification failed"); challenge_sha=sha_file(challenge_path)
        arguments=codex_exec_arguments(run_directory=run,model=model,reasoning_effort="low",sandbox="workspace-write",approval_mode=approval_mode,allow_web_search=False,enable_multi_agent=False,max_child_agents=1,last_message_path=last_path,ephemeral=True)
        context={"Attestation":attestation,"Arguments":arguments,"WorkingDirectory":run,"PromptText":launcher_canary_prompt(canary_entry_path,run,challenge_path,challenge_sha),"StdoutPath":events_path,"StderrPath":stderr_path,"LastMessagePath":last_path,"EvidencePath":evidence_path,"Challenge":challenge,"Binding":binding["Payload"]}
        result=invoker(context) if invoker else run_attested(attestation,arguments,run,context["PromptText"],events_path,stderr_path,600)
        require(result is not None and not result.get("TimedOut") and not result.get("OutputLimitExceeded") and int(result.get("ExitCode",-1))==0,"mandatory launcher canary failed")
        events=read_codex_json_log(events_path); require(events["TerminalType"]=="turn.completed","canary did not complete one turn"); require(read_json_file(last_path).get("marker")=="MATH_RESEARCH_LAUNCHER_CANARY_V2_OK","canary marker mismatches"); evidence=read_json_file(evidence_path)
        hashes=(evidence.get("run_manifest_sha256"),evidence.get("ledger_before_sha256"),evidence.get("ledger_after_sha256"),evidence.get("cycle_status_sha256")); require(all(isinstance(x,str) and re.fullmatch(r"[0-9a-f]{64}",x) for x in hashes),"canary evidence hash is invalid")
        require(evidence.get("protocol")=="math-research-launcher-canary/v2" and evidence.get("challenge_nonce")==nonce and evidence.get("run_manifest_sha256")==manifest_sha and evidence.get("ledger_before_sha256")==evidence.get("ledger_after_sha256") and evidence.get("cycle_status_exit_code")==0 and evidence.get("scratch_created") is True and evidence.get("scratch_removed") is True and not (run/names[5]).exists(),"canary evidence failed verification")
        require(sha_file(manifest)==manifest_sha and sha_file(challenge_path)==challenge_sha and sha_file(canary_entry_path)==binding["Payload"]["canary_entry"]["sha256"],"canary binding changed during execution"); require(execution_rules_fingerprint(run)["Sha256"]==rules["Sha256"],"execution rules changed during canary")
        if invoker is None: assert_attestation(attestation)
        evidence_text=evidence_path.read_text(encoding="utf-8"); payload={"schema_version":2,"protocol":"math-research-launcher-canary/v2","status":"passed","binding":binding["Payload"],"binding_sha256":binding["Sha256"],"completed_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"result":{"challenge_sha256":challenge_sha,"evidence_sha256":sha_text(evidence_text),"events_sha256":sha_file(events_path),"stderr_sha256":sha_file(stderr_path),"last_message_sha256":sha_file(last_path),"attempt_count":int(evidence["attempt_count"]),"total_round_count":int(evidence["total_round_count"])},"assurance":"proves_this_frozen_control_path_only_not_future_auto_review_decisions"}; write_signed_json(receipt,payload)
        return {"Passed":True,"Reused":False,"ReceiptPath":str(receipt),"BindingSha256":binding["Sha256"]}
    finally:
        for name in names: (run/name).unlink(missing_ok=True)
