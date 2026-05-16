# 外部水稻数据库搜集策略

## 为什么现在搜集其他数据库

当前 3K Rice genotype、phenotype、reference、annotation、Qmatrix、Oryzabase、Q-TARO 和 accession mapping 原始来源已经基本落地。下一步要构建 `accession_mapping_master.tsv` 和最小 benchmark 输入表，因此需要提前明确哪些外部数据库用于补 gene ID、trait-gene evidence、QTL evidence、functional annotation 和解释层。

## 为什么不扩成多数据集 genotype benchmark

第一版 benchmark 的主位数据仍然是 3K Rice accession-level SNP/indel genotype backbone。RiceVarMap、MBKbase、Dataverse 或其他数据库的 genotype / phenotype 不应直接混入主 backbone，否则会引入 panel 差异、coordinate build 差异、trait leakage 和 label provenance 混乱。

## Backbone 与 knowledge layer 的区别

3K Rice genotype backbone 提供 sample、SNP/indel 和 reference window 的主坐标系统。外部数据库只作为 knowledge layer：补充 gene ID mapping、function、ontology、known genes、QTL、external association evidence 和 candidate gene explanation。外部 evidence 只能作为 `weak localization evidence`，不能作为 `causal ground truth`。

## 数据库补充内容

- RAP-DB：IRGSP-1.0 gene annotation、RAP ID、function、RAP/MSU/RefSeq bridge。
- funRiceGenes：functionally characterized rice genes、cloned gene evidence、literature provenance。
- Oryzabase / Q-TARO：当前已有，继续整理为 Tier 1 / Tier 4 weak evidence 候选。
- RiceVarMap / RiceVarMap2：外部 variant annotation、allele frequency 和 candidate variant explanation。
- MSU / Ensembl Plants / Gramene：MSU/RAP/Ensembl/RefSeq cross-reference、GO 和 ontology。
- MBKbase-rice：germplasm、known allele、expression/multi-omics explanation。
- Lin et al. 2020 PNAS：hybrid yield / heterosis case study evidence。
- Sanciangco Dataverse：external GWAS evidence metadata，当前 raw 大文件 defer。

## 下载优先级

第一优先：accession ID mapping files、funRiceGenes、RAP-DB gene annotation / mapping、Oryzabase / Q-TARO 已有整理。当前清单：RAP-DB,funRiceGenes,Oryzabase,Q-TARO。

第二优先：RiceVarMap / RiceVarMap2 variation annotation、MSU / Gramene / Ensembl ID mapping。当前清单：RiceVarMap / RiceVarMap2,Rice Genome Annotation Project / MSU,Ensembl Plants / Gramene,MBKbase-rice,Lin et al. 2020 PNAS。

第三优先：MBKbase known allele / expression、Lin2020 PNAS hybrid-yield external evidence。

暂缓：Sanciangco Harvard Dataverse，以及 pan-genome / SV / CNV 数据和 multi-species 数据。

## 当前不进入第一版的数据

SV、PAV、CNV、pan-genome 专用数据、多物种 genotype benchmark、外部 phenotype prediction target、大规模 raw reads、FASTQ、BAM、CRAM、SRA 下载都不进入第一版主流程。

## 下一步下载顺序

1. 先完成 `accession_mapping_master.tsv`，固定 accession/source/provenance 字段。
2. metadata check RAP-DB 和 funRiceGenes，优先下载小型 gene/function/ID mapping 表。
3. metadata check MSU、Gramene、Ensembl Plants 的 ID cross-reference。
4. metadata check RiceVarMap/RiceVarMap2 的 annotation export，明确不导入其 genotype matrix。
5. Dataverse GWAS 大文件继续 defer；v0.2-core 优先自跑 3K GWAS。
