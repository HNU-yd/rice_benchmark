#!/usr/bin/env python3
"""Review trait descriptors and freeze a small v0.1 trait subset.

Usage:
    python scripts/trait_state/review_and_freeze_v0_1_traits.py
"""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

import build_trait_state_prototype as base


REPO_ROOT = Path(__file__).resolve().parents[2]
RECOMMENDATION_PATH = REPO_ROOT / "reports/trait_state/v0_1_trait_recommendation.tsv"
TRAIT_TABLE_PATH = REPO_ROOT / "reports/trait_state/trait_table_summary.tsv"
TRAIT_STATE_PATH = REPO_ROOT / "data/interim/trait_state/trait_state_table_prototype.tsv"
PHENOTYPE_XLSX = REPO_ROOT / "data/raw/traits/3kRG_PhenotypeData_v20170411.xlsx"
ORYZABASE_PATH = REPO_ROOT / "reports/weak_evidence_inventory/oryzabase_trait_gene_summary.tsv"
QTARO_PATH = REPO_ROOT / "reports/weak_evidence_inventory/qtaro_trait_summary.tsv"
REPORT_DIR = REPO_ROOT / "reports/trait_state_review"
INTERIM_DIR = REPO_ROOT / "data/interim/trait_state_review"
CONFIG_PATH = REPO_ROOT / "configs/v0_1_frozen_traits.yaml"

DESCRIPTOR_FIELDS = [
    "trait_id",
    "source_sheet",
    "trait_name",
    "trait_type_guess",
    "n_non_missing",
    "missing_rate",
    "n_unique_values",
    "category_distribution",
    "descriptor_found",
    "descriptor_source",
    "trait_definition",
    "measurement_method",
    "scale_or_code_meaning",
    "biological_interpretability",
    "coding_risk",
    "recommended_action",
    "manual_review_required",
    "notes",
]

CATEGORY_FIELDS = ["trait_id", "trait_name", "trait_state", "n_samples", "fraction", "notes"]

WEAK_MATCH_FIELDS = [
    "trait_id",
    "trait_name",
    "matched_source",
    "matched_keyword",
    "matched_trait_or_category",
    "match_strength",
    "notes",
]

FROZEN_FIELDS = [
    "trait_id",
    "source_sheet",
    "trait_name",
    "trait_type_guess",
    "n_non_missing",
    "category_summary",
    "biological_interpretability",
    "weak_evidence_match",
    "freeze_decision",
    "freeze_reason",
    "notes",
]

FROZEN_TRAIT_IDS = [
    "data_lt_2007__spkf",
    "data_lt_2007__fla_repro",
    "data_lt_2007__cult_code_repro",
    "data_lt_2007__llt_code",
    "data_lt_2007__pex_repro",
    "data_lt_2007__lsen",
    "data_lt_2007__pth",
    "data_lt_2007__cuan_repro",
    "data_lt_2007__cudi_code_repro",
]

TRAIT_ALIASES = {
    "BLCO_REV_VEG": ["leaf color", "blade color", "leaf blade color", "chlorophyll"],
    "CCO_REV_VEG": ["collar color", "leaf color"],
    "LIGCO_REV_VEG": ["ligule color", "leaf color"],
    "APCO_REV_REPRO": ["apiculus color", "lemma color"],
    "AUCO_REV_VEG": ["auricle color", "leaf color"],
    "BLPUB_VEG": ["blade pubescence", "leaf pubescence"],
    "BLSCO_REV_VEG": ["basal leafsheath color", "leaf sheath color", "leaf color"],
    "INCO_REV_REPRO": ["internode color", "internode"],
    "PEX_REPRO": ["panicle exsertion"],
    "CUAN_REPRO": ["culm angle", "tiller angle", "plant architecture"],
    "CUST_REPRO": ["culm strength", "lodging"],
    "LPCO_REV_POST": ["lemma and palea color", "lemma color", "palea color"],
    "SPKF": ["spikelet fertility", "fertility", "seed set percent"],
    "CUDI_CODE_REPRO": ["culm diameter", "basal internode", "internode"],
    "LSEN": ["leaf senescence", "senescence"],
    "PTY": ["panicle type"],
    "FLA_REPRO": ["flag leaf angle", "leaf angle"],
    "PTH": ["panicle threshability", "threshability"],
    "SCCO_REV": ["seed coat color"],
    "ENDO": ["endosperm type", "endosperm"],
    "SLLT_CODE": ["sterile lemma length", "lemma length"],
    "CUNO_CODE_REPRO": ["culm number", "tiller number"],
    "LLT_CODE": ["leaf length"],
    "CULT_CODE_REPRO": ["culm length", "stem length", "plant height"],
    "SDHT_CODE": ["seedling height", "plant height"],
    "PLT_CODE_POST": ["panicle length"],
    "SLCO_REV": ["sterile lemma color", "lemma color"],
    "LA": ["leaf angle"],
    "LPPUB": ["lemma and palea pubescence", "pubescence"],
    "PA_REPRO": ["panicle axis", "panicle angle"],
    "LIGSH": ["ligule shape", "leaf shape"],
    "PSH": ["panicle shattering", "seed shattering", "shattering"],
    "SECOND_BR_REPRO": ["secondary branching", "secondary branch number"],
    "NOCO_REV": ["node color", "culm color"],
}


