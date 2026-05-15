# Download Scripts

这些脚本目前是 Phase 2A dry-run 下载模板。

默认运行不会下载任何文件，也不会创建 `data/raw/`。

只有后续 Phase 2B 人工确认 source 后，才能用 `--execute` 执行实际下载。当前脚本中的实际下载命令仍保持禁用状态或示例状态，防止误下载大文件。

所有下载必须先写入 `manifest/download_manifest.tsv`。

所有下载后文件必须计算 sha256，并登记到 `manifest/checksum_table.tsv`。

raw data 不进入 git。

使用示例：

```bash
bash scripts/download/download_raw_data.sh
bash scripts/download/download_reference.sh
bash scripts/download/download_3k_snp.sh
bash scripts/download/download_3k_indel.sh
bash scripts/download/download_traits.sh
bash scripts/download/download_annotation.sh
bash scripts/download/download_weak_evidence.sh
```

不要在 Phase 2A 使用 `--execute`。
