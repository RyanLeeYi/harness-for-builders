# harness-trace core：由 harness-trace.sh 在 gate 通過後呼叫。
# stdin = PreToolUse payload JSON；argv[1] = repo_root；argv[2] = guard_dir。
# 詳見 harness-trace.SPEC.md。
import json, os, re, sys
from datetime import datetime, timezone

repo_root, guard_dir = sys.argv[1], sys.argv[2]
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
if not isinstance(data, dict):
    sys.exit(0)

sid = str(data.get("session_id", "?") or "?")

def norm(p):
    return os.path.normpath(p).replace("\\", "/")
rr = norm(repo_root)

def current_feature():
    """正在做的 feature，來源是 `.harness/current_feature` 這個明確的宣告。

    原本取「feature_list 裡第一個 failing」，那是**猜**——只要 failing 不只一條，
    或實際在做的不是排最前面那條，歸因就整批錯（2026-07-29 實測：那幾天所有 trace
    都被標成 F65，但實際在做 F85；2026-07-30 又全被標成 F66，實際在做 F90/F91）。
    錯的歸因比沒有歸因更糟，因為 /harness-retro 會拿它當真。

    所以：宣告了才記，沒宣告就回 "?"。寧可留白，不要猜。
    """
    try:
        with open(os.path.join(repo_root, ".harness", "current_feature"), encoding="utf-8") as f:
            declared = f.read().strip()
        if declared:
            return declared.splitlines()[0].strip()
    except Exception:
        pass
    return "?"

