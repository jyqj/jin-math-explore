# CP-ERR-0013：G9 半水平替代与组合门槛

**Issue #127；reference-only solver candidate；未独立验证。** 承接 CP12 / PR #125，旧文件不改动。

## 本轮推进

G9 可在明确的 CP12 有界支撑分布输入、BJS 显式上筛与 Mertens 输入下退回半水平，不用 L35、未知 C_s 或 L_eta。推导保留非零 H、实际质量换基、完整预筛水平和异常成本。实际区间计算给出固定主系数上界 **5.291548**，比原显示上界5.27231更差；这是减少依赖所付出的代价，不是数值纪录。

更关键的是组合步骤：重建了精确关系

```text
S5(beta,gamma) = G10 + C_wedge - C_order
G16_literal = C_wedge
```

两个修正量都非负。原文印刷的 G16 使用 A_(p1*p2)，而后续覆盖用 A_(p1*p2*p3)。实际素数差 `144568-3=5*29*997` 给出逐项覆盖失败，并有任意大参数的同类族。仅补下标也不能修复；`5504-1009=5*29*31` 证明负 ordering 项确实存在，`166318-3=5*29*31*37` 证明楔形还含四素数残余。

**范围边界：这排除无损逐项支配/直接注入路线，不证明完整素数序列的聚合不等式或其 big-O 版本为假，也不反驳论文主定理或哥德巴赫猜想。** CP12 的局部 G10 零域证书保持原状，但其收益不能自动用于全局预算。

## 计算与复现

[完整推导](proof.md) · [契约](contracts.json) · [来源](source-lock.json) · [历史索引](prior-work.json) · [结果](results.json) · [有限检查](validation.json) · [误差交接](error-handoff.json) · [计算记录](computation-record.json) · [计算交接](computation-handoff.json) · [独立审查任务](verification-ticket.md)。

在本目录，使用 Python>=3.10、mpmath==1.3.0：

```sh
python check_g9_combination.py --compute        # 重算24576个中点并比较冻结结果
python check_g9_combination.py --check          # 12哈希、1998有限实例、20负面控制；不积分
python -O check_g9_combination.py --self-test   # 不依赖assert
python check_g9_combination.py --require-global # 必须退出1
```

本轮只执行一次完整主积分；normal/-O比较针对有限与检查模式，不声称优化模式又积分一次。有限 AP 主项是人为有理数，不是 Li 实测误差；渐近族角点测试不是巨大素数枚举。

下一步优先重建 (4.27) 到 (4.31) 的有符号组合转换，分别处理楔形、ordering、三素数与四素数部分，而非先继续收紧小数。源输入和候选仍待独立审查；完整十二项状态为 INCONCLUSIVE，无数值 N0、独立回执或合并。
