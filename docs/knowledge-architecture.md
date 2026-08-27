# 数学任务分类、知识网络与结果反馈架构

版本：`jin-math-knowledge-architecture/v1`

本文件定义 `jin-math-explore` 的横向知识组织层。它补充已有的 Project 状态机、证据政策和独立验证，但不改变数学权威边界：Project 中冻结的 claim/candidate/receipt 与 `registry/shared-results/` 仍是数学结论的权威载体；分类、知识节点和反馈字段只是可审计的导航与组合投影。

## 1. 当前机制的判断

仓库已有基础设施对以下问题处理得较好：

- 把运营状态与数学状态分开；
- 用不可变 objective、双 head、窗口和 receipt 管理长期研究；
- 把有限计算、证明候选和独立验证分级；
- 用 PR、hash、CI 和 Project CAS 阻止静默状态漂移；
- 只允许已独立验证的结果跨 Project 复用。

缺口主要不在纵向研究流程，而在横向组合能力：

1. 旧 `problem_class` 同时混入问题来源、研究形态和预期产物，不能回答“它属于哪个数学领域、研究什么对象、目标是什么、可能用什么方法”。
2. objective 的 `domain` 是不可变数学语义的一部分，但自由文本不适合作为全局检索键。
3. 旧依赖只有 Project → Project，无法表达一个任务依赖的定义、定理、方法、约定、反例或已验证共享结果。
4. catalog 只投影状态和窗口，不能稳定回答“上一次工作到底增加了什么知识、减少了什么不确定性、留下多少验证/知识债务”。

因此本架构不重写 Project 内核，而是在 registry 侧增加三种正交对象：**faceted classification、typed dependency、audited feedback**。

## 2. 任务分类：一个问题必须有多个正交坐标

不得再用单一标签表示“问题类型”。Project registry v2 使用以下七个维度。

### 2.1 Subject：数学领域

- 标准：`MSC2020`。
- `primary`：一个主分类；候选阶段可为 `unclassified`。
- `secondary`：零个或多个交叉领域代码。
- `classification.status=reviewed` 后，主分类不得继续为 `unclassified`。

MSC 用于稳定的学科检索，不承担问题语义。具体 statement、定义域、量词和假设仍由 objective 决定。

### 2.2 Origin：问题从哪里产生

```text
known_open
likely_open_needs_audit
internal_frontier
missing_lemma
computational_conjecture
generalization
optimality_question
counterexample_search
```

Origin 描述进入研究队列的来源，不描述数学领域，也不等价于当前开放状态。

### 2.3 Goal types：要得到什么形式的结果

可多选，例如：

```text
existence / nonexistence / uniqueness
classification / characterization / equivalence
construction / counterexample
bound / optimality / asymptotic
regularity / convergence / stability
algorithm / decidability / computation
formalization / explanation
```

“证明一个开放问题”不是足够精确的目标类型。应写出最终结论的逻辑形态。

### 2.4 Object tags：研究对象

使用受控格式的 lowercase kebab-case，例如：

```text
finite-graph
elliptic-pde
c-star-algebra
riemannian-manifold
random-matrix
```

对象标签是仓库内约定，不冒充标准分类。发现同义词时，应统一词汇而不是永久保留多个拼写。

### 2.5 Method tags：当前相关的方法族

例如：

```text
fourier-analysis
probabilistic-method
forcing
semidefinite-programming
computer-algebra
```

Method tag 表示已知相关、候选或被审计的方法索引，不表示方法一定成功。失败方法应通过 Project memory/route review 或 obstruction 知识节点留下精确边界。

### 2.6 Portfolio role：该任务对整体研究计划的作用

```text
frontier_problem       直接面向最终难题
bridge_problem         连接多个领域或结果
foundation_building    建立下游所需基础
method_development     构造/验证可复用方法
application_case       检验理论在具体对象上的覆盖
```

该字段用于资源组合，不用于提升数学证据。

### 2.7 Classification status：分类本身也需要审查

- `provisional`：候选登记时允许不完整；
- `reviewed`：进入 Project genesis/活动状态前，主 MSC、具体 goal type 和至少一个 object tag 已人工或独立流程核查。

分类可以修订，因为它是运营投影；objective 不可因此被偷偷改写。若分类修订暴露 statement 语义变化，应新建 Project/fork，而不是只改标签。

## 3. Typed dependencies：把“依赖”分成三种

Project registry v2 的依赖结构为：

```json
{
  "projects": ["P-XXXX"],
  "knowledge": ["K-XXXX"],
  "shared_results": ["S-XXXX"]
}
```

- `projects`：另一个长期研究目标的运营/数学状态会阻塞本 Project；必须无环。
- `knowledge`：需要先读取、统一或补齐的基础节点。
- `shared_results`：已独立验证、可以提出显式 import proposal 的结果。

三者不能互相代替。特别是，`K-XXXX` 只提供导航和来源边界；只有相应 `S-XXXX` 或 Project receipt 才能作为已验证数学依赖。

## 4. 是否整理学科基础知识

