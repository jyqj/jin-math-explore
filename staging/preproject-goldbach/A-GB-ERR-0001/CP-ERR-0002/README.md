# G4/G5 native one-sided contracts — CP-ERR-0002

Issue **#50** · `A-GB-ERR-0001` · solver continuation, not independent verification.
Main base: `39002c5a6af8c7b7f093589e6a76cfd218fcbb99`.
Predecessor: `388c958afb2c89c571e43483b2154eb56e2e2e67` (CP-ERR-0001), unchanged.
Branch: `attempt/preproject-goldbach/error-g45-02`.

## 本轮推进

- 对G4/G5上界先扩大素数集合，完全去除本地误差对epsilon0的依赖。
  该技巧不能用于下界。
- 合法层级具有固定裕量5/318、89/1166；足够大N下不需要删去积分域。
- 在真实筛参数域上证明归一化F的sup和Lipschitz界均为1。
- 使用唯一大素因子(p,q)->pq，直接汇总经典BV余项；不导入L35。
- 得到包含六类成本的原生一侧合同，精确分离固定eta项与N衰减项。
  两项合计固定筛损失为(35086/33)*C_s*eta，其中C_s是明确声明的外部统一常数。
- 本轮实际区间重算给出 g4<23.60573、g5<19.51913。
  不仅保存普通浮点小数；程序保留中点余项和二维区间覆盖。

**局部状态：** uniform sieve/BV/PNT输入下的完整solver合同候选，待独立审查。
**数值状态：** 固定积分包络计算通过，人工积分恒等式/导数界仍需审查。
**全局状态：** INCONCLUSIVE；未修改旧十二项账本，未认证其他十项或完整定理。

## 实际结果

```text
g4 in [23.605651992250405827, 23.605726083520951118]
g5 in [19.519046441632147662, 19.519120458550824599]
```

方便的有理上界23.60573、19.51913各比旧显示上界减少0.00063。
只有未来相关解析输入及组合通过审查后，才可把全局条件预算余量从0.00012
改算为0.00138；这个11.5倍敏感度不是当前已验证的表示数或指数改进。

## 文件与复现

`proof.md` 给出F-ERR-009至F-ERR-014的推导；`contracts.json`与
`error-handoff.json`保存可执行合同和去重规则；`source-lock.json`记录版本与
原始来源访问限制；`results.json`保存真实区间结果；`attempt.json`绑定其余八文件。

```sh
python check_g45.py --compute
python check_g45.py --check
python check_g45.py --require-global  # expected nonzero: no global closure
```

需要mpmath 1.3.0；本轮Python 3.13.5、50位区间运算。12288个一维中点，
4096个二维区间格。二维项使用直接区间包含，没有启发式积分误差。
保存结果检查不等于重新执行完整积分；--compute才是实际重算。

前置zip内九个工件哈希和manifest自身哈希已在本轮核对。没有重跑旧MPFR套件，
没有把 sibling solver PASS 当作定理。出版社原始Iwaniec下载403，原PDF字节
未取得；U-LS的统一常数作为明确外部输入采用，不假装完成原证明审计。
Git clone仍因DNS失败，故不声称全仓测试/CI通过。没有合并或main修改。

下一实际求解对象：G1/G2下界的截断损失、有限层级和小参数一致性。
