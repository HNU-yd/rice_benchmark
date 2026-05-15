#!/usr/bin/env bash
set -euo pipefail

AWS_BIN="${AWS_BIN:-}"
if [[ -z "${AWS_BIN}" ]]; then
  AWS_BIN="$(command -v aws || command -v /root/.local/bin/aws || true)"
fi

RAW_LISTING_DIR="data/raw/listings"
REPORT_DIR="reports/fast_download"
mkdir -p "${RAW_LISTING_DIR}" "${REPORT_DIR}"

SUMMARY="${REPORT_DIR}/listing_summary.tsv"
printf "listing_id\tpath\tstatus\tn_lines\toutput_file\tnotes\n" > "${SUMMARY}"

run_listing() {
  local listing_id="$1"
  local path="$2"
  local recursive="$3"
  local output_file="${RAW_LISTING_DIR}/${listing_id}.txt"
  local report_file="${REPORT_DIR}/${listing_id}.txt"
  local tmp_file="${output_file}.tmp"
  local cmd=("${AWS_BIN}" s3 ls "${path}" --no-sign-request)
  if [[ "${recursive}" == "yes" ]]; then
    cmd=("${AWS_BIN}" s3 ls "${path}" --recursive --no-sign-request)
  fi

  if [[ -z "${AWS_BIN}" ]]; then
    : > "${output_file}"
    cp "${output_file}" "${report_file}"
    printf "%s\t%s\taws_cli_unavailable\t0\t%s\taws CLI not available\n" "${listing_id}" "${path}" "${output_file}" >> "${SUMMARY}"
    return 0
  fi

  set +e
  "${cmd[@]}" > "${tmp_file}.full" 2> "${tmp_file}.err"
  local status=$?
  set -e

  if [[ "${status}" -eq 0 ]]; then
    head -n 5000 "${tmp_file}.full" > "${output_file}"
    cp "${output_file}" "${report_file}"
    local n_lines
    n_lines="$(wc -l < "${output_file}" | tr -d ' ')"
    printf "%s\t%s\tsuccess\t%s\t%s\ttruncated_to_first_5000_lines_if_needed\n" "${listing_id}" "${path}" "${n_lines}" "${output_file}" >> "${SUMMARY}"
  else
    : > "${output_file}"
    cp "${tmp_file}.err" "${report_file}"
    printf "%s\t%s\tfailed\t0\t%s\t%s\n" "${listing_id}" "${path}" "${output_file}" "$(tr '\n\t' '  ' < "${tmp_file}.err")" >> "${SUMMARY}"
  fi

  rm -f "${tmp_file}.full" "${tmp_file}.err"
}

run_listing "aws_3kricegenome_root" "s3://3kricegenome/" "no"
run_listing "aws_3kricegenome_snpseek_dl" "s3://3kricegenome/snpseek-dl/" "no"
run_listing "aws_3kricegenome_vcf" "s3://3kricegenome/VCF/" "no"
run_listing "aws_3kricegenome_reduced" "s3://3kricegenome/reduced/" "no"
run_listing "aws_3kricegenome_reduced_recursive" "s3://3kricegenome/reduced/" "yes"
run_listing "aws_3kricegenome_snpseek_dl_recursive" "s3://3kricegenome/snpseek-dl/" "yes"
run_listing "aws_3kricegenome_snpseek_dl_phenotype" "s3://3kricegenome/snpseek-dl/phenotype/" "yes"
run_listing "aws_3kricegenome_snpseek_dl_core" "s3://3kricegenome/snpseek-dl/3krg-base-filt-core-v0.7/" "yes"

echo "Listing summary written to ${SUMMARY}"
