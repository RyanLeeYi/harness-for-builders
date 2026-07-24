**繁體中文** | **[English](../en/optimization-guide.md)**

# Harness 優化指南：讓 agent 每個 session 花更少 context 就進入狀況

> harness 建久了會膨脹。這份教你把「每 session 都要讀的操作檔」保持精瘦,不讓 context 被歷史雜訊塞滿。

## 核心概念

判斷一個檔案該不該瘦身,標準只有一條:

> **這個檔案是不是每個 session 都要進 agent 的 context?**

- **是(操作檔)**:`CLAUDE.md`、`ARCHITECTURE.md`、`feature_list.json`、`session-handoff.md` → 保持精瘦,定期修剪。
- **否(檔案庫)**:`DEVLOG.md`、`DECISIONS.md` → 收官才回頭讀,**不縮**。過程紀錄是 onboarding 和事故回顧的原料,砍掉等於銷毀證據。

兩者混為一談,是 harness 膨脹的主因。

---

## 1. `CLAUDE.md` 保持 index 化

`CLAUDE.md` 只留:規則、命令、邊界。細節(部署步驟、API 說明、踩坑記錄)放 `docs/`,用連結指過去。

往裡加東西前先問:**agent 每個 session 都需要讀到這條嗎?** 不是,就放 `docs/`。

---

## 2. `feature_list.json` 定期歸檔

passing 條目 > 10 條時,搬去 `feature_archive.json`(同格式),主檔只留 failing + 最近完成的 3 條。

`evidence` 一律寫指標(測試輸出的檔案路徑、commit hash),不貼全文 —— 全文放檔案裡,list 只留指標。

---

## 3. `session-handoff.md` 覆寫不追加

它只該有「當下狀態」。如果它在變長,就是用法錯了 —— 上個 session 的交接,在這個 session 用完就過期,直接覆寫掉。

---

## 4. `ARCHITECTURE.md` 只記現況

結構改了就改寫,不要留「以前是怎樣」。歷史與演進去 `DECISIONS.md`,架構檔只回答「現在長怎樣」。

---

## 5. 檔案庫型文件:不縮,但可拆

`DEVLOG.md`、`DECISIONS.md` 不做瘦身 —— 它們的價值就在完整。但專案跨季、真的太長時,按時間拆檔:

```
DEVLOG.md            ← 當季
docs/archive/DEVLOG-2026Q3.md  ← 歸檔,主檔留連結
```

拆檔是搬移,不是刪減。

---

## 執行順序

context 壓力來的時候,依這個順序清:

1. `session-handoff.md` 覆寫成當下狀態(最常膨脹)
2. `feature_list.json` 歸檔 passing 條目
3. `CLAUDE.md` 把細節搬去 `docs/`
4. `ARCHITECTURE.md` 砍掉過時描述

## 什麼時候做

- 每次收工順手清 `session-handoff.md`。
- passing 累積到 10 條、或感覺開場讀檔變慢時,清 `feature_list.json`。
- 收官時整批檢視一遍。
