# Completion policy

## Project 完成候选

完成候选必须：

- 精确绑定不可变 objective；
- 覆盖 statement 的完整 domain 和 quantifier order；
- 明示全部 assumptions；
- 绑定完整 proof/result/dependency bytes；
- 处理所有 material `cannot_imply` 和 unresolved；
- 对工具结果提供可复现记录和适当证据等级。

## 三个终局审计

同一冻结候选分别接受：

1. `quantifier_coverage`；
2. `strategy_soundness`；
3. `tool_reproducibility`。

三者必须在隔离上下文中对相同候选 PASS。任何非 PASS 都不能发布完成；coverage failure 保留可靠局部结果，soundness failure 必须隔离受影响 authority。

## 永久关闭

终局发布后：

- `project_complete=true`；
- 项目数学 head 永久不可变；
- 不写入“完成确认”型后续项目提交；
- Goal/运营系统失败时只重试控制面动作，不重跑或修改数学候选；
- 目标语义变化创建新 Project 或显式 fork。
