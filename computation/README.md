# Computation layer

计算任务由 `$math-science-computation` 执行，并以 `jin-math-computation-handoff/v1` 绑定 Project、Window、Attempt、Claim 和 objective commitment。

`queue/` 只保存待执行或可恢复的计算工作描述；大产物不得无审查直接提交。完整运行和 CI smoke reproduction 必须分开。
