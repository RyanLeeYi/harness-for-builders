#!/bin/bash
# verifier-bash-guard: acceptance-verifier 專用的 Bash 指令閘門(掛在 agent frontmatter 的 PreToolUse)
# 只擋會改變 repo 狀態的 git 指令--驗收者是唯讀角色,測試/腳本執行不受影響
# 鐵律: fail-open--payload 解析不了就放行,不擋
# 用 python 解析 JSON(這台機器的 git bash 沒有 jq)

# 先收 stdin 再進 python--heredoc 會佔用 python 的 stdin,不能讓它直接讀 payload
HOOK_PAYLOAD=$(cat) python - <<'PYEOF'
import json, os, re, sys

try:
    payload = json.loads(os.environ.get("HOOK_PAYLOAD", ""))
    cmd = payload.get("tool_input", {}).get("command", "")
except Exception:
    sys.exit(0)  # fail-open

if not isinstance(cmd, str) or not cmd:
    sys.exit(0)

MUTATING = re.compile(
    r"\bgit\s+(commit|push|add|reset|restore|checkout|switch|merge|rebase"
    r"|clean|stash|rm|mv|cherry-pick|revert|am|apply|tag|branch\s+-[dDmM])\b",
    re.IGNORECASE,
)

if MUTATING.search(cmd):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "驗收者不得執行會改變 repo 狀態的 git 指令(唯讀角色)。"
                "要看變更用 git status / diff / log。發現問題描述它,不要動它。"
            ),
        }
    }, separators=(",", ":")))  # ensure_ascii 預設 True: 中文以 \u escape 輸出,免疫 cp950 stdout

sys.exit(0)
PYEOF
