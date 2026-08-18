# harness-gate core：由 harness-gate.sh 在預篩通過後呼叫。stdin = PreToolUse payload JSON。
# 詳見 harness-gate.SPEC.md。
#
# fail-open 原則：解析不出來就不介入。這是流程提醒，不是安全邊界——
# 誤擋的代價高於漏抓（危險動作歸 harness-trace 管）。
import json, os, re, sys

HOME = os.path.expanduser("~")
GUARD_DIR = os.environ.get("HARNESS_GATE_DIR") or os.path.join(HOME, ".claude", "harness-gate")
# HARNESS_GATE_ROOTS：分號分隔的專案根目錄清單（G2 cwd 漂移偵測的範圍）。
# HARNESS_GATE_VAULT：知識庫根目錄（在裡面工作時本 hook 不介入）。
# 兩者都沒設時對應的閘門安靜停用（fail-open），G1 的 skill 閘門不受影響。
ROOTS_RAW = os.environ.get("HARNESS_GATE_ROOTS") or ""
VAULT_RAW = os.environ.get("HARNESS_GATE_VAULT") or ""

# 只擋終點與 harness 流程衝突的：訪談／規劃／開票，它們的終點是自己一套規格與
# ticket 流程，會跟 Plan → 簽核 → feature_list.json 打架。tdd、diagnosing-bugs
# 等在 harness 專案裡照樣該用，不列入。
#
# 比對前先剝掉 `namespace:` 前綴（plugin 裝是 `pkg:name`，npx skills 裝是裸名），
# 這樣換 skill 包不會讓整道閘門靜默失效。
# 判準是**終點**，不是「像不像規劃」：只擋會產出跟 feature_list.json 競爭的規格／
# 工單產物的。純訪談（grill-me／grilling／grill-with-docs）不產生競爭產物——
# grill-with-docs 的終點是 CONTEXT.md 與 ADR——在 harness 專案裡照樣該用。
GATED_SKILLS = {
    "brainstorming", "writing-plans",  # 來源包已移除，裸名留著防回裝
    "to-spec", "to-tickets",           # mattpocock：規格與開票
}


def bare_skill(name):
    return str(name).rsplit(":", 1)[-1].strip()

G2_TOOLS = ("Read", "Edit", "Write", "Bash")


def norm(p):
    return os.path.normpath(str(p)).replace("\\", "/").rstrip("/")


def key(p):
    # Windows 路徑大小寫不敏感；payload 的 cwd 與設定值大小寫未必一致
    return norm(p).lower()


def under(path, base):
    k, b = key(path), key(base)
    return k == b or k.startswith(b + "/")


ROOTS = [norm(r) for r in ROOTS_RAW.split(";") if r.strip()]
VAULT = norm(VAULT_RAW)

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
if not isinstance(data, dict):
    sys.exit(0)

cwd_raw = data.get("cwd")
if not cwd_raw:
    sys.exit(0)          # 缺 cwd → 定位不到，不介入
cwd = norm(cwd_raw)

if under(cwd, VAULT):
    sys.exit(0)          # vault 筆記工作本來就走通用流程

sid = str(data.get("session_id", "?") or "?")
tool = str(data.get("tool_name", ""))
ti = data.get("tool_input") or {}
if not isinstance(ti, dict):
    sys.exit(0)


def notify_once(k, message):
    """同 session 同主題只提醒一次，避免洗頻。"""
    safe = re.sub(r"[^A-Za-z0-9._-]", "", "%s-%s" % (sid, k))
    sentinel = os.path.join(GUARD_DIR, "notified-" + safe)
    if os.path.exists(sentinel):
        return
    try:
        os.makedirs(GUARD_DIR, exist_ok=True)
        open(sentinel, "w").close()
    except Exception:
        pass                      # 寫不了標記就每次都提醒，比靜默失效好
    print(json.dumps({"systemMessage": message}, ensure_ascii=False, separators=(",", ":")))


def deny(rule, reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
        "systemMessage": "harness-gate：blocked " + rule,
    }, ensure_ascii=False, separators=(",", ":")))


def harness_repo_of(path):
    """從 path 向上找出含 feature_list.json 的目錄（＝harness 專案 root）。

    不呼叫 git：走檔案系統就夠，還省一次子行程。
    """
    cur = norm(path)
    while True:
        if os.path.isfile(os.path.join(cur, "feature_list.json")):
            return cur
        parent = norm(os.path.dirname(cur))
        if parent == cur or not parent:
            return None
        cur = parent


# ---------------- G1：流程接錯（Skill gate）----------------
if tool == "Skill":
    skill = str(ti.get("skill", ""))
    if bare_skill(skill) not in GATED_SKILLS:
        sys.exit(0)
    repo = harness_repo_of(cwd)
    if repo:
        deny("wrong-workflow",
             "harness 流程保護：`%s` 的終點是它自己一套規格／ticket 流程，"
             "但這是 harness 專案（%s 有 feature_list.json）——新 feature 的終點是 "
             "Plan → 驗收清單經使用者簽核 → 凍結進 feature_list.json 的 acceptance。"
             "請改走五階段的 Plan（需求已清楚就直接開 feature 條目）。"
             "這是刻意機制不是錯誤；若此動作確為必要，請向使用者說明並取得確認後再進行。"
             % (skill, os.path.basename(repo)))
    else:
        notify_once("g1-workflow",
                    "harness-gate：正在用 `%s`，而 cwd 不在任何 harness 專案內（%s）。"
                    "若這件事的目標是某個 harness 專案，請先 `cd` 進該 repo 並改走 "
                    "Plan → 驗收簽核 → feature_list.json；若是工作案件／一次性腳本／"
                    "別人的 repo，忽略這則提醒即可。" % (skill, cwd))
    sys.exit(0)

# ---------------- G2：cwd 漂移（第 0 步沒做）----------------
if tool not in G2_TOOLS:
    sys.exit(0)

if tool == "Bash":
    text = str(ti.get("command", ""))
else:
    text = str(ti.get("file_path", ""))
if not text:
    sys.exit(0)
text = text.replace("\\", "/")

for root in ROOTS:
    # 兩者兵接第一段：字串比對抓出 <root>/<專案> 的專案名（成本近零）
    for m in re.finditer(re.escape(root) + r"/([^/\s'\"`;|)]+)", text, re.IGNORECASE):
        proj_dir = root + "/" + m.group(1)
        # 第二段：確認它真的是 harness 專案，才有資格提醒
        if not os.path.isfile(os.path.join(proj_dir, "feature_list.json")):
            continue
        if under(cwd, proj_dir):
            continue
        notify_once("cwd-" + m.group(1),
                    "harness-gate：正在操作 harness 專案 `%s` 的檔案，但 cwd 在 `%s`。"
                    "依 development-workflow 第 0 步，請先 `cd` 進 %s，"
                    "並讀 AGENTS.md（或 CLAUDE.md）、session-handoff.md、feature_list.json——"
                    "否則 repo 的 .claude/settings.json（effort）不會生效，repo 規則也不會自動載入。"
                    % (m.group(1), cwd, proj_dir))
        sys.exit(0)
