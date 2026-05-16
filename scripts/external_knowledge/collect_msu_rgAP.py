#!/usr/bin/env python3
"""Collect MSU / Rice Genome Annotation Project files for Phase 7A.

Inputs:
  https://rice.uga.edu/downloads_gad.shtml
  https://rice.uga.edu/download_osa1r7.shtml

Outputs:
  data/raw/external_knowledge/msu_rgAP/
  reports/external_knowledge/msu_rgAP/msu_rgAP_download_log.tsv
  manifest/download_manifest.tsv
  manifest/checksum_table.tsv

Usage:
  python scripts/external_knowledge/collect_msu_rgAP.py
"""

from __future__ import annotations

from external_knowledge_utils import REPO_ROOT, DownloadTarget, collect_targets


BASE = "https://rice.uga.edu"
RAW_DIR = REPO_ROOT / "data/raw/external_knowledge/msu_rgAP"
REPORT_DIR = REPO_ROOT / "reports/external_knowledge/msu_rgAP"
VERSION = "Rice Genome Annotation Project Release 7"


def targets() -> list[DownloadTarget]:
    source_id = "SRC_EXT_MSU_RGAP_001"
    return [
        DownloadTarget(
            "DL_EXT_MSU_RGAP_BATCH_PAGE_001",
            "FILE_EXT_MSU_RGAP_BATCH_PAGE_001",
            "MSU_RGAP",
            source_id,
            "external_gene_annotation",
            "batch_download_page_html",
            f"{BASE}/downloads_gad.shtml",
            RAW_DIR / "downloads_gad.shtml",
            VERSION,
            "MSU RGAP Release 7 / IRGSP-1.0",
            "Batch download page; metadata and fallback provenance",
        ),
        DownloadTarget(
            "DL_EXT_MSU_RGAP_RELEASE7_PAGE_001",
            "FILE_EXT_MSU_RGAP_RELEASE7_PAGE_001",
            "MSU_RGAP",
            source_id,
            "external_gene_annotation",
            "release7_download_page_html",
            f"{BASE}/download_osa1r7.shtml",
            RAW_DIR / "download_osa1r7.shtml",
            VERSION,
            "MSU RGAP Release 7 / IRGSP-1.0",
            "Release 7 download page; file link provenance metadata",
        ),
        DownloadTarget(
            "DL_EXT_MSU_RGAP_ALL_MODELS_GFF3_001",
            "FILE_EXT_MSU_RGAP_ALL_MODELS_GFF3_001",
            "MSU_RGAP",
            source_id,
            "external_gene_annotation",
            "all_models_gff3",
            f"{BASE}/osa1r7_download/osa1_r7.all_models.gff3.gz",
            RAW_DIR / "osa1_r7.all_models.gff3.gz",
            VERSION,
            "MSU RGAP Release 7 / IRGSP-1.0",
            "All gene models GFF3; gene annotation layer candidate",
        ),
        DownloadTarget(
            "DL_EXT_MSU_RGAP_FUNCTIONAL_ANNOTATION_001",
            "FILE_EXT_MSU_RGAP_FUNCTIONAL_ANNOTATION_001",
            "MSU_RGAP",
            source_id,
            "external_functional_annotation",
            "all_models_functional_annotation",
            f"{BASE}/osa1r7_download/osa1_r7.all_models.functional_annotation.txt.gz",
            RAW_DIR / "osa1_r7.all_models.functional_annotation.txt.gz",
            VERSION,
            "MSU RGAP Release 7 / IRGSP-1.0",
            "Functional annotation for all gene models; annotation and explanation layer candidate",
        ),
        DownloadTarget(
            "DL_EXT_MSU_RGAP_LOCUS_BRIEF_001",
            "FILE_EXT_MSU_RGAP_LOCUS_BRIEF_001",
            "MSU_RGAP",
            source_id,
            "external_gene_annotation",
            "locus_brief_info",
            f"{BASE}/osa1r7_download/osa1_r7.locus_brief_info.txt.gz",
            RAW_DIR / "osa1_r7.locus_brief_info.txt.gz",
            VERSION,
            "MSU RGAP Release 7 / IRGSP-1.0",
            "Locus brief information table; gene annotation and ID audit support",
        ),
        DownloadTarget(
            "DL_EXT_MSU_RGAP_GOSLIM_001",
            "FILE_EXT_MSU_RGAP_GOSLIM_001",
            "MSU_RGAP",
            source_id,
            "external_functional_annotation",
            "all_models_goslim",
            f"{BASE}/osa1r7_download/osa1_r7.all_models.GOSlim.txt.gz",
            RAW_DIR / "osa1_r7.all_models.GOSlim.txt.gz",
            VERSION,
            "MSU RGAP Release 7 / IRGSP-1.0",
            "GO Slim annotation; functional annotation layer candidate",
        ),
        DownloadTarget(
            "DL_EXT_MSU_RGAP_LEGACY_INDEX_001",
            "FILE_EXT_MSU_RGAP_LEGACY_INDEX_001",
            "MSU_RGAP",
            source_id,
            "external_gene_annotation",
            "legacy_annotation_index_html",
            f"{BASE}/pub/data/Eukaryotic_Projects/o_sativa/annotation_dbs/",
            RAW_DIR / "legacy_annotation_dbs_index.html",
            VERSION,
            "MSU RGAP Release 7 / legacy",
            "Legacy download index; metadata and manual fallback context",
        ),
    ]


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rows = collect_targets(targets(), REPORT_DIR, "msu_rgAP_download_log.tsv")
    downloaded = sum(1 for row in rows if row["download_status"] == "downloaded")
    failed = sum(1 for row in rows if row["download_status"] == "failed")
    skipped = sum(1 for row in rows if row["download_status"] == "skipped")
    print(f"msu_rgAP_downloaded={downloaded}")
    print(f"msu_rgAP_failed={failed}")
    print(f"msu_rgAP_skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
