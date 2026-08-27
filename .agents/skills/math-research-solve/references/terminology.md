# Math Research Solve canonical terminology

This glossary is normative for v13 and for migration decisions. Each term names a mathematical or project-semantic object; its JSON/Markdown file is only a storage carrier.

## `project_objective`

### 简要定义

一个数学研究项目永久不变的终局数学目标，也是判断后续工作是否仍属于同一项目的最高数学身份依据。

### 规范定义

`project_objective` 由准确命题 `statement`、对象与适用范围 `domain`、量词及依赖顺序 `quantifier_order`、允许前提 `assumptions`、可接受证据 `evidence_standard` 和终局解决条件 `completion_standard` 六项共同构成。六项共同决定“研究什么”和“怎样才算解决”；a semantic change requires a new project or explicit fork。

### 构成字段

`statement`、`domain`、`quantifier_order`、`assumptions`、`evidence_standard`、`completion_standard`，不多不少。

### 权威等级

永久项目数学身份；不可变。规范化六项内容是语义权威，`objective_commitment_sha256` 是机器承诺。

### 生命周期规则

在 genesis 创建并冻结，所有 task、Run、attempt、route、map、cognition、evidence、verification 和 export 绑定其哈希；暂停、完成、归档和 schema 迁移均不改变它。

### 允许的变化

允许存储路径、schema、Skill 版本、项目元数据、研究路线、工具、运行拓扑和派生视图变化，只要六项数学内容不变。

### 禁止的变化

禁止在原项目改写命题/定义域/量词、增删或弱化假设、降低证据或完成标准；程序不得自行宣称两个研究级目标数学等价。

### 不得混淆

不等于 Product Goal、`project.json`、任务、路线、文件、当前候选结论或整个项目 schema。

### 完成关系

候选必须覆盖全部定义域和量词，满足假设、证据与完成标准，并通过独立 verifier、terminal audit 和发布授权，才可使项目完成；特殊情形、有限计算、里程碑或路线成功均不足够。

### 机器绑定

规范化六项内容的 `objective_commitment_sha256`；存储载体可迁移但承诺不变。

## `task`

### 简要定义

项目中一项需要持久记录、可以跨会话继续的工作单元。

### 规范定义

`task` 表示 durable `research`、`external_intake`、`verification`、`strategy_review`、`project_maintenance` 或 `export` 工作，绑定项目目标与权限边界。纯问答不创建 task；非研究 task 不消耗 attempt。

### 构成字段

task ID、类型、目标哈希、范围、输入/输出、状态、权限与证据要求。

### 权威等级

项目级工作账本对象；低于 `project_objective`，高于临时对话待办。

### 生命周期规则

按持久需要创建，经历准备、活动、暂停/失败/完成并保留历史；可包含一个或多个 Run。

### 允许的变化

可更新执行状态、局部输入和输出指针，只要不扩大冻结权限或改写目标。

### 禁止的变化

禁止把 task 当作数学目标、attempt、ticket 或一次工具调用；禁止用完成 task 冒充完成项目。

### 不得混淆

`task` 是项目工作记录；`ticket` 是对单个协作者的冻结委派；`attempt` 是计数的研究路线执行。

### 完成关系

task 的交付物和验收条件满足时 task 完成，但只有覆盖终局目标的特殊 task 才可能参与项目完成。

### 机器绑定

task ID、project ID、objective hash 与持久 task record hash。

## `run`

### 简要定义

位于同一项目根、执行一个或多个持久 task 的连续研究运行容器。

### 规范定义

`Run` 保存同根执行历史、计数器、预算、事件、windows、tickets、attempts、routes、continuity、证据和输出。它承载生命周期，不拥有或替换永久数学目标。

### 构成字段

Run ID/路径、项目与目标绑定、状态、事件链、预算/计数、活动 task/window、artifacts 和 head 指针。

### 权威等级

项目执行层权威；`project.json` 指向 active Run，但 Run 低于项目永久身份。

### 生命周期规则

由 run genesis 创建，追加事件并推进状态；可结束、迁移或由 successor Run 继承，历史不可伪装成新 Run。

### 允许的变化

可追加受验证事件、window、attempt、checkpoint、evidence 和 route review；可在同目标/权限下创建 successor。

### 禁止的变化

禁止跨项目根偷换 Run、重置累积消耗、改写旧事件或把 Goal binding 当作数学身份。

### 不得混淆

不等于 product Goal、一次 attempt、shell 进程、agent thread 或整个 project。

### 完成关系

Run 可因预算耗尽、暂停、迁移或任务完成而结束；Run 结束不必然是项目完成。

### 机器绑定

Run ID、same-root path、objective commitment、event head 和 manifest hashes。

## `attempt`

### 简要定义

一个 window 内针对一个冻结证明对象、机制家族、量词策略、证据标准与 selected route 的计数研究执行。

### 规范定义

`attempt` 是 window 内部的受控数学研究单元；启动时绑定 task/Run/window、queue item、ticket、route decision、route、source map/head、project-core cognition、continuity capsule、资源与权限。它只处理 portfolio 中一个语义指纹。语义对象或路线因果解释改变时必须结束并 semantic reset，不能在 attempt 内偷换，也不能读取同一 window 中兄弟 attempt 尚未结算的工作。

### 构成字段

attempt ID/kind、window ID、queue item、ticket、route decision、route/route family、source map/head hashes、proof object、mechanism、quantifier strategy、evidence standard、cognition/capsule hashes、预算、状态、attempt outcome 与 reconciliation package。

### 权威等级

Run 内计数研究执行；其局部结论必须经 verification/promotion 才能进入长期权威记忆。

### 生命周期规则

通过 `ATTEMPT_START` 原子启动，checkpoint 只更新局部位置；`ATTEMPT_END` 冻结 attempt outcome，完成必要 verification，形成 `attempt_reconciliation_package`，最后进入 `ready_for_window_reconciliation`。项目级 memory/map 只在 window reconciliation 晋升和更新。

### 允许的变化

可推进推导、生成局部证据、更新问题清单和进度；允许同一冻结语义内的技术修正。

### 禁止的变化

禁止更换目标、proof object、mechanism family、quantifier strategy、evidence standard、selected route 或核心因果解释；外部 intake 不冒充 attempt。

### 不得混淆

不等于 task、Run、ticket、checkpoint、agent turn、路线档案或未计数 strategy review。

### 完成关系

attempt 结束只产生窗口结算输入，不独立推动项目 head；只有 window reconciliation 晋升后的证据才进入项目长期权威，终局候选还必须满足全部完成门禁。

### 机器绑定

