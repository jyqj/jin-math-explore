# Evidence policy

## 等级

| 等级 | 含义 | 不足以推出 |
|---|---|---|
| `conjecture` | 尚无可靠证据的精确命题 | 真实性 |
| `heuristic` | 结构直觉或非严格论证 | 有限或无限范围真值 |
| `numerical_evidence` | 浮点、采样或模拟结果 | 精确真值与一般定理 |
| `bounded_check` | 在明确有限区域内穷举/检查 | 区域外或无限量词 |
| `exact_check` | 对指定对象、恒等式或有限证书的精确计算 | 未覆盖量词或概念性证明 |
| `proof_candidate` | 完整候选证明，尚未独立通过 | 已验证定理 |
| `independently_verified` | 独立审查者对冻结候选 PASS | 审查范围之外的结论 |
| `verified_refutation` | 独立验证的反例或反驳 | 更宽命题的全面分类 |
| `verified_impossibility_boundary` | 独立验证的不可行边界 | 边界外路线不可行 |
| `withdrawn` | 已撤回，不可继续作为依赖 | 任何正面结论 |

## Claim 必备字段

- 精确 statement；
- domain 和 quantifier scope；
- assumptions；
- dependency hashes；
- evidence grade；
- evidence refs；
- `cannot_imply`；
- source/novelty boundary；
- verifier receipt（若声称独立验证）。

## 机械验证边界

Schema、哈希、路径和复现 smoke test 不能判断：

- 证明逻辑是否正确；
- 引用定理是否适用；
- 量词是否完整覆盖；
- 计算模型是否忠实于原问题；
- claim 是否真正新颖。

这些必须由独立数学审查完成。
