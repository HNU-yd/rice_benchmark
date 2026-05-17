# Stratified Residualization Feasibility Report

## Question

评估以下方案在当前 3K Rice benchmark 数据上的可行性：

> 性状值先做亚群、PC / kinship、来源批次、环境条件的残差化或分层标准化；负配对在同亚群、相近 PC、同一性状来源 / 环境内构造。

重点判断是否会出现 `subgroup x environment x batch x source` 多维分层后层太稀疏，导致无法训练或无法评价。

## Data Used

- Frozen v0.1 traits: 9 traits, all from `Data < 2007`.
- Frozen trait non-missing values: 18804 trait-accession rows.
- Unique accessions with any frozen non-missing trait: 2096.
- Available population covariates: Qmatrix subgroup, sample-level PC1-PC12, kinship matrix.
- Available environment proxy: `CROPYEAR` only; no full site / location / season table.
- Available source / origin proxies: `source_sheet`, country origin, Genesys `SUBTAXA`.
- Available sequencing batch metadata: RunInfo / LibraryName, but not a clean one-row phenotype measurement batch.

## Key Counts

| stratification | strata across 9 traits | median stratum size | strata < 20 | feasibility |
|---|---:|---:|---:|---|
| trait x subgroup | 81 | 193 | 0 / 81 | feasible |
| trait x source_sheet x subgroup | 81 | 193 | 0 / 81 | feasible; source_sheet is constant for frozen traits |
| trait x subgroup x CROPYEAR, missing as level | 1054 | 3 | 928 / 1054 | not feasible as hard residualization strata |
| trait x subgroup x country | 1958 | 2 | 1707 / 1958 | not feasible as hard strata |
| trait x subgroup x SUBTAXA | 305 | 7 | 215 / 305 | mostly too sparse and partly redundant with subgroup |
| trait x subgroup x CROPYEAR x country | 4055 | 1 | 3841 / 4055 | infeasible |
| trait x subgroup x CROPYEAR x SUBTAXA | 1452 | 2 | 1317 / 1452 | infeasible |

`CROPYEAR` coverage is weak: only 5257 / 18804 frozen trait rows have known year, about 28.0%. Per frozen trait, known-year coverage is only 27.4%-28.1%.

## Negative Pair Candidate Pools

For matched negative or decoy construction, row-weighted candidate pools are less severe than stratum counts because the missing-year stratum is large. Still, hard multidimensional matching quickly removes candidates.

| hard constraints inside each trait | median candidate pool | rows with pool < 10 | rows with pool < 20 | interpretation |
|---|---:|---:|---:|---|
| subgroup | 295 | 0.0% | 0.0% | safe |
| subgroup + CROPYEAR, missing as level | 186 | 15.6% | 21.0% | usable only if missing-year is allowed as a coarse unknown-env bucket |
| subgroup + country | 53 | 18.8% | 29.5% | borderline; exact country is too strict for many accessions |
| subgroup + CROPYEAR + country | 19 | 40.2% | 51.1% | not safe |
| subgroup + CROPYEAR + SUBTAXA | 120 | 19.6% | 25.9% | better than country but still sparse |

Known-year-only matching is much worse:

| hard constraints, known `CROPYEAR` only | rows retained | median candidate pool | rows with pool < 10 | rows with pool < 20 |
|---|---:|---:|---:|---:|
| subgroup + CROPYEAR | 5257 | 8 | 55.8% | 75.1% |
| subgroup + CROPYEAR + country | 5257 | 2 | 82.2% | 89.7% |
| subgroup + CROPYEAR + SUBTAXA | 5257 | 8 | 58.0% | 76.3% |

## PC And Batch Findings

- PC must not be converted into exact discrete strata. Among 2096 accessions, rounding PC1-PC5 to 4 decimals creates 2094 levels, with 2092 singleton levels.
- PC is feasible as a continuous covariate or nearest-neighbor distance constraint inside broader strata.
- Exact `library_names` is unusable as a hard batch stratum: 2096 / 2096 accessions have unique values among frozen-trait accessions.
- Broad sequencing metadata such as CenterName, Platform, and Model is mostly constant in current RunInfo, so it does not provide meaningful stratification for trait residualization.

## Assessment

Strict hard stratification by `subgroup x PC-bin x environment x batch x source` is not feasible. It will create many singleton or near-singleton layers and will make both residualization and within-layer evaluation unstable.

The feasible version is hierarchical:

1. Hard constraints:
   - same `trait_id`;
   - same `source_sheet` when multiple sheets are used;
   - same broad subgroup, or at least subgroup-balanced sampling.
2. Continuous / soft constraints:
   - PC distance by k-nearest-neighbor matching inside subgroup;
   - kinship as a covariance term for GWAS / residualization, not a hard stratum;
   - country / SUBTAXA as balance diagnostics or coarse covariates, not exact strata.
3. Environment handling:
   - use `CROPYEAR` only when known, but do not require exact year globally;
   - keep missing `CROPYEAR` as a distinct unknown-env status, not as proof of same environment;
   - do not claim full environment adjustment because site / location / season are absent.
4. Batch handling:
   - do not hard-match exact sequencing `LibraryName` or Run;
   - use genotype missingness / broad run metadata for QC diagnostics if needed.

## Recommendation

For the current v0.1 benchmark, use subgroup + PC-nearest matching as the main anti-confounding control. Treat `CROPYEAR`, country, SUBTAXA and batch as reporting / balance fields or soft penalties. Exact multiway hard matching should be avoided except for small targeted audits with minimum layer-size thresholds.

Suggested minimum thresholds:

- residualization or per-stratum standardization: at least 50 accessions per trait stratum, preferably 100+;
- matched negative / decoy sampling: at least 10-20 eligible candidates per accession after hard constraints;
- per-stratum evaluation reporting: hide or pool strata below a predeclared minimum, rather than reporting unstable metrics.

This keeps the core correction scientifically useful without fragmenting the data into non-trainable and non-evaluable layers.
