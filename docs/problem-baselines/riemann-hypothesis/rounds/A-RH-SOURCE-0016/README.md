# 第16轮：来源矩形矩与带误差的单胞接口

`A-RH-SOURCE-0016`，Issue #101，2026-09-07。
状态：**proof_candidate；reference-only；未经独立验证**。
接续第15轮冻结候选 `bea93a0308a7ddfd6bacc35c547ffd4ab6d5cee9`。

## 这轮推进了什么

不再把算术矩预算整体留作假设。以来源论文的固定测试函数配对关联公式为
明确输入，构造内外多项式包络，完成无权矩形矩的候选推导：对每个**固定
带宽 `0<b<1`**，实际 ζ 零点的归一化矩趋于 `1/b+b/3`。推导不需要单胞表示、
统一深度上界或逐项正性；来源定理本身没有在本轮独立验证。

严格保留三个区别：`b<1` 不等于临界端点 `b=1`；固定带宽不等于随高度移动的
带宽；真实零点数归一化不等于每单位长度质量一。双尺度使用同一组零点，
预算为 `kappa(theta)` 与 `kappa(3theta/4)`，不能直接写成理想端点预算。

几何接口现在有明确的账本：删去的部分以**深度加权的局部质量平方和**收费；
保留部分的给定单胞匹配以加权位移和深度误差收费；另外保留质量、简单点计数
和有限到周期化的误差。该账本尚未为实际零点构造低代价匹配。

反例同时说明，删除比例趋零不代表算子误差趋零：一族互异实点聚集可保持
正的归一化删除能量；单个越来越深的反射对也会造成大误差。它们不是实际
ζ 零点或两预算逃逸模型。

## 文件与实际复现

[proof.md](proof.md) 包含候选证明、源定理输入、固定参数的极限顺序与反例；
[claims.json](claims.json) 记录八项范围化结论；[source-scope.md](source-scope.md)
记录版本、父级依赖和未解决的接口。

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python check_source_bridge.py --samples 120 --output /tmp/rh16-validation.json
python check_source_bridge.py --check-package
```

依赖 Python、NumPy、mpmath、SymPy。本轮实际版本为 3.13.5、2.3.5、1.3.0、1.14.0。
一次六样例开发检查后，最终120样例运行通过：360项删除、360项传递、360项
源到模型上界检查，240项内外包络检查，240项去权恒等式向量检查，36项独立
数值积分比较，以及1,419项符号／整数／有理检查。计数细目见
[validation.json](validation.json)，不把重复尺度或向量元素当作独立证明。
最大积分／核残差约 `7.85e-12`。没有运行实际零点枚举或验证来源渐近式。

小型随机样例上的最终父级可行性不等式较保守、实际为空泛下界；它们只测试
实现一致性，不证明一个实际来源匹配成功。计算记录和哈希见
[computation-record.json](computation-record.json)、
[computation-handoff.json](computation-handoff.json)、[checkpoint.json](checkpoint.json)。

## 下一处缺口

`A-RH-MATCH-0017`：建立或反驳同时控制深度尾部、局部聚集和位移的轨道级
单胞匹配。临界带宽端点、来源的统一移动参数估计与保留深度上界也未建立。
本轮不是新无条件零点比例，更不是 RH 证明；数学审查与机械 CI 分开记录。
