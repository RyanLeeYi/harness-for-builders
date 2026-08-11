**繁體中文** | **[English](../en/architecture.md)**

# Harness for Builders：架構與設計取捨

> 這份講「為什麼這樣設計」。照 setup-guide 建置不需要讀它;但你想調整、或想說服團隊採用,理由都在這。

## 設計原則

**agent 的可靠性不來自 prompt 寫得多好,來自 repo 裡的結構化產物。**

這是整套框架的地基。prompt 是易失記憶:會被 context 截斷、會漂移、每個 session 都要重講,而且沒有審計軌跡。檔案是持久記憶:它在 repo 裡、被版控、是唯一事實來源。任何一個全新的 agent 打開 repo,不靠對話歷史,就該能回答四個問題:

1. **怎麼跑起來?** → `init.sh`
2. **做到哪了?** → `feature_list.json` + `session-handoff.md`
3. **接下來做什麼?** → `feature_list.json` 第一個 failing
4. **怎麼算做完?** → 該 feature 的 `acceptance`

答不出任一個,就是 harness 有缺口 —— 補檔案,不要用 prompt 補。

---

## 為什麼是「三級漸進」而不是一次到位

每個 harness 組件都有維護成本:要更新、會過時、會吃 context。全上等於背一堆還沒需要的負擔,這本身就是一種 cargo-cult。

三級的分界不是隨意的,是對應**痛點第一次出現**的時機:

- **L1** 解決「範圍失控」與「假完成」—— 專案一開始就會痛,所以動工日必建。
- **L2** 解決「跨 session 失憶」—— 第一次沒做完就收工才會痛,所以那時才建。
- **L3** 解決「難查的 bug」與「同型錯誤重複發生」—— 事故發生了才痛,不是功能一多就痛。

規則:**痛點出現前,不要預建對應的組件。** 小工具一輩子停在 L1 是正確的,不是偷懶。

---

## 為什麼要凍結 acceptance

這是最反直覺、也最重要的設計。

AI agent 有一個結構性傾向:當「通過驗收」和「達成目標」衝突時,它會傾向調整驗收去遷就產物 —— 把測試改鬆、把 acceptance 重寫得更好達成。這不是惡意,是最佳化壓力的自然結果。

凍結 acceptance 切斷這條捷徑:**目標由需求方在動工前定義並簽核,實作者無權更動。** 發現 acceptance 有缺漏是正常的 —— 但處理方式是「新增條目、回簽核」,不是「就地改寬」。這保證了「做完」的定義,永遠不是由「想宣稱做完的人」來下。

> 進階:若平台支援 hook,可以把「改到既有 acceptance」設成自動攔截(DENY),讓凍結不只是規則、而是機制。
>
> 真的要做,攔截條件要綁在**被保護的檔案**上,不要綁在某個工具型別上。實測過的失敗形狀:規則只判斷「這是不是編輯操作」,於是整檔覆寫、或用 shell 腳本改同一份 JSON,兩條路都靜默繞過,而紀錄照樣顯示一切正常。另一半同樣重要 —— 攔得太寬會把人逼去用沒有保護的繞道,所以判準要精確到「這個值有沒有被動」,而不是「有沒有提到這個欄位名」。

---

## 為什麼生成者 ≠ 驗收者

同一顆模型、同一段 context 裡,「我剛寫的東西對不對」是它最沒有能力誠實回答的問題 —— 它剛才做的每個決定,都會變成它現在為自己辯護的理由。

所以驗收固定交給**另一個 fresh-context 的 agent 或不同模型**,而且只餵兩樣東西:**PRD + 成品**,不給開發過程。驗收者不知道實作者「為什麼這樣寫」,只能對照 acceptance 逐條檢查「做到了沒、證據在哪」。

角色分工:

| 角色 | 回答的問題 | 誰做 |
|------|-----------|------|
| 規劃者 | 怎麼拆 | 主對話 / plan mode |
| 生成者 | 怎麼做 | 主 agent |
| 評估者(品質) | 寫得好不好 | code review |
| 評估者(驗收) | 做對了沒 | **另一個 fresh-context agent/模型** |

「品質」和「驗收」是兩件事:code review 問「寫得好不好」,驗收問「做對了沒」。兩個都要,而且是不同時機。

---

## 為什麼 status 要 evidence 閘門

`failing → passing` 一定要附 evidence(測試輸出路徑、截圖、commit hash),否則不准改。

理由:AI 最廉價的謊言就是「我做完了」。要求證據,把「宣稱」變成「舉證」。evidence 不必是全文 —— 寫指標(檔案路徑、hash)即可,重點是**可回溯**:任何人看到 passing,都能順著 evidence 去驗。

---

## 為什麼 feature 要申報 prerequisites

