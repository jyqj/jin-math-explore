# 哥德巴赫 CP-ERR-0005：G8 交换筛修复

**Reference-only solver candidate；未独立验证。** 关联[#74](https://github.com/jyqj/jin-math-explore/issues/74)，承接[#73](https://github.com/jyqj/jin-math-explore/pull/73)的冻结G6交接。旧PR和全部旧工件保持不变。

## 本轮进展

G8不能直接套用G6：提取乘积已超过经典BV水平。重新检查交换筛时，找到原文“残余一定是≥p2的素数”的精确等式缺口：p1本身被筛集排除。例子为254−79=5²·7，提取(5,7)后残余5<7；文中给出任意大参数的同类构造，并补上趋零的异常项预算。**这不是哥德巴赫反例，也不否定原论文主定理。**

改用带索引的交换多重序列，补齐合法筛界Z=sqrt(Q)；由真实筛模数的光滑支撑证明非互素H修正**恰好为零**，不是直接把未知误差忽略。保留加权均值定理这一外部输入，推导曲边双素数域与有符号上界的全部成本。

固定系数以96项精确有理级数及解析尾界重算：

```text
g8 ∈ [0.609611573201938690, 0.609611573201938694]
保守上界：0.609611574（原显示上界0.60962）
按组合系数−2计算的潜在余量增加：0.000016852
```

余量没有写入全局账本；有限N的G8仍须支付误差。统一线性筛常数和原始加权均值定理仍待独立源审查。

## 证据与复算

[完整推导](proof.md) · [原生契约](contracts.json) · [来源与缺口](source-lock.json) · [历史衔接](prior-work.json) · [误差和下一步](error-handoff.json) · [独立审查任务](verification-ticket.md)。

只需Python≥3.10，无第三方依赖；在本目录运行：

```sh
python check_g8.py --compute
python check_g8.py --check
python -O check_g8.py --self-test
python check_g8.py --require-global  # 必须退出1
```

`--compute`真正重算96项有理证书；`--check`检查11个哈希、保存的证书关系、有限回归与16项负面控制，不冒充原始定理审查。
实际有限检查覆盖593个偶数、1141个筛存活项、908个交换模数计数恒等式、96个误差乘积测试以及4个大参数反例族样本。具体输出在[validation.json](validation.json)；有限测试不能代替无限族和误差上界的解析证明。

12个文件全部提交新PR，仅归档未验证候选，不推进Project/registry/catalog或数学权威。原始PDF字节未取得，本地全仓测试未运行；远端CI以PR实际回执为准。

下一步优先审查U-WBV原始输入，尤其N-dependent权、N^(2/3)支撑、变化余类和严格端点，再将合法接口复用于G3/G10。
