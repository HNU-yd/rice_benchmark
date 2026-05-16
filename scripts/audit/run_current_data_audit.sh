#!/usr/bin/env bash
set -euo pipefail

mkdir -p reports/current_data_status reports/external_database_plan

python scripts/audit/summarize_current_assets.py
python scripts/audit/summarize_accession_mapping_sources.py
python scripts/audit/summarize_external_database_candidates.py
