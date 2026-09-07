# CP-ERR-0008：G1/G2 显式下界替换

**reference-only；solver proof candidate；尚未独立验证。** 关联 [#92](https://github.com/jyqj/jin-math-explore/issues/92)，承接 [PR #89](https://github.com/jyqj/jin-math-explore/pull/89)，此前文件不变。

本轮将有限小素数处理与实际质量换基用于**原始截断序列上的 G1/G2 下界**。
使用 BJS v6 的显式下界和经典绝对 BV，不依赖未知 C_s、L_eta，也不依赖前轮待验证的加权 BV 候选。
完整保留 P0 的水平成本、d=1 的共同质量误差，以及主因子可能为负时的方向。

得到的加权契约为

```text
(3G1+G2)/S_N >= 3k1+k2 - [1760/21*epsilon0 +45*q_a+10*q_b
                          +19734/25*epsilon+60*C_BV*log(N)^(3-A0)].
```

实际重算五个固定核，共 **20,480 个中点**。新选 rho=10^-6 时，保守主系数下界为
**k1>=14.877114、k2>=9.11587009**，均保住原显示目标；对应 BV 指数余量比旧 rho=10^-8 大 **100倍**。
代价是 G2 主系数的安全余量稍小，不是数值系数与实际 N0 的双重改善。rho=2*10^-6 已不能保住该固定核比较目标，其失败也被保存。

[完整推导](proof.md) · [逐项契约](contracts.json) · [既有积累](prior-work.json) · [来源与信任边界](source-lock.json) · [误差交接](error-handoff.json) · [独立审查任务](verification-ticket.md)。

## 复算

在本目录运行，Python>=3.10、mpmath==1.3.0：

```sh
python check_lower.py --compute       # 重算全部五个积分并对比 results.json
python check_lower.py --check         # 12个哈希、有限回归及22个负面控制；不重算积分
python -O check_lower.py --self-test  # 有限检查不依赖 assert
python check_lower.py --require-global # 必须退出1
```

[results.json](results.json) 保存逐项区间和解析余项；[validation.json](validation.json) 保存 **10,106项有限检查**。
[计算记录](computation-record.json) 和 [计算交接](computation-handoff.json) 记录实际命令与范围。

这是有完整推导和计算证书的局部候选。BJS 原定理/常数未独立重建，原 C_s 审计仍未完成；
巨大 P0 未枚举，有效数值 N0、完整十二项组合和哥德巴赫猜想均未证明。旧全局账本不变。
下一任务是 G4/G5 提取单素数上界的同类替换，先处理实际质量换基的汇总。
