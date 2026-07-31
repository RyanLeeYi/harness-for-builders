# Changelog

本專案版本紀錄。格式:新的在上。

## v1.0.1（2026-07-31）

- `architecture`（zh/en）：凍結 acceptance 的 hook 進階註記補上實作教訓——攔截條件要綁被保護的檔案而非工具型別，判準要精確到「值有沒有被動」。來源是上游 harness 實測到的靜默繞過。

## v1.0（2026-07-24）

首次發佈。

- 三級漸進 harness（L1 最小 → L2 交接 → L3 回饋驗證）
- 操作檔範本：`CLAUDE.md`、`init.sh`、`feature_list.json`、`session-handoff.md`、`ARCHITECTURE.md`
- 文件範本：`PLAN`、`PRD`、`DEVLOG`、`DECISIONS`、`CODING-RULES`
- 四份指南：README（哲學）、setup-guide（一步步）、architecture（設計取捨）、optimization-guide（context 瘦身）
- 雙語 zh / en
