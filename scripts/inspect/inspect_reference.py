#!/usr/bin/env python3
"""Inspect reference FASTA and GFF3 sequence naming."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from inventory_utils import INTERIM_DIR, RAW_ROOT, REPORT_DIR, compact_list, ensure_dirs, open_text, write_tsv


FASTA_FIELDS = ["source_file", "seq_name", "seq_length", "is_primary_chromosome_guess", "notes"]
GFF_FIELDS = ["source_file", "seqid", "n_features", "n_gene", "n_mRNA", "n_exon", "n_CDS", "notes"]


def inspect_fasta(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    current_name = ""
    current_desc = ""
    current_len = 0

    def flush() -> None:
        if not current_name:
            return
        is_primary = "yes" if current_name.startswith("NC_029") else "no"
        rows.append(
            {
                "source_file": str(path),
                "seq_name": current_name,
                "seq_length": current_len,
                "is_primary_chromosome_guess": is_primary,
                "notes": current_desc[:160],
            }
        )

    with open_text(path) as handle:
        for line in handle:
            line = line.rstrip("\n")
            if line.startswith(">"):
                flush()
                header = line[1:].strip()
                current_name = header.split()[0]
                current_desc = header
                current_len = 0
            else:
                current_len += len(line.strip())
        flush()
    return rows


def inspect_gff(path: Path) -> list[dict[str, object]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    with open_text(path) as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            seqid, feature_type = parts[0], parts[2]
            counts[seqid]["features"] += 1
            counts[seqid][feature_type] += 1
    rows: list[dict[str, object]] = []
    for seqid, counter in sorted(counts.items()):
        rows.append(
            {
                "source_file": str(path),
                "seqid": seqid,
                "n_features": counter["features"],
                "n_gene": counter["gene"],
                "n_mRNA": counter["mRNA"],
                "n_exon": counter["exon"],
                "n_CDS": counter["CDS"],
                "notes": f"feature_types={compact_list(counter.keys(), 20)}",
            }
        )
    return rows


def main() -> int:
    ensure_dirs()
    fasta_rows: list[dict[str, object]] = []
    gff_rows: list[dict[str, object]] = []
    for path in sorted((RAW_ROOT / "reference").glob("*.fna.gz")) + sorted((RAW_ROOT / "reference").glob("*.fa.gz")):
        fasta_rows.extend(inspect_fasta(path))
    for path in sorted((RAW_ROOT / "reference").glob("*.gff.gz")) + sorted((RAW_ROOT / "annotation").glob("*.gff.gz")):
        gff_rows.extend(inspect_gff(path))

    write_tsv(REPORT_DIR / "reference_inventory.tsv", fasta_rows, FASTA_FIELDS)
    write_tsv(INTERIM_DIR / "reference_chromosomes.tsv", fasta_rows, FASTA_FIELDS)
    write_tsv(REPORT_DIR / "gff3_inventory.tsv", gff_rows, GFF_FIELDS)
    write_tsv(INTERIM_DIR / "gff3_seqids.tsv", gff_rows, GFF_FIELDS)
    print(f"reference_sequences={len(fasta_rows)}")
    print(f"gff3_seqids={len(gff_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
