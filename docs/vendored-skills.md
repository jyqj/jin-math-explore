# Vendored base Skills

本仓库 vendoring 以下完整基础 Skill：

| Skill | Release | Files | Declared package tree SHA-256 |
|---|---:|---:|---|
| `math-research-solve` | 1.11 | 249 | `249daaa15b9f6d0dc61ca1d7e26db6b761beadb096cd60e3dc36778f88e60ca4` |
| `math-science-computation` | 1.11 | 28 | `5c084b5202b747275a9e5c7d44c2636a89d984ab3a13a8c4dd92f94796e676c5` |

## 来源

- Artifact：`pika_math_learning_toolkit-1.11`
- Release manifest version：`1.11`
- 原始目录：artifact 的 `payload/<skill-name>/`
- Vendored 目录：`.agents/skills/<skill-name>/`

复制时两个目标目录分别与 artifact payload 执行递归逐文件比对，结果无差异。`vendored-skills.lock.json` 保存 277 个普通文件的相对路径、SHA-256 和 Git 可表达的 executable bit。

## 不可变边界

- 不在 vendored payload 内添加仓库适配文件、报告或配置。
- 仓库专用流程继续放在独立 `.agents/skills/math-*` 目录中。
- 基础 Skill 更新使用独立基建变更，并同时更新版本、发布树哈希和逐文件锁。
- `python scripts/check_skill_dependencies.py --root . --strict` 必须通过。

## 当前验证记录

在 Apple Silicon macOS 上完成：

- 两个 vendored 目录与 release payload 的递归逐文件比对：无差异；
- 277 文件 SHA-256/executable inventory：PASS；
- terminology validators：PASS（36 + 2 terms）；
- computation MCP policy：PASS；
- backend routing policy：PASS；
- static platform parity：PASS（71/71 PowerShell mappings）。

完整 native parity test runner 没有全绿：多项 legacy/control-path 测试把 macOS `/var` 到 `/private/var` 的系统符号链接视为被禁止的 control-path symlink，另有 asset 测试因同一临时目录路径规范化差异失败。这与 release 对 macOS 的 `implemented-unverified` 标记一致。为保持 vendored payload 原样，本次不在复制内容内修补；后续使用独立 Skill 修复变更处理，不能把本次 focused/static PASS 宣称为完整 macOS runtime 验证。

## 许可证状态

来源 artifact 未包含独立许可证文件，本仓库本身也尚未选择开源许可证。当前公开提交记录的是仓库所有者明确要求 vendoring 的发布内容；在许可证状态改变前，不额外声明第三方再分发权利。
