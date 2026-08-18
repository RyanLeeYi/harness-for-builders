#!/usr/bin/env bash
# 驗證 harness-gate.sh：G1 流程接錯（Skill gate）、G2 cwd 漂移、去重、防誤殺。
# 2026-07-28 教訓：fail-open 的東西壞掉不噴錯，只會安靜放行——該擋與不該擋的情境都要實跑。
set -u
HOOK="$(dirname "$0")/harness-gate.sh"
BASE="${TMPDIR:-/tmp}/hgate-$$"
rm -rf "$BASE"; mkdir -p "$BASE"
trap 'rm -rf "$BASE"' EXIT

export HARNESS_GATE_DIR="$BASE/guard"; mkdir -p "$HARNESS_GATE_DIR"
export HARNESS_GATE_ROOTS="$BASE/SideProject"
export HARNESS_GATE_VAULT="$BASE/Obsidian"

pass=0; fail=0
ok(){ echo "PASS: $1"; pass=$((pass+1)); }
no(){ echo "FAIL: $1 -- $2"; fail=$((fail+1)); }

mkharness(){ # $1=dir → git repo + feature_list.json；echo toplevel
  local d="$1"; mkdir -p "$d"; git -C "$d" init -q
  printf '{"features":[{"id":"F1","name":"a","acceptance":"do X","status":"failing","evidence":null}]}\n' >"$d/feature_list.json"
  git -C "$d" rev-parse --show-toplevel
}

runhook(){ # $1=cwd $2=tool $3=tool_input_json [$4=sid]
  printf '{"session_id":"%s","cwd":"%s","hook_event_name":"PreToolUse","tool_name":"%s","tool_input":%s}' \
    "${4:-s1}" "$1" "$2" "$3" | bash "$HOOK"
}
runhook_nocwd(){ # $1=tool $2=tool_input_json
  printf '{"session_id":"s1","hook_event_name":"PreToolUse","tool_name":"%s","tool_input":%s}' \
    "$1" "$2" | bash "$HOOK"
}

MC=$(mkharness "$BASE/SideProject/mission-control")
LL=$(mkharness "$BASE/SideProject/lift-log")
PLAIN="$BASE/SideProject/plain"; mkdir -p "$PLAIN"          # 無 feature_list.json
HOME_DIR="$BASE/home"; mkdir -p "$HOME_DIR"                  # 非 git
VAULT="$BASE/Obsidian"; mkdir -p "$VAULT"; git -C "$VAULT" init -q
VAULT=$(git -C "$VAULT" rev-parse --show-toplevel)

echo "--- G1：流程接錯（Skill gate）---"

# 1. to-tickets @ harness repo → DENY
out=$(runhook "$MC" Skill '{"skill":"to-tickets"}' g1a)
echo "$out" | grep -q '"permissionDecision":"deny"' \
  && ok "1. to-tickets @ harness repo → DENY" || no "1. to-tickets @ harness repo → DENY" "out=<$out>"

# 2. to-spec @ harness repo → DENY
out=$(runhook "$LL" Skill '{"skill":"to-spec"}' g1b)
echo "$out" | grep -q '"permissionDecision":"deny"' \
  && ok "2. to-spec @ harness repo → DENY" || no "2. to-spec @ harness repo → DENY" "out=<$out>"

# 3. to-spec @ 家目錄（非 git）→ 提醒不擋
out=$(runhook "$HOME_DIR" Skill '{"skill":"to-spec"}' g1c)
{ echo "$out" | grep -q 'systemMessage' && ! echo "$out" | grep -q 'deny'; } \
  && ok "3. to-spec @ 家目錄 → 提醒不擋" || no "3. to-spec @ 家目錄 → 提醒不擋" "out=<$out>"

# 4. to-spec @ vault → 不介入
out=$(runhook "$VAULT" Skill '{"skill":"to-spec"}' g1d)
[ -z "$out" ] && ok "4. to-spec @ vault → 不介入" || no "4. to-spec @ vault → 不介入" "out=<$out>"

# 4b. 訪談類 @ harness repo → 放行（終點是 CONTEXT.md／ADR，不跟 feature_list 競爭）
for s in grill-me grilling grill-with-docs; do
  out=$(runhook "$MC" Skill "{\"skill\":\"mattpocock-skills:$s\"}" "g1-$s")
  [ -z "$out" ] && ok "4b. $s @ harness repo → 放行" || no "4b. $s 不該被擋" "out=<$out>"
done

# 5. 名單外的 skill @ harness repo → 放行（TDD 在 harness 專案照樣該用）
out=$(runhook "$MC" Skill '{"skill":"tdd"}' g1e)
[ -z "$out" ] && ok "5. tdd @ harness repo → 放行" || no "5. tdd skill 不該被擋" "out=<$out>"

# 6. 帶 namespace 前綴 @ harness repo → 一樣 DENY（換 skill 包不得靜默繞過）
out=$(runhook "$MC" Skill '{"skill":"mattpocock-skills:to-tickets"}' g1f)
echo "$out" | grep -q '"permissionDecision":"deny"' \
  && ok "6. mattpocock-skills:to-tickets → DENY（剝前綴比對）" || no "6. 帶前綴的 skill 沒被擋" "out=<$out>"