attempt-start receipt 绑定 window/source map/source head、portfolio member、route decision、ticket、route、cognition、selected rendering 和 initial capsule；attempt-end package 绑定 outcome、verification、route delta 与全部产物哈希。

## `route`

### 简要定义

为突破特定瓶颈而选择的证明机制与策略路径。

### 规范定义

`route` 说明 proof object、mechanism family、quantifier strategy、依赖、预期桥梁、针对的 bottleneck、创新点、工具、证据边界和 reopen/reset 条件。路线保存可跨 window 累积的研究事实；某次为什么现在采用它属于 `route_decision`，不是路线永久属性。

### 构成字段

route ID/family、对象、机制、量词策略、依赖、目标瓶颈、风险、不蕴含边界、证据、障碍、状态与重开条件。

### 权威等级

可变策略对象；低于 objective 与 verified memory。`route_review` 评估其证据状态，`route_decision` 只决定某个 window/attempt 是否采用它。

### 生命周期规则

可提出、比较、选择、执行、暂停、拒绝、隔离或重开；失败范围必须精确，未找到证明不等于排除路线。

### 允许的变化

新证据可重排路线或生成 successor route；语义实质变化需新 route ID/attempt。

### 禁止的变化

禁止以概率口号替代证据、把 obstacle 写成 refutation、在活动 attempt 内无 reset 偷换路线。

### 不得混淆

不等于 objective、attempt、route family、route review、research map 节点或候选证明。

### 完成关系

路线完成只说明其局部计划已执行/关闭；项目是否完成由 objective 与终局验证决定。

### 机器绑定

route card/hash、route review、历次 route delta、window/attempt route decision 与 attempt-start receipt。

## `ticket`

### 简要定义

给一个 worker/role 的冻结、哈希绑定、范围受限的协作任务记录。

### 规范定义

`ticket` 固定一个角色、问题、输入、工具/调用上限、可写 staging、资源上限、停止规则、失败返回和预期输出。它不是加密签名、capability 或一次性进程 lease；worker 不能据此扩大项目权限或发布权威状态。

### 构成字段

ticket ID、role、bounded question、input pointers/hashes、allowed tools、staging path、resource caps、stop rule、required outputs、failure return、reopen condition。

### 权威等级

host 对 worker 的执行约束；低于 project/Run authority，输出只有经 host validation 才可进入项目。

### 生命周期规则

在 attempt/verification/specialist/repair 前冻结，worker 按输入执行并返回，host 验证后关闭；同一 ticket 不跨语义 reset 复用。repair ticket 是 ticket 的受限子型，不是新顶层对象。

### 允许的变化

未派发前可通过新 ticket 替代；派发后内容不可变，只能返回成功或结构化失败。

### 禁止的变化

禁止调用 Goal/control/launcher/lease 等禁用面、读取未绑定输入、写出 staging 或把 ticket 当授权能力。

### 不得混淆

不等于 task、attempt、route、window queue item、lease、权限 envelope、消息或 worker 本身。

### 完成关系

所需输出满足 schema/hash/范围并经 host 验证时 ticket 完成；worker 自报成功不足够。

### 机器绑定

frozen ticket hash、contract initial-tickets hash、counter snapshot、input/output pointers。

## `research_map`

### 简要定义

把项目权威记忆、路线因果、证据边界、项目术语与按需检索入口组织成导航层的官方研究地图。

### 规范定义

`research_map` 不是历史全文，而是从 authority 派生的 window 边界快照：连接目标、verified milestones/results、失败/障碍、路线证据景观、当前瓶颈、证据规则、项目术语表、资产指针和 retrieval triggers。主地图必须在中心记号与项目内术语首次实质使用前作就地解释，独立术语表再稳定记录定义、项目作用与防混淆边界。它只能总结已有权威，不能补造缺失理由，也不能替未来 window 预选路线。

### 构成字段

map receipt/control、main map、project glossary、evidence rules、route landscape/review、relevant milestones/results、obstacles/failure boundaries、binding bridge、retrieval triggers 与 authoritative pointers。活动 route decision、selected route 和 current/next portfolio 不是 closed map 的构成字段。

### 权威等级

导航/派生层；权威低于目标、promoted memory、verified artifacts 和 route review。官方格式为 `math-research-map/v1`，不是 Skill schema version。

### 生命周期规则

在 window reconciliation 中从晋升后的权威材料统一构建、验证、发布；新发布或重建的地图必须同步重审主地图的首次定义和项目术语表。整个 window 执行期间 source map 冻结。head/authority 改变后旧 map stale 并需重建；关闭状态不携带下一 window 计划。旧发布地图可继续读取或作为已冻结窗口来源，新增术语表门禁不追写关闭历史。

### 允许的变化

可随 promoted memory、verification result、route delta 和 route review 更新节点、边、入口、首次定义和术语表；必须保留来源和 non-implication boundary。

### 禁止的变化

禁止把 map 当证明、让 map 创造验证状态、把 prototype 用于 v13 attempt activation、把 map 版本冒充项目版本，或用术语表替代主地图首次出现处的必要解释。

### 不得混淆

不等于长期记忆目录、route archive、项目索引、cognition snapshot 或普通思维导图。

### 完成关系

地图有效是 window planning 的必要准备；同一 window 的 attempts 绑定同一 source map。地图完整不表示数学目标完成。

### 机器绑定

map root/control/receipt hashes、main map 与 project glossary bytes、objective/head bindings 和官方 validator receipt。

## `tracked_topic_section`

### 简要定义

用户要求在主研究地图中长期保留、并在每次权威地图发布时重新维护状态、进度和排序的项目局部专题小节。

### 规范定义

`tracked_topic_section` 是 `01-主研究地图.md` 中一个带 `research-map-tracked-topic:v1` 标记的二级小节。它绑定稳定的项目局部 `topic_id` 和当次候选 authority manifest SHA-256，并以证据受限文字记录当前状态、已闭合与待闭合桥梁、以及它在当前证据成熟度或地图导航中的相对位置。每次新建或更新地图都必须从完整权威库存重新审查这三项，不得因为专题没有同名新文件就沿用旧值。

### 构成字段

二级标题、唯一 `topic_id`、`authority_manifest_sha256`、状态、进度、排序及其明示比较依据。

### 权威等级

地图导航／阅读层的持久发布义务；低于 `project_objective`、promoted memory、verified evidence、`route_review` 和 `research_authority_head`。

### 生命周期规则

用户在项目中显式登记后，随每次权威地图构建、window reconciliation 或 maintenance rebuild 重新绑定并审查；只有用户明确撤销跟踪义务时才可从当前地图移除。旧发布字节保持冻结。

### 允许的变化

可依新权威证据更新状态、进度、相对排序、小节在主地图中的位置和 manifest 绑定；证据不支持全序时必须保留不可比性。

