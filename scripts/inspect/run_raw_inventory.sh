#!/usr/bin/env bash
set -euo pipefail

mkdir -p reports/raw_data_inventory data/interim/inventory

python scripts/inspect/inspect_raw_files.py
python scripts/inspect/inspect_archives.py
python scripts/inspect/inspect_reference.py
python scripts/inspect/inspect_vcf_headers.py
python scripts/inspect/inspect_plink_files.py
python scripts/inspect/inspect_trait_table.py
python scripts/inspect/inspect_accession_metadata.py
python scripts/inspect/compare_accession_sets.py