# 7. 帶任意 namespace 前綴的 brainstorming → 仍 DENY（換 skill 包不該讓閘門失效）
out=$(runhook "$MC" Skill '{"skill":"anypkg:brainstorming"}' g1g)
echo "$out" | grep -q '"permissionDecision":"deny"' \
  && ok "7. anypkg:brainstorming → 仍 DENY" || no "7. 帶前綴的舊名沒被擋" "out=<$out>"

# 8. grilling @ harness repo → 放行（訪談類終點是 CONTEXT.md／ADR,不與 feature_list 競爭）
#    2026-08-18：本條原本測 `/prd`,該 skill 隨 PRD 層一併移除。留一條「不該擋的沒擋」,
#    否則 GATED_SKILLS 哪天擴張成擋所有 skill,測試仍會全綠。
out=$(runhook "$MC" Skill '{"skill":"mattpocock-skills:grilling"}' g1f)
[ -z "$out" ] && ok "8. grilling @ harness repo → 放行" || no "8. grilling 不該被擋" "out=<$out>"

echo "--- G2：cwd 漂移 ---"

# 7. 在家目錄 Read harness repo 的檔 → 提醒
out=$(runhook "$HOME_DIR" Read '{"file_path":"'"$MC"'/AGENTS.md"}' g2a)
{ echo "$out" | grep -q 'systemMessage' && ! echo "$out" | grep -q 'deny'; } \
  && ok "7. 家目錄 Read repo 檔 → 提醒" || no "7. 家目錄 Read repo 檔 → 提醒" "out=<$out>"

# 8. cwd 已在該 repo → 放行
out=$(runhook "$MC" Read '{"file_path":"'"$MC"'/AGENTS.md"}' g2b)
[ -z "$out" ] && ok "8. cwd 在該 repo → 放行" || no "8. cwd 在該 repo 不該提醒" "out=<$out>"

# 9. cwd 在另一個 harness repo → 提醒（跨專案）
out=$(runhook "$LL" Read '{"file_path":"'"$MC"'/AGENTS.md"}' g2c)
echo "$out" | grep -q 'systemMessage' \
  && ok "9. cwd 在別的 repo → 提醒" || no "9. cwd 在別的 repo → 提醒" "out=<$out>"

# 10. SideProject 下但無 feature_list.json → 放行（兩者兵接的第二段）
out=$(runhook "$HOME_DIR" Read '{"file_path":"'"$PLAIN"'/notes.md"}' g2d)
[ -z "$out" ] && ok "10. 非 harness 專案目錄 → 放行" || no "10. 非 harness 專案不該提醒" "out=<$out>"

# 11. 同 session 同專案第二次 → 靜默
runhook "$HOME_DIR" Read '{"file_path":"'"$MC"'/AGENTS.md"}' g2e >/dev/null
out=$(runhook "$HOME_DIR" Read '{"file_path":"'"$MC"'/session-handoff.md"}' g2e)
[ -z "$out" ] && ok "11. 同 session 同專案第二次 → 靜默" || no "11. 去重失效" "out=<$out>"

# 12. Bash command 內含 repo 路徑、cwd 在家目錄 → 提醒
out=$(runhook "$HOME_DIR" Bash '{"command":"ls '"$MC"'/docs"}' g2f)
echo "$out" | grep -q 'systemMessage' \
  && ok "12. Bash 提到 repo 路徑 → 提醒" || no "12. Bash 提到 repo 路徑 → 提醒" "out=<$out>"

# 13. payload 缺 cwd → 不介入（fail-open）
out=$(runhook_nocwd Read '{"file_path":"'"$MC"'/AGENTS.md"}')
[ -z "$out" ] && ok "13. 缺 cwd → 不介入" || no "13. 缺 cwd 應 fail-open" "out=<$out>"

# 14. 在 repo 內 Edit 自己的檔 → 放行（最常見的正常情形，絕不能吵）
out=$(runhook "$LL" Edit '{"file_path":"'"$LL"'/src/app.py","old_string":"a","new_string":"b"}' g2g)
[ -z "$out" ] && ok "14. repo 內 Edit → 放行" || no "14. repo 內 Edit 不該提醒" "out=<$out>"

# 15. 非法 JSON → 不介入（fail-open）。
#     2026-07-31：作者自己的 live 測試就寫出 "cwd":"C:\Users\user"（\U 不是合法 JSON 跳脫），
#     hook 靜默不介入，一度被誤判成「hook 壞了」。行為正確，但這一型要有測試釘住。
out=$(printf '{"session_id":"s9","cwd":"C:\\Users\\user","tool_name":"Read","tool_input":{"file_path":"'"$MC"'/AGENTS.md"}}' | bash "$HOOK")
[ -z "$out" ] && ok "15. 非法 JSON → 不介入（fail-open）" || no "15. 非法 JSON 應 fail-open" "out=<$out>"

echo
echo "PASS=$pass FAIL=$fail"
[ "$fail" -eq 0 ]
