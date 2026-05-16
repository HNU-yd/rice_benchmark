# 04d_build_accession_mapping_master.md

你现在执行 accession ID 对照表构建任务。

项目名称：3K Rice SNP/indel Trait-conditioned Localization Benchmark

当前最阻塞的问题是：phenotype 表中的 accession-like 字段和 genotype 中的 B001 / CX / IRIS 样本 ID 不能直接对齐。因此，本任务目标是整合已经下载的 accession mapping 来源，构建 `accession_mapping_master.tsv` 草稿，并给每条映射标记来源、匹配规则、置信度和人工审查标记。

本任务只做 accession mapping，不构建正式 benchmark schema，不构建 trait_value_table，不训练模型，不做 phenotype prediction。

---

## 1. 项目边界

第一版 benchmark 仍然限定为：

- 主位数据：3K Rice accession-level SNP/indel genotype backbone
- 变异范围：SNP + indel
- 主任务：trait-conditioned SNP/indel localization
- 不做 phenotype prediction
- 不做 trait classification
- 不纳入 SV / PAV / CNV
- 不使用 pan-reference / multi-reference / 多物种 genotype benchmark
- weak evidence 只能作为 weak localization evidence
- unknown / unlabeled variants 不能默认作为 negative

本任务只解决 accession ID 对照关系。

---

## 2. 输入数据

请自动查找并读取以下文件。若路径不同，请在 `data/raw/` 下自动搜索相似文件名。

### genotype 样本来源

```text
data/raw/variants/snp/core_v0.7.fam.gz
data/raw/variants/indel/Nipponbare_indel.fam.gz
data/raw/variants/snp/pruned_v2.1/pruned_v2.1.fam
data/raw/metadata/Qmatrix-k9-3kRG.csv
````

### accession 对照来源

```text
data/raw/accessions/snpseek/3K_list_sra_ids.txt
data/raw/accessions/genesys/genesys_3k_mcpd_passport.xlsx
data/raw/accessions/ncbi_prjeb6180/PRJEB6180_runinfo.csv
```

### trait / phenotype 来源

```text
data/raw/traits/3kRG_PhenotypeData_v20170411.xlsx
```

### 参考已有报告

```text
reports/current_data_status/
reports/raw_data_inventory/
reports/weak_evidence_inventory/
```

---

## 3. 本任务允许创建的目录

创建：

```text
data/interim/accession_mapping/
reports/accession_mapping/
scripts/mapping/
```

注意：

```text
data/interim/ 不进入 git。
reports/accession_mapping/ 可以进入 git。
scripts/mapping/ 可以进入 git。
```

---

## 4. 本任务禁止事项

禁止：

```text
不要下载新数据
不要构建正式 accession_table
不要构建正式 trait_value_table
不要构建 genotype_table
不要构建 split
不要构建 evaluator
不要训练模型
不要跑 GWAS
不要做 phenotype prediction
不要把 phenotype 当预测目标
不要把低置信度 name match 当作正式映射
不要提交 data/raw 或 data/interim
```

---

## 5. 输出文件

必须生成：

```text
data/interim/accession_mapping/accession_mapping_master.tsv
data/interim/accession_mapping/genotype_sample_master.tsv
data/interim/accession_mapping/phenotype_accession_candidates.tsv
data/interim/accession_mapping/phenotype_to_genotype_candidate_matches.tsv
data/interim/accession_mapping/unmatched_phenotype_accessions.tsv
data/interim/accession_mapping/manual_review_candidates.tsv

