# harness-trace — 開發 agent 越權偵測與 action trace（MVP spec）

> 建立：2026-07-20（Ryan × Cub brainstorming 定案）
> 2026-08-07 更新：`out-of-repo-write` 新增 vault `projects/` 例外（見「vault 例外」一節）＋回歸案例 7c／7d／7e；案例 7 的敘述原本把 scratchpad 寫成會 flag，一併更正。
> 定位：全域 `~/.claude` 基礎設施，與 `usage-guard.sh` 同架構。把文章〈可控的 Harness〉六元件裡最弱的 **Trace** 從「敘事式 DEVLOG」升級成「結構化、可回放、可抓越權、可餵 eval」。
> 對象：**開發 agent（Claude Code 在 side project 上的行為）**。產品層 agent 的 runtime trace 是後續獨立工作，不在此 spec。

---

## 背景與三層排序

文章的 Trace 有三個用途，彼此有依賴關係，定案排序（每一層產出下一層的原料）：

1. **抓越權**（本 spec，MVP）— 最便宜、即時保護、本質結構化，踩在 Permission×Trace 交叉點；直接執行 harness 既有鐵律。
2. **回放 debug**（後續）— 是第 1 層 action stream 的 curated 視圖，不重造 transcript/git。
3. **餵 eval / Meta Loop**（後續）— 越權旗標 + acceptance-verifier 驗收失敗自動成為 golden dataset 原料。

> 為什麼不靠 agent 自己寫 trace：**抓越權的本質是抓 agent 做了不該做的事；出錯/幻覺的 agent 不會舉報自己。** 越權偵測必須架在客觀、hook 攔截層。

---

## 機制

- **事件**：`PreToolUse`（不是 PostToolUse）。要在危險動作**執行前**攔下，`rm -rf` 跑完才記沒意義。
- **架構**：bash gate `~/.claude/scripts/harness-trace.sh` + python core `harness-trace-core.py`，與 usage-guard 同慣例（讀 stdin JSON、MSYS 上盡量用 bash 內建）。core 拆成獨立 `.py` 檔（不用 `python - <<'PY'`——heredoc 會佔用 stdin 使 payload 進不到 `sys.stdin`），bash 用 pipe 餵 stdin。
- **生效條件（缺一不介入）**：
  1. hook stdin 的 `cwd` 位於 git repo；
  2. repo root **不是** vault（`HARNESS_TRACE_VAULT`；沒設就不排除）；
  3. repo root 存在 `feature_list.json`（＝這是 harness 管理的專案）。
  - 任一不成立 → `exit 0`，完全不干擾（工作案件、別人的 repo、vault 筆記都不受影響）。
  - 判不出 cwd／無 git 時：**不介入**（與 usage-guard 相反——trace 是保護機制，寧可漏抓也不要誤擋非 harness 專案）。

---

## Trace schema（`<repo>/.harness/trace.jsonl`，每個 action 一行）

```json
{"ts":"2026-07-20T15:40:12+08:00","sid":"abc123","feature":"F3","tool":"Bash","target":"pytest tests/ -q","in_repo":true,"verdict":"ok"}
```

| 欄位 | 型別 | 說明 |
|---|---|---|
| `ts` | string | ISO 8601 含時區（本機時間） |
| `sid` | string | session_id（stdin `session_id`）；取不到就 `"?"` |
| `feature` | string | 當前 feature id。heuristic：讀 repo root `feature_list.json`，取 `features[]` 第一個 `status=="failing"` 的 `id`（對齊「一次只做一個、挑第一個 failing」）；讀不到／無 failing → `"?"` |
| `tool` | string | `Edit` / `Write` / `Bash`（其餘工具不記） |
| `target` | string | Edit/Write：`file_path`（repo 相對路徑，repo 外則絕對）。Bash：`command` 截斷至 200 字 |
| `in_repo` | bool | target 是否在 repo root 內（Bash 一律 `true`，command 無單一路徑） |
| `verdict` | string | `ok` / `overreach:<rule>` / `blocked:<rule>`（見下） |

- **檔案處置**：`.harness/trace.jsonl` **不進 git**（hook 首次寫入時確保 repo `.gitignore` 含 `.harness/`）。理由：越權當下已即時 block 保護；raw log 進 git 每 session 都髒。餵 eval 時再從中萃取 curated case 進 DEVLOG。
- **瘦身**：trace.jsonl 超過 5000 行時，rotate 成 `.harness/trace-<YYYYMMDD-HHMMSS>.jsonl`，主檔重開。

---

## 越權規則清單（MVP）

### 🔴 DENY — 攔截並回 block（只放不含糊的危險動作，高精準度）

