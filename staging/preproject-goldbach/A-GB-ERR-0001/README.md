# A-GB-ERR-0001 — signed error budget

**Issue #50 · CP-ERR-0001 · INCONCLUSIVE for actual paper closure.**
Base: `39002c5a6af8c7b7f093589e6a76cfd218fcbb99`.
Branch: `attempt/preproject-goldbach/error-budget-01`.

## 本轮推进

旧 GB-R007 / GB-T011 的“统一误差”任务现在有可运行的有向账本，而不是一句
“取 epsilon 足够小，再取 N 足够大”。

- 十二个显示小数的有符号主项精确为 **0.00172**。在4D尺度，为保住
  D/S>0.0004，实际可用误差余量只有 **0.00012**。
- 独立相对误差的放大系数为 **118.34034**，不是相消后的0.00172。
  无其他误差时，共同相对误差必须小于 **2/1972339**；脚本以4096个端点
  符号组合验证最坏方向可达。
- 给出 C(N)>=1/2 的望远镜乘积证明，统一把原始误差归一化。
- 给出条件共同 N0 定理和阈值模板，区分可固定的巨大常数与不能自动变小的
  C(epsilon)*epsilon。声明依赖图会拒绝量词循环，但不证明隐含依赖不存在。
- 发现式 (5.23) 的1/(p-1)到1/p替换按字面方向不对，给出正修正
  <=2*M_F*N^(-4/53)。这不是对主定理的反例。
- 明算G3端点漂移：最终组合中的成本 <=(115520000/897739)*xi。
- 证明分块误差 N/log(N)^A 乘上 log(N)^d 个cell后，要有 **A>d+2**
  才能在主项尺度衰减；记录了N依赖eta导致有限L失控的反例策略。

## 没有升级的内容

全部十二项解析估计仍是条件定理的假设。旧区间证书与G7新数值未混入活动
预算，L35/G7待审结果没有被当作已证输入。#35和#42仍待回执。

`error-ledger.json`有14项误差机制、5项语义gate；它不是可以直接求和的数组。
压缩O项与展开修正必须去重，未知语义gate不能当作零误差。
实际均匀系数、Buchstab主质量转移和source onsets未全部绑定，故共同N0在原论文
上的应用仍为INCONCLUSIVE。条件引理本身也只是待独立审查的solver数学。

## 文件与复现

`proof.md`保存F-ERR-001至F-ERR-008的推导与边界；`signed-ledger.json`
保存十二项方向、系数与来源；`error-ledger.json`保存误差/缺口；
`parameter-plan.json`保存条件依赖图；`source-lock.json`保存原文与旧账本定位；
`results.json`是实际精确计算输出，`attempt.json`绑定其余九个文件哈希。

```sh
python check_budget.py --compute
python check_budget.py --check
python check_budget.py --require-global  # expected exit 1: unresolved analytic inputs
```

只需要Python标准库。实际执行包含精确有理运算、整数小数交叉和、4096种符号
端点及8项故意错误的拒绝测试。机械通过不验证任何外部解析定理。

当前网络clone失败，未运行全仓测试、CI、旧MPFR套件或独立验证。
没有改main、Project、registry、catalog或冻结候选；没有提前发起合并型研究PR。
下一具体工作是G4/G5的一侧误差合同：F及导数的紧区间界、倒数修正、有限层级、
BV余项、PNT转移和小参数一致性，随后再完成十二项的真实合同实例化。
