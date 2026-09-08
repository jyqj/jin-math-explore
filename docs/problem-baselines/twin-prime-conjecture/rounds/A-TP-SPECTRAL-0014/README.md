# A-TP-SPECTRAL-0014：先判断双迹费用是否有机会支付

接续本地环带13和已冻结耦合/自适应候选。工作包 #129；base
`39002c5a6af8c7b7f093589e6a76cfd218fcbb99`；本轮是solver，不是独立审查者。

**核心结果：** 在固定来源的I上界、J_lambda下界确实成立的条件下，完全对称试验H的
软匹配双迹费用，对全部允许助手容量和全部Young参数都有明确下界。这个下界是
同一冻结数值括界所给“完全不扣损失”的乐观余量的 **5.096倍以上**。
因此原环带充分验收式不能用该冻结余量证书关闭，不必先做昂贵的38维q求积。

这是费用泛函与特定证书的比较，不是未知真实余量的上界、实际双素数计数的下界，
更不是对所有筛法的否定。来源数值仍为未独立核验的条件输入。

本轮还给出有支撑的最近零双迹投影及精确修改费用。完全对称的零双迹函数会失去
所需一阶收益，因此改造必须允许指定端点打破全对称性。支撑恢复与去迹不交换，
新函数的检测与算术实现仍待研究。

## 交付历史

第12轮已由PR #121原字节发布，本PR不重复添加。PR #126的ADAPTIVE-0013是不同候选。
ANNULUS-0013来自已上传ZIP，12个文件逐字节保留并已重新运行；其检查脚本上传被工具拦截，
未重试或改道上传。本PR按Issue #129的v1.1仅提交SPECTRAL-0014的完整12文件，旧环带发布仍然阻塞。
已创建的旧档部分树不等于内容提交或完整归档；不要只按轮数判断工件身份。

## 复现

```sh
python -B spectral_gate.py --output-dir /tmp/twin-spectral-fresh
# 比较新目录inputs/certificates/results与本目录冻结文件
python -B check_spectral_gate.py --self-test --check-hashes
python -O -B check_spectral_gate.py --self-test --check-hashes
python -B check_spectral_gate.py --require-global  # 必须exit1
```

证书只依赖Python标准库精确算术。`proof.md`给出连续/任意维的证明候选；有限检查
不能替代量词覆盖。`verification-ticket.md`是待领取隔离审查任务，不代表已启动worker。
全仓本地测试因直接git访问DNS失败未运行；新PR的CI以实际观察为准。
