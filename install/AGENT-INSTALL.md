# AGENT-INSTALL — 把強制層裝進全域 Claude Code 設定

*(Agent-executed runbook. Traditional Chinese primary; an AI agent can follow it regardless of the user's language — translate your reports to the user's language.)*

你是被使用者要求執行安裝的 AI agent。照本文逐步做，**每一步寫入前都先呈現計畫、取得使用者同意**。這份 payload 會載入使用者每個未來 session——這是信任邊界，不是普通檔案複製。

## 你會裝什麼

| 目標 | 內容 | 作用 |
|---|---|---|
| `<config>/agents/` | 4 支角色檔（executor／Explore／acceptance-verifier／plan-verifier） | 執行者、探索者、兩種檢查者；模型與唯讀邊界釘在 frontmatter |
| `<config>/scripts/` | 3 支 hook（harness-trace＋core、harness-gate＋core、no-emoji-guard）＋ verifier-bash-guard（由 acceptance-verifier frontmatter 引用）＋ harness-plan.py ＋ 4 套回歸測試 ＋ 2 份 SPEC | 凍結 acceptance 的 DENY、危險命令攔截、流程閘門、emoji 閘門、平行分析 |
| `<config>/skills/harness-init/` | 1 支 skill | 在任何 repo 建出符合 harness-for-builders 規格的最小 harness |
| `<config>/settings.json` | `claude-code/settings-fragment.json` 的 hooks 條目（**合併**） | 讓 hook 真的掛上 |

**不含**：任何規則文件（`rules/`）、記憶、人格、用量監看。那些是個人層，方法本身在本 repo 的文件裡。

## Step 0：定位設定根目錄

`CLAUDE_CONFIG_DIR` 有設就用它，否則 `~/.claude`。下文以 `<config>` 代稱。確認目錄存在。

## Step 1：盤點與合併計畫（唯讀）

1. 列出 `<config>/agents/`、`<config>/scripts/`、`<config>/skills/` 現有內容，找出**同名衝突**。
2. 讀 `<config>/settings.json`（不存在則計畫建立），比對 `claude-code/settings-fragment.json` 的三條 PreToolUse 是否已存在（比對 command 字串）。
3. 產出合併計畫呈給使用者：每個要寫的檔案、覆蓋還是新增、settings 動哪幾行。**同名衝突一律先問，不默認覆蓋。**
4. **等使用者明確同意才進 Step 2。**

## Step 2：寫入

1. 複製 `claude-code/agents/*` → `<config>/agents/`。
2. 複製 `claude-code/scripts/*` → `<config>/scripts/`。
3. 複製 `claude-code/skills/harness-init/` → `<config>/skills/harness-init/`。
4. 合併 settings：把 fragment 的三條 PreToolUse 條目 append 進 `<config>/settings.json` 的 `hooks.PreToolUse` 陣列（沒有該結構就建立）。**不動使用者既有的任何條目**，`_comment`／`_env_comment` 欄位不要複製進去。
5. `<config>` 不是 `~/.claude` 時：settings 條目與 `agents/acceptance-verifier.md` frontmatter 裡的 `$HOME/.claude/scripts/...` 路徑要一併改成實際的 `<config>/scripts/...`。

## Step 3：環境變數（選配，預設全略過）

沒設時對應功能安靜停用（fail-open），核心保護不受影響：

| 變數 | 作用 |
|---|---|
| `HARNESS_GATE_ROOTS` | 分號分隔的專案根目錄；設了才開 cwd 漂移偵測（G2） |
| `HARNESS_GATE_VAULT`／`HARNESS_TRACE_VAULT` | 知識庫根目錄，hook 在裡面不介入 |
| `HARNESS_TRACE_VAULT_PROJECTS` | 收官流程被允許寫入的外部子樹 |
| `NO_EMOJI_EXEMPT` | 分號分隔的路徑子字串，emoji 閘門放行（例：筆記庫） |

## Step 4：驗證（沒驗過的防線等於沒有防線）

1. 跑四套回歸測試，全綠才算裝好：
   ```bash
   cd <config>/scripts
   bash harness-trace-test.sh && bash harness-gate-test.sh && bash no-emoji-guard-test.sh && bash verifier-bash-guard-test.sh
   ```
2. 請使用者跑 `/hooks` 重新 trust，然後**重開 session**（agents 與 settings 都要重載）。
3. 重開後**故意觸發一次 DENY**：在任一 harness 專案（有 `feature_list.json` 的 repo）試改一條已凍結的 acceptance，應被擋下並說明理由。沒被擋就是沒裝好，回 Step 1 查。

## 更新既有安裝

重跑 Step 1–2（同名檔案這次是預期覆蓋，仍先呈計畫）；settings 已有的條目不重複 append。改完跑 Step 4。

## Uninstall

1. 刪 `<config>/agents/` 下本 payload 的 4 支角色檔、`<config>/scripts/` 下本 payload 的 13 個檔案、`<config>/skills/harness-init/`。
2. 從 `<config>/settings.json` 的 `hooks.PreToolUse` 移除那三條（比對 command 字串），其餘設定不動。
3. 各專案 repo 裡的 harness 產物（`feature_list.json`、`.harness/` 等）屬於專案，不在本次移除範圍。
4. 呈現完整移除計畫並取得同意後才動手。

## 上限（先說清楚）

- hook 是 **fail-open**：payload 解析不了就放行。這是刻意設計——誤擋日常工作的代價高於漏抓，代價是壞掉時不噴錯，所以 Step 4 的回歸測試在你每次改動 hook 後都要重跑。
- 這層擋的是「無意間越權」，擋不住蓄意繞過。信任邊界仍在你核准了什麼 payload。
