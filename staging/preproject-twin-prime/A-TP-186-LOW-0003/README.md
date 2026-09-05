# 第三轮：G0:R00 第一项真实积分的上界候选

`A-TP-186-LOW-0003` · 2026-09-05 · solver · Issue #49。

本轮从“报告字段是否正确”推进到连续核与实际积分本身。
对冻结规格中的 `physicalSourceOuterRoot 0 0`，构造了以下上界候选：

\[
\frac{\texttt{physicalSourceOuterRoot 0 0}}{23685317816/10^{24}}
\le10.42897229\times10^{-18}<11\times10^{-18}.
\]

它使用正更新方程、共同上测度、160-bit 有方向固定点和 GMP 精确整数线性卷积。
不是合成报告，不借用 `physical_integral_bounds` 的数值假设，也不依赖先前未验证的 Young 改进。
但连续测度控制与转写对应仍是**待独立审查的证明候选**；程序通过不是独立 verifier PASS。

## 交付文件

- [完整数学控制关系](low-kernel-proof.md)：Poisson/Dickman low 核、正更新、格子质量、带标记矩与最终目标。
- [冻结输入](inputs.json)：原参数与 77 个有理系数，SHA-256 被计算程序固定。
- [完整重算程序](compute_envelopes.py)：无旧积分输出或缓存输入；内嵌一个精确 GMP 乘法接口。
- [检查器](check_low_kernel.py)：有限代数/后端测试，以及保存结果的最终有理数复核。
- [实际计算结果](results.json)：含固定点整数因子、密度数组哈希、耗时与边界。
- [来源锁](source-lock.json)、[计算记录](computation-record.json)、[候选清单](attempt.json)。

## 运行

需要 Python 3.10+、gcc 和 GMP 开发头文件/链接库。程序不会下载、安装或修改依赖。
本轮实际使用 CPython 3.13.5、GMP 6.3.0。完整运行约 197 秒，峰值 RSS 约 2.0 GiB；
这是本机观测，不是其他环境的时长保证。资源较小的环境应先安排合适运行器。

```sh
python3 -B check_low_kernel.py --self-test
python3 -O -B check_low_kernel.py --self-test
python3 -B compute_envelopes.py --run --output fresh-results.json
python3 -B check_low_kernel.py --check-result fresh-results.json
```

输出路径必须不存在。`--check-result` 只重算最后的有理不等式，不会重算整个积分包络。
完整重算输出的时间/RSS可以变化；应比较输入哈希、密度哈希和全部数学整数结果，而不是要求执行元数据字节相同。

## 范围和下一步

这一轮只关闭了一个目标的 solver-stage 推导与数值上界；不是整个第一行都完成。
`physicalSourceOuterFace 0 0` 的相对目标 10 **未计算**，它含平方边缘积分，不能直接由 root 上界推出。
尚待处理的 148 个源积分界（包含该 face 项）、三个整体 cap 界及全文的其余分析/有限域输入未在本轮认证。
没有新的素数间隔纪录，没有孪生素数猜想证明，没有 Project authority 或 merge-intended attempt PR。

前一轮 #44 的冻结候选与待审 #47、第一轮待审 #39 均不改动。
新独立审查只接收本次冻结的九份文件、任务票据与指定原始来源，不继承 solver 对话。