### 禁止的变化

禁止无证据提升状态、用百分比伪造可比进度、把排序写成成功概率、`selected route`、`why_now` 或下一 window portfolio，也禁止通过改 `topic_id` 逃避未来维护。

### 不得混淆

不等于 route、route review、route decision、milestone、standalone result、task、checkpoint 或一般日志小节。

### 完成关系

三个字段当前且通过结构与语义审核，只能完成该专题的地图发布义务；不完成路线、window 或项目数学目标。

### 机器绑定

`research-map-tracked-topic:v1` marker、topic ID、candidate authority-manifest SHA-256、main-survey bytes、publication validation receipt 和 exact-candidate semantic-review closure。

## `terminal_sufficient_condition_register`

### 简要定义

用户显式要求研究地图维护“充分条件／充分命题”时，对全部非等价终端充分命题、逻辑关系、解决难度部分序和排除项进行哈希绑定的项目局部登记册。

### 规范定义

`terminal_sufficient_condition_register` 是 `tracked_topic_section` 的可选专门化。每个登记命题必须自身直接推出 `project_objective`，或经登记册内有限的 `implies` 路径到达一个直接推出目标的命题；一个命题的合取前提、局部引理、来源恢复、有限计算或单段解析身份不能被拆分冒充多个终端命题。每条仍可展开的研究路径都必须有一个可见的路径级终端命题，完整合取该路径到终局尚缺的桥；上层通用判据或中间 success gate 不能替代它。新发布专题先用一个哈希绑定的共享 `definition` callout 一次性固定可复用对象、记号和约定，再用各自具有描述性标题的 `proposition` callout 陈述完整路线特有假设和终局结论。自足、可移植的单位是共享定义卡加所选命题框，而不是强迫每个框重复展开同一积分、归一化或符号；只复制命题框时，它只是项目内部短式。外部字段列表不能替代定义卡或命题框。每个可见记录必须先有自己的标题，再放机器 marker。每条来源覆盖及排除项都以可解析 Obsidian 链接闭合“路线说明—实际结果或障碍证据—精确失败边界—终端命题”；排除项还要精确说明被排除的候选或中间条件、排除范围和完整路线是否保留，不能把局部不足升级为整条路线失败。历史／支撑子路线可以映射到父路径命题，只有权威证据表明在不改变路线数学身份时仍无法终端，才可映射到排除项。登记册同时保存逐来源候选覆盖、蕴含／等价／不可比关系，并在一个明示、非概率的证据基础上给出具体可执行命题的难度部分序。上层判据仍须以 `criterion_scale` 说明为什么不能和具体路线作同尺度比较。

### 构成字段

schema、topic/project/objective/authority-manifest bindings、coverage claim、difficulty basis、conditions、logical relations、difficulty relations、exclusions、candidate source coverage、shared definition card、visible route/evidence/failure/terminal link closure、explicit exclusion scope and route retention，以及 visible-section marker/path/hash binding。

### 权威等级

研究地图导航／综合层的持久发布义务；低于 `project_objective`、promoted memory、verified evidence、`route_review` 和 `research_authority_head`，不能创造新数学事实。

### 生命周期规则

用户显式登记充分条件专题时创建，随每次权威地图构建、window reconciliation 或 maintenance rebuild 重新绑定并重审。旧登记册字节保持冻结；新候选使用新哈希。后续发布必须比较前一权威地图，只有用户明确撤销时才能移除该义务。

### 允许的变化

可依新权威证据增删或合并命题、更新开放义务、路线映射、逻辑关系、难度依据、部分序与排除项；任何内容变化都要求新的 register hash、可见渲染、结构票据和 semantic-review closure。

### 禁止的变化

禁止把同一命题的多个前提计作多个终端命题、把非终端局部条件标成 terminal、用通用判据或中间 success gate 顶替路径级终端命题、遗漏路线审查中的候选、遗漏 criterion-layer 的难度 disposition、用成功概率或 `selected route` 代替难度依据、强造全序、删除不可比性、静默移除登记义务，或在 Skill/Harness 中硬编码某个真实项目的命题答案。

### 不得混淆

不等于 `tracked_topic_section` 的普通状态／进度／排序字段、route maturity table、route decision、proof obligation checklist、standalone result、必要条件清单或项目完成证书。

### 完成关系

结构和语义审核通过只完成该专题的地图发布义务。即使登记册完整，也不表示任何开放充分命题已经证明，更不表示项目目标完成。

### 机器绑定

`research-map-sufficient-condition-topic:v1` marker、`research-map-sufficient-condition-definitions:v1` marker 与可见定义卡哈希、`math-research-sufficient-condition-register/v1` canonical JSON、topic/objective/manifest hashes、visible entry/exclusion markers、publication validation receipt、prior-map downgrade check 和 exact-candidate semantic-review closure。

## `project_core_cognition`

### 简要定义

每个 attempt 冻结的项目级因果认知快照，用于在有限上下文中保留正确的全局研究理解。

### 规范定义

`project_core_cognition` 从 window 的 frozen source map/head、promoted memory、route review 和该 attempt 的 route decision 派生，包含终局目标、方法定位、已验证方法主链、推导瓶颈、路线选择因果、证据边界、按需检索触发器与 semantic reset 条件。它必须声明尚不存在的 proof objects/certificates，不能把路线优先级写成成功概率，也不能吸收兄弟 attempt 的未结算工作。

### 构成字段

objective、method orientation、key objects、verified method spine、derived bottleneck、route causality、evidence boundaries、retrieval triggers、reset conditions、missing-object declarations。

### 权威等级

attempt 级冻结派生认知；低于 map/memory/evidence authority，高于模型即时自由总结。

### 生命周期规则

attempt 前生成、验证、渲染并冻结 JSON/selected Markdown hashes；整个 attempt 不变，semantic reset 后生成新 cognition。

### 允许的变化

只能在 attempt 之间依据新权威材料生成新版本；budget profile 可选但内容保留顺序受协议约束。

### 禁止的变化

禁止 freehand deliverable、截断关键因果、在 checkpoint/capsule 中暗改、把未知机制写成已存在。

### 不得混淆

不等于永久 objective、research map、长期记忆全集、continuity capsule 或一般项目摘要。

### 完成关系

有效 cognition 使 attempt 可启动和压缩后恢复；它本身既非证明也非项目完成证据。

### 机器绑定

canonical JSON hash、selected rendering hash、window/source map/source head、memory/route-review/route-decision hashes 与 attempt-start receipt。

## `checkpoint`

### 简要定义

在 Run/attempt 事件边界持久记录当前权威执行状态与局部位置的恢复点。

### 规范定义