def ensure_dirs() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    base.write_tsv(path, rows, fields)


def normalize_text(value: object) -> str:
    text = str(value or "").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def sheet_to_dictionary_name(source_sheet: str) -> str:
    if source_sheet == "Data < 2007":
        return "<2007 Dictionary"
    if source_sheet == "Data > 2007":
        return ">2007 Dictionary"
    return "<2007 Dictionary"


def parse_dictionaries() -> dict[tuple[str, str], dict[str, object]]:
    workbook = base.read_workbook(PHENOTYPE_XLSX)
    output: dict[tuple[str, str], dict[str, object]] = {}
    for sheet_name, sheet in workbook.items():
        if "dictionary" not in sheet_name.lower():
            continue
        header_to_idx = {name: idx for idx, name in enumerate(sheet.headers)}
        field_idx = header_to_idx.get("Field Name")
        desc_idx = header_to_idx.get("Descriptor")
        value_idx = header_to_idx.get("Value")
        meaning_idx = header_to_idx.get("Value Description")
        if field_idx is None:
            continue
        for row_number, row in sheet.rows_by_number.items():
            if row_number == 1:
                continue
            field = row[field_idx].strip() if field_idx < len(row) else ""
            if not field:
                continue
            key = (sheet_name, field)
            entry = output.setdefault(key, {"descriptor": "", "code_meanings": {}})
            if desc_idx is not None and desc_idx < len(row) and row[desc_idx]:
                entry["descriptor"] = row[desc_idx]
            if value_idx is not None and meaning_idx is not None and value_idx < len(row):
                code = row[value_idx].strip()
                meaning = row[meaning_idx].strip() if meaning_idx < len(row) else ""
                if code and meaning:
                    entry["code_meanings"][code] = meaning
    return output


def recommended_traits() -> list[dict[str, str]]:
    rows = [row for row in read_tsv(RECOMMENDATION_PATH) if row.get("recommended_for_v0_1") == "true"]
    priority = {trait_id: idx for idx, trait_id in enumerate(FROZEN_TRAIT_IDS)}
    rows.sort(key=lambda row: (priority.get(row["trait_id"], 999), row["trait_id"]))
    return rows


def trait_table_by_id() -> dict[str, dict[str, str]]:
    return {row["trait_id"]: row for row in read_tsv(TRAIT_TABLE_PATH)}


def category_counts(trait_ids: set[str]) -> dict[str, Counter[str]]:
    counts: dict[str, Counter[str]] = {trait_id: Counter() for trait_id in trait_ids}
    for row in read_tsv(TRAIT_STATE_PATH):
        trait_id = row.get("trait_id", "")
        if trait_id in counts:
            raw_value = row.get("raw_value", "")
            counts[trait_id][raw_value] += 1
    return counts


def category_distribution_text(counts: Counter[str], code_meanings: dict[str, str], limit: int = 12) -> str:
    total = sum(counts.values())
    parts: list[str] = []
    for code, n in counts.most_common(limit):
        label = code_meanings.get(code, "")
        label_text = f"={label}" if label else ""
        parts.append(f"{code}{label_text}:{n}({base.fmt_number(n / total, 4)})")
    if len(counts) > limit:
        parts.append(f"...(+{len(counts) - limit})")
    return "; ".join(parts)


