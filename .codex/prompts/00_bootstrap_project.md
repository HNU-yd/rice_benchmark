# 00_bootstrap_project.md

你现在要为一个新的科研工程仓库建立 Phase 0 项目骨架。

项目名称：3K Rice SNP/indel Trait-conditioned Localization Benchmark

你的任务不是写模型，不是下载数据，不是处理数据，不是实现 schema，也不是写评价指标。  
你的任务只限于：建立仓库治理结构、项目边界文档、配置文件模板和空目录骨架。

---

## 1. 项目最高约束

本项目第一版严格限定为：

1. 主位数据：3K Rice。
2. 变异范围：SNP + indel。
3. 主任务：Task 1，trait-conditioned SNP/indel localization。
4. 第二任务：Task 2，reference-conditioned candidate SNP/indel edit hypothesis generation，仅作为 supplementary / application demo。
5. 第一版不做 phenotype prediction。
6. 第一版不预测 accession phenotype value。
7. 第一版不做 trait classification。
8. 第一版不纳入 SV、PAV、CNV。
9. 第一版不使用 pan-reference、multi-reference、五参考 anchor block、branch chunk、path state。
10. 第一版不引入多物种 benchmark。
11. 第一版不重新预训练 genome foundation model。
12. 第一版可使用 frozen Evo2 encoder，但本 prompt 不需要实现任何 Evo2 相关代码。
13. GWAS、QTL、known trait gene、LD block、credible interval、trait-gene annotation 都只能作为 weak localization evidence。
14. 这些 evidence 不能被写成 causal ground truth。
15. unknown / unlabeled variants 不能默认作为 negative。
16. matched decoy 是后续 benchmark 的必要组成部分，但本 prompt 不实现 decoy 构建。
17. 所有后续 split 必须固化为文件，不能在训练时动态重切。
18. 所有后续模型和 baseline 必须输出统一格式的 score table。
19. 修改 Python 代码时，后续必须同步更新 README 或对应 docs。本 prompt 先建立这一规则。

---

## 2. 本次任务范围

你只需要完成 Phase 0：bootstrap project。

允许创建：

```text
AGENTS.md
README.md
docs/
configs/
scripts/
src/
tests/
.codex/
````

允许创建配置模板和文档模板。

禁止在本次任务中做以下事情：

```text
不要下载任何数据
不要访问网络
不要写 VCF/BCF/FASTA/GFF 处理逻辑
不要实现 pandas/polars 数据 schema
不要实现 benchmark builder
不要实现 split
不要实现 evaluator
不要实现 baseline
不要实现 model
不要实现 Evo2 相关代码
不要实现 Task 2
不要生成 toy data
不要创建大文件
```

---

## 3. 需要创建的目录结构

请在当前仓库根目录下创建如下结构：

```text
.
├── AGENTS.md
├── README.md
├── configs/
│   ├── paths.yaml
│   └── sources.yaml
├── docs/
│   ├── project_scope.md
│   ├── data_acquisition_plan.md
│   ├── benchmark_scope.md
│   ├── codex_workflow.md
│   └── review_checklist.md
├── scripts/
│   ├── download/
│   │   └── .gitkeep
│   ├── inspect/
│   │   └── .gitkeep
│   └── utils/
│       └── .gitkeep
├── src/
│   └── ricebench/
│       └── __init__.py
├── tests/
│   └── .gitkeep
└── .codex/
    └── prompts/
        └── .gitkeep