`checkpoint` 记录项目/Run/window/目标绑定、控制 generation、事件 head、计数器、活动 lifecycle、current queue item/ticket/attempt、局部进度和恢复指针。v13 attempt checkpoint 只能更新变化的局部位置与问题，不能改动冻结认知、路线语义或导入兄弟 attempt 的未结算工作。

### 构成字段

project/Run/window/objective bindings、generation/event head、counters/budgets、current queue item/lifecycle、local progress/questions、capsule/cognition pointers、timestamp。

### 权威等级

持久恢复状态；对当前执行位置权威，但不能凌驾于 Contract、objective、event chain 或 frozen attempt semantics。

### 生命周期规则

在 genesis、attempt start/material progress/pause/handoff 等合法事件后写入；新 checkpoint 追加/替代 active pointer，旧 checkpoint 保留审计。

### 允许的变化

可推进已完成步骤、未决问题、消耗、事件和指针，前提是保持冻结对象与权限。

### 禁止的变化

禁止通过 checkpoint 换 route/objective/mechanism/quantifier/evidence、清零预算、伪造事件或跳过 hash readback。

### 不得混淆

不等于 continuity capsule、Git checkpoint、model summary、attempt end 或 project head。

### 完成关系

checkpoint 使状态可恢复并支持安全续跑；它不是阶段成功或终局完成声明。

### 机器绑定

generation-unique path/hash、event head、objective/Run/cognition/capsule pointers 与 atomic head transition。

## `continuity_capsule`

### 简要定义

为上下文压缩、暂停或接力保存 attempt 局部起点与最新位置的冻结绑定载体。

### 规范定义

`continuity_capsule` 指向同一 window/source map/head、同一 `project_core_cognition` JSON 和 selected rendering hashes、同一 route decision/card/attempt 语义，并保存变化的 local position、open questions、handoff 和 reset directive。它传递连续性，不能创造或修改项目级认知，也不能作为 sibling-attempt 消息通道。

### 构成字段

project/Run/window/attempt IDs、source map/head、objective/cognition/rendering hashes、route decision/pointer、local position、open questions、route sets、handoff/reset directive、generation。

### 权威等级

attempt 局部连续性载体；其引用必须服从 cognition、route、checkpoint 和 event authority。

### 生命周期规则

attempt start 创建初始 capsule；合法 checkpoint 可产生 successor capsule；压缩后重注入完全相同 cognition rendering 加最新 valid capsule。

### 允许的变化

successor capsule 可更新局部位置、问题、进度和合法 route disposition，不改变冻结语义。

### 禁止的变化

禁止在 capsule 内偷换 objective、proof object、mechanism、quantifier strategy、evidence standard、selected route 或因果解释；此类变化必须 semantic reset。

### 不得混淆

不等于 checkpoint、cognition、conversation summary、route card、handoff note 或 project memory。

### 完成关系

capsule 的目标是无语义漂移地恢复/接力 attempt；有效 capsule 不证明任何数学结论。

### 机器绑定

capsule hash、generation、cognition JSON/rendering hashes、route card 与 checkpoint/attempt-start receipts。

## `window`

### 简要定义

从同一研究地图快照启动、默认包含三个差异化 attempt、并以一次全局结算关闭的研究窗口。

### 规范定义

`window` 是当前 v13 的多路线研究周期。它在开始时读取最新 validated `research_map`，冻结 source map/head、三项 `route_portfolio`、queue、预算和停止条件；所有 attempt 完成验证后进入 `window_reconciliation`。中文“一轮研究”“研究窗口”都是它；英文 `round` 只表示预算计数，绝不是 window。

### 构成字段

window ID、source project head/map hashes、portfolio、三个 queue items/attempt bindings、预算、状态、reconciliation receipt 与 closing head。

### 权威等级

Run 内的研究编排边界；它协调 attempt 和发布，但不创造数学权威。

### 生命周期规则

`window_idle -> window_planning -> window_running -> window_verifying -> window_reconciling -> window_idle`。关闭后不保留 active route decision、selected route 或 next-window portfolio。

### 允许的变化

执行顺序和物理 agent 数可变；单 Agent 可串行处理同一队列，多 Agent 可并行。

### 禁止的变化

禁止在窗口中途换 source map/head、扩张 portfolio、让兄弟 attempt 交换未验证产物，或在关闭时预建下一窗口。

### 不得混淆

不等于 Run、attempt、round、route review、conversation turn 或时间周期。

### 完成关系

三个 attempt 均 ready，结算通过且新 map/head 发布后 window 才关闭；关闭 window 不等于完成项目。

### 机器绑定

window ID、source/closing head、source/new map receipts、portfolio/queue/package hashes 与 reconciliation receipt。

## `route_proposal`

### 简要定义

窗口规划时由 agent 基于同一地图快照提出、尚未被采用的候选路线说明。

### 规范定义

`route_proposal` 描述 proof object、mechanism family、quantifier strategy、目标瓶颈、依赖、预期检验和证据来源，供 Host 做语义去重与 portfolio 构造。它不是 route decision，也不因提出而成为活动路线。

### 构成字段

proposal ID、source map/head、proposer role、route fingerprint、targeted bottleneck、dependencies、success/failure gate、evidence refs。

### 权威等级

窗口规划提案；低于 route review、verified memory 和 Host decision。

### 生命周期规则

只在 window planning 产生，经去重后 accepted/rejected/merged；历史可保留审计，不能跨窗口自动激活。

### 允许的变化

采纳前可补充来源或明确 fingerprint；实质改变须新 proposal ID。

### 禁止的变化

禁止伪造证据、用改名绕过去重、把 proposal 当 route/map 事实或下一窗口计划。

### 不得混淆

不等于 route、route card、route decision、ticket 或自由聊天中的想法。

### 完成关系

proposal 被接受只表示可进入 portfolio，不表示 attempt、路线或项目成功。

### 机器绑定

proposal hash、source map/head、fingerprint、evidence refs 与 portfolio inclusion decision。

## `route_portfolio`

### 简要定义

一个 window 开始时冻结的三个语义上有实质差异的路线工作项集合。

### 规范定义

`route_portfolio` 从 route proposals 构造，三个成员必须在 `(proof_object, mechanism_family, quantifier_strategy)` 上形成非重复组合；不足时用 route discovery 覆盖未探索的方法空间，不制造改名重复。它只服务当前 window。

### 构成字段

portfolio ID、window/source bindings、exactly three member IDs/fingerprints、dedup evidence、coverage rationale、accepted-at timestamp/hash。

### 权威等级

Host 的窗口规划决定；不改变 route 的数学证据等级。

### 生命周期规则

在 window start 前冻结，三个 attempt 各绑定一项；window close 后清空活动状态，仅保留历史。

