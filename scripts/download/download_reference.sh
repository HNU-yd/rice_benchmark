#!/usr/bin/env bash
set -euo pipefail

EXECUTE="0"
if [[ "${1:-}" == "--execute" ]]; then
  EXECUTE="1"
fi

SOURCE_ID="SRC_REF_IRGSP_FASTA_003"
TARGET_DIR="data/raw/reference/"

echo "Reference genome download template"
echo "source_id=${SOURCE_ID}"
echo "target_dir=${TARGET_DIR}"
echo "Required confirmation: GCF/GCA source choice, FASTA package, chromosome naming, checksum"

if [[ "${EXECUTE}" != "1" ]]; then
  echo "DRY RUN ONLY. No files will be downloaded."
  exit 0
fi

echo "EXECUTE mode requested, but no reference download command is enabled until Phase 2B confirmation."
echo "Example command remains disabled:"
echo "# ncbi datasets download genome accession GCF_001433935.1 --include genome,gff3 --filename <confirmed_output.zip>"
exit 2

