你现在在 /home/data2/projects/rice_benchmark 仓库中工作。

当前项目是三千水稻无位点标签训练的性状条件 SNP/indel 定位评测体系。请严格遵守 v0.5.5 设计边界：

1. 当前仍是 chr1 SNP-only prototype。
2. 不训练模型。
3. 不构建正式 evaluator。
4. 不报告正式 AUROC / AUPRC。
5. 不扩展 whole-genome SNP+indel。
6. 不引入 SV / PAV / 泛基因组。
7. 不把 evidence 当训练 label。
8. 不把 matched decoy 当 true negative。
9. 不把 unknown / unlabeled variant 或 window 当 true negative。
10. accession_id 只能作为索引，不能作为模型输入。
11. 本轮任务只构建 split-aware evaluator scaffold，即评价器脚手架、输入输出 schema、任务 manifest、dry-run 校验和泄漏防护。

本轮任务名称：

09A_build_split_aware_evaluator_scaffold_v055

目标：

基于 08B matched decoy 层和 08C frozen split 层，构建 chr1 SNP-only prototype 的 split-aware evaluator scaffold。该 scaffold 只定义评价输入、评价单元、输出格式、任务 manifest 和 dry-run validation，不计算正式 benchmark 指标。

请先确认 08C 已经 commit / push，并记录当前 commit hash。

请阅读以下文件：

- reports/current_data_status/current_data_structure_report.md
- reports/matched_decoy_v055/matched_decoy_report.md
- reports/frozen_split_v055/frozen_split_report.md

- data/interim/matched_decoy_v055/objects/matched_decoy_object_table.tsv
- data/interim/matched_decoy_v055/pairs/matched_decoy_pair_table.tsv
- data/interim/matched_decoy_v055/diagnostics/decoy_validation.tsv

- data/interim/frozen_split_v055/assignments/frozen_split_assignment.tsv
- data/interim/frozen_split_v055/diagnostics/split_leakage_check.tsv
- data/interim/frozen_split_v055/diagnostics/split_validation.tsv
- data/interim/frozen_split_v055/diagnostics/split_manifest.tsv

- data/interim/v0_1_mini/window_table_chr1_v0_1.tsv
- data/interim/v0_1_mini/variant_table_chr1_snp_v0_1.tsv
- data/interim/v0_1_mini/variant_window_mapping_chr1_v0_1.tsv

- data/interim/task1_chr1_snp/window_weak_signal_chr1_snp.tsv
- data/interim/task1_chr1_snp/variant_weak_label_chr1_snp.tsv

- data/interim/baselines_chr1_snp/window_baseline_scores.tsv
- data/interim/baselines_chr1_snp/variant_baseline_scores.tsv

请生成目录：

data/interim/evaluator_scaffold_v055/
data/interim/evaluator_scaffold_v055/inputs/
data/interim/evaluator_scaffold_v055/tasks/
data/interim/evaluator_scaffold_v055/outputs_schema/
data/interim/evaluator_scaffold_v055/dry_run/
data/interim/evaluator_scaffold_v055/diagnostics/

reports/evaluator_scaffold_v055/

scripts/evaluator_scaffold/

需要输出以下表。

一、evaluator_object_input_table.tsv

用途：
定义可进入评价器的 evidence object 及其 split、trait、object 类型和 matched decoy 信息。

字段至少包括：

evaluator_object_id
object_id
trait_id
object_type
evidence_id
evidence_source
evidence_level
chrom
start
end
gene_id
gene_symbol
variant_id
window_id
assigned_split
assigned_role
prototype_locked_not_final
in_main_evaluation_candidate_pool
manual_review_required
broader_evidence
has_matched_decoy
n_matched_decoys
notes

要求：

- 只允许 development、prototype_locked、source_disjoint_or_temporal 的主评价对象进入 evaluator object input。
- manual review、broader evidence、excluded_no_exact_trait_mapping 不得进入主评价输入。
- prototype_locked 必须保留 prototype_locked_not_final=true。
- 不允许使用 final_locked 字段名。
- decoy 仍然是 matched background，不是真阴性。

二、evaluator_decoy_input_table.tsv

