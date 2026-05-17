你现在在 /home/data2/projects/rice_benchmark 仓库中工作。

当前项目是三千水稻无位点标签训练的性状条件 SNP/indel 定位评测体系。请严格遵守 /home/data2/projects/design v0.5.5 设计边界：

1. 当前可运行数据面仍是 chr1 SNP-only prototype。
2. 不训练模型。
3. 不冻结 split。
4. 不构建正式 evaluator。
5. 不报告正式 AUROC / AUPRC。
6. 不把 GWAS、QTL、Oryzabase、Q-TARO、funRiceGenes 或任何外部知识库当作 causal ground truth。
7. 不把 weak evidence 当训练 label。
8. 不把 unknown / unlabeled variant 或 window 当 true negative。
9. accession_id 只能作为索引，不能作为模型输入。
10. 本轮任务只构建 matched decoy 构建前置层，即 evidence object、candidate pool、matched pair 和 diagnostics。

当前 external knowledge v0.5.5 层已经完成，commit 为：

b68d08d Add v0.5.5 external knowledge integration layer

请先阅读以下文件：

- reports/current_data_status/current_data_structure_report.md
- reports/external_knowledge_v055/external_knowledge_integration_report.md
- data/interim/external_knowledge_v055/annotation/gene_annotation_table.tsv
- data/interim/external_knowledge_v055/mapping/gene_id_mapping_table.tsv
- data/interim/external_knowledge_v055/evidence/known_gene_evidence_table.tsv
- data/interim/external_knowledge_v055/evidence/trait_gene_evidence_table.tsv
- data/interim/external_knowledge_v055/evidence/qtl_interval_evidence_table.tsv
- data/interim/external_knowledge_v055/evidence/evidence_coordinate_mapping_table.tsv
- data/interim/external_knowledge_v055/evidence/evidence_source_manifest.tsv
- data/interim/external_knowledge_v055/qc_diagnostics/external_knowledge_validation.tsv
- data/interim/v0_1_mini/window_table_chr1_v0_1.tsv
- data/interim/v0_1_mini/variant_table_chr1_snp_v0_1.tsv
- data/interim/v0_1_mini/variant_window_mapping_chr1_v0_1.tsv
- data/interim/task1_chr1_snp/window_weak_signal_chr1_snp.tsv
- data/interim/task1_chr1_snp/variant_weak_label_chr1_snp.tsv
- data/interim/design_v055/decoy/matching_field_availability_table.tsv

本轮任务名称：

08B_build_matched_decoy_v055

目标：

基于当前 external knowledge v0.5.5 层和 chr1 SNP prototype，构建 matched decoy candidate pool、matched decoy pair 和 matching diagnostics。当前只做 chr1 SNP prototype 的匹配背景构建前置层，不做正式 full benchmark。

请生成目录：

data/interim/matched_decoy_v055/
data/interim/matched_decoy_v055/objects/
data/interim/matched_decoy_v055/candidate_pool/
data/interim/matched_decoy_v055/pairs/
data/interim/matched_decoy_v055/diagnostics/

reports/matched_decoy_v055/

scripts/matched_decoy/

需要输出以下表。

一、matched_decoy_object_table.tsv

用途：
统一进入匹配背景流程的 evidence object。对象可以是 gene-level evidence、region-level evidence、QTL interval evidence、variant-level evidence 或 window-level evidence。

字段至少包括：

object_id
object_type
trait_id
trait_name
evidence_id
evidence_source
evidence_source_type
evidence_level
support_level
allowed_usage
chrom
start
end
object_length
gene_id
gene_symbol
variant_id
window_id
source_database
source_record_id
mapping_status
coordinate_confidence
exact_frozen_trait_mapping
manual_review_required
in_main_evaluation_candidate_pool
exclusion_reason
notes

object_type 取值建议包括：

gene
interval
variant
window
qtl_interval
haplotype_region
manual_review_only

要求：

- 只允许 exact frozen trait mapping 的对象进入 main evaluation candidate pool。
- ambiguous frozen-trait keyword matches 进入 manual_review_required，不进入主评价。
- broader evidence 不进入主评价，只保留 broader_evidence_pool 标记。
- PEX_REPRO 当前 exact evidence 为 0，不允许强行补标签。
- Q-TARO 主要保留为 qtl_interval / region-level evidence，不强行 gene ID 映射。
- 所有 evidence 只能用于 evaluation / explanation / case study，不允许 training_label。

二、matched_decoy_candidate_pool.tsv

用途：
为每个 evidence object 生成匹配背景候选池。

字段至少包括：

