# 第五轮：第一行 root / face 两项的完整数值证书候选

**Attempt：** `A-TP-186-CONTRACTION-0005`　**协调：** #59  
**证据状态：** `proof_candidate` + `exact_check`；不是独立数学审查 PASS。

## 实际结果

取单位 \(u=I_0/10^{18}\)，其中 \(I_0=23685317816/10^{24}\)。
本轮完成真实 `G0:R00` 全网格正测度平方收缩，不是合成输入或抽样模型。

| 物理目标 | 已认证支配式给出的有理上界（单位 u） | 固定目标 | 本地数值判定 |
|---|---:|---:|---|
| `physicalSourceOuterRoot 0 0` | 10.396041 | 11 | PASS |
| `physicalSourceOuterFace 0 0` | 2.513205（已加边缘数组误差） | 10 | PASS |

更紧的计算端点约为 10.396040185127013394944167 和
2.513204435147038902084175。表中六位小数按准确分数向外放宽，不是浮点阈值。
[结果摘要](result.json) 给出可机器读取的有理界；[证明候选](proof.md) 给出对象、量词和归一化。

**条件边界：** 从有限数值证书到上述物理目标，要使用冻结试验的
Poisson/Dickman/cap/Mecke 恒等式、连续测度到共同正单元核的支配关系、
以及前轮边缘数组的数学包络和误差预算。这些依赖已经写成审查对象，
但本运行不是独立 verifier，不把前轮候选自动提升为已验证定理。
其他150项、两个有限域输入、完整186证明与孪生素数猜想均不在本次判定范围内。

## 算法与数据覆盖

真实网格 n=98264；source 下标 94919..95638；未标记片段数0..42全部计算，
已有标记后额外片段数最多41。没有使用高阶尾部近似。
53个平方签名归并为77个块和元组；全部算出，保留正负系数和两个见证来源。
320-bit 定点尺度只用于显式向外取整；整数乘积由 GMP 6.3.0 精确求得。
共同固定正测度先于平方展开冻结，避免把各矩单独的上界代入带符号表达式。

完整实数值运行及其 `-O` 重放的状态在 [执行记录](computation-record.json)。
源码重建已单独测试：从六份 predecessor 源文件重新生成 seed 与全部 marginal 数据，
压缩字节哈希和 generation 报告都与冻结输入一致，无需联网下载缓存。

## 重现

环境：Python 3.10+、g++（C++17）和 GMP 开发头文件/库；已测试 Linux + Python 3.13.5 + GMP 6.3.0。
原始 FLINT/Lean 不是本实现依赖，也没有声称运行了它们。

```sh
python3 -B run_pipeline.py --output fresh-run
python3 -O -B run_pipeline.py --output replay-run --compare fresh-run/contraction
```

脚本拒绝覆盖已有运行目录。`packed_gmp.so` 在本机编译，不随包分发。
缺少 predecessor 二进制数据时按源码重建；字节不匹配会停止。
科学输出比较包括77个准确贡献及所有结论字段，仅排除耗时字段。
程序完成与两个目标通过是不同字段，应读取 `root_11_certified` 和 `face_10_certified`，
不能只看退出码。生成或运行前应校验 [文件清单](artifact-sha256.json)。

## 文件与发布边界

GitHub 分支 `attempt/preproject-twin-prime/186-square-contraction-05` 保存20份
源码、输入、证明和结果摘要文件；未修改 main、旧 attempt、Project、registry 或 protocol。
下载包另含真实 seed、全部 marginal 数组、八组 kernel 数组、77项完整求和记录、运行日志，
以及继承的证明文档。大文件是有意不进入本次远端写集，不是虚报已经上传。
每一项均可由提供的源码重新生成，精确哈希见结果及 source-lock。

[独立审查任务](verification-ticket.md) 只定义新隔离上下文应检查的范围，不是审查已完成。
没有把2/152换算成猜想完成比例，也没有宣称新的素数间隔纪录。
