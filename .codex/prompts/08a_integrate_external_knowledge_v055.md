# 08A integrate external knowledge v0.5.5

你现在在 /home/data2/projects/rice_benchmark 仓库中工作。
将此prompt保存到 /home/data2/projects/rice_benchmark/.codex/prompts下。

当前项目是 3K Rice trait-conditioned SNP/indel localization benchmark。请严格遵守 v0.5.5 设计边界：

1. 当前可运行数据面仍是 v0.1 chr1 SNP-only prototype。
2. 不训练模型。
3. 不报告正式 AUROC/AUPRC。
4. 不把 GWAS、QTL、Oryzabase、Q-TARO、known genes、funRiceGenes 或任何外部知识库当作 causal ground truth。
5. 不把 weak evidence 当训练 label。
6. 不把 unknown/unlabeled variant/window 当 true negative。
7. accession_id 只能作为索引，不能作为模型输入。
8. 本轮目标是整合外部知识库，形成统一 annotation / evidence / gene ID mapping 层，为后续 matched decoy、candidate gene explanation 和 evaluator 做前置准备。

请先阅读以下文件和报告：

- reports/current_data_status/current_data_structure_report.md
- reports/current_data_status/v055_data_processing_report.md
- reports/external_knowledge/external_knowledge_07a_report.md
- reports/external_knowledge/external_knowledge_integration_plan.tsv
- reports/v0_1_mini/weak_evidence_mapping_summary.md
- reports/current_data_status/current_raw_file_summary.tsv
- reports/current_data_status/current_data_category_summary.tsv
- manifest/source_inventory.tsv
- manifest/download_manifest.tsv
- manifest/checksum_table.tsv

同时检查 data/raw/ 中已经下载的以下资源：

- RAP-DB
- funRiceGenes
- MSU / RGAP
- Oryzabase
- Q-TARO
- reference annotation files
- any existing external knowledge tables

本轮任务：构建统一 external knowledge / annotation / weak evidence 层。

请生成目录：

data/interim/external_knowledge_v055/
data/interim/external_knowledge_v055/annotation/
data/interim/external_knowledge_v055/evidence/
data/interim/external_knowledge_v055/mapping/
data/interim/external_knowledge_v055/qc_diagnostics/

reports/external_knowledge_v055/

scripts/external_knowledge/

需要输出以下核心表：

1. gene_annotation_table.tsv

用途：
统一 rice gene annotation，服务于 nearest gene、gene density、candidate gene explanation、gene-level matched decoy。

字段至少包括：
gene_id
gene_source
chrom
start
end
strand
gene_symbol
gene_name
gene_type
description
source_database
source_version
reference_build
coordinate_confidence
notes

要求：
- 坐标必须统一到当前 benchmark 使用的 reference build。
- 如果多个 annotation source 对同一 gene 有不同坐标或 ID，必须记录来源和映射状态。
- 不能把 gene annotation 当训练 label。

2. gene_id_mapping_table.tsv

用途：
统一 RAP-DB、MSU/RGAP、Oryzabase、funRiceGenes、Q-TARO 中的 gene ID / gene symbol。

字段至少包括：
mapping_id
source_gene_id
source_database
target_gene_id
target_database
gene_symbol
mapping_type
mapping_confidence
mapping_method
is_ambiguous
n_candidates
notes

mapping_type 例如：
exact_id_match
symbol_match
coordinate_overlap
alias_match
manual_review_required
unmapped

要求：
- 不要强行一对一映射 ambiguous gene。
- ambiguous mapping 必须保留并标记。
- manual_review_required 的记录要单独输出 review table。

3. known_gene_evidence_table.tsv

用途：
整理已知 / 已克隆 / 功能支持基因证据，用于 evaluation / explanation，不用于训练。

字段至少包括：
evidence_id
trait_id_or_name
gene_id
gene_symbol
evidence_source
source_database
source_record_id
evidence_type
support_level
species
chrom
start
end
reference_build
coordinate_mapping_status
allowed_usage
evidence_split_candidate
notes

evidence_type 例如：
cloned_gene
known_trait_gene
functional_gene
natural_allele_gene
candidate_gene_from_literature
database_trait_gene

support_level 例如：
high_confidence
medium_confidence
weak
annotation_only

allowed_usage 只能是：
evaluation_reference
explanation
case_study
development_evidence_candidate
不能是 training_label。

4. trait_gene_evidence_table.tsv

用途：
建立 trait 与 gene 的对应关系，允许一个 trait 对多个 gene，一个 gene 对多个 trait。

字段至少包括：
trait_gene_evidence_id
trait_id
trait_name
trait_name_normalized
gene_id
gene_symbol
evidence_id
evidence_source
support_level
trait_mapping_confidence
gene_mapping_confidence
allowed_usage
notes

