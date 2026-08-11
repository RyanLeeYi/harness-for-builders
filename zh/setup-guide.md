**繁體中文** | **[English](../en/setup-guide.md)**

# Harness for Builders：建置指南

> 這份帶你一步步把 harness 建起來。如果你是 AI agent 在讀:骨架直接建,但 `acceptance` 和架構邊界要先跟使用者討論(見每步的「⚠️ 要討論,不要猜」)。

## 前置需求

- 一個 git repo(新的或既有的)
- 一個 AI coding agent(Claude Code / Cursor / Codex / …)
- 熟悉你專案的啟動與測試命令

---

## Step 1：確認 repo 與範圍

在專案 repo 根目錄開工。先問自己(或使用者)一句:**這次的 MVP,「做什麼」跟「不做什麼」分別是?** 把不做的明確劃掉,是防範圍蔓延最有效的一招。

⚠️ **要討論,不要猜**:MVP 範圍是使用者的產品決策,agent 不要自己決定。

---

## Step 2：建 L1 —— 最小 harness(約 20 分鐘)

從 [templates/](templates/) 複製三個檔到 repo 根目錄,填空:

1. `templates/CLAUDE.md` → `CLAUDE.md`
2. `templates/init.sh` → `init.sh`(填入安裝依賴、準備 env、煙霧測試的命令)
3. `templates/feature_list.json` → `feature_list.json`

`CLAUDE.md` 裡的工作規則不要動,那是 harness 的核心約束:

1. 一次只做一個 feature(挑第一個 `failing`)
2. 狀態只能 `failing → passing`,且必須附驗證證據
3. 不做 list 之外的事;新事項先加進 list 標 failing
4. 動工後不得修改既有 feature 的 acceptance
5. 宣告完成前,先跑過啟動與測試命令並貼出輸出

---

## Step 3：把 MVP 範圍寫成 feature + acceptance,然後凍結

這是整個 harness 最關鍵的一步。把 Step 1 的「做什麼」逐條轉成 `feature_list.json` 的 feature,每條都要有可判定的 `acceptance`。

模糊的 acceptance 對 agent 沒用:

- ❌「要有良好的錯誤處理」
- ✅「缺 email 欄位時,回傳 400 + `{error: "email required"}`」

需求有模糊空間的 feature,先寫 PRD(`templates/PRD.md` → `docs/prd/<feature>.md`),把 Given/When/Then、介面契約、邊界情況定清楚,再轉成 acceptance。

同一步也要把 feature 之間的相依寫進 `prerequisites`:哪些 feature 必須先 passing,這條才做得下去或驗證得了。沒有相依就填空陣列,不要留空 —— 沒申報的欄位要當成「未申報」處理,不能拿來判斷能不能平行(見 [architecture.md](architecture.md))。

**凍結**:acceptance 由需求方簽核後,動工中實作者不得偷改。發現缺漏 → 新增條目、標 failing、回簽核,不動既有條目。

⚠️ **要討論,不要猜**:acceptance 寫歪 = harness 失效。agent 不確定「怎樣算過」時要停下來問,不要自己編一個寬鬆標準。

💡 **工作跨 3 條以上 feature、或跨多個面向(前端、後端、資料)**:動工前先切 envelope 再談個別 slice(slice 就是 feature,不是新 ID)——先簽核 envelope 的 `outcome`/`constraints`/`non_goals`,再逐條核准 slice。細節與 JSON 範例見 [architecture.md](architecture.md)。

---

## Step 4：每日開發迴圈

```
1. 開場:讀 CLAUDE.md、session-handoff.md、feature_list.json
   → 說出「我要做哪個 feature、怎麼驗證」(答不出 = harness 有缺口,先補)
2. 挑第一個 failing 的 feature
3. TDD:先寫測試(RED)→ 實作(GREEN)→ 重構(IMPROVE),覆蓋率 ≥ 80%
4. 跑 code review
5. 改 passing 前:找「另一個 fresh-context 的 agent/模型」驗收
   → 只餵 PRD + 成品,對照 acceptance 逐條檢查
6. 附上 evidence,status 改 passing
7. 收工:更新 session-handoff.md、DEVLOG 記一筆、commit + push
```

---

## Step 5：補 L2 —— 交接與連續性

第一個「沒做完就要收工」的 session 結束前,建:

- `templates/session-handoff.md` → `session-handoff.md`:收工前更新,**覆寫不追加**,只留當下狀態。
- `templates/ARCHITECTURE.md` → `docs/ARCHITECTURE.md`:結構、各層職責、資料流、**明確的邊界規則**。新 session 的 agent 讀這份,不用重新探索。

---

## Step 6：升 L3 —— 回饋與驗證

由事故或高風險觸發才上——同型錯誤重複發生、bug 無法從既有 log 定位、邊界違規曾實際發生、或進入 `strict` 風險面。**功能數不是理由**;沒有證明價值的 L3 組件應在收官 retro 中移除:

- **結構化日誌**:啟動、關鍵操作、錯誤路徑都要有 log —— 修 bug 前先確認日誌能指向失敗點。
- **邊界 guard 腳本**:用 grep / linter 把 `ARCHITECTURE.md` 的邊界規則變可執行檢查,違規 `exit 1`,寫進 CI 或 commit 前必跑。
- **驗收角色分離**:生成者 ≠ 驗收者。實作那顆模型會偏袒自己的產物,驗收固定交給另一個 fresh-context 的 agent/模型。
- **(選配)agent action trace**:若平台支援 hook(如 Claude Code 的 PreToolUse),記錄 agent 每個 Edit/Write/Bash,可即時攔越權、事後回放餵改進。非必需,有餘力再上。

---

## 每日使用

- 每個 session 用固定開場那句話起手。
- 一次一個 feature,附 evidence 才改 passing。
- 收工三件事:`session-handoff.md`、`DEVLOG` 記一筆卡點與解法、`git commit + push`。

## 維護原則

保持每個 session 都要讀的操作檔精瘦,細節見 [optimization-guide.md](optimization-guide.md)。收官時跑消融檢討,砍掉沒發揮作用的組件。
