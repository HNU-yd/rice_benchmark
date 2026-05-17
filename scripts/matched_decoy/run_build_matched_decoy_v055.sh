#!/usr/bin/env bash
set -euo pipefail

python scripts/matched_decoy/build_matched_decoy_objects_v055.py "$@"
python scripts/matched_decoy/build_detectability_research_bias_v055.py "$@"
python scripts/matched_decoy/build_matched_decoy_candidate_pool_v055.py "$@"
python scripts/matched_decoy/build_matched_decoy_pairs_v055.py "$@"
python scripts/matched_decoy/validate_matched_decoy_v055.py "$@"
