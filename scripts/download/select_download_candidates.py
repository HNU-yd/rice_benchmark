#!/usr/bin/env python3
"""Select fast-download candidates from lightweight source listings."""

from __future__ import annotations

import csv
import re
from pathlib import Path


LISTING_DIR = Path("data/raw/listings")
REPORT_DIR = Path("reports/fast_download")
MAX_BYTES = 1_200_000_000

FORBIDDEN_RE = re.compile(
    r"((?:\.bam|\.cram|\.fastq|\.fq)(?:\.gz)?$|(^|[/_.-])sra([/_.-]|$)|pav|cnv|largesv|(^|[/_.-])sv([/_.-]|$)|5refs|pan-genome)",
    re.I,
)
NON_PRIMARY_PANEL_RE = re.compile(
    r"(^|/)(1k1rg|pue|gq92|irri_elite|irri_lines|baap|hdf5|diseasenils|irrielite|magic|kaust_irri_3k_16refs)(/|$)",
    re.I,
)
ALLOW_EXT = (
    ".vcf",
    ".vcf.gz",
    ".bcf",
    ".h5",
    ".hdf5",
    ".tsv",
    ".csv",
    ".xls",
    ".xlsx",
    ".txt",
    ".tbi",
    ".gz",
    ".gff",
    ".gff3",
    ".gtf",
    ".fna",
    ".fa",
    ".fasta",
    ".zip",
    ".tar.gz",
    ".html",
    ".htm",
)


def parse_aws_listing(path: Path) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip() or " PRE " in line:
            continue
        parts = line.split(maxsplit=3)
        if len(parts) != 4:
            continue
        try:
            size = int(parts[2])
        except ValueError:
            continue
        key = parts[3]
        if not key:
            continue
        rows.append((size, key))
    return rows


def key_prefix_for_listing(path: Path) -> str:
    """Map non-recursive prefix listings back to their original S3 prefix."""
    return {
        "aws_3kricegenome_reduced.txt": "reduced/",
        "aws_3kricegenome_snpseek_dl.txt": "snpseek-dl/",
        "aws_3kricegenome_snpseek_dl_core.txt": "snpseek-dl/3krg-base-filt-core-v0.7/",
        "aws_3kricegenome_snpseek_dl_phenotype.txt": "snpseek-dl/phenotype/",
    }.get(path.name, "")


def normalize_key_for_listing(path: Path, key: str) -> str:
    prefix = key_prefix_for_listing(path)
    if prefix and not key.startswith(prefix):
        return f"{prefix}{key}"
    return key


def infer_category(key: str) -> tuple[str, str, str, str]:
    lower = key.lower()
    if "phenotype" in lower or "trait" in lower:
        return "trait_table", "trait_phenotype_table", "P0", "data/raw/traits"
    if "indel" in lower:
        return "indel_genotype", "indel_genotype", "P0", "data/raw/variants/indel"
    if "rice_rp" in lower:
        return "accession_metadata", "accession_metadata_archive", "P0", "data/raw/accessions"
    if "qmatrix" in lower:
        return "accession_metadata", "population_structure_matrix", "P1", "data/raw/metadata"
    if "core" in lower or "snp" in lower or lower.endswith((".bed.gz", ".bim.gz", ".fam.gz")):
        return "snp_genotype", "snp_genotype", "P0", "data/raw/variants/snp"
    if "qmatrix" in lower or "rice_rp" in lower or "manifest" in lower or "download" in lower or "readme" in lower or "license" in lower:
        return "accession_metadata", "metadata_or_description", "P1", "data/raw/metadata"
    if "gene" in lower or "annotation" in lower:
        return "annotation", "annotation", "P1", "data/raw/annotation"
    return "metadata", "metadata_or_description", "P2", "data/raw/metadata"


