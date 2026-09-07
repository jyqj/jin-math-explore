# A-TP-PHYSICAL-0010：真实186权的双边缘与支持障碍

接续冻结 PR #98；全部内容为reference-only归档，不推进Project authority。工作包#100，分支`program/i-0100/twin-physical-trace-10`，基点`39002c5a6af8c7b7f093589e6a76cfd218fcbb99`。

本轮不重复普通单纯形调参，而是回到实际对角系数和物理测度，形成三项成果：

- 重推两次带`B_R^{-1}/phi`权的边缘与端点系数限制，明确其不是把物理函数两个坐标置零。
- 对实际77系数试验H，构造正测度盒上的精确非零双边缘，排除base/enlarged内完全保持该边缘的助手。H在盒上约为`-7.3961212481e-24`；完整有理值已保存。此结论不自动适用于恢复后的`P_OH`，也不说明近似误差不可支付。
- 给出保留残差的正确不等式、有限双端点上筛/CRT计算和精确最小对角范数提升。取两个新根各在`N^0.1`内，平方计数支持指数为0.9485994；这只是支持预算，尚未证明真实残差渐近小于检测余量。

## 复现

Python3标准库即可，不需要旧bulk数组、网络、NumPy、CAS、Lean或FLINT。

```sh
cd docs/problem-baselines/twin-prime-conjecture/rounds/A-TP-PHYSICAL-0010
python -B physical_trace.py --output-dir /tmp/physical-trace-fresh
cmp certificate.json /tmp/physical-trace-fresh/certificate.json
cmp results.json /tmp/physical-trace-fresh/results.json
python -B check_physical_trace.py --self-test --check-hashes
python -O -B check_physical_trace.py --self-test --check-hashes
python -B check_physical_trace.py --require-global # 预期exit1，主动拒绝越界认证
```

实际执行的数目与输出见`computation-record.json`：152个对角恒等式、1,670,505项投影比较、784项CRT对照、24个有限端点素数对、21个纤维恢复及16项篡改拒绝。第二条计算路径仍属同一solver上下文，不是隔离审查。

## 导航及边界

`proof.md`包含T10-01..05、来源定位与下一数学缺口；`inputs.json`锁定77系数/掩码；`certificate.json`含原始精确值；`results.json`保留不能推出的结论；两份Python文件负责生成与复核；来源锁、执行记录、计算handoff、待领取验证任务和哈希清单构成完整12文件交付。

没有全网新颖性声明、没有新的素数间隔界或孪生素数证明。Git实际访问DNS失败，未在本地运行全仓测试；远端CI与提交身份在PR/Issue追加记录。没有请求或执行合并。
