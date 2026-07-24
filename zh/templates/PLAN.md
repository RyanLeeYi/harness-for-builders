---
updated: YYYY-MM-DD
status: 構想確認   # 構想確認 → MVP 開發中 → 迭代中 → 收官
repo: <repo 連結>
---

# <專案名稱> — PLAN

> 這份管「為什麼做、範圍、怎麼算成功」。是活文件:範圍變了就改。
> 「具體要什麼、怎麼算對」寫進 `docs/prd/`;「做到哪了」看 `feature_list.json`。

## 要解的問題
<誰的什麼痛>

## 成功指標(可量測,收官時回來對答案)
- <例:回答準確率 ≥ 80%(自建 20 題測試集)>
- <例:單次查詢延遲 < 3 秒>

## MVP 範圍
**做**:
- [ ] <核心功能 1>
- [ ] <核心功能 2>

**不做**(明確劃掉,防 scope creep):
- <例:不做 UI,CLI 就好>

## 技術選型
<一覽表;「為什麼選 A 不選 B」寫進 DECISIONS.md>

| 層 | 選擇 |
|----|------|
|    |      |

## 里程碑
- [ ] M1(日期):<可驗證的產出>
- [ ] M2(日期):<可驗證的產出>

## Agent Harness
- [ ] 動工日建 L1:`CLAUDE.md` + `init.sh` + `feature_list.json`(MVP 範圍逐條轉 feature + acceptance)
- [ ] 需求有模糊空間的 feature 先寫 PRD(`docs/prd/`)
- [ ] 第一個未完成收工的 session 前補 L2;bug 難查或功能變多時上 L3

## 品質標準(每個 feature 都適用)
- TDD:RED → GREEN → IMPROVE,覆蓋率 ≥ 80%
- 每個 feature 完成後 code review;status 改 passing 前找第二個 agent 驗收
- Commit 前:無硬編碼密鑰、輸入已驗證、錯誤訊息不洩漏敏感資料
- Conventional commits

## 收官 Checklist
- [ ] 成功指標回來對答案,數字寫進 DEVLOG 最後一筆
- [ ] Harness 消融檢討:哪些組件真的擋住問題、哪些是多餘開銷
- [ ] README 完整:問題 → 架構 → 安裝 → demo
