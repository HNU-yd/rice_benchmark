#!/usr/bin/env bash
set -euo pipefail

mkdir -p data/interim/task1_chr1_snp reports/task1_chr1_snp

python scripts/task1/build_chr1_snp_task1_instances.py
python scripts/task1/inspect_chr1_snp_task1_instances.py
