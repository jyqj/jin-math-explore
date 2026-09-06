# A-TP-TUPLE-0008：最窄可容许元组与下一解析接口

本轮接续已合并基线 #37 和冻结 #38 的单个40元组可容许性检查；将“存在一个186构型”推进为**完整最小直径证书和构型分类**，再明确可继续尝试的解析接口。#80的活动 cap-stratification 工作及全部旧候选保持不动。

| 基数 | 最小直径候选 | 归一化最窄构型数 | 反射类 |
|---|---|---|---|
|38|176|6|3|
|39|182|26|13|
|40|186|26|13|

所有结论为 reference-only 归档的 solver proof_candidate / exact_check，尚未独立数学审查；不宣称这些最小直径是新纪录。40/184的六个模17存活状态全部在模19失败，因此**只换40个偏移量不能把直径转换界压到186以下**。这不是实际素数间隔的下界。

另给出保留40元组的端点排除条件：若同一非负权下 `sum(w*r)-sum(w)-sum(w*a*b)>0`，其中a,b表示两端点素性，则出现非端点对，距离<=184。156种计数状态全部检查，但所需加权端点相关性估计尚未获得。也保留DHL[39,2]=>182和DHL[38,2]=>176的条件前沿。

## 文件与复现

`proof.md` 给出覆盖证明、五个有范围的claim与失败边界；`certificate.json` 保存全部终层位集和各层摘要；`results.json` 保存分类结果及明确否定的全局声明。两份代码分别使用位集和有限集合；后者不导入前者。

```sh
cd docs/problem-baselines/twin-prime-conjecture/rounds/A-TP-TUPLE-0008
python enumerate_tuples.py --output-dir /tmp/twin-tuple-fresh
python verify_tuples.py --self-test --check-hashes
python -O verify_tuples.py --self-test --check-hashes
python enumerate_tuples.py --list-tuples
python verify_tuples.py --require-global   # 必须exit1，不是故障
```

从新输出目录复现后，把两份生成JSON与冻结文件逐字节比较；不把旧输出的检查当作重算。实际执行证据见 `computation-record.json`。75个小网格对照9933个字面子集，58个生产正例，20个故意篡改，156个端点检测状态均已执行。`-O`结果相同。

`source-lock.json` 区分实际读取的冻结来源、未接收的本地大文件和未完成审查；`computation-handoff.json` 是pre-project归档交接，不冒充正式Project状态；`verification-ticket.md` 仅是待审查任务，不代表已运行另一个agent。

主分支基点：`39002c5a6af8c7b7f093589e6a76cfd218fcbb99`。工作包：#85。分支：`program/i-0085/twin-tuple-obstruction-08`。本目录12个文件是完整交付物，没有必须另取的bulk数组。代码不依赖网络、CAS、Lean或FLINT。Git clone在本环境DNS失败，未本地执行全仓测试；PR中的实际CI观察单独记录。没有请求或执行合并。
