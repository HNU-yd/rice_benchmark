#!/usr/bin/env bash
set -euo pipefail

mkdir -p \
  data/raw/external_knowledge/rapdb \
  data/raw/external_knowledge/funricegenes \
  data/raw/external_knowledge/msu_rgAP \
  data/interim/external_knowledge/rapdb \
  data/interim/external_knowledge/funricegenes \
  data/interim/external_knowledge/msu_rgAP \
  reports/external_knowledge/rapdb \
  reports/external_knowledge/funricegenes \
  reports/external_knowledge/msu_rgAP \
  reports/external_knowledge/summary

python scripts/external_knowledge/collect_rapdb.py
python scripts/external_knowledge/collect_funricegenes.py
python scripts/external_knowledge/collect_msu_rgAP.py
python scripts/external_knowledge/inspect_external_knowledge_files.py
