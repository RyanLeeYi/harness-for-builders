#!/usr/bin/env bash
# 驗證 harness-trace.sh：gate、trace 寫入、越權 DENY/RECORD、去重、防誤殺。
set -u
HOOK="$(dirname "$0")/harness-trace.sh"
BASE="${TMPDIR:-/tmp}/htrace-$$"
rm -rf "$BASE"; mkdir -p "$BASE"
trap 'rm -rf "$BASE"' EXIT
export HARNESS_TRACE_DIR="$BASE/guard"; mkdir -p "$HARNESS_TRACE_DIR"

pass=0; fail=0
ok(){ echo "PASS: $1"; pass=$((pass+1)); }
no(){ echo "FAIL: $1 -- $2"; fail=$((fail+1)); }

mkrepo(){ # $1=dir → git repo + feature_list.json(F1 passing, F2 failing)；echo repo toplevel
  local d="$1"; mkdir -p "$d"; git -C "$d" init -q
  cat >"$d/feature_list.json" <<'J'
{"features":[
 {"id":"F1","name":"a","acceptance":"do X","status":"passing","evidence":"e"},
 {"id":"F2","name":"b","acceptance":"do Y","status":"failing","evidence":null}
]}
J
  git -C "$d" rev-parse --show-toplevel
}

runhook(){ # $1=cwd $2=tool $3=tool_input_json [$4=sid]
  printf '{"session_id":"%s","cwd":"%s","hook_event_name":"PreToolUse","tool_name":"%s","tool_input":%s}' \
    "${4:-s1}" "$1" "$2" "$3" | bash "$HOOK"
}

REPO=$(mkrepo "$BASE/repo")
TRACE="$REPO/.harness/trace.jsonl"

# 1. 非 harness（git repo 但無 feature_list.json）→ 不介入
NOH="$BASE/plain"; mkdir -p "$NOH"; git -C "$NOH" init -q
NOH=$(git -C "$NOH" rev-parse --show-toplevel)
out=$(runhook "$NOH" Bash '{"command":"ls"}')
{ [ -z "$out" ] && [ ! -f "$NOH/.harness/trace.jsonl" ]; } && ok "非 harness 不介入" || no "非 harness 不介入" "out=<$out>"

# 2. 非 git 目錄 → 不介入
NG="$BASE/nogit"; mkdir -p "$NG"
out=$(runhook "$NG" Bash '{"command":"ls"}')
[ -z "$out" ] && ok "非 git 不介入" || no "非 git 不介入" "out=<$out>"

# 3. 正常 Bash → trace ok；feature 取自 .harness/current_feature 的明確宣告
#    （2026-07-30 起不再猜「第一個 failing」——那會讓歸因整批標錯，見 harness-trace.SPEC.md）
out=$(runhook "$REPO" Bash '{"command":"pytest -q"}')
{ [ -z "$out" ] && grep -q '"verdict":"ok"' "$TRACE" && grep -q '"feature":"?"' "$TRACE"; } \
  && ok "正常 Bash 記 ok；未宣告 → feature ?" \
  || no "正常 Bash（未宣告）" "out=<$out> trace=<$(cat "$TRACE" 2>/dev/null)>"

mkdir -p "$REPO/.harness"; printf 'F2\n' > "$REPO/.harness/current_feature"
: > "$TRACE"
out=$(runhook "$REPO" Bash '{"command":"pytest -q"}')
{ [ -z "$out" ] && grep -q '"feature":"F2"' "$TRACE"; } \
  && ok "宣告 current_feature → 歸因到該條" \
  || no "宣告 current_feature" "out=<$out> trace=<$(cat "$TRACE" 2>/dev/null)>"
rm -f "$REPO/.harness/current_feature"

# 4. frozen-acceptance（old_string 含既有 acceptance）→ block
out=$(runhook "$REPO" Edit '{"file_path":"'"$REPO"'/feature_list.json","old_string":"\"acceptance\":\"do Y\"","new_string":"\"acceptance\":\"do Z\""}')
{ echo "$out" | grep -q '"permissionDecision":"deny"' && grep -q 'blocked:frozen-acceptance' "$TRACE"; } \
  && ok "frozen-acceptance block" || no "frozen-acceptance" "out=<$out>"

