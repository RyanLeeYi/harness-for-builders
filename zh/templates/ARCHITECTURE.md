---
updated: YYYY-MM-DD
---

# <專案名稱> — ARCHITECTURE

> 只記現況。結構改了就改寫,不留「以前是怎樣」——歷史去 DECISIONS.md。
> 這份讓新 session 的 agent 不用重新探索整個 codebase。

## 系統概觀
<一段話 + 一張簡圖(ASCII 也行):主要組件與資料流>

## 目錄職責
| 目錄 | 職責 | 不可以做什麼 |
|------|------|-------------|
| `src/api` | 對外端點 | 不得直接 import `src/db`,必須經過 `src/services` |
| `src/services` | 商業邏輯 | |
| `src/db` | 資料存取 | 不含商業邏輯 |

## 資料流
<例:request → api → service → repository → db,回程反向>

## 邊界規則(可被 check-architecture 腳本驗證)
- <例:api 層不得出現 SQL 字串>
- <例:db 層不得 import service 層>

## 外部依賴
<第三方服務、API、其失敗時的預期行為>
