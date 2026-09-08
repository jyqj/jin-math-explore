# A-TP-ADAPTIVE-0013：按根分配辅助预算

接续已补交PR #121中的C12。工作包#122；一般推导为proof_candidate，有限计算为exact_check，尚无独立数学审查。

把所有保留根统一使用的辅助截止改为 `Z_r=x^ell/prod(r)`，在同一严格计数预算下得到变罚系数 `2rho^2/(ell-log_x(prod r))^2`。小根费用下降，最大根的最坏常数不变。所有跨组共享素数和不同保留根间的交叉项都保留。

由同一总质量支撑及密度输入，恢复误差的粗上界系数从 `gamma^2/[theta(ell-gamma)^2]` 改为 `gamma^2/(theta*ell^2)`：实际参数下，新界是旧界的精确比例 `5062500000000/24930019042009`，约20.31%。这是误差乘子的改进，不是实际恢复误差、整个目标或素数间隔按比例改进。

同一有限区间平方上界从约3.724780降至3.654824；同时保存n=1043处新平方反而较大的精确反例，排除无条件有限单调性。另一个抽象有限助手模型取得全部参数的有理凸最小值证书；它不是实际186轮廓。

```sh
cd docs/problem-baselines/twin-prime-conjecture/rounds/A-TP-ADAPTIVE-0013
python -B adaptive_sieve.py --output-dir /tmp/twin13-fresh
# 比较新生成inputs/certificates/results与冻结字节
python -B check_adaptive.py --self-test --check-hashes
python -O -B check_adaptive.py --self-test --check-hashes
python -B check_adaptive.py --require-global  # expected exit1
```

两份代码只需Python标准库。完整12文件含推导、代码、输入、证书、结果、来源、执行/交接记录、审查任务及哈希，无额外bulk依赖。checker的字面剩余类与直接除数反演是不同代码路径，但同一solver上下文不是独立verifier。

初版负面检查混淆了“删除原始共享根”和“删除已证明同余冲突的除数项”，实际失败后已修正、分别验收，记录未被抹去。实际恢复函数的q/a、合法助手素数契约和检测正性仍缺失，未得到新的prime-gap界或孪生素数证明。

base `39002c5a6af8c7b7f093589e6a76cfd218fcbb99`；branch `program/i-0122/twin-adaptive-sieve-13`；run `run-20260908-twin-adaptive-13`。原始C12在独立PR121补交，本轮不更改它。未请求合并；本地全仓测试/Lean/FLINT未运行，远端CI按实际观察另记。