`feature_list.json` 裡每個 feature 都可以有 `prerequisites`:一個 feature id 陣列,列出「必須先 passing,這條才做得下去或驗證得了」的其他 feature。沒有相依就是空陣列。

申報這件事不是流程儀式,是讓 agent(或人)答得出兩個問題:**接下來做哪個?哪兩條能平行?** 沒有這個欄位,順序只能從 id 大小猜 —— 但 id 順序不等於相依順序,F3 先建檔不代表它不依賴 F5。

平行的判準是三個條件同時成立,缺一個就不准平行:

- 不互為 `prerequisites`
- 動到的檔案沒有交集
- 依賴的資源(資料庫 schema、外部服務、共用狀態)沒有交集

**Fail-closed**:沒有 `prerequisites` 欄位的舊條目,要當成「未申報」處理,不能當成「沒有相依」直接拿來排序或放行平行。這跟「沒有證據不等於通過」是同一個原則 —— 缺欄位是缺資訊,不是預設安全。

若平台支援,可以加工具面檢查:`prerequisites` 參照的 id 必須存在、不得指向自己、不得形成循環;feature 要標 `passing` 前,列出的 `prerequisites` 必須全部已經 `passing`。

---

## 為什麼大工作要先切 envelope 再談 slice

在規格還沒動工前切,代價很低;動工後、acceptance 已經凍結才發現要拆,代價很高 —— 拆分要走「取代」(`superseded_by`)流程,比在規劃期先切貴得多。這是 envelope + slice 存在的理由。

適用門檻:一件工作預估跨三條以上 feature,或跨多個面向(前端、後端、資料)。小工作不建 envelope,單一 feature 就夠。

envelope 不是第二套 ID,**slice 就是 feature**。它是掛在一組 feature 上的共用約束層:

- `outcome`:整個 envelope 做完後,外部看得到的改變
- `constraints`:所有 slice 共用的技術、介面、相容性約束
- `non_goals`:整個 envelope 明確不做的事

簽核後,`constraints` 與 `non_goals` 跟 acceptance 同級凍結,實作者不得修改。

流程上,**先簽核 envelope,再簽核 slice**,而且只審「下一個可執行的 slice」—— 不必一次把所有 slice 談完。還沒輪到的 slice 只要先有三個欄位:穩定的 `id`、`outcome`、`prerequisites`。這三個缺一個就是阻斷項,不能用「之後再補」帶過 —— 少了 `prerequisites` 就沒辦法判斷它能不能跟別的 slice 平行。

schema 上,`features` 陣列維持平坦,不要巢狀化 —— 巢狀會讓所有讀 `feature_list.json` 的工具跟著改。envelope 只是額外的頂層陣列,每個 feature 用 `envelope` 欄位指回它所屬的 envelope id(不屬於任何 envelope 就留 `null`):

```json
{
  "envelopes": [
    {
      "id": "E1",
      "outcome": "<整個 envelope 做完後,外部看得到的改變>",
      "constraints": ["<所有 slice 共用的技術/介面/相容性約束>"],
      "non_goals": ["<整個 envelope 明確不做的事>"],
      "signed_off": "<簽核日期,簽核後 constraints 與 non_goals 凍結>"
    }
  ],
  "features": [
    {
      "id": "F12",
      "envelope": "E1",
      "prerequisites": ["F11"]
    }
  ]
}
```

---

## 消融檢討(Meta Loop)

收官時回頭問:**這套 harness 裡,哪個組件這次真的擋住了問題?哪個是純開銷?**

沒發揮作用的組件,下個專案不要照抄。這一步防止 harness 本身變成 cargo-cult —— 框架也要接受「被自己的標準檢驗」。若 L3 有啟用 trace,這個判斷可以用實際數據(攔了幾次越權、驗收 fail 了哪些)佐證,而不是靠印象。

---

## Agent 啟動順序

每個新 session 的固定開場:

> 「讀 `CLAUDE.md`、`session-handoff.md`、`feature_list.json`,然後告訴我你要做哪個 feature、怎麼驗證。」

這句話是一個**探針**:agent 若答得出來,代表 harness 完整;若答不出來,代表某個檔案缺了或過時了 —— 先補 harness 再開工,不要帶著缺口硬做。

---

## 這跟其他做法有什麼不同

- **vs. 只寫好 prompt / rules 檔**:那些仍是易失的、每 session 重載;harness 把狀態(做到哪、算不算完)外化成檔案。
- **vs. 只寫好測試**:測試驗「程式對不對」,但蓋不到 AI 協作特有的失效點 —— 範圍蔓延、跨 session 失憶、假完成、越權。harness 補的正是這一層。
- **vs. 更大的 agent 框架 / 編排工具**:harness 不是要你裝一套系統,而是幾個純文字檔 + 幾條規則。它跟你用哪個 agent、哪個模型無關 —— 換工具,harness 不用動。
