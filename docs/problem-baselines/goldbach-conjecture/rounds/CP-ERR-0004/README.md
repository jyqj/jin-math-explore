# 哥德巴赫 CP-ERR-0004：G6 原生下界

**本轮研究档案；reference-only；solver candidate；未独立验证。** 关联 [#70](https://github.com/jyqj/jin-math-explore/issues/70)，承接 [#50](https://github.com/jyqj/jin-math-explore/issues/50) 的 CP-ERR-0003。

## 本轮实际推进

前轮已分别给出 G4/G5、G1/G2 的条件误差契约，并明确把 G6 双素数下界列为下一任务。本轮重建原始截断集合，不重复整理基线。

建立 G6 的有符号误差契约：先删除真实计数中非负的平方对角，使 BV 模数映射成为单射；转为连续主项时再明确支付离散对角、去公因子、素数测度误差和有限筛水平漂移。正主项与负罚项分开估计，避免在核减误差可能为负时用错分母方向。

把固定系数化为单变量积分，以48阶有理 Taylor 多项式和解析余项完成有向计算：

```text
g6 ∈ [1.633573342946618456, 1.633573706594987299]
保守下界：1.6335733（原显示值为1.63357）
```

仅保留对数部分时，上界只有1.633080615714169010，不能达到目标；正修正项确有必要。这一失败对照不否定完整积分或原论文。

在明确的统一源输入下，证明可以先选小参数、再选 N，使 G6 局部原显示下界最终成立。没有给出有效数值 N0，也没有闭合完整十二项组合，更未证明哥德巴赫猜想。新增0.0000033只是局部主系数余量，未写入全局权威账本。

## 阅读与复算

[完整推导](proof.md) · [原生机读契约](contracts.json) · [既有积累与版本](prior-work.json) · [源锁与未决假设](source-lock.json) · [下一步/误差交接](error-handoff.json) · [独立审查票据](verification-ticket.md)。

在本目录执行（Python≥3.10，mpmath==1.3.0）：

```sh
python check_g6.py --compute        # 真正重算，并与冻结数值逐字段对比
python check_g6.py --check          # 只检查保存证书、11个哈希与负面控制
python -O check_g6.py --self-test   # 不依赖 Python assert
python check_g6.py --require-global # 必须退出1；拒绝全局闭合
```

[results.json](results.json) 保存12288中点有向计算；[validation.json](validation.json) 保存122个单射实例、486个有限符号检查、46个 Taylor 系数界及46个递推恒等式。
`--check` 含14项负面控制；这些回归检查不是普遍数学证明。首次完整证书计算实际约3.10秒，记录见 [computation-handoff.json](computation-handoff.json)。

## 发布边界

本次按用户要求提交完整 docs 档案 PR，而不是只留一个未合并 attempt 分支。12个文件均为新增；前轮冻结文件、Project heads、registry、catalog、协议和基线结论均不改动。

统一线性筛常数 C_s 的源端量词仍是明确假设；本轮不充当独立 verifier。源 PDF 只实际取得渲染/解析内容，没有伪造原始字节哈希。完整本地仓库测试未运行；远端检查以 PR 实际结果为准。

下一研究任务：G8 原生上界，先查变化筛界造成的模数重数，再决定 BV 聚合方式。
