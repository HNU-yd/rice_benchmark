#!/usr/bin/env python3
"""Compare accession/sample sets and write Phase 3 summary reports."""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

from inventory_utils import INTERIM_DIR, RAW_ROOT, REPORT_DIR, compact_list, ensure_dirs, normalize_id, read_tsv, write_tsv


OVERLAP_FIELDS = [
    "left_set",
    "right_set",
    "n_left",
    "n_right",
    "n_intersection_raw",
    "n_intersection_normalized",
    "jaccard_raw",
    "jaccard_normalized",
    "example_matches",
    "example_left_only",
    "example_right_only",
    "notes",
]
SUMMARY_FIELDS = ["set_name", "source_file_count", "n_ids_raw", "n_ids_normalized", "first_ids", "notes"]
CHROM_FIELDS = [
    "source_type",
    "source_file",
    "chrom_values",
    "n_chrom_values",
    "n_matching_reference",
    "n_not_matching_reference",
    "example_not_matching",
    "notes",
]
RISK_FIELDS = [
    "risk_id",
    "risk_category",
    "severity",
    "affected_files",
    "description",
    "why_it_matters",
    "recommended_action",
    "blocking_next_phase",
]


def read_id_set(path: Path, value_column: str, set_name: str) -> dict[str, object]:
    rows = read_tsv(path)
    ids = [row.get(value_column, "").strip() for row in rows if row.get(value_column, "").strip()]
    raw_set = set(ids)
    norm_set = {normalize_id(value) for value in ids if normalize_id(value)}
    sources = {row.get("source_file", "") for row in rows if row.get("source_file")}
    return {
        "set_name": set_name,
        "path": path,
        "ids": raw_set,
        "norm_ids": norm_set,
        "sources": sources,
        "first_ids": sorted(raw_set)[:20],
    }


def jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 0.0
    return len(left & right) / len(left | right)


