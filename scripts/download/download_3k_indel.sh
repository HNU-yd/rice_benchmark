#!/usr/bin/env bash
set -euo pipefail

EXECUTE="0"
if [[ "${1:-}" == "--execute" ]]; then
  EXECUTE="1"
fi

SOURCE_ID="SRC_3K_INDEL_GENOTYPE_002"
TARGET_DIR="data/raw/variants/indel/"
SOURCE_PREFIX="s3://3kricegenome/VCF/"

echo "3K Rice indel genotype download template"
echo "source_id=${SOURCE_ID}"
echo "source_prefix=${SOURCE_PREFIX}"
echo "target_dir=${TARGET_DIR}"
echo "Required confirmation: exact VCF path, indel representation, accession layout, reference build"

if [[ "${EXECUTE}" != "1" ]]; then
  echo "DRY RUN ONLY. No files will be downloaded."
  exit 0
fi

echo "EXECUTE mode requested, but no indel download command is enabled until Phase 2B confirmation."
echo "Example commands remain disabled:"
echo "# aws s3 ls ${SOURCE_PREFIX} --no-sign-request"
echo "# aws s3 cp <confirmed_s3_uri> ${TARGET_DIR} --no-sign-request"
exit 2

