# Research Project instructions

本目录下每个直接子目录是一个 `$math-research-solve` v13 Project。

Project 根必须严格只包含：

```text
project.json
README.md
研究地图/
.research/
```

不要在单个 Project 根内添加 `AGENTS.md`、临时脚本、下载文件或聊天摘要；本文件为所有 Project 提供就近指令。

进入 Project 后：

1. 运行 v13 startup；
2. 只在 `v13_ready` 时继续；
3. 加载不可变 objective、双 head、完整 memory index、最新 route review、研究地图和直接相关证据；
4. proof bodies、raw objects 和日志按需读取；
5. 权威变化使用 prepare → validate → commit；
6. 计算通过 `jin-math-computation-handoff/v1` 委托给 `$math-science-computation`；
7. 不得读取 sibling Project 或 sibling attempt 的未验证 staging；
8. 一个 Project 的窗口关闭后才可生成对应研究 PR。
