#!/bin/bash
set -e
# 目標:全新 clone 或換機後,跑這一支就能到「可開發、可驗證」狀態

<安裝依賴>        # npm install / uv sync / pip install -r requirements.txt
<準備本地資料/env> # cp .env.example .env(如缺)
<煙霧測試>        # 啟動一次或跑最小測試,證明環境是活的

echo "init OK"
