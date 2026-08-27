# Skill setup

## 仓库 Skills

Codex 从仓库根启动时会发现 `.agents/skills/` 下的仓库专用 Skills。

## 基础 Skills

本计划还需要 `skill-dependencies.json` 中锁定的：

- `math-research-solve` 1.11；
- `math-science-computation` 1.11。

默认发现位置包括：

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

当前检查只确认 Skill 入口存在，尚未重新计算发布树哈希。安装器或后续依赖适配器必须根据 `skill-dependencies.json` 核对版本和 package tree SHA-256。

完整 payload 在许可证/发布方式明确前不复制进本公开仓库。修改基础 Skill 时使用独立 `[infra][skill]` PR，不得与数学 authority PR 混合。
