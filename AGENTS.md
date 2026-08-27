# Agent entrypoint

默认使用简体中文与用户沟通；代码、命令、schema 字段和正式数学符号保持原文。

## 必读顺序

1. `PROGRAM_CHARTER.md`
2. `program/evidence-policy.md`
3. `program/project-lifecycle.md`
4. `projects/AGENTS.md`
5. 当前目标 Project 的 objective、双 head、研究地图和相关证据

不要把 README、Issue、PR 描述、CI PASS 或模型共识当成数学权威。

## 状态所有权

- `registry/projects/*.json` 是全局运营投影；一次 PR 只修改相关 Project 的注册文件。
- Project 内 `project.json` 是该项目唯一 CAS head。
- `catalog/` 是生成物；运行 `python scripts/build_catalog.py --root .` 更新，禁止手工编辑。
- Issue 标签只表示运营状态，不表示 claim 的数学等级。
- 未经独立验证的跨项目结果不得进入 `registry/shared-results/`。

## 工作隔离

- 一个 Project 对应一个不可变目标。
- 一个活动 window 使用三个不同语义指纹。
- attempts 只写各自 staging，不能消费 sibling 的未验证输出。
- verifier 使用新上下文，只读取冻结候选、依赖和审查任务，不修改候选。
- reconciliation 只整合已有证据，不执行新数学。

## 计算

数学或科学计算使用 `$math-science-computation`，并产生 `jin-math-computation-handoff/v1`。记录精确/数值意图、定义域、假设、后端、版本、输入、复现命令、产物哈希、证据等级和 `cannot_imply`。

## 研究项目

长期项目使用 `$math-research-solve` v13。运行权威提交前必须验证 objective commitment、expected heads、plan SHA 和 Goal 状态。不得把旧版本状态规则混入活动 v13 head。

## 修改后检查

```bash
python -m unittest discover -s tests -v
python scripts/validate_repository.py --root .
python scripts/build_catalog.py --root . --check
python scripts/check_skill_dependencies.py --root .
```

## Code Review Rules

### Mathematical authority

- Flag any change that upgrades finite, numerical, heuristic, sampled, or CAS evidence to a universal proof without a verified coverage bridge. Safe path: retain the narrower evidence grade and add an explicit `cannot_imply` boundary.
- Flag a claim marked `independently_verified` when no exact candidate/dependency hashes and separate verification receipt are present. Safe path: keep it `proof_candidate` until a frozen review passes.
- Flag cross-project reuse that bypasses an independently verified shared-result record and target-project import validation.

### State integrity

- Flag hand-edited files under `catalog/`, objective mutation without a fork, or PRs that advance both protocol and mathematical authority under the new protocol.
- Flag a Project registry entry whose `objective_sha256`, path, operational status, or mathematical status disagrees with disk state.

### Reproducibility

- Flag computation conclusions without frozen inputs, backend/version, reproduction command, artifact hashes, evidence grade, and `cannot_imply`.
- Mechanical tests belong in CI; review should focus on consequential mathematical authority and state-integrity failures.
