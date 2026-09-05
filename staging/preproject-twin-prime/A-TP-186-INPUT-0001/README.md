# A-TP-186-INPUT-0001：第一轮实际尝试

协调 Issue **#38**；基线 **#36 / PR #37**；角色 **solver**。本包保存于独立分支 `attempt/preproject-twin-prime/186-input-01`，不改动基线、不创建 Project、不提升数学 authority。

## 已实际取得的结果

1. 从 Katz 与 FKM 原始定理推导到可读的两个有限域输入规格，核对了常数、非零量词、A=B 与 p=2 的边界；实际 Lean 证明模块仍未能读出。
2. 将数值输入展开成104个外层界、45个内层界和3个cap界；对全部97行预算做了精确有理数检查。
3. 构造了略紧的新损失上界 **0.000696075048575236**，旧值为 **0.000696075110**；在相同积分假设下得到保证余量 **0.0000233604684209770…**。
4. 用逐项 AM-GM 加整数平方根界证明：固定这些积分表和系数，仅继续调整正 Young 参数的剩余可改善量小于 **5×10^-17**。这条狭窄但可证的边界说明下一步不应继续消耗在舍入微调上。
5. 检查了原40元组的全部可容许性条件；导出带符号扰动预算；五种错误输入自测均被拒绝。

以上不是新素数间隔纪录，也没有验证全部152个原始积分不等式。小幅优化只作用于它们成立时的算术组合。

## 文件

- `input-audit.md`：外部定理 → 数学规格的推导及访问限制。
- `arithmetic-certificate.md`：条件证书、最优性边界、扰动预算、tuple证书。
- `inputs.json`、`check_certificate.py`、`results.json`：可复现的原表、新参数和精确结果。
- `source-lock.json`：固定 commit / blob、读取定位、未获得的原始哈希。
- `computation-record.json`、`computation-handoff.json`：实际执行记录和 preproject 交接。
- `attempt.json`：候选分级、依赖、未闭合事项和冻结文件哈希。

## 复现

```sh
python3 -B check_certificate.py --check
python3 -B check_certificate.py --self-test
```

Python标准库足够。比较全用任意精度整数和 Fraction；小数只供显示。未执行原定制-FLINT积分程序或 Lean 构建。未运行仓库全量CI。

## 下一步与状态

本包的 solver 范围结果等待隔离 verifier；完整输入审查与186定理状态仍为 **INCONCLUSIVE**。下一实际数学工作应转向原始152个输入的证书覆盖，或者更换试验函数/支持域，而不是把本次微小算术增益包装成新的间隔结论。

正式 computation-handoff/v1 需要真实 P-XXXX 和 objective 文件；本项目尚未 genesis。本包诚实记录 preproject 交接，不能冒充生产 Project bridge 的验证通过。未创建 merge-intended PR；冻结 attempt 通过 Issue 交给独立验算，后续整合需合法 authority 路径。