def include_key(size: int, key: str) -> tuple[bool, str]:
    lower = key.lower()
    name = Path(key).name
    if FORBIDDEN_RE.search(lower):
        return False, "forbidden_read_or_out_of_scope_keyword"
    if NON_PRIMARY_PANEL_RE.search(lower):
        return False, "non_primary_panel_or_multi_reference_subset"
    if size <= 0:
        return False, "empty_or_directory_marker"
    if not lower.endswith(ALLOW_EXT):
        return False, "extension_not_prioritized"
    if size > MAX_BYTES:
        return False, f"larger_than_fast_download_limit_{MAX_BYTES}"

    primary_prefixes = (
        "reduced/",
        "snpseek-dl/3krg-base-filt-core-v0.7/",
        "snpseek-dl/phenotype/",
        "snpseek-dl/3k-pruned-v2.1/",
    )
    root_allowed = "/" not in key
    snpseek_root_file = lower.startswith("snpseek-dl/") and lower.count("/") == 1
    if not root_allowed and not snpseek_root_file and not lower.startswith(primary_prefixes):
        return False, "not_primary_3k_rice_source_path"

    if lower.startswith("reduced/"):
        reduced_keep = (
            "nipponbare_indel",
            "3krg-indel-readme",
            "2pt3mio_3krg-indel-readme",
            "nb_bialsnp_pseudo.vcf.gz",
            "nb_bialsnp_pseudo.vcf.gz.tbi",
            "nb-snp.frqx.gz",
            "27m-snpeff-dstinct-geneid",
            "readme-3krg",
            "filt_3krg-snp-readme",
            "990k_3krg-snp-readme",
        )
        if not any(token in lower for token in reduced_keep):
            return False, "reduced_path_not_selected_for_fast_primary_download"

    if lower.startswith("snpseek-dl/3k-pruned-v2.1/"):
        pruned_keep = (
            "3krg-newprunedsnpset.txt",
            "readme_pruned-v2.1.txt",
            "pca_pruned_v2.1.eigenvec",
            "result.log.txt",
        )
        if not any(token in lower for token in pruned_keep):
            return False, "pruned_large_matrix_skipped_for_fast_download"

    if snpseek_root_file:
        snpseek_root_keep = (
            "3k-hdra-snp-comm-miss5pc.txt.gz",
            "3k_coresnp-v2.1.plink.tar.gz",
            "nb_bialsnp_pseudo_canonical_all.vcf.gz",
            "qmatrix-k9-3krg.csv",
            "rice_rp.tar.gz",
            "snpseek_subsets.html",
        )
        if not any(token in lower for token in snpseek_root_keep):
            return False, "snpseek_root_file_not_selected_for_fast_download"

    if root_allowed:
        root_keep = (
            "3krg_download",
            "manifest",
            "readme",
            "rvp_manifest",
            "snpseek_down",
            "3k-",
            "3k_core",
            "nb_bialsnp_pseudo_canonical_all.vcf.gz",
            "rice_rp.tar.gz",
            "qmatrix",
            "snpseek_subsets",
        )
        if not any(token in lower for token in root_keep):
            return False, "root_file_not_selected_for_fast_primary_download"

    priority_keywords = [
        "phenotype",
        "trait",
        "variety",
        "accession",
        "sample",
        "metadata",
        "iris",
        "3krg",
        "3k",
        "snp",
        "indel",
        "vcf",
        "hdf5",
        "h5",
        "core",
        "filtered",
        "base",
        "pruned",
        "gwas",
        "qtl",
        "gene",
        "annotation",
        "readme",
        "license",
        "md5",
        "checksum",
        "manifest",
        "qmatrix",
        "rice_rp",
    ]
    if any(token in lower for token in priority_keywords):
        return True, "matches_priority_keyword"
    if name in {"MANIFEST", "MANIFEST-noURL", "MANIFEST_original.txt"}:
        return True, "manifest_file"
    return False, "not_relevant_enough"


def local_path_for(key: str, category_dir: str) -> str:
    return str(Path(category_dir) / Path(key).name)