| id | 規則 | 偵測 |
|---|---|---|
| `frozen-acceptance` | 改到 `feature_list.json` **既有**的凍結欄位值：feature 的 `"acceptance"`、`"non_goals"`，envelope 的 `"constraints"`、`"non_goals"`（2026-08-05 隨 envelope + slice 擴充；欄位清單見 core 的 `FROZEN_KEYS`） | tool==Edit 且 `file_path` basename==`feature_list.json`。從 `old_string` 抓出所有凍結欄位的**字串值**（陣列取每個元素），任一值沒有原樣出現在 `new_string` 就 block。**新增不擋、修改與刪除才擋**：新增 feature 時 `old_string` 不含既有值；往 `non_goals` 追加一條時既有元素仍原樣存在，故兩者都**不會誤擋**，對齊「發現新事項→加進 list 標 failing」允許項 |
| `denylist-cmd` | 執行 rules 明文禁的危險命令 | tool==Bash 且 `command` 命中 denylist regex：`git push .*(--force|-f)\b`、`git commit .*--no-verify`、`git reset --hard`、`\brm -rf\b`、`curl .*\|\s*sh`、`--no-gpg-sign` |

命中 → `verdict=blocked:<id>`，寫 trace 後回：
```json
{"decision":"block","reason":"harness 越權保護：<說明>。這是刻意機制不是錯誤；若此動作確為必要，請向使用者說明並取得確認後再進行。","systemMessage":"harness-trace：blocked <id>"}
```

### 🟡 RECORD-and-flag — 只記 `verdict`+`systemMessage` 提示，不擋（避免誤殺）

| id | 規則 | 偵測 |
|---|---|---|
| `out-of-repo-write` | Write/Edit 寫到 repo 外 | tool∈{Write,Edit} 且 target 解析後不在 repo root。**兩個例外不記**：① scratchpad／temp（`/(temp\|tmp)/claude/`，Claude 自己的暫存命名空間）② **vault 的 `projects/` 子樹**（見下方「vault 例外」） |
| `status-to-passing` | feature 狀態改 passing | tool==Edit 且 basename==`feature_list.json` 且 `new_string` 含 `"passing"` 而 `old_string` 含 `"failing"`（方便事後查是否附 evidence） |

回 `{"systemMessage":"..."}`（不含 `decision:block`），不阻擋。

#### vault 例外（2026/08/07 新增）

`out-of-repo-write` 放行 vault 的 `projects/` 子樹。預設路徑
無預設，用環境變數
`HARNESS_TRACE_VAULT_PROJECTS` 覆寫（測試用）。比對前兩側都經 `norm()` 再轉小寫。

**為什麼**：收工回寫 vault 的 `DEVLOG.md` / `DECISIONS.md` 是流程**明文要求**的動作——
寫在 `rules/common/development-workflow.md` 的「收工」條、repo 入口檔的「Vault 連動」段、
`usage-guard.sh` 收工第 4 步。原本它會被判成越權：**規則叫它寫、hook 記它越權，兩邊打架
時帶警告的那邊贏**，實測結果是 vault 長期一筆收官紀錄都收不到（三個專案只有 mission-control
偶爾有，因為它的 `AGENTS.md` 自己寫了這條）。這是 guard 與流程規範互相矛盾，不是模型不聽話。

**範圍刻意只到 `projects/`**：`career/`、`knowledge/`、`identity/`、`memory/` 從 repo session
寫入仍屬可疑，維持標記——收官回寫的正當性來自「這個 repo 對應那個專案資料夾」，不延伸到整個 vault。

### 🩺 schema-drift — 契約漂移自檢（2026/07/25 新增）

| id | 規則 | 偵測 |
|---|---|---|
| `schema-drift:<欄位>` | PreToolUse payload 少了 hook 賴以運作的必要欄位 | `cwd`（bash gate，缺了定位不到 repo）／`tool_name`、`tool_input`（core，缺了判不出動作）|

**要解決的問題**：hook 全程 fail-open——欄位讀不到就靜默 `exit 0`。若 Claude Code 改了 payload 契約，越權保護會**無聲關閉**，而 trace 仍照記 `verdict: ok`，看起來一切健康。實測過最糟的形狀：`tool_input` 缺失時，一個含 `rm -rf /` 的 Bash 命令被記成 `ok`。

**行為**：仍不 block（不擋使用者工作），但寫 trace `verdict: schema-drift:<欄位>` + systemMessage 警告；`harness-retro.py` 把它排在訊號**第一位**，因為機制失效期間的 trace 資料不可信，其他判讀沒有意義。缺 `cwd` 時無法定位 repo、無處寫 trace，改為每日警告一次（sentinel `schema-drift-cwd-YYYYMMDD`）。

