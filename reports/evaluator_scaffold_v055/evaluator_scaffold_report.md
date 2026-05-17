# Evaluator Scaffold v0.5.5 Report

## Scope

This run builds a split-aware evaluator scaffold for the chr1 SNP-only prototype. It is not a formal evaluator and does not calculate formal benchmark metrics.

No model was trained. No AUROC/AUPRC was reported. No final locked evaluation was created. `prototype_locked` is explicitly not `final_locked`. Evidence is not a training label, matched decoys are not true negatives, and unknown/unlabeled rows are not negatives.

## Generated Tables

| table | rows |
|---|---:|
| `data/interim/evaluator_scaffold_v055/inputs/evaluator_object_input_table.tsv` | 33981 |
| `data/interim/evaluator_scaffold_v055/inputs/evaluator_decoy_input_table.tsv` | 169905 |
| `data/interim/evaluator_scaffold_v055/outputs_schema/evaluator_score_input_schema.tsv` | 16 |
| `data/interim/evaluator_scaffold_v055/tasks/evaluator_task_manifest.tsv` | 84 |
| `data/interim/evaluator_scaffold_v055/outputs_schema/evaluator_output_schema.tsv` | 17 |
| `data/interim/evaluator_scaffold_v055/dry_run/baseline_score_dry_run_input.tsv` | 1559916 |
| `data/interim/evaluator_scaffold_v055/dry_run/evaluator_dry_run_join_check.tsv` | 7 |
| `data/interim/evaluator_scaffold_v055/diagnostics/evaluator_leakage_guard.tsv` | 10 |
| `data/interim/evaluator_scaffold_v055/diagnostics/evaluator_scaffold_validation.tsv` | 8 |

## Object Summary

- Current input commit hash: `b8b5794`.
- Evaluator object input rows: 33981.
- Evaluator decoy input rows: 169905.
- Object types: variant:32590;window:722;gene:623;qtl_interval:46.
- Splits: dev:22661;source_disjoint_or_temporal:9155;prototype_locked:2165.
- Task manifest rows: 84; all are dry-run only and non-formal.

## Dry-Run Join Coverage

- Window baseline dry-run join coverage: 5560/31140 (0.178548).
- Variant baseline dry-run join coverage: 131036/1528776 (0.085713).
- Baseline score dry-run alignment is a schema/join check only and does not produce benchmark metrics.

## Guard Summary

- Manual review rows in evaluator input: 0.
- Broader evidence rows in evaluator input: 0.
- Decoy rows written as true_negative: 0.
- Unknown/unlabeled rows written as negative: 0.
- Accession_id required by score schema: 0.
- Validation failed checks: 0.
- prototype_locked_not_final is retained for evaluator object rows.

## Current Limitations

- This remains a chr1 SNP-only prototype scaffold.
- The scaffold defines schemas, manifests, and dry-run joins only; it does not rank or score any model output.
- Baseline scores are accepted for dry-run schema alignment only.
- Gene and QTL region score sources are schema-defined but no current score table exists for them.
- Future formal metrics must use evidence_plus_matched_decoys and must not treat genome-wide unknowns as negatives.

## Next Step

The scaffold is ready for a chr1 SNP matched-ranking dry-run that exercises the schema and joins without reporting formal metrics.
