# Problem selection policy

## 候选来源

- 权威文献中明确提出的 open problem；
- 已知定理的自然但未解决推广；
- 关键证明中的缺失桥梁；
- 最优常数、临界指数、边界正则性或量词强化；
- 计算异常和反例空间；
- 多个活动项目共同依赖的基础 lemma。

## 必须分开的分类

```text
known_open
likely_open_needs_audit
internal_frontier
missing_lemma
computational_conjecture
generalization
optimality_question
counterexample_search
```

## 调度依据

调度可使用：

- frontier 清晰度；
- 是否存在决定性实验；
- proof object 多样性；
- verification debt；
- 已知失败模式是否重复；
- 共享 lemma 的下游影响；
- 计算和审查成本；
- 上一窗口的信息增益；
- source freshness。

禁止把模型主观“成功概率”、多数投票或叙事信心作为数学证据或完成依据。
