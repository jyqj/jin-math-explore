# A-TP-COUPLED-0012：联合辅助筛与恢复误差桥

接续冻结PR #112，工作包#113。全部文件为reference-only候选归档；一般证明待独立数学审查，有限计算为exact_check，不产生Project权威或新素数间隔结论。

本轮把两个独立的辅助根截断改为**联合乘积截断**。在同一总支撑预算、同一残差sup假设下，得到残差罚系数从小于5.444399改为小于2.722200的候选证明：主项系数恰好减半。真实共享素因子没有被当成独立事件，117个局部状态均计入。

另给出从数值试验H向实际恢复轮廓P_OH的稳定性桥：用未恢复双迹成本与外层删除L2误差共同控制恢复后成本，保留平方根交叉项、零容量纤维和同一归一化。它减少了下一步必须直接重算的对象，但本轮未获得实际两项输入或最终正性。

有限同模型的全部助手/Young参数优化由[0.111722941029,0.111722941030]改善为[0.079019222416,0.079019222417]；该模型不是实际186轮廓。只有残差系数减半，不能声称整个目标减半。

## 复现

```sh
cd docs/problem-baselines/twin-prime-conjecture/rounds/A-TP-COUPLED-0012
python -B coupled_sieve.py --output-dir /tmp/twin12-fresh
# 将新生成的inputs/certificates/results与冻结文件逐字节比较
python -B check_coupled.py --self-test --check-hashes
python -O -B check_coupled.py --self-test --check-hashes
python -B check_coupled.py --require-global   # 预期exit1：拒绝全局认证
```

只需Python标准库。实际执行记录见`computation-record.json`；其固定命令均完成，正常/-O输出相同。42,048个局部条目、1,801,494个剩余类乘积、180组容量、1296个CRT对照、54个双迹纤维、27项恢复转移及26项破坏测试通过。两条实现路径仍属于同一solver，不冒充隔离审查。

`proof.md`：C12-01..06完整推导与边界。`coupled_sieve.py`/`check_coupled.py`：生成和复核。`inputs.json`/`certificates.json`/`results.json`：固定输入、精确分数和结果。其余文件提供来源锁、执行记录、计算交接、独立审查任务和哈希清单。12文件均在本PR，没有额外bulk数组。

base：`39002c5a6af8c7b7f093589e6a76cfd218fcbb99`；branch：`program/i-0113/twin-coupled-sieve-12`。旧PR与#80活动范围不变；未请求合并。Git直接访问DNS失败，未本地运行全仓测试、Lean/FLINT或真实186全网格积分；仓库CI观察另记于PR。
