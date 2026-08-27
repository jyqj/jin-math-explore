# Resource policy

## 分层预算

研究计划必须显式保留以下资源类别，不能把全部能力耗在求解：

- source/frontier scouting；
- solver windows；
- independent verification；
- computation；
- reconciliation/map review；
- protocol maintenance。

具体比例由实际运行数据决定，不写死为数学规则。任何时刻都应优先偿还会阻塞权威提升的 verification debt 和 source-integrity debt。

## 并发

- 不同 Project 可并行。
- 同一 Project 同时最多一个权威活动 window。
- 一个 window 的三个 attempts 可并行，但使用独立 staging。
- 长计算必须具有进程标识、heartbeat、资源边界、原子 checkpoint 和幂等恢复。
- Tool timeout 后先确认原进程是否仍在运行，禁止不确定取消状态下重复启动全量计算。

## 停止和 Park

运行时间长不是自行停止的充分理由。可 Park 的原因包括：

- 明确资源不可用；
- 来源或定义未解决；
- 重复相同失败机制且没有新 proof object；
- 依赖共享结果尚未验证；
- 用户暂停。

Park 不改变数学状态，且必须记录 reopen condition。
