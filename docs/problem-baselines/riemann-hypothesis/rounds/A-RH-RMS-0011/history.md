# 历史恢复与本轮接续点

## 阅读范围，不夸大恢复程度

本轮通过 GitHub 连接器实际读取 main、分支清单、相关 Issue/PR、治理文件，
完整阅读第 10 轮 README 与 #67 冻结交接，并读取其计算交接和 #68 评论。
第 10 轮数学输入已按 commit/blob 定位；#68 在读取时没有评论或验证 receipt。
更早各轮的下表依据其 Issue 契约、冻结交接摘要及分支元数据，**不代表本轮
逐个重跑了全部历史检查器或重新证明了全部历史结论**。不以聊天记忆覆盖远端记录。

## 基线与两条路径

来源基线为 [#21](https://github.com/jyqj/jin-math-explore/issues/21) / draft
[PR #22](https://github.com/jyqj/jin-math-explore/pull/22)，冻结于
`cd3ee76330ec4c7ae731cebb37933a3b03458dc9`。其 PR 记录 16 个 reference-only
知识节点，且有知识节点/catalog PR 策略阻塞 #23；Project genesis 另受 #4/#20
约束。本轮不借新档案导入未合并知识节点或绕过 Project 创建门。

主研究链的物理文件位于各 commit 的 `staging/preproject-rh/<attempt>/`。
以下均按原记录保留为 solver candidate，而非已验证定理。

| 轮次 / Issue | Attempt | 冻结 commit | 已记录的方向与边界 |
|---|---|---|---|
| 1 / #24 | A-RH-RTD-0001 | `2f2ecdac7aec73d3996d3484e7a56b051a718f11` | rank–trace 非负缺陷分解；标量信息的不足 |
| 2 / #28 | A-RH-XSR-0002 | `325f67106496248915a0647d4eae4b15ff10b42f` | 阈值最优性、同尺度塌缩、理想格点二尺度余量 |
| 3 / #32 | A-RH-LCI-0003 | `95e3e56329cc124166ed80cfd25628bedd845d35` | 慢应变反驳过强全局匹配；局部紧性与离线对缺口 |
| 4 / #40 | A-RH-WTP-0004 | `340d6c4a3f2101d2cd08834ee3fe9cc9aed8f202` | 带权迹、截断次序、算子传递；不能盲目识别深度 |
| 5 / #45 | A-RH-CTP-0005 | `75ad472d97ed52b0fa8978b177fbe3ed98b592b7` | 中心化 Toeplitz 压缩与给定匹配下的扰动预算 |
| 6 / #48 | A-RH-CWR-0006 | `2577c7769b806075e2e3dc5d3b298e9d56458a46` | cyclic-wrap 反模型；抽象 Toeplitz/投影信息不足 |
| 7 / #54 | A-RH-SRE-0007 | `ddb7b51cfbcc805110c35dcaf03f2c2bc65b0ec7` | 从带符号缺陷抽取简单实点正能量；不扩大到全体零点 |
| 8 / #58 | A-RH-AOC-0008 | `1af426358ff62e540e1fdb5702c6dabd8d920dd9` | 锚点到反射对的正能量；真实指数洞区模型与覆盖缺口 |
| 9 / #63 | A-RH-SMP-0009 | `a97c80778bda2c5a337be978ccc9afec36b750ea` | 稀疏拼块和低总变差；快速交错仍需新方法 |
| 10 / #67 | A-RH-PER-0010 | `d00192b4b2cfb5669c2560c5f02e8d6ed3988a59` | 精确周期重构与锁相；定量误差要求 Q^2 delta -> 0 |

第 7 轮原数学 commit 是 `9715ec125e7dd357a464b5e2156e799017c75e8d`；
表中 head 另包含渲染勘误，不把它当作新的数学证明。
上述各 Issue 可通过 `https://github.com/jyqj/jin-math-explore/issues/<number>`
定位；对应独立审查队列依次为 #25、#31、继承 #31 的后继检查、#43、#46、
#51、#55、#60、#64、#68。这里只对本轮实际读取的 #68 声明“未见 receipt”，
不推断未重读队列的实时状态。

另有 #26 的 window-collapse 分支和 #30 的 lattice-extraction 分支，分别冻结于
`698d28d4e074f09fdb7dfdaffc65df1cdc94727b` 与
`ece0300abb4eb234e33963a02aacf41a1daa8fee`。只记录其定位，不将并行线的证明
作为本轮额外数学输入。

## 为什么本轮不是重复第 3 或第 10 轮

第 10 轮用逐系数上界再对 Q 个权重求和，产生额外 sqrt(Q)。本轮直接证明
归一化矩阵均方扰动界，同时用单胞假设推出舍入聚合质量至多 4，再做带权
Toeplitz 比较。由此得到新的 Q delta 条件，而非改名重述旧锁相公式。

慢应变思想已有先例，本轮不声称首次发现。新增反例精确适配第 10 轮的
周期、均值一、简单比例 2/3 和单胞模型；其全局最小相位代价精确为 1/128，
并给出全 Q 缺陷上界及短预算失败的解析证明。因此它确定的是新传递路线
仍不能删除的中间损失，而不是把旧反例重新包装成 RH 反例。

## Git 依赖与数学依赖分开

本轮 Git base 为 main `39002c5a6af8c7b7f093589e6a76cfd218fcbb99`，tree 为
`d6ac23dc843e26ba123ae167228e3a0c1ff6b750`；数学 parent 则是上述第 10 轮。
新分支 `program/i-0069/rh-rms-transfer-11` 只新增本目录十个文件。
这种 main-based 文档档案路径避免把整串未合并 staging、knowledge/catalog
冲突和旧 solver lease 一起带进 PR。不复制或改变前轮 evidence grade。
