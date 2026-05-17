# Matched Decoy v0.5.5 Report

## Scope

This run builds a chr1 SNP-only prototype matched decoy object, candidate-pool, pair, and diagnostics layer. It is not the full benchmark, not a frozen split, not a formal evaluator, and not a model-training run.

Matched decoys are matched background candidates. They are not true negatives, and unknown or unlabeled variants/windows are not interpreted as absence labels.

## Generated Tables

| table | rows |
|---|---:|
| `data/interim/matched_decoy_v055/objects/matched_decoy_object_table.tsv` | 114998 |
| `data/interim/matched_decoy_v055/candidate_pool/matched_decoy_candidate_pool.tsv` | 1019430 |
| `data/interim/matched_decoy_v055/pairs/matched_decoy_pair_table.tsv` | 169905 |
| `data/interim/matched_decoy_v055/diagnostics/decoy_matching_diagnostics.tsv` | 61 |
| `data/interim/matched_decoy_v055/diagnostics/matching_field_availability_v055.tsv` | 15 |
| `data/interim/matched_decoy_v055/diagnostics/detectability_bias_table_v055.tsv` | 114998 |
| `data/interim/matched_decoy_v055/diagnostics/research_bias_table_v055.tsv` | 114998 |
| `data/interim/matched_decoy_v055/diagnostics/decoy_validation.tsv` | 16 |

## Object Summary

| object_type | all objects | main evaluation candidates | candidate-pool covered | matched-decoy covered |
|---|---:|---:|---:|---:|
| gene | 80635 | 623 | 623 | 623 |
| qtl_interval | 1051 | 46 | 46 | 46 |
| variant | 32590 | 32590 | 32590 | 32590 |
| window | 722 | 722 | 722 | 722 |

## Key Counts

- Main evaluation candidate objects: 33981.
- Broader evidence objects excluded from main evaluation: 74248.
- Manual-review-required objects excluded from main evaluation: 2611.
- PEX_REPRO exact main-evaluation evidence objects: 0.
- Q-TARO interval objects: 1051; these remain region-level / interval-level evidence and are not high-confidence gene mappings.
- Mean candidate rows per main object: 30.0000.
- Mean decoy rows per main object: 5.0000.
- Validation failed checks: 0.

## Matching Fields

- Used fields: coordinate, position_bin, gene_density, variant_density, annotation_richness, evidence_source_coverage, database_detectability, interval_length, research_bias, chr1_snp_coverage.
- Unavailable fields: MAF, LD, missingness, mappability, recombination_rate.
- Detectability proxy: chr1 SNP coverage, window coverage, variant coverage, and database detectability proxy.
- Research-bias proxy: annotation record count, external knowledge hit count, database source count, trait evidence count, and known-gene proximity proxy.

## Handling Rules

- Only exact frozen trait mapping enters the main evaluation candidate pool.
- Ambiguous frozen-trait keyword matches and broader evidence are retained but excluded from the main pool.
- PEX_REPRO remains at zero exact main-evaluation evidence objects; no label was force-filled.
- Q-TARO is handled as region-level qtl_interval evidence, not causal label and not high-confidence gene label.
- All usage remains evaluation / explanation / case study / development evidence candidate only; no training_label is introduced.

## Limitations

- The candidate pool is bounded and prototype-scale, not a full genome-wide matched background enumeration.
- Current matching uses chr1 SNP-only coverage; indels, MAF, LD, mappability, recombination rate, and full callability are unavailable.
- Detectability and research-bias controls are proxies and must not be reported as complete correction.
- Q-TARO coordinates are source-reported intervals without liftover.
- Candidate decoys are background controls, not true negatives.

## Split Readiness

The layer is sufficient to start a split-freezing design pass for the chr1 SNP-only prototype, provided the split step preserves gene/interval proximity blocking and keeps manual-review/broader evidence out of the main evaluation pool.
