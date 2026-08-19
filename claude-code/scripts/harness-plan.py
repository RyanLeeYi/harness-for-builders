"""harness-plan：用 feature 之間的檔案耦合回答「該不該合併」與「用什麼順序做」。

2026-07-29 的並行開發評估定案（vault memory `2026-07-29_feature切分與並行開發可行性`）：
價值分布是 **~80% 在「該不該合併」**、~15% 在執行順序、~5% 在並行。
所以這支腳本的主要輸出是**合併建議**，不是排程表。

用法：
  harness-plan.py <repo_root> --check <FEATURE_ID>   開 feature 前的重疊檢查
  harness-plan.py <repo_root> --dsm                  對所有 failing 出 DSM 與合併建議
  harness-plan.py <repo_root> --dsm --json           結構化輸出

資料來源是 feature_list.json 的 `touches`（涉及檔案）、`requires`（排他性資源）、
`prerequisites`（必須先完成的 feature id），以及選填的 `needs`／`creates`（API 級契約名，
例如 `api:auth-token`、`table:sessions`；A.needs 與 B.creates 交集 → A 排在 B 後，沒寫進
prerequisites 就列為「未宣告的時序耦合」警告）。
touches 空的條目一律略過並在報告裡列出——**沒有資料不等於沒有耦合**，不要當成「安全」。

prerequisites 是**宣告**的順序，優先於耦合推論出的順序。它跟 touches 是不同的東西：
touches 交集說的是「這兩條會撞在一起」（無方向），prerequisites 說的是「這條要先做完」
（有方向）。可平行要三個條件同時成立：不互為 prerequisites、touches 無交集、requires 無交集。
"""

from __future__ import annotations

import json
import sys
from collections import Counter

# Windows 主控台預設 cp950，印到 stdout 的 ⛔ ⚠ 這類符號會丟 UnicodeEncodeError 直接中斷，
# 而且是在報告印到一半的時候——看起來像腳本壞了，其實只是編碼。輸出一律走 UTF-8。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 被超過這個比例的 feature 碰到的檔案＝架構級 hub（例：lift-log 的 sw.js 在 76/92 條裡）。
# 這種檔案讓任兩條 feature 都「重疊」，留著只會把訊號洗掉，計算重疊時一律排除。
HUB_RATIO = 0.5


# 2026-08-19：passing 條目整條歸檔後，主檔只留 failing。但分析仍需要看到全體——
# hub 偵測是跨全體統計比例（少了歷史條目，sw.js 這種檔案的比例掉到門檻下，
# 於是不再被排除，任兩條都變成假重疊），prerequisites 存在性檢查也要比對全體 id
# （指向已 passing 的前置會被誤報成「指向不存在的 F59」）。
# 所以讀檔在這裡合併歸檔，agent 每個 session 讀的主檔仍然只有 failing。
ARCHIVE = "docs/archive/features.jsonl"


def load(repo_root: str) -> list[dict]:
    with open(f"{repo_root}/feature_list.json", encoding="utf-8") as f:
        features = json.load(f).get("features") or []
    try:
        with open(f"{repo_root}/{ARCHIVE}", encoding="utf-8") as f:
            archived = [json.loads(line) for line in f if line.strip()]
    except FileNotFoundError:
        return features
    seen = {f.get("id") for f in features}
    return features + [a for a in archived if a.get("id") not in seen]


def hub_files(features: list[dict]) -> set[str]:
    if not features:
        return set()
    counter = Counter(t for f in features for t in (f.get("touches") or []))
    limit = max(2, int(len(features) * HUB_RATIO))
    return {path for path, n in counter.items() if n >= limit}


def signal_touches(feature: dict, hubs: set[str]) -> set[str]:
    return set(feature.get("touches") or []) - hubs


def overlap(a: dict, b: dict, hubs: set[str]) -> dict:
    files = signal_touches(a, hubs) & signal_touches(b, hubs)
    resources = set(a.get("requires") or []) & set(b.get("requires") or [])
    return {"files": sorted(files), "resources": sorted(resources)}


def prereq_problems(features: list[dict]) -> list[str]:
    """prerequisites 的資料完整性：指向不存在、指向自己、形成循環。

    這三種都會讓「順序」與「能不能平行」變成沒有根據的斷言，所以是報告的第一段，
    不是附註——資料壞掉時先修資料，不要照著壞資料排程。
    """
    ids = {f["id"] for f in features}
    problems = []
    for f in features:
        for p in f.get("prerequisites") or []:
            if p == f["id"]:
                problems.append(f"{f['id']} 的 prerequisites 指向自己")
            elif p not in ids:
                problems.append(f"{f['id']} 的 prerequisites 指向不存在的 {p}")
    # 循環：反覆移除前置都已滿足的條目，移不動就是有環
    pending = {f["id"]: {p for p in (f.get("prerequisites") or []) if p in ids} for f in features}
    changed = True
    while changed and pending:
        changed = False
        for fid in list(pending):
            if not (pending[fid] & pending.keys()):
                del pending[fid]
                changed = True
    if pending:
        problems.append("prerequisites 形成循環：" + "、".join(sorted(pending)))
    return problems


