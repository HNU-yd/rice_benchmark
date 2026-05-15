# 审阅清单

每次 Codex 任务完成后，使用本清单检查改动是否仍符合项目边界。

- 是否违反 3K Rice only？
- 是否违反 SNP + indel only？
- 是否把任务写成 `phenotype prediction`？
- 是否引入 `trait classification`？
- 是否把 `weak localization evidence` 写成 `causal ground truth`？
- 是否把 unknown variants 当成 negative labels？
- 是否跳过 source inventory 并直接假设数据格式？
- 是否覆盖 raw data？
- 是否动态随机切分 split？
- 是否新增代码但没有更新 README/docs？
- 是否新增脚本但没有 usage example？
- 是否把 Task 2 扩大到 supplementary application demo 之外？
- 是否在 v1 中引入 SV、PAV、CNV、pan-reference、multi-reference、multi-species 或 pretraining 范围？
- 生成的 outputs 是否已按要求登记或记录？
- Inputs、outputs 和 limitations 是否足够清楚，便于审阅？