candidate_pool_id
object_id
trait_id
object_type
candidate_object_id
candidate_object_type
candidate_chrom
candidate_start
candidate_end
candidate_length
same_chrom
position_bin
position_distance
gene_density_object
gene_density_candidate
variant_density_object
variant_density_candidate
annotation_richness_object
annotation_richness_candidate
evidence_source_coverage_object
evidence_source_coverage_candidate
database_detectability_object
database_detectability_candidate
interval_length_object
interval_length_candidate
chr1_snp_window_coverage_object
chr1_snp_window_coverage_candidate
chr1_snp_variant_coverage_object
chr1_snp_variant_coverage_candidate
candidate_pool_status
candidate_exclusion_reason
notes

要求：

- 当前仅基于 chr1 SNP prototype 构建候选池。
- 候选对象不能与 evidence object 是同一个对象。
- 候选池不代表真阴性，只是 matched background candidate pool。
- 候选池生成必须记录哪些字段可用、哪些不可用。
- 对 QTL interval，必须匹配 interval length 或 length bin。
- 对 gene-level evidence，必须匹配 gene length、local gene density、annotation richness 和 known-gene proximity proxy。
- 对 window/variant evidence，必须匹配 position bin、variant density、gene density、MAF/missingness/LD proxy，如果这些字段可用。

三、matched_decoy_pair_table.tsv

用途：
从候选池中选择最终匹配背景对。

字段至少包括：

decoy_pair_id
object_id
trait_id
object_type
decoy_object_id
decoy_object_type
match_rank
match_score
matching_level
matching_status
relaxation_level
relaxation_reason
n_candidates_before_filter
n_candidates_after_filter
matched_fields
unavailable_fields
field_balance_score
position_balance_score
density_balance_score
annotation_balance_score
detectability_balance_score
research_bias_balance_score
notes

matching_level 建议包括：

L1_strict_matched
L2_relaxed_position_density
L3_relaxed_annotation_detectability
L4_available_background_only
failed_no_candidate

要求：

- 每个 evidence object 尽量选择多个 decoy。
- 若严格匹配候选不足，按预先规则放宽，并记录 relaxation_level 和 relaxation_reason。
- 不能把 decoy 写成 negative label。
- 如果没有合格 decoy，要记录 failed_no_candidate，并进入 diagnostics。
- matched pair 不用于训练，只用于评价和背景控制。

四、decoy_matching_diagnostics.tsv

用途：
记录匹配背景构建质量。

字段至少包括：

diagnostic_id
object_type
trait_id
n_evidence_objects
n_main_evaluation_objects
n_objects_with_candidate_pool
n_objects_with_matched_decoy
n_objects_without_decoy
median_candidates_per_object
mean_candidates_per_object
median_decoys_per_object
mean_match_score
median_match_score
n_strict_matches
n_relaxed_matches
n_failed_matches
top_failure_reasons
field_balance_summary
position_balance_summary
gene_density_balance_summary
variant_density_balance_summary
annotation_richness_balance_summary
detectability_balance_summary
research_bias_balance_summary
notes

要求：

- 按 object_type 和 trait_id 分层输出。
- 必须报告 PEX_REPRO exact evidence 为 0 的情况。
- 必须报告 Q-TARO interval 是否只能进入 region-level evidence。
- 必须报告 manual review 和 broader evidence 的数量。
- 必须说明当前是 chr1 SNP-only prototype，不代表 full benchmark。

五、matching_field_availability_v055.tsv

用途：
记录每个匹配字段是否可用，避免把不可用字段误写成已经控制。

字段至少包括：

field_name
field_category
availability
proxy_field
used_in_object_table
used_in_candidate_pool
used_in_pair_matching
used_in_diagnostics
used_in_sensitivity
missing_reason
notes

field_category 建议包括：

coordinate
position
gene_density
variant_density
annotation_richness
evidence_source_coverage
database_detectability
interval_length
MAF
LD
missingness
mappability
research_bias
chr1_snp_coverage

要求：

- 对 mappability、recombination_rate、true literature count 等如果没有可靠数据，必须标记 unavailable 或 proxy_used。
- 不可用字段不能在报告中声称已经控制。
- 可以使用 external knowledge hit count、annotation record count、known-gene proximity 作为 research bias proxy，但必须写清楚只是 proxy。

六、detectability_bias_table_v055.tsv

用途：
记录对象级可检测性 proxy。

字段至少包括：

object_id
object_type
chrom
start
end
missingness_rate
callability_proxy
chr1_snp_coverage
window_coverage
variant_coverage
mappability_proxy
low_complexity_or_repeat_proxy
database_detectability_proxy
detectability_score
detectability_fields_available
notes

要求：

- 如果没有真实 mappability，只能标记 unavailable 或 proxy。
- detectability_score 必须说明计算方式。
- 不能声称完成完整 detectability correction。