**開放契約原則**：只驗「必要欄位在不在」，**不鎖封閉欄位集合**——payload 多出未知欄位是正常演進，不得誤報。這條是 2026-07-22 共用 controller 專案的教訓（`hook payload 是開放契約，驗證不可鎖封閉欄位集合`）在此處的具體落實。

### 🟡 延後（不在 MVP）

- **off-feature-edit**：改到與當前 feature 無關的檔。需 `feature_list.json` 宣告 per-feature 檔案 scope，或接 `scripts/check-architecture.sh` 的邊界規則。MVP 不做。

---

## 效能與去重

- 每個 tool call 都跑，沿用 usage-guard 的省成本原則：純 bash regex 判斷，不 fork python（schema 寫入用 bash `printf`，不需 JSON parser——欄位皆為已知字串，注意跳脫 `"` 與 `\`）。
- `feature_list.json` 的當前 feature 每個 hook 呼叫要讀一次；以 mtime 快取到 `~/.claude/harness-trace/feature-<repo-hash>.txt`，`feature_list.json` 沒變就讀快取。
- block 類**不去重**（每次危險動作都要擋）；RECORD 類的 systemMessage 提示每 session 每 rule 只提一次（sentinel，仿 usage-guard），避免洗頻。

---

## 測試（`~/.claude/scripts/harness-trace-test.sh`，改 hook 後必跑）

以 stdin 餵造的 PreToolUse payload，斷言輸出（block / silent-but-recorded / systemMessage-only）與 trace.jsonl 內容：

1. 非 harness 專案（無 feature_list.json）→ 不介入、不寫 trace
2. vault repo → 不介入
3. 正常 Bash（pytest）→ 寫 trace `verdict=ok`、不 block
4. `frozen-acceptance`：Edit 既有 feature 的 acceptance（`old_string` 含 `"acceptance"`）→ block + trace `blocked:frozen-acceptance`
4e. **envelope `constraints` 被改**（值沒原樣保留）→ block
4f. **envelope `non_goals` 追加一條**（既有元素原樣保留）→ **不 block**
4g. **envelope `non_goals` 刪掉既有一條** → block
4b. **新增 feature**：Edit feature_list.json 加一條新 feature（`old_string` 為 `]`／既有 feature 尾、不含既有 acceptance；`new_string` 帶新 acceptance）→ **不 block**、trace `ok`（守住不誤殺允許項）
5. `denylist-cmd`：`git push --force` → block；`rm -rf build/` → block
6. denylist 非命中：`git push`（無 --force）→ ok，不 block
7. `out-of-repo-write`：Write 到 repo 外的一般路徑 → 不 block、trace `overreach:out-of-repo-write`、有 systemMessage
7c. **例外**：Write 到 scratchpad（`temp/claude/` 下）→ trace `ok`、**無** systemMessage
7d. **例外**：Edit vault `projects/<專案>/DEVLOG.md`（收官回寫）→ trace `ok`、**無** systemMessage
7e. **例外不擴散**：Write vault `career/` → 仍 `overreach:out-of-repo-write` 並有 systemMessage
8. `status-to-passing`：Edit failing→passing → 不 block、trace 記錄、systemMessage
9. RECORD 類 systemMessage 同 session 同 rule 第二次 → 靜默（去重）
10. `.gitignore` 首次自動補 `.harness/`
11. feature heuristic：feature_list 有多個 failing → 取第一個；無 failing → `feature=?`
12. `schema-drift`：payload 缺 `tool_name` → 不 block、trace `schema-drift:tool_name`、systemMessage
13. `schema-drift`：payload 缺 `tool_input`（`tool_name` 在）→ 同上，且**不得**被誤記成 `ok`
14. **開放契約**：payload 多出未知欄位 → 正常運作、trace `ok`，不得誤報 drift
15. schema-drift systemMessage 同 session 第二次 → 靜默（去重）
16. 缺 `cwd` → 不靜默死掉，回 systemMessage 警告（每日一次）

> 案例數會隨規則增補成長，判準是**全綠**，不寫死數字。

---

## 落地後

- 更新 `settings.json` 註冊 PreToolUse hook（matcher: Edit|Write|Bash）。
- 更新 vault `templates/軟體開發/HARNESS.md` 的 L3「6. 結構化日誌」段：把現行模糊的「應用程式 log」改寫成兩件事——(a) 應用程式 log（原意，修 bug 用）；(b) **agent action trace（harness-trace hook，抓越權用）**，並指到本機制。
- 建立 memory 檔 `harness-trace-mechanism.md` + 更新 MEMORY.md 索引（仿 usage-guard 的記錄方式）。
- 消融檢討時機：跑過幾個 session 後，看 block 有沒有誤殺、trace 有沒有真的幫上回放/eval——沒發揮就砍，別 cargo-cult。
