#!/usr/bin/env python3
"""Collect RAP-DB annotation and known-gene files for Phase 7A.

Inputs:
  External HTTPS endpoints under https://rapdb.dna.naro.go.jp/

Outputs:
  data/raw/external_knowledge/rapdb/
  reports/external_knowledge/rapdb/rapdb_download_log.tsv
  manifest/download_manifest.tsv
  manifest/checksum_table.tsv

Usage:
  python scripts/external_knowledge/collect_rapdb.py
"""

from __future__ import annotations

from pathlib import Path

from external_knowledge_utils import REPO_ROOT, DownloadTarget, collect_targets


BASE = "https://rapdb.dna.naro.go.jp"
VERSION = "RAP-DB IRGSP-1.0 2026-02-05"
RAW_DIR = REPO_ROOT / "data/raw/external_knowledge/rapdb"
REPORT_DIR = REPO_ROOT / "reports/external_knowledge/rapdb"


def targets() -> list[DownloadTarget]:
    source_id = "SRC_EXT_RAPDB_001"
    return [
        DownloadTarget(
            "DL_EXT_RAPDB_DOWNLOAD_PAGE_001",
            "FILE_EXT_RAPDB_DOWNLOAD_PAGE_001",
            "RAP-DB",
            source_id,
            "external_gene_annotation",
            "download_page_html",
            f"{BASE}/download/irgsp1.html",
            RAW_DIR / "irgsp1_download_page.html",
            VERSION,
            "IRGSP-1.0",
            "RAP-DB IRGSP-1.0 download page; link provenance metadata",
        ),
        DownloadTarget(
            "DL_EXT_RAPDB_DOWNLOAD_JS_001",
            "FILE_EXT_RAPDB_DOWNLOAD_JS_001",
            "RAP-DB",
            source_id,
            "external_gene_annotation",
            "download_page_javascript",
            f"{BASE}/assets/download.99861702.js",
            RAW_DIR / "download.99861702.js",
            VERSION,
            "IRGSP-1.0",
            "RAP-DB download page JavaScript containing versioned file links",
        ),
        DownloadTarget(
            "DL_EXT_RAPDB_REP_ANNOT_20260205_001",
            "FILE_EXT_RAPDB_REP_ANNOT_20260205_001",
            "RAP-DB",
            source_id,
            "external_gene_annotation",
            "representative_annotation_tsv",
            f"{BASE}/download/archive/irgsp1/IRGSP-1.0_representative_annotation_2026-02-05.tsv.gz",
            RAW_DIR / "IRGSP-1.0_representative_annotation_2026-02-05.tsv.gz",
            VERSION,
            "IRGSP-1.0",
            "Representative gene annotation table; annotation layer candidate",
        ),
        DownloadTarget(
            "DL_EXT_RAPDB_REP_EXON_GTF_20260205_001",
            "FILE_EXT_RAPDB_REP_EXON_GTF_20260205_001",
            "RAP-DB",
            source_id,
            "external_gene_annotation",
            "representative_transcript_exon_gtf",
            f"{BASE}/download/archive/irgsp1/IRGSP-1.0_representative_transcript_exon_2026-02-05.gtf.gz",
            RAW_DIR / "IRGSP-1.0_representative_transcript_exon_2026-02-05.gtf.gz",
            VERSION,
            "IRGSP-1.0",
            "Representative transcript exon GTF; coordinate annotation layer candidate",
        ),
        DownloadTarget(
            "DL_EXT_RAPDB_RAP_MSU_20260205_001",
            "FILE_EXT_RAPDB_RAP_MSU_20260205_001",
            "RAP-DB",
            source_id,
            "external_gene_id_mapping",
            "rap_msu_id_mapping",
            f"{BASE}/download/archive/RAP-MSU_2026-02-05.txt.gz",
            RAW_DIR / "RAP-MSU_2026-02-05.txt.gz",
            VERSION,
            "IRGSP-1.0 / MSU RGAP",
            "RAP-DB to MSU LOC_Os ID mapping table; gene ID mapping layer candidate",
        ),
        DownloadTarget(
            "DL_EXT_RAPDB_TRANSCRIPT_EVIDENCE_20120411_001",
            "FILE_EXT_RAPDB_TRANSCRIPT_EVIDENCE_20120411_001",
            "RAP-DB",
            source_id,
            "external_gene_id_mapping",
            "transcript_evidence_accession_mapping",
            f"{BASE}/download/archive/IRGSP-1.0_transcript-evidence_2012-04-11.txt.gz",
            RAW_DIR / "IRGSP-1.0_transcript-evidence_2012-04-11.txt.gz",
            "2012-04-11",
            "IRGSP-1.0",
            "Transcript evidence accession/species mapping; metadata and ID audit support",
        ),
        DownloadTarget(
            "DL_EXT_RAPDB_CURATED_PAGE_001",
            "FILE_EXT_RAPDB_CURATED_PAGE_001",
            "RAP-DB",
            source_id,
            "external_known_gene_evidence",
            "curated_genes_page_html",
            f"{BASE}/curated_genes/curated_gene_list.html",
            RAW_DIR / "curated_gene_list.html",
            VERSION,
            "IRGSP-1.0",
            "RAP-DB curated genes page; known gene evidence provenance",
        ),
        DownloadTarget(
            "DL_EXT_RAPDB_CURATED_JSON_001",
            "FILE_EXT_RAPDB_CURATED_JSON_001",
            "RAP-DB",
            source_id,
            "external_known_gene_evidence",
            "curated_genes_json",
            f"{BASE}/curated_genes/curated_genes.json",
            RAW_DIR / "curated_genes.json",
            VERSION,
            "IRGSP-1.0",
            "RAP-DB curated genes JSON; known gene evidence layer candidate",
        ),
        DownloadTarget(
            "DL_EXT_RAPDB_AGRI_PAGE_001",
            "FILE_EXT_RAPDB_AGRI_PAGE_001",
            "RAP-DB",
            source_id,
            "external_known_gene_evidence",
            "agronomically_important_genes_page_html",
            f"{BASE}/agri_genes/agri_gene_list.html",
            RAW_DIR / "agri_gene_list.html",
            VERSION,
            "IRGSP-1.0",
            "RAP-DB agronomically important genes page; known gene evidence provenance",
        ),
        DownloadTarget(
            "DL_EXT_RAPDB_AGRI_JSON_001",
            "FILE_EXT_RAPDB_AGRI_JSON_001",
            "RAP-DB",
            source_id,
            "external_known_gene_evidence",
            "agronomically_important_genes_json",
            f"{BASE}/agri_genes/agri_genes.json",
            RAW_DIR / "agri_genes.json",
            VERSION,
            "IRGSP-1.0",
            "RAP-DB agronomically important genes JSON; known gene evidence layer candidate",
        ),
    ]


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rows = collect_targets(targets(), REPORT_DIR, "rapdb_download_log.tsv")
    downloaded = sum(1 for row in rows if row["download_status"] == "downloaded")
    failed = sum(1 for row in rows if row["download_status"] == "failed")
    skipped = sum(1 for row in rows if row["download_status"] == "skipped")
    print(f"rapdb_downloaded={downloaded}")
    print(f"rapdb_failed={failed}")
    print(f"rapdb_skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
