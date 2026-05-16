#!/usr/bin/env python3
"""Build chr1 weak evidence candidate audit for v0.1-mini inputs."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INTERIM_DIR = REPO_ROOT / "data/interim/v0_1_mini"
REPORT_DIR = REPO_ROOT / "reports/v0_1_mini"

ORYZABASE_INVENTORY = REPO_ROOT / "reports/weak_evidence_inventory/oryzabase_inventory.tsv"
QTARO_INVENTORY = REPO_ROOT / "reports/weak_evidence_inventory/qtaro_inventory.tsv"
FROZEN_TRAITS = REPO_ROOT / "reports/trait_state_review/frozen_v0_1_traits.tsv"
WINDOW_TABLE = INTERIM_DIR / "window_table_chr1_v0_1.tsv"
VARIANT_TABLE = INTERIM_DIR / "variant_table_chr1_snp_v0_1.tsv"
VARIANT_WINDOW_MAPPING = INTERIM_DIR / "variant_window_mapping_chr1_v0_1.tsv"

CANDIDATE_FIELDS = [
    "evidence_candidate_id",
    "source",
    "evidence_tier",
    "evidence_type",
    "trait_id",
    "trait_name",
    "trait_or_category",
    "chrom",
    "refseq_chrom",
    "start",
    "end",
    "gene_id",
    "gene_symbol",
    "coordinate_build_uncertain",
    "overlaps_chr1_window",
    "matched_window_ids",
    "notes",
]

AUDIT_FIELDS = [
    "source",
    "evidence_tier",
    "evidence_type",
    "n_raw_records",
    "n_chr1_candidates",
    "n_with_coordinates",
    "n_without_coordinates",
    "n_overlapping_windows",
    "coordinate_build_uncertain_count",
    "notes",
]

TRAIT_ALIASES = {
    "SPKF": ["spikelet fertility", "seed set percent", "fertility"],
    "FLA_REPRO": ["flag leaf angle", "leaf angle"],
    "CULT_CODE_REPRO": ["culm length", "stem length", "plant height"],
    "LLT_CODE": ["leaf length"],
    "PEX_REPRO": ["panicle exsertion"],
    "LSEN": ["leaf senescence", "senescence"],
    "PTH": ["panicle threshability", "threshability"],
    "CUAN_REPRO": ["culm angle", "tiller angle"],
    "CUDI_CODE_REPRO": ["culm diameter", "basal internode", "internode length"],
}


def write_tsv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: "" if row.get(field) is None else row.get(field, "") for field in fields})


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_text(value: object) -> str:
    text = str(value or "").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def compact(values: list[str], limit: int = 30) -> str:
    seen: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    if len(seen) <= limit:
        return ";".join(seen)
    return ";".join(seen[:limit]) + f";...(+{len(seen) - limit})"


def parse_int(value: object) -> int | None:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def inventory_path(path: Path, field: str) -> Path | None:
    rows = read_tsv(path)
    if not rows:
        return None
    value = rows[0].get(field, "")
    if not value:
        return None
    return REPO_ROOT / value


def frozen_traits() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in read_tsv(FROZEN_TRAITS):
        trait_name = row["trait_name"]
        keywords = list(TRAIT_ALIASES.get(trait_name, []))
        weak = row.get("weak_evidence_match", "")
        if ":" in weak:
            parts = weak.split(":")
            if len(parts) >= 2 and parts[1]:
                keywords.append(parts[1])
        keywords.append(trait_name.replace("_", " "))
        rows.append({**row, "keywords": [normalize_text(keyword) for keyword in keywords if normalize_text(keyword)]})
    return rows


def matches_trait(text: str, keywords: list[str]) -> tuple[bool, str]:
    for keyword in keywords:
        if keyword and keyword in text:
            return True, keyword
    for keyword in keywords:
        tokens = [token for token in keyword.split() if len(token) >= 4]
        if len(tokens) >= 2 and all(token in text for token in tokens):
            return True, keyword
    return False, ""


def read_windows() -> list[dict[str, object]]:
    windows: list[dict[str, object]] = []
    for row in read_tsv(WINDOW_TABLE):
        windows.append({**row, "start_int": int(row["start"]), "end_int": int(row["end"])})
    return windows


def overlapping_windows(start: int | None, end: int | None, windows: list[dict[str, object]]) -> list[str]:
    if start is None or end is None:
        return []
    lo, hi = sorted((start, end))
    return [str(row["window_id"]) for row in windows if int(row["start_int"]) <= hi and int(row["end_int"]) >= lo]


def build_qtaro_candidates(traits: list[dict[str, object]], windows: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, int]]:
    qtaro_path = inventory_path(QTARO_INVENTORY, "utf8_file")
    raw_rows = read_csv(qtaro_path) if qtaro_path else []
    candidates: list[dict[str, object]] = []
    chr1_rows = [row for row in raw_rows if str(row.get("Chr", "")).strip() == "1"]
    sequence = 1
    for row in chr1_rows:
        text = normalize_text(
            " ".join(
                [
                    row.get("QTL/Gene", ""),
                    row.get("Major category", ""),
                    row.get("Category of object character", ""),
                    row.get("Character", ""),
                ]
            )
        )
        start = parse_int(row.get("Genome start"))
        end = parse_int(row.get("Genome end"))
        matched_windows = overlapping_windows(start, end, windows)
        for trait in traits:
            ok, keyword = matches_trait(text, trait["keywords"])
            if not ok:
                continue
            candidates.append(
                {
                    "evidence_candidate_id": f"qtaro_chr1_{sequence:05d}",
                    "source": "Q-TARO",
                    "evidence_tier": "Tier 4 QTL interval",
                    "evidence_type": "qtl_interval",
                    "trait_id": trait["trait_id"],
                    "trait_name": trait["trait_name"],
                    "trait_or_category": row.get("Character", "") or row.get("Category of object character", ""),
                    "chrom": "1",
                    "refseq_chrom": "NC_029256.1",
                    "start": start,
                    "end": end,
                    "gene_id": row.get("QTL/Gene", ""),
                    "gene_symbol": row.get("QTL/Gene", ""),
                    "coordinate_build_uncertain": "true",
                    "overlaps_chr1_window": "true" if matched_windows else "false",
                    "matched_window_ids": compact(matched_windows),
                    "notes": f"matched_keyword={keyword}; Q-TARO interval is weak localization evidence only; coordinate build requires later validation",
                }
            )
            sequence += 1
    stats = {
        "n_raw_records": len(raw_rows),
        "n_chr1_source_records": len(chr1_rows),
    }
    return candidates, stats


def build_oryzabase_candidates(traits: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, int]]:
    oryza_path = inventory_path(ORYZABASE_INVENTORY, "source_file")
    raw_rows = read_tsv(oryza_path) if oryza_path else []
    candidates: list[dict[str, object]] = []
    chr1_rows = [row for row in raw_rows if str(row.get("Chromosome No.", "")).strip() == "1"]
    sequence = 1
    for row in chr1_rows:
        text = normalize_text(
            " ".join(
                [
                    row.get("CGSNL Gene Symbol", ""),
                    row.get("CGSNL Gene Name", ""),
                    row.get("Trait Class", ""),
                    row.get("Trait Ontology", ""),
                    row.get("Explanation", ""),
                ]
            )
        )
        for trait in traits:
            ok, keyword = matches_trait(text, trait["keywords"])
            if not ok:
                continue
            candidates.append(
                {
                    "evidence_candidate_id": f"oryzabase_chr1_{sequence:05d}",
                    "source": "Oryzabase",
                    "evidence_tier": "Tier 1 known/cloned trait gene",
                    "evidence_type": "gene_or_trait_evidence_without_coordinate",
                    "trait_id": trait["trait_id"],
                    "trait_name": trait["trait_name"],
                    "trait_or_category": row.get("Trait Class", ""),
                    "chrom": "1",
                    "refseq_chrom": "NC_029256.1",
                    "start": "",
                    "end": "",
                    "gene_id": row.get("RAP ID", "") or row.get("MSU ID", "") or row.get("Trait Gene Id", ""),
                    "gene_symbol": row.get("CGSNL Gene Symbol", ""),
                    "coordinate_build_uncertain": "true",
                    "overlaps_chr1_window": "false",
                    "matched_window_ids": "",
                    "notes": f"matched_keyword={keyword}; Oryzabase chr1 gene-trait evidence lacks coordinate in current inventory; weak localization evidence only",
                }
            )
            sequence += 1
    stats = {
        "n_raw_records": len(raw_rows),
        "n_chr1_source_records": len(chr1_rows),
    }
    return candidates, stats


def audit_rows(qtaro: list[dict[str, object]], qtaro_stats: dict[str, int], oryza: list[dict[str, object]], oryza_stats: dict[str, int]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for source, evidence_tier, evidence_type, candidates, stats in [
        ("Q-TARO", "Tier 4 QTL interval", "qtl_interval", qtaro, qtaro_stats),
        ("Oryzabase", "Tier 1 known/cloned trait gene", "gene_or_trait_evidence_without_coordinate", oryza, oryza_stats),
    ]:
        with_coordinates = [row for row in candidates if row.get("start") and row.get("end")]
        overlapping = [row for row in candidates if row.get("overlaps_chr1_window") == "true"]
        uncertain = [row for row in candidates if row.get("coordinate_build_uncertain") == "true"]
        rows.append(
            {
                "source": source,
                "evidence_tier": evidence_tier,
                "evidence_type": evidence_type,
                "n_raw_records": stats.get("n_raw_records", 0),
                "n_chr1_candidates": len(candidates),
                "n_with_coordinates": len(with_coordinates),
                "n_without_coordinates": len(candidates) - len(with_coordinates),
                "n_overlapping_windows": len(overlapping),
                "coordinate_build_uncertain_count": len(uncertain),
                "notes": f"source_chr1_records={stats.get('n_chr1_source_records', 0)}; weak localization evidence only; not causal ground truth",
            }
        )
    return rows


def read_summary(path: Path) -> dict[str, str]:
    rows = read_tsv(path)
    return rows[0] if rows else {}


def write_mapping_summary(candidates: list[dict[str, object]], audit: list[dict[str, object]]) -> None:
    by_source = defaultdict(int)
    by_trait = defaultdict(int)
    with_coord = 0
    without_coord = 0
    for row in candidates:
        by_source[str(row["source"])] += 1
        by_trait[str(row["trait_name"])] += 1
        if row.get("start") and row.get("end"):
            with_coord += 1
        else:
            without_coord += 1
    lines = [
        "# Weak Evidence Chr1 Mapping Summary",
        "",
        "本报告记录 v0.1-mini chr1 输入骨架中的 weak evidence 关键词匹配结果。",
        "",
        "## 总览",
        "",
        f"- chr1 weak evidence candidates：{len(candidates)}。",
        f"- 有坐标 candidates：{with_coord}。",
        f"- 无坐标 candidates：{without_coord}。",
        "",
        "## 按来源统计",
        "",
    ]
    for source, n in sorted(by_source.items()):
        lines.append(f"- {source}：{n}。")
    lines.extend(["", "## 按冻结 trait 统计", ""])
    for trait, n in sorted(by_trait.items()):
        lines.append(f"- `{trait}`：{n}。")
    lines.extend(
        [
            "",
            "## 审计口径",
            "",
            "Oryzabase / Q-TARO 只作为 `weak localization evidence`。坐标体系仍需后续验证，所有候选均不能写成 `causal ground truth`。没有匹配 evidence 的区域仍是 `unknown_unlabeled`，不能作为 negative。",
        ]
    )
    (REPORT_DIR / "weak_evidence_mapping_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_main_report(candidates: list[dict[str, object]], audit: list[dict[str, object]]) -> None:
    variant_summary = read_summary(REPORT_DIR / "variant_table_chr1_summary.tsv")
    window_summary = read_summary(REPORT_DIR / "window_table_chr1_summary.tsv")
    chrom_rows = read_tsv(REPORT_DIR / "chromosome_map_report.tsv")
    with_coord = sum(1 for row in candidates if row.get("start") and row.get("end"))
    without_coord = len(candidates) - with_coord
    q_taro_coord = sum(1 for row in candidates if row.get("source") == "Q-TARO" and row.get("start") and row.get("end"))
    oryza_without = sum(1 for row in candidates if row.get("source") == "Oryzabase" and not row.get("start"))
    required = [
        INTERIM_DIR / "chromosome_map.tsv",
        INTERIM_DIR / "variant_table_chr1_snp_v0_1.tsv",
        INTERIM_DIR / "snp_table_chr1_v0_1.tsv",
        INTERIM_DIR / "window_table_chr1_v0_1.tsv",
        INTERIM_DIR / "variant_window_mapping_chr1_v0_1.tsv",
        INTERIM_DIR / "weak_evidence_chr1_candidates.tsv",
        REPORT_DIR / "weak_evidence_chr1_audit.tsv",
    ]
    can_rerun_05c = all(path.exists() for path in required)
    lines = [
        "# v0.1-mini Chr1 SNP-only Input Skeleton Report",
        "",
        "## 本次任务目标",
        "",
        "本阶段补齐 05C 所需的 chr1 SNP-only 输入骨架，包括 chromosome map、chr1 SNP variant table、chr1 sliding window table、variant-window mapping 和 chr1 weak evidence audit。本阶段不构建 Task 1 instances，不训练模型，不构建 evaluator，不做 phenotype prediction。",
        "",
        "## 为什么要补这个前置步骤",
        "",
        "05C 构建 Task 1 instances 依赖固定的 variant/window/evidence 输入表。上一轮 05C 因这些输入不存在而停止，因此本阶段只补齐前置输入。",
        "",
        "## Chromosome Map 结果",
        "",
        f"- chromosome map 行数：{len(chrom_rows)}。",
        "- chr1 固定映射为 `1 -> NC_029256.1`。",
        "",
        "## chr1 SNP Variant Table 结果",
        "",
        f"- chr1 SNP 数：{variant_summary.get('n_variants', '')}。",
        f"- 位置范围：{variant_summary.get('min_pos', '')} - {variant_summary.get('max_pos', '')}。",
        "- PLINK BIM 的 allele1 / allele2 未伪装为 ref / alt，后续仍需 allele orientation validation。",
        "",
        "## chr1 Window Table 结果",
        "",
        f"- chr1 reference length：{window_summary.get('reference_length', '')}。",
        f"- window size：{window_summary.get('window_size', '')}，stride：{window_summary.get('stride', '')}。",
        f"- chr1 window 数：{window_summary.get('n_windows', '')}。",
        "",
        "## Variant-window Mapping 结果",
        "",
        f"- variant-window mapping 行数：{window_summary.get('n_variant_window_mapping_rows', '')}。",
        "- 滑动窗口重叠，因此同一个 SNP 可映射到多个 window。",
        "",
        "## Weak Evidence chr1 Audit 结果",
        "",
        f"- chr1 weak evidence candidates：{len(candidates)}。",
        f"- 有坐标 candidates：{with_coord}。",
        f"- 无坐标 candidates：{without_coord}。",
        "",
        "## 哪些 weak evidence 有坐标",
        "",
        f"- Q-TARO chr1 interval candidates 有坐标：{q_taro_coord}。坐标 build 仍标记为 uncertain。",
        "",
        "## 哪些 weak evidence 只有 gene/trait 语义，没有坐标",
        "",
        f"- Oryzabase chr1 gene/trait candidates 无坐标：{oryza_without}。当前只保留 chromosome、gene ID / symbol 和 trait 语义。",
        "",
        "## 为什么不把 weak evidence 当作 causal ground truth",
        "",
        "Oryzabase known/cloned genes 与 Q-TARO QTL interval 只能提供候选区域或语义相关线索，不能证明具体 SNP 为 causal variant。本阶段输出只用于 weak localization evidence。",
        "",
        "## 为什么 unknown 不是 negative",
        "",
        "没有 overlap evidence 的 variant/window 只是未标注或未覆盖，不能解释为 true negative。后续 05C 必须保留 `unknown_unlabeled`。",
        "",
        "## 是否可以重新执行 05C",
        "",
        f"- 05C 必需输入是否齐备：{'yes' if can_rerun_05c else 'no'}。",
        "",
        "## 结论",
        "",
        "本任务只构建 05C 的前置输入表。如果所有必需表都存在，则可以重新执行 `05c_build_chr1_snp_task1_instances.md`。",
    ]
    (REPORT_DIR / "v0_1_mini_input_skeleton_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    windows = read_windows()
    traits = frozen_traits()
    qtaro_candidates, qtaro_stats = build_qtaro_candidates(traits, windows)
    oryza_candidates, oryza_stats = build_oryzabase_candidates(traits)
    candidates = qtaro_candidates + oryza_candidates
    audit = audit_rows(qtaro_candidates, qtaro_stats, oryza_candidates, oryza_stats)
    write_tsv(INTERIM_DIR / "weak_evidence_chr1_candidates.tsv", candidates, CANDIDATE_FIELDS)
    write_tsv(REPORT_DIR / "weak_evidence_chr1_audit.tsv", audit, AUDIT_FIELDS)
    write_mapping_summary(candidates, audit)
    write_main_report(candidates, audit)
    print(f"weak_evidence_chr1_candidates={len(candidates)}")
    print(f"weak_evidence_with_coordinates={sum(1 for row in candidates if row.get('start') and row.get('end'))}")
    print(f"weak_evidence_without_coordinates={sum(1 for row in candidates if not row.get('start'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