七、research_bias_table_v055.tsv

用途：
记录对象级研究偏倚和注释丰富度 proxy。

字段至少包括：

object_id
object_type
gene_id
gene_symbol
chrom
start
end
annotation_record_count
external_knowledge_hit_count
known_gene_proximity
database_source_count
trait_evidence_count
annotation_richness_score
literature_bias_proxy
research_bias_score
research_bias_fields_available
notes

要求：

- 当前可以用 external knowledge hit count、annotation record count、known-gene proximity、database_source_count 作为 proxy。
- 不得声称这是完整 literature bias correction。
- 字段不可用必须记录。

八、decoy_validation.tsv

用途：
记录本轮构建的验证结果。

字段至少包括：

check_name
status
n_records
n_failed
details
blocking_issue
notes

至少检查：

- 所有输出表存在且非空，除非合理 skipped。
- matched_decoy_object_table 有 object_id 且无重复。
- 主评价候选池只包含 exact frozen trait mapping。
- PEX_REPRO 没有被强行补 evidence。
- Q-TARO 没有被强行 gene ID 映射为高置信 gene evidence。
- broader evidence 没有进入主评价对象。
- manual review 对象没有进入主评价对象。
- decoy candidate / pair 没有把 unknown/unlabeled 标成 true_negative。
- decoy pair 的 object_id 和 decoy_object_id 不相同。
- failed matching 对象进入 diagnostics。
- 所有匹配字段在 matching_field_availability_v055.tsv 中有记录。
- allowed_usage 中没有 training_label。
- 输出表主键或组合键无重复。

九、报告

生成：

reports/matched_decoy_v055/matched_decoy_report.md

报告必须说明：

1. 当前仍是 chr1 SNP-only prototype。
2. 本轮构建的是 matched decoy candidate pool 和 pair layer，不是正式 full benchmark。
3. matched decoy 是匹配背景，不是真阴性。
4. 本轮没有训练模型。
5. 本轮没有冻结 split。
6. 本轮没有构建正式 evaluator。
7. 本轮没有报告正式 AUROC / AUPRC。
8. 只使用 exact frozen trait mapping 进入主 evaluation candidate pool。
9. ambiguous frozen-trait keyword matches 和 broader evidence 如何处理。
10. PEX_REPRO exact evidence 为 0，不能强行补标签。
11. Q-TARO 当前只作为 region-level / interval-level evidence。
12. 各 object_type 有多少 evidence objects。
13. 每类 object 生成了多少 candidate pool 和 matched pair。
14. 每个 evidence object 平均有多少 candidate 和 decoy。
15. 使用了哪些匹配字段。
16. 哪些匹配字段不可用。
17. detectability 和 research bias 使用了哪些 proxy。
18. 哪些 evidence 无法构建 decoy，原因是什么。
19. 当前限制。
20. 是否可以进入下一步 split 冻结。

十、脚本要求

请把脚本放到：

scripts/matched_decoy/

建议脚本：

1. build_matched_decoy_objects_v055.py
2. build_matched_decoy_candidate_pool_v055.py
3. build_matched_decoy_pairs_v055.py
4. build_detectability_research_bias_v055.py
5. validate_matched_decoy_v055.py

脚本要求：

- 可重复运行。
- 有命令行参数。
- 不修改 raw data。
- 不硬编码绝对路径。
- 对缺失字段给出 skipped 或 unavailable，不要静默失败。
- 输出 validation summary。
- 所有输出表必须包含版本字段或能通过 manifest 追踪版本。

十一、完成后请总结

请在最终回复中总结：

1. 生成了哪些文件。
2. 每个文件多少行。
3. 主评价候选 object 数量。
4. broader evidence / manual review object 数量。
5. PEX_REPRO 是否仍为 0 exact evidence。
6. Q-TARO 如何处理。
7. 每类 object 的 candidate pool 覆盖率。
8. 每类 object 的 matched pair 覆盖率。
9. 每个 evidence object 平均 candidate 和 decoy 数量。
10. 哪些字段用于匹配。
11. 哪些字段不可用。
12. detectability / research bias 使用了哪些 proxy。
13. 是否有任何 allowed_usage 被错误写成 training_label。
14. 是否有任何 decoy 被错误写成 true_negative。
15. 当前限制。
16. 是否可以进入 split 冻结。

注意：

- 不训练模型。
- 不冻结 split。
- 不构建正式 evaluator。
- 不扩展 whole-genome SNP+indel。
- 不引入 SV/PAV/pan-reference。
- 不报告正式 AUROC/AUPRC。
- 不把 evidence 当 causal ground truth。
- 不把 decoy 当 true negative。