def compare_sets(sets: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    summary_rows: list[dict[str, object]] = []
    for item in sets:
        summary_rows.append(
            {
                "set_name": item["set_name"],
                "source_file_count": len(item["sources"]),
                "n_ids_raw": len(item["ids"]),
                "n_ids_normalized": len(item["norm_ids"]),
                "first_ids": compact_list(item["first_ids"], 20),
                "notes": f"source={item['path']}",
            }
        )

    overlap_rows: list[dict[str, object]] = []
    for left, right in combinations(sets, 2):
        left_ids = left["ids"]
        right_ids = right["ids"]
        left_norm = left["norm_ids"]
        right_norm = right["norm_ids"]
        raw_matches = sorted(left_ids & right_ids)
        norm_matches = sorted(left_norm & right_norm)
        overlap_rows.append(
            {
                "left_set": left["set_name"],
                "right_set": right["set_name"],
                "n_left": len(left_ids),
                "n_right": len(right_ids),
                "n_intersection_raw": len(raw_matches),
                "n_intersection_normalized": len(norm_matches),
                "jaccard_raw": f"{jaccard(left_ids, right_ids):.6f}",
                "jaccard_normalized": f"{jaccard(left_norm, right_norm):.6f}",
                "example_matches": compact_list(raw_matches or norm_matches, 10),
                "example_left_only": compact_list(sorted(left_ids - right_ids), 10),
                "example_right_only": compact_list(sorted(right_ids - left_ids), 10),
                "notes": "normalized overlap uses case/symbol stripping; not a validated accession mapping",
            }
        )
    return overlap_rows, summary_rows


def split_chroms(value: str) -> list[str]:
    return [item for item in str(value or "").split(",") if item and not item.startswith("...")]


def write_chromosome_report() -> list[dict[str, object]]:
    ref_rows = read_tsv(INTERIM_DIR / "reference_chromosomes.tsv")
    ref_chroms = {row["seq_name"] for row in ref_rows if row.get("seq_name")}
    rows: list[dict[str, object]] = []

    def add(source_type: str, source_file: str, chroms: list[str], notes: str = "") -> None:
        chrom_set = set(chroms)
        matching = chrom_set & ref_chroms
        not_matching = chrom_set - ref_chroms
        rows.append(
            {
                "source_type": source_type,
                "source_file": source_file,
                "chrom_values": compact_list(sorted(chrom_set), 80),
                "n_chrom_values": len(chrom_set),
                "n_matching_reference": len(matching),
                "n_not_matching_reference": len(not_matching),
                "example_not_matching": compact_list(sorted(not_matching), 20),
                "notes": notes,
            }
        )

    for row in ref_rows:
        add("reference_chromosomes", row.get("source_file", ""), [row.get("seq_name", "")], row.get("notes", ""))
    for row in read_tsv(INTERIM_DIR / "gff3_seqids.tsv"):
        add("gff3_seqids", row.get("source_file", ""), [row.get("seqid", "")], "GFF3 direct seqid comparison")
    for row in read_tsv(REPORT_DIR / "snp_file_inventory.tsv"):
        add(
            "snp_vcf_chroms",
            row.get("file_path", ""),
            split_chroms(row.get("first_observed_chroms", "")),
            "VCF observed chroms are numeric; require mapping to RefSeq NC_* names",
        )
    for row in read_tsv(REPORT_DIR / "plink_file_inventory.tsv"):
        source_type = "indel_plink_chroms" if row.get("data_category_guess") == "indel_genotype" else "snp_plink_chroms"
        add(
            source_type,
            row.get("file_group", ""),
            split_chroms(row.get("chrom_values", "")),
            "PLINK chrom values are numeric; require mapping to RefSeq NC_* names",
        )
    write_tsv(REPORT_DIR / "chromosome_naming_report.tsv", rows, CHROM_FIELDS)
    return rows


def write_risk_report(overlap_rows: list[dict[str, object]], chrom_rows: list[dict[str, object]]) -> None:
    def overlap(left: str, right: str) -> int:
        for row in overlap_rows:
            if {row["left_set"], row["right_set"]} == {left, right}:
                return int(row["n_intersection_normalized"])
        return 0

    chrom_mismatches = [row for row in chrom_rows if row["source_type"] in {"snp_vcf_chroms", "snp_plink_chroms", "indel_plink_chroms"} and int(row["n_not_matching_reference"] or 0) > 0]
    raw_rows = read_tsv(REPORT_DIR / "raw_file_inventory.tsv")
    evidence_files = [row for row in raw_rows if row.get("inferred_category") == "weak_evidence"]
    evidence_desc = (
        f"已发现 {len(evidence_files)} 个 raw weak evidence candidate，但尚未做 provenance、coordinate build 和 checksum/manifest 补登记。"
        if evidence_files
        else "fast download 和 inventory 中没有发现可直接使用的 weak evidence 表。"
    )
    rows = [
        {
            "risk_id": "RISK_ACCESSION_ID_MISMATCH",
            "risk_category": "accession ID mismatch",
            "severity": "high",
            "affected_files": "trait table; genotype PLINK/VCF; metadata",
            "description": "trait table 中的 accession-like values 与 B001-style genotype sample IDs 尚未建立可信映射。",
            "why_it_matters": "Task 1 需要 trait-conditioned localization；trait_state 不能与 genotype accession 错配。",
            "recommended_action": "先建立 accession mapping crosswalk，再构建 benchmark 输入表。",
            "blocking_next_phase": "yes",
        },
        {
            "risk_id": "RISK_SNP_INDEL_SAMPLE_MISMATCH",
            "risk_category": "SNP / indel sample mismatch",
            "severity": "medium",
            "affected_files": "core_v0.7.*; Nipponbare_indel.*",
            "description": f"SNP PLINK 与 indel PLINK normalized overlap={overlap('snp_samples', 'indel_samples')}；需要确认是否为同一 accession panel。",
            "why_it_matters": "SNP+indel benchmark 需要一致的 accession context。",
            "recommended_action": "用 FAM IDs 建立 genotype accession set，并检查所有 candidate genotype 文件的 sample order。",
            "blocking_next_phase": "yes",
        },
        {
            "risk_id": "RISK_TRAIT_GENOTYPE_OVERLAP",
            "risk_category": "trait / genotype overlap insufficient",
            "severity": "high",
            "affected_files": "3kRG_PhenotypeData_v20170411.xlsx; genotype files",
            "description": "trait_accessions 与 genotype sample IDs 的 raw/normalized overlap 需要人工解释，当前不应假设可直接对齐。",
            "why_it_matters": "trait_state 构建依赖 accession overlap；否则会产生错误标签或样本泄漏。",
            "recommended_action": "检查 phenotype sheet 中 accession 字段含义，并与 RICE_RP/Qmatrix/FAM 建立映射。",
            "blocking_next_phase": "yes",
        },
        {
            "risk_id": "RISK_REFERENCE_BUILD_MISMATCH",
            "risk_category": "reference build mismatch",
            "severity": "medium",
            "affected_files": "FASTA/GFF3; SNP/indel genotype",
            "description": "FASTA/GFF3 为 RefSeq NC_* 命名，SNP/indel genotype 多为 numeric chromosome 命名。",
            "why_it_matters": "reference window extraction 和 variant coordinate lookup 需要统一 coordinate system。",
            "recommended_action": "建立 1-12 到 NC_029256.1-NC_029267.1 的 chromosome mapping，并记录 source provenance。",
            "blocking_next_phase": "yes",
        },
        {
            "risk_id": "RISK_CHROMOSOME_NAMING_MISMATCH",
            "risk_category": "chromosome naming mismatch",
            "severity": "medium",
            "affected_files": compact_list([row["source_file"] for row in chrom_mismatches], 10),
            "description": "numeric chromosome 与 RefSeq accession-style seqid 不能直接 join。",
            "why_it_matters": "直接 join 会导致 variant/window/gene annotation 无匹配。",
            "recommended_action": "在 Phase 4 前固定 chromosome naming normalization 规则。",
            "blocking_next_phase": "yes",
        },
        {
            "risk_id": "RISK_WEAK_EVIDENCE_MISSING",
            "risk_category": "weak evidence missing or unverified",
            "severity": "medium",
            "affected_files": compact_list([row.get("local_path", "") for row in evidence_files], 10) if evidence_files else "known gene / QTL / GWAS lead SNP tables",
            "description": evidence_desc,
            "why_it_matters": "weak evidence 只有在 provenance、trait specificity 和 coordinate build 清楚时才能作为 weak localization evidence。",
            "recommended_action": "补登记 source、checksum 和 coordinate build；不能把 weak evidence 写成 causal ground truth。",
            "blocking_next_phase": "no",
        },
        {
            "risk_id": "RISK_RAW_EVIDENCE_NOT_IN_MANIFEST",
            "risk_category": "unregistered raw evidence",
            "severity": "medium",
            "affected_files": compact_list([row.get("local_path", "") for row in evidence_files if row.get("checksum_status") != "registered"], 10),
            "description": "部分 evidence raw files 不在当前 checksum manifest 中。",
            "why_it_matters": "未登记 checksum 的 raw evidence 后续不可作为可复现输入。",
            "recommended_action": "在确认来源后更新 manifest/checksum；若 provenance 不清楚则仅作为待审阅 raw candidate。",
            "blocking_next_phase": "no",
        },
        {
            "risk_id": "RISK_UNKNOWN_NOT_NEGATIVE",
            "risk_category": "unknown cannot be negative",
            "severity": "high",
            "affected_files": "all unlabeled variants/windows",
            "description": "未被 weak evidence 标注的 SNP/indel 不能自动作为 negative。",
            "why_it_matters": "unknown != negative 是本 benchmark 的核心标签原则。",
            "recommended_action": "后续使用 matched decoy 或 explicitly unlabeled policy，不能使用 naive negative sampling。",
            "blocking_next_phase": "yes",
        },
        {
            "risk_id": "RISK_ARCHIVE_CONTENT_UNCLEAR",
            "risk_category": "archive content unclear",
            "severity": "medium",
            "affected_files": "RICE_RP.tar.gz; 3K_coreSNP-v2.1.plink.tar.gz; chr zip archives",
            "description": "archive 已列目录，但大型 PED/BED/VCF-like 成员未全量解析。",
            "why_it_matters": "archive 内部格式和 sample order 可能决定 mini/core 数据选择。",
            "recommended_action": "只在确定 v0.1-mini/v0.2-core 范围后解包必要小文件或使用 streaming parser。",
            "blocking_next_phase": "no",
        },
        {
            "risk_id": "RISK_LARGE_GENOTYPE_NOT_FULLY_INSPECTED",
            "risk_category": "large genotype file not fully inspected",
            "severity": "medium",
            "affected_files": "VCF, PED, BED, per-chromosome zip",
            "description": "本阶段只检查 header、FAM/BIM 和 archive listing，未全量解析 genotype matrix。",
            "why_it_matters": "variant count、missingness、sample order 和 genotype encoding 仍需后续验证。",
            "recommended_action": "Phase 4/5 只对选定 mini 范围做受控解析。",
            "blocking_next_phase": "no",
        },
    ]
    write_tsv(REPORT_DIR / "raw_data_risk_report.tsv", rows, RISK_FIELDS)


def write_recommendation(overlap_rows: list[dict[str, object]]) -> None:
    text = """# v0.1-mini 数据范围建议

## 推荐方案 A：最快跑通

优先使用 `core_v0.7.bed.gz`、`core_v0.7.bim.gz`、`core_v0.7.fam.gz` 作为 SNP-only prototype 的主 genotype 输入。该组文件已经有 FAM/BIM，可快速得到 sample set、variant coordinates 和 chromosome values。先选择 chr1 的一小段 reference window 做 prototype，避免一开始解包 per-chromosome PED zip 或大型 archive。

trait table 可以进入 inventory 和 accession mapping，但暂时不要作为 phenotype prediction target。只有在 trait accession 与 genotype accession 建立明确映射后，才能构建 trait_state。

## 推荐方案 B：更接近正式 benchmark

在方案 A 跑通后，同时纳入 `Nipponbare_indel.bed.gz`、`Nipponbare_indel.bim.gz`、`Nipponbare_indel.fam.gz`，形成 SNP+indel 的 v0.2-core 候选。当前 SNP PLINK 与 indel PLINK 的样本 ID 看起来都是 B001-style，但仍需检查 sample order 和 accession provenance。

坐标层面必须先建立 numeric chromosome 到 RefSeq `NC_029256.1`-`NC_029267.1` 的 mapping，再做 FASTA/GFF3/reference window join。

## 推荐方案 C：如果 trait accession 对齐失败

如果 `3kRG_PhenotypeData_v20170411.xlsx` 无法可靠映射到 genotype accession，v0.1-mini 应先做 genotype/reference/annotation 层面的 localization input prototype，不生成正式 trait-conditioned labels。此时可以保留 trait table inventory，并把 trait_state 构建延后到 accession crosswalk 完成之后。

## 当前不建议

不建议先使用 `NB_bialSNP_pseudo*.vcf.gz` 作为主 genotype 输入，因为 header 只显示 dummy sample，不能直接代表 accession-level genotype matrix。不建议一开始解包大型 PED 或全量 BED genotype，也不建议把 weak evidence 缺失区域当作 negative。
"""
    (REPORT_DIR / "v0_1_mini_recommendation.md").write_text(text, encoding="utf-8")


def write_main_report(overlap_rows: list[dict[str, object]], chrom_rows: list[dict[str, object]]) -> None:
    raw_rows = read_tsv(REPORT_DIR / "raw_file_inventory.tsv")
    raw_size = sum(int(row.get("file_size_bytes") or 0) for row in raw_rows)
    evidence_rows = [row for row in raw_rows if row.get("inferred_category") == "weak_evidence"]
    ref_rows = read_tsv(REPORT_DIR / "reference_inventory.tsv")
    gff_rows = read_tsv(REPORT_DIR / "gff3_inventory.tsv")
    snp_rows = read_tsv(REPORT_DIR / "snp_file_inventory.tsv")
    plink_rows = read_tsv(REPORT_DIR / "plink_file_inventory.tsv")
    indel_rows = read_tsv(REPORT_DIR / "indel_file_inventory.tsv")
    trait_rows = read_tsv(REPORT_DIR / "trait_table_inventory.tsv")
    meta_rows = read_tsv(REPORT_DIR / "accession_metadata_inventory.tsv")
    risk_rows = read_tsv(REPORT_DIR / "raw_data_risk_report.tsv")

    snp_plink = [row for row in plink_rows if row.get("data_category_guess") == "snp_genotype"]
    high_risks = [row for row in risk_rows if row.get("severity") == "high"]
    chrom_mismatch = [row for row in chrom_rows if row.get("source_type") in {"snp_vcf_chroms", "snp_plink_chroms", "indel_plink_chroms"} and int(row.get("n_not_matching_reference") or 0) > 0]

    text = f"""# Phase 3 Raw Data Inventory 报告

## 1. 本次 inventory 目标

本次任务只检查已经落盘的 raw data，不继续下载，不构建 benchmark schema，不训练模型，不生成 split、evaluator 或 Evo2 代码。目标是判断 reference、annotation、SNP genotype、indel genotype、trait table 和 accession metadata 是否具备进入 v0.1-mini / v0.2-core 的基本条件。

## 2. 已检查的数据目录

已检查 `data/raw/reference/`、`data/raw/annotation/`、`data/raw/accessions/`、`data/raw/variants/`、`data/raw/traits/`、`data/raw/metadata/`、`data/raw/listings/`，并读取 `manifest/download_manifest.tsv` 和 `manifest/checksum_table.tsv`。

## 3. raw 文件总数和总大小

`data/raw` 当前文件数为 {len(raw_rows)}，登记大小合计约 {raw_size / (1024 ** 3):.2f} GiB。完整清单见 `raw_file_inventory.tsv`。

## 4. reference FASTA 结果

FASTA inventory 识别到 {len(ref_rows)} 条 sequence，其中 RefSeq primary chromosome 为 12 条，命名为 `NC_029256.1` 到 `NC_029267.1`。其余为 unplaced scaffold。该 reference 可作为 IRGSP-1.0 reference window 来源。

## 5. GFF3 annotation 结果

GFF3 inventory 识别到 {len(gff_rows)} 个 seqid。GFF3 seqid 使用与 FASTA 相同的 RefSeq accession-style 命名，因此 FASTA 与 GFF3 可以直接按 seqid 对齐。

## 6. SNP genotype 结果

VCF 检查识别到 {len(snp_rows)} 个 `.vcf.gz` 文件；这些 VCF header 中 sample count 很低或为 dummy sample，不应直接作为 accession-level genotype 主输入。SNP PLINK 检查识别到 {len(snp_plink)} 个 SNP PLINK group，其中 `core_v0.7.*` 提供 B001-style sample IDs 和 BIM variant coordinates，更适合作为 v0.1-mini 起点。

## 7. indel genotype 结果

indel PLINK 检查识别到 {len(indel_rows)} 个 indel group，主要是 `Nipponbare_indel.*.gz`。其 FAM sample IDs 与 SNP core PLINK 同为 B001-style，适合在 v0.2-core 中纳入，但需要先验证 sample order 和 accession provenance。

## 8. trait table 结果

trait table inventory 识别到 {len(trait_rows)} 个 sheet。XLSX 中可抽取 accession-like 字段和 trait-like 字段，但当前不能把 trait values 当作 phenotype prediction target，只能用于后续构建 `trait_state`。

## 9. accession metadata 结果

`RICE_RP.tar.gz` 内只发现 PLINK `bed/bim/fam` 成员，没有发现独立 passport/variety metadata 表。已抽取小型 FAM 文件到 `data/interim/inventory/extracted_metadata/`。`Qmatrix-k9-3kRG.csv` 提供 B001-style ID 和 subpopulation proportion，可与 genotype FAM 做直接 overlap。

## 10. accession overlap 结果

pairwise overlap 已写入 `accession_overlap_matrix.tsv`。总体结论：SNP PLINK、indel PLINK、Qmatrix/RICE_RP FAM 的 B001-style IDs 具备较高直接对齐潜力；trait table 的 accession-like values 需要进一步判定字段含义和 ID mapping，不能直接假设已对齐。

## 11. chromosome naming 结果

FASTA/GFF3 使用 `NC_*` accession-style seqid。SNP VCF、SNP PLINK 和 indel PLINK 主要使用 numeric chromosome values，如 `1` 到 `12`。直接 join 会失败，必须在 Phase 4 前建立 chromosome naming mapping。当前发现 {len(chrom_mismatch)} 个 genotype source 存在 direct naming mismatch。

## 12. 主要风险

主要 high risk 包括 accession ID mismatch、trait/genotype overlap insufficient、unknown cannot be negative。另发现 {len(evidence_rows)} 个 raw weak evidence candidate，但尚未完成 provenance、coordinate build 和 checksum/manifest 补登记。完整风险见 `raw_data_risk_report.tsv`。

## 13. v0.1-mini 建议

v0.1-mini 建议优先使用 `core_v0.7.*` 做 SNP-only chr1 prototype；trait table 先只进入 accession mapping 审计，不作为 prediction target。v0.2-core 再纳入 `Nipponbare_indel.*`，形成 SNP+indel。详细建议见 `v0_1_mini_recommendation.md`。

## 14. 下一步

根据 inventory 结果，创建 Phase 4 prompt：确定 v0.1-mini 数据范围，并开始构建最小可运行 benchmark 输入表。
"""
    (REPORT_DIR / "raw_data_inventory_report.md").write_text(text, encoding="utf-8")


def main() -> int:
    ensure_dirs()
    sets = [
        read_id_set(INTERIM_DIR / "snp_samples.tsv", "sample_id", "snp_samples"),
        read_id_set(INTERIM_DIR / "indel_samples.tsv", "sample_id", "indel_samples"),
        read_id_set(INTERIM_DIR / "plink_samples.tsv", "sample_id", "plink_samples"),
        read_id_set(INTERIM_DIR / "trait_accessions.tsv", "accession_candidate", "trait_accessions"),
        read_id_set(INTERIM_DIR / "metadata_accessions.tsv", "accession_candidate", "metadata_accessions"),
    ]
    overlap_rows, summary_rows = compare_sets(sets)
    write_tsv(REPORT_DIR / "accession_overlap_matrix.tsv", overlap_rows, OVERLAP_FIELDS)
    write_tsv(INTERIM_DIR / "accession_set_summary.tsv", summary_rows, SUMMARY_FIELDS)
    chrom_rows = write_chromosome_report()
    write_risk_report(overlap_rows, chrom_rows)
    write_recommendation(overlap_rows)
    write_main_report(overlap_rows, chrom_rows)
    print(f"accession_sets={len(sets)}")
    print(f"overlap_pairs={len(overlap_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
