# G1/G2 native lower contracts — CP-ERR-0003

Issue **#50** · `A-GB-ERR-0001` · exposed solver continuation, not independent review.
Base: `39002c5a6af8c7b7f093589e6a76cfd218fcbb99`.
Predecessor: `55f97ee95dc8d6341f42012dd1a618be25fe150d`, unchanged.
Branch: `attempt/preproject-goldbach/error-g12-03`.

## 本轮进展

保留原始截断素数集合。对N>=16、0<epsilon0<=1/2，严格证明
`1-Li((1-epsilon0)N)/Li(N) <= (32/21)*epsilon0`，无隐藏的epsilon0依赖常数。

主动降低筛水平而不改变原始G对象：
- Q1=N^(24/53)，实际s1恒为6；
- Q2=N^((4/33)*(33/8-10^-8))，实际s2也固定。

两个核参数的对数漂移因此都为零，仍保住原主项下界；代价是更大的源端起点。
保留fixed/log比较模式及其(1089/16)*h成本，避免混用两模式的优点。

实际有向区间计算：
```text
k1 = 53*psi(6) in [14.877114447209748899, 14.877115500225139932]
k2 = 33*psi(33/8-10^-8) in [9.115870447035543370, 9.115870447268373959]
k2,0 = 33*psi(33/8) in [9.115870450628733126, 9.115870450861563771]
```
k1是本轮的较低水平比较系数，不是论文f(53/8)主系数的精确重算。

在明确U-LS/U-BV/U-PNT输入下，3G1+G2的归一化总亏损候选为
`(1760/21)*epsilon0 +45*q_alpha +10*q_beta +384*e_star +8*L*C_BV*log(N)^(2-A0)`。
固定损失与衰减损失已分离；没有把不明源端常数当作数值零。
完整推导见proof.md式(30)-(48)，F-ERR-015至020；contracts/error-handoff保存机读接口。

## Reproduction

```sh
python check_g12.py --compute
python check_g12.py --check
python check_g12.py --require-global  # expected exit 1
```
需要mpmath 1.3.0。12288个中点、50位区间对数、人工证明的二阶导数余项。
冻结后的--compute只重算对比，不覆盖results.json；--check只检查保存证书。
486个有限符号检查和8个负面控制不替代一般数学证明或源定理审查。

本轮实际检查前置zip的八个工件哈希。新manifest绑定其余八个文件。
原PDF字节与全仓checkout获取均失败DNS；不声称原始论文重审、全仓测试、
旧MPFR套件重跑或独立验证。没有修改任何旧候选、全局账本或main。

**局部：** 外部统一输入下的solver候选及实际端点数值证书。
**全局：** INCONCLUSIVE，未证明十二项闭合或哥德巴赫猜想。
下一同类任务：G6的双素数下界、对角和去公因子分支；独立审查另行隔离。
