#!/usr/bin/env python3
"""Build chr1 SNP-only minimal Task 1 instance prototype.

Usage:
    python scripts/task1/build_chr1_snp_task1_instances.py
"""

from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INTERIM_DIR = REPO_ROOT / "data/interim/task1_chr1_snp"
REPORT_DIR = REPO_ROOT / "reports/task1_chr1_snp"

FROZEN_TRAITS = REPO_ROOT / "reports/trait_state_review/frozen_v0_1_traits.tsv"
HIGH_CONF_ACCESSIONS = REPO_ROOT / "data/interim/trait_state/high_confidence_accessions.tsv"
TRAIT_STATE_TABLE = REPO_ROOT / "data/interim/trait_state/trait_state_table_prototype.tsv"
VARIANT_TABLE = REPO_ROOT / "data/interim/v0_1_mini/variant_table_chr1_snp_v0_1.tsv"
WINDOW_TABLE = REPO_ROOT / "data/interim/v0_1_mini/window_table_chr1_v0_1.tsv"
WEAK_EVIDENCE = REPO_ROOT / "data/interim/v0_1_mini/weak_evidence_chr1_candidates.tsv"

INSTANCE_FIELDS = [
    "instance_id",
    "trait_id",
    "trait_name",
    "internal_accession_id",
    "genotype_sample_id",
    "window_id",
    "chrom",
    "refseq_chrom",
    "start",
    "end",
    "trait_state",
    "trait_group",
    "trait_direction",
    "n_snp_in_window",
    "window_weak_signal",
    "window_label_state",
    "evidence_tier_summary",
    "notes",
]

WINDOW_SIGNAL_FIELDS = [
    "trait_id",
    "window_id",
    "chrom",
    "refseq_chrom",
    "start",
    "end",
    "n_overlapping_evidence",
    "overlap_evidence_sources",
    "max_evidence_tier",
    "window_weak_signal",
    "window_label_state",
    "coordinate_build_uncertain",
    "notes",
]

VARIANT_LABEL_FIELDS = [
    "trait_id",
    "variant_id",
    "chrom",
    "refseq_chrom",
    "pos",
    "overlap_evidence_id",
    "evidence_source",
    "evidence_tier",
    "evidence_type",
    "variant_label_state",
    "distance_to_nearest_evidence",
    "notes",
]

MANIFEST_FIELDS = ["manifest_key", "manifest_value", "notes"]
INSTANCE_SUMMARY_FIELDS = ["metric", "value", "notes"]
TRAIT_SUMMARY_FIELDS = [
    "trait_id",
    "trait_name",
    "n_accessions_with_state",
    "n_instances",
    "n_windows",
    "n_windows_with_weak_evidence",
    "state_distribution",
    "notes",
]
WINDOW_SUMMARY_FIELDS = [
    "trait_id",
    "n_windows_total",
    "n_windows_positive_weak_evidence",
    "n_windows_regional_weak_evidence",
    "n_windows_unknown_unlabeled",
    "positive_or_regional_fraction",
    "notes",
]

TIER_RANK = {
    "Tier 1 known/cloned trait gene": 1,
    "Tier 2 GWAS self-generated": 2,
    "Tier 3 curated literature interval": 3,
    "Tier 4 QTL interval": 4,
}


def ensure_dirs() -> None:
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: "" if row.get(field) is None else row.get(field, "") for field in fields})


def fmt(value: float | None, digits: int = 6) -> str:
    if value is None or math.isnan(value):
        return ""
    text = f"{value:.{digits}f}"
    return text.rstrip("0").rstrip(".")


def compact(values: list[str], limit: int = 20) -> str:
    seen: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    if len(seen) <= limit:
        return ";".join(seen)
    return ";".join(seen[:limit]) + f";...(+{len(seen) - limit})"


def frozen_traits() -> dict[str, dict[str, str]]:
    return {row["trait_id"]: row for row in read_tsv(FROZEN_TRAITS)}


