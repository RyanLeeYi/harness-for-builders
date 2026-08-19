**[English](../README.md)** | **繁體中文**

# Harness for Builders

> AI coding agent 的可靠性不來自 prompt 寫得多好——來自 repo 裡的結構化產物。
> 這個框架告訴你該建哪些檔案、什麼時候建，而且建置這件事本身可以交給你的 agent。

**Harness for Builders** 是一套工具中立的框架，用來打造一個 AI agent 能可靠工作的 repo：Claude Code、Cursor、Codex，或任何讀寫得了檔案的工具都適用。它裝進你 repo 的是檔案，不是 runtime 或服務。動工日必建三個檔案；其餘每個產物都有自己的觸發條件——痛點出現才加，不再發揮作用就刪。

它有兩條車道。**車道 A（任何工具）**：訪談引導、自己建 repo 產物——見[開始使用](#開始使用)。**車道 B（Claude Code）**：加裝強制層——凍結 acceptance 與危險命令的 DENY hook、四支釘死邊界的角色檔——見[安裝](#安裝claude-code-強制層)。車道 A 永遠不依賴車道 B。

> By [Ryan Lee](https://github.com/RyanLeeYi) · **v2.0** · 最後更新 2026-08-18 · [Changelog](../CHANGELOG.md)

## 目錄

- [為什麼需要](#為什麼需要)
- [怎麼運作](#怎麼運作)
- [開始使用](#開始使用)
- [安裝（Claude Code 強制層）](#安裝claude-code-強制層)
- [日常操作](#日常操作)
- [文件](#文件)
- [上限](#上限)
- [授權與致謝](#授權與致謝)

## 為什麼需要

把越多工作交給 AI agent——寫功能、修 bug、重構——它就越需要一個「知道現況」的地方：專案怎麼跑、規則是什麼、範圍在哪、上次做到哪。那個地方就是你的 **harness**。沒有它，你會撞上一組測試蓋不到的失效點——它們是「協作」的失敗，不是「程式」的失敗：

| 症狀 | 用什麼擋 |
|------|----------|
| Agent 忘記上次做到哪，每個 session 重新摸索 | `session-handoff.md` + 固定開場 prompt |
| 宣稱「做完了」但沒實際驗證 | `feature_list.json` 的 evidence 閘門 |
| 動到不該碰的東西、擅自擴大範圍 | `ARCHITECTURE.md` 邊界 + 「清單外的事不做」 |
| 為了讓測試過，偷偷放寬標準 | **凍結 acceptance** |
| 每個 session 重讀整個 codebase，燒光 context | 索引化的 `CLAUDE.md` + 檔案瘦身 |

prompt 每個 session 重來一次、會漂移、會被忘記；檔案不會——它躺在 repo 裡當唯一事實來源。harness 用**檔案**把每個失效點釘死，而不是每次用 prompt 提醒。

## 怎麼運作

一個沒有任何對話歷史的新 agent 打開你的 repo，必須答得出四個問題：

```
   怎麼跑起來？    ----->  init.sh
   現在做到哪？    ----->  feature_list.json + session-handoff.md
   下一步做什麼？  ----->  feature_list.json 裡第一條 failing
   怎樣算做完？    ----->  該 feature 的 acceptance（已凍結）

   有一題答不出來 = harness 有缺口 -> 用檔案補，不是用 prompt 補
```

三個檔案從動工日就負責回答它們。其餘全部**痛點觸發**：每個產物都有明確的「什麼時候加」——也有明確的「什麼時候刪」，因為只有加入路徑的 harness 保證單向長胖：加東西感覺安全、刪東西感覺有風險，陳舊的層會沉積下來。沒有階梯要爬、沒有升降級儀式，觸發條件就是全部的規則。

| 產物 | 什麼時候加 | 什麼時候刪 |
|------|-----------|-----------|
| `CLAUDE.md` + `init.sh` + `feature_list.json` | 動工日、第一行 code 之前（約 20 分鐘） | 不刪——這就是 harness |
| `session-handoff.md` | 第一次沒做完就收工之前 | 連續數個 session 沒被讀過 |
| `docs/ARCHITECTURE.md` | 新 agent 無法從 code 看出邊界與資料流 | code 已經自己講得清楚 |
| 結構化日誌、邊界 guard 腳本、獨立驗收者 | 事故觸發：同型錯誤重複發生、bug 無法從既有 log 定位、邊界違規實際發生過。功能數量**永遠不是**理由 | 累積足夠樣本仍沒攔到任何一次真實越權 |

```
 你的 repo
 |
 |- 動工日必建 ---------------------------------------------------
 |   |- CLAUDE.md ............ 規則、指令、邊界（每個 session 都讀）
 |   |- init.sh .............. 一個指令回到「可開發可驗證」狀態
 |   |- feature_list.json .... 範圍與驗收的狀態機
 |                             * acceptance 簽核後凍結，動工之前
 |                             * 沒有 evidence 不得翻 passing
 |                             * prerequisites 要申報；沒申報 != 沒有
 |
 |- 痛點觸發，各走各的時鐘 ---------------------------------------
 |   |- session-handoff.md ... 上次做到哪（覆寫，不累積）
 |   |- docs/ARCHITECTURE.md . 結構、資料流、邊界（只寫現況）
 |   |- 結構化日誌 ........... 讓 agent 看得到自己為什麼失敗
 |   |- check-architecture.sh  邊界規則變成跑得起來的檢查
 |   |- 獨立驗收者 ........... 另一個 fresh-context agent，只餵
 |                             凍結的 acceptance + 成品，不給過程
 |
 |- docs/ -- 收官才讀，不進日常 context --------------------------
     |- PLAN.md ............. 為什麼做、範圍、成功指標
     |- DEVLOG.md ........... 卡點與解法（onboarding / retro 素材）
     |- DECISIONS.md ........ 難回頭的選擇與理由
     |- prd/（選配）......... 給團隊或非工程讀者的敘事規格
     |- archive/ ............ passing feature 的 acceptance 原文歸檔
```

關鍵名詞一口氣講完：**harness** 是上面那組檔案——工作環境，不是框架程式碼。**feature_list.json** 是範圍的狀態機：一條 feature 一個條目，status 只有 `failing`/`passing`，翻 passing 一律要證據。**acceptance** 是「怎麼驗證做完了」——動工前寫好、簽核、然後**凍結**：整套 harness 最重要的一個詞。

### 角色與委派

harness 管檔案；這一節管**工作誰來做**。它是工具中立的——不管你的 agent 工具有沒有 subagent、多模型，還是只有多開幾個視窗，同一套分工都適用。

**預設：主 session 自己做。** 委派有真實成本（重送 context、丟掉思路）。派工前先過 [baton](https://github.com/cablate/baton) 的五問煞車——Outcome（交付物與可觀察的完成條件講得出來嗎）、Direct-work（一個 agent 自己做會不會更快更穩）、Independence（各條不重讀同一批來源、不互等）、Ownership（每個檔案只有一個主人）、Closure（誰整合、誰解矛盾、誰跑最終驗證）。任一答不出就不派。本地不要再維護第二份同樣的規則，只留 baton 沒有的：不可外包清單，以及五問對應到你自己機制的那張表。

真的要分工時，worker 只有三種，差別在**它是為了什麼存在**：

| 角色 | 目的 | 契約 |
|------|------|------|
| **執行者** | 省下主 session 的預算，做範圍已定的實作 | 派工前五件事要齊：目標、限制、完成條件、檔案路徑、原因。缺一項就不派。永遠不給它架構決策、範圍變更、安全工作 |
| **探索者** | 唯讀搜尋，避免灌爆主 context | 四件事要齊：問題、範圍、證據格式、停止條件 |
| **檢查者** | 回答「做對了沒」，不帶作者的偏袒 | **只餵凍結的 acceptance 與成品**——不給開發過程、不給作者的辯護。獨立性來自 fresh context，不是來自換一顆模型。一個軸只跑一個檢查者；疊第二個同模型檢查者是成本翻倍換假獨立，因為分身共享同一套誤讀 |

派工單的內容比派工的時機更容易出錯,而且錯法很隱蔽:**worker 通常不是站在你腳下**。隔離用的 worktree 一般從遠端的預設分支開,不是從你的 HEAD —— 所以你剛 commit 但還沒 push 的規格,它看不到,而 `git status` 是乾淨的,什麼都不會提醒你。所以規格**原文直接寫進派工 prompt**,並明講「prompt 裡這份就是權威來源,不要回去 feature list 找它,找不到也不要因此停下」。少了後面那句,worker 會照 repo 入口規則去查表、查不到就正確地停工,而你付了一整輪。

worker 回報「我看到的檔案跟你講的不一樣」時,**先去驗它的基準,不要先假設它讀錯**。這條是 2026-08-19 買來的:同一條 feature 連續兩輪派工報廢,主 session 兩次都不信 worker,第二輪才發現基準落後本機 8 個 commit —— 兩次回報都是對的。

兩件事永遠留在主 session：**未知 bug 的診斷**（trace、假設、修補、驗證是同一條耦合路徑，拆成 pipeline 會把思路拆斷），以及**對檢查結果的最終判斷**（檢查者報嚴重度與證據；修不修、延不延、駁不駁是編排者的工作，外包不出去）。

設計理由——包括「生成者不得驗收自己的產出」——在 [architecture.md](architecture.md)。

規格放哪，一條規則：**acceptance 是權威，而且必須自足**——不用打開別的文件就能逐條判定。PRD 可以有，當作給團隊與非工程讀者的敘事；但如果你的凍結保護只蓋 `feature_list.json`，宣告「以 PRD 為準」就是把權威交給唯一沒有保護的那份檔案。完整的失敗故事在 [setup-guide](setup-guide.md)。

## 開始使用

你需要：一個 git repo（新舊皆可）、一個 AI coding agent、20 分鐘建起手三檔。

**你可以把整個 repository 丟給你的 agent，它會帶你建完。** 在你的專案裡打開 agent，貼上：

```text
讀 https://github.com/RyanLeeYi/harness-for-builders —— 從 README.md 開始，
然後照 zh/setup-guide.md 一步步在這個 repo 建出最小 harness。
骨架（init.sh、feature_list.json）可以直接建，但核心內容不准猜：
每條 feature 的 acceptance、架構邊界、專案規則，要逐層訪談我來定。
動筆前先給我看完整的檔案計畫。
```

Agent 唯一不能替你做的事，是決定**怎樣算做完**。acceptance 寫錯，整套 harness 就在驗證錯的東西——所以 setup-guide 是一場訪談，不是一張表單。

## 安裝（Claude Code 強制層）

上面的一切靠約定運作——agent 讀了檔案、同意遵守。這條車道給規則裝上**牙齒**：在工具執行前就 DENY。它裝進你的全域 Claude Code 設定：

- **3 支 hook**——已簽核 acceptance 的凍結保護（Edit/Write/Bash 三條路徑都蓋）、危險命令攔截（`rm -rf`、force push、`--no-verify`）、與 harness 流程競爭的規劃 skill 閘門、檔案 emoji 閘門；每支自帶回歸測試
- **4 支角色檔**——執行者、探索者、兩種檢查者，模型與唯讀邊界釘在 frontmatter（驗收者自帶 hook，會改變 repo 狀態的 git 指令直接 DENY）
- **1 支 skill**——`/harness-init`：在任何 repo 建出符合規格的最小 harness，接著訪談你定第一條 acceptance

Clone 本 repo，在裡面啟動 Claude Code，貼上：

```text
讀這個 checkout 裡的 install/AGENT-INSTALL.md，照它把 harness 強制層裝進我的
全域 Claude Code 設定。動筆前先給我看完整的合併計畫、取得我的同意。
```

> **信任邊界**：這份 payload 會載入你每個未來的 session。核准寫入前先審
> [claude-code/](../claude-code/)——角色檔、腳本、settings 片段。runbook 的
> 收尾是跑完四套測試並故意觸發一次 DENY：沒驗過的防線等於沒有防線。

裝完 `/hooks` 重新 trust 並重開 session。Uninstall 步驟在同一份 runbook。

## 日常操作

| 任務 | 去哪裡 |
|------|--------|
| 建最小 harness，痛點出現再加產物 | [Setup guide](setup-guide.md) |
| 理解設計：為什麼痛點觸發、為什麼凍結 acceptance | [Architecture](architecture.md) |
| 專案變大時維持每 session 必讀檔的精瘦 | [Optimization guide](optimization-guide.md) |
| 直接用現成模板開工 | [templates/](templates/) |
| 團隊 repo、工具混雜、沒有 CI | [project-harness-kit](https://github.com/RyanLeeYi/project-harness-kit) —— 可執行關卡變體 |
| 看這套方法的個人實際部署 | [ai-dev-harness](https://github.com/RyanLeeYi/ai-dev-harness) —— 活的地圖 |

## 文件

| 主題 | 文件 |
|------|------|
| 逐步建置與訪談流程 | [zh/setup-guide.md](setup-guide.md) · [English](../en/setup-guide.md) |
| 設計決策與取捨 | [zh/architecture.md](architecture.md) · [English](../en/architecture.md) |
| 常駐檔案瘦身 | [zh/optimization-guide.md](optimization-guide.md) · [English](../en/optimization-guide.md) |
| 可複製的模板 | [zh/templates/](templates/) · [English](../en/templates/) |
| 版本紀錄 | [CHANGELOG.md](../CHANGELOG.md) |

## 上限

先講清楚，因為知道上限才用得對：

- **凍結不等於不會錯。** 凍結的 acceptance 也可能把現實描述錯。驗收 fail 對上的是規格 bug 時，回簽核流程改規格——不要把實作扭去對齊錯的目標。
- **harness 管流程，不管正確性。** 它是測試之外的一層：範圍、交接、context、越權。功能本身對不對，仍取決於你寫的 acceptance。
- **檔案擋不住蓄意造假。** evidence 閘門擋的是「順手宣稱完成」；有寫檔權限的 agent 可以偽造。真正的強制要靠 agent 碰不到的檢查——腳本、hook、PR 關卡（見邊界 guard 與 project-harness-kit）。
- **不要 cargo-cult。** 小工具一輩子只靠起手三檔是正確的，不是偷懶。收官時問一句：這次哪個組件真的發揮了作用？沒發揮的，下個專案不照抄。

## 授權與致謝

方法改編自 [Learn Harness Engineering](https://walkinglabs.github.io/learn-harness-engineering/zh-TW/projects/)。「文件丟給任何 AI 就能自我建置」的形態借自 CW Lin 的 [Vault for Founders](https://github.com/cwlin0131/Vault-for-Founders)。本 README 的敘事結構參考 [pilotfish](https://github.com/Nanako0129/pilotfish)。

MIT License —— 見 [LICENSE](../LICENSE)。