# 4b. 新增 feature（old_string 不含既有 acceptance）→ 不誤擋
out=$(runhook "$REPO" Edit '{"file_path":"'"$REPO"'/feature_list.json","old_string":"]","new_string":",{\"id\":\"F3\",\"acceptance\":\"do W\",\"status\":\"failing\"}]"}')
echo "$out" | grep -q 'deny' && no "新增 feature 不誤擋" "out=<$out>" || ok "新增 feature 不誤擋"

# 4c. 尾錨追加新 feature：old_string 帶到前一條 acceptance，但值原樣保留 → 不誤擋（2026-07-25 retro）
out=$(runhook "$REPO" Edit '{"file_path":"'"$REPO"'/feature_list.json","old_string":"\"acceptance\":\"do Y\"}]","new_string":"\"acceptance\":\"do Y\"},{\"id\":\"F4\",\"acceptance\":\"do V\",\"status\":\"failing\"}]"}')
echo "$out" | grep -q 'deny' && no "尾錨追加不誤擋" "out=<$out>" || ok "尾錨追加新 feature 不誤擋"

# 4e. envelope 的 constraints 被改 → block（2026-08-05 envelope + slice）
out=$(runhook "$REPO" Edit '{"file_path":"'"$REPO"'/feature_list.json","old_string":"\"constraints\":[\"keep API v1\"]","new_string":"\"constraints\":[\"drop API v1\"]"}')
{ echo "$out" | grep -q '"permissionDecision":"deny"'; } \
  && ok "envelope constraints 被改 → block" || no "envelope constraints block" "out=<$out>"

# 4f. envelope 的 non_goals 新增一條（既有元素原樣保留）→ 不誤擋
out=$(runhook "$REPO" Edit '{"file_path":"'"$REPO"'/feature_list.json","old_string":"\"non_goals\":[\"no UI change\"]","new_string":"\"non_goals\":[\"no UI change\",\"no schema change\"]"}')
echo "$out" | grep -q 'deny' && no "non_goals 追加不誤擋" "out=<$out>" || ok "envelope non_goals 追加不誤擋"

# 4g. envelope 的 non_goals 刪掉既有一條 → 仍要擋
out=$(runhook "$REPO" Edit '{"file_path":"'"$REPO"'/feature_list.json","old_string":"\"non_goals\":[\"no UI change\",\"no schema change\"]","new_string":"\"non_goals\":[\"no schema change\"]"}')
echo "$out" | grep -q '"permissionDecision":"deny"' && ok "envelope non_goals 刪除仍擋" || no "envelope non_goals 刪除仍擋" "out=<$out>"

# 4d. 刪掉既有 acceptance（值沒原樣保留）→ 仍要擋
out=$(runhook "$REPO" Edit '{"file_path":"'"$REPO"'/feature_list.json","old_string":"\"acceptance\":\"do Y\"","new_string":"\"acceptance\":\"\""}')
echo "$out" | grep -q '"permissionDecision":"deny"' && ok "刪除既有 acceptance 仍擋" || no "刪除既有 acceptance 仍擋" "out=<$out>"

# 4e. Write 整檔覆寫 feature_list 且含 passing → RECORD status-to-passing（2026-07-25 retro）
out=$(runhook "$REPO" Write '{"file_path":"'"$REPO"'/feature_list.json","content":"{\"features\":[{\"id\":\"F1\",\"status\":\"passing\"}]}"}')
grep -q 'overreach:status-to-passing' "$TRACE" && ok "Write 覆寫 feature_list → status-to-passing"   || no "Write 覆寫 feature_list" "out=<$out> tail=<$(tail -1 "$TRACE")>"

# 4f. Bash 改 feature_list（python heredoc 之類）→ RECORD feature-list-via-bash（2026-07-25 retro）
out=$(runhook "$REPO" Bash '{"command":"python -c \"import json;d=json.load(open(1));json.dump(d,open(2,1))\" && echo done >> feature_list.json"}')
grep -q 'overreach:feature-list-via-bash' "$TRACE" && ok "Bash 寫 feature_list → RECORD"   || no "Bash 寫 feature_list → RECORD" "out=<$out> tail=<$(tail -1 "$TRACE")>"

