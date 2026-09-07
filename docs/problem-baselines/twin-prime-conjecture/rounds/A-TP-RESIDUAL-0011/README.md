# A-TP-RESIDUAL-0011：双端点残差上筛与软迹匹配

接续冻结PR #105 / #100，本轮给出残差费用的统一渐近估计候选，而不是继续调已失败的普通单纯形多项式。

**核心结果候选：** 对固定sup界的有符号残差数组，两个辅助Selberg平方给出
`residual_pair / C_x <= rho_*^2/(z_a*z_b) * ||u||² + o(1)`，条件为`2gamma+2z_a+2z_b<1`。证明保留两个辅助根相互及与保留根的共享素数；没有假定坐标独立，也没有把T10依赖r的最小提升容量错误因式分解。此残差上界不需要素数分布估计；助手自身的单素数项仍需合法支持与分布契约。

实际40维对应156个局部状态，精确误差多项式为
`2099t²+14700t³+16493t⁴-14630t⁵-4142t⁶`。
选择严格可用的`z_a=z_b=9/80`，罚系数小于5.444399；5.4106656079附近的数值只是截止族的不可取边界下确界。

**助手推进：** 给出允许残差的精确软匹配公式，零容量纤维也有有限、明确的费用。将Young参数改写为theta后，整个目标为一维凸函数。固定有限模型的全部实助手系数、全部正Young参数的最优值落在`[0.111722941029,0.111722941030]`。这不是实际186权或有限区间素数平方和的数值。

## 完整复现

```sh
cd docs/problem-baselines/twin-prime-conjecture/rounds/A-TP-RESIDUAL-0011
python -B sieve_product.py --output-dir /tmp/twin-residual-fresh
# compare fresh inputs.json / certificates.json / results.json with frozen bytes
python -B check_sieve_product.py --self-test --check-hashes
python -O -B check_sieve_product.py --self-test --check-hashes
python -B check_sieve_product.py --require-global # expected exit1
```

代码只用Python标准库整数和Fraction。全部结果、26类内核计数、有限CRT证书和助手最优括区间都在本目录；无外部bulk数组依赖。实际检查包括74,752项局部核、3,202,656个剩余类乘积、104,976个CRT系数对、1000个区间整数及23项破坏/非法参数测试。

`proof.md`给出R11-01..05及范围；`source-lock.json`锁定来源与历史；`computation-record.json`记录实际执行；`verification-ticket.md`是未执行的隔离审查任务。`artifact-sha256.json`绑定其余11个文件。

本包为reference-only的solver候选，不是独立数学审查或Project状态事务。下一缺口是真正恢复后的双迹、合法助手的单素数评价和同尺度正性比较；没有新的184界或孪生素数证明。工作包#108，base `39002c5a6af8c7b7f093589e6a76cfd218fcbb99`，分支`program/i-0108/twin-residual-sieve-11`。未请求合并；远端CI观察在PR/Issue交接中，不等同于数学验证。
