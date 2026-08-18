#!/usr/bin/env bash
# PreToolUse hook：流程接錯（G1）與 cwd 漂移（G2）攔截。詳見 harness-gate.SPEC.md。
# 與 harness-trace 平行、不共用程式——那支的生效條件是「cwd 在 harness repo」，
# 而本支的 G2 要處理的恰是 cwd 不在 repo 的情形。
set -u

stdin=""
IFS= read -r -d '' stdin || true
[ -n "$stdin" ] || exit 0

# 預篩：stdin 同時不含 Skill 呼叫與任一 root 的目錄名 → 立刻退出，不付 python 啟動成本。
# 絕大多數 tool call 走到這裡就結束，成本是一次字串比對。
#
# 這裡刻意只認「這是不是一個 Skill 呼叫」，不認 skill 名——名單留在 core 一份。
# 舊版硬編單一 skill 包的 namespace 前綴，換包後整道 G1 會在這層靜默失效。
# HARNESS_GATE_ROOTS：分號分隔的專案根目錄清單；沒設時 G2 停用，G1（skill 閘門）照常
ROOTS_RAW="${HARNESS_GATE_ROOTS:-}"
hit=0
case "$stdin" in *'"skill"'*) hit=1 ;; esac
if [ "$hit" -eq 0 ]; then
  IFS=';' read -ra _roots <<< "$ROOTS_RAW"
  for _r in "${_roots[@]}"; do
    _b="${_r%/}"; _b="${_b##*/}"; _b="${_b##*\\}"
    [ -n "$_b" ] || continue
    case "$stdin" in *"$_b"*) hit=1; break ;; esac
  done
fi
[ "$hit" -eq 1 ] || exit 0

# core 從獨立檔載入（不能用 `python - <<'PY'`：heredoc 會佔用 stdin，
# 使 payload JSON 進不到 sys.stdin）。stdin = payload。
CORE="$(dirname "${BASH_SOURCE[0]}")/harness-gate-core.py"
[ -f "$CORE" ] || exit 0
command -v python >/dev/null 2>&1 || exit 0
printf '%s' "$stdin" | PYTHONUTF8=1 python "$CORE"
exit 0
