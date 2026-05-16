#!/usr/bin/env bash
set -euo pipefail

mkdir -p data/interim/v0_1_mini reports/v0_1_mini

python scripts/build_v0_1/build_chromosome_map.py
python scripts/build_v0_1/build_chr1_snp_variant_tables.py
python scripts/build_v0_1/build_chr1_window_tables.py
python scripts/build_v0_1/build_chr1_weak_evidence_audit.py
