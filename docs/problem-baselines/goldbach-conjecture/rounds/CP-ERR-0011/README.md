# CP-ERR-0011：G7 显式下界与连续移动边界

**reference-only；solver proof candidate；未独立验证。** 关联 Issue #115，承接 PR #109。
旧 G7 候选 #41 和所有前轮字节保持不变。

本轮完成 G7 的显式下筛替换：先限制合法区域，再使用 BJS 下筛与经典 BV。
双素数质量误差（含 d=1）统一汇总；完整支付 P0 水平和实际质量换算的对数成本，
不需要未知 C_s、L_eta 或 CP6 待审的加权分布候选。

新的连续单调比较核把双测度转移亏损控制为53r_N，没有人为的移动指标跳跃项。
证明条带损失为二阶，但整体核损失具有正的一阶下界。另证明真实整数指数端点不可能共享素数，
并用五阶小角界控制正高阶修正，没有把它丢成零。

一次完整计算实际执行73,728个中点、50位有向区间算术：

```text
sigma=1e-7: I_sigma in [3.790293206551658497,3.790296383322238964]
safe floor =3.7902931 > original comparator3.79029
sigma=5e-7: full fixed-kernel upper <=3.790283491027131158 < comparator
```

固定间隙方案牺牲一些系数余量，换取核和合法域不随 N 漂移；不是系数纪录或实际N0改善。
在明确输入下，局部总损失3e-6后仍有最终下界3.7902901。未更新全局账本。

## 文件与复现

[推导](proof.md) · [合同](contracts.json) · [来源](source-lock.json) · [既有积累](prior-work.json) ·
[结果](results.json) · [有限检查](validation.json) · [误差交接](error-handoff.json) ·
[计算记录](computation-record.json) · [计算交接](computation-handoff.json) · [审查票据](verification-ticket.md)。

Python>=3.10，mpmath==1.3.0，在本目录执行：

```sh
python check_g7_explicit.py --compute        # 真正重算三个积分并对比冻结结果
python check_g7_explicit.py --check          # 12哈希、2327有限实例、20负面控制；不积分
python -O check_g7_explicit.py --self-test   # 有限回归不依赖assert
python check_g7_explicit.py --require-global # 必须退出1
```

有限 AP 主项是人为有理数，单调测度测试是离散替代核，不是小N下BV的实测证明。
BJS定理/表、BV与Mertens是导入输入；原始Cs审计仍未解决，独立审查和十二项整体仍待完成。
本次直接Git传输失败DNS，没有全仓本地测试或原PDF字节哈希；远端CI以PR实际观察为准。
下一任务：G3/G10交换上界的支撑、端点与分布接口审计。没有启动后台验证者或合并PR。