reports/accession_mapping/accession_mapping_summary.md
reports/accession_mapping/accession_mapping_source_summary.tsv
reports/accession_mapping/genotype_mapping_coverage.tsv
reports/accession_mapping/phenotype_mapping_coverage.tsv
reports/accession_mapping/mapping_confidence_summary.tsv
reports/accession_mapping/manual_review_candidates_preview.tsv
```

---

## 6. ID 标准化规则

创建脚本：

```text
scripts/mapping/build_accession_mapping_master.py
```

必须实现以下标准化函数：

### 6.1 基础标准化

```text
去除首尾空格
统一大写
下划线、连字符、多个空格统一
去除括号中的多余空格
保留原始值和标准化值
```

### 6.2 IRGC 编号解析

从以下形式中提取 IRGC 编号：

```text
IRGC_53418-1
IRGC 53418
IRGC_52339-1
PR_106::IRGC_53418-1
```

输出标准形式：

```text
IRGC_53418
IRGC_52339
```

注意：`-1`、`-2` 这类后缀保留在原始字段中，但标准化匹配时可以去掉。

### 6.3 stock name 标准化

例如：

```text
KHAO_YAI_GUANG
GOBOL_SAIL_(BALAM)
PR_106::IRGC_53418-1
```

需要生成：

```text
normalized_stock_name
stock_name_without_irgc_suffix
stock_name_before_double_colon
```

### 6.4 B001 / CX / IRIS ID 检测

检测：

```text
B001
CX133
IRIS_313-11480
```

作为 `3K_DNA_IRIS_UNIQUE_ID` 风格 ID。

---

## 7. 构建 genotype_sample_master.tsv

读取：

```text
core_v0.7.fam.gz
Nipponbare_indel.fam.gz
pruned_v2.1.fam
Qmatrix-k9-3kRG.csv
```

输出：

```text
data/interim/accession_mapping/genotype_sample_master.tsv
```

字段：

```text
genotype_sample_id
snp_core_available
indel_available
pruned_snp_available
qmatrix_available
qmatrix_id
subgroup_max
subgroup_max_prob
source_sets
notes
```

要求统计：

```text
core SNP 样本数
indel 样本数
pruned SNP 样本数
Qmatrix 样本数
core SNP ∩ indel
core SNP ∩ Qmatrix
core SNP ∩ pruned SNP
```

报告写入：

```text
reports/accession_mapping/genotype_mapping_coverage.tsv
```

---

## 8. 读取 3K_list_sra_ids.txt

这个文件是主桥梁。

字段预期包括：

```text
3K_DNA_IRIS_UNIQUE_ID
Genetic_Stock_varname
Country_Origin_updated
SRA Accession
```

如果字段名有细微变化，自动识别。

需要生成：

```text
normalized_3k_id
normalized_stock_name
parsed_irgc_id
sra_accession
country
```

它负责连接：

```text
B001 / CX / IRIS ID
↔ stock name
↔ SRA accession
```

---

## 9. 读取 NCBI RunInfo

读取：

```text
PRJEB6180_runinfo.csv
```

关键字段：

```text
Run
Experiment
LibraryName
SRAStudy
BioProject
Sample
BioSample
SampleName
```

注意：

```text
3K_list_sra_ids.txt 里的 SRA Accession 很可能是 ERS 样本号。
RunInfo 里的 Sample 字段也是 ERS 样本号。
```

通过：

```text
SRA Accession ↔ Sample
```

建立连接。

输出到 master 中：

```text
sra_sample_accession
run_accessions
experiment_accessions
biosample_ids
library_names
```

如果一个 Sample 对应多个 Run，用分号连接。

---

## 10. 读取 Genesys MCPD

读取：

```text
genesys_3k_mcpd_passport.xlsx
```

主 sheet 通常是：

```text
MCPD
```

关键字段可能包括：

```text
ACCENUMB
ACCENAME
ORIGCTY
SUBTAXA
DOI
ACCEURL
```

需要生成：

```text
genesys_accenumb
genesys_accename
genesys_origcty
genesys_subtaxa
genesys_doi
genesys_url
genesys_parsed_irgc_id
genesys_normalized_name
```

匹配方式：

```text
parsed_irgc_id ↔ genesys_parsed_irgc_id
normalized_stock_name ↔ genesys_normalized_name
```

如果同名但 IRGC 不一致，标记 manual_review。

---

## 11. 读取 phenotype XLSX

读取：

```text
3kRG_PhenotypeData_v20170411.xlsx
```

不要构建 trait_value_table，只抽取 accession-like 字段。

重点字段：

```text
STOCK_ID
GS_ACCNO
NAME
Source_Accno
```

如果字段名不同，请自动寻找包含以下关键词的列：

```text
stock
acc
accno
name
source
iris
irgc
```

输出：

```text
data/interim/accession_mapping/phenotype_accession_candidates.tsv
```

字段：

```text
sheet_name
row_id
stock_id
gs_accno
name
source_accno
raw_accession_value
accession_column
normalized_value
parsed_irgc_id
normalized_name
notes
```

---

## 12. 构建 accession_mapping_master.tsv

以 genotype sample 为主表，每行一个 genotype sample。

输出字段必须包括：

```text
internal_accession_id
genotype_sample_id

snp_core_available
indel_available
pruned_snp_available
qmatrix_available

three_k_dna_iris_unique_id
genetic_stock_varname
normalized_stock_name
stock_name_before_double_colon
parsed_irgc_id
country_origin
sra_accession

run_accessions
experiment_accessions
biosample_ids
library_names

genesys_accenumb
genesys_accename
genesys_origcty
genesys_subtaxa
genesys_doi
genesys_url

phenotype_match_count
best_phenotype_sheet
best_phenotype_row_id
best_phenotype_stock_id
best_phenotype_gs_accno
best_phenotype_name
best_phenotype_source_accno

genotype_mapping_confidence
phenotype_mapping_confidence
mapping_rule
manual_review_flag
usable_for_trait_mapping
notes
```

---

## 13. 匹配置信度规则

### genotype_mapping_confidence

```text
A:
  genotype_sample_id 精确匹配 3K_DNA_IRIS_UNIQUE_ID，
  且 SRA accession 可在 RunInfo 中找到。

