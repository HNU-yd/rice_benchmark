#!/usr/bin/env bash
set -euo pipefail

mkdir -p data/interim/baselines_chr1_snp reports/baselines_chr1_snp

python scripts/baselines/build_chr1_snp_baselines.py
python scripts/eval/evaluate_chr1_snp_baselines.py
python scripts/eval/validate_baseline_outputs.py