def weak_records() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for row in read_tsv(ORYZABASE_PATH):
        text = " ".join(
            [
                row.get("trait_class", ""),
                row.get("example_trait_ontology", ""),
                row.get("example_gene_symbols", ""),
            ]
        )
        records.append(
            {
                "source": "Oryzabase",
                "text": normalize_text(text),
                "label": row.get("trait_class", ""),
                "detail": row.get("example_trait_ontology", ""),
            }
        )
    for row in read_tsv(QTARO_PATH):
        text = " ".join([row.get("major_category", ""), row.get("trait_category", ""), row.get("trait", "")])
        records.append(
            {
                "source": "Q-TARO",
                "text": normalize_text(text),
                "label": row.get("trait", "") or row.get("trait_category", ""),
                "detail": row.get("trait_category", ""),
            }
        )
    return records


def query_phrases(trait_name: str, descriptor: str) -> list[str]:
    phrases = list(TRAIT_ALIASES.get(trait_name, []))
    if descriptor:
        phrases.append(descriptor)
    phrases.append(trait_name.replace("_", " "))
    out: list[str] = []
    for phrase in phrases:
        norm = normalize_text(phrase)
        if norm and norm not in out:
            out.append(norm)
    return out


def match_weak_evidence(trait_name: str, descriptor: str, records: list[dict[str, str]]) -> dict[str, str]:
    phrases = query_phrases(trait_name, descriptor)
    best: dict[str, str] | None = None
    best_score = -1
    for phrase in phrases:
        tokens = [token for token in phrase.split() if len(token) >= 4]
        for record in records:
            text = record["text"]
            score = 0
            strength = "none"
            if phrase and phrase in text:
                score = 3 + len(phrase.split())
                strength = "strong_keyword"
            elif tokens and all(token in text for token in tokens):
                score = 2 + len(tokens)
                strength = "weak_keyword"
            elif len(tokens) >= 2 and sum(1 for token in tokens if token in text) >= 2:
                score = 1
                strength = "weak_keyword"
            if score > best_score:
                best_score = score
                best = {
                    "matched_source": record["source"],
                    "matched_keyword": phrase,
                    "matched_trait_or_category": record["label"] or record["detail"],
                    "match_strength": strength,
                    "notes": "关键词级弱语义匹配；不能解释为 causal ground truth",
                }
    if best and best["match_strength"] != "none":
        return best
    return {
        "matched_source": "none",
        "matched_keyword": "",
        "matched_trait_or_category": "",
        "match_strength": "none",
        "notes": "未找到明确 weak evidence 关键词匹配",
    }


def interpretability(
    descriptor_found: bool,
    n_non_missing: int,
    n_unique: int,
    max_fraction: float,
    weak_strength: str,
) -> str:
    if not descriptor_found:
        return "unknown"
    if n_non_missing < 1000:
        return "low"
    if n_unique <= 8 and max_fraction <= 0.85 and weak_strength in {"strong_keyword", "weak_keyword"}:
        return "high"
    if n_unique <= 10 and max_fraction <= 0.9:
        return "medium"
    return "low"


def coding_risk(descriptor_found: bool, n_unique: int, max_fraction: float, missing_rate: float, labels_found: bool) -> str:
    if not descriptor_found or not labels_found or n_unique > 10 or max_fraction > 0.95:
        return "high"
    if n_unique > 8 or max_fraction > 0.9 or missing_rate > 0.30:
        return "medium"
    return "low"


def recommended_action(trait_id: str, bio: str, risk: str, n_non_missing: int, max_fraction: float) -> str:
    if trait_id in FROZEN_TRAIT_IDS and n_non_missing >= 1000 and bio in {"high", "medium"} and risk != "high" and max_fraction <= 0.85:
        return "keep_for_v0_1"
    if n_non_missing >= 1000 and bio in {"high", "medium"} and risk != "high" and max_fraction <= 0.90:
        return "keep_for_sensitivity_only"
    if bio == "unknown":
        return "exclude_metadata_or_unclear"
    return "defer_until_manual_review"


def category_rows_for_trait(
    trait_id: str,
    trait_name: str,
    counts: Counter[str],
    code_meanings: dict[str, str],
) -> list[dict[str, object]]:
    total = sum(counts.values())
    n_unique = len(counts)
    rows: list[dict[str, object]] = []
    for code, n in counts.most_common():
        fraction = n / total if total else 0.0
        notes: list[str] = []
        if fraction > 0.9:
            notes.append("class_imbalance_high")
        if n_unique > 10:
            notes.append("too_many_categories")
        label = code_meanings.get(code, "")
        if label:
            notes.append(f"code_meaning={label}")
        rows.append(
            {
                "trait_id": trait_id,
                "trait_name": trait_name,
                "trait_state": code,
                "n_samples": n,
                "fraction": base.fmt_number(fraction, 6),
                "notes": "; ".join(notes) if notes else "distribution_ok",
            }
        )
    return rows


