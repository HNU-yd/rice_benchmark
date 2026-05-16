# 现在最该做的不是继续下载，而是登记 + 审查 weak evidence

你现在需要让 Codex 做一个小任务：

```text
03c_register_and_inspect_weak_evidence.md
```

目标：

1. 给 `OryzabaseGeneListEn.tsv` 和 `qtaro_sjis.zip` 计算 checksum。
2. 更新 `download_manifest.tsv` 和 `checksum_table.tsv`。
3. 解压 Q-TARO，转 UTF-8。
4. 检查 Q-TARO 字段：trait、Chr、Genome start、Genome end、QTL name、reference。
5. 检查 Oryzabase 字段：gene symbol、RAP ID、MSU ID、chromosome、trait class、Trait Ontology。
6. 生成 weak evidence inventory。
7. 不做正式 `weak_evidence_table`，只做 raw inventory。

---

## Codex prompt：03c_register_and_inspect_weak_evidence.md

保存为：

```bash
/home/data2/projects/rice_benchmark/.codex/prompts/03c_register_and_inspect_weak_evidence.md
```

内容如下：

````markdown
# 03c_register_and_inspect_weak_evidence.md

你现在执行 Phase 3C：weak evidence raw file registration and inventory。

当前已经手动下载了两个 weak evidence raw files：

1. `data/raw/evidence/known_genes/oryzabase/OryzabaseGeneListEn.tsv`
2. `data/raw/evidence/qtl/qtaro/qtaro_sjis.zip`

GWAS lead SNP 文件当前没有下载成功。不要继续卡 GWAS 下载。GWAS lead SNP 后续通过 3K phenotype + genotype + Qmatrix 自己计算，作为 v0.2-core 的 Tier 2 weak evidence。

本任务只做 weak evidence raw inventory，不构建正式 `weak_evidence_table`，不做 model，不做 benchmark schema。

---

## 1. 项目边界

第一版 benchmark 仍然限定为：

- 3K Rice
- SNP + indel
- Task 1: trait-conditioned SNP/indel localization
- 不做 phenotype prediction
- 不做 trait classification
- weak evidence != causal ground truth
- unknown != negative

本任务中的 Oryzabase 和 Q-TARO 只能作为 weak localization evidence。

---

## 2. 本任务允许做什么

允许读取：