用途：
定义每个 evidence object 对应的 matched decoy 对象。

字段至少包括：

evaluator_decoy_id
evaluator_object_id
object_id
decoy_pair_id
decoy_object_id
trait_id
object_type
assigned_split
decoy_assignment_status
match_rank
match_score
matching_level
relaxation_level
matched_fields
unavailable_fields
notes

要求：

- decoy split 必须跟随 evidence object split。
- 不允许 decoy 独立随机分配 split。
- decoy 不得写成 negative label 或 true negative。
- 如果 object 没有 decoy，应进入 diagnostics，不进入正式 matched evaluation input。

三、evaluator_score_input_schema.tsv

用途：
定义后续模型或 baseline score 输入评价器时必须遵守的 schema。

字段至少包括：

field_name
required
dtype
description
allowed_values
example
notes

必须包含以下 score input 字段：

score_table_name
score_source
score_version
score_level
trait_id
variant_id
window_id
gene_id
object_id
score
score_direction
split_version
aggregation_recipe_version
model_version
notes

score_level 取值建议：

variant
window
gene
region
trait_level_variant
trait_level_window

score_source 取值建议：

baseline
model
diagnostic
random

要求：

- 明确 accession-level scores 不能直接用于 final evidence evaluation，必须先聚合为 trait-level map。
- baseline score 可以进入 dry-run，但不能生成正式主结果。

四、evaluator_task_manifest.tsv

用途：
定义评价任务清单，但不运行正式评价。

字段至少包括：

task_id
task_name
task_type
object_type
score_level
input_object_table
input_decoy_table
required_score_fields
assigned_split
allowed_splits
metric_family
is_formal_metric
is_dry_run_only
notes

task_type 建议包括：

matched_ranking
topk_recovery
rank_percentile
enrichment_over_matched_background
distance_to_evidence
overlap_with_region
diagnostic_only

要求：

- 当前全部标记为 is_dry_run_only=true 或 formal_metric=false。
- 不允许在本轮输出正式 benchmark 指标。
- AUROC/AUPRC 如果出现，只能作为 future_supported_metric，并注明 calculated_on=evidence_plus_matched_decoys，不能基于 genomewide unknown negatives。
- task manifest 必须区分 development、prototype_locked、source_disjoint_or_temporal。

五、evaluator_output_schema.tsv

用途：
定义未来 evaluator 输出格式。

字段至少包括：

field_name
required
dtype
description
allowed_values
example
notes

必须覆盖以下未来输出字段：

evaluation_run_id
task_id
score_source
score_version
object_id
trait_id
object_type
assigned_split
metric_name
metric_value
n_evidence_objects
n_decoys
calculated_on
uses_true_negative
uses_unknown_as_negative
prototype_locked_not_final
notes

要求：

- uses_true_negative 必须默认为 false。
- uses_unknown_as_negative 必须默认为 false。
- calculated_on 必须支持 evidence_plus_matched_decoys。
- 不得把 decoy 表述为 true negative。

六、baseline_score_dry_run_input.tsv

用途：
将当前已有 baseline prototype score 按 evaluator score schema 做 dry-run 对齐。

字段至少包括：

dry_run_score_id
score_source
score_version
score_level
trait_id
variant_id
window_id
object_id
score
score_direction
split_version
matched_to_evaluator_object
matched_to_decoy
notes

要求：

- 可以接入已有 random_uniform、window_snp_density、genomic_position、shuffled_trait baseline scores。
- 只做 schema 对齐和 join coverage 检查。
- 不计算正式指标。
- 若某 baseline score 无法映射到 evaluator object 或 decoy，必须记录原因。

七、evaluator_dry_run_join_check.tsv

用途：
检查 evaluator object、decoy、split 和 score 表能否正确 join。

字段至少包括：

check_id
check_name
status
n_input_records
n_matched_records
n_unmatched_records
match_rate
details
blocking_issue
notes

至少检查：

- evaluator object 能 join 到 split assignment。
- evaluator object 能 join 到 matched decoy pair。
- decoy pair 能跟随 evidence object split。
- baseline score 能 join 到 evaluator object 或 decoy。
- manual review / broader evidence 没有进入 evaluator object。
- prototype_locked 没有被写成 final_locked。
- unknown / unlabeled 没有被写成 negative。
- decoy 没有被写成 true_negative。

