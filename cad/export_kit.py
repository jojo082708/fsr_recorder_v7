"""
模組化套件輸出：共用後段 + 可換前段（每個尺寸一個資料夾）
用法：
  python3 export_kit.py OUT                         # 預設：穿鞋 310×110、赤腳 254×100
  python3 export_kit.py OUT shoe:300x105 barefoot:240x95   # 另外產生指定尺寸的前段
輸出：
  OUT/00_共用後段/        F1A 後段、感測匣零件、走線蓋板（所有尺寸共用，只印一次）
  OUT/<尺寸>/             F1B 前段 + 對應鞋頭擋塊（赤腳另有 H1 腳跟墊塊）
"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import afo_v17 as A

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "out", "kit")
specs = sys.argv[2:] or ["shoe:310x110", "barefoot:254x100"]


def variant(spec):
    mode, size = spec.split(":")
    L, W = (float(v) for v in size.lower().split("x"))
    if mode == "barefoot":
        return f"赤腳前段_{L:.0f}x{W:.0f}", dict(Variant_Name=f"赤腳前段 {L:.0f}×{W:.0f}", Shoe_Length=12.0 + L, Shoe_Max_Width=W,
                                                 Heel_Offset=12.0, Split=True, Toe_Stopper="custom", Heel_Spacer=True, Foot_Scale=(L, W))
    return f"穿鞋前段_{L:.0f}x{W:.0f}", dict(Variant_Name=f"穿鞋前段 {L:.0f}×{W:.0f}", Shoe_Length=L, Shoe_Max_Width=W,
                                             Heel_Offset=12.0, Split=True, Toe_Stopper="H22_T9", Heel_Spacer=False, Foot_Scale=None)


def write(folder, items):
    for sub in ("STL", "3MF", "STEP"):
        os.makedirs(os.path.join(folder, sub), exist_ok=True)
    for base, w, printable in items:
        tm = A.as_mesh(w)
        if printable:
            tm.export(os.path.join(folder, "STL", base + ".stl"))
            tm.export(os.path.join(folder, "3MF", base + ".3mf"))
        if hasattr(w, "vertices"):
            A.write_faceted_step(os.path.join(folder, "STEP", base + ".step"), [(base, tm)])
        else:
            import cadquery as cq
            cq.exporters.export(w, os.path.join(folder, "STEP", base + ".step"))


summary = []
common_done = False
for spec in specs:
    name, v = variant(spec)
    p = dict(A.P); p.update(v)
    parts, D = A.build(p, verbose=False)
    if not common_done:
        items = [("F1A_AFO_foot_rear_common", parts["F1A_腳底件後段(分件)"][0], True),
                 ("B2_wire_cover", parts["B2_走線蓋板"][0], True)]
        for k, (w, m) in parts.items():
            if k.startswith("C"):
                code = k.split("_")[0]; base = A.ASCII[code.split("-")[0]] + "_" + code.split("-")[1]
                items.append((base, w, not k.startswith("C3")))
        write(os.path.join(OUT, "00_共用後段"), items)
        rear = parts["F1A_腳底件後段(分件)"][0]
        summary.append(("00_共用後段", "F1A 後段 %.0f×%.0f×%.0f" % tuple(rear.bounds[1] - rear.bounds[0]), D["S1"], D["S2"]))
        common_done = True
    front = parts["F1B_腳底件前段(分件)"][0]
    items = [("F1B_AFO_foot_front", front, True)]
    for k, (w, m) in parts.items():
        if k.startswith("T1"):
            items.append(("T1_toe_stopper", w, True))
        if k.startswith("H1"):
            items.append(("H1_heel_spacer_barefoot", w, True))
    write(os.path.join(OUT, name), items)
    full = parts["F1_AFO腳底件_v17"][0]
    summary.append((name, "F1B 前段 %.0f×%.0f×%.0f，整體 %.0f×%.0f" % (*(front.bounds[1] - front.bounds[0]), *(full.bounds[1] - full.bounds[0])[:2]),
                    D["S1"], D["S2"]))
    print(name, "front", np.round(front.bounds[1] - front.bounds[0], 1), "full", np.round(full.bounds[1] - full.bounds[0], 1))
with open(os.path.join(OUT, "套件清單.txt"), "w") as fh:
    for row in summary:
        fh.write(f"{row[0]}: {row[1]}；S1 {row[2]}、S2 {row[3]}\n")
print("done", OUT)
