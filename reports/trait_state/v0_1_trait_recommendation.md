# v0.1 Trait Recommendation

本报告基于 A/B high-confidence accession subset 生成。trait_state 是模型条件输入，不是 phenotype prediction label。

## 推荐优先进入 v0.1 的 trait

`data_lt_2007__blco_rev_veg`、`data_lt_2007__cco_rev_veg`、`data_lt_2007__ligco_rev_veg`、`data_lt_2007__apco_rev_repro`、`data_lt_2007__auco_rev_veg`、`data_lt_2007__blpub_veg`、`data_lt_2007__blsco_rev_veg`、`data_lt_2007__inco_rev_repro`、`data_lt_2007__pex_repro`、`data_lt_2007__cuan_repro`、`data_lt_2007__cust_repro`、`data_lt_2007__lpco_rev_post`、`data_lt_2007__spkf`、`data_lt_2007__cudi_code_repro`、`data_lt_2007__lsen`、`data_lt_2007__pty`、`data_lt_2007__fla_repro`、`data_lt_2007__pth`、`data_lt_2007__scco_rev`、`data_lt_2007__endo`、`data_lt_2007__sllt_code`、`data_lt_2007__cuno_code_repro`、`data_lt_2007__llt_code`、`data_lt_2007__cult_code_repro`、`data_lt_2007__sdht_code`、`data_lt_2007__plt_code_post`、`data_lt_2007__slco_rev`、`data_lt_2007__la`、`data_lt_2007__lppub`、`data_lt_2007__pa_repro`、`data_lt_2007__ligsh`、`data_lt_2007__psh`、`data_lt_2007__second_br_repro`、`data_lt_2007__noco_rev`。

## 暂缓 trait

`data_lt_2007__apco_rev_post`、`data_lt_2007__awpr_repro`、`data_lt_2007__awco_rev`、`data_gt_2007__apco_rev_post`、`data_gt_2007__apco_rev_repro`、`data_gt_2007__apsh`、`data_gt_2007__auco_rev_veg`、`data_gt_2007__blco_rev_veg`、`data_gt_2007__blpub_veg`、`data_gt_2007__blsco_rev_veg`、`data_gt_2007__cco_rev_veg`、`data_gt_2007__cuan_repro`、`data_gt_2007__cust_repro`、`data_gt_2007__fla_erepro`、`data_gt_2007__fla_repro`、`data_gt_2007__inco_rev_repro`、`data_gt_2007__la`、`data_gt_2007__ligco_rev_veg`、`data_gt_2007__ligsh`、`data_gt_2007__lpco_rev_post`、`data_gt_2007__lppub`、`data_gt_2007__lsen`、`data_gt_2007__noco_rev`、`data_gt_2007__pa_repro`、`data_gt_2007__pex_repro`、`data_gt_2007__psh`、`data_gt_2007__pth`、`data_gt_2007__pty`、`data_gt_2007__slco_rev`、`data_gt_2007__sllt_code`、`data_gt_2007__spkf`、`data_gt_2007__second_br_repro`、`data_gt_2007__awco_rev`、`data_gt_2007__awdist`、`data_gt_2007__awco_lrev`、`phenotype_data__apco_rev_repro`、`phenotype_data__auco_rev_veg`、`phenotype_data__awco_rev`、`phenotype_data__blco_rev_veg`、`phenotype_data__blpub_veg`。

另有 48 个未在此处展开，详见 TSV。

## 不能作为 trait 的 metadata 字段

`data_gt_2007__cropyear`、`data_gt_2007__name`、`data_gt_2007__stock_id`、`data_lt_2007__cropyear`、`data_lt_2007__name`、`data_lt_2007__stock_id`、`phenotype_data__cropyear`、`phenotype_data__gs_accno`、`phenotype_data__name`、`phenotype_data__seqno`、`phenotype_data__source_accno`、`phenotype_data__stock_id`。

## 使用口径

- P0：连续性状，非缺失样本数 >= 1000。
- P1：非缺失样本数 >= 500，且为连续性状或清晰 categorical / binary trait。
- P2：样本数较少、metadata-like、类别过多或暂不适合进入 v0.1-mini。
- C/D 级 accession mapping 样本不进入本推荐。