# 4g. Bash 只是讀 feature_list → 不誤報
out=$(runhook "$REPO" Bash '{"command":"cat feature_list.json | head -5"}')
tail -1 "$TRACE" | grep -q 'feature-list-via-bash' && no "Bash 讀 feature_list 不誤報" "tail=<$(tail -1 "$TRACE")>"   || ok "Bash 讀 feature_list 不誤報"

# 5. denylist：rm -rf / push --force → block
out=$(runhook "$REPO" Bash '{"command":"rm -rf build/"}')
echo "$out" | grep -q 'deny' && ok "rm -rf block" || no "rm -rf block" "out=<$out>"
out=$(runhook "$REPO" Bash '{"command":"git push --force origin main"}')
echo "$out" | grep -q 'deny' && ok "push --force block" || no "push --force block" "out=<$out>"

# 6. git push 無 force → 不 block
out=$(runhook "$REPO" Bash '{"command":"git push origin main"}')
[ -z "$out" ] && ok "git push 非 force 不擋" || no "git push 非 force" "out=<$out>"

# 7. out-of-repo-write → 不 block、systemMessage、trace overreach（sid=s1 首次）
out=$(runhook "$REPO" Write '{"file_path":"'"$BASE"'/scratch.txt","content":"x"}')
if echo "$out" | grep -q 'deny'; then no "repo外寫入不擋" "out=<$out>"
elif echo "$out" | grep -q 'systemMessage' && grep -q 'overreach:out-of-repo-write' "$TRACE"; then ok "repo外寫入 record+flag"
else no "repo外寫入 record+flag" "out=<$out>"; fi

# 7c. scratchpad 寫入（temp/claude/ 下）→ 記 ok、不 flag（去雜訊；sid=s3 全新）
SCR="$BASE/Temp/claude/sess/scratchpad/verify.py"
out=$(runhook "$REPO" Write '{"file_path":"'"$SCR"'","content":"x"}' s3)
t1=$(tail -1 "$TRACE")
if echo "$out" | grep -q 'systemMessage'; then no "scratchpad 寫入不 flag" "應靜默 out=<$out>"
elif echo "$t1" | grep -q '"verdict":"ok"' && echo "$t1" | grep -q 'verify.py' && echo "$t1" | grep -q '"in_repo":false'; then ok "scratchpad 寫入記 ok 不 flag"
else no "scratchpad 寫入記 ok 不 flag" "tail=<$t1>"; fi

# 7d. vault projects/ 回寫（收官寫 DEVLOG）→ 記 ok、不 flag（2026-08-07）
#     規則要求收工回寫 vault，原本會被判 out-of-repo-write：規則叫寫、hook 記越權，
#     打架的結果是 vault 長期收不到收官紀錄。放行的只有 projects/ 子樹。
#     兩個 Windows 陷阱：① runhook 是 bash 函式，`VAR=x runhook` 只設 shell 變數，不會 export
#     給裡面的 `bash "$HOOK"`，要顯式 export；② MSYS 會把看起來像 POSIX 路徑的 env value 轉成
#     `C:/...` 再交給 python，而 JSON payload 裡的字串不會被轉——兩邊形式不同就永遠比不對。
#     所以 env 與 payload 一律走 `cygpath -m` 用同一種形式。
VP="$(cygpath -m "$BASE" 2>/dev/null || echo "$BASE")/Obsidian/projects"
export HARNESS_TRACE_VAULT_PROJECTS="$VP"
out=$(runhook "$REPO" Edit \
      '{"file_path":"'"$VP"'/2026-07-健身紀錄系統/DEVLOG.md","old_string":"a","new_string":"b"}' s4)
t1=$(tail -1 "$TRACE")
if echo "$out" | grep -q 'systemMessage'; then no "vault projects 回寫不 flag" "應靜默 out=<$out>"
elif echo "$t1" | grep -q '"verdict":"ok"' && echo "$t1" | grep -q 'DEVLOG.md'; then ok "vault projects 回寫記 ok 不 flag"
else no "vault projects 回寫記 ok 不 flag" "tail=<$t1>"; fi

