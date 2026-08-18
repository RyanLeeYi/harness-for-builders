# harness-gate — 流程接錯與 cwd 漂移的攔截（spec）

> 建立：2026-07-31（Ryan × Cub brainstorming 定案）
> 定位：全域 `~/.claude` 基礎設施，與 `harness-trace` 平行、**不共用程式**。
> 對象：主 session 的開發行為。管的是「有沒有走 harness 流程」，不是「做了什麼危險動作」（那是 harness-trace）。

---

## 起因

2026-07-31，Ryan 要求在 mission-control 加一個新功能。Claude 全程 **cwd 停在家目錄**，直接呼叫一個訪談 skill（`brainstorming`），沒 `cd` 進 repo、沒讀 repo `AGENTS.md`／`session-handoff.md`／`feature_list.json`。

兩個獨立的失誤：

1. **流程接錯**：`brainstorming` 的終點是 `writing-plans` 加它自己的 specs 目錄；harness 專案的新 feature 終點是 Plan → 驗收清單簽核 → 凍結進 `feature_list.json` 的 `acceptance`。前半段（釐清需求）重疊，尾巴完全不同。
2. **第 0 步沒做**：`development-workflow.md` 要求 session 開場先確認 cwd 在專案 repo 內。沒做的後果是 repo `.claude/settings.json`（effort xhigh）不生效、repo 規則得靠模型自己想起來去讀。

**為什麼要 hook 而不是寫進 `CLAUDE.md`**：當時那套 skill 包由 SessionStart hook 注入，帶 `EXTREMELY-IMPORTANT` 字樣，位階比 `CLAUDE.md` 的散文強勢。再加一段文字等於再賭一次模型記得——正是 2026-07-25 教訓所說「靠模型記得就等於沒有」。

**為什麼不折進 harness-trace**：它的生效條件第 1 條是「cwd 位於 harness repo」，而本 spec 的 G2 要處理的恰是 cwd **不在** repo 的情形。為了塞進去而放寬那個 gate，會賠掉一個已測試過的保護。

---

## 機制

- **事件**：`PreToolUse`，matcher `Skill|Read|Edit|Write|Bash`。
- **架構**：bash gate `harness-gate.sh` + python core `harness-gate-core.py`（同 harness-trace 慣例：core 走獨立檔＋pipe 餵 stdin，不用 heredoc——heredoc 會佔用 stdin 使 payload 進不到 `sys.stdin`）。
- **成本控制**：bash 端先做一次子字串預篩，stdin 同時不含任一受閘門管的 skill 名與任一 side-project 根目錄名 → 立刻 `exit 0`。絕大多數 tool call 的成本是一次字串比對，不付 python 啟動成本。

### 設定（環境變數，皆有預設，測試用）

| 變數 | 預設 | 用途 |
|---|---|---|
| `HARNESS_GATE_ROOTS` | （無預設；沒設時 G2 停用） | side-project 根目錄，`;` 分隔多個（不能用 `:`——Windows 路徑本身含 `C:`） |
| `HARNESS_GATE_DIR` | `$HOME/.claude/harness-gate` | 去重標記檔目錄 |
| `HARNESS_GATE_VAULT` | （無預設；沒設時不排除） | vault 路徑，一律不介入 |

---

## G1 — 流程接錯（Skill gate）

**觸發**：`tool_name == "Skill"` 且 `tool_input.skill` ∈
`{brainstorming, writing-plans}`（比對前剝掉 namespace 前綴）。

| cwd 情形 | 動作 |
|---|---|
| 位於 git repo、repo root 有 `feature_list.json` | **DENY** |
| 位於 vault | **不介入**（vault 筆記工作本來就走通用流程） |
| 其他（家目錄、非 harness repo、非 git） | **提醒不擋**（`systemMessage`，同 session 只發一次） |

DENY 的 reason 指出替代路徑：新 feature 走 Plan → 驗收清單簽核 → 凍結進 `feature_list.json`；並附上「若此動作確為必要，請向使用者說明並取得確認」的逃生口（同 harness-trace 慣例，不做成死路）。

**刻意不擋非 repo 情形**：工作案件、一次性腳本、別人的 repo 都適用通用流程，硬擋是誤殺。這一格用提醒換低誤殺率——它本來就只是 G2 的補網，真正治本的是 G2。

**名單只放這兩個 skill**：`test-driven-development`、`systematic-debugging` 等在 harness 專案裡照樣該用，不在名單內。

---

## G2 — 第 0 步沒做（cwd 漂移）

**觸發**：`tool_name` ∈ `{Read, Edit, Write, Bash}`，從 payload 抽出目標路徑
（`file_path`；Bash 取 `command` 內以任一 root 為前綴的路徑），判定：

1. 路徑落在某個 `<root>/<專案>/` 之下 →
2. 該 `<專案>` 目錄存在 `feature_list.json`（**兩者兵接**：先字串比對過濾，命中才驗檔案存在）→
3. cwd 不在同一個 `<專案>` 之下 →
4. → **提醒不擋**：先 `cd` 進 repo，並讀 `AGENTS.md`（或 `CLAUDE.md`）、`session-handoff.md`、`feature_list.json`

**去重**：同 session 同專案只提醒一次，標記檔 `$HARNESS_GATE_DIR/cwd-<sid>-<專案>`。

**為什麼不擋**：跨 repo 讀檔是正當行為（對照兩個專案的做法、從 vault 查資料）。這裡要治的是「整場 session 都在外面做事」，一次提醒就足夠；擋下去只會製造摩擦。

**為什麼含 `Read`**：今天的失誤裡，第一個露餡的動作就是在家目錄 `Read` repo 的 `AGENTS.md`。只看寫入類工具會漏掉整個探索階段。

---

## 輸出格式

- DENY：`{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"…"},"systemMessage":"harness-gate：blocked <id>"}`
- 提醒：`{"systemMessage":"harness-gate：…"}`
- 不介入：無輸出，`exit 0`

**fail-open 原則**：payload 解析失敗、路徑判不出、python 不可用 → 一律不介入。這是流程提醒，不是安全邊界；誤擋的代價高於漏抓（危險動作由 harness-trace 負責）。

---

## 回歸測試

`harness-gate-test.sh`，20 個情境（該擋 4、該提醒 5、該放行 8、不介入 3）。

另有 5 個真實 payload 的 live 驗證（Windows 反斜線路徑、真實 repo），2026-07-31 全數通過。**測資要用真實形狀**——同一天作者自己捏的 live payload 寫出 `"cwd":"C:\Users\user"`（`\U` 不是合法 JSON 跳脫），hook 依 fail-open 靜默不介入，一度被誤判成 hook 壞了。已固化為情境 15。

### 已知限制

payload 契約若變更（欄位改名、`cwd` 消失），harness-gate 會**靜默失效**，不像 harness-trace 有 schema-drift 自檢。理由：本 hook 是流程提醒而非安全邊界，且 harness-trace 對同一份 payload 已有偵測——但它只在 cwd 位於 harness repo 時生效，而 G2 的場景恰好相反。若日後發現提醒莫名消失，先跑 `harness-gate-test.sh` 核對 payload 格式。

2026-07-28 教訓：fail-open 的東西壞掉時不噴錯，只會安靜放行——**每一種該擋與不該擋的情境都要實跑並固化**，不能只驗該擋的那幾條。
