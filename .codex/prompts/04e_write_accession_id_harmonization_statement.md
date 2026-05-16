# 04e_write_accession_id_harmonization_statement.md

你现在执行 accession ID harmonization 情况说明文档撰写任务。

项目名称：3K Rice SNP/indel Trait-conditioned Localization Benchmark

当前项目已经完成 accession mapping 草稿，核心结果为：

- genotype union samples: 3024
- core SNP samples: 3024
- indel samples: 3023
- pruned SNP samples: 3024
- Qmatrix samples: 3023
- 3K_list_sra_ids coverage: 3024 / 3024
- NCBI RunInfo coverage: 3024 / 3024
- Genesys MCPD coverage: 2706 / 3024
- phenotype 任意匹配: 2281 / 3024
- phenotype A/B 可用匹配: 2269 / 3024
- phenotype confidence:
  - A = 0
  - B = 2269
  - C = 12
  - D = 743

本任务目标是写清楚 accession ID 对齐问题，形成后续论文、补充材料、审稿回复和项目文档都能引用的说明。

---

## 1. 本任务目标

创建：

```text
docs/accession_id_harmonization.md
reports/accession_mapping/accession_id_harmonization_statement.md
reports/accession_mapping/C_level_review_policy.md
````

可根据已有结果更新：

```text
reports/accession_mapping/accession_mapping_summary.md
README.md
```

但不要重写 accession mapping 代码。

---

## 2. 本任务禁止事项

禁止：

```text
不要下载新数据
不要修改 raw data
不要重跑 accession mapping 主流程
不要构建 trait_value_table
不要构建正式 benchmark schema
不要训练模型
不要跑 GWAS
不要把 C 级名称匹配纳入主分析
不要把 phenotype 当 prediction target
不要把 weak evidence 写成 causal ground truth
不要提交 data/raw 或 data/interim
```

---

## 3. 需要读取的文件

读取以下文件，如果存在：

```text
reports/accession_mapping/accession_mapping_summary.md
reports/accession_mapping/genotype_mapping_coverage.tsv
reports/accession_mapping/phenotype_mapping_coverage.tsv
reports/accession_mapping/mapping_confidence_summary.tsv
reports/accession_mapping/manual_review_candidates_preview.tsv
data/interim/accession_mapping/accession_mapping_master.tsv
data/interim/accession_mapping/manual_review_candidates.tsv
data/interim/accession_mapping/phenotype_to_genotype_candidate_matches.tsv
reports/current_data_status/project_data_status_summary.md
```

注意：`data/interim/` 只读取，不提交。

---

## 4. docs/accession_id_harmonization.md 内容要求

主体中文，语气正式、清楚、适合后续论文方法部分和补充材料引用。

必须包含以下部分：

### 4.1 背景

说明 3K Rice 数据来自多个系统：

```text
genotype / PLINK / Qmatrix
phenotype XLSX
3K_list_sra_ids
NCBI RunInfo
Genesys MCPD passport
SRA / BioSample / Run metadata
```

这些数据使用不同 ID 体系，不能直接一列对应一列。

必须说明：

```text
genotype 端通常使用 B001 / CX / IRIS_313 等 3K DNA/IRIS ID；
phenotype 端使用 STOCK_ID / GS_ACCNO / NAME / Source_Accno 等 accession-like 字段；
SRA 使用 ERS / ERR / BioSample / Run；
Genesys 使用 ACCENUMB / ACCENAME / passport 字段；
因此直接 overlap 为 0 或较低是正常的多源数据整合问题。
```

---

### 4.2 为什么会不匹配

必须分条解释：

```text
1. genotype ID 和 phenotype ID 属于不同数据系统。
2. 一个材料可能存在多个名称、别名、IRGC 编号和 stock 编号。
3. SRA / Run / BioSample 是测序元数据层，不等同于 phenotype accession。
4. Genesys MCPD 覆盖约 2700 个 accession，不覆盖完整 3024 个 genotype 样本。
5. phenotype 表不是所有 genotype accession 都有表型记录。
6. 名称匹配容易产生假阳性，因此不能直接使用。
```

---

### 4.3 使用的数据源

列出每个数据源及作用：

```text
core_v0.7.fam.gz：
  SNP genotype sample ID 来源。