# 7e. vault 其他區域（career/）仍要 flag——放行的是收官回寫，不是「整個 vault 隨便寫」
out=$(runhook "$REPO" Write '{"file_path":"'"$BASE"'/Obsidian/career/履歷.md","content":"x"}' s5)
if echo "$out" | grep -q 'systemMessage' && grep -q 'overreach:out-of-repo-write' "$TRACE"; then ok "vault career 寫入仍 flag"
else no "vault career 寫入仍 flag" "out=<$out>"; fi
unset HARNESS_TRACE_VAULT_PROJECTS

# 7f. 寫 .harness/current_feature（開工）→ parallel-check 提醒。
# 訊息本身也要真的印得出來——2026-08-17 初版塞了 U+26A0，cp950 stdout 直接 UnicodeEncodeError，
# 提醒發不出去而 sentinel 已建立，整個 session 再也不提醒。所以這裡驗 systemMessage 有出現，不只驗 trace。
out=$(runhook "$REPO" Write '{"file_path":"'"$REPO"'/.harness/current_feature","content":"F160"}' s6)
if echo "$out" | grep -q 'Traceback'; then no "開工 → parallel-check" "訊息無法輸出 out=<$out>"
elif echo "$out" | grep -q 'systemMessage' && grep -q 'overreach:parallel-check' "$TRACE"; then ok "開工 → parallel-check"
else no "開工 → parallel-check" "out=<$out>"; fi

out=$(runhook "$REPO" Write '{"file_path":"'"$REPO"'/.harness/current_feature","content":"F161"}' s6)
if echo "$out" | grep -q 'systemMessage'; then no "parallel-check 去重" "同 session 應靜默 out=<$out>"
else ok "parallel-check 去重"; fi

# 7g. 本 session 第一次寫原始碼 → 記 note:first-source-write，且**不得**發任何 systemMessage。
# 這是 Approval 關卡的代理訊號（見 silent_mark 的註解）；一旦它開始提醒就會洗頻，所以靜默是規格不是細節。
out=$(runhook "$REPO" Write '{"file_path":"'"$REPO"'/app.py","content":"x"}' s7)
if echo "$out" | grep -q 'systemMessage'; then no "第一次寫原始碼 → 靜默記錄" "不該有訊息 out=<$out>"
elif grep -q 'note:first-source-write' "$TRACE"; then ok "第一次寫原始碼 → 靜默記錄"
else no "第一次寫原始碼 → 靜默記錄" "tail=<$(tail -1 "$TRACE")>"; fi

# 同 session 第二次不再記（否則每次寫檔都標一次，統計就沒意義）
runhook "$REPO" Write '{"file_path":"'"$REPO"'/app2.py","content":"x"}' s7 >/dev/null
if [ "$(grep -c 'note:first-source-write' "$TRACE")" = "1" ]; then ok "first-source-write 每 session 只記一次"
else no "first-source-write 每 session 只記一次" "count=$(grep -c 'note:first-source-write' "$TRACE")"; fi

# 文件與 .harness 不算原始碼
runhook "$REPO" Write '{"file_path":"'"$REPO"'/README.md","content":"x"}' s8 >/dev/null
if [ "$(grep -c 'note:first-source-write' "$TRACE")" = "1" ]; then ok "文件寫入不算原始碼"
else no "文件寫入不算原始碼" "count=$(grep -c 'note:first-source-write' "$TRACE")"; fi

# 8. status failing→passing → 不 block、systemMessage、trace（sid=s2 避免與 test7 去重衝突）
out=$(runhook "$REPO" Edit '{"file_path":"'"$REPO"'/feature_list.json","old_string":"\"status\":\"failing\"","new_string":"\"status\":\"passing\""}' s2)
if echo "$out" | grep -q 'deny'; then no "status→passing 不擋" "out=<$out>"
elif grep -q 'overreach:status-to-passing' "$TRACE"; then ok "status→passing record"
else no "status→passing record" "out=<$out> tail=<$(tail -1 "$TRACE")>"; fi

# 9. RECORD systemMessage 同 sid 同 rule 第二次 → 靜默（sid=s1 已在 test7 flag 過 out-of-repo）
out=$(runhook "$REPO" Write '{"file_path":"'"$BASE"'/scratch2.txt","content":"y"}' s1)
echo "$out" | grep -q 'systemMessage' && no "record 去重" "應靜默 out=<$out>" || ok "record systemMessage 去重"

