# v0.1-mini Chr1 SNP-only Input Skeleton Report

## 本次任务目标

本阶段补齐 05C 所需的 chr1 SNP-only 输入骨架，包括 chromosome map、chr1 SNP variant table、chr1 sliding window table、variant-window mapping 和 chr1 weak evidence audit。本阶段不构建 Task 1 instances，不训练模型，不构建 evaluator，不做 phenotype prediction。

## 为什么要补这个前置步骤

05C 构建 Task 1 instances 依赖固定的 variant/window/evidence 输入表。上一轮 05C 因这些输入不存在而停止，因此本阶段只补齐前置输入。

## Chromosome Map 结果

- chromosome map 行数：12。
- chr1 固定映射为 `1 -> NC_029256.1`。

## chr1 SNP Variant Table 结果

- chr1 SNP 数：42466。
- 位置范围：1178 - 43255617。
- PLINK BIM 的 allele1 / allele2 未伪装为 ref / alt，后续仍需 allele orientation validation。

## chr1 Window Table 结果

- chr1 reference length：43270923。
- window size：100000，stride：50000。
- chr1 window 数：865。

## Variant-window Mapping 结果

- variant-window mapping 行数：84886。
- 滑动窗口重叠，因此同一个 SNP 可映射到多个 window。

## Weak Evidence chr1 Audit 结果

- chr1 weak evidence candidates：543。
- 有坐标 candidates：42。
- 无坐标 candidates：501。

## 哪些 weak evidence 有坐标

- Q-TARO chr1 interval candidates 有坐标：42。坐标 build 仍标记为 uncertain。

## 哪些 weak evidence 只有 gene/trait 语义，没有坐标

- Oryzabase chr1 gene/trait candidates 无坐标：501。当前只保留 chromosome、gene ID / symbol 和 trait 语义。

## 为什么不把 weak evidence 当作 causal ground truth

Oryzabase known/cloned genes 与 Q-TARO QTL interval 只能提供候选区域或语义相关线索，不能证明具体 SNP 为 causal variant。本阶段输出只用于 weak localization evidence。

## 为什么 unknown 不是 negative

没有 overlap evidence 的 variant/window 只是未标注或未覆盖，不能解释为 true negative。后续 05C 必须保留 `unknown_unlabeled`。

## 是否可以重新执行 05C

- 05C 必需输入是否齐备：yes。

## 结论

本任务只构建 05C 的前置输入表。如果所有必需表都存在，则可以重新执行 `05c_build_chr1_snp_task1_instances.md`。