### 允许的变化

冻结前可因去重或缺失字段重建；冻结后不得替换成员。

### 禁止的变化

禁止跨 window 复用为当前计划、包含语义重复项、在上一窗口结算时预生成下一 portfolio。

### 不得混淆

不等于 route review、路线优先级列表、next-window plan 或三个 ticket 的简单集合。

### 完成关系

portfolio 完整只允许窗口启动；项目完成仍由 objective 和终局证据决定。

### 机器绑定

portfolio hash、window/source hashes、member proposal/route fingerprints 与三个 route decisions。

## `route_review`

### 简要定义

依据已存档证据全局审视路线状态、障碍和重排条件但不创造数学的记录。

### 规范定义

`route_review` 汇总已验证结论、失败边界、障碍、route delta 和 reopen conditions，使路线景观自洽。它可以记录比较和 reranking conditions，但不得选择未来 window 的路线或生成新数学。

### 构成字段

review ID/version、source authority、route assessments、comparisons、bottlenecks、reranking conditions、evidence refs、`new_math_performed=false`。

### 权威等级

权威策略审视记录；低于数学证据，高于 map 中的派生摘要。

### 生命周期规则

window reconciliation 中更新；下一 window planning 读取最新 review 后另行作决定。

### 允许的变化

新验证证据和 scoped route delta 可改变状态、排序与重开条件。

### 禁止的变化

禁止产生 theorem、把 obstacle 升格为 refutation、写 selected route 或 next portfolio。

### 不得混淆

不等于 route decision、route portfolio、strategy audit、window reconciliation 或 research map。

### 完成关系

review 完成只表示路线景观已整理，不表示窗口或项目完成。

### 机器绑定

review schema/hash、source package/evidence refs、window reconciliation 与 map receipt。

## `route_decision`

### 简要定义

窗口开始时为一个具体 attempt 选择一条路线并说明为什么现在选择它的冻结决定。

### 规范定义

`route_decision` 绑定 window/source map/head、portfolio member 和一个 selected route，记录 `why_now`、相对其他成员的理由、目标瓶颈、不确定性、成功/候选失败门及重排条件。它只在所属 window/attempt 内有当前控制效力。

### 构成字段

decision ID、window/attempt/source bindings、selected route/fingerprint、why_now、alternative comparison、targeted bottleneck、uncertainty、gates、evidence refs。

### 权威等级

Host 的 attempt 启动决定；不能覆盖 route review 或数学证据。

### 生命周期规则

window planning 生成，attempt start 冻结，window close 后失去活动效力但保留历史。

### 允许的变化

冻结前可因验证失败重建；冻结后语义改变必须结束 attempt 并由未来 window 重新决策。

### 禁止的变化

禁止写入 closed research map 作为下一步命令、跨 window 续用或把优先级写成成功概率。

### 不得混淆

不等于 route、route proposal、route review、portfolio 或 selected-route map field。

### 完成关系

decision 有效只允许 attempt 启动；路线执行和项目完成另行判断。

### 机器绑定

decision hash、window/source/portfolio/route/cognition/ticket 与 attempt-start receipt。

## `route_delta`

### 简要定义

一个 attempt 对路线事实状态提出的、范围明确且等待窗口结算采纳的增量记录。

### 规范定义

`route_delta` 记录本 attempt 对证据边界、障碍、失败候选、已验证副产物、reopen condition 或路线状态的影响，并明确 `cannot_imply`。它是事实更新提案，不是路线选择或下一步计划。

### 构成字段

delta ID、attempt/window/route、claims、evidence/verification refs、scope、cannot_imply、obstacle/failure classification、reopen condition。

### 权威等级

attempt reconciliation package 内的结算输入；经 window reconciliation 采纳后才改变权威 route review/map。

### 生命周期规则

ATTEMPT_END 形成，结算时 accepted/rejected/partially_applied，原字节保留。

### 允许的变化

提交前可随验证结果收窄；提交后只能由结算产生新的采纳记录。

### 禁止的变化

禁止越过验证晋升结论、把 candidate FAIL 扩大为 route FAIL、携带 next-route 指令。

### 不得混淆

不等于 route decision、route review、map patch、checkpoint 或 successor plan。

### 完成关系

delta 被采纳只更新路线状态；不直接完成 attempt、window 或项目。

### 机器绑定

delta hash、attempt package、verification/evidence pointers 与 reconciliation application receipt。

## `attempt_outcome`

### 简要定义

ATTEMPT_END 对该 attempt 执行终态的封闭分类。

### 规范定义

`attempt_outcome` 只能是 `candidate_found`、`no_candidate`、`inconclusive`、`awaiting_input` 或 `failed`。它描述执行结果，不等于 verifier verdict、路线状态或数学真值。

### 构成字段

attempt/window identity、closed outcome value、candidate/verification pointers、scope、completed-at 与 artifact refs。

### 权威等级

attempt 生命周期权威；数学结论仍服从 verification/promotion。

### 生命周期规则

ATTEMPT_END 冻结；受限 repair 后由新 candidate/verification 形成最终 package，不覆写旧结果字节。

### 允许的变化

仅在结束提交前按事实选择闭集值；发布后更正需新事件和保留原记录。

### 禁止的变化

禁止把 PASS/FAIL 当 outcome，把 no_candidate 当 route refutation，或省略 awaiting_input/failed 的边界。

### 不得混淆

不等于 verification result、route delta、ticket completion、window state 或 project completion。

### 完成关系

outcome 冻结是 attempt ready 的必要条件；任何单独 outcome 都不足以完成 window/项目。

### 机器绑定

immutable outcome hash、attempt/window/ticket、candidate/verifier pointers 与 reconciliation package。

## `verification_result`

### 简要定义

对一个冻结候选及完整依赖进行独立检查所得的 `PASS`、`FAIL` 或 `INCONCLUSIVE`。

### 规范定义

`verification_result` 只覆盖其绑定 candidate/claim、scope、quantifiers 和 dependencies。优先由未参与生成的 verifier 执行；无 subagent 时可用隔离上下文的串行 verifier role 并记录 `single_agent_fallback`，但不得冒充不同物理 agent。

### 构成字段

verification ID、verifier role/independence mode、candidate/dependency hashes、scope/quantifiers、verdict、earliest error/doubts、completed-at。

### 权威等级

数学晋升门禁；PASS 使覆盖内容 promotion-eligible，但最终晋升由 Host/window reconciliation 决定。

### 生命周期规则

每个 candidate hash 一份结果；repair 产生新 candidate hash 和新 verification。结果字节不可覆写。

### 允许的变化

只能对新候选或新依赖重新验证；可记录更强独立性，但不能回写原 verdict。

