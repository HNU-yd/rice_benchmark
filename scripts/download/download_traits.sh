#!/usr/bin/env bash
set -euo pipefail

EXECUTE="0"
if [[ "${1:-}" == "--execute" ]]; then
  EXECUTE="1"
fi

SOURCE_ID="SRC_TRAIT_TABLE_003"
TARGET_DIR="data/raw/traits/"
SOURCE_URL="https://s3-ap-southeast-1.amazonaws.com/oryzasnp-atcg-irri-org/3kRG-phenotypes/3kRG_PhenotypeData_v20170411.xlsx"

echo "3K Rice trait table download template"
echo "source_id=${SOURCE_ID}"
echo "source_url=${SOURCE_URL}"
echo "target_dir=${TARGET_DIR}"
echo "Required confirmation: source version, file size, checksum, accession overlap, trait_state use only"

if [[ "${EXECUTE}" != "1" ]]; then
  echo "DRY RUN ONLY. No files will be downloaded."
  exit 0
fi

echo "EXECUTE mode requested, but no trait table download command is enabled until Phase 2B confirmation."
echo "Example command remains disabled:"
echo "# curl -L --fail --output ${TARGET_DIR}/3kRG_PhenotypeData_v20170411.xlsx ${SOURCE_URL}"
exit 2