Nipponbare_indel.fam.gz：
  indel genotype sample ID 来源。

pruned_v2.1.fam：
  pruned SNP sample ID 来源。

Qmatrix-k9-3kRG.csv：
  群体结构和 sample ID 辅助来源。

3K_list_sra_ids.txt：
  3K DNA/IRIS ID ↔ stock name ↔ country ↔ SRA accession 的主桥梁。

PRJEB6180_runinfo.csv：
  SRA accession ↔ Run / Experiment / BioSample / LibraryName 的补充桥梁。

Genesys MCPD：
  IRGC / passport / accession name / country / DOI 的补充来源。

3kRG_PhenotypeData_v20170411.xlsx：
  trait_state 的原始 phenotype 来源，不作为 phenotype prediction target。
```

---

### 4.4 ID 对齐链路

写清楚主要链路：

```text
genotype sample ID
→ 3K DNA/IRIS ID
→ stock name / SRA accession
→ NCBI RunInfo / BioSample / Run
→ Genesys passport / IRGC / accession name
→ phenotype STOCK_ID / GS_ACCNO / NAME / Source_Accno
```

说明这是一条多证据链，而不是单字段匹配。

---

### 4.5 置信度分级

必须定义 A/B/C/D。

建议写法：

```text
A 级：
  phenotype 表中直接出现 genotype sample ID 或 3K DNA/IRIS ID 的精确匹配。

B 级：
  通过 SRA accession、IRGC、GS_ACCNO、Source_Accno 或多源 ID 证据链建立的高置信匹配。

C 级：
  仅通过 normalized stock name 或材料名称相似建立的候选匹配，缺乏硬 ID 支撑。

D 级：
  没有可用 phenotype mapping。
```

必须明确：

```text
主 benchmark 只使用 A/B 级。
C 级只进入人工审查，不进入主分析。
D 级不进入 trait-conditioned training/evaluation。
```

---

### 4.6 当前映射结果

写入当前数字：

```text
3024 个 genotype 样本中：
- 3024 个可以匹配到 3K_list_sra_ids；
- 3024 个可以匹配到 NCBI RunInfo；
- 2706 个可以匹配到 Genesys MCPD；
- 2269 个具有 A/B 级 phenotype mapping；
- 12 个只有 C 级名称候选匹配；
- 743 个没有 phenotype mapping。
```

说明：

```text
2269 个 A/B 级样本将作为 trait-conditioned prototype 的 high-confidence accession subset。
C 级和 D 级不进入主 benchmark。
```

---

### 4.7 C 级样本处理原则

必须单独说明。

内容包括：

```text
C 级只表示名称级候选匹配。
由于水稻材料存在别名、衍生系、近等基因系、重复 stock 和命名变体，仅靠名称相似可能产生错误 genotype–phenotype 配对。
因此 C 级样本默认不进入主 benchmark。
只有在人工复核中发现 IRGC / GS_ACCNO / Source_Accno / SRA 等硬 ID 证据时，才可以升级。
升级后的样本必须标记为 manual_reviewed，并保留审查记录。
```

---

### 4.8 C 级人工审查标准

写清楚如何审查：

```text
1. 是否存在 IRGC 编号精确一致。
2. 是否存在 GS_ACCNO 或 Source_Accno 精确一致。
3. 材料名称是否唯一匹配。
4. 是否存在多个候选 genotype。
5. 国家来源是否一致。
6. 是否存在衍生系、近等基因系或命名变体风险。
7. Genesys passport 与 3K stock name 是否冲突。
```

人工决策：

```text
accept_as_B_manual
keep_as_C_excluded
reject_as_D
needs_more_evidence
```

默认策略：

```text
除非有硬 ID 证据，否则 C 级不升级。
```

---

### 4.9 为什么排除未映射样本

说明：

```text
743 个 D 级样本不是数据错误，而是当前 phenotype 数据源中没有可高置信映射的 trait 记录。
这些样本仍可用于 genotype-only 统计、MAF/LD 估计或自监督 genotype representation。
但它们不能用于 trait-conditioned training/evaluation，因为缺少可靠 trait_state。
```

---

### 4.10 审稿风险与防御

必须写一节，回答审稿人可能的问题：

```text
问题 1：为什么不是 3024 个样本都用于 trait-conditioned benchmark？
回答：只有 2269 个样本具有高置信 genotype–phenotype 映射。为了避免错误配对，主分析只使用高置信子集。