B:
  genotype_sample_id 精确匹配 3K_DNA_IRIS_UNIQUE_ID，
  但 SRA accession 未在 RunInfo 中找到。

C:
  只能通过名称或 IRGC 间接匹配。

D:
  无法匹配。
```

### phenotype_mapping_confidence

```text
A:
  phenotype 中存在与 genotype_sample_id / 3K_DNA_IRIS_UNIQUE_ID 的精确匹配。

B:
  phenotype 中存在与 SRA accession / IRGC / GS_ACCNO 的精确匹配。

C:
  phenotype 中只有 normalized stock name 匹配。
  必须 manual_review_flag = true。

D:
  没有 phenotype 匹配。
```

### usable_for_trait_mapping

```text
true:
  phenotype_mapping_confidence 是 A 或 B。

false:
  phenotype_mapping_confidence 是 C 或 D。
```

注意：

```text
C 级名称匹配不能直接进入正式 trait_value_table。
```

---

## 14. phenotype_to_genotype_candidate_matches.tsv

输出所有 phenotype 候选匹配，不只保留最佳匹配。

字段：

```text
phenotype_sheet
phenotype_row_id
phenotype_column
phenotype_raw_value
phenotype_normalized_value
candidate_genotype_sample_id
candidate_3k_id
candidate_stock_name
candidate_irgc_id
match_rule
match_confidence
manual_review_flag
notes
```

匹配规则包括：

```text
exact_3k_id
exact_sra_accession
exact_irgc_id
exact_gs_accno
normalized_stock_name
stock_name_before_double_colon
```

---

## 15. manual_review_candidates.tsv

输出需要人工检查的候选。

条件：

```text
同一个 phenotype 行匹配多个 genotype
同一个 genotype 匹配多个 phenotype 行
只有 name match，没有 ID match
IRGC 一致但名称明显不同
名称一致但国家不同
Genesys 和 3K_list 的国家不同
```

字段：

```text
review_id
issue_type
genotype_sample_id
phenotype_sheet
phenotype_row_id
candidate_values
reason
recommended_action
notes
```

---

## 16. 报告要求

创建：

```text
reports/accession_mapping/accession_mapping_summary.md
```

主体中文，必须包含：

1. 本次任务目标。
2. 使用了哪些输入文件。
3. genotype 样本覆盖情况。
4. 3K_list_sra_ids 匹配情况。
5. RunInfo 匹配情况。
6. Genesys MCPD 匹配情况。
7. phenotype 匹配情况。
8. A / B / C / D 置信度统计。
9. 可用于 trait mapping 的样本数。
10. 不能用于 trait mapping 的原因。
11. 是否可以进入正式 trait_value_table 构建。
12. 下一步建议。

结论必须谨慎：

```text
只有 A/B 级 phenotype mapping 可以进入正式 trait_value_table。
C 级 name match 只能人工复核，不能直接训练。
如果 A/B 映射样本不足，则先不构建 trait-conditioned instances。
```

---

## 17. 运行命令

执行：

```bash
python scripts/mapping/build_accession_mapping_master.py
```

然后执行：

```bash
find reports/accession_mapping -maxdepth 1 -type f | sort
find data/interim/accession_mapping -maxdepth 1 -type f | sort
python -m py_compile scripts/mapping/*.py
git status --short --ignored
```

---

## 18. Git 提交要求

注意：

```text
data/raw/ 不能提交。
data/interim/ 不能提交。
```

确认 `git status --short --ignored` 中 data 仍然是 ignored。

提交：

```bash
git add reports/accession_mapping scripts/mapping README.md docs .gitignore
git commit -m "build accession ID mapping master draft"
git push
```

如果 README.md 或 docs 没有改动，可以不提交它们。

---

## 19. 最终回复要求

完成后用中文报告：

```text
1. 当前工作目录
2. genotype 样本数统计
3. 3K_list_sra_ids 匹配覆盖率
4. RunInfo 匹配覆盖率
5. Genesys MCPD 匹配覆盖率
6. phenotype 匹配覆盖率
7. A/B/C/D 置信度统计
8. usable_for_trait_mapping 样本数
9. 是否可以开始构建正式 trait_value_table
10. 主要风险
11. 生成的报告文件
12. Git commit / push 状态
13. raw/interim data 是否未进入 git
14. 下一步
```

下一步应该是：

```text
如果 A/B 级 phenotype mapping 足够，则构建 trait_state 和最小 Task 1 instances；
如果不足，则先人工审查 manual_review_candidates.tsv，并补充 accession ID mapping。
```

现在开始构建 accession_mapping_master.tsv 草稿。