```text
data/raw/evidence/known_genes/oryzabase/OryzabaseGeneListEn.tsv
data/raw/evidence/qtl/qtaro/qtaro_sjis.zip
manifest/download_manifest.tsv
manifest/checksum_table.tsv
````

允许创建：

```text
reports/weak_evidence_inventory/
data/interim/evidence/qtaro/
data/interim/evidence/oryzabase/
```

允许创建脚本：

```text
scripts/inspect/inspect_weak_evidence.py
scripts/inspect/register_weak_evidence_raw.py
```

---

## 3. 本任务禁止做什么

禁止：

```text
不要继续下载 GWAS lead SNP
不要继续下载新的 raw data
不要把 weak evidence 写成 causal ground truth
不要把 unknown variants 当 negative
不要构建正式 weak_evidence_table
不要构建 benchmark schema
不要构建 split
不要构建 evaluator
不要写 model
不要写 Evo2 代码
不要做 phenotype prediction
不要把 data/raw 或 data/interim 提交到 git
```

---

## 4. checksum 和 manifest 登记

对以下文件计算 sha256：

```text
data/raw/evidence/known_genes/oryzabase/OryzabaseGeneListEn.tsv
data/raw/evidence/qtl/qtaro/qtaro_sjis.zip
```

更新：

```text
manifest/download_manifest.tsv
manifest/checksum_table.tsv
```

要求：

```text
data_category = weak_evidence
file_role = known_trait_gene_list / qtl_interval_archive
download_status = downloaded
source_id = SRC_WEAK_ORYZABASE_GENE_001 / SRC_WEAK_QTARO_QTL_001
checksum_sha256 = 实际 sha256
file_size_bytes = 实际文件大小
```

不要写虚假 checksum。

---

## 5. Q-TARO inventory

解压：

```bash
mkdir -p data/interim/evidence/qtaro
unzip -o data/raw/evidence/qtl/qtaro/qtaro_sjis.zip -d data/interim/evidence/qtaro
```

尝试转码：

```bash
for f in data/interim/evidence/qtaro/*; do
  if [[ -f "$f" ]]; then
    iconv -f SHIFT_JIS -t UTF-8 "$f" > "${f}.utf8" || true
  fi
done
```

检查字段和行数。

输出：

```text
reports/weak_evidence_inventory/qtaro_inventory.tsv
reports/weak_evidence_inventory/qtaro_columns.tsv
reports/weak_evidence_inventory/qtaro_trait_summary.tsv
```

重点识别字段：

```text
QTL name
Trait
Category
Chr
Genome start
Genome end
Marker
LOD
Reference
```

如果字段名不同，请记录实际字段名，不要强行改。

Evidence tier 记录为：

```text
Tier 4: QTL interval
```

---

## 6. Oryzabase inventory

读取：

```text
data/raw/evidence/known_genes/oryzabase/OryzabaseGeneListEn.tsv
```

自动判断分隔符：TSV / CSV / HTML fallback。

输出：

```text
reports/weak_evidence_inventory/oryzabase_inventory.tsv
reports/weak_evidence_inventory/oryzabase_columns.tsv
reports/weak_evidence_inventory/oryzabase_trait_gene_summary.tsv
```

重点识别字段：

```text
Gene Symbol
Gene Name
Trait
Trait Class
Trait ID
RAP ID
MSU ID
Chromosome
Trait Ontology
Plant Ontology
GO
```

如果 direct curl 下载的是 HTML 而不是 TSV，必须在报告中标记：

```text
downloaded file appears to be HTML, manual browser download required
```

Evidence tier 记录为：

```text
Tier 1: known / cloned trait gene
```

---

## 7. GWAS lead SNP 状态记录

创建：

```text
reports/weak_evidence_inventory/gwas_lead_snp_status.md
```

内容写明：

```text
当前未下载到可靠的 GWAS lead SNP raw file。
本地 data/raw 搜索结果只发现 phenotype、snpEff GeneID、Oryzabase、Q-TARO 等文件。
GWAS lead SNP 不阻塞 v0.1-mini。
v0.2-core 建议通过 3K phenotype + core SNP genotype + Qmatrix 自己计算 GWAS lead SNP。
self-computed GWAS 仍然只能作为 weak localization evidence，不能作为 causal ground truth。
```

---

## 8. 总报告

创建：

```text
reports/weak_evidence_inventory/weak_evidence_inventory_report.md
```

主体中文，包含：

```text
1. 本次任务目标
2. 已检查 weak evidence 文件
3. Q-TARO 检查结果
4. Oryzabase 检查结果
5. GWAS lead SNP 状态
6. 每类 evidence tier
7. 是否可以支撑 v0.1-mini
8. 主要风险
9. 下一步建议
```

明确写：

```text
v0.1-mini 可以使用 Tier 1 Oryzabase known genes + Tier 4 Q-TARO QTL intervals。
GWAS lead SNP 后续自跑，不作为当前阻塞项。
```

---

## 9. 运行命令

执行：

```bash
python scripts/inspect/register_weak_evidence_raw.py
python scripts/inspect/inspect_weak_evidence.py
python scripts/utils/validate_download_manifest.py manifest/download_manifest.tsv
python -m py_compile scripts/inspect/register_weak_evidence_raw.py scripts/inspect/inspect_weak_evidence.py
git status --short --ignored
```

---

## 10. Git 提交

raw/interim data 不进入 git。

确认：

```bash
git status --short --ignored
```

如果只显示 `!! data/`，可以提交报告和脚本：

```bash
git add manifest reports/weak_evidence_inventory scripts/inspect README.md docs
git commit -m "register and inspect rice weak evidence sources"
git push
```

不要提交 `data/raw/` 或 `data/interim/`。

---

## 11. 最终回复

完成后用中文报告：

```text
1. 当前工作目录
2. Q-TARO 是否可读
3. Oryzabase 是否可读
4. GWAS lead SNP 状态
5. checksum / manifest 更新状态
6. evidence tier 总结
7. 是否足够支撑 v0.1-mini
8. Git commit / push 状态
9. raw/interim data 是否未进入 git
10. Next step
```

Next step:

```text
创建 Phase 4 prompt：确定 v0.1-mini 数据范围，并开始构建最小可运行 benchmark 输入表。
```

现在开始执行 Phase 3C weak evidence raw inventory。

````

---

# GWAS lead SNP 后面怎么做

GWAS 不再靠下载，直接自己算。等 Phase 4/5 做完 accession mapping 后，增加一个任务：

```text
05_self_gwas_weak_evidence.md
````

核心输入：

```text
core_v0.7.{bed,bim,fam}.gz
3kRG_PhenotypeData_v20170411.xlsx
Qmatrix-k9-3kRG.csv
accession_mapping_table
```

基本方法：

```bash
plink \
  --bfile core_v0.7 \
  --pheno trait.pheno \
  --covar Qmatrix-k9-3kRG.csv \
  --linear hide-covar \
  --out gwas/<trait_id>
```

然后每个 trait 取：

```text
lead SNP
significant SNP
LD/window interval
```

进入：

```text
evidence_tier = Tier 2
evidence_type = self_computed_GWAS_lead_SNP
```

但这个必须等 **trait accession mapping** 修好。你现在 inventory 结果显示 phenotype accession-like values 和 B001-style genotype IDs 直接 overlap 为 0，所以马上跑 GWAS 没意义。先解决 accession mapping。
