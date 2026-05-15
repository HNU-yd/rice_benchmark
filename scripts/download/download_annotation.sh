#!/usr/bin/env bash
set -euo pipefail

EXECUTE="0"
if [[ "${1:-}" == "--execute" ]]; then
  EXECUTE="1"
fi

SOURCE_ID="SRC_GENE_ANNOTATION_001"
TARGET_DIR="data/raw/annotation/"
SOURCE_PAGE="https://www.ncbi.nlm.nih.gov/refseq/annotation_euk/Oryza_sativa_Japonica_Group/102/"

echo "Gene annotation download template"
echo "source_id=${SOURCE_ID}"
echo "source_page=${SOURCE_PAGE}"
echo "target_dir=${TARGET_DIR}"
echo "Required confirmation: annotation release, package URL, gene ID system, checksum"

if [[ "${EXECUTE}" != "1" ]]; then
  echo "DRY RUN ONLY. No files will be downloaded."
  exit 0
fi

echo "EXECUTE mode requested, but no annotation download command is enabled until Phase 2B confirmation."
echo "Example command remains disabled:"
echo "# curl -L --fail --output ${TARGET_DIR}/<confirmed_annotation_file> <confirmed_annotation_url>"
exit 2