def build_review_outputs() -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    recommendations = recommended_traits()
    trait_ids = {row["trait_id"] for row in recommendations}
    table_by_id = trait_table_by_id()
    dictionaries = parse_dictionaries()
    counts_by_trait = category_counts(trait_ids)
    weak = weak_records()

    descriptor_rows: list[dict[str, object]] = []
    distribution_rows: list[dict[str, object]] = []
    weak_rows: list[dict[str, object]] = []
    frozen_rows: list[dict[str, object]] = []

    for rec in recommendations:
        trait_id = rec["trait_id"]
        trait_name = rec["trait_name"]
        source_sheet = rec["source_sheet"]
        stats = table_by_id.get(trait_id, rec)
        dictionary_name = sheet_to_dictionary_name(source_sheet)
        dictionary_entry = dictionaries.get((dictionary_name, trait_name), {"descriptor": "", "code_meanings": {}})
        descriptor = str(dictionary_entry.get("descriptor", "") or "")
        code_meanings = dict(dictionary_entry.get("code_meanings", {}) or {})
        counts = counts_by_trait.get(trait_id, Counter())
        total = sum(counts.values())
        n_unique = len(counts)
        max_fraction = max((n / total for n in counts.values()), default=0.0)
        n_non_missing = int(stats.get("n_non_missing", rec.get("n_non_missing", "0")) or 0)
        missing_rate = float(stats.get("missing_rate", rec.get("missing_rate", "0")) or 0)
        descriptor_found = bool(descriptor)
        labels_found = bool(code_meanings) and all(code in code_meanings for code in counts)
        weak_match = match_weak_evidence(trait_name, descriptor, weak)
        bio = interpretability(descriptor_found, n_non_missing, n_unique, max_fraction, weak_match["match_strength"])
        risk = coding_risk(descriptor_found, n_unique, max_fraction, missing_rate, labels_found)
        action = recommended_action(trait_id, bio, risk, n_non_missing, max_fraction)
        manual_review_required = "false" if action == "keep_for_v0_1" else "true"
        distribution_text = category_distribution_text(counts, code_meanings)
        notes: list[str] = []
        if max_fraction > 0.9:
            notes.append("class_imbalance_high")
        if n_unique > 10:
            notes.append("too_many_categories")
        if not labels_found:
            notes.append("code_meaning_incomplete")
        if trait_id in FROZEN_TRAIT_IDS and action != "keep_for_v0_1":
            notes.append("listed_in_freeze_priority_but_failed_filter")
        notes.append("编码型 trait；不能当作连续生物量")
        descriptor_rows.append(
            {
                "trait_id": trait_id,
                "source_sheet": source_sheet,
                "trait_name": trait_name,
                "trait_type_guess": rec["trait_type_guess"],
                "n_non_missing": n_non_missing,
                "missing_rate": stats.get("missing_rate", rec.get("missing_rate", "")),
                "n_unique_values": stats.get("n_unique_values", n_unique),
                "category_distribution": distribution_text,
                "descriptor_found": "true" if descriptor_found else "false",
                "descriptor_source": dictionary_name if descriptor_found else "",
                "trait_definition": descriptor,
                "measurement_method": "3K phenotype descriptor code in phenotype XLSX dictionary",
                "scale_or_code_meaning": "; ".join(f"{code}={meaning}" for code, meaning in code_meanings.items()),
                "biological_interpretability": bio,
                "coding_risk": risk,
                "recommended_action": action,
                "manual_review_required": manual_review_required,
                "notes": "; ".join(notes),
            }
        )
        distribution_rows.extend(category_rows_for_trait(trait_id, trait_name, counts, code_meanings))
        weak_rows.append(
            {
                "trait_id": trait_id,
                "trait_name": trait_name,
                **weak_match,
            }
        )
        if action == "keep_for_v0_1":
            frozen_rows.append(
                {
                    "trait_id": trait_id,
                    "source_sheet": source_sheet,
                    "trait_name": trait_name,
                    "trait_type_guess": rec["trait_type_guess"],
                    "n_non_missing": n_non_missing,
                    "category_summary": distribution_text,
                    "biological_interpretability": bio,
                    "weak_evidence_match": f"{weak_match['matched_source']}:{weak_match['matched_keyword']}:{weak_match['match_strength']}",
                    "freeze_decision": "freeze_for_v0_1",
                    "freeze_reason": "descriptor 清楚、类别分布未过度极端、样本数充足，并存在关键词级 weak evidence 语义联系",
                    "notes": "trait_state 条件输入；不是 phenotype prediction label",
                }
            )

    order = {trait_id: idx for idx, trait_id in enumerate(FROZEN_TRAIT_IDS)}
    frozen_rows.sort(key=lambda row: order.get(str(row["trait_id"]), 999))
    return descriptor_rows, distribution_rows, weak_rows, frozen_rows