def declared(items: list[dict]) -> list[dict]:
    """有 `prerequisites` 欄位的條目。**沒有欄位 ≠ 沒有依賴**——跟 touches 同一條原則：
    資料缺席時不准替它斷言「可以先做／可以平行」，只能把它列進未申報清單。
    """
    return [f for f in items if "prerequisites" in f]


def layers(items: list[dict], all_ids: set[str]) -> list[list[str]]:
    """依 prerequisites 做拓樸分層。同一層＝前置條件都已滿足，彼此沒有先後關係。

    只算**有申報** prerequisites 的 failing 條目之間的相依；指向已 passing 條目的前置
    視為已滿足。有環時回傳空清單（由 prereq_problems 負責報告，這裡不猜）。
    """
    items = declared(items)
    ids = {f["id"] for f in items}
    pending = {f["id"]: {p for p in (f.get("prerequisites") or []) if p in ids} for f in items}
    out: list[list[str]] = []
    while pending:
        ready = sorted(fid for fid, deps in pending.items() if not deps)
        if not ready:
            return []
        out.append(ready)
        for fid in ready:
            del pending[fid]
        for deps in pending.values():
            deps -= set(ready)
    return out


def inferred_edges(items: list[dict]) -> dict[str, set[str]]:
    """needs／creates 推論出的時序耦合（2026-08-19 抄 gsd-core needs/creates，Dimension 3b 精神）：
    A.needs 與 B.creates 有交集 → A 要等 B。回傳 {A: {B, ...}}。

    這是**推論**，不是宣告：waves() 會把它當 prerequisite 排，但報告只警告不擋——
    「沒申報 prerequisites 卻有隱性時序」是規格要補的資料，不是工具替它斷言。
    """
    out: dict[str, set[str]] = {}
    for a in items:
        needs = set(a.get("needs") or [])
        if not needs:
            continue
        for b in items:
            if b is not a and needs & set(b.get("creates") or []):
                out.setdefault(a["id"], set()).add(b["id"])
    return out


def undeclared_timing(items: list[dict]) -> list[str]:
    """推論出 A 要等 B，但 A.prerequisites 沒寫 B → 未宣告的時序耦合（只警告）。"""
    out = []
    for a_id, bs in inferred_edges(items).items():
        a = next(f for f in items if f["id"] == a_id)
        declared_p = set(a.get("prerequisites") or [])
        for b in sorted(bs - declared_p):
            out.append(f"{a_id} needs 的東西由 {b} creates，但 {a_id} 的 prerequisites 沒寫 {b}")
    return out


def _place(fid, f, wave, prereqs, by_id, hubs):
    w = 1 + max((wave[p] for p in prereqs), default=0)
    while any(wave[o] == w and _conflict(f, by_id[o], hubs) for o in wave):
        w += 1
    wave[fid] = w


def waves(order: list[list[str]], items: list[dict], hubs: set[str]) -> tuple[list[list[str]], list[str]]:
    """gsd-core planner 的分層規則（2026-08-19 抄入）：wave = max(prerequisite waves) + 1，
    同一 wave 內 touches／requires 有交集 → 後者下推一層，直到同 wave 零交集。

    只排**同時**有 prerequisites 申報與 touches 資料的條目；prerequisite 是 failing 但沒排進
    wave（資料不足）的條目列進 blocked，不猜它能排第幾波。回傳 (waves, blocked)。
    """
    by_id = {f["id"]: f for f in items}
    wave: dict[str, int] = {}
    blocked: list[str] = []
    pending_ids = {fid for layer in order for fid in layer}
    inferred = inferred_edges(items)

    def prereqs_of(fid: str) -> list[str]:
        f = by_id[fid]
        ps = [p for p in (f.get("prerequisites") or []) if p in pending_ids]
        # needs/creates 推論邊也當 prerequisite 排（報告另外警告它沒宣告）
        ps += [p for p in sorted(inferred.get(fid, ())) if p in pending_ids and p not in ps]
        return ps

    for layer in order:
        todo = [fid for fid in layer if fid in by_id]
        # 推論邊可能指向同一拓樸層的條目，所以同層反覆掃到沒有進展為止
        while todo:
            ready = [fid for fid in todo if all(p in wave for p in prereqs_of(fid))]
            if not ready:
                blocked.extend(todo)
                break
            for fid in ready:
                _place(fid, by_id[fid], wave, prereqs_of(fid), by_id, hubs)
            todo = [fid for fid in todo if fid not in ready]
    out: list[list[str]] = []
    for fid, w in wave.items():
        while len(out) < w:
            out.append([])
        out[w - 1].append(fid)
    return out, blocked


