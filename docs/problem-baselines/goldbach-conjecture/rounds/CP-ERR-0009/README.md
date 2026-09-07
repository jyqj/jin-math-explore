# CP-ERR-0009：G4/G5 显式上筛与一维证书

**reference-only solver candidate；尚未独立验证。** 工作票据 [#99](https://github.com/jyqj/jin-math-explore/issues/99)，承接 [PR #97](https://github.com/jyqj/jin-math-explore/pull/97) 的 G4/G5 任务。旧候选只读，不改变全局数学状态。

## 本轮结果

重建逐提取素数的实际质量换算，并证明所有质量偏差之和只需一个经典 BV 预算；不乘提取素数的个数。两个重叠范围则保留至多2的重数。

使用显式 BJS 上筛，完整支付预筛乘积 P0 和多出的一个对数，给出 G4/G5 上界候选；不再需要未知 Cs、L_eta，也不需要前轮待审的加权 BV 桥梁。BJS 定理与表中常数仍是明确导入输入。

将公共二重修正化成一维积分，以48阶有理 Taylor 展开和解析余项，实际完成 **28,672 个一维中点**：

```text
g4 in [23.605686437359609383, 23.605687876075436255]
g5 in [19.519080862878462493, 19.519082283006322277]
保守上界：23.605688、19.519083
```

相较 CP2 的保守主系数上界合计收紧0.000089；这不是实际计数的双侧区间，也未记入全局预算。公共正修正没有丢掉，只是不再需要二维网格。

## 文件与复算

[完整推导](proof.md) · [合同](contracts.json) · [既有积累](prior-work.json) · [来源](source-lock.json) · [误差交接](error-handoff.json) · [审查票据](verification-ticket.md)。

Python>=3.10、mpmath==1.3.0，在本目录运行：

```sh
python check_upper.py --compute        # 重算所有积分，并与 results.json 比较
python check_upper.py --self-test      # 3942项有限身份/支持/代数检查
python check_upper.py --check          # 哈希、有限重放与20项负面控制；不求积
python -O check_upper.py --compute     # 禁用 assert 后的同上下文复现
python check_upper.py --require-global # 预期退出1，拒绝全局结论
```

[results.json](results.json) 和 [validation.json](validation.json) 是真实输出。有限 AP 模型使用可变小筛界、R=N及合成有理质量偏移，只核对代数身份，不表示这些小 N 满足 BV/BJS 渐近假设。
[计算记录](computation-record.json) 与 [交接](computation-handoff.json) 区分真正求积、有限检查和哈希检查。所有结果均为同上下文复现，不是独立验证。

本包共13文件，所有推导、代码、结果和局限均纳入实际 PR。直接 git 访问失败；未声称本地全仓测试或源 PDF 字节哈希。远端 CI 以 PR 交接的实际观察为准。

下一任务：G6 的显式下筛替换，先处理双素数质量、两种对角及 P0 水平。完整十二项、源输入独立审查与有效数值 N0 仍未闭合。
