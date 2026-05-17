# Matched-Ranking Dry-Run v0.5.5 Report

## Scope

This run is a matched-ranking dry-run and evaluator adapter smoke test for the chr1 SNP-only prototype. It is not a formal evaluator and does not create final locked evaluation outputs.

No model was trained. No formal AUROC/AUPRC was reported. Evidence is not a training label, matched decoys are matched background only, and unknown/unlabeled rows are not negatives.

## Generated Tables

| table | rows |
|---|---:|
| `data/interim/evaluator_dry_run_v055/adapter/object_score_adapter_table.tsv` | 4 |
| `data/interim/evaluator_dry_run_v055/matched_sets/dry_run_matched_set_score_table.tsv` | 679620 |
| `data/interim/evaluator_dry_run_v055/ranks/dry_run_rank_position_table.tsv` | 135924 |
| `data/interim/evaluator_dry_run_v055/coverage/dry_run_score_coverage_table.tsv` | 188 |
| `data/interim/evaluator_dry_run_v055/diagnostics/dry_run_missing_score_diagnostics.tsv` | 1 |
| `data/interim/evaluator_dry_run_v055/diagnostics/dry_run_evaluator_adapter_contract.tsv` | 7 |
| `data/interim/evaluator_dry_run_v055/diagnostics/dry_run_leakage_guard.tsv` | 10 |
| `data/interim/evaluator_dry_run_v055/diagnostics/dry_run_validation.tsv` | 11 |

## Inputs

- Input commit hash: `e1639ac`.
- Baseline score sources used: `random_uniform`, `window_snp_density`, `genomic_position`, and `shuffled_trait` from the chr1 SNP prototype baseline score tables.
- Score sources are represented as `baseline:<baseline_name>` in dry-run outputs.

## Adapter Summary

- variant: ADAPT_VARIANT_EXACT_V1 (exact_variant_score); allowed_for_formal_eval=false.
- window: ADAPT_WINDOW_EXACT_V1 (exact_window_score); allowed_for_formal_eval=false.
- gene: ADAPT_GENE_WINDOW_MEAN_V1 (mean_overlapping_window_score); allowed_for_formal_eval=false.
- qtl_interval: ADAPT_QTL_INTERVAL_WINDOW_MEAN_V1 (mean_overlapping_window_score); allowed_for_formal_eval=false.

## Coverage And Rank Diagnostics

- Rank diagnostic rows: 135924.
- Rankable object/source rows: 135924.
- Unrankable object/source rows: 0.
- Object types in rank diagnostics: variant:130360;window:2888;gene:2492;qtl_interval:184.
- Split distribution in rank diagnostics: dev:90644;source_disjoint_or_temporal:36620;prototype_locked:8660.
- Score sources in rank diagnostics: baseline:genomic_position:33981;baseline:random_uniform:33981;baseline:shuffled_trait:33981;baseline:window_snp_density:33981.
- Coverage groups by object_type/source: ('gene', 'baseline:genomic_position'):17;('gene', 'baseline:random_uniform'):17;('gene', 'baseline:shuffled_trait'):17;('gene', 'baseline:window_snp_density'):17;('variant', 'baseline:genomic_position'):12;('variant', 'baseline:random_uniform'):12;('variant', 'baseline:shuffled_trait'):12;('variant', 'baseline:window_snp_density'):12.

Split-level score coverage:

- dev: rankable 90644/90644 (1); all-decoy score coverage 90644/90644 (1).
- prototype_locked: rankable 8660/8660 (1); all-decoy score coverage 8660/8660 (1).
- source_disjoint_or_temporal: rankable 36620/36620 (1); all-decoy score coverage 36620/36620 (1).

- Dry-run rank, percentile, top1, and top5 fields are process diagnostics only and are not formal top-k hit rates.
- Gene and qtl_interval rank rows use overlapping-window adapter aggregation and are diagnostic only.

## Guard Summary

- Manual review / broader evidence guard failures: 0.
- Decoy rows written as true negative: 0.
- Unknown/unlabeled rows written as negative: 0.
- Accession_id is not required as a score input field in this dry-run.
- Validation failed checks: 0.
- Missing-score diagnostic rows: 1.

## Current Limitations

- This remains a chr1 SNP-only dry-run.
- Variant and window object ranks use baseline scores only.
- Gene and QTL interval scoring relies on overlapping-window mean aggregation and has not been formalized.
- The dry-run does not define formal metric aggregation across traits, splits, or object types.
- No accession-level score adapter is accepted for direct evidence evaluation.

## Next Step

The dry-run is ready to feed 09C evaluator scaffold hardening or a candidate gene explanation adapter, while still keeping formal metric reporting out of scope.
