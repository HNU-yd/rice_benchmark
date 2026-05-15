#!/usr/bin/env bash
set -euo pipefail

EXECUTE="0"
if [[ "${1:-}" == "--execute" ]]; then
  EXECUTE="1"
fi

TARGET_DIR="data/raw/evidence/"

echo "Weak evidence download template"
echo "target_dir=${TARGET_DIR}"
echo "Required confirmation: provenance, trait specificity, coordinate build, leakage control"
echo "Candidate sources: SRC_WEAK_QTL_001, SRC_WEAK_KNOWN_GENES_001, SRC_WEAK_GWAS_001"

if [[ "${EXECUTE}" != "1" ]]; then
  echo "DRY RUN ONLY. No files will be downloaded."
  exit 0
fi

echo "EXECUTE mode requested, but no weak evidence download command is enabled until Phase 2B confirmation."
echo "Example command remains disabled:"
echo "# curl -L --fail --output ${TARGET_DIR}/<confirmed_evidence_file> <confirmed_evidence_url>"
exit 2

