# jin-math-explore

一个面向**批量、长期、最困难数学问题**的 AI 研究仓库。

本仓库不是聊天记录归档，也不是普通习题集。它把每个问题建模为独立、可恢复、可验证的长期研究项目，并以 Git 提交和 Pull Request 发布权威状态变化。

## 核心原则

- **Issue 是队列，不是数学真相。** Issue 用于候选问题、来源核查、阻塞、租约和调度。
- **项目文件是数学状态。** 每个问题拥有不可变目标、研究地图、因果记忆、尝试包和验证记录。
- **PR 是权威变化。** `main` 只接收已闭合的研究窗口、独立验证、来源更新或基础设施变更。
- **计算不是证明。** 有限搜索、数值实验和 CAS 输出必须声明证据等级及 `cannot_imply`。
- **验证与求解隔离。** 验证者只读取冻结候选与依赖，不继承求解者聊天叙事。
- **跨项目复用需重新接纳。** 其他项目的已验证结果只能通过显式导入协议进入本项目。
- **并发先声明冲突域。** Agent 通过 Issue lease、独立 branch、base SHA 和精确写集协作；lease 不拥有数学权威。

详细约束见 [`GOVERNANCE.md`](GOVERNANCE.md)、[`PROGRAM_CHARTER.md`](PROGRAM_CHARTER.md) 和 [`program/`](program/)。

## 多 Agent 协作

GitHub 在这里承担五种职责：Issue / Project 是协调平面，branch 是临时执行平面，受保护 `main` 是发布平面，Project heads / receipts 是数学平面，CI 是机械验证平面。

每个 merge-intended PR 必须：

1. 绑定一个 work packet Issue；
2. 在 Issue 中取得有限期 lease，并声明 actor/run/role、base SHA 和 read/write set；
3. 使用单写 owner 的短期 branch；
4. 在 PR body 提交机器可读 coordination manifest；
5. 通过 title/branch/path、manifest/write-set、repository、catalog 和 Skill lock 检查；
6. 在最新 `main` 上 squash merge。

详细协议见 [`program/multi-agent-governance.md`](program/multi-agent-governance.md)。同一 GitHub 用户可以承载多个 Agent，因此 username 或 approval 不能证明 verifier 独立；独立性按 run、上下文可见性和冻结输入记录。

## 仓库结构

```text
GOVERNANCE.md            多 Agent 治理宪章
program/                 全局研究计划与协作政策
registry/projects/       每个长期问题一个独立注册文件
registry/shared-results/ 可跨项目复用的已验证结果
projects/                math-research-solve v13 项目根
computation/             共享计算协议、队列和环境说明
catalog/                 从 registry 生成的全局视图
schemas/                 机器契约
scripts/                 校验和生成工具
.agents/skills/          仓库专用工作流 Skills
.github/                 Issue Forms、PR 模板和 CI
```

## 本地验证

要求 Python 3.10+：

```bash
python -m unittest discover -s tests -v
python scripts/validate_repository.py --root .
python scripts/build_catalog.py --root . --check
python scripts/check_skill_dependencies.py --root .
```

或运行：

```bash
make check
```

PR 中还会运行：

```bash
python scripts/pr_policy.py --root .
python scripts/coordination_policy.py --root .
```

登记一个待来源核查的候选：

```bash
python scripts/register_candidate.py \
  --project-id P-0001 \
  --slug example-hard-problem \
  --title "Example hard problem" \
  --problem-class likely_open_needs_audit
python scripts/build_catalog.py --root .
```

## Skills

仓库专用 Skills：

- `$math-research-program`：跨项目队列、窗口和资源控制。
- `$math-frontier-scout`：发现候选难题，输出待核查候选，不宣称开放性。
- `$math-source-audit`：独立核查开放状态、来源和已知边界。
- `$math-independent-verifier`：验证冻结 claim、proof 和 computation bundle。
- `$math-computation-handoff`：把 Project attempt 与可复现计算绑定。
- `$math-window-pr`：发布一个已闭合研究窗口的最小 PR。

已 vendoring 的基础能力：

- `$math-research-solve` 1.11：每个问题的严格研究内核。
- `$math-science-computation` 1.11：计算执行与可复现记录。

两个完整 Skill 已原样放入 `.agents/skills/`。依赖版本和发布树哈希记录在 [`skill-dependencies.json`](skill-dependencies.json)，277 个文件的 SHA-256 与 Git executable bit 锁定在 [`vendored-skills.lock.json`](vendored-skills.lock.json)。仓库 CI 会逐文件重算，不允许 payload 静默漂移。来源和边界见 [`docs/vendored-skills.md`](docs/vendored-skills.md)。

## 当前阶段

当前是 **program foundation v0 + governance v1**：先建立状态所有权、证据边界、多 Agent 并发纪律、机器契约和 CI，再启动首批真实研究项目。

## 许可证

本仓库尚未选择开源许可证。在仓库所有者明确许可证前，默认不授予复制、修改或再分发许可。
