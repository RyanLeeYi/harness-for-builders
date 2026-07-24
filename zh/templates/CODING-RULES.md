# 開發規則

> 連進 `CLAUDE.md`,或挑需要的直接貼進去。這是「怎麼做」的通用規則,與 PRD 的「要什麼」分開。
> 這是一份**預設**,不是聖經——跟你團隊既有的 lint / 風格慣例衝突時,以團隊為準。

## Immutability
永遠建立新物件,不要 in-place 修改既有物件——回傳修改後的複本。
不可變資料能避免隱藏副作用、讓除錯更容易、支援安全的並行。

## 檔案組織
多個小檔 > 少數大檔:
- 高內聚、低耦合
- 200–400 行為常態,800 行為上限
- 按 feature/domain 組織,不要按類型
- 函式盡量小(< 50 行)、避免深巢狀(> 4 層)

## 錯誤處理
- 每一層都明確處理錯誤,不靜默吞掉
- UI 面向的錯誤訊息友善;伺服器端記詳細 context
- 錯誤訊息不洩漏敏感資料

## 輸入驗證(在系統邊界)
- 所有外部輸入(user input、API 回應、檔案內容)處理前先驗證
- 有 schema 驗證就用;快速失敗、訊息清楚
- 不信任外部資料

## 測試(最低 80% 覆蓋)
- Unit:個別函式、工具、元件
- Integration:API endpoint、資料庫操作
- E2E:關鍵使用者流程
- **TDD**:先寫測試(RED)→ 跑,應失敗 → 最小實作(GREEN)→ 跑,應通過 → 重構(IMPROVE)
- 修實作,不要為了讓測試過而改測試(除非測試本身寫錯)

## 安全(commit 前檢查清單)
- [ ] 無硬編碼密鑰——一律用環境變數或 secret manager
- [ ] 所有 user input 已驗證
- [ ] SQL 用參數化查詢(防 injection)
- [ ] HTML 已消毒(防 XSS)
- [ ] 認證/授權已驗證
- [ ] 錯誤訊息不洩漏敏感資料

## Git
Commit message 格式:
```
<type>: <description>

<optional body>
```
type:`feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `perf` / `ci`