def high_confidence_accessions() -> set[str]:
    return {row["genotype_sample_id"] for row in read_tsv(HIGH_CONF_ACCESSIONS)}


def windows() -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in read_tsv(WINDOW_TABLE):
        out.append(
            {
                **row,
                "start_int": int(row["start"]),
                "end_int": int(row["end"]),
                "n_snp_int": int(row["n_snp"]),
            }
        )
    return out


def variants() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in read_tsv(VARIANT_TABLE):
        rows.append({**row, "pos_int": int(row["pos"])})
    rows.sort(key=lambda row: int(row["pos_int"]))
    return rows


def trait_states(frozen: dict[str, dict[str, str]], high_conf: set[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with TRAIT_STATE_TABLE.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["trait_id"] not in frozen:
                continue
            if row["genotype_sample_id"] not in high_conf:
                continue
            rows.append(row)
    rows.sort(key=lambda row: (row["trait_id"], row["genotype_sample_id"]))
    return rows


def parse_evidence(frozen: dict[str, dict[str, str]]) -> dict[str, list[dict[str, object]]]:
    evidence_by_trait: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in read_tsv(WEAK_EVIDENCE):
        trait_id = row["trait_id"]
        if trait_id not in frozen:
            continue
        start = int(row["start"]) if row.get("start") else None
        end = int(row["end"]) if row.get("end") else None
        evidence_by_trait[trait_id].append({**row, "start_int": start, "end_int": end})
    return evidence_by_trait


def best_tier(tiers: list[str]) -> str:
    if not tiers:
        return ""
    return sorted(tiers, key=lambda tier: TIER_RANK.get(tier, 99))[0]


def overlaps(start: int, end: int, evidence: dict[str, object]) -> bool:
    ev_start = evidence.get("start_int")
    ev_end = evidence.get("end_int")
    if ev_start is None or ev_end is None:
        return False
    lo, hi = sorted((int(ev_start), int(ev_end)))
    return start <= hi and end >= lo


def distance_to_interval(pos: int, evidence: dict[str, object]) -> int | None:
    ev_start = evidence.get("start_int")
    ev_end = evidence.get("end_int")
    if ev_start is None or ev_end is None:
        return None
    lo, hi = sorted((int(ev_start), int(ev_end)))
    if lo <= pos <= hi:
        return 0
    if pos < lo:
        return lo - pos
    return pos - hi


def build_window_signals(
    frozen: dict[str, dict[str, str]],
    window_rows: list[dict[str, object]],
    evidence_by_trait: dict[str, list[dict[str, object]]],
) -> tuple[dict[tuple[str, str], dict[str, object]], list[dict[str, object]], dict[str, Counter[str]]]:
    signal_by_key: dict[tuple[str, str], dict[str, object]] = {}
    rows: list[dict[str, object]] = []
    label_counts_by_trait: dict[str, Counter[str]] = defaultdict(Counter)
    for trait_id in frozen:
        trait_evidence = evidence_by_trait.get(trait_id, [])
        for window in window_rows:
            start = int(window["start_int"])
            end = int(window["end_int"])
            overlapping = [ev for ev in trait_evidence if overlaps(start, end, ev)]
            sources = compact([str(ev["source"]) for ev in overlapping])
            tiers = [str(ev["evidence_tier"]) for ev in overlapping]
            uncertain = any(str(ev.get("coordinate_build_uncertain", "")).lower() == "true" for ev in overlapping)
            label_state = "regional_weak_evidence" if overlapping else "unknown_unlabeled"
            weak_signal = len(overlapping)
            row = {
                "trait_id": trait_id,
                "window_id": window["window_id"],
                "chrom": window["chrom"],
                "refseq_chrom": window["refseq_chrom"],
                "start": window["start"],
                "end": window["end"],
                "n_overlapping_evidence": len(overlapping),
                "overlap_evidence_sources": sources,
                "max_evidence_tier": best_tier(tiers),
                "window_weak_signal": weak_signal,
                "window_label_state": label_state,
                "coordinate_build_uncertain": "true" if uncertain else "false",
                "notes": "weak localization evidence only" if overlapping else "unknown_unlabeled; no supervised absence class assigned",
            }
            signal_by_key[(trait_id, str(window["window_id"]))] = row
            label_counts_by_trait[trait_id][label_state] += 1
            rows.append(row)
    write_tsv(INTERIM_DIR / "window_weak_signal_chr1_snp.tsv", rows, WINDOW_SIGNAL_FIELDS)
    return signal_by_key, rows, label_counts_by_trait


def build_variant_labels(
    frozen: dict[str, dict[str, str]],
    variant_rows: list[dict[str, object]],
    evidence_by_trait: dict[str, list[dict[str, object]]],
) -> tuple[list[dict[str, object]], dict[str, Counter[str]]]:
    rows: list[dict[str, object]] = []
    counts_by_trait: dict[str, Counter[str]] = defaultdict(Counter)
    for trait_id in frozen:
        trait_evidence = [ev for ev in evidence_by_trait.get(trait_id, []) if ev.get("start_int") is not None and ev.get("end_int") is not None]
        for variant in variant_rows:
            pos = int(variant["pos_int"])
            best_ev: dict[str, object] | None = None
            best_distance: int | None = None
            for ev in trait_evidence:
                distance = distance_to_interval(pos, ev)
                if distance is None:
                    continue
                if best_distance is None or distance < best_distance:
                    best_distance = distance
                    best_ev = ev
                    if distance == 0:
                        break
            if best_ev is not None and best_distance == 0:
                label_state = "regional_weak_evidence"
                row = {
                    "trait_id": trait_id,
                    "variant_id": variant["variant_id"],
                    "chrom": variant["chrom"],
                    "refseq_chrom": variant["refseq_chrom"],
                    "pos": variant["pos"],
                    "overlap_evidence_id": best_ev["evidence_candidate_id"],
                    "evidence_source": best_ev["source"],
                    "evidence_tier": best_ev["evidence_tier"],
                    "evidence_type": best_ev["evidence_type"],
                    "variant_label_state": label_state,
                    "distance_to_nearest_evidence": 0,
                    "notes": "variant lies in weak evidence interval; weak localization evidence only",
                }
            else:
                label_state = "unknown_unlabeled"
                row = {
                    "trait_id": trait_id,
                    "variant_id": variant["variant_id"],
                    "chrom": variant["chrom"],
                    "refseq_chrom": variant["refseq_chrom"],
                    "pos": variant["pos"],
                    "overlap_evidence_id": "",
                    "evidence_source": "",
                    "evidence_tier": "",
                    "evidence_type": "",
                    "variant_label_state": label_state,
                    "distance_to_nearest_evidence": "" if best_distance is None else best_distance,
                    "notes": "unknown_unlabeled; no supervised absence class assigned",
                }
            counts_by_trait[trait_id][label_state] += 1
            rows.append(row)
    write_tsv(INTERIM_DIR / "variant_weak_label_chr1_snp.tsv", rows, VARIANT_LABEL_FIELDS)
    return rows, counts_by_trait


def write_instances(
    frozen: dict[str, dict[str, str]],
    state_rows: list[dict[str, str]],
    window_rows: list[dict[str, object]],
    signal_by_key: dict[tuple[str, str], dict[str, object]],
) -> int:
    path = INTERIM_DIR / "task1_chr1_snp_instances.tsv"
    n_instances = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INSTANCE_FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for state in state_rows:
            trait_id = state["trait_id"]
            trait_name = frozen[trait_id]["trait_name"]
            for window in window_rows:
                signal = signal_by_key[(trait_id, str(window["window_id"]))]
                writer.writerow(
                    {
                        "instance_id": f"{trait_id}__{state['genotype_sample_id']}__{window['window_id']}",
                        "trait_id": trait_id,
                        "trait_name": trait_name,
                        "internal_accession_id": state["internal_accession_id"],
                        "genotype_sample_id": state["genotype_sample_id"],
                        "window_id": window["window_id"],
                        "chrom": window["chrom"],
                        "refseq_chrom": window["refseq_chrom"],
                        "start": window["start"],
                        "end": window["end"],
                        "trait_state": state["trait_state"],
                        "trait_group": state["trait_group"],
                        "trait_direction": state["trait_direction"],
                        "n_snp_in_window": window["n_snp"],
                        "window_weak_signal": signal["window_weak_signal"],
                        "window_label_state": signal["window_label_state"],
                        "evidence_tier_summary": signal["max_evidence_tier"],
                        "notes": "trait_state is a condition signal; window label is weak localization evidence or unknown_unlabeled",
                    }
                )
                n_instances += 1
    return n_instances


def state_distribution(rows: list[dict[str, str]]) -> str:
    counts = Counter(row["trait_state"] for row in rows)
    total = sum(counts.values())
    return "; ".join(f"{key}:{value}({fmt(value / total, 4)})" for key, value in counts.most_common())


def write_reports(
    frozen: dict[str, dict[str, str]],
    high_conf_count: int,
    state_rows: list[dict[str, str]],
    window_rows: list[dict[str, object]],
    variant_rows: list[dict[str, object]],
    n_instances: int,
    window_label_counts: dict[str, Counter[str]],
    variant_label_counts: dict[str, Counter[str]],
    evidence_by_trait: dict[str, list[dict[str, object]]],
) -> None:
    state_rows_by_trait: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in state_rows:
        state_rows_by_trait[row["trait_id"]].append(row)
    n_window_trait_pairs = len(frozen) * len(window_rows)
    n_variant_trait_pairs = len(frozen) * len(variant_rows)
    n_windows_with_weak = sum(counts.get("regional_weak_evidence", 0) + counts.get("positive_weak_evidence", 0) for counts in window_label_counts.values())
    n_variants_with_weak = sum(counts.get("regional_weak_evidence", 0) + counts.get("positive_weak_evidence", 0) for counts in variant_label_counts.values())
    manifest_rows = [
        {"manifest_key": "n_accessions", "manifest_value": high_conf_count, "notes": "high-confidence accession subset size"},
        {"manifest_key": "n_traits", "manifest_value": len(frozen), "notes": "frozen v0.1 traits"},
        {"manifest_key": "n_windows", "manifest_value": len(window_rows), "notes": "chr1 windows"},
        {"manifest_key": "n_variants", "manifest_value": len(variant_rows), "notes": "chr1 SNP variants"},
        {"manifest_key": "n_instances", "manifest_value": n_instances, "notes": "trait_state accession rows multiplied by chr1 windows"},
        {"manifest_key": "n_windows_with_weak_evidence", "manifest_value": n_windows_with_weak, "notes": "trait-window pairs with weak evidence"},
        {"manifest_key": "n_variants_with_weak_evidence", "manifest_value": n_variants_with_weak, "notes": "trait-variant pairs with weak evidence"},
        {"manifest_key": "n_unknown_windows", "manifest_value": n_window_trait_pairs - n_windows_with_weak, "notes": "unknown_unlabeled trait-window pairs; no supervised absence class assigned"},
        {"manifest_key": "n_unknown_variants", "manifest_value": n_variant_trait_pairs - n_variants_with_weak, "notes": "unknown_unlabeled trait-variant pairs; no supervised absence class assigned"},
        {"manifest_key": "prototype_version", "manifest_value": "v0.1-chr1-snp-task1", "notes": "prototype only"},
        {"manifest_key": "created_at", "manifest_value": datetime.now(timezone.utc).isoformat(), "notes": "UTC timestamp"},
    ]
    write_tsv(INTERIM_DIR / "task1_chr1_snp_instance_manifest.tsv", manifest_rows, MANIFEST_FIELDS)
    summary_rows = [
        {"metric": "frozen_traits", "value": len(frozen), "notes": "from frozen v0.1 traits"},
        {"metric": "high_confidence_accessions", "value": high_conf_count, "notes": "A/B accession mapping with SNP core and Qmatrix"},
        {"metric": "chr1_snp_variants", "value": len(variant_rows), "notes": "from chr1 SNP variant table"},
        {"metric": "chr1_windows", "value": len(window_rows), "notes": "100kb windows, 50kb stride"},
        {"metric": "task1_instances", "value": n_instances, "notes": "full chr1 SNP-only instance prototype"},
        {"metric": "trait_window_pairs_with_weak_evidence", "value": n_windows_with_weak, "notes": "regional weak evidence"},
        {"metric": "trait_variant_pairs_with_weak_evidence", "value": n_variants_with_weak, "notes": "regional weak evidence"},
        {"metric": "unknown_unlabeled_window_pairs", "value": n_window_trait_pairs - n_windows_with_weak, "notes": "not negative"},
        {"metric": "unknown_unlabeled_variant_pairs", "value": n_variant_trait_pairs - n_variants_with_weak, "notes": "not negative"},
    ]
    write_tsv(REPORT_DIR / "task1_chr1_snp_instance_summary.tsv", summary_rows, INSTANCE_SUMMARY_FIELDS)
    trait_summary_rows: list[dict[str, object]] = []
    for trait_id, trait in frozen.items():
        rows = state_rows_by_trait.get(trait_id, [])
        windows_with_weak = window_label_counts[trait_id].get("regional_weak_evidence", 0) + window_label_counts[trait_id].get("positive_weak_evidence", 0)
        trait_summary_rows.append(
            {
                "trait_id": trait_id,
                "trait_name": trait["trait_name"],
                "n_accessions_with_state": len(rows),
                "n_instances": len(rows) * len(window_rows),
                "n_windows": len(window_rows),
                "n_windows_with_weak_evidence": windows_with_weak,
                "state_distribution": state_distribution(rows),
                "notes": "trait_state is condition input, not prediction label",
            }
        )
    write_tsv(REPORT_DIR / "task1_chr1_snp_trait_summary.tsv", trait_summary_rows, TRAIT_SUMMARY_FIELDS)
    window_summary_rows: list[dict[str, object]] = []
    for trait_id in frozen:
        counts = window_label_counts[trait_id]
        pos = counts.get("positive_weak_evidence", 0)
        regional = counts.get("regional_weak_evidence", 0)
        unknown = counts.get("unknown_unlabeled", 0)
        window_summary_rows.append(
            {
                "trait_id": trait_id,
                "n_windows_total": len(window_rows),
                "n_windows_positive_weak_evidence": pos,
                "n_windows_regional_weak_evidence": regional,
                "n_windows_unknown_unlabeled": unknown,
                "positive_or_regional_fraction": fmt((pos + regional) / len(window_rows), 6),
                "notes": "unknown_unlabeled windows are not negative",
            }
        )
    write_tsv(REPORT_DIR / "task1_chr1_snp_window_signal_summary.tsv", window_summary_rows, WINDOW_SUMMARY_FIELDS)
    frozen_names = "、".join(f"`{row['trait_name']}`" for row in frozen.values())
    qtl_candidates = sum(1 for values in evidence_by_trait.values() for row in values if row.get("start_int") is not None)
    coordless = sum(1 for values in evidence_by_trait.values() for row in values if row.get("start_int") is None)
    lines = [
        "# chr1 SNP-only Minimal Task 1 Instance Report",
        "",
        "## 本次任务目标",
        "",
        "本阶段基于 frozen v0.1 traits、high-confidence accession subset、chr1 SNP variant/window tables 和 chr1 weak evidence audit，构建 chr1 SNP-only minimal Task 1 instance prototype。本阶段不训练模型，不构建 evaluator，不做 phenotype prediction。",
        "",
        "## 输入数据",
        "",
        "- frozen traits：`configs/v0_1_frozen_traits.yaml` 和 `reports/trait_state_review/frozen_v0_1_traits.tsv`。",
        "- accession subset：`data/interim/trait_state/high_confidence_accessions.tsv`。",
        "- chr1 SNP/window：`data/interim/v0_1_mini/variant_table_chr1_snp_v0_1.tsv` 和 `window_table_chr1_v0_1.tsv`。",
        "- weak evidence：`data/interim/v0_1_mini/weak_evidence_chr1_candidates.tsv`。",
        "",
        "## Frozen Trait 子集",
        "",
        frozen_names + "。",
        "",
        "## 样本与变异规模",
        "",
        f"- high-confidence accession 数：{high_conf_count}。",
        f"- chr1 SNP 数：{len(variant_rows)}。",
        f"- chr1 window 数：{len(window_rows)}。",
        f"- Task 1 instance 数：{n_instances}。",
        "",
        "## Weak Evidence 覆盖情况",
        "",
        f"- trait-window weak evidence pairs：{n_windows_with_weak}。",
        f"- trait-variant weak evidence pairs：{n_variants_with_weak}。",
        f"- 有坐标 QTL candidates：{qtl_candidates}。",
        f"- 无坐标 gene/trait semantic candidates：{coordless}。",
        "",
        "## Window Weak Signal 规则",
        "",
        "窗口与带坐标 weak evidence interval overlap 时标记为 `regional_weak_evidence`，`window_weak_signal` 为 overlap evidence 数量。没有 overlap 的窗口标记为 `unknown_unlabeled`。",
        "",
        "## Variant Weak Label 规则",
        "",
        "variant 落入 Q-TARO interval 时标记为 `regional_weak_evidence`。当前 Oryzabase 证据没有可用坐标，只保留在 evidence audit 中，不直接标记 variant。",
        "",
        "## 为什么没有 evidence 不等于 negative",
        "",
        "没有 evidence 只表示当前 weak evidence 来源未覆盖该 window 或 variant，不能解释为 true negative。本 prototype 保留 `unknown_unlabeled`。",
        "",
        "## 为什么这不是 phenotype prediction",
        "",
        "`trait_state` 是条件输入，不是预测目标。本阶段没有预测 accession phenotype value，没有训练模型，也没有构建 evaluator。",
        "",
        "## 当前 Prototype 的限制",
        "",
        "- 仅覆盖 chr1 SNP，不包含 indel、其他染色体或 SV/PAV/CNV。",
        "- Q-TARO coordinate build 仍标记为 uncertain。",
        "- Oryzabase chr1 gene/trait evidence 当前缺少坐标，不能形成 variant/window overlap。",
        "- allele1 / allele2 未验证为 reference / alternate allele。",
        "",
        "## 下一步建议",
        "",
        "如果 Task 1 instance prototype 合格，则构建 minimal evaluator 和 random / heuristic baseline prototype。",
        "",
        "## 结论",
        "",
        "这是 chr1 SNP-only minimal Task 1 instance prototype。它不是最终 benchmark。weak evidence 只是 weak localization evidence。unknown_unlabeled 不作为 negative。",
    ]
    (REPORT_DIR / "task1_chr1_snp_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ensure_dirs()
    frozen = frozen_traits()
    high_conf = high_confidence_accessions()
    window_rows = windows()
    variant_rows = variants()
    state_rows = trait_states(frozen, high_conf)
    evidence_by_trait = parse_evidence(frozen)
    signal_by_key, _signal_rows, window_label_counts = build_window_signals(frozen, window_rows, evidence_by_trait)
    _variant_rows, variant_label_counts = build_variant_labels(frozen, variant_rows, evidence_by_trait)
    n_instances = write_instances(frozen, state_rows, window_rows, signal_by_key)
    write_reports(
        frozen,
        len(high_conf),
        state_rows,
        window_rows,
        variant_rows,
        n_instances,
        window_label_counts,
        variant_label_counts,
        evidence_by_trait,
    )
    print(f"frozen_traits={len(frozen)}")
    print(f"high_confidence_accessions={len(high_conf)}")
    print(f"chr1_snp_variants={len(variant_rows)}")
    print(f"chr1_windows={len(window_rows)}")
    print(f"task1_instances={n_instances}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