def candidate_rows() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    candidates: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    skipped_seen: set[str] = set()

    seed_urls = [
        {
            "candidate_id": "CAND_REF_FASTA_GCF001433935",
            "data_category": "reference",
            "file_role": "reference_fasta",
            "source": "NCBI RefSeq GCF_001433935.1",
            "remote_path_or_url": "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/001/433/935/GCF_001433935.1_IRGSP-1.0/GCF_001433935.1_IRGSP-1.0_genomic.fna.gz",
            "access_method_type": "https",
            "expected_format": "FASTA.gz",
            "priority": "P0",
            "local_path": "data/raw/reference/GCF_001433935.1_IRGSP-1.0_genomic.fna.gz",
            "reason_selected": "confirmed_exact_reference_fasta",
            "notes": "size_bytes=118932090; source_id=SRC_REF_IRGSP_FASTA_003",
        },
        {
            "candidate_id": "CAND_REF_GFF_GCF001433935",
            "data_category": "annotation",
            "file_role": "reference_gff3",
            "source": "NCBI RefSeq GCF_001433935.1",
            "remote_path_or_url": "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/001/433/935/GCF_001433935.1_IRGSP-1.0/GCF_001433935.1_IRGSP-1.0_genomic.gff.gz",
            "access_method_type": "https",
            "expected_format": "GFF3.gz",
            "priority": "P0",
            "local_path": "data/raw/reference/GCF_001433935.1_IRGSP-1.0_genomic.gff.gz",
            "reason_selected": "confirmed_exact_reference_gff3",
            "notes": "size_bytes=10328864; source_id=SRC_REF_IRGSP_FASTA_003",
        },
        {
            "candidate_id": "CAND_REF_MD5_GCF001433935",
            "data_category": "metadata",
            "file_role": "reference_md5",
            "source": "NCBI RefSeq GCF_001433935.1",
            "remote_path_or_url": "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/001/433/935/GCF_001433935.1_IRGSP-1.0/md5checksums.txt",
            "access_method_type": "https",
            "expected_format": "TXT",
            "priority": "P0",
            "local_path": "data/raw/checksums/GCF_001433935.1_IRGSP-1.0_md5checksums.txt",
            "reason_selected": "confirmed_reference_md5_file",
            "notes": "size_bytes=12720; source_id=SRC_REF_IRGSP_FASTA_003",
        },
    ]
    candidates.extend(seed_urls)

    seen_remote = {row["remote_path_or_url"] for row in candidates}
    seen_local = {row["local_path"] for row in candidates}
    counter = len(candidates) + 1
    for listing in sorted(LISTING_DIR.glob("*.txt")):
        for size, raw_key in parse_aws_listing(listing):
            key = normalize_key_for_listing(listing, raw_key)
            include, reason = include_key(size, key)
            if not include:
                if FORBIDDEN_RE.search(key) and key not in skipped_seen:
                    skipped.append(
                        {
                            "remote_path_or_url": f"s3://3kricegenome/{key}",
                            "size_bytes": str(size),
                            "reason_skipped": reason,
                        }
                    )
                    skipped_seen.add(key)
                continue
            remote = f"s3://3kricegenome/{key}"
            if remote in seen_remote:
                continue
            category, role, priority, local_dir = infer_category(key)
            expected_format = Path(key).suffix.lstrip(".").upper() or "unknown"
            if key.lower().endswith(".vcf.gz"):
                expected_format = "VCF.gz"
            elif key.lower().endswith(".tar.gz"):
                expected_format = "tar.gz"

            local_path = local_path_for(key, local_dir)
            if local_path in seen_local:
                continue
            candidates.append(
                {
                    "candidate_id": f"CAND_AUTO_{counter:04d}",
                    "data_category": category,
                    "file_role": role,
                    "source": "AWS Open Data 3K Rice",
                    "remote_path_or_url": remote,
                    "access_method_type": "s3",
                    "expected_format": expected_format,
                    "priority": priority,
                    "local_path": local_path,
                    "reason_selected": reason,
                    "notes": f"size_bytes={size}; listing={listing.name}",
                }
            )
            seen_remote.add(remote)
            seen_local.add(local_path)
            counter += 1

    unresolved = [
        {
            "data_category": "weak_evidence",
            "needed_data": "known trait genes / cloned genes",
            "reason_unresolved": "no exact downloadable table identified in fast listing",
            "suggested_next_step": "manual database export review for OGRO/Oryzabase/Q-TARO",
        },
        {
            "data_category": "weak_evidence",
            "needed_data": "GWAS lead SNPs / significant SNPs",
            "reason_unresolved": "no exact 3K Rice GWAS lead SNP table identified",
            "suggested_next_step": "manual literature curation with leakage control",
        },
        {
            "data_category": "accession_metadata",
            "needed_data": "curated accession metadata with accession_id fields",
            "reason_unresolved": "RICE_RP / manifest files may contain metadata but require later inventory",
            "suggested_next_step": "inspect downloaded metadata archives without assuming schema",
        },
    ]
    return candidates, skipped, unresolved


def write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    candidates, skipped, unresolved = candidate_rows()
    write_tsv(
        REPORT_DIR / "auto_download_candidates.tsv",
        candidates,
        [
            "candidate_id",
            "data_category",
            "file_role",
            "source",
            "remote_path_or_url",
            "access_method_type",
            "expected_format",
            "priority",
            "local_path",
            "reason_selected",
            "notes",
        ],
    )
    write_tsv(
        REPORT_DIR / "skipped_large_raw_reads.tsv",
        skipped,
        ["remote_path_or_url", "size_bytes", "reason_skipped"],
    )
    write_tsv(
        REPORT_DIR / "unresolved_needed_data.tsv",
        unresolved,
        ["data_category", "needed_data", "reason_unresolved", "suggested_next_step"],
    )
    print(f"selected_candidates={len(candidates)}")
    print(f"skipped_forbidden={len(skipped)}")
    print(f"unresolved_needed={len(unresolved)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
