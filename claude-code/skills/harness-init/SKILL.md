---
name: harness-init
description: 在當前專案建立符合 harness-for-builders 規格的最小 harness（AGENTS.md／init／feature_list.json／.harness/）。骨架直接建，規格靠訪談——acceptance 與邊界不能猜。已有 harness 時接續現況，不重建。適用時機：使用者要在一個 repo 開始用 harness、或說「/harness-init」時。
---

# harness-init — 把這個 repo 變成 harness 專案

你的任務：在當前 repo 建立最小 harness。**骨架可以直接建，核心內容必須訪談**——acceptance 寫錯，整套 harness 就在驗證錯的東西。

## Step 0：偵測現況（先做，避免重建）

1. 確認在 git repo 內（不在就先問使用者要不要 `git init`）。
2. 檢查 `feature_list.json`、`AGENTS.md`／`CLAUDE.md`、`session-handoff.md` 是否已存在。
   - **已有 `feature_list.json`**：這是現成 harness 專案。讀它與 handoff，回報現況（幾條 failing、上次做到哪），**接續而不是重建**，本 skill 到此為止。
   - 部分存在：只補缺的，不覆寫既有內容。

## Step 1：建骨架（不用問）

1. `AGENTS.md`（repo 根目錄；若使用者的工具只認 `CLAUDE.md`，建 `CLAUDE.md` 為薄殼指向它）：

```markdown
# <專案名> — Agent 入口

## 怎麼跑
<init 指令與 smoke check——Step 2 訪談後填>

## 邊界
<可動／不可動的範圍——Step 2 訪談後填>

## 狀態
- 範圍與驗收：`feature_list.json`（acceptance 簽核後凍結；沒有 evidence 不得改 passing）
- 上次做到哪：`session-handoff.md`
```

2. `feature_list.json`：

```json
{
  "features": []
}
```

3. `.harness/` 目錄，並確保 `.gitignore` 含 `.harness/` 一行。
4. `init.*`：先看專案有沒有現成的環境恢復方式（`package.json` scripts、`Makefile`、`docker compose`）。**有就在 AGENTS.md 引用，不要再包一層**；什麼都沒有才寫一支最小 `init.sh`／`init.ps1`（裝依賴＋跑一條 smoke check）。

## Step 2：訪談（不准跳過、不准代填）

逐層問使用者，一次一組，答案寫回對應檔案：

1. **怎麼跑**：開發環境怎麼恢復？跑什麼確認活著？→ 填 AGENTS.md「怎麼跑」與 init。
2. **邊界**：哪些目錄／檔案不能動？有沒有不能碰的外部資源？→ 填 AGENTS.md「邊界」。
3. **第一條 feature**：現在最想做成的一件事是什麼？怎樣算做完？追問到 acceptance **自足可逐條判定**（執行方式＋明確判準，不引用外部文件）為止。寫成：

```json
{
  "id": "F1",
  "name": "<功能名>",
  "acceptance": [{"id": "A1", "check": "<執行方式 + 明確判準>"}],
  "status": "failing",
  "evidence": []
}
```

## Step 3：簽核與凍結

把 feature 條目呈給使用者確認。**明確同意後**才寫入 `feature_list.json`——寫入即視為凍結（若裝了 harness-trace hook，之後改 acceptance 會被 DENY，這是刻意機制）。

## Step 4：收尾

1. 回報建了什麼、第一條 feature 是什麼。
2. 提醒：開工時寫 `.harness/current_feature`（內容就是 feature id），trace 歸因靠它。
3. 其餘產物**痛點出現才加**：第一次沒做完就收工前建 `session-handoff.md`；新 agent 看不懂邊界才建 `docs/ARCHITECTURE.md`。不要現在預建。

## 鐵律

- 不覆寫使用者既有檔案；衝突時呈報，讓使用者決定。
- acceptance 與邊界**只能來自訪談**，你不得代答。使用者說「你幫我決定」時，給選項與建議，仍要他選。
- 完整方法與理由：https://github.com/RyanLeeYi/harness-for-builders
