# 孪生素数第四轮：第一行 face 的真实积分上界候选

`A-TP-186-FACE-0004` · 2026-09-05 · solver stage · Issue #53。

## 实际结果

对固定规格的 `physicalSourceOuterFace 0 0`，以
`Iref=23685317816/10^24` 为纯粹的正有理数参考量，本轮得到

\[
\boxed{X_{\mathrm{face}}/I_{\mathrm{ref}}\le2.52164329\times10^{-18}
       <10\times10^{-18}.}
\]

这是实际求值的连续积分支配上界候选，不是合成报告，不是准确积分值，
不假设原来的 `physical_integral_bounds` 或 `Iref<=trialIH`。
解析对应、代码正确性及输入抄录仍待上下文隔离的独立审查。

两个标记位置分别产生约0.4236246751206311和2.0980186129942044个1e-18相对单位的上界贡献；
十进制分项仅供展示，最后的2.52164329由有理数向上舍入。

## 新的可复用计算接口

利用次数6的径向多项式，将带符号边缘相关改成准确整数有限差分滑动。
对权的不确定性单独累计绝对误差，不依赖FLINT或FFT，也不以反复区间相减掩盖相消。
三个实际cap只涉及Dickman的前两个延迟段，可由对数和收敛级数构造真正的单元积分包络。

实际生成：294792个cap单元质量区间；2104058个前缀边缘系数区间；
两个前缀的全部系数绝对宽度不超过512/2^160=2^-151，这不是相对精度声明。
460次生产网格准确中心点积与滑动结果相等。

这些数组接入同一个共同正测度上的39坐标平方矩，并保留擦除坐标与剩余坐标的两种标记来源。
完整计算使用53种平方签名和1803次正整数线性卷积。

## 文件与重现

- [数学推导](marginal-proof.md)
- [冻结输入](inputs.json)、[来源锁](source-lock.json)
- [整数后端](exact_backend.py)、[边缘生成器](marginals.py)
- [face求值](compute_face.py)、[有限测试/最终因子检查](check_face.py)
- [实际结果](results.json)、[执行记录](computation-record.json)
- [候选清单](attempt.json)、[独立审查任务](verification-ticket.md)

要求Python3.10+、gcc及GMP开发库。生产执行者必须先确认inputs.json的SHA256为
`2d22687c4842fa19b742a5dc4991cdbfdecbc12392d7eb0be938f6db222a5fbd`。

```sh
python3 -B check_face.py --self-test
python3 -O -B check_face.py --self-test
python3 -B marginals.py --output-dir generated
python3 -B compute_face.py --generated generated --output fresh-face.json
python3 -B check_face.py --check-result fresh-face.json
```

最后一条只重算已保存结果的有理数归一化，不能替代前面的全量求值。
再次生成的时间字段和包含时间字段的结果哈希可能不同；输入、数组与数学字段须准确对应。

记录到的完成运行：边缘生成55.352秒；完整source/face求值526.933秒；
峰值RSS3276636KiB。它们不是未来运行时间保证。

## 大数组与分支状态

十二份小文件提交到独立attempt分支；约53MiB的生成数组只在完整本地交付包中，
其哈希在执行记录中，全部可由已提交源代码重建。不可声称这些二进制文件已在GitHub。
没有向main提交数学权威，也没有merge-intended attempt PR。

## 两份同名第三轮包的区别

聊天附带的14文件包（ZIP f7f339ae...）与仓库#49冻结的9文件root候选
（commit cec587a86e...）不是同一包。源码与结果来源分别列明，未合并成一份虚假的连续记录。
#52审查的是后者的root候选；本轮没有执行该审查。

## 不能推出与下一目标

本轮单独处理1条face输入；不是全部152项，也不复核root候选、构建原Lean证明或降低186。
与另一冻结root候选合看，首行两个标量已有solver候选材料，仍须分别独立审查。
后续可复用这些边缘数组处理G0:R01；先重建该行的倾斜测度/标记窗口和径向支撑，
不能直接把第一行数值搬过去。较大径向范围须扩展数组，而不是越界复用。
