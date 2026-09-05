# 孪生素数第二轮：152项数值输入桥接

**Attempt** `A-TP-186-BRIDGE-0002` · **Issue** #44 · **日期** 2026-09-05  
**角色** solver；结果为待独立验证的候选，不是 verifier receipt。

## 本轮结果

建立完整152目标表与可执行的有理端点检查器；明确新总余量PASS与固定Lean输入是不同条件，并用可复现合成反模型分离它们。另核对10段cell掩码、48个组字段、61个low裁剪，证明并检查内部mask嵌套和face径向上包络。

| 层次 | 本轮状态 |
|---|---|
| 152目标与97任务的有限编号、数值方向 | 已生成并结构检查 |
| 有理端点传递、齐次性、mask/face局部引理 | proof_candidate；文中给出证明 |
| 合成数据反模型、13种破坏测试 | exact_check；已实际运行 |
| 真正152项物理积分的数值证明 | 未执行；INCONCLUSIVE |
| 原Lean构建、独立验证、186定理、孪生素数猜想 | 本轮未证明、未提升 |

重要区别：合成反模型中有150个固定目标未满足，**不表示原论文的150个积分界错误**。它只反驳“总余量PASS自动认证全部固定常数”的推论。程序本来可以服务于不同数值的总余量证书；新增桥接服务于固定输入。

## 文件

- `bridge-theorem.md`：明确假设的传递证明、反模型、几何与剩余缺口。
- `targets.json`：逐字复用前一冻结包的数值输入，SHA-256已核对；保留原format。
- `coverage.json`：149个源量和3个cap的完整目标表；公共方向和尺度在表头。
- `geometry.py`：从有理参数重建源ladder、97任务并对照规格常数。
- `upstream_assembler.py`：上游验收公式的独立精确模型；不是整个上游程序。
- `check_bridge.py`：实际receipt的条件算术检查与自测；不认证区间算法或对象语义。
- `results.json`：已执行自测的确定性输出，所有fixture都明确为合成。
- `source-lock.json`、`computation-record.json`、`attempt.json`：来源、运行和候选绑定。

```sh
python3 -B check_bridge.py --self-test
python3 -O -B check_bridge.py --self-test
python3 -B check_bridge.py --receipt /path/to/fresh.json
```

最后一个命令的退出0也仅代表 `CONDITIONAL_ARITHMETIC_PASS`；没有真实包络有效性和对象对应的证明，就不能解除任何Lean公理。传入receipt时需保留原cap的J0/Jplus/Jtail区间及全部149项原始端点，不能只传 `passed:true` 或汇总数。

## 最早未闭合点

下一项可证伪任务应聚焦 `G0:R00` 的low核：从精确测度定义证明程序的支配关系，随后取得root/face上界，而不是重复参数微调。完整积分运行在当前环境受限于缺少python-flint及定制FLINT构建；本轮没有伪装成完成该运行。

冻结前的本地/远端文件状态以Issue#44交接和交付记录为准。该attempt独立分支不修改前驱#38、基线PR#37、main、Project heads或registry。
