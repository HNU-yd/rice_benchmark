你现在在 /home/data2/projects/rice_benchmark 仓库中工作。

当前项目是三千水稻无位点标签训练的性状条件 SNP/indel 定位评测体系。请严格遵守 v0.5.5 设计边界：

1. 当前仍是 chr1 SNP-only prototype。
2. 不训练模型。
3. 不构建正式 evaluator。
4. 不报告 AUROC / AUPRC。
5. 不扩展 whole-genome SNP+indel。
6. 不引入 SV / PAV / 泛基因组。
7. 不把 evidence 当训练 label。
8. 不把 matched decoy 当 true negative。
9. 不把 unknown / unlabeled variant 或 window 当 true negative。
10. accession_id 只能作为索引，不能作为模型输入。
11. 本轮任务只做 chr1 SNP prototype 的 leakage-aware split 冻结。

本轮任务名称：

08C_freeze_chr1_snp_split_v055

目标：

基于 08B matched decoy 前置层和当前 chr1 SNP-only prototype，构建防泄漏的 split assignment。重点不是随机切分，而是避免 gene、interval、QTL、nearby evidence、matched decoy pair 和 trait evidence 在不同 split 之间泄漏。

请先确认 08B 已经 commit / push，并记录当前 commit hash。

请阅读以下文件：

- reports/current_data_status/current_data_structure_report.md
- reports/matched_decoy_v055/matched_decoy_report.md
- data/interim/matched_decoy_v055/objects/matched_decoy_object_table.tsv
- data/interim/matched_decoy_v055/candidate_pool/matched_decoy_candidate_pool.tsv
- data/interim/matched_decoy_v055/pairs/matched_decoy_pair_table.tsv
- data/interim/matched_decoy_v055/diagnostics/decoy_matching_diagnostics.tsv
- data/interim/matched_decoy_v055/diagnostics/decoy_validation.tsv
- data/interim/design_v055/metadata/trait_usability_table.tsv
- data/interim/design_v055/metadata/trait_preprocessing_table.tsv
- data/interim/design_v055/negative_pairs/negative_pair_protocol_table.tsv
- data/interim/design_v055/negative_pairs/balance_diagnostics_table.tsv
- data/interim/trait_state/high_confidence_accessions.tsv
- data/interim/trait_state/trait_state_table_prototype.tsv
- data/interim/v0_1_mini/window_table_chr1_v0_1.tsv
- data/interim/v0_1_mini/variant_table_chr1_snp_v0_1.tsv
- data/interim/v0_1_mini/variant_window_mapping_chr1_v0_1.tsv

请生成目录：

data/interim/frozen_split_v055/
data/interim/frozen_split_v055/units/
data/interim/frozen_split_v055/blocks/
data/interim/frozen_split_v055/assignments/
data/interim/frozen_split_v055/diagnostics/

reports/frozen_split_v055/

scripts/frozen_split/

需要输出以下表。

一、split_unit_table.tsv

用途：
定义所有参与 split 的基本对象，包括 accession、region block、trait、evidence object、decoy pair。

字段至少包括：

split_unit_id
split_unit_type
source_object_id
source_table
trait_id
object_type
chrom
start
end
gene_id
gene_symbol
variant_id
window_id
accession_id
decoy_pair_id
in_main_evaluation_candidate_pool
manual_review_required
broader_evidence
allowed_usage
notes

split_unit_type 建议包括：

accession
region
trait
evidence_object
decoy_pair

要求：

- manual review 和 broader evidence 可以登记，但不能进入主评价 split。
- matched decoy pair 必须绑定其 evidence object。
- decoy 仍然是 matched background，不是真阴性。
- accession_id 只用于 split 和索引，不进入模型。

二、split_block_table.tsv

用途：
构建防泄漏 block，防止同一 gene、相邻 gene、重叠 interval、nearby QTL 或同一 matched decoy set 跨 split 泄漏。

字段至少包括：

split_block_id
block_type
chrom
block_start
block_end
block_length
member_unit_ids
n_units
traits
genes
evidence_sources
decoy_pair_ids
block_rule
leakage_risk_level
notes

block_type 建议包括：

gene_block
gene_neighborhood_block
interval_overlap_block
qtl_region_block
window_neighborhood_block
variant_neighborhood_block
decoy_set_block
mixed_evidence_block
accession_block
trait_block

要求：

- 同一 gene 的 evidence / decoy 不能跨 split。
- 相邻 gene 或 nearby evidence 应进入同一个 block。
- overlapping interval / same QTL interval 不能跨 split。
- 同一 matched decoy set 应绑定同一个 block。
- block 构建距离阈值必须写入 manifest。
- 发现潜在泄漏时记录 leakage_risk_level。

三、frozen_split_assignment.tsv

用途：
给 split unit 和 split block 分配冻结 split。

字段至少包括：

assignment_id
split_version
random_seed
split_unit_id
split_block_id
split_unit_type
assigned_split
assigned_role
trait_id
object_type
chrom
start
end
assignment_rule
prototype_locked_not_final
notes

assigned_split 建议包括：

train
dev
test
prototype_locked
source_disjoint_or_temporal
excluded_manual_review
excluded_broader_evidence
excluded_no_exact_trait_mapping
diagnostic_only

assigned_role 建议包括：

training_candidate
development_evaluation
prototype_locked_evaluation
source_disjoint_evaluation
excluded
diagnostic

要求：

