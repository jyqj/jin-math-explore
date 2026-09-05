# A-GB-G7-0001 — G7 legal-domain repair

Issue **#41** · checkpoint **CP-G7-0001** · solver candidate, not independently verified.
Base: `70484b065fc3b6a64f06955a5f9c895531750891`.
Branch: `attempt/preproject-goldbach/g7-domain-01`.

## 本轮实际结果

继承 v0.3 的 G7 域缺口与 1D 降维，不重编号旧结论。

1. 先在原非负筛和上限制到 `u+v<=37/106-h_N`，再调用下界筛。
2. 明确区分条带损失 `(14045/16)h_N^2` 和全保留域参数漂移
   `(70225/132)h_N`；后者不能遗漏。
3. 发现并记录式 (5.32) 展开漏保留 `3/11` 上限的新局部问题。
   应使用 `min(3/11,37/106-u)`；多算的正三角贡献至多 `1/557568`。
4. 在正确矩形上舍去非负高阶修正，仍实际认证得到
   `I0 in [3.790296429629882382, 3.790299606400463397]`，故 `g_R>=I0>3.79029`。
5. 利用提取素因子与小筛因子的大小分离，给出经典 BV 余项汇总候选，
   不消费待审的 L35 sibling 结论。

## 证据边界

`proof.md` 是完整的局部 solver 候选；`results.json` 是新运行的比较积分证书。
它的数值误差由分段二阶导数上界控制，不采用自适应积分器的误差估计。
导数界与积分到筛计数的解析转移仍须人工独立验证。
上端点只属于 I0，不是完整 g_R 的上界。

外部筛法、BV/PNT 作为明确输入采用，未在此重证。
旧文件原始字节未重新导入；PDF 哈希仍为空；v2 HTML/PDF 内部日期差异已登记。
旧 MPFR 证书未重跑，不把当前运行冒称为独立复核。

## Files and reproduction

- `proof.md`: legal cutoff, two losses, new source correction, numerical derivative
  proof, and classical-BV/PNT transfer with quantified scope.
- `source-lock.json`: source locators, visual checks, legacy reported commitments.
- `claims.json`: eight new local IDs and non-implication boundaries.
- `check_g7.py`, `results.json`: runnable directed numerical certificate and output.
- `error-handoff.json`: seven signed terms / corrections for the global ledger.
- `computation-handoff.json`: actual backend, command and trust basis.
- `attempt.json`: candidate status and hashes of all other files.

```sh
python check_g7.py --compute   # actual interval computation; requires mpmath 1.3.0
python check_g7.py             # arithmetic, serialization and manifest checks
```

No full repository checkout was available, so repository-wide tests and CI
are not claimed. The attempt does not modify main, any sibling candidate,
Project heads, registry or catalog. No merge-intended attempt PR is opened.
Next: independent review of this frozen package, then `A-GB-ERR-0001`.