# 10. .gitignore 自動補 .harness/
grep -q '^\.harness/' "$REPO/.gitignore" && ok ".gitignore 補 .harness/" || no ".gitignore" "content=<$(cat "$REPO/.gitignore" 2>/dev/null)>"

# 11. feature heuristic：無 failing → feature=?
R2="$BASE/repo2"; mkdir -p "$R2"; git -C "$R2" init -q
cat >"$R2/feature_list.json" <<'J'
{"features":[{"id":"F1","name":"a","acceptance":"x","status":"passing","evidence":"e"}]}
J
R2=$(git -C "$R2" rev-parse --show-toplevel)
out=$(runhook "$R2" Bash '{"command":"ls"}')
grep -q '"feature":"?"' "$R2/.harness/trace.jsonl" && ok "無 failing → feature ?" \
  || no "無 failing feature ?" "trace=<$(cat "$R2/.harness/trace.jsonl" 2>/dev/null)>"

# --- schema-drift：payload 契約漂移偵測（開放契約：只驗必要欄位在，多的欄位不管） ---

# 12. 缺 tool_name → 不 block、systemMessage、trace verdict schema-drift
out=$(printf '{"session_id":"d1","cwd":"%s","hook_event_name":"PreToolUse","toolName":"Bash","tool_input":{"command":"ls"}}' "$REPO" | bash "$HOOK")
t1=$(tail -1 "$TRACE")
if echo "$out" | grep -q 'deny'; then no "缺 tool_name 不擋" "out=<$out>"
elif echo "$out" | grep -q 'systemMessage' && echo "$t1" | grep -q '"verdict":"schema-drift:tool_name"'; then ok "缺 tool_name → schema-drift"
else no "缺 tool_name → schema-drift" "out=<$out> tail=<$t1>"; fi

# 13. 缺 tool_input（tool_name 在）→ schema-drift，且不可被誤判成正常 ok
out=$(printf '{"session_id":"d2","cwd":"%s","hook_event_name":"PreToolUse","tool_name":"Bash","toolInput":{"command":"rm -rf /"}}' "$REPO" | bash "$HOOK")
t1=$(tail -1 "$TRACE")
if echo "$t1" | grep -q '"verdict":"schema-drift:tool_input"' && echo "$out" | grep -q 'systemMessage'; then ok "缺 tool_input → schema-drift"
else no "缺 tool_input → schema-drift" "out=<$out> tail=<$t1>"; fi

# 14. 多出未知欄位 → 正常運作，不得誤報 drift（開放契約，別鎖封閉欄位集合）
out=$(printf '{"session_id":"d3","cwd":"%s","hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"pytest -q"},"futureField":"x","another":{"n":1}}' "$REPO" | bash "$HOOK")
t1=$(tail -1 "$TRACE")
if echo "$t1" | grep -q 'schema-drift'; then no "未知欄位不誤報 drift" "tail=<$t1>"
elif [ -z "$out" ] && echo "$t1" | grep -q '"verdict":"ok"'; then ok "未知欄位不誤報 drift"
else no "未知欄位不誤報 drift" "out=<$out> tail=<$t1>"; fi

# 15. schema-drift systemMessage 同 sid 去重（d1 已在 test12 報過）
out=$(printf '{"session_id":"d1","cwd":"%s","hook_event_name":"PreToolUse","toolName":"Bash","tool_input":{"command":"ls"}}' "$REPO" | bash "$HOOK")
echo "$out" | grep -q 'systemMessage' && no "schema-drift 去重" "應靜默 out=<$out>" || ok "schema-drift systemMessage 去重"

# 16. 缺 cwd（bash gate 前的漂移）→ 警告一次，不靜默死掉
rm -f "$HARNESS_TRACE_DIR"/schema-drift-cwd-* 2>/dev/null
out=$(printf '{"session_id":"d4","workingDir":"%s","hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"ls"}}' "$REPO" | bash "$HOOK")
echo "$out" | grep -q 'systemMessage' && ok "缺 cwd → 警告" || no "缺 cwd → 警告" "out=<$out>"

echo "----"; echo "pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
