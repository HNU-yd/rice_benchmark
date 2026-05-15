#!/usr/bin/env bash
set -euo pipefail

EXECUTE="0"
if [[ "${1:-}" == "--execute" ]]; then
  EXECUTE="1"
fi

SOURCE_ID="SRC_3K_SNP_GENOTYPE_001"
TARGET_DIR="data/raw/variants/snp/"
SOURCE_PREFIX="s3://3kricegenome/snpseek-dl/3krg-base-filt-core-v0.7/"

echo "3K Rice SNP genotype download template"
echo "source_id=${SOURCE_ID}"
echo "source_prefix=${SOURCE_PREFIX}"
echo "target_dir=${TARGET_DIR}"
echo "Required confirmation: exact file list, release, chromosome partitioning, accession list, checksum"

if [[ "${EXECUTE}" != "1" ]]; then
  echo "DRY RUN ONLY. No files will be downloaded."
  exit 0
fi

echo "EXECUTE mode requested, but no SNP download command is enabled until Phase 2B confirmation."
echo "Example commands remain disabled:"
echo "# aws s3 ls ${SOURCE_PREFIX} --no-sign-request"
echo "# aws s3 cp <confirmed_s3_uri> ${TARGET_DIR} --no-sign-request"
exit 2

