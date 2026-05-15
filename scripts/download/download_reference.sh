#!/usr/bin/env bash
set -euo pipefail

EXECUTE="0"
if [[ "${1:-}" == "--execute" ]]; then
  EXECUTE="1"
fi

SOURCE_ID="SRC_REF_IRGSP_FASTA_003"
TARGET_DIR="data/raw/reference/"
FASTA_URL="https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/001/433/935/GCF_001433935.1_IRGSP-1.0/GCF_001433935.1_IRGSP-1.0_genomic.fna.gz"
GFF_URL="https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/001/433/935/GCF_001433935.1_IRGSP-1.0/GCF_001433935.1_IRGSP-1.0_genomic.gff.gz"

echo "Reference genome download template"
echo "source_id=${SOURCE_ID}"
echo "target_dir=${TARGET_DIR}"
echo "fasta_url=${FASTA_URL}"
echo "gff_url=${GFF_URL}"
echo "Required confirmation: GCF/GCA source choice, FASTA package, chromosome naming, checksum"

if [[ "${EXECUTE}" != "1" ]]; then
  echo "DRY RUN ONLY. No files will be downloaded."
  exit 0
fi

echo "EXECUTE mode requested, but no reference download command is enabled until Phase 2C confirmation."
echo "Example command remains disabled:"
echo "# curl -L --fail --output ${TARGET_DIR}/GCF_001433935.1_IRGSP-1.0_genomic.fna.gz ${FASTA_URL}"
echo "# curl -L --fail --output ${TARGET_DIR}/GCF_001433935.1_IRGSP-1.0_genomic.gff.gz ${GFF_URL}"
exit 2
