# 孪生素数猜想：既有进展基线 v1

**来源截止：** 2026-09-05　**协调：** Issue #36  
**仓库等级：** `reference_only` / pre-genesis  
**分支：** `program/i-0036/twin-prime-baseline-v1`

## 当前状态

目标仍是证明存在无穷多对相差恰好 2 的素数。当前检索到的最新可信一手材料仍将它作为未解决问题；这是一份有日期和范围的来源状态记录，不是关于所有文献的穷尽性断言。[Stadlmann2026; OpenAI2026]

令 $H_1=\liminf_{n\to\infty}(p_{n+1}-p_n)$。本次必须同时保留三个层次，不能将旧纪录当作最新声称，也不能将新声称当作仓库已验证定理：

| 层次 | 结果 | 基线处理 |
|---|---|---|
| 已发表的经典基准 | Polymath8b：$H_1\le246$ | 外部已发表定理；仓库未重新验证证明 |
| 新预印本 | Stadlmann：$H_1\le240$ | 锁定 `arXiv:2608.31126v1`；完整证明复核未做 |
| 本次发现的最小新报告上界 | OpenAI：$\mathrm{DHL}[40,2]$，进而 $H_1\le186$ | 论文声称无条件；配套 Lean 保留三个输入公理；本仓库未复现 |

来源分别为 [Polymath2014b, Thm. 1.4(i)]、[Stadlmann2026, abstract / §1]、[OpenAI2026, Thm. 1.1 / Cor. 1.2]。**246 是已发表参考层，不称为截至今日不加限定的“世界最新纪录”。186 是新报告层，不称为本仓库已独立确认的纪录。**

## 导航

- [精确目标、量词和状态](objective-and-status.md)
- [进展与二级结论总账](progress-ledger.md)
- [方法依赖与障碍](methods-and-barriers.md)
- [186 新结果的证据分层与复核接口](latest-186-review.md)
- [来源范围、版本锁和审计债务](source-audit.md)
- [后续研究入口与迁移](frontier-and-migration.md)
- [机器可读结论](claims.json) / [参考文献](references.bib)
- [本目录结构检查器](check_baseline.py)

## 本仓库实际完成了什么

这一轮建立文献及逻辑边界基线，没有新增孪生素数证明、反例或经独立验证的数学结论。没有运行 Lean、186 的完整数值证书、大范围素数枚举；也没有继承一份已核实的旧孪生素数研究账本。后续必须从这里继续，不能把“整理了外部进展”计为“本仓库取得了同样的数学突破”。

仓库级 Project genesis、知识节点和 catalog 发布另行走既定门禁；本目录不创建 Project heads，不改变任何 claim authority。

## 重现结构检查

```sh
python3 -B docs/problem-baselines/twin-prime-conjecture/check_baseline.py
```

检查只涉及 JSON、来源 ID、依赖无环、文档链接和文件哈希，不检查论文证明。远端 PR 状态及 CI 结果以 Issue/PR 的冻结交接为准。
