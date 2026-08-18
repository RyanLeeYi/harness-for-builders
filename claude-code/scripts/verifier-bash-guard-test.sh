#!/bin/bash
# verifier-bash-guard 回歸測試: 該擋的擋了 + 不該擋的沒擋 + fail-open
G="$(dirname "$0")/verifier-bash-guard.sh"
pass=0; fail=0

check() { # $1=描述 $2=payload(整段 stdin) $3=deny|allow
  out=$(printf '%s' "$2" | bash "$G")
  if [ "$3" = deny ]; then
    printf '%s' "$out" | grep -q '"permissionDecision":"deny"' && r=ok || r=NG
  else
    printf '%s' "$out" | grep -q '"permissionDecision":"deny"' && r=NG || r=ok
  fi
  if [ "$r" = ok ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL: $1"; fi
}

p() { printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$1"; }

# 該擋
check "git commit"        "$(p 'git commit -m fix')"            deny
check "git push"          "$(p 'git push origin main')"         deny
check "git reset hard"    "$(p 'git reset --hard HEAD')"        deny
check "git add"           "$(p 'git add -A')"                   deny
check "git checkout"      "$(p 'git checkout main')"            deny
check "串接尾端的 git push" "$(p 'npm test && git push')"          deny
check "大寫 GIT PUSH"      "$(p 'GIT PUSH origin main')"         deny
# 不該擋
check "git status"        "$(p 'git status --short')"           allow
check "git diff"          "$(p 'git diff HEAD')"                allow
check "git log"           "$(p 'git log --oneline -5')"         allow
check "npm test"          "$(p 'npm test')"                     allow
check "python 驗證腳本"    "$(p 'python verify_f1.py')"          allow
check "legit 不誤殺"       "$(p 'legit push data.csv')"          allow
check "append failures"   "$(p 'echo x >> .harness/failures.jsonl')" allow
# fail-open: 真實形狀但缺欄位 / 整包壞掉
check "缺 command 欄位"    '{"tool_name":"Bash","tool_input":{}}' allow
check "非 JSON payload"    'not json at all'                     allow

echo "pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
