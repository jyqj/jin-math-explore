# Knowledge network

`knowledge/nodes/` 存放需求驱动的 `K-XXXX.json` 知识节点，用于跨 Project 的定义、方法、先修关系、来源地图和共享缺口导航。

## Authority boundary

知识节点不是数学真相的独立 authority：

- `reference_only` 只表示已记录来源与适用范围；
- `source_audited` 只表示来源/表述经过审计；
- `independently_verified` 必须同时绑定现有 `S-XXXX` shared result 与 receipt；
- 任何节点都必须写明 `cannot_imply`；
- Project 使用节点时仍需检查定义、假设和量词是否与当前 objective 一致。

## When to add a node

仅在真实候选/Project 需要、多个任务需统一约定、已审计资产可复用，或共享基础缺口需要分派时添加。不要把教材章节或百科目录整体搬入仓库。

机器契约见 [`schemas/knowledge-node.schema.json`](../schemas/knowledge-node.schema.json)，完整策略见 [`docs/knowledge-architecture.md`](../docs/knowledge-architecture.md)。
