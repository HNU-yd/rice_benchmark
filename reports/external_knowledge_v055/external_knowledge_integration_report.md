# External Knowledge v0.5.5 Integration Report

## Scope

This run integrates local RAP-DB, funRiceGenes, MSU / RGAP, Oryzabase, Q-TARO, and reference annotation resources into a unified external knowledge / annotation / weak localization reference layer.

No model was trained. No matched decoy or frozen split was constructed. No evidence row is allowed to be used as a training label, and no unknown/unlabeled variant or window is treated as a true negative.

## Raw Sources Used

- `data/raw/external_knowledge/rapdb/IRGSP-1.0_representative_annotation_2026-02-05.tsv.gz` (RAP-DB, gene_annotation)
- `data/raw/external_knowledge/rapdb/IRGSP-1.0_representative_transcript_exon_2026-02-05.gtf.gz` (RAP-DB, gene_annotation)
- `data/raw/external_knowledge/rapdb/RAP-MSU_2026-02-05.txt.gz` (RAP-DB, id_mapping_resource)
- `data/raw/external_knowledge/rapdb/curated_genes.json` (RAP-DB, known_gene_database)
- `data/raw/external_knowledge/rapdb/agri_genes.json` (RAP-DB, known_gene_database)
- `data/raw/external_knowledge/funricegenes/geneInfo.table.txt` (funRiceGenes, known_gene_database)
- `data/raw/external_knowledge/funricegenes/geneKeyword.table.txt` (funRiceGenes, external_trait_gene_knowledge)
- `data/raw/external_knowledge/funricegenes/famInfo.table.txt` (funRiceGenes, id_mapping_resource)
- `data/raw/external_knowledge/msu_rgAP/osa1_r7.all_models.gff3.gz` (MSU_RGAP, gene_annotation)
- `data/raw/external_knowledge/msu_rgAP/osa1_r7.locus_brief_info.txt.gz` (MSU_RGAP, gene_annotation)
- `data/raw/evidence/known_genes/oryzabase/OryzabaseGeneListEn.tsv` (Oryzabase, known_gene_database)
- `data/raw/evidence/qtl/qtaro/qtaro_sjis.zip` (Q-TARO, qtl_database)
- `data/raw/reference/GCF_001433935.1_IRGSP-1.0_genomic.gff.gz` (NCBI_RefSeq, gene_annotation)

## Generated Tables

| table | rows |
|---|---:|
| `data/interim/external_knowledge_v055/annotation/gene_annotation_table.tsv` | 125082 |
| `data/interim/external_knowledge_v055/mapping/gene_id_mapping_table.tsv` | 154144 |
| `data/interim/external_knowledge_v055/evidence/known_gene_evidence_table.tsv` | 80635 |
| `data/interim/external_knowledge_v055/evidence/trait_gene_evidence_table.tsv` | 80635 |
| `data/interim/external_knowledge_v055/evidence/qtl_interval_evidence_table.tsv` | 1051 |
| `data/interim/external_knowledge_v055/evidence/evidence_coordinate_mapping_table.tsv` | 81686 |
| `data/interim/external_knowledge_v055/evidence/evidence_source_manifest.tsv` | 13 |
| `data/interim/external_knowledge_v055/qc_diagnostics/external_knowledge_manual_review_table.tsv` | 95848 |
| `data/interim/external_knowledge_v055/qc_diagnostics/external_knowledge_validation.tsv` | 13 |

## Gene ID Mapping Success

| source | mapping rows | successful mapped rows | success rate |
|---|---:|---:|---:|
| Oryzabase | 51801 | 47509 | 0.9171 |
| Q-TARO | 661 | 0 | 0.0000 |
| RAP-DB | 66605 | 55968 | 0.8403 |
| funRiceGenes_famInfo | 18556 | 18128 | 0.9769 |
| funRiceGenes_geneInfo | 16521 | 16142 | 0.9771 |

## Evidence Mapping Summary

- Gene-level evidence/reference rows: 80635.
- Interval-level QTL rows: 1051.
- Variant-level evidence rows: 0 in this integration pass.
- Trait-gene rows with exact frozen 9 trait mapping: 4696.
- Ambiguous frozen-trait keyword matches requiring manual review: 2391.
- Trait-gene rows kept in broader evidence pool or manual review: 75939.
- Manual review rows: 95848.
- Validation failed checks: 0.

Support-level counts:
- high_confidence: 11598
- medium_confidence: 23108
- weak: 45929

Coordinate mapping status counts:
- gene_level_only: 6859
- mapped_high_confidence: 73776
- region_level_only: 1033
- unmapped: 18

## Frozen-Trait Candidate Pool

- CUAN_REPRO: 3 gene-level rows
- CUDI_CODE_REPRO: 524 gene-level rows
- CULT_CODE_REPRO: 907 gene-level rows
- FLA_REPRO: 52 gene-level rows
- LLT_CODE: 11 gene-level rows
- LSEN: 482 gene-level rows
- PTH: 4 gene-level rows
- SPKF: 2713 gene-level rows

## Usage Boundary

All rows in these tables are restricted to evaluation reference, explanation, case study, or development evidence candidate usage. They are not training labels and are not causal ground truth.

## Current Limitations

- Q-TARO coordinates are treated as source-reported intervals and downgraded to region-level overlap; no liftover was performed.
- Trait-name mapping uses conservative keyword rules against the frozen 9 traits and therefore leaves many rows in the broader pool.
- Some Oryzabase and funRiceGenes records lack stable RAP/MSU coordinates and require manual review.
- Source license and redistribution terms were not reinterpreted in this processing step.
- Detectability and research-bias matching fields are still not complete; this layer is only a prerequisite for matched decoy construction.

## Next Step Toward Matched Decoy

Use `gene_annotation_table.tsv` for gene density and nearest-gene features, `gene_id_mapping_table.tsv` for RAP/MSU/Oryzabase/funRiceGenes harmonization, and the gene/QTL reference tables to define evidence objects. The matched decoy step must match evidence objects against comparable non-evidence background by chromosome/position, gene density, variant density, MAF/LD when available, annotation richness, and explicit matching-field availability.
