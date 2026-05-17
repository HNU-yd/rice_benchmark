# Design v0.5.5 Data Processing Report

## Scope

This run aligns the current `rice_benchmark` frozen v0.1 trait data with the v0.5.5 design documents. It materializes data-driven covariate availability, trait usability, trait preprocessing, matching-field availability, and main negative-pair protocol tables.

This run does not train a model, does not build phenotype prediction targets, does not use GWAS/QTL/known-gene evidence as training labels, and does not turn unknown variants/windows into negatives.

## Generated Tables

- `data/interim/design_v055/metadata/covariate_accession_table.tsv`: 2268 high-confidence accession covariate rows.
- `data/interim/design_v055/metadata/trait_usability_table.tsv`: 9 frozen trait usability rows.
- `data/interim/design_v055/metadata/trait_preprocessing_table.tsv`: 9 frozen trait preprocessing rows.
- `data/interim/design_v055/decoy/matching_field_availability_table.tsv`: matching and detectability field status before decoy construction.
- `data/interim/design_v055/negative_pairs/negative_pair_protocol_table.tsv`: 18804 main mismatched trait-state pair rows.
- `data/interim/design_v055/negative_pairs/candidate_pool_size_table.tsv`: row-level candidate pool sizes.
- `data/interim/design_v055/negative_pairs/balance_diagnostics_table.tsv`: row-level subgroup/PC/CROPYEAR/source diagnostics for selected pairs.
- `data/interim/design_v055/qc_diagnostics/v055_generated_table_schema.tsv`: schema records for all generated v0.5.5 protocol tables.

Review copies of the small protocol and summary tables were written to `reports/current_data_status/v055_*.tsv`.

## Covariate Coverage

- Qmatrix broad subgroup coverage: 2268 / 2268 accessions.
- PC1-PC12 coverage: 2268 / 2268 accessions.
- CROPYEAR known coverage: 741 / 2268 accessions; missing CROPYEAR is retained as `unknown_env`.
- Exact sequencing `LibraryName` remains QC-only and is not used as a residualization or hard pairing stratum.

## Trait Usability

- Frozen traits assessed: 9.
- Usable for main under current thresholds: 9 / 9.
- Current frozen traits are categorical/binary, so numeric residualization is not applied in this processing pass.
- Trait states remain condition signals; they are not phenotype prediction labels.

## Negative Pair Protocol

- Main mismatched trait-state pairs generated: 18804.
- L1 main hard negative rows: 18804.
- L2 relaxed hard negative rows: 0.
- L3 covariate-balanced negative rows: 0.
- Rows without a pair: 0.
- L4 random/shuffled controls are intentionally not generated here because v0.5.5 defines them as diagnostic-only.

## Candidate Pool Summary

| trait_id | n rows | median L1 pool | L1 pool < 20 | selected L1 | selected L2 | selected L3 | no pair |
|---|---:|---:|---:|---:|---:|---:|---:|
| data_lt_2007__cuan_repro | 2094 | 155 | 0 | 2094 | 0 | 0 | 0 |
| data_lt_2007__cudi_code_repro | 2093 | 108 | 0 | 2093 | 0 | 0 | 0 |
| data_lt_2007__cult_code_repro | 2075 | 235 | 0 | 2075 | 0 | 0 | 0 |
| data_lt_2007__fla_repro | 2092 | 200 | 0 | 2092 | 0 | 0 | 0 |
| data_lt_2007__llt_code | 2076 | 173 | 0 | 2076 | 0 | 0 | 0 |
| data_lt_2007__lsen | 2093 | 218 | 0 | 2093 | 0 | 0 | 0 |
| data_lt_2007__pex_repro | 2095 | 153 | 0 | 2095 | 0 | 0 | 0 |
| data_lt_2007__pth | 2092 | 216 | 0 | 2092 | 0 | 0 | 0 |
| data_lt_2007__spkf | 2094 | 124 | 0 | 2094 | 0 | 0 | 0 |

## Validation

- Failed checks: 0.
- Warning checks: 0.

## Risks And Next Engineering Tasks

- `CROPYEAR` is only a weak environment proxy; the project still lacks a complete site/location/season table.
- Detectability and research-bias matching fields are only partial or missing; matched decoy construction must keep these fields marked unavailable until unified tables exist.
- Kinship is present as a large raw matrix but is not loaded into hard strata; use it only for LMM/covariance baselines or sensitivity analyses.
- Next step: integrate external knowledge into a unified gene annotation / known-gene evidence / gene-ID mapping layer, then construct matched decoy and frozen splits.
