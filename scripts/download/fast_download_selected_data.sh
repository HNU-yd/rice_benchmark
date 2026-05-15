#!/usr/bin/env bash
set -uo pipefail

EXECUTE="0"
if [[ "${1:-}" == "--execute" ]]; then
  EXECUTE="1"
fi

AWS_BIN="${AWS_BIN:-}"
if [[ -z "${AWS_BIN}" ]]; then
  AWS_BIN="$(command -v aws || command -v /root/.local/bin/aws || true)"
fi

CANDIDATES="reports/fast_download/auto_download_candidates.tsv"
FAILURES="reports/fast_download/download_failures.tsv"
MAX_BYTES="${MAX_FAST_DOWNLOAD_BYTES:-1200000000}"

mkdir -p reports/fast_download
printf "candidate_id\tremote_path_or_url\tlocal_path\treason\n" > "${FAILURES}"

if [[ ! -f "${CANDIDATES}" ]]; then
  echo "Missing ${CANDIDATES}" >&2
  exit 1
fi

if [[ "${EXECUTE}" != "1" ]]; then
  echo "DRY RUN ONLY. No files will be downloaded."
fi

tail -n +2 "${CANDIDATES}" | while IFS=$'\t' read -r candidate_id data_category file_role source remote access_method expected_format priority local_path reason_selected notes; do
  case "${remote,,}" in
    *bam*|*cram*|*fastq*|*fq*|*sra*)
      printf "%s\t%s\t%s\tforbidden_read_level_file\n" "${candidate_id}" "${remote}" "${local_path}" >> "${FAILURES}"
      continue
      ;;
  esac

  size_bytes="0"
  if [[ "${notes}" =~ size_bytes=([0-9]+) ]]; then
    size_bytes="${BASH_REMATCH[1]}"
  fi
  if [[ "${size_bytes}" -gt "${MAX_BYTES}" ]]; then
    printf "%s\t%s\t%s\tlarger_than_MAX_FAST_DOWNLOAD_BYTES_%s\n" "${candidate_id}" "${remote}" "${local_path}" "${MAX_BYTES}" >> "${FAILURES}"
    continue
  fi

  echo "[${candidate_id}] ${remote} -> ${local_path}"
  if [[ "${EXECUTE}" != "1" ]]; then
    continue
  fi

  mkdir -p "$(dirname "${local_path}")"
  if [[ -s "${local_path}" ]]; then
    echo "  skip existing ${local_path}"
    continue
  fi

  partial="${local_path}.partial"
  rm -f "${partial}"
  if [[ "${access_method}" == "s3" ]]; then
    if [[ -z "${AWS_BIN}" ]]; then
      printf "%s\t%s\t%s\taws_cli_unavailable\n" "${candidate_id}" "${remote}" "${local_path}" >> "${FAILURES}"
      continue
    fi
    "${AWS_BIN}" s3 cp "${remote}" "${partial}" --no-sign-request
    status=$?
  else
    curl -L --fail --retry 5 --retry-delay 10 -o "${partial}" "${remote}"
    status=$?
  fi

  if [[ "${status}" -eq 0 && -s "${partial}" ]]; then
    mv "${partial}" "${local_path}"
  else
    rm -f "${partial}"
    printf "%s\t%s\t%s\tdownload_failed_status_%s\n" "${candidate_id}" "${remote}" "${local_path}" "${status}" >> "${FAILURES}"
    continue
  fi
done

echo "Download failure report: ${FAILURES}"
