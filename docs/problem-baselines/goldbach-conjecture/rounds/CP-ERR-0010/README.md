# CP-ERR-0010：G6 显式下界与固定指数余量

**Reference-only solver candidate；尚未独立验证。** 任务 [#107](https://github.com/jyqj/jin-math-explore/issues/107)，承接 [PR #103](https://github.com/jyqj/jin-math-explore/pull/103) 的 G6 交接。所有旧候选不改写。

## 本轮推进

保留原始截断，完成 G6 双素数支路的显式下筛替换。两个不同的大素因子确定唯一模数分解，包括 d=1，因此全部素数对的实际质量偏差只需一个经典 BV 预算，而非乘上素数对数量。真实对角可删除，但连续主项的离散对角仍需扣除。

候选计入完整 P0 预筛支撑、负主因子的安全换算和新增的对数损失，不再依赖未知 Cs、L_eta 或 CP6 的待审加权 BV。BJS 定理/常数和经典 BV/Mertens 仍是导入输入，不是本轮独立重建。

进一步比较固定指数余量 sigma=10^-6：在完整起点条件 h_star<=sigma 下，核不再随 N 漂移。36,864个中点的有向区间计算得到

```text
g_(1e-6) in [1.633572214376088686,1.633572578036168926]
safe lower coefficient = 1.6335722 > original comparator 1.63357
```

该系数低于旧CP4的1.6335733，是“消除核漂移、牺牲少量系数余量”的取舍，不是新的数值纪录，也不代表实际N0改善。sigma=4e-6的比较积分上端点1.633569192166073863已低于目标，失效边界被保留；不是实际G6计数的上界或哥德巴赫反例。

## 证明、复算和完整档案

[完整证明](proof.md) · [机读契约](contracts.json) · [数值包络](results.json) · [有限检查](validation.json) · [误差/下一步](error-handoff.json) · [历史索引](prior-work.json) · [来源范围](source-lock.json) · [计算记录](computation-record.json) · [计算交接](computation-handoff.json) · [独立审查票据](verification-ticket.md)。

Python>=3.10，mpmath==1.3.0；在本目录运行：

```sh
python check_g6_explicit.py --compute       # 重算全部三个积分并对比冻结结果
python check_g6_explicit.py --check         # 12个哈希、有限复算和20项负面控制；不做求积
python -O check_g6_explicit.py --self-test  # 不依赖assert的精确有限检查
python check_g6_explicit.py --require-global # 必须退出1
```

本轮实际生成了三个积分证书；有限测试正常/-O输出一致。10260项检查包括同一2558个模数三元组上的AP、换基、单射分别核对，不是10260个独立数学结论。有限AP样本用合成解析质量，不是实际Li误差或小N下的BV验证。

13个新文件全部进入本轮PR；SHA-256清单绑定其余12个文件。源PDF原始字节未取得，完整本地仓库测试未运行，原Iwaniec审计、独立审查及十二项整体闭合仍未完成。PR/CI只检查发布与机械边界，不提升数学证据等级。没有合并main或更新全局系数账本。

下一步：G7显式下界，先处理s>=2的移动合法域及边界条带，不能直接复制G6整域s>=3的条件。