def write_config(frozen_rows: list[dict[str, object]]) -> None:
    lines = [
        "version: v0.1-frozen-traits",
        "",
        "source:",
        '  recommendation_table: "reports/trait_state/v0_1_trait_recommendation.tsv"',
        '  descriptor_review: "reports/trait_state_review/trait_descriptor_review.tsv"',
        "",
        "constraints:",
        "  no_phenotype_prediction: true",
        "  trait_state_is_condition_signal: true",
        "  weak_evidence_not_causal_ground_truth: true",
        "  unknown_not_negative: true",
        '  accession_confidence_levels: ["A", "B"]',
        '  excluded_accession_confidence_levels: ["C", "D"]',
        "",
        "frozen_traits:",
    ]
    for row in frozen_rows:
        lines.extend(
            [
                f"  - trait_id: \"{row['trait_id']}\"",
                f"    source_sheet: \"{row['source_sheet']}\"",
                f"    trait_name: \"{row['trait_name']}\"",
                f"    trait_type_guess: \"{row['trait_type_guess']}\"",
                f"    n_non_missing: {row['n_non_missing']}",
                f"    biological_interpretability: \"{row['biological_interpretability']}\"",
                f"    freeze_decision: \"{row['freeze_decision']}\"",
            ]
        )
    CONFIG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_interim_ids(frozen_rows: list[dict[str, object]]) -> None:
    path = INTERIM_DIR / "frozen_v0_1_trait_ids.txt"
    path.write_text("\n".join(str(row["trait_id"]) for row in frozen_rows) + "\n", encoding="utf-8")


def compact_names(rows: list[dict[str, object]], limit: int = 30) -> str:
    if not rows:
        return "无。"
    names = [f"`{row['trait_id']}`" for row in rows]
    shown = names[:limit]
    suffix = f"\n\n另有 {len(names) - limit} 个未展开，详见 TSV。" if len(names) > limit else ""
    return "、".join(shown) + "。" + suffix