def _conflict(a: dict, b: dict, hubs: set[str]) -> bool:
    ov = overlap(a, b, hubs)
    return bool(ov["files"] or ov["resources"])


def failing(features: list[dict]) -> list[dict]:
    return [f for f in features if f.get("status") != "passing"]


def cmd_check(features: list[dict], target_id: str) -> int:
    hubs = hub_files(features)
    target = next((f for f in features if f.get("id") == target_id), None)
    if target is None:
        print(f"找不到 feature {target_id}")
        return 1
    if not (target.get("touches") or []):
        print(f"⚠ {target_id} 還沒有 touches——開工前先估涉及哪些檔案，否則這個檢查沒有意義。")
        return 0

    findings = []
    for other in failing(features):
        if other.get("id") == target_id:
            continue
        ov = overlap(target, other, hubs)
        if ov["files"] or ov["resources"]:
            findings.append((other, ov))

    print(f"# 開 feature 前的重疊檢查 — {target_id} {target.get('name', '')}")
    print(f"\n（已排除 {len(hubs)} 個架構級 hub 檔案；它們讓任兩條都重疊，不具鑑別力）")
    for t in undeclared_timing(failing(features)):
        if t.startswith(f"{target_id} "):
            print(f"\n⚠ {t}")
    if not findings:
        print("\n沒有與其他 failing 條目重疊。可以獨立進行。")
        return 0
    print("\n與這些 failing 條目重疊——**先問「是不是該合併成一條」**，再考慮順序：\n")
    for other, ov in findings:
        print(f"- **{other['id']}** {other.get('name', '')}")
        if ov["files"]:
            print(f"    共用檔案：{', '.join(ov['files'])}")
        if ov["resources"]:
            print(f"    ⛔ 共用排他資源：{', '.join(ov['resources'])}——不可並行")
    print(
        "\n判準（2026-07-29 定案）：**一條 feature = 一個病灶／一個程式碼邊界，不是一個症狀**。"
        "\n同一批檔案要改兩次、或兩條在講同一個缺陷的兩面 → 合併，別為了「條目好看」而拆。"
    )
    return 0


