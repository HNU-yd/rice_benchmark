#!/usr/bin/env python3
"""Evaluate chr1 SNP baseline score tables with weak-evidence ranking metrics.

Inputs:
  data/interim/baselines_chr1_snp/window_baseline_scores.tsv
  data/interim/baselines_chr1_snp/variant_baseline_scores.tsv
  data/interim/task1_chr1_snp/window_weak_signal_chr1_snp.tsv
  data/interim/task1_chr1_snp/variant_weak_label_chr1_snp.tsv

Outputs:
  reports/baselines_chr1_snp/window_baseline_metrics.tsv
  reports/baselines_chr1_snp/variant_baseline_metrics.tsv
  reports/baselines_chr1_snp/topk_window_hits.tsv
  reports/baselines_chr1_snp/topk_variant_hits.tsv
  reports/baselines_chr1_snp/baseline_evaluation_report.md

Usage:
  python scripts/eval/evaluate_chr1_snp_baselines.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INTERIM_DIR = REPO_ROOT / "data/interim/baselines_chr1_snp"
REPORT_DIR = REPO_ROOT / "reports/baselines_chr1_snp"

WINDOW_SCORES = INTERIM_DIR / "window_baseline_scores.tsv"
VARIANT_SCORES = INTERIM_DIR / "variant_baseline_scores.tsv"
WINDOW_SIGNAL = REPO_ROOT / "data/interim/task1_chr1_snp/window_weak_signal_chr1_snp.tsv"
VARIANT_LABEL = REPO_ROOT / "data/interim/task1_chr1_snp/variant_weak_label_chr1_snp.tsv"
FROZEN_TRAITS = REPO_ROOT / "reports/trait_state_review/frozen_v0_1_traits.tsv"

POSITIVE_LABEL_STATES = {"positive_weak_evidence", "regional_weak_evidence"}

WINDOW_METRIC_FIELDS = [
    "baseline_name",
    "trait_id",
    "n_windows",
    "n_positive_or_regional_windows",
    "top_10_hit_rate",
    "top_20_hit_rate",
    "top_50_hit_rate",
    "top_100_hit_rate",
    "weak_evidence_recall_at_10",
    "weak_evidence_recall_at_20",
    "weak_evidence_recall_at_50",
    "weak_evidence_recall_at_100",
    "median_rank_percentile_of_evidence_windows",
    "enrichment_over_random_at_50",
    "notes",
]

VARIANT_METRIC_FIELDS = [
    "baseline_name",
    "trait_id",
    "n_variants",
    "n_positive_or_regional_variants",
    "top_100_hit_rate",
    "top_500_hit_rate",
    "top_1000_hit_rate",
    "top_5000_hit_rate",
    "weak_evidence_recall_at_100",
    "weak_evidence_recall_at_500",
    "weak_evidence_recall_at_1000",
    "weak_evidence_recall_at_5000",
    "median_rank_percentile_of_evidence_variants",
    "enrichment_over_random_at_1000",
    "notes",
]

TOPK_FIELDS = [
    "level",
    "baseline_name",
    "trait_id",
    "k",
    "n_ranked",
    "n_positive_or_regional",
    "n_hits",
    "hit_rate",
    "weak_evidence_recall",
    "expected_hits_random",
    "enrichment_over_random",
    "notes",
]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def require_inputs() -> None:
    missing = [path for path in [WINDOW_SCORES, VARIANT_SCORES, WINDOW_SIGNAL, VARIANT_LABEL, FROZEN_TRAITS] if not path.exists()]
    if missing:
        raise FileNotFoundError("missing required input files: " + ", ".join(str(path) for path in missing))


def write_tsv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def fmt(value: float | None, digits: int = 6) -> str:
    if value is None:
        return ""
    text = f"{value:.{digits}f}"
    return text.rstrip("0").rstrip(".")


def median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def trait_names() -> dict[str, str]:
    return {row["trait_id"]: row["trait_name"] for row in read_tsv(FROZEN_TRAITS)}


def positive_windows() -> dict[str, set[str]]:
    positives: dict[str, set[str]] = defaultdict(set)
    for row in read_tsv(WINDOW_SIGNAL):
        if row["window_label_state"] in POSITIVE_LABEL_STATES:
            positives[row["trait_id"]].add(row["window_id"])
    return positives


def positive_variants() -> dict[str, set[str]]:
    positives: dict[str, set[str]] = defaultdict(set)
    for row in read_tsv(VARIANT_LABEL):
        if row["variant_label_state"] in POSITIVE_LABEL_STATES:
            positives[row["trait_id"]].add(row["variant_id"])
    return positives


def grouped_score_rows(path: Path) -> tuple[tuple[str, str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        current_key: tuple[str, str] | None = None
        current_rows: list[dict[str, str]] = []
        for row in reader:
            key = (row["baseline_name"], row["trait_id"])
            if current_key is None:
                current_key = key
            elif key != current_key:
                yield current_key, current_rows
                current_key = key
                current_rows = []
            current_rows.append(row)
        if current_key is not None:
            yield current_key, current_rows


def topk_rows(
    level: str,
    baseline_name: str,
    trait_id: str,
    rows: list[dict[str, str]],
    id_field: str,
    positive_ids: set[str],
    top_ks: list[int],
) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    n_ranked = len(rows)
    n_positive = len(positive_ids)
    background_rate = (n_positive / n_ranked) if n_ranked else None
    for k in top_ks:
        limit = min(k, n_ranked)
        hits = sum(1 for row in rows[:limit] if row[id_field] in positive_ids)
        hit_rate = (hits / limit) if limit else None
        evidence_recall = (hits / n_positive) if n_positive else None
        expected_hits = (limit * n_positive / n_ranked) if n_ranked else None
        enrichment = (hit_rate / background_rate) if background_rate and hit_rate is not None else None
        out.append(
            {
                "level": level,
                "baseline_name": baseline_name,
                "trait_id": trait_id,
                "k": k,
                "n_ranked": n_ranked,
                "n_positive_or_regional": n_positive,
                "n_hits": hits,
                "hit_rate": fmt(hit_rate),
                "weak_evidence_recall": fmt(evidence_recall),
                "expected_hits_random": fmt(expected_hits),
                "enrichment_over_random": fmt(enrichment),
                "notes": "unknown_unlabeled used only as ranking background",
            }
        )
    return out


def metric_row(
    level: str,
    baseline_name: str,
    trait_id: str,
    rows: list[dict[str, str]],
    id_field: str,
    positive_ids: set[str],
    top_ks: list[int],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    hits = topk_rows(level, baseline_name, trait_id, rows, id_field, positive_ids, top_ks)
    topk_by_k = {int(row["k"]): row for row in hits}
    evidence_percentiles = [float(row["score_percentile"]) for row in rows if row[id_field] in positive_ids]
    median_percentile = median(evidence_percentiles)
    if level == "window":
        row = {
            "baseline_name": baseline_name,
            "trait_id": trait_id,
            "n_windows": len(rows),
            "n_positive_or_regional_windows": len(positive_ids),
            "top_10_hit_rate": topk_by_k[10]["hit_rate"],
            "top_20_hit_rate": topk_by_k[20]["hit_rate"],
            "top_50_hit_rate": topk_by_k[50]["hit_rate"],
            "top_100_hit_rate": topk_by_k[100]["hit_rate"],
            "weak_evidence_recall_at_10": topk_by_k[10]["weak_evidence_recall"],
            "weak_evidence_recall_at_20": topk_by_k[20]["weak_evidence_recall"],
            "weak_evidence_recall_at_50": topk_by_k[50]["weak_evidence_recall"],
            "weak_evidence_recall_at_100": topk_by_k[100]["weak_evidence_recall"],
            "median_rank_percentile_of_evidence_windows": fmt(median_percentile),
            "enrichment_over_random_at_50": topk_by_k[50]["enrichment_over_random"],
            "notes": "weak evidence ranking metric; no formal binary-classifier metric",
        }
    else:
        row = {
            "baseline_name": baseline_name,
            "trait_id": trait_id,
            "n_variants": len(rows),
            "n_positive_or_regional_variants": len(positive_ids),
            "top_100_hit_rate": topk_by_k[100]["hit_rate"],
            "top_500_hit_rate": topk_by_k[500]["hit_rate"],
            "top_1000_hit_rate": topk_by_k[1000]["hit_rate"],
            "top_5000_hit_rate": topk_by_k[5000]["hit_rate"],
            "weak_evidence_recall_at_100": topk_by_k[100]["weak_evidence_recall"],
            "weak_evidence_recall_at_500": topk_by_k[500]["weak_evidence_recall"],
            "weak_evidence_recall_at_1000": topk_by_k[1000]["weak_evidence_recall"],
            "weak_evidence_recall_at_5000": topk_by_k[5000]["weak_evidence_recall"],
            "median_rank_percentile_of_evidence_variants": fmt(median_percentile),
            "enrichment_over_random_at_1000": topk_by_k[1000]["enrichment_over_random"],
            "notes": "weak evidence ranking metric; no formal binary-classifier metric",
        }
    return row, hits


def evaluate_score_file(
    level: str,
    path: Path,
    id_field: str,
    positive_by_trait: dict[str, set[str]],
    top_ks: list[int],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    metric_rows: list[dict[str, object]] = []
    all_topk_rows: list[dict[str, object]] = []
    for (baseline_name, trait_id), rows in grouped_score_rows(path):
        row, hits = metric_row(level, baseline_name, trait_id, rows, id_field, positive_by_trait.get(trait_id, set()), top_ks)
        metric_rows.append(row)
        all_topk_rows.extend(hits)
    return metric_rows, all_topk_rows


def numeric_values(rows: list[dict[str, object]], baseline_name: str, field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        if row.get("baseline_name") != baseline_name:
            continue
        value = str(row.get(field, ""))
        if value:
            values.append(float(value))
    return values


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def aggregate_line(rows: list[dict[str, object]], baseline_name: str, recall_field: str, enrichment_field: str, median_field: str) -> str:
    recall = mean(numeric_values(rows, baseline_name, recall_field))
    enrichment = mean(numeric_values(rows, baseline_name, enrichment_field))
    median_percentile = mean(numeric_values(rows, baseline_name, median_field))
    return f"| `{baseline_name}` | {fmt(recall)} | {fmt(enrichment)} | {fmt(median_percentile)} |"


def write_report(window_metrics: list[dict[str, object]], variant_metrics: list[dict[str, object]]) -> None:
    baseline_names = sorted({str(row["baseline_name"]) for row in window_metrics})
    window_lines = [
        "| baseline | mean weak_evidence_recall_at_50 | mean enrichment_over_random_at_50 | mean evidence rank percentile |",
        "|---|---:|---:|---:|",
    ]
    variant_lines = [
        "| baseline | mean weak_evidence_recall_at_1000 | mean enrichment_over_random_at_1000 | mean evidence rank percentile |",
        "|---|---:|---:|---:|",
    ]
    for baseline_name in baseline_names:
        window_lines.append(
            aggregate_line(
                window_metrics,
                baseline_name,
                "weak_evidence_recall_at_50",
                "enrichment_over_random_at_50",
                "median_rank_percentile_of_evidence_windows",
            )
        )
        variant_lines.append(
            aggregate_line(
                variant_metrics,
                baseline_name,
                "weak_evidence_recall_at_1000",
                "enrichment_over_random_at_1000",
                "median_rank_percentile_of_evidence_variants",
            )
        )

    lines = [
        "# chr1 SNP Baseline Evaluation Report",
        "",
        "## 本次任务目标",
        "",
        "本阶段构建 minimal evaluator 和 random / heuristic baseline prototype，用于检查 chr1 SNP-only Task 1 weak localization evidence 的排序行为。本阶段不训练模型，不构建深度学习模型，不执行 GWAS，不做 phenotype prediction。",
        "",
        "## 使用的输入数据",
        "",
        "- `data/interim/task1_chr1_snp/window_weak_signal_chr1_snp.tsv`。",
        "- `data/interim/task1_chr1_snp/variant_weak_label_chr1_snp.tsv`。",
        "- `data/interim/v0_1_mini/window_table_chr1_v0_1.tsv`。",
        "- `data/interim/v0_1_mini/variant_table_chr1_snp_v0_1.tsv`。",
        "- `reports/trait_state_review/frozen_v0_1_traits.tsv`。",
        "",
        "## Baseline 类型",
        "",
        "- `random_uniform`：每个 trait 内固定 seed 随机分数，seed 为 20260516。",
        "- `window_snp_density`：window 层面使用 `n_snp_in_window`，variant 层面继承 overlapping windows 中最大的 SNP density。",
        "- `genomic_position`：用 window start 或 variant pos 除以 chr1 prototype length。",
        "- `shuffled_trait`：将 trait-specific weak signal 映射到另一个 trait，仅作为 prototype sanity check，不是正式 negative control。",
        "",
        "## Window-level 评价结果",
        "",
        "下表为 baseline-level 摘要；均值只在对应指标非空的 trait 上计算，因此不把无 weak evidence 的 trait 强行计入 recall 或 enrichment。",
        "",
        *window_lines,
        "",
        "## Variant-level 评价结果",
        "",
        "下表为 baseline-level 摘要；均值只在对应指标非空的 trait 上计算，因此不把无 weak evidence 的 trait 强行计入 recall 或 enrichment。",
        "",
        *variant_lines,
        "",
        "## Random Baseline 表现",
        "",
        "`random_uniform` 是固定 seed 的 ranking background；它用于给 top-k hit rate、weak evidence recall 和 enrichment_over_random 提供随机参照。",
        "",
        "## SNP Density Heuristic 表现",
        "",
        "`window_snp_density` 用于检查 weak evidence 是否集中在 SNP 密度较高的 window。它不是生物学模型，也不使用 accession phenotype value。",
        "",
        "## Shuffled Trait Baseline 表现",
        "",
        "`shuffled_trait` 保留 source trait 的 weak signal 分布，但打乱 trait_id 对应关系，用于检查 trait-specific weak evidence 是否主要来自坐标分布重叠。",
        "",
        "## 为什么 unknown_unlabeled 不是 negative",
        "",
        "`unknown_unlabeled` 只表示当前 weak evidence 来源没有覆盖该 window 或 variant，不能解释为 true negative，也不能用于构造 causal / non-causal 二分类标签。本阶段只把它作为 ranking background。",
        "",
        "## 为什么本阶段不报告正式 AUROC / AUPRC",
        "",
        "当前还没有 matched decoy，也没有 frozen split。因此 AUROC、AUPRC、accuracy、precision、F1 等正式二分类指标需要 matched decoy 后才能作为正式主指标。本阶段只报告 top-k ranking、weak evidence recall、evidence rank percentile 和 enrichment_over_random。",
        "",
        "## 当前 Prototype 的限制",
        "",
        "- 仅覆盖 chr1 SNP，不包含 indel 和其他染色体。",
        "- weak evidence 不是 causal ground truth。",
        "- 没有 matched decoy，因此不能解释为正式监督评测。",
        "- `shuffled_trait` 使用 weak signal 分布做 sanity check，不能作为正式 negative control。",
        "- variant 层面的 `window_snp_density` 是从 overlapping windows 派生的粗略 heuristic。",
        "",
        "## 下一步建议",
        "",
        "构建 matched decoy 和 frozen split，然后再进入正式 evaluator 指标。",
        "",
        "## 结论",
        "",
        "这是 evaluator / baseline prototype。正式主指标需要 matched decoy 和冻结 split 后再计算。",
    ]
    (REPORT_DIR / "baseline_evaluation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    require_inputs()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    _traits = trait_names()
    window_metrics, topk_window_rows = evaluate_score_file("window", WINDOW_SCORES, "window_id", positive_windows(), [10, 20, 50, 100])
    variant_metrics, topk_variant_rows = evaluate_score_file(
        "variant", VARIANT_SCORES, "variant_id", positive_variants(), [100, 500, 1000, 5000]
    )
    write_tsv(REPORT_DIR / "window_baseline_metrics.tsv", window_metrics, WINDOW_METRIC_FIELDS)
    write_tsv(REPORT_DIR / "variant_baseline_metrics.tsv", variant_metrics, VARIANT_METRIC_FIELDS)
    write_tsv(REPORT_DIR / "topk_window_hits.tsv", topk_window_rows, TOPK_FIELDS)
    write_tsv(REPORT_DIR / "topk_variant_hits.tsv", topk_variant_rows, TOPK_FIELDS)
    write_report(window_metrics, variant_metrics)
    print(f"window_metric_rows={len(window_metrics)}")
    print(f"variant_metric_rows={len(variant_metrics)}")
    print(f"topk_window_rows={len(topk_window_rows)}")
    print(f"topk_variant_rows={len(topk_variant_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
