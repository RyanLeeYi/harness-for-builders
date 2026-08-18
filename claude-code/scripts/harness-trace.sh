#!/usr/bin/env bash
# PreToolUse hook：開發 agent 越權偵測 + action trace。詳見 harness-trace.SPEC.md。
set -u
# HARNESS_TRACE_VAULT：知識庫根目錄（在裡面的 repo 不追蹤）；沒設就不排除任何路徑
VAULT_DIR="${HARNESS_TRACE_VAULT:-}"

stdin=""
IFS= read -r -d '' stdin || true
[ -n "$stdin" ] || exit 0

# bash 快速 gate：非 harness 專案即刻退出，不付 python 成本
cwd=""
[[ "$stdin" =~ \"cwd\":\"([^\"]*)\" ]] && cwd="${BASH_REMATCH[1]//\\\\//}"
if [ -z "$cwd" ]; then
  # 沒有 cwd 不代表「不在專案裡」——PreToolUse payload 一定帶 cwd，缺了就是契約漂移，
  # 而此時 hook 定位不到 repo，越權保護等同關閉。每天警告一次（無 repo 可寫 trace）。
  case "$stdin" in *'"hook_event_name":"PreToolUse"'*)
    GD="${HARNESS_TRACE_DIR:-$HOME/.claude/harness-trace}"
    mkdir -p "$GD" 2>/dev/null
    S="$GD/schema-drift-cwd-$(date +%Y%m%d)"
    if [ ! -e "$S" ]; then
      : >"$S" 2>/dev/null
      printf '{"systemMessage":"harness-trace：PreToolUse payload 缺 cwd 欄位——hook 無法定位 repo，越權保護形同關閉。請跑 ~/.claude/scripts/harness-trace-test.sh 並核對 payload 格式。"}\n'
    fi
  ;; esac
  exit 0
fi
command -v git >/dev/null 2>&1 || exit 0
repo_root=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null || true)
[ -n "$repo_root" ] || exit 0
# 注意空值語意：VAULT_DIR 為空時 `""*` 會匹配所有路徑而整支停用，所以先驗非空
if [ -n "$VAULT_DIR" ]; then
  case "$repo_root" in "$VAULT_DIR"*) exit 0 ;; esac
fi
[ -f "$repo_root/feature_list.json" ] || exit 0

GUARD_DIR="${HARNESS_TRACE_DIR:-$HOME/.claude/harness-trace}"
[ -d "$GUARD_DIR" ] || mkdir -p "$GUARD_DIR" 2>/dev/null

# python core 從獨立檔載入（不能用 `python - <<'PY'`：heredoc 會佔用 stdin，
# 使 payload JSON 進不到 sys.stdin）。stdin = payload；argv = repo_root, guard_dir。
CORE="$(dirname "${BASH_SOURCE[0]}")/harness-trace-core.py"
[ -f "$CORE" ] || exit 0
printf '%s' "$stdin" | PYTHONUTF8=1 python "$CORE" "$repo_root" "$GUARD_DIR"
exit 0
