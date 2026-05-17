#!/usr/bin/env bash
set -euo pipefail

python scripts/frozen_split/build_split_units_v055.py "$@"
python scripts/frozen_split/build_split_blocks_v055.py "$@"
python scripts/frozen_split/assign_frozen_splits_v055.py "$@"
python scripts/frozen_split/build_split_balance_diagnostics_v055.py "$@"
python scripts/frozen_split/check_split_leakage_v055.py "$@"
python scripts/frozen_split/validate_frozen_split_v055.py "$@"
