# Pull Request protocol

## 一个窗口一个 PR

研究 PR 推荐以完整关闭的 window 为单位。Attempt staging 可以位于独立 worktree/branch，但不分别推进 `main` 上的项目 authority。

## PR 必须绑定

- Project ID；
- objective commitment SHA-256；
- base commit；
- expected project/research/execution heads；
- window ID；
- 三个 attempt package；
- verifier receipts；
- reconciliation result；
- map/memory/route-review 变化；
- computation handoffs；
- evidence grades 和 `cannot_imply`。

## 分离原则

- `[infra]` PR 可以改变协议、schema、Skill 或 CI，但不得同时发布依赖新规则的数学结论。
- `[window]` PR 使用 `main` 上已存在的协议。
- `[terminal]` PR 不得夹带协议修改或额外研究。