```

不要删除已有文件。
如果文件已经存在，请在不破坏已有内容的前提下补充必要内容。

---

## 4. AGENTS.md 内容要求

`AGENTS.md` 是后续所有 Codex 任务的最高工程约束文件。

请写入以下内容：

### 4.1 Project Role

说明本仓库用于构建：

```text
3K Rice SNP/indel trait-conditioned localization benchmark
```

### 4.2 Hard Scientific Boundaries

必须明确：

```text
The primary benchmark is 3K Rice only.
The first version supports SNP and indel only.
Task 1 is trait-conditioned SNP/indel localization.
Task 2 is only supplementary.
This project must not become phenotype prediction.
This project must not become trait classification.
This project must not treat weak evidence as causal ground truth.
This project must not treat unknown variants as true negatives.
This project must not introduce SV/PAV/CNV/pan-reference/multi-reference/multi-species/pretraining in v1.
```

### 4.3 Engineering Rules

必须明确：

```text
Raw data must never be overwritten.
All downloaded files must be registered in manifest files.
Every script must have a clear input, output, and usage example.
Any data-processing logic must be reproducible from command line.
Every generated benchmark table must have a documented schema.
All train/val/test splits must be materialized as files.
No dynamic random splitting inside training code.
All models and baselines must write standardized output tables.
When Python code is added or changed, README or docs must be updated.
```

### 4.4 Codex Behavior Rules

必须明确：

```text
Do not broaden the scientific scope.
Do not silently add new tasks.
Do not introduce phenotype prediction heads.
Do not implement unrequested modules.
Do not assume missing data are negative labels.
Do not use GWAS/QTL/known genes as causal ground truth.
Before modifying many files, inspect the repository structure.
After completing a task, summarize changed files and remaining risks.
```

---

## 5. README.md 内容要求

`README.md` 写成项目首页，不要太长，但必须包含：

1. Project title。
2. One-paragraph summary。
3. Current scope。
4. Explicit non-goals。
5. Planned pipeline。
6. Current repository status。
7. Directory overview。
8. Codex workflow note。

其中 Planned pipeline 必须是：

```text
Phase 0: repository governance and project constraints
Phase 1: 3K Rice data source inventory
Phase 2: raw data download, checksum, and manifest registration
Phase 3: raw data inventory and accession/trait/variant compatibility audit
Phase 4: decide v0.1-mini / v0.2-core / v1.0-full benchmark scope
Phase 5: schema and benchmark table construction
Phase 6: data normalization and window construction
Phase 7: weak evidence and matched decoy construction
Phase 8: frozen split generation
Phase 9: evaluator and baseline implementation
Phase 10: frozen Evo2 feature precomputation
Phase 11: Task 1 model training and inference
Phase 12: ablation, negative controls, and Task 2 supplementary demo
```

README 必须明确：当前 Phase 0 不包含数据下载、schema、模型或评价实现。

---

## 6. docs/project_scope.md 内容要求

写清楚项目范围：

```text
主位数据：3K Rice
变异范围：SNP + indel
主任务：trait-conditioned SNP/indel localization
第二任务：reference-conditioned candidate SNP/indel edit hypothesis generation
核心输出：
  variant-level score
  window-level signal map
  candidate significant regions
  fine SNP/indel loci
```

同时写清楚 non-goals：

```text
phenotype prediction
trait classification
causal/non-causal strong supervised classification
SV/PAV/CNV
pan-reference
multi-reference
multi-species benchmark
genome model pretraining
```

---

## 7. docs/data_acquisition_plan.md 内容要求

这个文档只写计划，不写下载脚本。

必须列出后续 Phase 1 需要确认的数据类别：

```text
1. 3K Rice accession metadata
2. 3K Rice SNP genotype data
3. 3K Rice indel genotype data
4. Nipponbare / IRGSP reference genome FASTA
5. gene annotation / functional annotation
6. trait / phenotype tables used only to construct trait_state
7. weak localization evidence:
   - known trait genes / cloned genes
   - GWAS lead SNPs / significant SNPs
   - QTL intervals
   - LD blocks / credible intervals if available
   - trait-gene annotation / pathway evidence
