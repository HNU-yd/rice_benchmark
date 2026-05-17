#!/usr/bin/env bash
set -euo pipefail

python scripts/external_knowledge/build_gene_annotation_table.py "$@"
python scripts/external_knowledge/build_gene_id_mapping_table.py "$@"
python scripts/external_knowledge/build_known_gene_evidence_table.py "$@"
python scripts/external_knowledge/build_trait_gene_evidence_table.py "$@"
python scripts/external_knowledge/build_qtl_interval_evidence_table.py "$@"
python scripts/external_knowledge/build_evidence_coordinate_mapping_table.py "$@"
python scripts/external_knowledge/validate_external_knowledge_layer.py "$@"
