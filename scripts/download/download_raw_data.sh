#!/usr/bin/env bash
set -euo pipefail

EXECUTE="0"
if [[ "${1:-}" == "--execute" ]]; then
  EXECUTE="1"
fi

echo "Phase 2A raw data download template"
echo "Target manifest: manifest/download_manifest.tsv"
echo "Planned raw data root: data/raw/"

if [[ "${EXECUTE}" != "1" ]]; then
  echo "DRY RUN ONLY. No files will be downloaded."
  echo "Planned sub-scripts:"
  echo "  scripts/download/download_reference.sh"
  echo "  scripts/download/download_3k_snp.sh"
  echo "  scripts/download/download_3k_indel.sh"
  echo "  scripts/download/download_traits.sh"
  echo "  scripts/download/download_annotation.sh"
  echo "  scripts/download/download_weak_evidence.sh"
  exit 0
fi

echo "EXECUTE mode requested, but Phase 2B manual confirmations are required before enabling downloads."
echo "No files were downloaded."
exit 2

