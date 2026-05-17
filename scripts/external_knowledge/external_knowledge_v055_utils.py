#!/usr/bin/env python3
"""Utilities for the v0.5.5 external knowledge integration layer."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_BUILD = "IRGSP-1.0 / GCF_001433935.1"

DEFAULT_INTERIM_ROOT = REPO_ROOT / "data/interim/external_knowledge_v055"
DEFAULT_REPORT_ROOT = REPO_ROOT / "reports/external_knowledge_v055"

GENE_ANNOTATION_FIELDS = [
    "gene_id",
    "gene_source",
    "chrom",
    "start",
    "end",
    "strand",
    "gene_symbol",
    "gene_name",
    "gene_type",
    "description",
    "source_database",
    "source_version",
    "reference_build",
    "coordinate_confidence",
    "notes",
]

GENE_ID_MAPPING_FIELDS = [
    "mapping_id",
    "source_gene_id",
    "source_database",
    "target_gene_id",
    "target_database",
    "gene_symbol",
    "mapping_type",
    "mapping_confidence",
    "mapping_method",
    "is_ambiguous",
    "n_candidates",
    "notes",
]

KNOWN_GENE_EVIDENCE_FIELDS = [
    "evidence_id",
    "trait_id_or_name",
    "gene_id",
    "gene_symbol",
    "evidence_source",
    "source_database",
    "source_record_id",
    "evidence_type",
    "support_level",
    "species",
    "chrom",
    "start",
    "end",
    "reference_build",
    "coordinate_mapping_status",
    "allowed_usage",
    "evidence_split_candidate",
    "notes",
]

TRAIT_GENE_EVIDENCE_FIELDS = [
    "trait_gene_evidence_id",
    "trait_id",
    "trait_name",
    "trait_name_normalized",
    "gene_id",
    "gene_symbol",
    "evidence_id",
    "evidence_source",
    "support_level",
    "trait_mapping_confidence",
    "gene_mapping_confidence",
    "allowed_usage",
    "notes",
]

QTL_INTERVAL_EVIDENCE_FIELDS = [
    "qtl_evidence_id",
    "trait_id_or_name",
    "trait_name_normalized",
    "chrom",
    "start",
    "end",
    "interval_length",
    "source_database",
    "source_record_id",
    "evidence_type",
    "coordinate_mapping_status",
    "reference_build",
    "linked_gene_id",
    "linked_gene_symbol",
    "allowed_usage",
    "notes",
]

EVIDENCE_COORDINATE_MAPPING_FIELDS = [
    "evidence_id",
    "original_source",
    "original_reference_build",
    "original_chrom",
    "original_start",
    "original_end",
    "mapped_reference_build",
    "mapped_chrom",
    "mapped_start",
    "mapped_end",
    "mapping_method",
    "mapping_confidence",
    "mapping_status",
    "failure_reason",
    "notes",
]

EVIDENCE_SOURCE_MANIFEST_FIELDS = [
    "source_name",
    "source_version",
    "raw_file_path",
    "processed_table",
    "checksum",
    "download_or_access_date",
    "source_type",
    "allowed_usage",
    "license_or_terms_note",
    "processing_script",
    "notes",
]

MANUAL_REVIEW_FIELDS = [
    "review_id",
    "record_type",
    "source_database",
    "source_record_id",
    "raw_trait_name",
    "raw_gene_id",
    "raw_gene_symbol",
    "candidate_mappings",
    "ambiguity_reason",
    "recommended_action",
    "priority",
    "notes",
]

VALIDATION_FIELDS = [
    "check_name",
    "status",
    "n_records",
    "n_failed",
    "details",
    "blocking_issue",
    "notes",
]

SUMMARY_FIELDS = [
    "metric",
    "value",
    "notes",
]

REFSEQ_TO_CHROM = {
    "NC_029256.1": "1",
    "NC_029257.1": "2",
    "NC_029258.1": "3",
    "NC_029259.1": "4",
    "NC_029260.1": "5",
    "NC_029261.1": "6",
    "NC_029262.1": "7",
    "NC_029263.1": "8",
    "NC_029264.1": "9",
    "NC_029265.1": "10",
    "NC_029266.1": "11",
    "NC_029267.1": "12",
}

ALLOWED_USAGE_VALUES = {
    "evaluation_reference",
    "explanation",
    "case_study",
    "development_evidence_candidate",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def existing(path: Path) -> bool:
    return path.exists() and path.is_file()


def text_open(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="")
    return path.open("r", encoding="utf-8", errors="replace", newline="")


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not existing(path):
        return []
    with text_open(path) as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not existing(path):
        return []
    with text_open(path) as handle:
        return list(csv.DictReader(handle))


def write_tsv(path: Path, rows: Iterable[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            normalized = {}
            for field in fields:
                value = row.get(field)
                if value is None or value == "":
                    normalized[field] = "NA"
                else:
                    normalized[field] = value
            writer.writerow(normalized)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean(value: object) -> str:
    return str(value or "").strip()


def is_missing_value(value: object) -> bool:
    text = clean(value)
    return text == "" or text.lower() in {"na", "n/a", "nan", "none", "null"}


def compact(value: object, limit: int = 300) -> str:
    text = re.sub(r"\s+", " ", clean(value))
    return text if len(text) <= limit else text[: limit - 15] + "...[truncated]"


def normalize_chrom(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    if text in REFSEQ_TO_CHROM:
        return REFSEQ_TO_CHROM[text]
    lowered = text.lower()
    lowered = lowered.replace("chromosome", "chr")
    match = re.search(r"(?:chr)?0*([1-9]|1[0-2])$", lowered)
    if match:
        return match.group(1)
    if lowered in {"m", "mt", "mitochondrion", "mitochondrial"}:
        return "Mt"
    return text


def parse_int(value: object) -> int | None:
    text = clean(value).replace(",", "")
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def valid_interval(chrom: str, start: object, end: object) -> bool:
    left = parse_int(start)
    right = parse_int(end)
    return bool(chrom) and left is not None and right is not None and left >= 1 and right >= left


def parse_gff_attributes(text: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for item in clean(text).split(";"):
        if not item:
            continue
        if "=" in item:
            key, value = item.split("=", 1)
        elif " " in item:
            key, value = item.split(" ", 1)
            value = value.strip('"')
        else:
            continue
        attrs[key.strip()] = value.strip().strip('"')
    return attrs


def split_multi(value: object) -> list[str]:
    text = clean(value)
    if not text or text.lower() in {"none", "na", "n/a", "-"}:
        return []
    parts = re.split(r"[;,|]+", text)
    out: list[str] = []
    for part in parts:
        part = clean(part)
        if part and part not in out:
            out.append(part)
    return out


def strip_msu_transcript(value: str) -> str:
    text = clean(value)
    return re.sub(r"\.\d+$", "", text)


def first_nonempty(*values: object) -> str:
    for value in values:
        text = clean(value)
        if text:
            return text
    return ""


def normalize_trait_name(value: object) -> str:
    text = clean(value).lower()
    text = re.sub(r"to:\d+\s*-\s*", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--interim-root", type=Path, default=DEFAULT_INTERIM_ROOT)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    return parser.parse_args()


def ensure_output_dirs(interim_root: Path, report_root: Path) -> None:
    for subdir in ("annotation", "evidence", "mapping", "qc_diagnostics"):
        (interim_root / subdir).mkdir(parents=True, exist_ok=True)
    report_root.mkdir(parents=True, exist_ok=True)


def rap_annotation_meta(repo_root: Path) -> dict[str, dict[str, str]]:
    path = repo_root / "data/raw/external_knowledge/rapdb/IRGSP-1.0_representative_annotation_2026-02-05.tsv.gz"
    rows = read_tsv(path)
    meta: dict[str, dict[str, str]] = {}
    for row in rows:
        locus = clean(row.get("Locus_ID"))
        if not locus:
            continue
        if locus not in meta:
            meta[locus] = {
                "description": clean(row.get("Description")),
                "gene_symbol": first_nonempty(
                    row.get("RAP-DB Gene Symbol Synonym(s)"),
                    row.get("CGSNL Gene Symbol"),
                    row.get("Oryzabase Gene Symbol Synonym(s)"),
                ),
                "gene_name": first_nonempty(
                    row.get("RAP-DB Gene Name Synonym(s)"),
                    row.get("CGSNL Gene Name"),
                    row.get("Oryzabase Gene Name Synonym(s)"),
                ),
                "oryzabase_trait_gene_id": clean(row.get("Oryzabase Trait Gene ID")),
            }
    return meta


def build_gene_annotation_rows(repo_root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    rap_meta = rap_annotation_meta(repo_root)

    rap_gtf = repo_root / "data/raw/external_knowledge/rapdb/IRGSP-1.0_representative_transcript_exon_2026-02-05.gtf.gz"
    gene_coords: dict[str, dict[str, object]] = {}
    if existing(rap_gtf):
        with text_open(rap_gtf) as handle:
            for line in handle:
                if not line.strip() or line.startswith("#"):
                    continue
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 9 or parts[2] != "transcript":
                    continue
                attrs = parse_gff_attributes(parts[8])
                gene_id = clean(attrs.get("gene_id"))
                if not gene_id:
                    continue
                start = parse_int(parts[3])
                end = parse_int(parts[4])
                chrom = normalize_chrom(parts[0])
                if start is None or end is None:
                    continue
                current = gene_coords.setdefault(
                    gene_id,
                    {"chrom": chrom, "start": start, "end": end, "strand": parts[6]},
                )
                current["start"] = min(int(current["start"]), start)
                current["end"] = max(int(current["end"]), end)
        for gene_id, coord in sorted(gene_coords.items()):
            meta = rap_meta.get(gene_id, {})
            key = (gene_id, "RAP-DB")
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "gene_id": gene_id,
                    "gene_source": "RAP-DB",
                    "chrom": coord["chrom"],
                    "start": coord["start"],
                    "end": coord["end"],
                    "strand": coord["strand"],
                    "gene_symbol": meta.get("gene_symbol", ""),
                    "gene_name": meta.get("gene_name", ""),
                    "gene_type": "representative_transcript_locus",
                    "description": meta.get("description", ""),
                    "source_database": "RAP-DB",
                    "source_version": "IRGSP-1.0 representative annotation 2026-02-05",
                    "reference_build": REFERENCE_BUILD,
                    "coordinate_confidence": "source_reported_irsgp1_high",
                    "notes": "RAP-DB GTF transcript coordinates; annotation is not a training label",
                }
            )

    msu_locus = repo_root / "data/raw/external_knowledge/msu_rgAP/osa1_r7.locus_brief_info.txt.gz"
    for row in read_tsv(msu_locus):
        if clean(row.get("is_representative")).upper() not in {"Y", "YES", "TRUE", "1"}:
            continue
        gene_id = clean(row.get("locus"))
        chrom = normalize_chrom(row.get("chr"))
        start = parse_int(row.get("start"))
        end = parse_int(row.get("stop"))
        if not gene_id or start is None or end is None:
            continue
        key = (gene_id, "MSU_RGAP")
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "gene_id": gene_id,
                "gene_source": "MSU_RGAP",
                "chrom": chrom,
                "start": start,
                "end": end,
                "strand": clean(row.get("ori")),
                "gene_symbol": "",
                "gene_name": "",
                "gene_type": "representative_locus",
                "description": clean(row.get("annotation")),
                "source_database": "MSU_RGAP",
                "source_version": "Rice Genome Annotation Project Release 7",
                "reference_build": "MSU RGAP Release 7 / IRGSP-1.0",
                "coordinate_confidence": "source_reported_irsgp1_high",
                "notes": "MSU representative locus; annotation is not a training label",
            }
        )

    ncbi_gff = repo_root / "data/raw/reference/GCF_001433935.1_IRGSP-1.0_genomic.gff.gz"
    if existing(ncbi_gff):
        with text_open(ncbi_gff) as handle:
            for line in handle:
                if not line.strip() or line.startswith("#"):
                    continue
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 9 or parts[2] != "gene":
                    continue
                attrs = parse_gff_attributes(parts[8])
                gene_id = first_nonempty(attrs.get("gene"), attrs.get("Name"), attrs.get("ID"))
                if not gene_id:
                    continue
                key = (gene_id, "NCBI_RefSeq")
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        "gene_id": gene_id,
                        "gene_source": "NCBI_RefSeq",
                        "chrom": normalize_chrom(parts[0]),
                        "start": parts[3],
                        "end": parts[4],
                        "strand": parts[6],
                        "gene_symbol": first_nonempty(attrs.get("gene"), attrs.get("Name")),
                        "gene_name": first_nonempty(attrs.get("description"), attrs.get("product")),
                        "gene_type": first_nonempty(attrs.get("gene_biotype"), attrs.get("gbkey")),
                        "description": first_nonempty(attrs.get("description"), attrs.get("product"), attrs.get("Note")),
                        "source_database": "NCBI_RefSeq",
                        "source_version": "NCBI Oryza sativa Japonica Group Annotation Release 102",
                        "reference_build": REFERENCE_BUILD,
                        "coordinate_confidence": "source_reported_refseq_high",
                        "notes": "Reference GFF gene feature; annotation is not a training label",
                    }
                )
    return rows


def load_annotation_index(interim_root: Path) -> dict[str, dict[str, str]]:
    rows = read_tsv(interim_root / "annotation/gene_annotation_table.tsv")
    index: dict[str, dict[str, str]] = {}
    for row in rows:
        gene_id = clean(row.get("gene_id"))
        if not gene_id:
            continue
        index.setdefault(gene_id, row)
        index.setdefault(strip_msu_transcript(gene_id), row)
    return index


def add_mapping(
    rows: list[dict[str, str]],
    source_gene_id: str,
    source_database: str,
    target_gene_id: str,
    target_database: str,
    gene_symbol: str,
    mapping_type: str,
    mapping_confidence: str,
    mapping_method: str,
    n_candidates: int,
    notes: str,
) -> None:
    source_gene_id = clean(source_gene_id)
    target_gene_id = clean(target_gene_id)
    if not source_gene_id and not gene_symbol:
        return
    is_ambiguous = "true" if mapping_type in {"manual_review_required", "unmapped"} or n_candidates > 1 else "false"
    rows.append(
        {
            "mapping_id": f"MAP_{len(rows) + 1:08d}",
            "source_gene_id": source_gene_id,
            "source_database": source_database,
            "target_gene_id": target_gene_id,
            "target_database": target_database,
            "gene_symbol": clean(gene_symbol),
            "mapping_type": mapping_type,
            "mapping_confidence": mapping_confidence,
            "mapping_method": mapping_method,
            "is_ambiguous": is_ambiguous,
            "n_candidates": str(n_candidates),
            "notes": notes,
        }
    )


def unique_mapping_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str, str, str]] = set()
    unique: list[dict[str, str]] = []
    for row in rows:
        key = (
            row["source_gene_id"],
            row["source_database"],
            row["target_gene_id"],
            row["target_database"],
            row["mapping_type"],
        )
        if key in seen:
            continue
        seen.add(key)
        row = dict(row)
        row["mapping_id"] = f"MAP_{len(unique) + 1:08d}"
        unique.append(row)
    return unique


def build_gene_id_mapping_rows(repo_root: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []

    rap_msu = repo_root / "data/raw/external_knowledge/rapdb/RAP-MSU_2026-02-05.txt.gz"
    if existing(rap_msu):
        with text_open(rap_msu) as handle:
            for line in handle:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 2:
                    continue
                rap_id = clean(parts[0])
                raw_targets = [strip_msu_transcript(item) for item in split_multi(parts[1]) if item.lower() != "none"]
                targets = sorted(set(raw_targets))
                if not targets:
                    add_mapping(rows, rap_id, "RAP-DB", "", "MSU_RGAP", "", "unmapped", "low", "RAP-MSU table reports None", 0, "manual review required before use")
                elif len(targets) == 1:
                    add_mapping(rows, rap_id, "RAP-DB", targets[0], "MSU_RGAP", "", "exact_id_match", "high", "RAP-MSU official mapping", 1, "")
                else:
                    add_mapping(rows, rap_id, "RAP-DB", ";".join(targets), "MSU_RGAP", "", "manual_review_required", "medium", "RAP-MSU official mapping has multiple target loci", len(targets), "ambiguous multi-target mapping")

    for file_name, source_name in (("geneInfo.table.txt", "funRiceGenes_geneInfo"), ("famInfo.table.txt", "funRiceGenes_famInfo")):
        for row in read_tsv(repo_root / f"data/raw/external_knowledge/funricegenes/{file_name}"):
            rap = clean(row.get("RAPdb"))
            msu = strip_msu_transcript(row.get("MSU", ""))
            symbol = clean(row.get("Symbol"))
            if rap and msu:
                add_mapping(rows, rap, source_name, msu, "MSU_RGAP", symbol, "exact_id_match", "high", f"{file_name} RAPdb-MSU columns", 1, "")
            for alias in split_multi(symbol):
                if rap:
                    add_mapping(rows, alias, source_name, rap, "RAP-DB", alias, "alias_match", "medium", f"{file_name} Symbol-RAPdb columns", 1, "symbol alias from funRiceGenes")
                if msu:
                    add_mapping(rows, alias, source_name, msu, "MSU_RGAP", alias, "alias_match", "medium", f"{file_name} Symbol-MSU columns", 1, "symbol alias from funRiceGenes")

    for row in read_tsv(repo_root / "data/raw/evidence/known_genes/oryzabase/OryzabaseGeneListEn.tsv"):
        symbol = clean(row.get("CGSNL Gene Symbol")).strip("[]")
        rap_ids = split_multi(row.get("RAP ID"))
        msu_ids = [strip_msu_transcript(item) for item in split_multi(row.get("MSU ID"))]
        if rap_ids and msu_ids:
            for rap in rap_ids:
                for msu in sorted(set(msu_ids)):
                    add_mapping(rows, rap, "Oryzabase", msu, "MSU_RGAP", symbol, "exact_id_match", "medium", "Oryzabase RAP ID and MSU ID columns", len(set(msu_ids)), "Oryzabase trait gene table mapping")
        elif symbol and not rap_ids and not msu_ids:
            add_mapping(rows, symbol, "Oryzabase", "", "", symbol, "unmapped", "low", "Oryzabase symbol without RAP/MSU ID", 0, "manual review required")
        for rap in rap_ids:
            if symbol:
                add_mapping(rows, symbol, "Oryzabase", rap, "RAP-DB", symbol, "alias_match", "medium", "Oryzabase symbol and RAP ID columns", len(rap_ids), "")
        for msu in msu_ids:
            if symbol:
                add_mapping(rows, symbol, "Oryzabase", msu, "MSU_RGAP", symbol, "alias_match", "medium", "Oryzabase symbol and MSU ID columns", len(msu_ids), "")

    qtaro_path = repo_root / "data/interim/evidence/qtaro/qtaro_sjis.csv.utf8"
    if not existing(qtaro_path):
        qtaro_path = repo_root / "data/interim/evidence/qtaro/qtaro_sjis.csv"
    for row in read_csv(qtaro_path):
        qtl_gene = clean(row.get("QTL/Gene"))
        if qtl_gene:
            add_mapping(rows, qtl_gene, "Q-TARO", "", "", qtl_gene, "manual_review_required", "low", "Q-TARO QTL/Gene field is not a stable gene ID", 0, "QTL names and gene symbols are mixed")

    unique = unique_mapping_rows(rows)
    review_rows = manual_review_from_mapping(unique)
    return unique, review_rows


def manual_review_from_mapping(mapping_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    review_rows: list[dict[str, str]] = []
    for row in mapping_rows:
        if row.get("is_ambiguous") != "true":
            continue
        review_rows.append(
            {
                "review_id": f"MR_{len(review_rows) + 1:08d}",
                "record_type": "gene_id_mapping",
                "source_database": row.get("source_database", ""),
                "source_record_id": row.get("mapping_id", ""),
                "raw_trait_name": "",
                "raw_gene_id": row.get("source_gene_id", ""),
                "raw_gene_symbol": row.get("gene_symbol", ""),
                "candidate_mappings": row.get("target_gene_id", ""),
                "ambiguity_reason": row.get("notes", "") or row.get("mapping_type", ""),
                "recommended_action": "manual_review_before_evaluation_use",
                "priority": "P1" if row.get("mapping_type") == "manual_review_required" else "P2",
                "notes": "ambiguous or unmapped gene ID mapping",
            }
        )
    return review_rows


def lookup_gene_coord(annotation_index: dict[str, dict[str, str]], *gene_ids: object) -> dict[str, str]:
    for gene_id in gene_ids:
        text = clean(gene_id)
        if not text:
            continue
        for item in [text, strip_msu_transcript(text)]:
            if item in annotation_index:
                return annotation_index[item]
    return {}


def evidence_row(
    rows: list[dict[str, str]],
    trait: str,
    gene_id: str,
    gene_symbol: str,
    evidence_source: str,
    source_database: str,
    source_record_id: str,
    evidence_type: str,
    support_level: str,
    coord: dict[str, str],
    allowed_usage: str,
    split_candidate: str,
    notes: str,
) -> None:
    status = "mapped_high_confidence" if valid_interval(coord.get("chrom", ""), coord.get("start", ""), coord.get("end", "")) else "gene_level_only"
    rows.append(
        {
            "evidence_id": f"KGE_{len(rows) + 1:08d}",
            "trait_id_or_name": clean(trait),
            "gene_id": clean(gene_id),
            "gene_symbol": clean(gene_symbol),
            "evidence_source": evidence_source,
            "source_database": source_database,
            "source_record_id": clean(source_record_id),
            "evidence_type": evidence_type,
            "support_level": support_level,
            "species": "Oryza sativa",
            "chrom": coord.get("chrom", ""),
            "start": coord.get("start", ""),
            "end": coord.get("end", ""),
            "reference_build": coord.get("reference_build", REFERENCE_BUILD) if coord else REFERENCE_BUILD,
            "coordinate_mapping_status": status,
            "allowed_usage": allowed_usage,
            "evidence_split_candidate": split_candidate,
            "notes": notes,
        }
    )


def build_known_gene_evidence_rows(repo_root: Path, interim_root: Path) -> list[dict[str, str]]:
    annotation_index = load_annotation_index(interim_root)
    rows: list[dict[str, str]] = []

    for file_name, database, evidence_type, support_level in [
        ("curated_genes.json", "RAP-DB_curated_genes", "known_trait_gene", "high_confidence"),
        ("agri_genes.json", "RAP-DB_agri_genes", "database_trait_gene", "medium_confidence"),
    ]:
        path = repo_root / f"data/raw/external_knowledge/rapdb/{file_name}"
        if not existing(path):
            continue
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        for item in data:
            gene_id = clean(item.get("locus"))
            coord = {
                "chrom": normalize_chrom(item.get("seqid")),
                "start": clean(item.get("start")),
                "end": clean(item.get("end")),
                "reference_build": REFERENCE_BUILD,
            }
            trait_terms = []
            if clean(item.get("traits")):
                trait_terms.extend(split_multi(item.get("traits")))
            for term in item.get("to") or []:
                trait_terms.append(clean(term))
            trait_text = ";".join([term for term in trait_terms if term]) or "unspecified_trait"
            references = item.get("references") or {}
            evidence_row(
                rows,
                trait_text,
                gene_id,
                clean(item.get("gene_symbols")),
                "RAP-DB JSON",
                database,
                gene_id,
                evidence_type,
                support_level,
                coord,
                "development_evidence_candidate",
                "development",
                f"references={len(references)}; external knowledge is not a training label",
            )

    for row in read_tsv(repo_root / "data/raw/external_knowledge/funricegenes/geneInfo.table.txt"):
        rap = clean(row.get("RAPdb"))
        msu = strip_msu_transcript(row.get("MSU", ""))
        symbol = clean(row.get("Symbol"))
        coord = lookup_gene_coord(annotation_index, rap, msu)
        evidence_row(
            rows,
            "unspecified_trait",
            first_nonempty(rap, msu, symbol),
            symbol,
            "funRiceGenes geneInfo",
            "funRiceGenes",
            first_nonempty(rap, msu, symbol),
            "known_trait_gene",
            "high_confidence",
            coord,
            "explanation",
            "broader_evidence_pool",
            "funRiceGenes geneInfo lacks explicit trait field; use for candidate gene explanation only unless trait linkage is added",
        )

    for row_index, row in enumerate(read_tsv(repo_root / "data/raw/external_knowledge/funricegenes/geneKeyword.table.txt"), start=1):
        rap = clean(row.get("RAPdb"))
        msu = strip_msu_transcript(row.get("MSU", ""))
        symbol = clean(row.get("Symbol"))
        coord = lookup_gene_coord(annotation_index, rap, msu)
        evidence_row(
            rows,
            row.get("Keyword", ""),
            first_nonempty(rap, msu, symbol),
            symbol,
            "funRiceGenes geneKeyword",
            "funRiceGenes",
            f"geneKeyword:{row_index}",
            "database_trait_gene",
            "weak",
            coord,
            "development_evidence_candidate",
            "development",
            f"title={compact(row.get('Title'), 180)}; evidence text retained in raw file; not a training label",
        )

    for row in read_tsv(repo_root / "data/raw/evidence/known_genes/oryzabase/OryzabaseGeneListEn.tsv"):
        rap = first_nonempty(*split_multi(row.get("RAP ID")))
        msu = first_nonempty(*[strip_msu_transcript(item) for item in split_multi(row.get("MSU ID"))])
        symbol = clean(row.get("CGSNL Gene Symbol")).strip("[]")
        coord = lookup_gene_coord(annotation_index, rap, msu)
        evidence_row(
            rows,
            first_nonempty(row.get("Trait Class"), row.get("Trait Ontology"), row.get("Explanation")),
            first_nonempty(rap, msu, symbol),
            symbol,
            "Oryzabase GeneListEn",
            "Oryzabase",
            row.get("Trait Gene Id", ""),
            "database_trait_gene",
            "medium_confidence",
            coord,
            "development_evidence_candidate",
            "development",
            "Oryzabase trait gene entry; weak localization reference only, not causal ground truth",
        )
    return rows


def frozen_trait_keywords(repo_root: Path) -> list[dict[str, str]]:
    path = repo_root / "reports/trait_state_review/frozen_v0_1_traits.tsv"
    rows = read_tsv(path)
    output: list[dict[str, str]] = []
    for row in rows:
        keywords: set[str] = {normalize_trait_name(row.get("trait_name"))}
        weak_match = clean(row.get("weak_evidence_match"))
        parts = weak_match.split(":")
        if len(parts) >= 2:
            keywords.add(normalize_trait_name(parts[1]))
        # Add conservative aliases for descriptor abbreviations used in frozen traits.
        trait_name = clean(row.get("trait_name")).lower()
        alias_map = {
            "spkf": ["seed set percent", "fertility", "sterility"],
            "fla_repro": ["flag leaf angle", "leaf angle"],
            "cult_code_repro": ["culm length", "plant height", "relative plant height"],
            "llt_code": ["leaf length", "flag leaf length"],
            "pex_repro": ["panicle exsertion"],
            "lsen": ["leaf senescence", "senescence"],
            "pth": ["panicle threshability", "threshability"],
            "cuan_repro": ["culm angle", "flag leaf angle"],
            "cudi_code_repro": ["culm diameter", "stem diameter"],
        }
        for alias in alias_map.get(trait_name, []):
            keywords.add(normalize_trait_name(alias))
        output.append(
            {
                "trait_id": row.get("trait_id", ""),
                "trait_name": row.get("trait_name", ""),
                "keywords": ";".join(sorted(k for k in keywords if k)),
            }
        )
    return output


def match_frozen_trait(trait_name: str, frozen_keywords: list[dict[str, str]]) -> tuple[str, str, str]:
    normalized = normalize_trait_name(trait_name)
    if not normalized:
        return "", "", "missing_trait_name"
    matches: list[tuple[str, str]] = []
    for row in frozen_keywords:
        for keyword in row["keywords"].split(";"):
            if keyword and (keyword in normalized or normalized in keyword):
                matches.append((row["trait_id"], row["trait_name"]))
                break
    unique = sorted(set(matches))
    if len(unique) == 1:
        return unique[0][0], unique[0][1], "keyword_match_to_frozen_trait"
    if len(unique) > 1:
        return ";".join(item[0] for item in unique), ";".join(item[1] for item in unique), "ambiguous_keyword_match"
    return "", "", "broader_evidence_pool_not_frozen_trait"


def build_trait_gene_evidence_rows(repo_root: Path, interim_root: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    known_rows = read_tsv(interim_root / "evidence/known_gene_evidence_table.tsv")
    frozen_keywords = frozen_trait_keywords(repo_root)
    rows: list[dict[str, str]] = []
    review_rows: list[dict[str, str]] = []
    for evidence in known_rows:
        trait_id, trait_name, confidence = match_frozen_trait(evidence.get("trait_id_or_name", ""), frozen_keywords)
        gene_conf = "mapped_gene_coordinate" if evidence.get("coordinate_mapping_status") == "mapped_high_confidence" else "gene_id_or_symbol_only"
        rows.append(
            {
                "trait_gene_evidence_id": f"TGE_{len(rows) + 1:08d}",
                "trait_id": trait_id,
                "trait_name": trait_name or evidence.get("trait_id_or_name", ""),
                "trait_name_normalized": normalize_trait_name(evidence.get("trait_id_or_name", "")),
                "gene_id": evidence.get("gene_id", ""),
                "gene_symbol": evidence.get("gene_symbol", ""),
                "evidence_id": evidence.get("evidence_id", ""),
                "evidence_source": evidence.get("evidence_source", ""),
                "support_level": evidence.get("support_level", ""),
                "trait_mapping_confidence": confidence,
                "gene_mapping_confidence": gene_conf,
                "allowed_usage": evidence.get("allowed_usage", ""),
                "notes": "trait-gene relation is for evaluation reference or explanation only; not a training label",
            }
        )
        if confidence in {"ambiguous_keyword_match", "broader_evidence_pool_not_frozen_trait", "missing_trait_name"}:
            review_rows.append(
                {
                    "review_id": f"MR_TRAIT_{len(review_rows) + 1:08d}",
                    "record_type": "trait_gene_mapping",
                    "source_database": evidence.get("source_database", ""),
                    "source_record_id": evidence.get("evidence_id", ""),
                    "raw_trait_name": evidence.get("trait_id_or_name", ""),
                    "raw_gene_id": evidence.get("gene_id", ""),
                    "raw_gene_symbol": evidence.get("gene_symbol", ""),
                    "candidate_mappings": trait_id,
                    "ambiguity_reason": confidence,
                    "recommended_action": "manual_review_before_main_evaluation" if confidence == "ambiguous_keyword_match" else "keep_in_broader_pool",
                    "priority": "P1" if confidence == "ambiguous_keyword_match" else "P3",
                    "notes": "trait name was not reliably mapped to exactly one frozen v0.1 trait",
                }
            )
    return rows, review_rows


def build_qtl_interval_rows(repo_root: Path) -> list[dict[str, str]]:
    path = repo_root / "data/interim/evidence/qtaro/qtaro_sjis.csv.utf8"
    if not existing(path):
        path = repo_root / "data/interim/evidence/qtaro/qtaro_sjis.csv"
    rows: list[dict[str, str]] = []
    for row in read_csv(path):
        start = parse_int(row.get("Genome start"))
        end = parse_int(row.get("Genome end"))
        chrom = normalize_chrom(row.get("Chr"))
        length = (end - start + 1) if start is not None and end is not None and end >= start else None
        status = "region_level_only" if valid_interval(chrom, start, end) else "unmapped"
        notes = ["Q-TARO interval is region-level weak localization reference only"]
        if length is not None and length > 5_000_000:
            notes.append("broad_interval")
        if not valid_interval(chrom, start, end):
            notes.append("missing_or_invalid_interval")
        rows.append(
            {
                "qtl_evidence_id": f"QTL_QTARO_{len(rows) + 1:08d}",
                "trait_id_or_name": row.get("Character", ""),
                "trait_name_normalized": normalize_trait_name(row.get("Character", "")),
                "chrom": chrom,
                "start": start if start is not None else "",
                "end": end if end is not None else "",
                "interval_length": length if length is not None else "",
                "source_database": "Q-TARO",
                "source_record_id": row.get("id", ""),
                "evidence_type": "qtl_interval",
                "coordinate_mapping_status": status,
                "reference_build": "Q-TARO source coordinates; treated as IRGSP-1.0-compatible but coordinate_build_uncertain",
                "linked_gene_id": "",
                "linked_gene_symbol": row.get("QTL/Gene", ""),
                "allowed_usage": "development_evidence_candidate",
                "notes": "; ".join(notes),
            }
        )
    return rows


def build_coordinate_mapping_rows(interim_root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for evidence in read_tsv(interim_root / "evidence/known_gene_evidence_table.tsv"):
        status = evidence.get("coordinate_mapping_status", "") or "gene_level_only"
        rows.append(
            {
                "evidence_id": evidence.get("evidence_id", ""),
                "original_source": evidence.get("source_database", ""),
                "original_reference_build": evidence.get("reference_build", ""),
                "original_chrom": evidence.get("chrom", ""),
                "original_start": evidence.get("start", ""),
                "original_end": evidence.get("end", ""),
                "mapped_reference_build": evidence.get("reference_build", REFERENCE_BUILD),
                "mapped_chrom": evidence.get("chrom", ""),
                "mapped_start": evidence.get("start", ""),
                "mapped_end": evidence.get("end", ""),
                "mapping_method": "source_reported_gene_coordinate_or_annotation_join",
                "mapping_confidence": "high" if status == "mapped_high_confidence" else "low",
                "mapping_status": status,
                "failure_reason": "" if status == "mapped_high_confidence" else "no reliable coordinate in source or annotation join",
                "notes": "coordinate mapping audit; not a causal label",
            }
        )
    for evidence in read_tsv(interim_root / "evidence/qtl_interval_evidence_table.tsv"):
        status = evidence.get("coordinate_mapping_status", "") or "region_level_only"
        rows.append(
            {
                "evidence_id": evidence.get("qtl_evidence_id", ""),
                "original_source": evidence.get("source_database", ""),
                "original_reference_build": evidence.get("reference_build", ""),
                "original_chrom": evidence.get("chrom", ""),
                "original_start": evidence.get("start", ""),
                "original_end": evidence.get("end", ""),
                "mapped_reference_build": REFERENCE_BUILD if status != "unmapped" else "",
                "mapped_chrom": evidence.get("chrom", "") if status != "unmapped" else "",
                "mapped_start": evidence.get("start", "") if status != "unmapped" else "",
                "mapped_end": evidence.get("end", "") if status != "unmapped" else "",
                "mapping_method": "source_reported_qtaro_interval_no_liftover",
                "mapping_confidence": "low" if status != "unmapped" else "none",
                "mapping_status": status,
                "failure_reason": "" if status != "unmapped" else "invalid or missing interval coordinate",
                "notes": "QTL interval is downgraded to region-level overlap; not causal label",
            }
        )
    return rows


def manifest_lookup(repo_root: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for path in (repo_root / "manifest/download_manifest.tsv", repo_root / "manifest/checksum_table.tsv"):
        for row in read_tsv(path):
            local = clean(row.get("local_path"))
            if local:
                rows.setdefault(local, {}).update(row)
    return rows


def build_source_manifest_rows(repo_root: Path) -> list[dict[str, str]]:
    lookup = manifest_lookup(repo_root)
    source_specs = [
        ("RAP-DB", "IRGSP-1.0 2026-02-05", "data/raw/external_knowledge/rapdb/IRGSP-1.0_representative_annotation_2026-02-05.tsv.gz", "annotation/gene_annotation_table.tsv", "gene_annotation", "build_gene_annotation_table.py"),
        ("RAP-DB", "IRGSP-1.0 2026-02-05", "data/raw/external_knowledge/rapdb/IRGSP-1.0_representative_transcript_exon_2026-02-05.gtf.gz", "annotation/gene_annotation_table.tsv", "gene_annotation", "build_gene_annotation_table.py"),
        ("RAP-DB", "IRGSP-1.0 2026-02-05", "data/raw/external_knowledge/rapdb/RAP-MSU_2026-02-05.txt.gz", "mapping/gene_id_mapping_table.tsv", "id_mapping_resource", "build_gene_id_mapping_table.py"),
        ("RAP-DB", "IRGSP-1.0 2026-02-05", "data/raw/external_knowledge/rapdb/curated_genes.json", "evidence/known_gene_evidence_table.tsv", "known_gene_database", "build_known_gene_evidence_table.py"),
        ("RAP-DB", "IRGSP-1.0 2026-02-05", "data/raw/external_knowledge/rapdb/agri_genes.json", "evidence/known_gene_evidence_table.tsv", "known_gene_database", "build_known_gene_evidence_table.py"),
        ("funRiceGenes", "public static site accessed 2026-05-16", "data/raw/external_knowledge/funricegenes/geneInfo.table.txt", "evidence/known_gene_evidence_table.tsv", "known_gene_database", "build_known_gene_evidence_table.py"),
        ("funRiceGenes", "public static site accessed 2026-05-16", "data/raw/external_knowledge/funricegenes/geneKeyword.table.txt", "evidence/known_gene_evidence_table.tsv", "external_trait_gene_knowledge", "build_known_gene_evidence_table.py"),
        ("funRiceGenes", "public static site accessed 2026-05-16", "data/raw/external_knowledge/funricegenes/famInfo.table.txt", "mapping/gene_id_mapping_table.tsv", "id_mapping_resource", "build_gene_id_mapping_table.py"),
        ("MSU_RGAP", "Release 7", "data/raw/external_knowledge/msu_rgAP/osa1_r7.all_models.gff3.gz", "annotation/gene_annotation_table.tsv", "gene_annotation", "build_gene_annotation_table.py"),
        ("MSU_RGAP", "Release 7", "data/raw/external_knowledge/msu_rgAP/osa1_r7.locus_brief_info.txt.gz", "annotation/gene_annotation_table.tsv", "gene_annotation", "build_gene_annotation_table.py"),
        ("Oryzabase", "local GeneListEn", "data/raw/evidence/known_genes/oryzabase/OryzabaseGeneListEn.tsv", "evidence/known_gene_evidence_table.tsv", "known_gene_database", "build_known_gene_evidence_table.py"),
        ("Q-TARO", "local qtaro_sjis", "data/raw/evidence/qtl/qtaro/qtaro_sjis.zip", "evidence/qtl_interval_evidence_table.tsv", "qtl_database", "build_qtl_interval_evidence_table.py"),
        ("NCBI_RefSeq", "Annotation Release 102", "data/raw/reference/GCF_001433935.1_IRGSP-1.0_genomic.gff.gz", "annotation/gene_annotation_table.tsv", "gene_annotation", "build_gene_annotation_table.py"),
    ]
    rows: list[dict[str, str]] = []
    for source_name, version, raw_path, processed, source_type, script in source_specs:
        path = repo_root / raw_path
        info = lookup.get(raw_path, {})
        checksum = first_nonempty(info.get("checksum_value"), info.get("checksum_sha256"))
        if not checksum and existing(path):
            checksum = sha256_file(path)
        rows.append(
            {
                "source_name": source_name,
                "source_version": version,
                "raw_file_path": raw_path,
                "processed_table": f"data/interim/external_knowledge_v055/{processed}",
                "checksum": checksum,
                "download_or_access_date": first_nonempty(info.get("download_finished_at"), info.get("computed_at"), "local_file_present" if existing(path) else "missing"),
                "source_type": source_type,
                "allowed_usage": "evaluation_reference;explanation;case_study;development_evidence_candidate",
                "license_or_terms_note": "license/terms not reinterpreted in this processing step; review source pages before redistribution",
                "processing_script": f"scripts/external_knowledge/{script}",
                "notes": "external knowledge resource only; not training label",
            }
        )
    return rows


def merge_manual_review_tables(interim_root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in [
        interim_root / "mapping/external_knowledge_manual_review_table.tsv",
        interim_root / "evidence/trait_gene_manual_review_table.tsv",
    ]:
        for row in read_tsv(path):
            row = {field: row.get(field, "") for field in MANUAL_REVIEW_FIELDS}
            row["review_id"] = f"MR_{len(rows) + 1:08d}"
            rows.append(row)
    return rows


def validate_external_knowledge(repo_root: Path, interim_root: Path, report_root: Path) -> list[dict[str, str]]:
    validation: list[dict[str, str]] = []

    def add(check_name: str, status: str, n_records: int, n_failed: int, details: str, blocking: str = "false", notes: str = "") -> None:
        validation.append(
            {
                "check_name": check_name,
                "status": status,
                "n_records": str(n_records),
                "n_failed": str(n_failed),
                "details": details,
                "blocking_issue": blocking,
                "notes": notes,
            }
        )

    annotation = read_tsv(interim_root / "annotation/gene_annotation_table.tsv")
    invalid_annotation = [row for row in annotation if not valid_interval(row.get("chrom", ""), row.get("start", ""), row.get("end", ""))]
    add("gene_annotation_table_coordinates_valid", "pass" if not invalid_annotation else "fail", len(annotation), len(invalid_annotation), "start/end/chrom valid for gene annotation rows", "true" if invalid_annotation else "false")

    mappings = read_tsv(interim_root / "mapping/gene_id_mapping_table.tsv")
    missing_conf = [row for row in mappings if not clean(row.get("mapping_confidence"))]
    add("gene_id_mapping_has_confidence", "pass" if not missing_conf else "fail", len(mappings), len(missing_conf), "mapping_confidence must be populated", "true" if missing_conf else "false")

    known = read_tsv(interim_root / "evidence/known_gene_evidence_table.tsv")
    training_known = [row for row in known if row.get("allowed_usage") == "training_label"]
    add("known_gene_evidence_no_training_label_usage", "pass" if not training_known else "fail", len(known), len(training_known), "known-gene evidence must not be training_label", "true" if training_known else "false")

    qtl = read_tsv(interim_root / "evidence/qtl_interval_evidence_table.tsv")
    bad_qtl = [row for row in qtl if row.get("allowed_usage") == "training_label" or "causal" in row.get("evidence_type", "").lower()]
    add("qtl_interval_no_causal_or_training_usage", "pass" if not bad_qtl else "fail", len(qtl), len(bad_qtl), "QTL interval evidence remains region-level weak reference", "true" if bad_qtl else "false")

    manifest = read_tsv(interim_root / "evidence/evidence_source_manifest.tsv")
    bad_manifest = [row for row in manifest if not row.get("source_name") or not row.get("checksum")]
    add("evidence_source_manifest_has_source_and_checksum", "pass" if not bad_manifest else "fail", len(manifest), len(bad_manifest), "source_name and checksum required", "true" if bad_manifest else "false")

    manual = read_tsv(interim_root / "qc_diagnostics/external_knowledge_manual_review_table.tsv")
    ambiguous = [row for row in mappings if row.get("is_ambiguous") == "true"]
    add("ambiguous_mapping_in_manual_review", "pass" if len(manual) >= len(ambiguous) else "fail", len(ambiguous), max(0, len(ambiguous) - len(manual)), "ambiguous/unmapped gene ID mappings must enter manual review", "true" if len(manual) < len(ambiguous) else "false")

    coord = read_tsv(interim_root / "evidence/evidence_coordinate_mapping_table.tsv")
    allowed_status = {"mapped_high_confidence", "mapped_low_confidence", "gene_level_only", "region_level_only", "unmapped", "manual_review_required"}
    bad_coord = [row for row in coord if row.get("mapping_status") not in allowed_status]
    add("evidence_coordinates_mapped_or_downgraded", "pass" if not bad_coord else "fail", len(coord), len(bad_coord), "coordinate mapping status must be explicit", "true" if bad_coord else "false")

    table_keys = [
        ("annotation/gene_annotation_table.tsv", "gene_id", annotation),
        ("mapping/gene_id_mapping_table.tsv", "mapping_id", mappings),
        ("evidence/known_gene_evidence_table.tsv", "evidence_id", known),
        ("evidence/trait_gene_evidence_table.tsv", "trait_gene_evidence_id", read_tsv(interim_root / "evidence/trait_gene_evidence_table.tsv")),
        ("evidence/qtl_interval_evidence_table.tsv", "qtl_evidence_id", qtl),
        ("evidence/evidence_coordinate_mapping_table.tsv", "evidence_id", coord),
    ]
    for table_name, key_field, rows in table_keys:
        keys = [row.get(key_field, "") for row in rows]
        n_missing = sum(1 for key in keys if not key)
        n_duplicates = len(keys) - len(set(keys))
        failed = n_missing + n_duplicates
        add(
            f"{table_name}_primary_key_unique",
            "pass" if failed == 0 else "fail",
            len(rows),
            failed,
            f"primary key {key_field}; missing={n_missing}; duplicates={n_duplicates}",
            "true" if failed else "false",
        )

    write_tsv(interim_root / "qc_diagnostics/external_knowledge_validation.tsv", validation, VALIDATION_FIELDS)
    write_tsv(report_root / "external_knowledge_validation.tsv", validation, VALIDATION_FIELDS)
    write_report(repo_root, interim_root, report_root, validation)
    return validation


def count_rows(path: Path) -> int:
    return max(0, len(read_tsv(path)))


def write_report(repo_root: Path, interim_root: Path, report_root: Path, validation: list[dict[str, str]]) -> None:
    annotation = read_tsv(interim_root / "annotation/gene_annotation_table.tsv")
    mappings = read_tsv(interim_root / "mapping/gene_id_mapping_table.tsv")
    known = read_tsv(interim_root / "evidence/known_gene_evidence_table.tsv")
    trait_gene = read_tsv(interim_root / "evidence/trait_gene_evidence_table.tsv")
    qtl = read_tsv(interim_root / "evidence/qtl_interval_evidence_table.tsv")
    coord = read_tsv(interim_root / "evidence/evidence_coordinate_mapping_table.tsv")
    manifest = read_tsv(interim_root / "evidence/evidence_source_manifest.tsv")
    manual = read_tsv(interim_root / "qc_diagnostics/external_knowledge_manual_review_table.tsv")

    mapping_by_source: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in mappings:
        mapping_by_source[row.get("source_database", "")].append(row)
    mapping_summary: list[str] = []
    for source, rows in sorted(mapping_by_source.items()):
        success = sum(
            1
            for row in rows
            if row.get("mapping_type") not in {"unmapped", "manual_review_required"}
            and not is_missing_value(row.get("target_gene_id"))
        )
        rate = success / len(rows) if rows else 0
        mapping_summary.append(f"| {source or 'unknown'} | {len(rows)} | {success} | {rate:.4f} |")

    frozen_trait_rows = [
        row
        for row in trait_gene
        if row.get("trait_mapping_confidence") == "keyword_match_to_frozen_trait"
        and not is_missing_value(row.get("trait_id"))
    ]
    frozen_trait_row_ids = {row.get("trait_gene_evidence_id") for row in frozen_trait_rows}
    ambiguous_trait_rows = [row for row in trait_gene if row.get("trait_mapping_confidence") == "ambiguous_keyword_match"]
    broader_rows = [row for row in trait_gene if row.get("trait_gene_evidence_id") not in frozen_trait_row_ids]
    support_counter = Counter(row.get("support_level", "unknown") for row in known)
    coord_counter = Counter(row.get("mapping_status", "unknown") for row in coord)
    failed_checks = [row for row in validation if row.get("status") == "fail"]

    files = [
        ("gene_annotation_table.tsv", interim_root / "annotation/gene_annotation_table.tsv"),
        ("gene_id_mapping_table.tsv", interim_root / "mapping/gene_id_mapping_table.tsv"),
        ("known_gene_evidence_table.tsv", interim_root / "evidence/known_gene_evidence_table.tsv"),
        ("trait_gene_evidence_table.tsv", interim_root / "evidence/trait_gene_evidence_table.tsv"),
        ("qtl_interval_evidence_table.tsv", interim_root / "evidence/qtl_interval_evidence_table.tsv"),
        ("evidence_coordinate_mapping_table.tsv", interim_root / "evidence/evidence_coordinate_mapping_table.tsv"),
        ("evidence_source_manifest.tsv", interim_root / "evidence/evidence_source_manifest.tsv"),
        ("external_knowledge_manual_review_table.tsv", interim_root / "qc_diagnostics/external_knowledge_manual_review_table.tsv"),
        ("external_knowledge_validation.tsv", interim_root / "qc_diagnostics/external_knowledge_validation.tsv"),
    ]

    lines = [
        "# External Knowledge v0.5.5 Integration Report",
        "",
        "## Scope",
        "",
        "This run integrates local RAP-DB, funRiceGenes, MSU / RGAP, Oryzabase, Q-TARO, and reference annotation resources into a unified external knowledge / annotation / weak localization reference layer.",
        "",
        "No model was trained. No matched decoy or frozen split was constructed. No evidence row is allowed to be used as a training label, and no unknown/unlabeled variant or window is treated as a true negative.",
        "",
        "## Raw Sources Used",
        "",
    ]
    for row in manifest:
        lines.append(f"- `{row['raw_file_path']}` ({row['source_name']}, {row['source_type']})")

    lines.extend(["", "## Generated Tables", "", "| table | rows |", "|---|---:|"])
    for name, path in files:
        lines.append(f"| `{rel(path)}` | {count_rows(path)} |")

    lines.extend(["", "## Gene ID Mapping Success", "", "| source | mapping rows | successful mapped rows | success rate |", "|---|---:|---:|---:|"])
    lines.extend(mapping_summary)

    lines.extend(
        [
            "",
            "## Evidence Mapping Summary",
            "",
            f"- Gene-level evidence/reference rows: {len(known)}.",
            f"- Interval-level QTL rows: {len(qtl)}.",
            "- Variant-level evidence rows: 0 in this integration pass.",
            f"- Trait-gene rows with exact frozen 9 trait mapping: {len(frozen_trait_rows)}.",
            f"- Ambiguous frozen-trait keyword matches requiring manual review: {len(ambiguous_trait_rows)}.",
            f"- Trait-gene rows kept in broader evidence pool or manual review: {len(broader_rows)}.",
            f"- Manual review rows: {len(manual)}.",
            f"- Validation failed checks: {len(failed_checks)}.",
            "",
            "Support-level counts:",
        ]
    )
    for key, value in sorted(support_counter.items()):
        lines.append(f"- {key}: {value}")

    lines.extend(["", "Coordinate mapping status counts:"])
    for key, value in sorted(coord_counter.items()):
        lines.append(f"- {key}: {value}")

    frozen_traits = Counter(row.get("trait_name", "unknown") for row in frozen_trait_rows)
    lines.extend(["", "## Frozen-Trait Candidate Pool", ""])
    if frozen_traits:
        for trait_name, value in sorted(frozen_traits.items()):
            lines.append(f"- {trait_name}: {value} gene-level rows")
    else:
        lines.append("- No external gene-level rows mapped to frozen traits.")

    lines.extend(
        [
            "",
            "## Usage Boundary",
            "",
            "All rows in these tables are restricted to evaluation reference, explanation, case study, or development evidence candidate usage. They are not training labels and are not causal ground truth.",
            "",
            "## Current Limitations",
            "",
            "- Q-TARO coordinates are treated as source-reported intervals and downgraded to region-level overlap; no liftover was performed.",
            "- Trait-name mapping uses conservative keyword rules against the frozen 9 traits and therefore leaves many rows in the broader pool.",
            "- Some Oryzabase and funRiceGenes records lack stable RAP/MSU coordinates and require manual review.",
            "- Source license and redistribution terms were not reinterpreted in this processing step.",
            "- Detectability and research-bias matching fields are still not complete; this layer is only a prerequisite for matched decoy construction.",
            "",
            "## Next Step Toward Matched Decoy",
            "",
            "Use `gene_annotation_table.tsv` for gene density and nearest-gene features, `gene_id_mapping_table.tsv` for RAP/MSU/Oryzabase/funRiceGenes harmonization, and the gene/QTL reference tables to define evidence objects. The matched decoy step must match evidence objects against comparable non-evidence background by chromosome/position, gene density, variant density, MAF/LD when available, annotation richness, and explicit matching-field availability.",
        ]
    )

    report_path = report_root / "external_knowledge_integration_report.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(name: str, rows: list[dict[str, str]], extra: str = "") -> None:
    print(f"{name}_rows={len(rows)}")
    if extra:
        print(extra)