**有必要，但必须按需求生长，不建设百科全书镜像。**

### 4.1 创建全局知识节点的准入条件

满足至少一项才创建 `K-XXXX`：

1. 一个候选/Project 在 objective freeze、attempt、verification 或复现中明确依赖它；
2. 两个以上任务需要统一同一套定义、符号或假设约定；
3. 一个已审计方法、定理、反例或 obstruction 具有跨 Project 复用价值；
4. 一个基础缺口已经成为可命名、可分派、可验证的共享 blocker。

仅仅“这个领域很重要”不构成录入理由。大段教材内容、百科式历史、无下游引用的概念清单不进入权威网络。

### 4.2 三层知识结构

| 层 | 位置 | 用途 | 权威 |
|---|---|---|---|
| Project-local working knowledge | Project research map / memory / attempts | 当前目标的工作定义、路线和失败边界 | 由 Project head/receipt 决定 |
| Global knowledge node | `knowledge/nodes/K-XXXX.json` | 跨任务导航、先修关系、约定、来源和缺口 | 默认不构成证明 |
| Verified shared result | `registry/shared-results/S-XXXX.json` | 可提出跨 Project 导入的已验证结果 | 独立验证 receipt 绑定 |

Project-local 内容只有在出现真实复用需求、完成来源/证据边界整理后，才提升为全局知识节点。知识节点只有绑定已存在的 `S-XXXX` 和 receipt 时，才能标记 `independently_verified`；节点自身不能“自证”。

### 4.3 知识节点类型

```text
definition / notation / theorem / lemma / equivalence
method / example / counterexample / obstruction
computational_fact / reference_map / knowledge_gap
```

每个节点记录：主/次 MSC、对象/方法标签、statement、假设、scope、conventions、先修节点、到 K/P/S 的类型化关系、authority、source refs 与 `cannot_imply`。

先修关系必须无环；`equivalent_to` 等语义关系可以双向，但不能被误当成先修顺序。

## 5. 结果反馈：关注“状态变化”，不只关注“有没有解出”

每个 registry entry 保存最新一次已审计事件的 `result_feedback`。它是 receipt 的非权威摘要，字段包括：

- `event_type` / `event_id` / `receipt`：精确绑定来源事件；
- `frontier_movement`：`clarified`、`narrowed`、`reframed`、`expanded`、`unchanged` 或终局关闭；
- 本次新增的 verified claims / refutations；
- 排除的路线数量；
- 解决与未解决 blocker 数量；
- `verification_debt`：等待独立审查的候选数量；
- `knowledge_debt`：缺失定义、来源、桥梁或方法节点的明确清单；
- `next_frontier`：下一项最小、可验证、能改变状态的工作。

### 5.1 为什么不使用单一“进度分数”

不同数学问题的证明深度、反例价值和基础工作不可直接压成一个数字。单一分数会诱导模型制造容易计数的碎片。系统保留多维事件指标，并要求每次非空反馈绑定存在的 receipt。

### 5.2 什么算有效结果

以下都可以是净进展，但证据等级必须诚实：

- 精确澄清 statement、量词、定义或开放状态；
- 把 frontier 缩小到更窄命题或参数区间；
- 独立验证一个 lemma、反例、impossibility boundary；
- 用可复现计算排除有限范围或发现稳定模式；
- 证明某条方法路线在明确假设下失败；
- 清偿验证债务或把隐含基础缺口转成可分派 `K-XXXX`；
- 形成可复用的已验证 `S-XXXX`。

“写了更多文本”“运行时间更长”“模型更自信”不算结果。

### 5.3 反馈闭环

```text
candidate classification
  -> source audit + prerequisite map
  -> reviewed classification / objective freeze
  -> research window
  -> frozen candidates + independent verification
  -> reconciliation receipt
  -> result_feedback projection
  -> catalog / scheduler chooses next decisive frontier
```

调度器可以使用这些字段决定资源优先级，但不得根据反馈摘要自行提升 claim。任何冲突以 Project artifact/receipt 为准，并修复 registry 投影。

## 6. 机器约束与演进

- `taxonomy/facets.json` 是 v1 闭词表；新增枚举值需要 infra PR、schema、validator 与测试一起更新。
- MSC 只做语法校验，不把完整外部 MSC 数据库 vendoring 到仓库。
- Project 和 knowledge prerequisites 的缺失引用、自引用与环都会使 CI 失败。
- active/genesis 后的 Project 必须使用 `reviewed` 分类；候选可暂时 `unclassified`。
- catalog 仍是生成视图，不可手工编辑；空仓库输出保持兼容。
- 本次迁移发生在首个真实 registry entry 之前，因此直接切换到 `jin-math-project-registry/v2`，不保留双写 authority。

## 7. 设计边界

本架构不保证分类永远正确，不替代来源审计，不把知识图谱关系当作逻辑蕴含，也不把反馈计数当作证明质量。它的目标是让后续任务能够被稳定地检索、组合、阻塞、复用和复盘，同时保持现有数学权威链不变。
