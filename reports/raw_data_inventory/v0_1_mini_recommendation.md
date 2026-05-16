# v0.1-mini 数据范围建议

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
