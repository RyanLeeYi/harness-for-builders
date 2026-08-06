**[English](../README.md)** | **繁體中文**

# Harness for Builders：讓任何 AI agent 可靠地幫你把專案做完

> By [Ryan Lee](https://github.com/RyanLeeYi)
>
> **你可以把整份文件丟給任何 AI,它就會帶你把 harness 建起來。**
>
> **v1.0** · 最後更新:2026-07-24 · [Changelog](../CHANGELOG.md)

> 💡 **形態受 [Vault for Founders](https://github.com/cwlin0131/Vault-for-Founders)(作者 CW Lin)啟發** —— 借用它「文件丟給任何 AI 就能自我建置」的做法,套用到 *agent harness* 而非創辦人知識庫。底層方法改編自 [Learn Harness Engineering](https://walkinglabs.github.io/learn-harness-engineering/zh-TW/projects/)。

---

## 給 AI Agent 的話

如果你是正在讀這份文件、要幫使用者建立開發環境的 AI agent:

Harness for Builders 是一套用 repo 結構化產物管理 AI coding agent 工作環境的框架。你的任務是帶使用者把它建起來。**檔案骨架可以直接建**(`init.sh`、`feature_list.json` 的殼);但**核心內容 —— feature 的 acceptance、架構邊界、專案規則 —— 必須先跟使用者討論再寫,不是填空。**

**建議閱讀順序:**

1. 讀這份 README,掌握整體架構與哲學
2. 讀 [setup-guide.md](setup-guide.md),照步驟建置
3. 讀 [architecture.md](architecture.md),理解設計取捨(為什麼三級漸進、為什麼凍結 acceptance)
4. 用 [templates/](templates/) 產出使用者專案的骨架
5. **重要**:`acceptance` 和架構邊界不能替使用者猜。照 setup-guide 的討論流程,一層一層帶使用者定義出「怎麼驗證才算做完」。驗收標準寫歪,整個 harness 就失效
6. 建好後,讀 [optimization-guide.md](optimization-guide.md),幫使用者把每個 session 都要讀的操作檔保持精瘦

---

## 這是什麼

Harness for Builders 是一套完整框架,讓你從零建立「AI agent 能可靠工作的 repo」,包含為什麼、怎麼做、以及現成模板。

當你把越來越多開發工作交給 AI(寫功能、修 bug、重構),它需要一個能「知道現況」的地方:專案怎麼跑、規則是什麼、範圍到哪、上次做到哪。那個地方就是你的 **harness**。

**核心主張:agent 的可靠性不來自 prompt 寫得多好,來自 repo 裡的結構化產物。** prompt 會被遺忘、會漂移、每個 session 都要重講;檔案不會 —— 它就在 repo 裡,是唯一事實來源。

```
 一個全新的 agent 打開你的 repo,不靠對話歷史,要能回答四個問題:

   ┌ 怎麼跑起來?  ──────→  init.sh
   │
   ├ 做到哪了?    ──────→  feature_list.json  +  session-handoff.md
   │
   ├ 接下來做什麼? ──────→  feature_list.json 第一個 failing 的條目
   │
   └ 怎麼算做完?  ──────→  該 feature 的 acceptance（已凍結）

 任一題答不出來 = harness 有缺口 → 補檔案,不要用 prompt 補
```

### 關鍵名詞

- **Harness**:一組放在 repo 裡的檔案,讓 agent 知道怎麼跑、做什麼、算不算做完。不是框架程式碼,是「工作環境」。
- **feature_list.json**:範圍與驗收的狀態機。每個功能一條,狀態只有 `failing` / `passing`,改 passing 一定要附證據,功能間的相依用 `prerequisites` 申報 —— 沒申報視為未知,不能當「沒有相依」。
- **acceptance**:「怎麼驗證才算過」。動工前寫好、簽核後**凍結** —— 這是 harness 最關鍵的一個字。
- **session**:一次連續的開發工作。agent 的 context 會斷,所以每個 session 收工要留交接。

---

## 為什麼需要 harness

沒有 harness 的 AI 開發,你大概遇過這些:

| 症狀 | harness 怎麼擋 |
|------|----------------|
| agent 忘記上次做到哪,每次重新摸索 | `session-handoff.md` + 固定開場 |
| 宣稱「做完了」但根本沒驗證 | `feature_list` 的 evidence 閘門 |
| 改到不該改的東西、擅自擴大範圍 | `ARCHITECTURE.md` 邊界 + 「不做 list 之外的事」 |
| 為了讓測試過,偷偷放寬標準 | **凍結的 acceptance** |
| 每個 session 都把整個 codebase 讀一遍,燒 context | index 化的 `CLAUDE.md` + 檔案瘦身 |

harness 把這些用**檔案**釘死,而不是每次靠 prompt 提醒。

---

## 三級漸進(核心哲學:按需要升級,不要一次全上)

| 級 | 時機 | 建置產物 |
|----|------|----------|
| **L1 最小 harness** | 專案動工日,寫第一行程式前 | `CLAUDE.md` + `init.sh` + `feature_list.json` |
| **L2 交接與連續性** | 第一個沒做完就收工的 session 結束前 | `session-handoff.md` + `docs/ARCHITECTURE.md` |
| **L3 回饋與驗證** | 出現第一個「難查的 bug」或功能數 > 5 | 結構化日誌 + 邊界 guard 腳本 + 驗收角色分離 |

```
 你的 repo
 │
 ├─ L1 ── 動工日必建,約 20 分鐘 ────────────────────────────────
 │   ├─ CLAUDE.md ............ 規則、命令、邊界（每 session 都讀,保持精瘦）
 │   ├─ init.sh .............. 一鍵回到「可開發、可驗證」狀態
 │   └─ feature_list.json .... 範圍與驗收的狀態機
 │                            ★ acceptance 動工前簽核後凍結
 │                            ★ 沒 evidence 不准改 passing
 │                            ★ prerequisites 需申報,未申報 ≠ 沒有相依
 │
 ├─ L2 ── 第一次沒做完就收工 ──────────────────────────────────
 │   ├─ session-handoff.md ... 上次做到哪（覆寫不追加）
 │   └─ docs/ARCHITECTURE.md . 結構、資料流、邊界規則（只記現況）
 │
 ├─ L3 ── 難查的 bug,或功能數 > 5 ────────────────────────────
 │   ├─ 結構化日誌 ........... 讓 agent 看得到失敗原因
 │   ├─ check-architecture.sh  把邊界規則變成可執行檢查
 │   └─ 獨立驗收者 ........... 另一個 fresh-context 的 agent／模型
 │
 └─ docs/ ── 收官才回頭讀,不進每日 context ────────────────────
     ├─ PLAN.md ............. 為什麼做、範圍、成功指標
     ├─ prd/<feature>.md .... 具體要什麼、怎麼算對
     ├─ DEVLOG.md ........... 卡點與解法（onboarding／事故回顧原料）
     └─ DECISIONS.md ........ 難回頭的技術選擇與理由


 角色分離（L3）:生成的人不可以是驗收的人

   規劃者 ──→ 生成者 ──→ 評估者(品質) ──→ 評估者(驗收)
   怎麼拆      怎麼做      寫得好不好         做對了沒
                                              ▲
                                    只餵 PRD + 成品,不給開發過程
                                    由另一個 fresh-context 模型執行
```

> **不要 cargo-cult。** 小專案一輩子停在 L1 都沒問題。每個組件都有維護成本,只在它真的擋住問題時才加。收官時做一次**消融檢討**:哪個組件這次真的發揮作用?沒用到的,下個專案不要照抄。設計理由見 [architecture.md](architecture.md)。

---

## 我需要什麼才能開始

- 一個 git repo(新專案或既有專案都行)
- 一個 AI coding agent(Claude Code、Cursor、Codex、或任何能讀寫檔案的)
- 20 分鐘建 L1

接下來 → [setup-guide.md](setup-guide.md)

---

## 這跟「寫好測試」「寫好 prompt」有什麼不同

- **比 prompt 持久**:prompt 每個 session 重來;harness 是檔案,活在 repo 裡。
- **比測試多一層**:測試驗「程式對不對」;harness 還管「範圍、交接、context、越權」—— 這些是 AI 協作特有的失效點,測試蓋不到。
- **獨立驗收**:生成的 agent 會偏袒自己的產物,所以驗收交給另一個 fresh-context 的 agent/模型。詳見 [architecture.md](architecture.md) 的「生成者 ≠ 驗收者」。
