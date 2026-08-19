"""harness-plan.py 的最小回歸：waves() 的 gsd 規則。python harness-plan-test.py"""
import importlib.util, sys, os
spec = importlib.util.spec_from_file_location("hp", os.path.join(os.path.dirname(__file__), "harness-plan.py"))
hp = importlib.util.module_from_spec(spec); spec.loader.exec_module(hp)

F = [
    {"id": "F1", "status": "failing", "prerequisites": [], "touches": ["a.py"]},
    {"id": "F2", "status": "failing", "prerequisites": [], "touches": ["a.py", "b.py"]},   # 與 F1 交集 → 下推
    {"id": "F3", "status": "failing", "prerequisites": [], "touches": ["c.py"]},
    {"id": "F4", "status": "failing", "prerequisites": ["F2"], "touches": ["d.py"]},        # 依賴 F2 → wave 3
    {"id": "F5", "status": "failing", "prerequisites": ["F6"], "touches": ["e.py"]},        # F6 沒 touches → blocked
    {"id": "F6", "status": "failing", "prerequisites": []},                                  # 沒 touches 不排
]
items = [f for f in F if f.get("touches")]
order = hp.layers(F, {f["id"] for f in F})
wv, blocked = hp.waves(order, items, set())
assert wv == [["F1", "F3"], ["F2"], ["F4"]], wv
assert blocked == ["F5"], blocked
# 零交集時全部 wave 1
wv2, _ = hp.waves(order, [items[0], items[2]], set())
assert wv2 == [["F1", "F3"]], wv2
# needs/creates：F8 needs api:x，F7 creates 它且同層 → F8 推到 F7 後一波；且列為未宣告時序
G = [
    {"id": "F7", "status": "failing", "prerequisites": [], "touches": ["p.py"], "creates": ["api:x"]},
    {"id": "F8", "status": "failing", "prerequisites": [], "touches": ["q.py"], "needs": ["api:x"]},
    {"id": "F9", "status": "failing", "prerequisites": ["F7"], "touches": ["r.py"], "needs": ["api:x"]},  # 有宣告 → 不警告
]
wv3, b3 = hp.waves(hp.layers(G, {f["id"] for f in G}), G, set())
assert wv3 == [["F7"], ["F8", "F9"]], wv3
assert b3 == [], b3
assert hp.undeclared_timing(G) == ["F8 needs 的東西由 F7 creates，但 F8 的 prerequisites 沒寫 F7"], hp.undeclared_timing(G)
print("harness-plan-test: ok")
