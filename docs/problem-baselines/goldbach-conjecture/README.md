# 哥德巴赫猜想 pre-genesis 基线

**协调 Issue：** `#27`  
**来源刷新边界：** `2026-08-31`  
**继承快照：** `Goldbach_Research_Ledger_v0.3.md` / `secondary_conclusions_v0.3.json`  
**权限等级：** `reference_only`

本目录先完成两件事：

1. 把哥德巴赫问题的人类既有进展、当前来源状态和逻辑边界整理成可复用基线；
2. 把此前 v0.1–v0.3 研究的结论、证书、修复和未闭合依赖迁移为可审计的继续研究入口。

它不创建 v13 Project，不宣称证明二元哥德巴赫，也不把 `1+1.9` 预印本、异常集预印本或有限计算升级为已独立验证数学。

## 导航

- [目标、表述与当前状态](objective-and-status.md)
- [进展与依赖总账](progress-ledger.md)
- [方法、障碍与已知能力边界](methods-and-barriers.md)
- [此前项目结论迁移](prior-project-conclusions.md)
- [来源审计](source-audit.md)
- [后续 frontier 与迁移计划](frontier-and-migration.md)
- [`claims.json`](claims.json)：机器可读的快照承诺、关键 claim 与依赖状态
- [`references.bib`](references.bib)：本基线直接使用的来源

## 当前最早未闭合点

此前研究没有停在“还要继续研究”的泛化描述，而是把最早关键缺口定位为：

1. `G_7` 对 Lemma 2.5 的合法域截断与边界层；
2. Lemma 3.5 在 `G_9,G_11,G_12` 上逐 dyadic block 的完整实例化；
3. 十二项不等式的带符号统一误差、量词顺序与共同 `N_0`;
4. 完整候选形成后的上下文隔离独立验证。

下一研究窗口因此先关闭解析接口，不先优化 `1.894`。

## Legacy payload 状态

v0.3 的 100 条 `GB-*` 结论由原始 `secondary_conclusions_v0.3.json` 的 SHA-256 承诺：

```text
03b7c7847f1c9633da9419f084683670e800b83bf1cee9eb730b68c5cb6d1ed1
```

本次提交保存其身份、分类、关键结论和依赖 frontier；由于当前 GitHub 运行上下文没有取得 File Library 原文件的原始字节，本次 **不伪造逐字副本**。精确 100-entry payload 的后续导入必须验证上述哈希后再完成。
