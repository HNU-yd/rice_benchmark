#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python "${SCRIPT_DIR}/build_object_score_adapter_v055.py" "$@"
python "${SCRIPT_DIR}/build_dry_run_matched_set_scores_v055.py" "$@"
python "${SCRIPT_DIR}/compute_dry_run_rank_positions_v055.py" "$@"
python "${SCRIPT_DIR}/summarize_dry_run_score_coverage_v055.py" "$@"
python "${SCRIPT_DIR}/validate_evaluator_dry_run_v055.py" "$@"
