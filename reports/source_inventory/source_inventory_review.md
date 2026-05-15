# Source Inventory 审阅报告

## 1. 审阅目标

本报告审阅 Phase 1 生成的 `manifest/source_inventory.tsv`、`manifest/source_inventory.schema.tsv`、`configs/sources.yaml`、`docs/data_source_inventory.md` 和 `docs/data_download_risk_notes.md`。

审阅目标是确认当前 source inventory 是否覆盖 3K Rice SNP/indel trait-conditioned localization benchmark 的必要数据源，识别 P0 数据源进入 Phase 2 前的人工确认项，并检查是否存在违反项目边界的来源。

本报告不下载 raw data，不解析 VCF/BCF/FASTA/GFF，不设计最终 schema，不实现 benchmark builder、split、evaluator、baseline、model 或 Evo2 代码。

## 2. 当前 source_inventory 行数

`manifest/source_inventory.tsv` 当前包含 21 条数据源记录，不含表头。

## 3. 已覆盖的数据类别

当前已覆盖 7 类必需 `data_category`：

- `accession_metadata`
- `snp_genotype`
- `indel_genotype`
- `reference_genome`
- `gene_annotation`
- `trait_table`
- `weak_evidence`

覆盖范围满足 Phase 1 inventory 的最低要求。

## 4. P0 数据源覆盖情况

P0 数据源已覆盖：

- `accession_metadata`：1 条 P0 记录。
- `snp_genotype`：1 条 P0 记录。
- `indel_genotype`：2 条 P0 记录。
- `reference_genome`：1 条 P0 记录。
- `trait_table`：2 条 P0 记录。
- `weak_evidence`：3 条 P0 记录。

`gene_annotation` 当前为 P1，符合其主要用于 explanation、candidate_gene_ranking_table 和 matched decoy matching features 的定位。

## 5. SNP genotype 数据源风险

SNP genotype 的 P0 记录是 `SRC_3K_SNP_GENOTYPE_001`，指向 AWS / SNP-Seek 相关 S3 prefix，状态为 `partially_verified`，风险等级为 `high`。

主要风险：

- 具体 file list、release、chromosome partitioning 和 checksum 尚未冻结。
- 需要确认是否为 accession-level genotype。
- 需要确认 reference build 是否为 Nipponbare / IRGSP-1.0 或可无损映射。
- 需要确认 accession list 是否能与 accession metadata、indel genotype 和 trait table 对齐。
- 文件体量可能较大，Phase 2 必须设计 checksum 和断点续传策略。

## 6. indel genotype 数据源风险

indel genotype 有两条 P0 记录：

- `SRC_3K_INDEL_GENOTYPE_001`：SNP-Seek short indel genotype dataset。
- `SRC_3K_INDEL_GENOTYPE_002`：3K RG accession-level VCF files。

主要风险：

- SNP-Seek 原入口当前依赖 mirror 或恢复后的正式入口，exact indel bulk download path 未确认。
- accession-level indel genotype 是否与 SNP genotype 使用同一 accession ID 仍需核验。
- indel ref / alt allele 表示、normalization 规则和 insertion / deletion anchor convention 需要在 schema 前确认。
- 如果后续用于 Task 2 hidden genotype evaluation，必须确认输入阶段不会泄漏 accession genotype。

## 7. accession metadata 对齐风险

accession metadata 的 P0 记录来自 SNP-Seek / IRIC，当前为 `partially_verified` 且风险等级为 `high`。

主要风险：

- SNP-Seek 原入口临时离线，mirror 的 export 行为和可复现性需要确认。
- accession_id、variety name、sample_id、IRGC/IRIS 编号可能存在别名或版本差异。
- 需要分别与 SNP genotype、indel genotype 和 trait table 建立 crosswalk。
- split construction 不能在训练时动态猜测 accession 对齐。

## 8. trait table 对齐风险

trait table 有两条 P0 记录：

- `SRC_TRAIT_TABLE_001`：SNP-Seek / IRGCIS 3K passport and phenotype data。
- `SRC_TRAIT_TABLE_003`：3kRG phenotype spreadsheet。

主要风险：

- `SRC_TRAIT_TABLE_003` 是直接数据文件 URL，Phase 1 未下载，Phase 2 前必须人工确认版本、权限、checksum 和记录结构。
- trait / phenotype table 只能用于构建 trait_state，不能作为 `phenotype prediction` target。
- 每个 trait 的 accession overlap、trait unit、重复测量、环境信息和 high/low 或 case/control 分组可行性尚未确认。
- 与 genotype accession 的交集不足可能影响 v0.1-mini / v0.2-core / v1.0-full scope 决策。

## 9. reference build 一致性风险

reference genome 的 P0 记录是 `SRC_REF_IRGSP_FASTA_001`，候选为 NCBI Datasets GCA_001433935.1 / IRGSP-1.0。

主要风险：

- FASTA package、chromosome naming convention、sequence checksum 和 assembly accession 需要在 Phase 2 固化。
- SNP genotype、indel genotype、gene annotation、QTL intervals 和 GWAS lead SNPs 必须统一到同一 reference build。
- RAP-DB、MSU、NCBI、Ensembl Plants 的 gene ID 和 coordinate convention 可能不同，需要后续 crosswalk。

## 10. weak evidence 泄漏风险

weak evidence 已登记 known trait genes、Q-TARO QTL、literature-curated GWAS lead SNPs、LD blocks / credible intervals、RiceVarMap 和 pathway annotation 候选来源。

主要风险：

- GWAS/QTL/known genes 只能作为 `weak localization evidence`，不能写成 `causal ground truth`。
- Literature-curated GWAS lead SNPs 的 panel、trait 和 phenotype 定义可能与 benchmark evaluation target 重叠，存在 evidence leakage 风险。
- QTL intervals 和 LD blocks 的 coordinate build 可能需要 remapping。
- unknown / unlabeled variants 不能默认作为 negative。

## 11. excluded_for_v1 数据源检查

当前 inventory 包含 `SRC_EXCLUDED_PAV_SV_001`，其 `verification_status = excluded_for_v1`，`exclude_from_v1 = yes`。

该记录用于提醒 3K rice SV/PAV/pan-genome resources 属于第一版范围外内容。它不应进入 v1 主 benchmark，也不应影响 SNP + indel only 的主任务设计。

## 12. Phase 2 下载前必须人工确认的问题

进入 Phase 2 下载前必须逐项确认：

- 每个 P0 source 的 URL、S3 path、database export 或 paper supplement 是否可访问。
- 每个 P0 source 的 release、file name、file size、checksum 和 download time 记录方法。
- SNP genotype 与 indel genotype 是否使用同一 reference build 和 accession ID。
- accession metadata 是否包含 accession_id、variety name、sample_id、subpopulation、country/region 和 sample quality。
- trait table 与 genotype accession 的 overlap、trait unit、重复测量和环境信息。
- reference genome FASTA 的 exact package、chromosome naming convention、FAI/dict 生成规则和 checksum。
- weak evidence 的 trait-specific provenance、coordinate build、panel overlap 和 leakage flag。
- raw data 路径是否被 `.gitignore` 排除，下载文件是否只能进入 `data/raw/` 和 manifest。

## 13. 是否允许进入 Phase 2 的建议

可以进入 Phase 2 下载脚本准备，但 P0 数据源的 URL / access method / reference build / accession ID mapping 仍需在下载前逐项确认。

Phase 2 的第一步不应直接下载大文件，而应先创建下载计划 prompt、补齐 `download_manifest.tsv` / `checksum_table.tsv` 设计、确认 `.gitignore` 和 raw data 防误提交规则。

