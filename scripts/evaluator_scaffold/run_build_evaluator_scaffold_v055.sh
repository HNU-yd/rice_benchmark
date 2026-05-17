#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python "${SCRIPT_DIR}/build_evaluator_object_input_v055.py" "$@"
python "${SCRIPT_DIR}/build_evaluator_decoy_input_v055.py" "$@"
python "${SCRIPT_DIR}/build_evaluator_score_schema_v055.py" "$@"
python "${SCRIPT_DIR}/build_evaluator_task_manifest_v055.py" "$@"
python "${SCRIPT_DIR}/build_baseline_score_dry_run_input_v055.py" "$@"
python "${SCRIPT_DIR}/run_evaluator_scaffold_validation_v055.py" "$@"
