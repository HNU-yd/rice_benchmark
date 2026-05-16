# Accession ID Harmonization Statement

本项目以 3K Rice accession-level SNP/indel genotype 为 backbone，但 genotype、phenotype、passport 与测序元数据来自不同系统，分别使用 DNA/IRIS ID、stock ID、run accession、BioSample、passport accession 和材料名称等标识。这些字段描述对象不同，不能把任意单一字段直接作为跨系统 accession key。

因此，本项目将 accession 对齐定义为多源 ID harmonization，而不是简单 overlap。当前证据链为 genotype sample ID -> 3K DNA/IRIS ID -> stock name / SRA accession -> NCBI RunInfo / BioSample / Run -> Genesys passport / IRGC / accession name -> phenotype accession-like fields。每条映射均保留 source、match rule、confidence 和 manual review flag。

当前 genotype union samples 为 3024。`3K_list_sra_ids.txt` 和 NCBI RunInfo 均覆盖 3024 / 3024，Genesys MCPD 覆盖 2706 / 3024。phenotype 侧共有 2269 个 A/B high-confidence phenotype mappings、12 个 C-level name-only candidates 和 743 个 unmapped samples；phenotype confidence 为 A=0、B=2269、C=12、D=743。

A 级表示 phenotype 表中直接出现 genotype sample ID 或 3K DNA/IRIS ID；B 级表示通过硬 ID 或多源 ID 证据链建立高置信匹配；C 级表示只有 normalized stock name 或材料名称相似；D 级表示无可用 phenotype mapping。主 benchmark 只使用 A/B；C 级默认排除并进入人工审查；D 级不进入 trait-conditioned training/evaluation。

该策略用于降低 false genotype-trait pairing 风险。水稻材料存在别名、衍生系、近等基因系、重复 stock 和命名变体，名称相似不等于材料相同。C 级候选只有在人工复核中获得硬 ID 证据后，才可版本化升级为人工确认的 B 级。

743 个 D 级样本不被解释为 negative，也不表示 genotype 数据不可用。它们可用于 genotype-only 统计、MAF/LD 估计或 representation 分析，但因缺少可靠 trait_state，不进入 trait-conditioned benchmark。后续 `trait_value_table`、split 和 Task 1 instances 仅在 high-confidence accession subset 内构建。
