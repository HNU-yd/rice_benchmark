# Weak Evidence Chr1 Mapping Summary

本报告记录 v0.1-mini chr1 输入骨架中的 weak evidence 关键词匹配结果。

## 总览

- chr1 weak evidence candidates：543。
- 有坐标 candidates：42。
- 无坐标 candidates：501。

## 按来源统计

- Oryzabase：501。
- Q-TARO：42。

## 按冻结 trait 统计

- `CUAN_REPRO`：23。
- `CUDI_CODE_REPRO`：38。
- `CULT_CODE_REPRO`：210。
- `FLA_REPRO`：25。
- `LLT_CODE`：57。
- `LSEN`：33。
- `PEX_REPRO`：2。
- `PTH`：4。
- `SPKF`：151。

## 审计口径

Oryzabase / Q-TARO 只作为 `weak localization evidence`。坐标体系仍需后续验证，所有候选均不能写成 `causal ground truth`。没有匹配 evidence 的区域仍是 `unknown_unlabeled`，不能作为 negative。