```

必须写明：

```text
Downloading starts only after source_inventory.tsv is created and reviewed.
Raw data must be stored under data/raw/ in later phases.
Each downloaded file must be registered with URL/access method, source version, checksum, file size, and download time.
```

注意：本 prompt 不创建 data/raw/，除非仓库已经有 data 目录。Phase 0 只写文档和配置模板。

---

## 8. docs/benchmark_scope.md 内容要求

写清楚 benchmark 逻辑：

```text
The benchmark will be built only after raw data inventory confirms what is available in 3K Rice.
Schema design should follow actual downloadable data, not idealized assumptions.
Task 1 input unit: trait_state + accession + reference_window.
Task 1 output: variant-level score, window-level signal map, candidate region, fine SNP/indel locus.
Task 2 is supplementary and must hide accession genotype during input.
```

强调：

```text
unknown != negative
weak evidence != causal ground truth
matched decoy is required in the final benchmark
splits must be frozen
```

---

## 9. docs/codex_workflow.md 内容要求

说明后续 Codex 每次任务应该像小 PR：

每次任务必须报告：

```text
Goal
Files changed
Commands run
Tests or checks run
Outputs generated
Known limitations
Whether README/docs were updated
```

说明 Codex 不应该一次性实现大模块。

---

## 10. docs/review_checklist.md 内容要求

写一份审阅清单，用于每次 Codex 完成任务后检查。

至少包含：

```text
是否违反 3K Rice only？
是否违反 SNP + indel only？
是否把任务写成 phenotype prediction？
是否引入 trait classification？
是否把 weak evidence 写成 causal ground truth？
是否把 unknown 当 negative？
是否跳过 source inventory 直接假设数据格式？
是否覆盖 raw data？
是否动态随机切 split？
是否新增代码但没有更新 README/docs？
是否新增脚本但没有 usage example？
```

---

## 11. configs/paths.yaml 内容要求

创建一个模板配置，不要绑定具体机器路径。

内容示例：

```yaml
project:
  name: rice_trait_locus_benchmark
  version: phase0

paths:
  root: "."
  data_raw: "data/raw"
  data_interim: "data/interim"
  data_processed: "data/processed"
  manifest: "manifest"
  reports: "reports"
  logs: "logs"

notes:
  - "This file is a template created in Phase 0."
  - "Do not assume these directories contain data yet."
```

本次不需要创建 data/raw 等目录，只在配置里预留。

---

## 12. configs/sources.yaml 内容要求

创建一个数据源模板，不填虚假 URL。

内容示例：

```yaml
sources:
  accession_metadata:
    required: true
    status: "to_be_identified"
    notes: "3K Rice accession metadata and ID mapping."

  snp_genotype:
    required: true
    status: "to_be_identified"
    notes: "3K Rice accession-level SNP genotype data."

  indel_genotype:
    required: true
    status: "to_be_identified"
    notes: "3K Rice accession-level indel genotype data."

  reference_genome:
    required: true
    status: "to_be_identified"
    notes: "Nipponbare / IRGSP reference genome FASTA."

  gene_annotation:
    required: true
    status: "to_be_identified"
    notes: "GFF3/GTF and functional annotation."

  trait_table:
    required: true
    status: "to_be_identified"
    notes: "Trait values used to construct trait_state, not phenotype prediction targets."

  weak_evidence:
    required: true
    status: "to_be_identified"
    notes: "GWAS/QTL/known gene evidence used as weak localization evidence."
```

---

## 13. src/ricebench/**init**.py 内容要求

只写最小包初始化信息：

```python
"""3K Rice SNP/indel trait-conditioned localization benchmark."""

__version__ = "0.0.0-phase0"
```

不要创建其它 Python 模块。

---

## 14. 执行检查

完成后请运行：

```bash
find . -maxdepth 4 -type f | sort
```

如果当前环境支持 `tree`，也可以运行：

```bash
tree -a -I ".git"
```

不要运行任何下载命令。

---

## 15. 最终回复要求

完成后，请在回复中报告：

```text
1. Created / updated files
2. Commands run
3. What was intentionally not implemented
4. Risks or next steps
```

其中 next step 应该是：

```text
Create 01_data_source_inventory.md to identify 3K Rice data sources before any download or schema implementation.
```

现在开始执行 Phase 0 bootstrap。