def cmd_dsm(features: list[dict], as_json: bool) -> int:
    all_failing = failing(features)
    hubs = hub_files(features)
    no_data = [f["id"] for f in all_failing if not (f.get("touches") or [])]
    # 沒有 touches 的條目**完全不進分析**。放進去的話它們會落在「可獨立進行」，
    # 那是沒有根據的斷言——資料缺席不是「沒有耦合」的證據。
    items = [f for f in all_failing if f.get("touches")]
    graph: dict[str, set[str]] = {f["id"]: set() for f in items}
    pairs = []
    for i, a in enumerate(items):
        for b in items[i + 1 :]:
            ov = overlap(a, b, hubs)
            if ov["files"] or ov["resources"]:
                graph[a["id"]].add(b["id"])
                graph[b["id"]].add(a["id"])
                pairs.append((a["id"], b["id"], ov))

    # circuit＝連通元件（DSM partitioning 後排不掉的對角線方塊）＝合併候選
    seen: set[str] = set()
    circuits: list[list[str]] = []
    for fid in graph:
        if fid in seen:
            continue
        stack, comp = [fid], []
        seen.add(fid)
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for nxt in graph[cur]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        circuits.append(sorted(comp, key=lambda x: items.index(next(f for f in items if f["id"] == x))))

    if as_json:
        print(json.dumps(
            {
                "failing": [f["id"] for f in all_failing],
                "analyzed": [f["id"] for f in items],
                "hubs": sorted(hubs),
                "no_touches_data": no_data,
                "prereq_problems": prereq_problems(features),
                "order_layers": layers(all_failing, {f["id"] for f in features}),
                "waves": waves(layers(all_failing, {f["id"] for f in features}), items, hubs)[0],
                "wave_blocked": waves(layers(all_failing, {f["id"] for f in features}), items, hubs)[1],
                "inferred_edges": {k: sorted(v) for k, v in inferred_edges(items).items()},
                "undeclared_timing": undeclared_timing(items),
                "circuits": circuits,
                "pairs": [{"a": a, "b": b, **ov} for a, b, ov in pairs],
            },
            ensure_ascii=False, indent=2,
        ))
        return 0

    name = {f["id"]: f.get("name", "") for f in items}
    print("# harness-plan — failing feature 的耦合結構\n")
    problems = prereq_problems(features)
    if problems:
        print("## ⛔ prerequisites 資料有問題，先修再看下面\n")
        for p in problems:
            print(f"- {p}")
        print("\n（順序與平行的判斷全部建立在這份資料上，資料壞掉時下面的結論不可信）\n")
    print(f"failing：{len(all_failing)} 條，其中 {len(items)} 條有 touches 資料"
          f"｜已排除 {len(hubs)} 個架構級 hub 檔案")
    if hubs:
        print(f"  hub：{', '.join(sorted(hubs))}")
    if no_data:
        print(f"\n⚠ 沒有 touches 資料，未納入分析：{', '.join(no_data)}")
        print("  （沒有資料不等於沒有耦合——開工前補估）")

    merge = [c for c in circuits if len(c) > 1]
    solo = [c[0] for c in circuits if len(c) == 1]
    print("\n## 合併候選（circuit：彼此有耦合，拆開做會重複同一批儀式）\n")
    if not merge:
        print("無——目前的 failing 條目彼此沒有非 hub 的檔案交集。")
    for comp in merge:
        print(f"- **{' ＋ '.join(comp)}**")
        for fid in comp:
            print(f"    - {fid} {name[fid]}")
        # 列出**兩兩之間**的實際連結，不是全體交集——circuit 常是傳遞連起來的
        # （A 與 B 共用 x、B 與 C 共用 y，三者交集是空的），只印交集會變成「沒有理由」。
        inside = [(a, b, ov) for a, b, ov in pairs if a in comp and b in comp]
        for a, b, ov in inside:
            why = []
            if ov["files"]:
                why.append("、".join(ov["files"]))
            if ov["resources"]:
                why.append("⛔ 排他資源 " + "、".join(ov["resources"]))
            print(f"    {a}–{b}：{'；'.join(why)}")

    print("\n## 可獨立進行（無檔案／資源耦合）\n")
    print("　".join(solo) if solo else "（無）")

    undeclared = [f["id"] for f in all_failing if "prerequisites" not in f]
    order = layers(all_failing, {f["id"] for f in features})
    if order and len(order) > 1:
        print("\n## 執行順序（依 prerequisites 拓樸分層）\n")
        for i, layer in enumerate(order, 1):
            print(f"{i}. {'　'.join(layer)}")
        print("\n同一層代表前置條件都已滿足，彼此沒有宣告的先後關係。")
    if undeclared:
        print(f"\n⚠ 沒有申報 prerequisites，未納入順序與平行判斷：{'、'.join(undeclared)}")
        print("  （沒有欄位不等於沒有依賴——下次動到這幾條時順手補）")

    timing = undeclared_timing(items)
    if timing:
        print("\n## ⚠ 未宣告的時序耦合（needs／creates 推論，只警告不擋）\n")
        for line in timing:
            print(f"- {line}")
        print("\n波次排序已把這些當 prerequisite 處理；規格該補 prerequisites，不是靠工具猜。")

    # 執行波次＝prerequisites 分層再用 touches／requires 交集下推（gsd-core 規則）。
    # 沒申報 prerequisites 或沒 touches 的一律不排——寧可少建議，也不要建議一個會撞車的平行。
    if order:
        wv, blocked = waves(order, items, hubs)
        if wv:
            print("\n## 執行波次（同一波零檔案／資源交集，可同時派）\n")
            for i, w in enumerate(wv, 1):
                print(f"wave {i}. {'　'.join(w)}")
            print("\n規則：wave = max(prerequisite waves)+1；同波有 touches／requires 交集就把後者下推一波。"
                  "\n真的要平行時，每個會寫入的 agent 各自 `isolation: \"worktree\"`，收工前整合。")
        if blocked:
            print(f"\n⚠ 前置條目資料不足、未排波次：{'、'.join(blocked)}")

    print(
        "\n---\n價值提醒：這份分析的主要用途是**減少 feature 條數**，其次才是順序與平行。"
        "\n2026-07-29 否決的是「多開 session 改同一個 checkout」——那個反對理由（互相踩到）"
        "\n由 worktree 隔離解掉了，所以 2026-08-05 起平行重新開放，但邊界只放在 feature 之間，"
        "\n不在一條 feature 內部拆。"
    )
    return 0


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    repo_root = sys.argv[1]
    features = load(repo_root)
    if sys.argv[2] == "--check" and len(sys.argv) >= 4:
        return cmd_check(features, sys.argv[3])
    if sys.argv[2] == "--dsm":
        return cmd_dsm(features, "--json" in sys.argv)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