### 禁止的变化

禁止用 FAIL 否定未覆盖整条路线、用 INCONCLUSIVE 充当失败或让 solver 自报 PASS。

### 不得混淆

不等于 attempt outcome、terminal audit、evidence grade、route review 或 reviewer comment。

### 完成关系

PASS 是数学晋升的必要条件之一；项目完成还需 objective coverage、terminal audit 和发布授权。

### 机器绑定

verification artifact hash、candidate/dependency pointers、ticket/role、independence mode 与 package/promotion receipt。

## `attempt_reconciliation_package`

### 简要定义

一个 attempt 交给 window reconciliation 的哈希绑定完整结算输入。

### 规范定义

`attempt_reconciliation_package` 统一指“大纲中的窗口结算输入、窗口结算包、结算提案”。每个 attempt 只产生一个最终 package，包含 outcome、artifacts、verification、route delta、obstacles、cannot_imply、surviving results 和 reopen conditions；它不发布项目级 memory/map。

### 构成字段

package ID、window/attempt/source bindings、outcome、artifact/evidence/verification hashes、route delta、result classifications、obstacles、cannot_imply、reopen conditions、ready state。

### 权威等级

attempt 结束权威与 window reconciliation 输入；低于完成后的 promoted memory/map/head。

### 生命周期规则

在验证/受限 repair 结束后冻结，标记 `ready_for_window_reconciliation`，结算消费但不改写原字节。

### 允许的变化

冻结前可加入必要 verification；冻结后只能创建 superseding package 并保留 lineage。

### 禁止的变化

禁止包含 successor route/ticket/attempt、next portfolio、未绑定 artifact 或未经验证的 promotion 声明。

### 不得混淆

不等于整个 window 的 reconciliation receipt、attempt outcome、checkpoint、map patch 或 project head。

### 完成关系

三个 package 全部 ready 是 window reconciliation 前提；单个 package 不关闭 window。

### 机器绑定

package hash、source map/head、window/attempt、outcome/verification/delta/artifact hashes 与 reconciliation receipt。

## `window_reconciliation`

### 简要定义

窗口末尾统一验证、晋升研究资产、更新路线景观并发布新研究地图和项目头的全局转换。

### 规范定义

`window_reconciliation` 在三个 packages ready 后运行：核验绑定，promotion eligible evidence/memory，应用 scoped route delta，分类副产物，执行 `new_math_performed=false` 的 route review，重建/验证 research map，最后发布 project head。它不为未来 window 选路。

### 构成字段

window/source/closing head、three package pointers、promotion decisions、delta applications、route review、new map/validation receipts、queue-clear proof。

### 权威等级

Host 拥有的窗口级发布转换；只有它可以把 attempt-local 候选晋升为项目级权威。

### 生命周期规则

三 attempt ready 后开始，全部门禁通过后一次关闭 window；失败则保留原 head 和可恢复 staging。

### 允许的变化

可拒绝、部分采纳或收窄 package 提案，只要保留理由和证据；可重建自洽 map。

### 禁止的变化

禁止创造新数学、改写原 evidence/package、跳过 verification、发布半结算 head 或生成 next-window portfolio。

### 不得混淆

不等于 route review、ATTEMPT_END、terminal audit、map validation 或一般总结复盘。

### 完成关系

成功后 window 关闭并回到 window_idle；项目仅在终局门禁也通过时完成。

### 机器绑定

reconciliation plan/receipt hashes、three packages、promotion/delta/review/map receipts 与 expected-old/new head。

## `window_queue_item`

### 简要定义

持久窗口队列中绑定一个 attempt 工作项及其执行/验证状态的编排记录。

### 规范定义

`window_queue_item` 管理当前 window 的一个 portfolio member，从 queued 到 attempt/verification/package ready。它引用 immutable tickets，但本身不是 ticket、capability 或 lease；恢复表示按 head/状态重新入队，不是“恢复租约”。

### 构成字段

queue item ID、window/portfolio/attempt/route decision、solver/verifier ticket pointers、dependencies、state、budget、staging/package pointers。

### 权威等级

Host 的编排状态；不授予 worker 权限或数学权威。

### 生命周期规则

window planning 创建，经历 queued/dispatched/solver_terminal/verifying/ready，window close 清空活动队列并保留历史。

### 允许的变化

Host 可在合法 readback 后重排执行顺序、重入队或绑定 verifier；agent 数变化不改变身份。

### 禁止的变化

禁止把 queue item 当 ticket/lease、跨 window 复用、扩张工具权限或绕过 package/reconciliation。

### 不得混淆

不等于 task、ticket、attempt、agent slot、process lease 或 verification queue 的可视列表。

### 完成关系

item ready 只表示对应 attempt 可参加结算；三个 ready 才允许 window reconciliation。

### 机器绑定

queue item hash、window/portfolio/attempt/ticket pointers、state events 与 package hash。

## `research_role`

### 简要定义

当前窗口协作中的封闭逻辑职责：`lead`、`verifier`、`specialist`。

### 规范定义

`lead` 始终存在并拥有编排连续性；`verifier` 检查冻结候选但不拥有 promotion/Goal authority；`specialist` 只解决范围受限的局部问题。角色不等于物理 agent 数。没有 subagent 时由 lead 串行承担所需角色并记录隔离方式；不必占满可用 subagent。

### 构成字段

role value、actor/session identity、ticket、scope、independence mode、allowed actions、forbidden authority。

### 权威等级

协作职责分类；所有角色都低于 Goal Host/project authority。

### 生命周期规则

lead 随 window/attempt 保持；verifier/specialist 按 ticket 激活并在交付后结束。角色可由同一 agent 分时承担但记录必须真实。

### 允许的变化

可按资源派生更多同角色 worker 或退化为单 Agent 串行，只要 ticket/隔离/权限不变。

### 禁止的变化

禁止 specialist 选路或晋升证据、verifier 修改候选、任何 worker 冒充 Goal Host，或虚报物理独立性。

### 不得混淆

不等于 agent、ticket、thread、queue item、Goal Host 或固定三人编制。

### 完成关系

角色任务完成不等于 attempt/window/project 完成；只满足对应 ticket/verification 门禁。

### 机器绑定

ticket role、actor/session ID、independence mode、access log 与 completion artifact。

## `semantic_reset`

### 简要定义

attempt 冻结语义发生实质变化时结束原 attempt、保留其结果并等待未来重新规划的转换。

### 规范定义

当 proof object、mechanism family、quantifier strategy、evidence standard、selected route 或核心因果解释改变时触发 `semantic_reset`。它关闭当前 attempt 并记录 directive/原因；不会在同一 window 中私自替换 portfolio member，也不会自动启动 successor。

