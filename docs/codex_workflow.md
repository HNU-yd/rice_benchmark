# Codex Workflow

每次 Codex 任务都应按小 PR 处理：目标清楚、文件改动有边界、检查步骤可复现。

Codex 不应在一次任务中实现大模块。工作需要按阶段推进，使每一步都能先接受科研范围、工程质量和可复现性审阅，再进入下一阶段。

## 必须报告的任务信息

每次任务完成后必须报告：

- Goal。
- Files changed。
- Commands run。
- Tests or checks run。
- Outputs generated。
- Known limitations。
- Whether README/docs were updated。

## 文档规则

新增或修改 Python 代码时，必须在同一任务中更新 README 或对应 docs。