八、evaluator_leakage_guard.tsv

用途：
记录评价器泄漏防护检查。

字段至少包括：

guard_id
guard_name
status
n_checked
n_failed
details
blocking_issue
notes

至少检查：

- evidence used_for_training = false。
- allowed_usage 不包含 training_label。
- manual review 不进入主评价。
- broader evidence 不进入主评价。
- decoy uses_true_negative = false。
- unknown_as_negative = false。
- accession_id 不作为 score schema 必需字段。
- accession-level score 不直接进入 formal evidence evaluation。
- prototype_locked_not_final = true。
- final_locked 字段没有出现。
- development 与 prototype_locked 的 proximity leakage 状态来自 split_leakage_check，并必须通过或标记 warning。

九、evaluator_scaffold_validation.tsv

用途：
记录本轮 scaffold 验证结果。

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
- evaluator object input 只包含允许 split。
- decoy input 不含 true_negative。
- task manifest 不含 formal metric。
- output schema 中 uses_unknown_as_negative 默认 false。
- score schema 中 accession_id 不是必需字段。
- dry-run score input 不生成正式指标。
- validation 没有 blocking issue。

十、报告

生成：

reports/evaluator_scaffold_v055/evaluator_scaffold_report.md

报告必须说明：

1. 当前仍是 chr1 SNP-only prototype。
2. 本轮只是 split-aware evaluator scaffold，不是正式 evaluator。
3. 本轮没有训练模型。
4. 本轮没有报告 AUROC/AUPRC。
5. 本轮没有构建 final locked evaluation。
6. evaluator object input 包含多少 object。
7. decoy input 包含多少 matched decoy。
8. development / prototype_locked / source_disjoint_or_temporal 各有多少 object。
9. baseline dry-run score join 覆盖率如何。
10. 是否有 manual review / broader evidence 进入 evaluator input。
11. 是否有 decoy 被写成 true_negative。
12. 是否有 unknown/unlabeled 被写成 negative。
13. 是否有 accession_id 被要求作为 score 输入。
14. prototype_locked_not_final 是否保留。
15. 当前限制。
16. 是否可以进入 chr1 SNP dry-run evaluator 或 baseline matched-ranking dry-run。

十一、脚本要求

请把脚本放到：

scripts/evaluator_scaffold/

建议脚本：

1. build_evaluator_object_input_v055.py
2. build_evaluator_decoy_input_v055.py
3. build_evaluator_score_schema_v055.py
4. build_evaluator_task_manifest_v055.py
5. build_baseline_score_dry_run_input_v055.py
6. run_evaluator_scaffold_validation_v055.py

脚本要求：

- 可重复运行。
- 有命令行参数。
- 不修改 raw data。
- 不硬编码绝对路径。
- 不计算正式指标。
- 对缺失字段给出 skipped 或 unavailable，不要静默失败。
- 输出 validation summary。
- 所有输出表必须包含 scaffold_version 或能通过 manifest 追踪版本。

十二、完成后请总结：

1. 当前 commit hash。
2. 生成了哪些文件。
3. 每个文件多少行。
4. evaluator object input 有多少 object。
5. decoy input 有多少 decoy。
6. 各 split 有多少 object。
7. dry-run baseline score join 覆盖率。
8. 是否有 manual review / broader evidence 错误进入 evaluator input。
9. 是否有 decoy 被写成 true_negative。
10. 是否有 unknown/unlabeled 被写成 negative。
11. 是否有 accession_id 被要求作为 score 输入。
12. 是否没有输出正式指标。
13. 当前限制。
14. 是否可以进入下一步 chr1 SNP matched-ranking dry-run。

注意：
- 执行完prompt需要push
- 不训练模型。
- 不构建正式 evaluator。
- 不报告 AUROC/AUPRC。
- 不扩展 whole-genome SNP+indel。
- 不引入 SV/PAV/pan-reference。
- 不把 evidence 当训练 label。
- 不把 decoy 当 true negative。
- 不把 unknown/unlabeled 当 negative。