### 构成字段

reset ID、attempt/window、changed semantic fields、reason/evidence、preserved artifacts、cannot_imply、reopen condition。

### 权威等级

attempt 语义边界事件；不能改变 project objective 或权限 envelope。

### 生命周期规则

checkpoint/strategy audit 发现触发条件后记录，ATTEMPT_END 冻结为 package；未来 window planning 决定是否重开或采用别路。

### 允许的变化

允许保留与新路线无关的已验证事实和精确失败边界。

### 禁止的变化

禁止把换记号/工具/局部引理冒充 reset，或借 reset 绕过 window portfolio、预算和验证。

### 不得混淆

不等于 checkpoint、route rename、repair ticket、route decision、project fork 或 next-attempt command。

### 完成关系

reset 只诚实结束一个不再保持语义的 attempt；不关闭 window 或证明路线失败。

### 机器绑定

reset directive/event hash、changed-field fingerprint、attempt package 与 future route proposal references。

## `result_map_role`

### 简要定义

已验证研究结果在项目地图中的可见性分类：`milestone`、`standalone_result` 或 `route_local`。

### 规范定义

`milestone` 改变全局局面或路线排序；`standalone_result` 具有独立复用价值；`route_local` 只服务一条路线历史。分类只决定地图组织和可见性，不改变数学真值、scope 或 evidence grade。

### 构成字段

result ID、role value、scope、objective relation、reusable value、cannot_imply、evidence/verification refs。

### 权威等级

window reconciliation 的组织决定；低于 verified result 本身的数学权威。

### 生命周期规则

结果通过 verification 后在 reconciliation 分类；新证据可重分类但保留历史和不重复正文。

### 允许的变化

可因全局影响或复用价值变化调整可见性，一个结论可有关联节点但避免重复权威正文。

### 禁止的变化

禁止用分类提升证据等级、把 route-local observation 写成 theorem、或因目标未解而丢弃 verified byproduct。

### 不得混淆

不等于 attempt outcome、verification result、evidence grade、route status 或完成等级。

### 完成关系

任何 map role 都不能单独完成项目；它只决定结果如何进入长期研究资产。

### 机器绑定

classification record/hash、result/verification/memory pointers 与 map node/index bindings。

## `objective_commitment`

### 简要定义
六字段 objective core 的规范字节 SHA-256。
### 规范定义
永久数学身份；不随元数据、路径、Run 或 schema 变化。
### 构成字段
六个有序字段、规范字节、SHA-256。
### 权威等级
不可变项目身份。
### 生命周期规则
genesis 或迁移时创建，之后不变。
### 允许的变化
仅新项目或显式 fork。
### 禁止的变化
禁止 Unicode 规范化、重排 assumptions 或混入元数据。
### 不得混淆
不等于旧 objective 文件哈希、project head 或 Goal。
### 完成关系
绑定完成候选但自身不证明完成。
### 机器绑定
objective pointer、所有 heads、map、attempt 与 receipts。

## `research_authority_head`

### 简要定义
已提升研究权威的独立 head。
### 规范定义
只承载 memory、route review、map 与 source integrity。
### 构成字段
generation、memory、review、map、source integrity。
### 权威等级
项目数学权威。
### 生命周期规则
仅 promotion、reconciliation 或 invalidation 推进。
### 允许的变化
经验证的证据提升或隔离。
### 禁止的变化
禁止由 checkpoint 或 ATTEMPT_END 推进。
### 不得混淆
不等于 execution state 或 project CAS head。
### 完成关系
承载最终数学候选与审计绑定。
### 机器绑定
project.json pointer 与 candidate manifest。

## `execution_state_head`

### 简要定义
执行生命周期的独立 head。
### 规范定义
承载 window、attempt、queue、verification、closing、maintenance 与 audit。
### 构成字段
generation、phase、window、attempts、queues、audits。
### 权威等级
执行控制权威，不提升数学结论。
### 生命周期规则
每个有效执行转换可推进。
### 允许的变化
检查点、激活、closing、结算准备与维护。
### 禁止的变化
禁止暗中改变研究权威。
### 不得混淆
不等于 research authority。
### 完成关系
记录 terminal audit 与 pending Goal 状态。
### 机器绑定
project.json pointer 与 transition plan。

## `window_source_binding`

### 简要定义
window 的冻结来源联合。
### 规范定义
只能是 validated_map 或一次 genesis_objective。
### 构成字段
kind、source pointers/hashes、consumed 标志。
### 权威等级
window 来源权威。
### 生命周期规则
激活前冻结，window 关闭时清空。
### 允许的变化
下一 window 可从新 validated map 建立。
### 禁止的变化
迁移项目禁止 genesis，genesis 禁止重复消费。
### 不得混淆
不等于 route decision。
### 完成关系
保证 attempt 从合法权威起步。
### 机器绑定
三份 prepare、activation receipt 与 cognition。

## `prepare_record` / `window_activation`

prepare record 是非权威候选；window activation 是一次 CAS 同时使三份已验证 prepare 可达。第三份失败时零 attempt，废弃 ID 不复用。

## `attempt_closing`

### 简要定义
候选冻结与验证边界阶段。
### 规范定义
先以 `attempt_package_preflight_receipt` 证明 package 机械闭包，再冻结 outcome、candidate、dependencies、artifact refs 并等待验证或一次同语义 repair。
### 构成字段
outcome、candidate、dependencies、artifact refs、package preflight receipt、verification、repair count。
### 权威等级
attempt 生命周期权威。
### 生命周期规则
semantic reset 或 candidate freeze 进入，ATTEMPT_END 退出。若整个三-attempt window 恰好停留在纠正版安装前形成的无 receipt `verification_queued` 状态，可由一次性原子 `QUEUED_PREFLIGHT_REBIND` 同时撤销三张旧 verifier queue item、绑定三份新 preflight closure 并返回 closing；随后必须签发新 verifier tickets。
### 允许的变化
一次 verifier-directed 同语义 repair；repair 的新候选必须先形成新的 package preflight receipt。
### 禁止的变化
禁止换 source、route 或 semantic fingerprint；兼容重绑禁止部分执行、重复执行、修改 counters/repair count，或用于已有 receipt、repair、verification result 的 attempt。
### 不得混淆
不等于 checkpoint 或新 attempt。
### 完成关系
只完成 attempt，不完成 window/project。
### 机器绑定
closing head、package preflight receipt、verification queue 与 package。

## `attempt_package_preflight_receipt`

### 简要定义

候选冻结前对一个 attempt 输出包的规范字节、完整 inventory 和交叉哈希闭包进行确定性验证的 PASS 收据。

### 规范定义

