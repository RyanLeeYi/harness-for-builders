# <專案名>

## 啟動與驗證
- 環境恢復:`./init.sh`
- 啟動:<命令>;測試:<命令>
- 你宣告任何功能完成前,必須先跑過上面兩個命令並貼出輸出

## 專案結構與邊界
- <目錄職責一覽,例:src/api 不得直接 import src/db,必須經過 src/services>
- 完整架構見 `docs/ARCHITECTURE.md`(L2 起)

## 工作規則
1. 一次只做一個 feature(看 `feature_list.json`,挑第一個 failing)
2. feature 狀態只能 failing → passing,且必須附驗證證據(測試輸出/截圖路徑)
3. 不做 feature_list 之外的事;發現該做的新事項 → 先加進 list 標 failing,不直接做
4. 動工後不得修改既有 feature 的 acceptance(發現缺漏 → 新增條目標 failing,回需求方簽核)
5. session 結束前更新 `session-handoff.md`(L2 起)
6. 收工時檢查 `git status` + 未推 commit:程式碼有改動就 commit 並 push(remote:<repo URL>)

## 開發規則
見 `docs/CODING-RULES.md`(immutability、小檔案、錯誤處理、TDD、80% 覆蓋、conventional commits)。

## 專案特例
<只寫全域規則沒有的專案特有約束,例:必須沿用既有 repository pattern、不引入新依賴>