def write_report(
    descriptor_rows: list[dict[str, object]],
    distribution_rows: list[dict[str, object]],
    weak_rows: list[dict[str, object]],
    frozen_rows: list[dict[str, object]],
) -> None:
    reviewed_n = len(descriptor_rows)
    descriptor_found_n = sum(1 for row in descriptor_rows if row["descriptor_found"] == "true")
    high_imbalance_traits = sorted(
        {
            row["trait_id"]
            for row in distribution_rows
            if "class_imbalance_high" in str(row.get("notes", ""))
        }
    )
    too_many_category_traits = sorted(
        {
            row["trait_id"]
            for row in distribution_rows
            if "too_many_categories" in str(row.get("notes", ""))
        }
    )
    weak_matched = [row for row in weak_rows if row["match_strength"] != "none"]
    deferred = [
        row
        for row in descriptor_rows
        if row["recommended_action"] in {"defer_until_manual_review", "exclude_metadata_or_unclear"}
    ]
    sensitivity = [row for row in descriptor_rows if row["recommended_action"] == "keep_for_sensitivity_only"]
    lines = [
        "# Trait Descriptor Review Report",
        "",
        "## 本次任务目标",
        "",
        "本阶段审查 Phase 5A 推荐的 34 个编码型 trait，核对 descriptor、编码含义、类别分布和 weak evidence 关键词匹配，并冻结一个小规模 v0.1-mini trait 子集。本阶段不构建 Task 1 instances，不训练模型，不做 phenotype prediction。",
        "",
        "## 为什么不能直接使用 34 个推荐 trait",
        "",
        "Phase 5A 的推荐主要基于样本覆盖度。34 个 trait 全部是 categorical / binary 编码字段，编码值不是连续生物量。如果不审查 descriptor 和 code meaning，容易把数值编码误读为表型强度，或把极度不平衡类别纳入主流程。",
        "",
        "## Phenotype 字段为什么主要是 categorical / binary",
        "",
        "3K phenotype XLSX 中的 `Data < 2007` 主要采用描述符代码记录形态、颜色、结构和生育相关表型。代码例如颜色等级、形态类别或有序评分，适合构建 trait_state 条件输入，但不能直接作为连续 phenotype prediction target。",
        "",
        "## Descriptor 审查结果",
        "",
        f"- 审查 trait 数量：{reviewed_n}。",
        f"- 找到 descriptor 的 trait 数量：{descriptor_found_n}。",
        f"- 冻结进入 v0.1-mini 的 trait 数量：{len(frozen_rows)}。",
        f"- 保留为 sensitivity-only 的 trait 数量：{len(sensitivity)}。",
        f"- 暂缓或排除的 trait 数量：{len(deferred)}。",
        "",
        "## 类别分布审查结果",
        "",
        f"- 最大类别比例 > 0.9 的 trait 数量：{len(high_imbalance_traits)}。",
        f"- 类别数 > 10 的 trait 数量：{len(too_many_category_traits)}。",
        "极度不平衡或类别过多的 trait 默认不进入 v0.1-mini 主流程。",
        "",
        "## Weak Evidence 关键词匹配结果",
        "",
        f"- 有 Oryzabase / Q-TARO 关键词级匹配的 trait 数量：{len(weak_matched)}。",
        "这些匹配只表示 weak localization evidence 语义联系，不能写成 causal ground truth。",
        "",
        "## 冻结的 v0.1 Trait 子集",
        "",
        compact_names(frozen_rows, 20),
        "",
        "## 暂缓或排除的 trait",
        "",
        compact_names(deferred, 40),
        "",
        "## 对后续 Task 1 Instances 的影响",
        "",
        "后续 chr1 SNP-only minimal Task 1 instances 只应使用 `configs/v0_1_frozen_traits.yaml` 中的 frozen traits。sensitivity-only trait 可用于附录或消融，但不进入主流程。",
        "",
        "## 为什么这不是 phenotype prediction",
        "",
        "`trait_state` 是模型条件输入，用于构造 trait-conditioned localization query。本阶段没有预测 accession phenotype value，没有训练模型，没有构建 split，也没有构建 evaluator。",
        "",
        "## AGENTS.md 未提交改动处理",
        "",
        "`AGENTS.md` 当前新增规则为：每次执行 prompt 后更新 `status.md`。这是工作流规则，本阶段会随提交纳入，并已更新 `status.md`。",
        "",
        "## 主要风险",
        "",
        "- 冻结 traits 仍然是编码型状态，不能当作连续生物量。",
        "- weak evidence 只做关键词级弱语义匹配，不能替代人工证据审查。",
        "- 类别含义来自 phenotype XLSX dictionary，后续论文方法中应保留原始 code meaning。",
        "",
        "## 下一步建议",
        "",
        "如果 frozen v0.1 trait 子集质量可以接受，则构建 chr1 SNP-only minimal Task 1 instances。",
        "",
        "## 结论",
        "",
        "v0.1-mini 只使用冻结的 trait 子集。trait_state 是条件输入，不是预测目标。编码含义不清楚的 trait 不进入主流程。",
    ]
    (REPORT_DIR / "trait_descriptor_review_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ensure_dirs()
    descriptor_rows, distribution_rows, weak_rows, frozen_rows = build_review_outputs()
    write_tsv(REPORT_DIR / "trait_descriptor_review.tsv", descriptor_rows, DESCRIPTOR_FIELDS)
    write_tsv(REPORT_DIR / "trait_category_distribution.tsv", distribution_rows, CATEGORY_FIELDS)
    write_tsv(REPORT_DIR / "trait_to_weak_evidence_keyword_match.tsv", weak_rows, WEAK_MATCH_FIELDS)
    write_tsv(REPORT_DIR / "frozen_v0_1_traits.tsv", frozen_rows, FROZEN_FIELDS)
    write_config(frozen_rows)
    write_interim_ids(frozen_rows)
    write_report(descriptor_rows, distribution_rows, weak_rows, frozen_rows)

    print(f"reviewed_traits={len(descriptor_rows)}")
    print(f"descriptor_found={sum(1 for row in descriptor_rows if row['descriptor_found'] == 'true')}")
    print(f"weak_keyword_matched={sum(1 for row in weak_rows if row['match_strength'] != 'none')}")
    print(f"frozen_traits={len(frozen_rows)}")
    print("no_task1_instances_built=true")
    print("trait_state_is_condition_signal=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