`attempt_package_preflight_receipt` 由本地 finalizer 在 fresh same-volume staging 中完成 JSON canonicalization、package-local pointer 回填、Markdown SHA 检查和 manifest 生成后最后写出，再由独立只读 checker 重算。它绑定 attempt、package root、candidate、ordered dependencies、artifact refs、manifest、完整 inventory 和 byte budget。它只证明机械闭包，不进行数学、来源、量词、scope 或 evidence 判断，也不替代 `verification_result`。

### 构成字段

schema、attempt ID、PASS status、package root、candidate、dependencies、artifact refs hash、package inventory hash、artifact manifest、file/byte counts、maximum bytes、finalizer version。

### 权威等级

候选冻结前的确定性机械门禁；低于独立数学 verification，但对 `ATTEMPT_CLOSE`、repair requeue 和 `ATTEMPT_END` 的字节闭包是强制条件。

### 生命周期规则

raw solver output 保持不变；finalizer 在新 staging 中生成一份 receipt。任何 candidate、dependency、artifact ref 或 package byte 改变都要求新 staging 和新 receipt。closing commit 后 receipt 与 package 一同不可变。唯一兼容例外不是 receipt 复用，而是 `QUEUED_PREFLIGHT_REBIND`：对纠正版安装前已经排队的同一窗口三项，一次性把三份 fresh receipt 闭包重绑到 closing 并废弃全部旧 verifier tickets；该转换不改变数学语义、计数或 repair count，且成功后不可再次适用。

### 允许的变化

冻结前可重新运行 finalizer 生成一份全新 package；同一语义 repair 可生成新 candidate、dependencies、artifact refs 和 receipt。

### 禁止的变化

禁止原地修补已冻结 package、复用旧 receipt、让 receipt/manifest 自引用、用 preflight PASS 宣称数学 PASS，或把冻结前机械修正计作 `LIMITED_REPAIR`。

### 不得混淆

不等于 `verification_result`、attempt outcome、commit plan、artifact manifest、computation record、source review 或 terminal audit。

### 完成关系

receipt PASS 只允许候选进入 closing/verification；它不能使 attempt promotion-eligible、关闭 window 或完成项目。

### 机器绑定

`math-research-attempt-package-preflight/v1` canonical bytes、receipt pointer/hash、package inventory、manifest、closing candidate/dependencies/artifact refs 与 commit Harness readback。

## `scoped_review_gate`

### 简要定义
范围化的阻断转换门禁。
### 规范定义
由指定 lifecycle 拥有，直到证据满足 release condition。
### 构成字段
scope、owner、blocked transition、dependency closure、release condition、evidence refs。
### 权威等级
跨生命周期安全门禁。
### 生命周期规则
随缺口创建，随绑定证据释放。
### 允许的变化
缩小依赖闭包需证据。
### 禁止的变化
禁止当作 lifecycle state 或无证据清除。
### 不得混淆
不等于 maintenance phase。
### 完成关系
项目级 gate 阻止 activation/completion。
### 机器绑定
execution head 与 release receipt。

## `maintenance_reconciliation`

### 简要定义
迟到验证与来源完整性的非新数学结算。
### 规范定义
确认、隔离或失效既有权威并传播依赖闭包。
### 构成字段
late verification、source status、dependency closure、quarantine、publication。
### 权威等级
维护型 authority transition。
### 生命周期规则
maintenance phase 内完成。
### 允许的变化
接受迟到 PASS 或隔离失权证据。
### 禁止的变化
禁止新数学或改写关闭 window 历史。
### 不得混淆
不等于 window reconciliation。
### 完成关系
可恢复 activation eligibility，不能自行完成目标。
### 机器绑定
maintenance receipt、source review 与双 heads。

## `map_semantic_review`

### 简要定义

研究地图每次新建或更新时，由空白上下文 fresh subagent 对精确候选执行的独立语义发布审核。

### 规范定义

`map_semantic_review` 由冻结 packet、绑定 ticket、封闭 result 和最终 closure 构成。它证明候选地图对完整研究权威清单和八类综合职责作了证据受限、数学诚实的全局综合；它不证明新数学，也不替代结构验证。

### 构成字段

协议与候选哈希、可见树 inventory、authority inventory/manifest、结构票据、作者与 reviewer principal、fresh-subagent dispatch、至多三轮 lineage、修复映射、逐项覆盖、八类 synthesis 结果、最终 verdict 与未决项。

### 权威等级

研究权威发布门禁；只有 `math-research-map-review-closure/v1` 对最终精确候选的 PASS 才有接受权威。

### 生命周期规则

每轮 reviewer 必须不同于作者和此前 reviewer，且不得编写或修改地图。`FAIL|INCONCLUSIVE`、subagent 不可用或三轮无 PASS 均保留旧研究权威并进入现有 `review_required`/reconciliation failure 路径。

### 允许的变化

作者可按不可变 findings 调整候选，或 Host 可按 retrieval request 增加最小证据切片；两者都必须创建新哈希、packet、ticket 和 reviewer。

### 禁止的变化

不得使用薄 PASS、非空指针、重复 reviewer、继承作者上下文、reviewer 修图、`single_agent_fallback` 或旧结果覆盖新候选。

### 不得混淆

不得与研究地图结构验证、尝试候选数学验证、terminal audit、普通代码审查或 lifecycle state 混淆。

### 完成关系

它只完成一次精确地图候选的发布审核；不完成项目目标，也不证明一般能力提升。

### 机器绑定

`scripts/map_semantic_review_v1.py`; `references/map-semantic-review-v1.md`; `semantic_review_receipt`; `math-research-map-review-packet/v1`; `math-research-map-review-ticket/v1`; `math-research-map-review-result/v1`; `math-research-map-review-closure/v1`.

## `completion_publication_pair`

### 简要定义
数学完成发布与 Goal 控制确认的两步握手。
### 规范定义
冻结 terminal summary 与 completion plan，fresh-check Goal 后发布 immutable completion head；readback 后再次 fresh-check Goal 并只更新 Goal 控制面。
### 构成字段
completion head、永久 pending flag、两次 fresh Goal check、同一 Goal completion call。
### 权威等级
终局项目与控制面握手。
### 生命周期规则
三类 terminal audit PASS 后一次执行。
### 允许的变化
项目内不允许任何后续变化；Goal 更新失败时只可重试同一 Goal completion call。
### 禁止的变化
禁止 partial result、Goal-only completion、清除 pending、项目内 acknowledgement 或任何 final-head 后写入。
### 不得混淆
不等于单一 CAS。
### 完成关系
两步完成后 Goal 才可报告 complete。
### 机器绑定
final authority/execution heads、audit receipts；Goal completion 只在产品控制面发生，不回写项目。
