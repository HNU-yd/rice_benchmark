# Frozen Split v0.5.5 Report

## Scope

This run freezes a leakage-aware prototype split for the chr1 SNP-only prototype. It is not the final full benchmark split. `prototype_locked` is explicitly not `final_locked`.

No model was trained. No formal evaluator was built. No AUROC/AUPRC was reported. Evidence is not a training label, and matched decoy is not a true negative.

## Generated Tables

| table | rows |
|---|---:|
| `data/interim/frozen_split_v055/units/split_unit_table.tsv` | 288045 |
| `data/interim/frozen_split_v055/blocks/split_block_table.tsv` | 117571 |
| `data/interim/frozen_split_v055/assignments/frozen_split_assignment.tsv` | 288045 |
| `data/interim/frozen_split_v055/diagnostics/split_balance_diagnostics.tsv` | 37 |
| `data/interim/frozen_split_v055/diagnostics/split_leakage_check.tsv` | 9 |
| `data/interim/frozen_split_v055/diagnostics/split_validation.tsv` | 12 |
| `data/interim/frozen_split_v055/diagnostics/split_manifest.tsv` | 1 |

## Split Unit Counts

| split_unit_type | rows |
|---|---:|
| accession | 2268 |
| decoy_pair | 169905 |
| evidence_object | 114998 |
| region | 865 |
| trait | 9 |

## Split Block Counts

| block_type | rows |
|---|---:|
| accession_block | 2268 |
| broader_evidence_exclusion_block | 74248 |
| decoy_set_block | 33981 |
| excluded_no_exact_trait_mapping_block | 4158 |
| gene_block | 270 |
| interval_overlap_block | 4 |
| manual_review_exclusion_block | 2611 |
| mixed_evidence_block | 9 |
| qtl_region_block | 4 |
| trait_block | 9 |
| window_neighborhood_block | 9 |

## Assignment Summary

- Current input commit hash: `767f3e4`.
- Accession split counts: train:1606;dev:336;test:326.
- Evidence object split counts: excluded_broader_evidence:74248;dev:22661;source_disjoint_or_temporal:9155;excluded_no_exact_trait_mapping:4158;excluded_manual_review:2611;prototype_locked:2165.
- PEX_REPRO main evidence rows after split: 0.
- Manual review rows in main evaluation splits: 0.
- Broader evidence rows in main evaluation splits: 0.
- Decoy pair split mismatch checks failed: 0.
- Leakage warnings: 0; leakage failures: 0.
- Validation failed checks: 0.

## Block Rules

- Non-QTL evidence, gene evidence, window evidence, variant evidence, and their decoy pairs use mixed evidence blocks with 5000000 bp proximity bins.
- QTL intervals use overlap/nearby components with 1000000 bp max gap.
- Decoy pairs follow their evidence object split.
- Manual review, broader evidence, and non-exact trait mapping objects are assigned to excluded split states and do not enter main evaluation splits.

## Balance Diagnostics

- Accession split uses broad_subgroup-stratified deterministic hashing and reports PC1-PC5 means by split.
- Evidence split reports trait, object type, source, and position summaries.
- Gene density and variant density summaries remain delegated to matched decoy diagnostics and are marked unavailable in split unit tables.

## Leakage Handling

- Same accession does not cross train/dev/test.
- Mixed evidence, QTL interval, and decoy set blocks are kept within a single development/prototype/source-disjoint split.
- Evidence object and corresponding decoy pair assignments are checked for consistency.
- Unknown/unlabeled and decoy rows are never represented as true negatives.

## Limitations

- This is a chr1 SNP-only prototype split and does not cover whole-genome SNP+indel data.
- Region blocking uses coarse proximity bins and QTL source coordinates without liftover.
- MAF, LD, mappability, recombination rate, and full callability are not available in this split layer.
- `prototype_locked` is a prototype holdout state only, not the final full benchmark lock.

## Next Step

The split layer is sufficient to start an evaluator scaffold for the chr1 SNP-only prototype, while preserving the current no-training and no-formal-AUROC/AUPRC boundary.
