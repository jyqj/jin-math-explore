# Cross-project transfer policy

跨项目复用分为：

- `shared_lemma`
- `shared_method`
- `shared_computation`
- `shared_obstruction`

来源对象必须已经独立验证，并登记到 `registry/shared-results/`。目标 Project 必须创建 import proposal，核查：

1. 定义是否一致；
2. 假设是否在目标项目成立；
3. 量词和对象类别是否匹配；
4. source claim 和 commit/hash 是否仍有效；
5. `cannot_imply` 是否被保留；
6. 是否需要目标项目内重新验证。

未验证的 staging、聊天摘要、Issue 评论或 sibling attempt 输出不可跨项目传播为权威输入。
