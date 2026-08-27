# Skill setup

## 仓库 Skills

Codex 从仓库根启动时会发现 `.agents/skills/` 下的仓库专用 Skills。

## 基础 Skills

仓库已经在 `.agents/skills/` 内 vendoring `skill-dependencies.json` 中锁定的：

- `math-research-solve` 1.11；
- `math-science-computation` 1.11。

Codex 从仓库根运行时直接发现它们。备用发现位置仍包括：

```text
$JIN_MATH_SKILLS_ROOT/<name>
$CODEX_HOME/skills/<name>
~/.agents/skills/<name>
```

执行只读诊断：

```bash
python scripts/check_skill_dependencies.py --root .
```

要求当前机器实际可运行时使用：

```bash
python scripts/check_skill_dependencies.py --root . --strict
```

严格检查会读取 `vendored-skills.lock.json`，重算全部文件 SHA-256、精确文件集合和 Git executable bit。`package_tree_sha256` 同时与发布包的 `SOURCE_VERSIONS.json` 元数据绑定。

修改基础 Skill 时必须使用独立 `[infra][skill]` 变更，重新生成锁文件并提供与来源树的差异说明；不得与数学 authority 变更混合。
