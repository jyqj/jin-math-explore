# CP-ERR-0008 独立审查任务（未执行）

冻结输入是本 PR 最终 head 下的13个文件；`artifact-sha256.json` 绑定其他12个文件。
准确提交号和树见 #92 / PR 最终交接；不得用可变分支替代冻结 hash。
新执行上下文、新 run_id、independent_verifier 角色；不能继承 solver 对话，不能修改候选。
本票据不启动 worker、不授予 lease，也不构成 receipt。修正须另开候选。

## 检查范围

V1. 从 Li-Liu v2 还原 G1/G2、p<(1-epsilon0)N、两个固定筛界及归一化。k1=53psi(6)不是原 f(53/8)主系数的精确重算。核对权重3、1和最终除4。

V2. 核对 BJS v6 Theorem6 是下界、D>=z²、实际质量 M、例外素数乘积 W_N 以及 d<W_N D；C2<=154来自所引用表和单调性，不是本轮自行验证的常数。尝试取得精确版 PDF 字节并独立绑定，原始字节缺失不得伪造。

V3. 检查 K 的 N-uniformity、小参数先固定、P0 与 W_N 的关系；实际 D_i 不除以 P0，而须支付 P0 D_i<=R 的起点条件。核对 rho、kappa2、sigma、式(11)及100倍仅为指数余量的范围。

V4. 审查经典最大端点 BV 至 pi/Li 的换算，包括素数幂、积分自2起的常数、d=1、严格端点及 B=A0+8。不得使用 CP6 候选充当经典输入；也不得以此声称有效数值 C_BV/N0。

V5. 重证 r_M=r-Delta/phi、倒数totient引理和 (4+3logR)E。检查负 Gamma 的反例、|Gamma|<=2、两行共享质量而须付权重，以及 extra log 导致 A0>3。

V6. 核对 R_i 的所有常数2/4、C(N)>=1/2、有限奇异乘积恒等式、大 p|N 尾项、epsilon0截断。独立推出两行和组合的全部系数，尤其 epsilon 的4081/50、1089/2、19734/25及 BV 的15/60。

V7. 从延迟微分关系重建单积分、4<=s<=6的导数界、s=6端点和 midpoint 余项。重跑 `python check_lower.py --compute` 的全部20,480中点，核查二进制端点转Fraction及18位向外舍入，不能用--check冒充求积复现。

V8. 核对新 rho=1e-6 的G2 lower9.11587009、比旧floor稍差的取舍，以及rho=2e-6的固定核失败。这些区间不能变成真实G_i计数的上下界，更不是全部筛法的不可行边界。

V9. fixed/log模式另付1089/16*h_star；审查psi单调性与小区间界，拒绝混用宽松起点和零漂移。检查每行最终误差delta的共同参数选择、delta=4e-8例子、未提供数值N0的界限。

V10. 运行--check、-O --self-test和预期失败的--require-global，确认12哈希、10,106有限项和22负面控制。检查13项纯新增远端diff；原候选和全局账本不变。报告源导入、有限检查、数值证书、解析论证与全局状态的不同等级。

## 输出

逐项 PASS / FAIL / INCONCLUSIVE，记录 exact candidate/source hashes、首个错误或缺失假设、实际命令及 cannot_imply。
局部 PASS 不闭合原 Iwaniec 审计、剩余十项、组合引理、全篇论文或二元哥德巴赫。
独立 receipt 需另取工作包、lease、分支；本轮作者不代写它。
