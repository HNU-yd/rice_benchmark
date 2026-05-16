#!/usr/bin/env python3
"""Collect funRiceGenes public tables and metadata for Phase 7A.

Inputs:
  https://funricegenes.github.io/
  https://venyao.xyz/funRiceGenes/

Outputs:
  data/raw/external_knowledge/funricegenes/
  reports/external_knowledge/funricegenes/funricegenes_download_log.tsv
  manifest/download_manifest.tsv
  manifest/checksum_table.tsv

Usage:
  python scripts/external_knowledge/collect_funricegenes.py
"""

from __future__ import annotations

from external_knowledge_utils import REPO_ROOT, DownloadTarget, collect_targets


RAW_DIR = REPO_ROOT / "data/raw/external_knowledge/funricegenes"
REPORT_DIR = REPO_ROOT / "reports/external_knowledge/funricegenes"
VERSION = "funRiceGenes public static site accessed 2026-05-16"


def targets() -> list[DownloadTarget]:
    source_id = "SRC_EXT_FUNRICEGENES_001"
    return [
        DownloadTarget(
            "DL_EXT_FUNRICEGENES_HOME_001",
            "FILE_EXT_FUNRICEGENES_HOME_001",
            "funRiceGenes",
            source_id,
            "external_known_gene_evidence",
            "static_home_page_html",
            "https://funricegenes.github.io/",
            RAW_DIR / "funricegenes_home.html",
            VERSION,
            "mixed_or_to_be_confirmed",
            "Static home page with download links and citation metadata",
        ),
        DownloadTarget(
            "DL_EXT_FUNRICEGENES_SHINY_HOME_001",
            "FILE_EXT_FUNRICEGENES_SHINY_HOME_001",
            "funRiceGenes",
            source_id,
            "external_known_gene_evidence",
            "shiny_page_html",
            "https://venyao.xyz/funRiceGenes/",
            RAW_DIR / "funricegenes_shiny_home.html",
            VERSION,
            "mixed_or_to_be_confirmed",
            "Interactive Shiny page saved as metadata and manual-download fallback context",
        ),
        DownloadTarget(
            "DL_EXT_FUNRICEGENES_GENEINFO_001",
            "FILE_EXT_FUNRICEGENES_GENEINFO_001",
            "funRiceGenes",
            source_id,
            "external_known_gene_evidence",
            "cloned_gene_table",
            "https://funricegenes.github.io/geneInfo.table.txt",
            RAW_DIR / "geneInfo.table.txt",
            VERSION,
            "mixed_or_to_be_confirmed",
            "Functionally characterized/cloned rice gene table; known gene evidence layer candidate",
        ),
        DownloadTarget(
            "DL_EXT_FUNRICEGENES_FAMINFO_001",
            "FILE_EXT_FUNRICEGENES_FAMINFO_001",
            "funRiceGenes",
            source_id,
            "external_gene_id_mapping",
            "gene_family_member_table",
            "https://funricegenes.github.io/famInfo.table.txt",
            RAW_DIR / "famInfo.table.txt",
            VERSION,
            "mixed_or_to_be_confirmed",
            "Gene family members table; gene ID mapping and candidate gene explanation support",
        ),
        DownloadTarget(
            "DL_EXT_FUNRICEGENES_KEYWORD_001",
            "FILE_EXT_FUNRICEGENES_KEYWORD_001",
            "funRiceGenes",
            source_id,
            "external_functional_annotation",
            "gene_keyword_table",
            "https://funricegenes.github.io/geneKeyword.table.txt",
            RAW_DIR / "geneKeyword.table.txt",
            VERSION,
            "mixed_or_to_be_confirmed",
            "Gene-keyword table; functional annotation and candidate explanation layer candidate",
        ),
        DownloadTarget(
            "DL_EXT_FUNRICEGENES_REFERENCE_001",
            "FILE_EXT_FUNRICEGENES_REFERENCE_001",
            "funRiceGenes",
            source_id,
            "external_known_gene_evidence",
            "literature_reference_table",
            "https://funricegenes.github.io/reference.table.txt",
            RAW_DIR / "reference.table.txt",
            VERSION,
            "mixed_or_to_be_confirmed",
            "Literature reference table; evidence provenance support",
        ),
        DownloadTarget(
            "DL_EXT_FUNRICEGENES_NETWORK_PDF_001",
            "FILE_EXT_FUNRICEGENES_NETWORK_PDF_001",
            "funRiceGenes",
            source_id,
            "external_functional_annotation",
            "interaction_network_pdf",
            "https://funricegenes.github.io/net.pdf",
            RAW_DIR / "net.pdf",
            VERSION,
            "mixed_or_to_be_confirmed",
            "Interaction network PDF; metadata/explanation support only in 07A",
        ),
        DownloadTarget(
            "DL_EXT_FUNRICEGENES_HELP_PDF_001",
            "FILE_EXT_FUNRICEGENES_HELP_PDF_001",
            "funRiceGenes",
            source_id,
            "external_known_gene_evidence",
            "help_manual_pdf",
            "https://funricegenes.github.io/help.pdf",
            RAW_DIR / "help.pdf",
            VERSION,
            "mixed_or_to_be_confirmed",
            "Help manual; metadata and schema interpretation support",
        ),
    ]


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rows = collect_targets(targets(), REPORT_DIR, "funricegenes_download_log.tsv")
    downloaded = sum(1 for row in rows if row["download_status"] == "downloaded")
    failed = sum(1 for row in rows if row["download_status"] == "failed")
    skipped = sum(1 for row in rows if row["download_status"] == "skipped")
    print(f"funricegenes_downloaded={downloaded}")
    print(f"funricegenes_failed={failed}")
    print(f"funricegenes_skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
