# Changelog

本專案版本紀錄。格式:新的在上。

## v1.1（2026-08-06）

- `feature_list.json` 模板（zh/en）：每個 feature 新增 `prerequisites` 欄位，申報「必須先 passing 才能實作或驗證」的相依 feature id，沒有相依為空陣列。
- `architecture`（zh/en）：新增兩節 —— 為什麼 feature 要申報 prerequisites（答出「下一條做哪個」與「哪兩條能平行」、平行三條件、fail-closed 原則）、為什麼大工作要先切 envelope 再談 slice（slice 就是 feature、共用約束層 `outcome`/`constraints`/`non_goals`、先簽 envelope 再逐條核准 slice、schema 維持平坦陣列）。
- `setup-guide`（zh/en）：Step 3 補上 `prerequisites` 的填寫時機，加大工作先切 envelope 的提示。
- `README`（zh/en）：關鍵名詞與 L1 建置圖補上 `prerequisites` 的行為說明。

## v1.0.1（2026-07-31）

- `architecture`（zh/en）：凍結 acceptance 的 hook 進階註記補上實作教訓——攔截條件要綁被保護的檔案而非工具型別，判準要精確到「值有沒有被動」。來源是上游 harness 實測到的靜默繞過。

## v1.0（2026-07-24）

首次發佈。

- 三級漸進 harness（L1 最小 → L2 交接 → L3 回饋驗證）
- 操作檔範本：`CLAUDE.md`、`init.sh`、`feature_list.json`、`session-handoff.md`、`ARCHITECTURE.md`
- 文件範本：`PLAN`、`PRD`、`DEVLOG`、`DECISIONS`、`CODING-RULES`
- 四份指南：README（哲學）、setup-guide（一步步）、architecture（設計取捨）、optimization-guide（context 瘦身）
- 雙語 zh / en