要求：
- trait name mapping 必须保留原始名称和 normalized 名称。
- 无法可靠映射到 frozen 9 traits 的证据不能强行进入主评价；可进入 broader evidence pool 或 manual review。

5. qtl_interval_evidence_table.tsv

用途：
整合 Q-TARO / QTL interval / region-level evidence。

字段至少包括：
qtl_evidence_id
trait_id_or_name
trait_name_normalized
chrom
start
end
interval_length
source_database
source_record_id
evidence_type
coordinate_mapping_status
reference_build
linked_gene_id
linked_gene_symbol
allowed_usage
notes

要求：
- QTL / interval 只能作为 region-level weak localization evidence。
- 不得写成 causal label。
- 如果 interval 太宽，应标记 broad_interval，并在评价中降级为 region-level overlap。

6. evidence_coordinate_mapping_table.tsv

用途：
记录所有 evidence 坐标映射情况。

字段至少包括：
evidence_id
original_source
original_reference_build
original_chrom
original_start
original_end
mapped_reference_build
mapped_chrom
mapped_start
mapped_end
mapping_method
mapping_confidence
mapping_status
failure_reason
notes

mapping_status 例如：
mapped_high_confidence
mapped_low_confidence
gene_level_only
region_level_only
unmapped
manual_review_required

7. evidence_source_manifest.tsv

用途：
记录每个外部知识库来源、版本、文件路径、checksum 和用途。

字段至少包括：
source_name
source_version
raw_file_path
processed_table
checksum
download_or_access_date
source_type
allowed_usage
license_or_terms_note
processing_script
notes

source_type 例如：
gene_annotation
known_gene_database
qtl_database
external_trait_gene_knowledge
id_mapping_resource

8. external_knowledge_manual_review_table.tsv

用途：
记录需要人工审查的 ambiguous / unmapped / conflicting mapping。

字段至少包括：
review_id
record_type
source_database
source_record_id
raw_trait_name
raw_gene_id
raw_gene_symbol
candidate_mappings
ambiguity_reason
recommended_action
priority
notes

9. external_knowledge_validation.tsv

用途：
记录本轮处理的质量检查。

字段至少包括：
check_name
status
n_records
n_failed
details
blocking_issue
notes

至少检查：
- gene_annotation_table 坐标是否有效
- gene_id_mapping_table 是否有 mapping confidence
- known_gene_evidence_table 是否没有 training_label usage
- qtl_interval_evidence_table 是否没有 causal label usage
- evidence source manifest 是否有 source 和 checksum
- ambiguous mapping 是否进入 manual review
- evidence 坐标是否统一到 reference build 或被降级
- 输出表是否有主键且无重复主键

10. reports/external_knowledge_v055/external_knowledge_integration_report.md

报告必须说明：

- 使用了哪些 raw sources。
- 生成了哪些表，每个表多少行。
- 各来源 gene ID mapping 成功率。
- ambiguous / unmapped 记录数量。
- 哪些 evidence 可以映射到 frozen 9 traits，哪些只能进入 broader evidence pool。
- 哪些 evidence 是 gene-level，哪些是 interval-level，哪些是 variant-level。
- 所有 evidence 都只用于 evaluation / explanation / case study，不用于 model training。
- 当前仍有哪些限制，例如坐标版本不一致、trait name mapping 模糊、QTL interval 太宽、source license 不明、字段缺失等。
- 下一步如何基于这些表构建 matched decoy。

脚本要求：

请把脚本放到：

scripts/external_knowledge/

建议脚本包括：

1. build_gene_annotation_table.py
2. build_gene_id_mapping_table.py
3. build_known_gene_evidence_table.py
4. build_qtl_interval_evidence_table.py
5. build_evidence_coordinate_mapping_table.py
6. validate_external_knowledge_layer.py

脚本要求：
- 可重复运行。
- 有命令行参数。
- 不把绝对路径硬编码到脚本主体。
- 输出 validation summary。
- 对缺失源文件给出清晰错误或 skipped 状态。
- 不修改 raw data。

完成后请输出总结：

1. 生成了哪些文件。
2. 每个文件多少行。
3. 各 source 的 mapping 成功率。
4. 哪些 evidence 可进入 frozen 9 traits 的 evaluation candidate pool。
5. 哪些 evidence 只能作为 broader evidence 或 manual review。
6. 是否有任何 evidence 被错误标成 training label。
7. 当前仍有哪些缺口。
8. 是否可以进入下一步 matched decoy 构建。

注意：
- 不训练模型。
- 不构建 matched decoy。
- 不冻结 split。
- 不扩展 whole-genome SNP+indel。
- 不引入 SV/PAV/pan-reference。
- 不报告正式 AUROC/AUPRC。
- 提交到git@github.com:HNU-yd/rice_benchmark.git
