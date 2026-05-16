# C-Level Accession Match Review Policy

## C 级定义

C 级 accession match 指仅通过 normalized stock name、材料名称相似或 `stock_name_before_double_colon` 产生的 genotype–phenotype 候选匹配。该级别缺少 IRGC、GS_ACCNO、Source_Accno、SRA accession、BioSample 或 3K DNA/IRIS ID 等硬 ID 证据。

## 为什么不能直接使用

水稻材料存在别名、命名变体、衍生系、近等基因系、重复 stock、同名异物和数据库规范化差异。名称相似可能产生 false match。一旦把 false match 写入 trait_value_table，会造成错误 trait_state，并污染 trait-conditioned training/evaluation。因此，C 级默认排除在主 benchmark 之外。

## 人工审查字段

人工审查 C 级候选时，至少检查以下字段：

- genotype_sample_id
- genetic_stock_varname
- country_origin
- phenotype sheet / row_id
- phenotype `NAME`
- phenotype `STOCK_ID`
- phenotype `GS_ACCNO`
- phenotype `Source_Accno`
- Genesys `ACCENAME`
- Genesys `ACCENUMB`
- Genesys country / DOI / URL
- match_rule
- candidate IRGC ID

## 可升级条件

C 级候选只有满足以下条件之一，才可以升级：

- IRGC 编号精确一致，并且没有更高置信冲突。
- `GS_ACCNO` 或 `Source_Accno` 与 passport / 3K source 中的硬 ID 精确一致。
- SRA accession、BioSample 或 RunInfo 可以连接到同一 3K DNA/IRIS ID。
- 多个独立来源同时支持同一材料，并且国家来源、名称和 passport 字段无冲突。

升级后的决策值为 `accept_as_B_manual`。升级记录必须包含证据字段、审查人、审查日期、版本和理由。

## 拒绝条件

出现以下情况时，不得升级：

- 只有名称相似，没有硬 ID 证据。
- 一个 phenotype 行匹配多个 genotype，且无法区分真实 accession。
- 一个 genotype 匹配多个 phenotype 行，且无法确定重复记录或聚合规则。
- IRGC 一致但名称、国家或 passport 信息存在不可解释冲突。
- 名称一致但 IRGC / GS_ACCNO / Source_Accno 不一致。
- 存在衍生系、近等基因系或 breeding line 风险，且无额外证据。

拒绝或保留的决策值为 `keep_as_C_excluded`、`reject_as_D` 或 `needs_more_evidence`。

## 记录格式

人工审查记录至少包含：

```text
genotype_sample_id
phenotype_sheet
phenotype_row_id
candidate_values
review_decision
evidence_fields
reviewer
review_date
version
notes
```

允许的 `review_decision`：

```text
accept_as_B_manual
keep_as_C_excluded
reject_as_D
needs_more_evidence
```

## 当前策略

当前策略是默认排除 C 级候选，不进入主 benchmark。只有人工复核并获得硬 ID 证据的样本，才允许版本化升级。未升级的 C 级样本不能进入正式 trait_value_table、trait-conditioned training 或 evaluation。
