# Changelog

本專案版本紀錄。格式:新的在上。

## v1.3（2026-08-18）

- `setup-guide`（zh/en）：新增「規格放哪」的取捨說明。PRD 加一行指過去的 acceptance＝同一份規格存在兩個檔案，兩份會漂移；指定誰為準時要再問「哪一份比較難被偷偷改」——凍結若只保護 `feature_list.json`，「以 PRD 為準」就是把權威交給沒有保護的那一份，而且要到驗收才發現不一致。單人專案建議讓 acceptance 自足並在 passing 後歸檔；有團隊或非工程讀者時保留 PRD，但權威仍歸 acceptance。**`templates/PRD.md` 保留不動**——上游 harness 移除 PRD 層的理由建立在「只有一個人讀 feature_list」這個前提上，那不是這套 kit 的預設情境。

## v1.2（2026-08-11）

- `README`／`setup-guide`／`architecture`（zh/en）：**L3 的升級條件改為事故觸發**——同型錯誤重複發生、bug 無法從既有 log 定位、邊界違規曾實際發生、或進入 `strict` 風險面。原本的「功能數 > 5」不再是理由;沒有證明價值的 L3 組件應在收官 retro 中移除。來源是上游 harness 的實測:完整 harness 沒有穩定提高任務通過率,卻顯著增加 token 與延遲成本。

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