问题 2：排除样本是否造成偏差？
回答：后续将报告 included / excluded accession 的群体结构、国家来源和 genotype 可用性分布，并在固定 high-confidence subset 上构建 split。

问题 3：为什么 C 级不用？
回答：C 级仅由名称匹配产生，缺乏硬 ID 证据。为避免 false match，主分析排除 C 级样本。

问题 4：未映射样本是否作为 negative？
回答：不会。未映射或无 trait 的样本不作为 negative，也不进入 trait-conditioned 分析。
```

---

### 4.11 对后续 benchmark 的影响

说明：

```text
1. high-confidence accession subset 将被冻结。
2. trait_value_table 只从 A/B 级样本构建。
3. split 只能在 high-confidence subset 内生成。
4. C 级样本如果人工升级，必须版本化记录。
5. D 级样本不参与 trait-conditioned training/evaluation。
6. unknown / unmapped 不等于 negative。
```

---

## 5. reports/accession_mapping/accession_id_harmonization_statement.md

这个文件是短版说明，用于报告和论文草稿。

要求：

```text
800-1500 字中文
语言正式
不写代码细节
强调多源 ID 体系差异、映射置信度、样本纳入标准
```

必须包含当前关键数字：

```text
3024 genotype samples
2269 A/B high-confidence phenotype mappings
12 C-level name-only candidates
743 unmapped samples
```

---

## 6. reports/accession_mapping/C_level_review_policy.md

这个文件专门说明 C 级样本如何处理。

必须包含：

```text
1. C 级定义
2. C 级为什么不能直接用
3. C 级人工审查字段
4. 可升级条件
5. 拒绝条件
6. 记录格式
7. 当前策略：默认排除主 benchmark
```

---

## 7. 可选：生成 C 级预览表

如果 `manual_review_candidates.tsv` 存在，请生成：

```text
reports/accession_mapping/C_level_candidates_for_review.tsv
```

只包含 C 级候选。

字段：

```text
genotype_sample_id
genetic_stock_varname
country_origin
phenotype_sheet
phenotype_row_id
phenotype_name
phenotype_stock_id
phenotype_gs_accno
phenotype_source_accno
genesys_accename
genesys_accenumb
match_rule
recommended_action
notes
```

---

## 8. Git 提交要求

不要提交 `data/raw/` 或 `data/interim/`。

提交：

```bash
git add docs/accession_id_harmonization.md reports/accession_mapping README.md docs
git commit -m "document accession ID harmonization policy"
git push
```

如果 README/docs 没有变化，可以只提交新文档和报告。

---

## 9. 最终回复要求

完成后用中文报告：

```text
1. 当前工作目录
2. 生成的文档
3. 当前 accession mapping 关键数字
4. A/B/C/D 分级是否写清楚
5. C 级审查规则是否写清楚
6. 是否明确 C/D 不进入主 benchmark
7. Git commit / push 状态
8. raw/interim data 是否未进入 git
9. 下一步
```

下一步应该是：

```text
基于 A/B 级 high-confidence accession subset 构建 trait_state prototype；C 级只做人工审查，不进入主分析。
```

现在开始写 accession ID harmonization 情况说明。

````

---

这个文档写完后，后面所有地方都按这个口径：

```text
不是“有些样本没对上”。
而是“我们进行了多源 ID harmonization，并只使用高置信映射样本，避免错误 genotype–trait 配对”。
````

这个表述很重要。它会直接影响审稿人对数据质量的判断。
