#!/usr/bin/env python3
"""Generate, validate, and render frozen v13 project-core cognition."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from v13_common import configure_stdio

SCHEMA = "math-research-project-core-cognition/v1"
MAX_BYTES = 24 * 1024
TOKEN_TARGET = 7000
TOKEN_LIMIT = 8192
BUDGET_SCHEMA = "math-research-cognition-budget/v1"
RENDER_PROFILES = ("normal", "compact", "minimal_safe")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
AUTH_PREFIXES = ("memory:", "route-review:", "evidence:", "asset:", "project:", "map-node:")


class CognitionError(ValueError):
    def __init__(self, code: str, path: str, message: str):
        super().__init__(message)
        self.code, self.path, self.message = code, path, message


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, code: str, path: str, message: str) -> None:
    if not condition:
        raise CognitionError(code, path, message)


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def string_list(value: Any, *, nonempty: bool = True) -> bool:
    return isinstance(value, list) and (bool(value) or not nonempty) and all(text(x) for x in value)


def refs(value: Any, *, require_causal_authority: bool = False) -> bool:
    if not string_list(value) or not all(x.startswith(AUTH_PREFIXES) for x in value):
        return False
    return not require_causal_authority or any(x.startswith(("memory:", "route-review:")) for x in value)


def validate(value: Any, *, activation: bool = False) -> dict[str, Any]:
    top = {"schema", "project_id", "project_objective_sha256", "proposed_attempt_id", "window_source_binding", "source_head_sha256", "objective", "source_bindings", "method_orientation", "verified_method_spine", "current_bottleneck", "route_decision", "evidence_boundaries", "retrieval_triggers", "semantic_reset_conditions", "freeze_policy"}
    require(isinstance(value, dict) and set(value) == top, "cognition_fields_invalid", "$", "Cognition uses a closed top-level schema.")
    require(value["schema"] == SCHEMA, "cognition_schema_invalid", "schema", "Expected project-core-cognition/v1.")
    require(text(value["project_id"]), "project_id_invalid", "project_id", "Project ID is required.")
    require(text(value["proposed_attempt_id"]), "attempt_id_invalid", "proposed_attempt_id", "A proposed attempt ID is required before atomic activation.")
    source = value["window_source_binding"]
    require(isinstance(source, dict) and source.get("kind") in {"validated_map", "genesis_objective"}, "window_source_binding_invalid", "window_source_binding", "Expected the closed validated_map/genesis_objective union.")
    genesis = source.get("kind") == "genesis_objective"
    if genesis:
        require(set(source) == {"kind", "objective_commitment_sha256", "consumed"} and source["consumed"] is False and bool(HEX64.fullmatch(str(source["objective_commitment_sha256"]))), "genesis_binding_invalid", "window_source_binding", "Genesis must be unconsumed and bind the objective.")
        require(value["source_head_sha256"] is None, "genesis_source_head_forbidden", "source_head_sha256", "Genesis has no prior research head.")
    else:
        require(set(source) == {"kind", "map_sha256", "validation_receipt_sha256", "research_authority_head_sha256"} and all(bool(HEX64.fullmatch(str(source[k]))) for k in ("map_sha256", "validation_receipt_sha256", "research_authority_head_sha256")), "validated_map_binding_invalid", "window_source_binding", "Validated-map binding is incomplete.")
        require(isinstance(value["source_head_sha256"], str) and bool(HEX64.fullmatch(value["source_head_sha256"])), "hash_invalid", "source_head_sha256", "A source-head SHA-256 is required.")
    require(isinstance(value["project_objective_sha256"], str) and bool(HEX64.fullmatch(value["project_objective_sha256"])), "hash_invalid", "project_objective_sha256", "A lowercase SHA-256 is required.")
    require(text(value["objective"]), "objective_missing", "objective", "The terminal objective must be stated.")

    bindings = value["source_bindings"]
    bkeys = {"map_schema", "map_validation_receipt_sha256", "map_status", "route_review_schema", "route_review_sha256", "route_review_id", "route_card_sha256", "selected_route_id", "activation_eligible", "missing_activation_bindings"}
    require(isinstance(bindings, dict) and set(bindings) == bkeys, "source_bindings_invalid", "source_bindings", "Source bindings are incomplete.")
    require(bindings["map_validation_receipt_sha256"] is None if genesis else isinstance(bindings["map_validation_receipt_sha256"], str) and bool(HEX64.fullmatch(bindings["map_validation_receipt_sha256"])), "binding_hash_invalid", "source_bindings.map_validation_receipt_sha256", "Map receipt binding is inconsistent with source kind.")
    for key in ("route_review_sha256", "route_card_sha256"):
        require(bindings[key] is None or (isinstance(bindings[key], str) and bool(HEX64.fullmatch(bindings[key]))), "binding_hash_invalid", "source_bindings." + key, "Binding hash must be SHA-256 or null when the legacy asset does not exist.")
    require(bindings["route_review_id"] is None or text(bindings["route_review_id"]), "binding_id_invalid", "source_bindings.route_review_id", "Route review ID must be nonempty or null.")
    require(text(bindings["selected_route_id"]), "binding_id_invalid", "source_bindings.selected_route_id", "Selected route ID is required.")
    require(isinstance(bindings["activation_eligible"], bool), "activation_flag_invalid", "source_bindings.activation_eligible", "Activation eligibility must be boolean.")
    require(string_list(bindings["missing_activation_bindings"], nonempty=False), "missing_bindings_invalid", "source_bindings.missing_activation_bindings", "Missing activation bindings must be a string array.")
    if bindings["activation_eligible"]:
        require(not bindings["missing_activation_bindings"], "activation_bindings_inconsistent", "source_bindings.missing_activation_bindings", "An activation-eligible cognition cannot report missing bindings.")
    if activation:
        require(bindings["activation_eligible"] is True and not bindings["missing_activation_bindings"], "legacy_map_activation_forbidden", "source_bindings.activation_eligible", "A legacy or incomplete cognition cannot activate a v13 attempt.")
        if not genesis:
            require(bindings["map_schema"] == "math-research-map/v1" and bindings["map_status"] == "current", "legacy_map_activation_forbidden", "source_bindings.map_schema", "Only a current official research-map v1 may activate a v13 attempt.")
            require(bindings["route_review_schema"] == "math-research-route-review/v2", "route_review_v2_required", "source_bindings.route_review_schema", "Validated-map activation requires route review v2.")
            require(isinstance(bindings["route_review_sha256"], str) and text(bindings["route_review_id"]), "activation_binding_missing", "source_bindings", "Validated-map activation requires route review bindings.")
        require(isinstance(bindings["route_card_sha256"], str), "activation_binding_missing", "source_bindings.route_card_sha256", "Activation requires an attempt-local route card.")

    orientation = value["method_orientation"]
    okeys = {"method_family", "baseline_method", "project_modification", "high_level_mechanism", "key_objects", "parameters", "evidence_refs"}
    require(isinstance(orientation, dict) and set(orientation) == okeys, "method_orientation_fields_invalid", "method_orientation", "Method orientation uses a closed schema.")
    for key in ("method_family", "baseline_method", "project_modification", "high_level_mechanism"):
        require(text(orientation[key]), "method_orientation_missing", "method_orientation." + key, "State what the method is, its baseline, the project modification, and the high-level mechanism before technical steps.")
    objects = orientation["key_objects"]
    require(isinstance(objects, list) and objects, "key_objects_missing", "method_orientation.key_objects", "Define the main proof objects before using them.")
    for i, item in enumerate(objects):
        require(isinstance(item, dict) and set(item) == {"name", "role"} and text(item["name"]) and text(item["role"]), "key_object_definition_invalid", f"method_orientation.key_objects[{i}]", "Each key object needs a name and role.")
    parameters = orientation["parameters"]
    require(isinstance(parameters, list), "parameter_definitions_invalid", "method_orientation.parameters", "Parameters must be an array, even when empty.")
    for i, item in enumerate(parameters):
        p = f"method_orientation.parameters[{i}]"
        require(isinstance(item, dict) and set(item) == {"symbol", "meaning", "frozen_value", "choice_reason", "evidence_refs"}, "parameter_definition_invalid", p, "Each parameter needs symbol, mathematical meaning, frozen value, choice reason, and evidence.")
        for key in ("symbol", "meaning", "frozen_value", "choice_reason"):
            require(text(item[key]), "parameter_definition_missing", p + "." + key, "Do not use an unexplained parameter in the frozen cognition.")
        require(refs(item["evidence_refs"]), "parameter_source_missing", p + ".evidence_refs", "Parameter roles and values need authoritative sources.")
    require(refs(orientation["evidence_refs"]), "method_orientation_source_missing", "method_orientation.evidence_refs", "Method orientation needs authoritative sources.")

    methods = value["verified_method_spine"]
    mkeys = {"claim_id", "conclusion", "method_spine", "reusable_structures", "bottleneck_effect", "cannot_imply", "evidence_refs"}
    require(isinstance(methods, list) and (methods or genesis), "method_spine_missing", "verified_method_spine", "An empty verified spine is honest only at genesis.")
    for i, item in enumerate(methods):
        p = f"verified_method_spine[{i}]"
        require(isinstance(item, dict) and set(item) == mkeys, "method_fields_invalid", p, "Method milestone fields are invalid.")
        for key in ("claim_id", "conclusion", "method_spine", "bottleneck_effect", "cannot_imply"):
            require(text(item[key]), "method_causality_missing", p + "." + key, "Verified conclusions require method and boundary causality.")
        require(string_list(item["reusable_structures"]), "reusable_structures_missing", p + ".reusable_structures", "Reusable structures are required.")
        require(refs(item["evidence_refs"]), "method_source_missing", p + ".evidence_refs", "Method claims require authoritative evidence references.")

    bottleneck = value["current_bottleneck"]
    bk = {"statement", "derivation", "target_quantity", "evidence_refs"}
    require(isinstance(bottleneck, dict) and set(bottleneck) == bk, "bottleneck_fields_invalid", "current_bottleneck", "Bottleneck fields are invalid.")
    for key in ("statement", "derivation", "target_quantity"):
        require(text(bottleneck[key]), "bottleneck_causality_missing", "current_bottleneck." + key, "Bottleneck and derivation are required.")
    require(refs(bottleneck["evidence_refs"]), "bottleneck_source_missing", "current_bottleneck.evidence_refs", "Bottleneck needs authoritative evidence.")

    decision = value["route_decision"]
    dk = {"route_id", "mechanism", "why_now", "why_over_alternatives", "targeted_bottleneck", "reused_verified_structures", "uncertainty", "success_gate", "candidate_failure_gate", "rerank_conditions", "uninstantiated_objects", "evidence_refs"}
    require(isinstance(decision, dict) and set(decision) == dk, "route_decision_fields_invalid", "route_decision", "Route decision fields are invalid.")
    require(decision["route_id"] == bindings["selected_route_id"], "selected_route_mismatch", "route_decision.route_id", "Selected route differs from source binding.")
    for key in ("mechanism", "why_now", "targeted_bottleneck", "uncertainty", "success_gate", "candidate_failure_gate"):
        require(text(decision[key]), "route_decision_reason_missing", "route_decision." + key, "Route choice requires a causal reason and explicit gates.")
    comparisons = decision["why_over_alternatives"]
    require(isinstance(comparisons, list) and comparisons, "why_over_alternatives_missing", "route_decision.why_over_alternatives", "At least one alternative must be compared.")
    for i, item in enumerate(comparisons):
        require(isinstance(item, dict) and set(item) == {"route_id", "reason"} and text(item["route_id"]) and text(item["reason"]), "alternative_reason_invalid", f"route_decision.why_over_alternatives[{i}]", "Alternative comparison is invalid.")
    for key in ("reused_verified_structures", "rerank_conditions", "uninstantiated_objects"):
        require(string_list(decision[key], nonempty=(key != "uninstantiated_objects")), "route_decision_list_invalid", "route_decision." + key, "Route decision list is invalid.")
    require(refs(decision["evidence_refs"], require_causal_authority=True), "route_decision_authority_missing", "route_decision.evidence_refs", "Selection reasons must cite memory or route review authority.")

    boundaries = value["evidence_boundaries"]
    require(isinstance(boundaries, list) and boundaries, "evidence_boundaries_missing", "evidence_boundaries", "Evidence boundaries are required.")
    for i, item in enumerate(boundaries):
        require(isinstance(item, dict) and set(item) == {"statement", "classification", "scope", "cannot_imply", "evidence_refs"}, "evidence_boundary_invalid", f"evidence_boundaries[{i}]", "Evidence boundary fields are invalid.")
        require(item["classification"] in ("verified", "verified_refutation", "verified_impossibility_boundary", "bounded_negative", "unresolved_obstacle", "reproduction_blocked"), "evidence_class_invalid", f"evidence_boundaries[{i}].classification", "Unknown evidence class.")
        for key in ("statement", "scope", "cannot_imply"):
            require(text(item[key]), "evidence_boundary_missing", f"evidence_boundaries[{i}].{key}", "Evidence scope and non-implication are required.")
        require(refs(item["evidence_refs"]), "evidence_boundary_source_missing", f"evidence_boundaries[{i}].evidence_refs", "Evidence boundary needs sources.")

    require(isinstance(value["retrieval_triggers"], list) and value["retrieval_triggers"], "retrieval_triggers_missing", "retrieval_triggers", "On-demand retrieval rules are required.")
    for i, item in enumerate(value["retrieval_triggers"]):
        require(isinstance(item, dict) and set(item) == {"when", "retrieve", "purpose"} and text(item["when"]) and string_list(item["retrieve"]) and text(item["purpose"]), "retrieval_trigger_invalid", f"retrieval_triggers[{i}]", "Retrieval trigger is invalid.")
    require(string_list(value["semantic_reset_conditions"]), "semantic_reset_missing", "semantic_reset_conditions", "Semantic reset conditions are required.")
    freeze = value["freeze_policy"]
    require(isinstance(freeze, dict) and set(freeze) == {"immutable_during_attempt", "checkpoint_may_replace", "replacement_requires"}, "freeze_policy_invalid", "freeze_policy", "Freeze policy is invalid.")
    require(freeze["immutable_during_attempt"] is True and freeze["checkpoint_may_replace"] == "continuity_capsule_only" and freeze["replacement_requires"] == "semantic_reset_and_new_attempt", "freeze_policy_weak", "freeze_policy", "Cognition must remain immutable within the attempt.")
    payload = canonical(value)
    return {"ok": True, "schema": SCHEMA, "canonical_bytes": len(payload), "canonical_budget_status": "within_budget" if len(payload) <= MAX_BYTES else "exceeded", "sha256": sha256_bytes(payload), "activation_eligible": activation}


def render_normal(value: dict[str, Any]) -> str:
    validate(value)
    orientation = value["method_orientation"]
    bindings = value["source_bindings"]
    lines = ["# 本轮冻结的项目认知核心", "", "## 绑定与使用边界", ""]
    if bindings["activation_eligible"]:
        lines.append(f"本认知绑定当前 {bindings['map_schema']} 地图、{bindings['route_review_schema']} 路线复核和已冻结路线卡，可在全部哈希一致时进入 v13 attempt-start 门禁。")
    else:
        missing = "、".join(bindings["missing_activation_bindings"]) or "未满足的 v13 激活绑定"
        lines.append(f"这是从 {bindings['map_schema']} 阅读层提取的只读项目认知，只能用于恢复全局认识，不能启动 v13 attempt。当前缺少：{missing}；不得为通过格式而伪造相应资产或哈希。")
    lines += ["", "## 最终目标", "", value["objective"], "", "## 这个项目采用的是什么方法", "", f"方法家族：{orientation['method_family']}。", "", f"基线方法：{orientation['baseline_method']}", "", f"本项目的改造：{orientation['project_modification']}", "", f"整体机制：{orientation['high_level_mechanism']}", "", "### 关键数学对象", ""]
    for item in orientation["key_objects"]:
        lines.append(f"- **{item['name']}**：{item['role']}")
    if orientation["parameters"]:
        lines += ["", "### 关键参数为什么这样取", ""]
        for item in orientation["parameters"]:
            lines.append(f"- **{item['symbol']}**：{item['meaning']} 冻结取值：{item['frozen_value']}。选择理由：{item['choice_reason']}")
    lines += ["", "## 已核验的严格方法链", ""]
    for item in value["verified_method_spine"]:
        lines += [f"- **{item['conclusion']}** 方法主干：{item['method_spine']} 可复用结构：{'；'.join(item['reusable_structures'])} 对瓶颈的影响：{item['bottleneck_effect']} 不能推出：{item['cannot_imply']}"]
    b = value["current_bottleneck"]
    d = value["route_decision"]
    lines += ["", "## 当前瓶颈是怎样定位出来的", "", f"{b['statement']} {b['derivation']} 需要改变的量是：{b['target_quantity']}。", "", "## 为什么本轮走这条路线", "", f"当前路线：{d['route_id']}。{d['mechanism']} 为什么现在做：{d['why_now']} 针对的瓶颈：{d['targeted_bottleneck']}。", ""]
    for alt in d["why_over_alternatives"]:
        lines.append(f"- 暂缓 {alt['route_id']}：{alt['reason']}")
    lines += ["", f"不确定性：{d['uncertainty']}", f"成功门：{d['success_gate']}", f"候选失败门：{d['candidate_failure_gate']}"]
    if d["uninstantiated_objects"]:
        lines += ["", "尚未实例化：" + "；".join(d["uninstantiated_objects"]) + "。"]
    lines += ["", "## 证据边界", ""]
    for item in value["evidence_boundaries"]:
        lines.append(f"- {item['statement']}（{item['classification']}，范围：{item['scope']}）。不能推出：{item['cannot_imply']}")
    lines += ["", "## 何时沿双链读取细节", ""]
    for item in value["retrieval_triggers"]:
        lines.append(f"- 当{item['when']}时，读取 {'、'.join(item['retrieve'])}，用于{item['purpose']}。")
    lines += ["", "## 何时必须重置而不是继续 checkpoint", ""]
    for item in value["semantic_reset_conditions"]:
        lines.append(f"- {item}")
    if bindings["activation_eligible"]:
        lines += ["", "本文件在本轮 attempt 内保持逐字节不变；checkpoint 只能更新局部 continuity capsule。"]
    else:
        lines += ["", "本文件是只读恢复认知，不是 attempt 冻结资产；补齐 v13 激活绑定以后，必须重新生成并冻结新的 cognition，不能把本稿直接升级为 attempt 权威状态。"]
    return "\n".join(lines).rstrip() + "\n"


def _boundary_line(item: dict[str, Any]) -> str:
    return f"{item['statement']}（{item['classification']}；范围：{item['scope']}）；不能推出：{item['cannot_imply']}"


def render_compact(value: dict[str, Any]) -> str:
    validate(value)
    o = value["method_orientation"]
    b = value["current_bottleneck"]
    d = value["route_decision"]
    bindings = value["source_bindings"]
    lines = [
        "# 本轮冻结的项目认知核心（紧凑版）", "",
        "## 目标与方法", "", value["objective"], "",
        f"方法家族：{o['method_family']}。基线：{o['baseline_method']} 改造：{o['project_modification']} 机制：{o['high_level_mechanism']}", "",
        "关键对象：" + "；".join(f"{x['name']}：{x['role']}" for x in o["key_objects"]) + "。",
    ]
    if o["parameters"]:
        lines.append("参数：" + "；".join(f"{x['symbol']}={x['frozen_value']}（{x['meaning']}；理由：{x['choice_reason']}）" for x in o["parameters"]) + "。")
    lines += ["", "## 已证主干与瓶颈", ""]
    for item in value["verified_method_spine"]:
        lines.append(f"- {item['conclusion']}；方法：{item['method_spine']}；可复用：{'、'.join(item['reusable_structures'])}；作用：{item['bottleneck_effect']}；边界：{item['cannot_imply']}")
    lines += ["", f"当前瓶颈：{b['statement']} 推导：{b['derivation']} 必须改变：{b['target_quantity']}。", "", "## 本轮路线", "", f"{d['route_id']}：{d['mechanism']} 现在优先，因为：{d['why_now']} 它直接针对：{d['targeted_bottleneck']}。"]
    for alt in d["why_over_alternatives"]:
        lines.append(f"- 暂缓 {alt['route_id']}：{alt['reason']}")
    lines += [f"不确定性：{d['uncertainty']}", f"成功门：{d['success_gate']}", f"单候选失败门：{d['candidate_failure_gate']}"]
    if d["uninstantiated_objects"]:
        lines.append("尚未实例化：" + "；".join(d["uninstantiated_objects"]) + "。")
    lines += ["", "## 证据边界", ""] + [f"- {_boundary_line(x)}" for x in value["evidence_boundaries"]]
    lines += ["", "## 检索与重置", ""]
    for item in value["retrieval_triggers"]:
        lines.append(f"- {item['when']} → {'、'.join(item['retrieve'])}（{item['purpose']}）")
    lines.append("必须重置：" + "；".join(value["semantic_reset_conditions"]) + "。")
    if bindings["activation_eligible"]:
        lines.append("本版与正常版来自同一 cognition；本轮冻结其所选渲染哈希，checkpoint 只能更新 continuity capsule。")
    else:
        lines.append("本版只用于旧项目只读恢复，不能激活 v13 attempt。")
    return "\n".join(lines).rstrip() + "\n"


def render_minimal_safe(value: dict[str, Any]) -> str:
    validate(value)
    o = value["method_orientation"]
    b = value["current_bottleneck"]
    d = value["route_decision"]
    lines = [
        "# 本轮冻结的项目认知核心（最小安全版）", "",
        f"目标：{value['objective']}", "",
        f"方法：在{o['baseline_method']}基础上，使用{o['method_family']}；本项目{o['project_modification']}，通过{o['high_level_mechanism']}连接到目标。",
        "对象：" + "；".join(f"{x['name']}={x['role']}" for x in o["key_objects"]) + "。",
    ]
    if o["parameters"]:
        lines.append("参数：" + "；".join(f"{x['symbol']}={x['frozen_value']}，含义：{x['meaning']}，理由：{x['choice_reason']}" for x in o["parameters"]) + "。")
    lines += ["", "已证主干："]
    for item in value["verified_method_spine"]:
        lines.append(f"- {item['conclusion']}；由{item['method_spine']}得到；复用{'、'.join(item['reusable_structures'])}；影响{item['bottleneck_effect']}；不能推出{item['cannot_imply']}。")
    lines += ["", f"瓶颈：{b['statement']}；因为{b['derivation']}；要改变{b['target_quantity']}。", "", f"本轮路线 {d['route_id']}：{d['mechanism']} 现在选择它，因为{d['why_now']}；它针对{d['targeted_bottleneck']}。"]
    lines.append("备选暂缓：" + "；".join(f"{x['route_id']}：{x['reason']}" for x in d["why_over_alternatives"]) + "。")
    lines += [f"不确定性：{d['uncertainty']}", f"成功：{d['success_gate']}", f"仅该候选失败：{d['candidate_failure_gate']}"]
    if d["uninstantiated_objects"]:
        lines.append("不存在、不得假定：" + "；".join(d["uninstantiated_objects"]) + "。")
    lines += ["", "证据边界："] + [f"- {_boundary_line(x)}" for x in value["evidence_boundaries"]]
    lines += ["", "按需读取："] + [f"- {x['when']}：{'、'.join(x['retrieve'])}，用于{x['purpose']}。" for x in value["retrieval_triggers"]]
    lines += ["重置条件：" + "；".join(value["semantic_reset_conditions"]) + "。", "此最小版只压缩表达，不改变目标、方法因果、瓶颈、选路、证据边界或重置语义；Token 超限不得阻断研究。"]
    return "\n".join(lines).rstrip() + "\n"


def render(value: dict[str, Any], profile: str = "normal") -> str:
    require(profile in RENDER_PROFILES, "render_profile_invalid", "profile", "Unknown cognition render profile.")
    return {"normal": render_normal, "compact": render_compact, "minimal_safe": render_minimal_safe}[profile](value)


def count_tokens(rendered: str) -> dict[str, Any]:
    helper = Path(__file__).with_name("count_openai_tokens.js")
    node = shutil.which("node")
    if node and helper.is_file():
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "cognition.md"
            source.write_text(rendered, encoding="utf-8", newline="\n")
            proc = subprocess.run([node, str(helper), str(source)], text=True, capture_output=True, encoding="utf-8", timeout=60)
            if proc.returncode == 0:
                result = json.loads(proc.stdout)
                if result.get("ok") is True and isinstance(result.get("tokens"), int) and result["tokens"] >= 0:
                    return {"tokenizer": result["tokenizer"], "quality": result["quality"], "tokens": result["tokens"]}
    encoded = rendered.encode("utf-8")
    return {"tokenizer": "utf8-byte-upper-bound/v1", "quality": "upper_bound", "tokens": len(encoded)}


def prepare_budget_bundle(value: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    validation = validate(value)
    output_dir.mkdir(parents=True, exist_ok=True)
    renderings = []
    rendered_by_profile: dict[str, str] = {}
    for profile in RENDER_PROFILES:
        rendered = render(value, profile)
        rendered_by_profile[profile] = rendered
        path = output_dir / (profile.replace("_", "-") + ".md")
        path.write_text(rendered, encoding="utf-8", newline="\n")
        counted = count_tokens(rendered)
        renderings.append({
            "profile": profile,
            "sha256": sha256_bytes(rendered.encode("utf-8")),
            "utf8_bytes": len(rendered.encode("utf-8")),
            "tokens": counted["tokens"],
            "tokenizer": counted["tokenizer"],
            "count_quality": counted["quality"],
        })
    by_name = {item["profile"]: item for item in renderings}
    if by_name["normal"]["tokens"] <= TOKEN_TARGET:
        selected = by_name["normal"]
    elif by_name["compact"]["tokens"] <= TOKEN_LIMIT:
        selected = by_name["compact"]
    elif by_name["minimal_safe"]["tokens"] <= TOKEN_LIMIT:
        selected = by_name["minimal_safe"]
    else:
        selected = by_name["minimal_safe"]
    status = "within_budget" if selected["tokens"] <= TOKEN_LIMIT else "exceeded"
    receipt = {
        "schema": BUDGET_SCHEMA,
        "cognition_sha256": validation["sha256"],
        "token_target": TOKEN_TARGET,
        "token_limit": TOKEN_LIMIT,
        "selection_policy": "normal_at_target_then_compact_then_minimal_safe_else_continue_minimal_safe",
        "renderings": renderings,
        "selected_profile": selected["profile"],
        "selected_rendered_sha256": selected["sha256"],
        "selected_tokens": selected["tokens"],
        "budget_status": status,
        "attempt_blocking": False,
        "maintenance_due": status == "exceeded",
    }
    (output_dir / "token-receipt.json").write_bytes(canonical(receipt))
    return receipt


def validate_budget_receipt(value: dict[str, Any], receipt: Any) -> dict[str, Any]:
    keys = {"schema", "cognition_sha256", "token_target", "token_limit", "selection_policy", "renderings", "selected_profile", "selected_rendered_sha256", "selected_tokens", "budget_status", "attempt_blocking", "maintenance_due"}
    require(isinstance(receipt, dict) and set(receipt) == keys, "cognition_budget_receipt_invalid", "$", "Cognition budget receipt uses a closed schema.")
    require(receipt["schema"] == BUDGET_SCHEMA, "cognition_budget_schema_invalid", "schema", "Expected cognition-budget/v1.")
    require(receipt["cognition_sha256"] == sha256_bytes(canonical(value)), "cognition_budget_binding_mismatch", "cognition_sha256", "Budget receipt does not bind this cognition.")
    require(receipt["token_target"] == TOKEN_TARGET and receipt["token_limit"] == TOKEN_LIMIT, "cognition_budget_policy_mismatch", "$", "Token policy mismatch.")
    require(receipt["selection_policy"] == "normal_at_target_then_compact_then_minimal_safe_else_continue_minimal_safe", "cognition_budget_policy_mismatch", "selection_policy", "Unknown selection policy.")
    require(receipt["attempt_blocking"] is False, "cognition_budget_must_not_block", "attempt_blocking", "Token budget may not block an attempt.")
    require(receipt["selected_profile"] in RENDER_PROFILES, "render_profile_invalid", "selected_profile", "Selected render profile is invalid.")
    require(isinstance(receipt["renderings"], list) and {x.get("profile") for x in receipt["renderings"] if isinstance(x, dict)} == set(RENDER_PROFILES), "renderings_invalid", "renderings", "All three render profiles are required.")
    rendering_keys = {"profile", "sha256", "utf8_bytes", "tokens", "tokenizer", "count_quality"}
    by_name = {}
    for item in receipt["renderings"]:
        require(set(item) == rendering_keys, "rendering_fields_invalid", "renderings", "Rendering receipt fields are invalid.")
        profile = item["profile"]
        rendered_profile = render(value, profile)
        encoded = rendered_profile.encode("utf-8")
        require(item["sha256"] == sha256_bytes(encoded) and item["utf8_bytes"] == len(encoded), "rendered_cognition_hash_mismatch", "renderings", "Rendered cognition bytes do not match the receipt.")
        require(item["tokenizer"] in {"o200k_base", "utf8-byte-upper-bound/v1"} and item["count_quality"] in {"exact", "upper_bound"} and isinstance(item["tokens"], int) and item["tokens"] >= 0, "token_receipt_invalid", "renderings", "Token counter receipt is invalid.")
        if item["tokenizer"] == "utf8-byte-upper-bound/v1":
            require(item["count_quality"] == "upper_bound" and item["tokens"] == len(encoded), "token_receipt_mismatch", "renderings", "UTF-8 upper-bound count is inconsistent.")
        else:
            recounted = count_tokens(rendered_profile)
            if recounted["tokenizer"] == "o200k_base" and recounted["quality"] == "exact":
                require(item["tokens"] == recounted["tokens"], "token_receipt_mismatch", "renderings", "Exact o200k token count changed.")
        by_name[profile] = item
    expected = by_name["normal"] if by_name["normal"]["tokens"] <= TOKEN_TARGET else by_name["compact"] if by_name["compact"]["tokens"] <= TOKEN_LIMIT else by_name["minimal_safe"]
    require(receipt["selected_profile"] == expected["profile"], "render_profile_selection_invalid", "selected_profile", "Selected profile does not follow the deterministic fallback order.")
    selected = by_name[receipt["selected_profile"]]
    rendered = render(value, receipt["selected_profile"])
    digest = sha256_bytes(rendered.encode("utf-8"))
    require(selected.get("sha256") == digest == receipt["selected_rendered_sha256"], "rendered_cognition_hash_mismatch", "selected_rendered_sha256", "Selected rendered cognition hash mismatch.")
    require(selected.get("tokens") == receipt["selected_tokens"] and isinstance(receipt["selected_tokens"], int), "token_receipt_mismatch", "selected_tokens", "Selected token count is inconsistent.")
    expected_status = "within_budget" if receipt["selected_tokens"] <= TOKEN_LIMIT else "exceeded"
    require(receipt["budget_status"] == expected_status and receipt["maintenance_due"] is (expected_status == "exceeded"), "budget_status_invalid", "budget_status", "Budget status is inconsistent.")
    return {"ok": True, "selected_profile": receipt["selected_profile"], "selected_rendered_sha256": digest, "selected_tokens": receipt["selected_tokens"], "budget_status": expected_status, "attempt_blocking": False, "maintenance_due": receipt["maintenance_due"]}


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--input", required=True, type=Path)
    g.add_argument("--output", required=True, type=Path)
    v = sub.add_parser("validate")
    v.add_argument("--input", required=True, type=Path)
    v.add_argument("--activation", action="store_true")
    r = sub.add_parser("render")
    r.add_argument("--input", required=True, type=Path)
    r.add_argument("--output", type=Path)
    r.add_argument("--profile", choices=RENDER_PROFILES, default="normal")
    b = sub.add_parser("prepare-budget")
    b.add_argument("--input", required=True, type=Path)
    b.add_argument("--output-dir", required=True, type=Path)
    q = sub.add_parser("validate-budget")
    q.add_argument("--input", required=True, type=Path)
    q.add_argument("--receipt", required=True, type=Path)
    args = p.parse_args(argv)
    try:
        value = load(args.input)
        result = validate(value, activation=getattr(args, "activation", False))
        if args.command == "generate":
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(canonical(value))
        elif args.command == "render":
            rendered = render(value, args.profile)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(rendered, encoding="utf-8", newline="\n")
            else:
                sys.stdout.write(rendered)
                return 0
        elif args.command == "prepare-budget":
            result = prepare_budget_bundle(value, args.output_dir)
        elif args.command == "validate-budget":
            result = validate_budget_receipt(value, load(args.receipt))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except CognitionError as exc:
        print(json.dumps({"ok": False, "error": {"code": exc.code, "path": exc.path, "message": exc.message}}, ensure_ascii=False, indent=2))
        return 2
    except Exception as exc:
        print(json.dumps({"ok": False, "error": {"code": "internal_error", "message": f"{type(exc).__name__}: {exc}"}}, ensure_ascii=False, indent=2))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
