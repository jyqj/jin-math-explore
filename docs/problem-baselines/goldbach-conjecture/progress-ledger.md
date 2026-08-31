# 进展与依赖总账

## 1. v0.3 快照承诺

此前项目产生了 100 条唯一 `GB-*` 结论，采用 `E/P/D/H/A/R/T` 分类。机器快照和主要资产由以下哈希绑定。

| Legacy artifact | SHA-256 | 迁移用途 |
|---|---|---|
| `Goldbach_Research_Ledger_v0.3.md` | `7c235de78814873f789d1276eb961a49f555e249f9c03d0be2da692345243169` | 可读研究总账 |
| `secondary_conclusions_v0.3.json` | `03b7c7847f1c9633da9419f084683670e800b83bf1cee9eb730b68c5cb6d1ed1` | 100-entry 机器 claim 集 |
| `Stage3_Research_Report_v0.3.md` | `bbadf455b72419adfaea4985f2d1adc6e429ea8b96a02ea24b77a532bc282adb` | 第三阶段报告 |
| `External_Theorem_Interface_Audit_v0.3.md` | `ad5f9036fb0c85211c0f3e2f8c4cba5039762047698dae326e4044963e620749` | 外部定理接口 |
| `analytic_dependency_graph.json` | `c14e7bb3c152c5ca8c7384b41ffc84bae3276986d99214b9efdfdf4f19d5dcde` | 32 节点、84 边 DAG |
| `analytic_domain_certificate_v0.3.json` | `44ffee82197c6b8e71c7d69f00c7e5c8e981317e738e90116441dd80f502b4a1` | 区域与参数证书 |
| `dependency_status_v0.3.json` | `c692c3bfb290fa4d41b77c43c5000981a597c20d1ce967af32052c138d58fbb3` | 分支状态 |
| `interval_certificate_v0.2.json` | `01d927f3dacf1f3fef8c29a5be30378fdff319afcca19a866d058e18e5d84be7` | `mpmath.iv` 区间证书 |
| `mpfr_interval_certificate_v0.3.json` | `f3cf185cca7e2b29df53aee04b3d3ce694f6c2e73025215a6477f307891f4305` | 独立 GNU MPFR 证书 |
| `parameter_certificate.json` | `def247dd5ad21226ceee39f003f9ecd7650f82c4246f6f9f888cfc7858e8393c` | 精确参数链 |
| `proof_issue_register_v0.3.json` | `77168e5d8341f2a81500b1ada35a872e51f52e7f7d43674cd00c6d4a88b16681` | 12 项证明问题 |
| `prop43_symbolic_certificate_v0.3.json` | `21a0de88558c1ab598916803afe69764de0a26d136518bf3ee22fa65cd4615cd` | Proposition 4.3 符号证书 |
| `validation_summary_v0.3.json` | `f72886b2533b15d67127de1edac06ca0ac32ba0d380fd71a15fc13b28a3ffad6` | 机械验证摘要 |

哈希只证明对象身份，不证明其中数学陈述正确。

## 2. 已关闭或条件关闭的分支

| Branch | v0.3 状态 | 证据边界 |
|---|---|---|
| 数值主项：`mpmath.iv` | `closed-conditional` | 依赖冻结公式与外部解析不等式 |
| 数值主项：GNU MPFR | `closed-conditional` | 独立有向舍入引擎 |
| 双引擎一致性 | `closed-with-one-serialization-artifact` | 11/12 区间直接相交；`G_3` 为序列化伪差 |
| 参数不等式 | `closed-exact` | 有理数精确检查 |
| Proposition 4.3 系数代数 | `closed-conditional-on-local-repairs` | 需要下标与误差修复 |
| `S_6` 区域包含 | `closed-conditional-on-local-repairs` | 有限几何证书 |
| Wu Buchstab 全局上界接口 | `closed` | 来源与参数最小值已检查 |
| Lemma 2.5：`G_1,G_2,G_4,G_5,G_6` | `closed` | 合法域具有固定正裕量 |

## 3. 仍未闭合的关键路径

| ID / Branch | 状态 | 最小下一证据 |
|---|---|---|
| `ISS-G7-LEMMA2.5-DOMAIN` | `repair-required` | 合法截断、非负丢弃与边界层 \(o(1)\) |
| `G_8` switching 解释 | `repair-required` | 把三条局部修复传播到完整不等式 |
| Lemma 3.5 对 `G_9,G_11,G_12` | `open` | 每个 dyadic block 的假设—对象—证据矩阵 |
| 共同带符号误差与 \(N_0\) | `open` | 正确量词顺序和统一常数 |
| Theorem 1.1 全篇 | `not-closed` | 完整候选与独立 verifier |
| 二元哥德巴赫 | `not-addressed-by-this-proof` | 覆盖所有偶数的全新桥梁 |

## 4. 数值与符号审计摘要

v0.3 的机械摘要记录：

- `secondary_conclusion_count = 100`；
- 所有 legacy claim ID 唯一；
- 12 个论文显示常数均被 MPFR 区间覆盖；
- 最终 MPFR 主项余量严格为正；
- \(M/4>0.0004\)；
- Eq. `(4.30)` 与最终系数向量符号检查匹配；
- proof issue register 含 12 项；
- 11 项双引擎区间直接相交，1 项为保存精度导致的序列化伪差。

这证明的是冻结计算与有限代数的机械性质，不证明外部解析调用或主定理。

## 5. 当前 frontier movement

```text
数值主项
  -> 已条件关闭
有限组合代数与区域包含
  -> 已在局部修复条件下关闭
G7 合法域 / G8 修复传播 / Lemma 3.5 block 实例化
  -> 当前最早开放层
统一误差与共同 N0
  -> 下一个开放层
独立数学验证
  -> 尚未进入
```

因此本项目下一步的有效进展，应表现为开放边向下游移动，而不是重复提高同一积分精度。
