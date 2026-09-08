# CP-ERR-0012：G3/G10 交换上界与真正活跃域

**reference-only；solver proof candidate；未独立验证。** 工作包 [#119](https://github.com/jyqj/jin-math-explore/issues/119)，承接 [PR #118](https://github.com/jyqj/jin-math-explore/pull/118)；此前候选保持冻结。

## 本轮实质进展

G10 的原值子序列在 `p1*p2^3<N` 时整项为零：提取的 p2 自身处在筛界之下。精确保留活跃域后，固定主系数的保守上界从原显示 **5.40996** 降到 **5.194297**。这是局部上界候选，不是全局哥德巴赫常数或指数的改进；新余量未记入全局账本。

同时修复“残余只能是素数”的推断：`142−7=3^3*5` 的残余9通过原筛。给出任意大参数的同类族和幂次节省异常预算，而不是据此否定论文主定理。

G3/G10 不在旧 CP6 支撑内，本轮从最大双线性大筛和 Siegel–Walfisz 重新推导 `[N^(1/3),N^(2/3)]` 上的有界权分布桥。G10 的非互素提取修正 H **不为零**，与主特征中移除素数的修正区分并付费；继续保留完整 P0 预筛成本、实际质量换基和 G3 的指数小参数。

## 固定积分与复算

```text
g3(9/19) ∈ [0.842884125262610409, 0.842884125262610410]
g10(active) ∈ [5.194296087251842655, 5.194296165620083345]
removed wedge ∈ [0.215661666553658440, 0.215661689773877904]
```

一次完整主计算实际执行8192个中点，50位有向区间算术；G3另用32项精确有理对数级数。人工解析余项与算术信任边界见 [完整推导](proof.md)。

```sh
python check_switching.py --compute       # 全部固定积分重算并比较冻结字段
python check_switching.py --self-test     # 5819个有限计数实例
python check_switching.py --check         # 12哈希、有限回归、20个负面控制；不积分
python check_switching.py --require-global # 必须退出1；拒绝全局结论
```

Python>=3.10，mpmath==1.3.0。[数值输出](results.json)、[有限检查](validation.json)、[原生合同](contracts.json)、[计算记录](computation-record.json)、[计算交接](computation-handoff.json)、[完整性清单](artifact-sha256.json) 均在本目录。

有限原筛模型用整数幂判断实际指数；AP质量则是人为有理 `X_m=2N/(3m)`，不是Li实测误差，也不验证小N满足渐近输入。重复表示例 `370−139=21*11=33*7` 保留索引，不可去重。

## 依赖、未闭合范围与下一步

[来源锁](source-lock.json) 与 [前置索引](prior-work.json) 区分原始来源、不可得字节与未审候选；[误差交接](error-handoff.json) 给出有害符号与参数顺序；[独立审查票据](verification-ticket.md) 尚未执行，不表示有后台worker。

导入的BJS定理/表、大筛/SW及Mertens没有独立重建。未给有效数值N0、巨大P0、原Iwaniec/Pan–Ding全文审计或十二项闭合；源PDF字节哈希为空。完整本地仓库测试未运行；PR远端CI以实际观察为准。

下一步：G9的混合水平和相应组合输入，先审查冻结L35候选及适用条件，不把普通绝对分布界直接移植到因子化权。