def append_trace(tool, target, in_repo, verdict):
    hdir = os.path.join(repo_root, ".harness")
    os.makedirs(hdir, exist_ok=True)
    gi = os.path.join(repo_root, ".gitignore")
    try:
        existing = open(gi, encoding="utf-8").read() if os.path.exists(gi) else ""
        if not re.search(r"(?m)^\.harness/?\s*$", existing):
            with open(gi, "a", encoding="utf-8") as f:
                f.write(("" if existing == "" or existing.endswith("\n") else "\n") + ".harness/\n")
    except Exception:
        pass
    tpath = os.path.join(hdir, "trace.jsonl")
    try:
        if os.path.exists(tpath):
            with open(tpath, encoding="utf-8") as f:
                n = sum(1 for _ in f)
            if n >= 5000:
                os.replace(tpath, os.path.join(hdir, "trace-%s.jsonl" % datetime.now().strftime("%Y%m%d-%H%M%S")))
    except Exception:
        pass
    entry = {"ts": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
             "sid": sid, "feature": current_feature(), "tool": tool,
             "target": target, "in_repo": in_repo, "verdict": verdict}
    try:
        with open(tpath, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")
    except Exception:
        pass

def notify_once(key, message):
    # 同一 session 同一類訊息只提醒一次（避免洗頻）
    sentinel = os.path.join(guard_dir, "notified-%s-%s" % (re.sub(r"[^A-Za-z0-9]", "", sid), key))
    if os.path.exists(sentinel):
        return
    try:
        open(sentinel, "w").close()
    except Exception:
        pass
    print(json.dumps({"systemMessage": message}, ensure_ascii=False, separators=(",", ":")))

# schema-drift gate：payload 是「開放契約」——只驗必要欄位在不在，多出來的未知欄位一律不管。
# 少了必要欄位時，舊行為是靜默 fail-open：整個越權保護等同關閉，trace 卻照記 verdict ok，
# 看起來一切健康。這裡把那種無聲失效變成看得見的訊號（仍不 block，不擋使用者工作）。
missing = [k for k in ("tool_name", "tool_input") if k not in data]
if missing:
    keys = ",".join(missing)
    append_trace(str(data.get("tool_name", "?")), "", True, "schema-drift:" + keys)
    notify_once("schema-drift",
                "harness-trace：PreToolUse payload 缺必要欄位 %s——hook 可能因 Claude Code 契約變更而失效，"
                "越權保護形同關閉。請跑 ~/.claude/scripts/harness-trace-test.sh 並核對 payload 格式。" % keys)
    sys.exit(0)

tool = data.get("tool_name", "")
if tool not in ("Edit", "Write", "Bash"):
    sys.exit(0)
ti = data.get("tool_input") or {}

# target / in_repo
if tool == "Bash":
    cmd = str(ti.get("command", ""))
    target, in_repo = cmd[:200], True
else:
    cmd = ""
    fp = str(ti.get("file_path", ""))
    ap = norm(fp if os.path.isabs(fp) else os.path.join(repo_root, fp))
    in_repo = (ap == rr or ap.startswith(rr + "/"))
    target = ap[len(rr) + 1:] if in_repo else ap

_fl_name = os.path.basename(str(ti.get("file_path", ""))) == "feature_list.json"
fl_edit = (tool == "Edit" and _fl_name)
# 2026-07-25 retro：原本只認 Edit，改用 Write 或 Bash 寫 JSON 就整組保護失效（實際發生過：
# 用 python heredoc 改 feature_list，4 次 failing→passing 全被記成 ok）。這裡把 Write 一併納入，
# Bash 側則以「命令提到 feature_list.json 且看得出寫入意圖」記一筆 RECORD（不 DENY：讀取/查詢也常提到它）。
fl_write = (tool == "Write" and _fl_name)
fl_bash = (
    tool == "Bash"
    and "feature_list.json" in cmd
    and re.search(r"(>>?\s*\S*feature_list\.json|\bjson\.dump|\bwrite\(|\bsed\b.*-i|\bjq\b|"
                  r"\btee\b|\bcp\b|\bmv\b|open\([^)]*feature_list\.json[^)]*['\"][wa])", cmd)
)

def is_scratch(p):
    # Claude 自己的 temp 命名空間（scratchpad 等暫存檔）——寫這裡是指定行為，不算越界。
    return bool(re.search(r"/(?:temp|tmp)/claude/", p, re.I))

# 2026-08-07：收官回寫 vault 的 DEVLOG / DECISIONS 是流程明文要求的動作（development-workflow
# 的「收工」條、repo 入口檔的「Vault 連動」段、usage-guard 收工第 4 步）。原本它會被判成
# out-of-repo-write：規則叫它寫、hook 記它越權——兩邊打架時帶警告的那邊贏，實測結果就是
# vault 長期收不到任何收官紀錄。只放行 vault 的 projects/ 子樹；career/、knowledge/、
# identity/ 等區域從 repo session 寫入仍屬可疑，維持標記。
# HARNESS_TRACE_VAULT_PROJECTS：知識庫裡「流程要求收官回寫」的子樹（例如 <vault>/projects）。
# 沒設就不放行任何外部路徑——repo 外寫入一律標記。
_VP_RAW = os.environ.get("HARNESS_TRACE_VAULT_PROJECTS") or ""
VAULT_PROJECTS = norm(_VP_RAW) if _VP_RAW else ""

def is_vault_project(p):
    if not VAULT_PROJECTS:
        return False
    b = VAULT_PROJECTS.rstrip("/").lower()
    q = p.rstrip("/").lower()
    return q == b or q.startswith(b + "/")

def rm_rf(c):
    for m in re.finditer(r"\brm\s+(-[a-zA-Z]+)", c):
        f = m.group(1).lower()
        if "r" in f and "f" in f:
            return True
    return False

# 簽核後凍結的欄位。acceptance 是字串；envelope 的 constraints／non_goals 與 feature 的
# non_goals 是字串陣列。2026-08-05 導入 envelope + slice 時一併納入——規則寫了「與 acceptance
# 同級凍結」但 hook 不認得，那條規則就只有文字沒有強制力（見 memory guard-rules-tool-coupling）。
FROZEN_KEYS = ("acceptance", "constraints", "non_goals")
_FROZEN_RE = re.compile(
    r'"(?:%s)"\s*:\s*(?:("(?:[^"\\]|\\.)*")|(\[[^\]]*\]))' % "|".join(FROZEN_KEYS), re.S)

def frozen_values(text):
    """抓出文字裡所有被凍結欄位的字串值（用來比對是否原樣保留）。

    陣列取「每個元素」而不是整段 blob：這樣往 non_goals 新增一條不會被誤擋，
    只有改掉或刪掉既有元素才擋——跟 acceptance 那條精準化的理由相同（過嚴的 DENY
    會把人逼去用 Bash 改檔，連 RECORD 都繞過）。
    """
    out = []
    for m in _FROZEN_RE.finditer(text):
        blob = m.group(1) or m.group(2) or ""
        out.extend(re.findall(r'"((?:[^"\\]|\\.)*)"', blob))
    return out

def deny_reason():
    # 2026-07-25 retro：原規則只看 old_string 有沒有 "acceptance" 這個字，於是「在檔尾追加新 feature」
    # 也被擋（錨點會帶到前一條的 acceptance）——過嚴的 DENY 把人逼去用 Bash 改檔，連 RECORD 都繞過了。
    # 精準化：既有 acceptance 值只要原樣出現在 new_string 就是沒被改，放行；真的被改/刪才擋。
    if fl_edit:
        olds = frozen_values(str(ti.get("old_string", "")))
        new = str(ti.get("new_string", ""))
        if any(v not in new for v in olds):
            return ("frozen-acceptance",
                    "改到 feature_list.json 已簽核凍結的欄位（acceptance／envelope 的 "
                    "constraints、non_goals）；動工後這些欄位已凍結。")
    if tool == "Bash":
        if rm_rf(cmd):
            return ("denylist-cmd", "命令含 rm -rf（遞迴強制刪除）。")
        for pat, desc in [
            (r"git\s+push\b.*(--force|\s-f\b)", "git push --force"),
            (r"git\s+commit\b.*--no-verify", "git commit --no-verify"),
            (r"git\s+reset\s+--hard", "git reset --hard"),
            (r"curl\b.*\|\s*sh\b", "curl 管道到 sh"),
            (r"--no-gpg-sign", "--no-gpg-sign"),
        ]:
            if re.search(pat, cmd):
                return ("denylist-cmd", f"命令含禁用操作：{desc}。")
    return None

def record_flag():
    if (tool in ("Write", "Edit") and not in_repo
            and not is_scratch(ap) and not is_vault_project(ap)):
        return ("out-of-repo-write", "寫入 repo 外路徑。")
    # 第三層（2026-08-17）：開工時提醒看可平行組。開工的明確訊號是寫 `.harness/current_feature`，
    # 不是新增 feature（那個由下面的 coupling-check 管）。2026-08-05 起平行重新開放，但 rules 的
    # direct-first 例外二「兩條以上真正獨立」只是文字、沒有 gate——靠模型記得等於沒有。
    # 判斷一樣不在這裡做，交給 harness-plan.py；這裡只負責「不會被忘記」。
    if (tool in ("Write", "Edit") and in_repo
            and target == ".harness/current_feature"):
        return ("parallel-check",
                "開工——跑 `python ~/.claude/scripts/harness-plan.py . --dsm`，看「可獨立進行」"
                "那段有沒有可與本條平行的 failing 條目（三條件全成立才算：不互為 prerequisites、"
                "touches 無交集、requires 無交集）。有就主動向使用者提議平行派工＋各自 worktree，"
                "沒有就照常序列。判定失真的兩個來源：touches 填目錄（逃過 hub 排除，讓任兩條都假重疊）、"
                "requires 塞 feature id（那是 prerequisites 的語意，會被誤判成共用排他資源）。")
    # 第二層（2026-07-30）：新增 feature 時提醒跑耦合檢查。
    # 檢查本身不在這裡做——PreToolUse 時檔案還沒寫進去，新條目讀不到；
    # 硬從 new_string 解析等於把 harness-plan 的邏輯複製一份，改一邊忘一邊。
    # 這裡只負責「不會被忘記」，判斷交給那支腳本。
    new_feature = (fl_edit and '"status"' in str(ti.get("new_string", ""))
                   and '"failing"' in str(ti.get("new_string", ""))
                   and '"failing"' not in str(ti.get("old_string", "")))
    if new_feature or (fl_write and '"failing"' in str(ti.get("content", ""))):
        return ("new-feature-coupling-check",
                "新增了 failing feature——開工前跑 "
                "`python ~/.claude/scripts/harness-plan.py . --check <FEATURE_ID>`，"
                "與既有 failing 條目有檔案／排他資源重疊時先問「是不是該合併成一條」"
                "（2026-07-29 定案：一條 feature = 一個病灶，不是一個症狀）。")
    if fl_edit and '"passing"' in str(ti.get("new_string", "")) and '"failing"' in str(ti.get("old_string", "")):
        return ("status-to-passing", "把 feature 從 failing 改為 passing——請確認已附 evidence。")
    if fl_write and '"passing"' in str(ti.get("content", "")):
        return ("status-to-passing", "整檔覆寫 feature_list.json 且含 passing——請確認已附 evidence。")
    if fl_bash:
        return ("feature-list-via-bash",
                "用 Bash 改 feature_list.json——凍結 acceptance 的保護不經過這條路，請自行確認"
                "沒有改到既有 acceptance，且 status 改 passing 已附 evidence。")
    return None

def silent_mark():
    """只記 trace、不擋也不提醒的觀察點（2026-08-17）。

    Approval 是硬關卡，但它的觸發判準刻意留成形容詞（大／架構／有風險），所以寫不進 gate——
    等於它的成效完全不可觀測：我判斷對幾次、漏幾次、多停幾次，全部靜默。

    這裡記下「本 session 第一次寫入原始碼」當代理訊號。**它證明不了有沒有經過 Approval**
    （hook 看不到核准這件事），但讓 /harness-retro 能把「一進來就直接開寫」的 session 挑出來
    人工對照。不擋、不提醒——提醒會在刻意跳過 Approval 時洗頻。
    """
    if tool not in ("Write", "Edit") or not in_repo:
        return None
    if target.startswith(".harness/") or target.endswith((".md", ".json", ".txt", ".jsonl")):
        return None
    sentinel = os.path.join(guard_dir, "srcwrite-%s" % re.sub(r"[^A-Za-z0-9]", "", sid))
    if os.path.exists(sentinel):
        return None
    try:
        open(sentinel, "w").close()
    except Exception:
        return None
    return "first-source-write"

deny = deny_reason()
flag = None if deny else record_flag()
if deny:
    verdict = f"blocked:{deny[0]}"
elif flag:
    verdict = f"overreach:{flag[0]}"
else:
    _mark = silent_mark()
    verdict = f"note:{_mark}" if _mark else "ok"

append_trace(tool, target, in_repo, verdict)

# 輸出 decision
if deny:
    reason = f"harness 越權保護：{deny[1]} 這是刻意機制不是錯誤；若此動作確為必要，請向使用者說明並取得確認後再進行。"
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
          "permissionDecision": "deny", "permissionDecisionReason": reason},
          "systemMessage": f"harness-trace：blocked {deny[0]}"}, ensure_ascii=False, separators=(",", ":")))
elif flag:
    notify_once(flag[0], f"harness-trace：{flag[1]}（{flag[0]}，已記入 trace）")