- 当前不能使用 final_locked 这个名称。
- 必须使用 prototype_locked，并明确 prototype_locked_not_final = true。
- manual review 不进入主评价 split。
- broader evidence 不进入主评价 split。
- PEX_REPRO 不能被强行补 evidence。
- decoy pair 的 split 必须跟随 evidence object。
- 同一 split_block 不得跨 development 和 prototype_locked。
- 所有随机过程必须固定 random_seed。

四、split_balance_diagnostics.tsv

用途：
评估 split 平衡性。

字段至少包括：

diagnostic_id
split_version
diagnostic_type
assigned_split
trait_id
object_type
n_units
n_blocks
n_accessions
n_evidence_objects
n_decoy_pairs
subgroup_distribution
PC_balance_summary
trait_distribution
evidence_source_distribution
object_type_distribution
position_distribution
gene_density_summary
variant_density_summary
notes

至少检查：

- accession split 的 subgroup 平衡。
- accession split 的 PC 分布。
- evidence split 的 trait 分布。
- evidence split 的 object_type 分布。
- evidence split 的 source 分布。
- region split 的 position 分布。
- decoy pair 是否随 evidence split 分配。

五、split_leakage_check.tsv

用途：
检查 split 泄漏。

字段至少包括：

check_id
check_name
status
n_checked
n_leakage
leakage_type
affected_units
affected_blocks
details
blocking_issue
notes

至少检查：

- 同一个 accession 不跨 train/dev/test。
- 同一个 gene block 不跨 development/prototype_locked。
- overlapping interval block 不跨 development/prototype_locked。
- same QTL / nearby QTL block 不跨 development/prototype_locked。
- same decoy set 不跨 split。
- manual review 不进入主评价 split。
- broader evidence 不进入主评价 split。
- PEX_REPRO 没有被强行补 evidence。
- prototype_locked 没有被写成 final_locked。
- evidence object 和对应 decoy pair split 一致。
- unknown / unlabeled 没有被写成 true negative。

六、split_validation.tsv

用途：
记录本轮 split 构建的验证结果。

字段至少包括：

check_name
status
n_records
n_failed
details
blocking_issue
notes

至少检查：

- 所有输出表存在且非空。
- 主键或组合键无重复。
- split_unit_table 含 accession / evidence_object / decoy_pair / region / trait 单元。
- split_block_table 含 gene / interval / decoy_set 等防泄漏 block。
- frozen_split_assignment 不含 final_locked。
- prototype_locked_not_final 标记存在。
- manual review 和 broader evidence 没有进入主评价 split。
- decoy pair 跟随 evidence object split。
- leakage_check 全部通过或明确标记 non-blocking warning。
- split_manifest 信息完整。

七、split_manifest.tsv

用途：
记录 split 版本、规则、随机种子、来源表和限制。

字段至少包括：

split_name
split_version
random_seed
source_tables
created_at
created_by_script
rule_summary
block_rule_summary
prototype_locked_not_final
limitations
notes

必须记录：

- accession split seed
- region/block split rule
- evidence split rule
- proximity block rule
- decoy pair split rule
- trait challenge rule
- 当前仍是 chr1 SNP-only prototype
- 不是 final full benchmark split

八、报告

生成：

reports/frozen_split_v055/frozen_split_report.md

报告必须说明：

1. 当前仍是 chr1 SNP-only prototype。
2. 本轮冻结的是 prototype split，不是 final full benchmark split。
3. prototype_locked 不是 final_locked。
4. 本轮没有训练模型。
5. 本轮没有构建 evaluator。
6. 本轮没有报告 AUROC/AUPRC。
7. split unit 有哪些类型，各多少。
8. split block 如何构建。
9. gene / interval / QTL / decoy set leakage 如何避免。
10. accession split 的 subgroup / PC balance。
11. evidence split 中 development / prototype_locked / source_disjoint_or_temporal 各有多少 object。
12. manual review 和 broader evidence 如何排除。
13. PEX_REPRO 如何处理。
14. decoy pair 如何跟随 evidence object split。
15. 是否存在 leakage warning。
16. 当前限制。
17. 是否可以进入 evaluator scaffold。

九、脚本要求

请把脚本放到：

scripts/frozen_split/

建议脚本：

1. build_split_units_v055.py
2. build_split_blocks_v055.py
3. assign_frozen_splits_v055.py
4. build_split_balance_diagnostics_v055.py
5. check_split_leakage_v055.py
6. validate_frozen_split_v055.py

脚本要求：

- 可重复运行。
- 有命令行参数。
- 不修改 raw data。
- 不硬编码绝对路径。
- 所有随机过程固定 random seed。
- 对缺失字段给出 skipped 或 unavailable，不要静默失败。
- 输出 validation summary。
- 所有输出表必须包含 split_version 或能通过 manifest 追踪版本。

十、完成后请总结：

1. 当前 commit hash。
2. 生成了哪些文件。
3. 每个文件多少行。
4. split unit 各类型数量。
5. split block 各类型数量。
6. accession split 各 split 有多少 accession。
7. subgroup / PC balance 是否通过。
8. evidence split 各 split 有多少 object。
9. prototype_locked 是否明确不是 final_locked。
10. manual review / broader evidence 是否被排除。
11. PEX_REPRO 是否没有被强行补 evidence。
12. decoy pair 是否全部跟随 evidence object split。
13. 是否存在 leakage warning。
14. 当前限制。
15. 是否可以进入 evaluator scaffold。

注意：

- 不训练模型。
- 不构建 evaluator。
- 不报告 AUROC/AUPRC。
- 不扩展 whole-genome SNP+indel。
- 不引入 SV/PAV/pan-reference。
- 不把 evidence 当训练 label。
- 不把 decoy 当 true negative。
