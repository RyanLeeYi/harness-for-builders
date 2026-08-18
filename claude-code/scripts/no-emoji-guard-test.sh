#!/bin/bash
# no-emoji-guard-test.sh — 跑一輪就知道 guard 還活著沒。
#
# 為什麼需要：這支 hook 的失敗模式是「無聲放行」——payload 解不開就 exit 0。
# 所以「沒被擋」不等於「沒有 emoji」，也可能是牆倒了。定期跑這支確認會擋的還會擋。
#
# 兩個踩過的坑，改這支之前先讀：
#
# 1) 一定要用 printf 餵 payload，不要用 echo。Git Bash 的 echo 會吃掉 JSON 裡的反斜線
#    （Windows 路徑全是反斜線），JSON 解析失敗後每個 case 都 fail-open 成 exit 0，
#    於是測試全綠但其實什麼都沒測到。
#
# 2) 測試資料裡的 emoji 不能寫字面字元，要用碼點組（下面的 EMO_* 變數）。
#    寫字面的話，guard 會在你存這個檔案的時候把你自己擋下來。

GUARD="$(dirname "$0")/no-emoji-guard.py"
fail=0

EMO_CHECK=$(printf '\u2705')       # 綠底白勾
EMO_PARTY=$(printf '\U0001F389')   # 拉炮
EMO_ROCKET=$(printf '\U0001F680')  # 火箭

run() {
    local want="$1" name="$2" payload="$3"
    printf '%s' "$payload" | python "$GUARD" >/dev/null 2>&1
    local got=$?
    if [ "$got" = "$want" ]; then
        echo "  PASS  $name"
    else
        echo "  FAIL  $name (want exit=$want, got exit=$got)"
        fail=1
    fi
}

echo "no-emoji-guard 行為測試"

run 0 "純中文＋排版符號放行" \
    '{"tool_input":{"file_path":"C:/dev/a.md","content":"這是中文，含排版記號"}}'

run 2 "content 含 emoji 攔下" \
    '{"tool_input":{"file_path":"C:/dev/a.md","content":"完成了 '"$EMO_CHECK"' 很棒 '"$EMO_PARTY"'"}}'

run 2 "Edit 的 new_string 含 emoji 攔下" \
    '{"tool_input":{"file_path":"C:/dev/a.md","new_string":"部署完成 '"$EMO_ROCKET"'"}}'

export NO_EMOJI_EXEMPT='/my-notes/;\my-notes\'
run 0 "豁免路徑（反斜線）整檔放行" \
    '{"tool_input":{"file_path":"C:\\Users\\me\\my-notes\\knowledge\\x.md","content":"筆記 '"$EMO_CHECK"'"}}'

run 0 "豁免路徑（正斜線）整檔放行" \
    '{"tool_input":{"file_path":"C:/Users/me/my-notes/knowledge/x.md","content":"筆記 '"$EMO_CHECK"'"}}'
unset NO_EMOJI_EXEMPT

run 2 "未設豁免時筆記路徑照擋" \
    '{"tool_input":{"file_path":"C:/Users/me/my-notes/knowledge/x.md","content":"筆記 '"$EMO_CHECK"'"}}'

run 0 "Obsidian 待辦行的 Tasks 標記放行" \
    '{"tool_input":{"file_path":"C:/dev/t.md","content":"- [x] 買菜 '"$EMO_CHECK"' 2026-08-07"}}'

run 0 "壞 payload fail-open" \
    'not json at all'

[ "$fail" = 0 ] && echo "全數通過" || echo "有失敗項目"
exit $fail
