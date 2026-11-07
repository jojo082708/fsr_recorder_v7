"""FSR-17 模組化套件：共用後段 + 可換前段（穿鞋 / 赤腳 / 任意尺寸）"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import afo_v17 as A
import drawing_lib as dl
from matplotlib.patches import Circle

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "drawings")
R = {}
for v in ("shoe", "barefoot"):
    p = dict(A.P); p.update(A.VARIANTS[v])
    parts, D = A.build(p, verbose=False)
    R[v] = dict(p=p, D=D, parts={k: A.as_mesh(w) for k, (w, m) in parts.items()})
P0 = R["shoe"]["parts"]
rear = P0["F1A_腳底件後段(分件)"]
cart = [m for k, m in P0.items() if k.startswith(("C0", "C1"))]
cov = P0["B2_走線蓋板"]
fs, fb = R["shoe"]["parts"]["F1B_腳底件前段(分件)"], R["barefoot"]["parts"]["F1B_腳底件前段(分件)"]
ts = [m for k, m in R["shoe"]["parts"].items() if k.startswith("T1")][0]
tb = [m for k, m in R["barefoot"]["parts"].items() if k.startswith("T1")][0]
hs = [m for k, m in R["barefoot"]["parts"].items() if k.startswith("H1")][0]
CR, CS, CB, CT, CH = (0.93, 0.64, 0.42), (0.52, 0.66, 0.88), (0.55, 0.78, 0.62), (0.95, 0.62, 0.30), (0.85, 0.55, 0.75)

dl.TAG = "AFO v17 模組化 / 左腳"
fig, bg = dl.new_sheet(17, "模組化套件：共用後段 + 可換前段（穿鞋 / 赤腳 / 任意尺寸）", "不依比例；俯視 1:3 (A3)",
    ["共用後段 F1A（後跟杯、小腿件介面、S2 腳跟感測匣、走線出口）只印一次；依需求換前段 F1B（含 S1 大拇趾球感測匣）＋對應鞋頭擋塊 T1。",
     "前後段接法：x = 120 底板搭接 30 mm，6 × M4×12 平頭螺絲由底面鎖入後段 M4 熱熔螺母 → 鬆 6 支螺絲即可換前段。放大從 x = 140 之後才開始，所以所有前段都能接同一個後段。",
     "赤腳時插入 H1 腳跟墊塊（12 mm，2 支 Ø5 插腳）讓腳跟位置與穿鞋相同 → S1 (197.3, −25)、S2 (45.3, +12) 兩種用法都一樣，不必移動感測器。",
     "任意尺寸：python3 cad/export_kit.py out/kit shoe:長x寬 barefoot:腳長x腳寬（例 shoe:300x105）→ 產生該尺寸前段 + 擋塊；前段長度上限約 300（列印平台）。"])
ax = fig.add_axes([0.01, 0.2, 0.66, 0.78]); ax.set_aspect("equal"); ax.axis("off")
d, up = (-0.7, -0.9, -0.8), (0, 0, 1)
OS, OB = np.array([60.0, -150.0, 0]), np.array([60.0, 150.0, 0])
items = [(rear, CR, 1.0), (cov, (0.35, 0.55, 0.9), 1.0)] + [(m, (0.45, 0.78, 0.5), 1.0) for m in cart if m.bounds[0][0] < 120]
items += [(fs.copy().apply_translation(OS), CS, 1.0), (ts.copy().apply_translation(OS + [25, 0, 15]), CT, 1.0)]
items += [(m.copy().apply_translation(OS), (0.45, 0.78, 0.5), 1.0) for m in cart if m.bounds[0][0] > 120]
items += [(fb.copy().apply_translation(OB), CB, 1.0), (tb.copy().apply_translation(OB + [25, 0, 15]), CT, 1.0),
          (hs.copy().apply_translation([-40, 0, 60]), CH, 1.0)]
items += [(m.copy().apply_translation(OB), (0.45, 0.78, 0.5), 1.0) for m in cart if m.bounds[0][0] > 120]
lo, hi = dl.render(ax, items, d, up, lw=0.3)
ax.set_xlim(lo[0] - 40, hi[0] + 40); ax.set_ylim(lo[1] - 10, hi[1] + 10)
I = lambda pt: dl.proj(np.asarray(pt, float), d, up)[0][0]
for pt, t, txt in (((40, 0, 70), (-70, 40), "F1A 共用後段"), ((260, 0, 10) + OS, (70, -30), "F1B 穿鞋前段 310×110"),
                   ((330, 0, 30) + OS, (80, 20), "T1 擋塊（v15 放大）"), ((230, 0, 10) + OB, (60, 50), "F1B 赤腳前段 254×100"),
                   ((280, 20, 30) + OB, (70, 25), "T1 客製擋塊（依腳型）"), ((-34, 0, 100), (-60, 30), "H1 腳跟墊塊（赤腳用）")):
    dl.balloon(ax, I(pt), I(pt) + np.array(t), txt, fs=7.5)
for o in (OS, OB):
    a, b = I((120, 0, 7)), I(np.array([120, 0, 7]) + o)
    ax.plot([a[0], b[0]], [a[1], b[1]], ls="--", lw=0.6, color="#555", zorder=11)
ax.set_title("同一個後段，可接穿鞋前段或赤腳前段", fontsize=9)

# 右：兩種組合俯視
for k, (v, ttl) in enumerate((("shoe", "穿鞋組合（整體 349 × 134）"), ("barefoot", "赤腳組合（整體 299 × 122）"))):
    axp = dl.view_axes(fig, (290, 175 - k * 110, 116, 100), 3.2)
    r = R[v]; pp = r["parts"]
    its = [(rear, CR, 1.0), (pp["F1B_腳底件前段(分件)"], CS if v == "shoe" else CB, 1.0), (cov, (0.35, 0.55, 0.9), 1.0)]
    its += [(m, CT, 1.0) for kk, m in pp.items() if kk.startswith("T1")] + [(m, CH, 1.0) for kk, m in pp.items() if kk.startswith("H1")]
    its += [(m, (0.45, 0.78, 0.5), 1.0) for m in cart]
    lo, hi = dl.render(axp, its, (0, 0, -1), (0, 1, 0), lw=0.2)
    dl.set_center(axp, (lo + hi) / 2)
    raw = np.loadtxt(os.path.join(HERE, "data", "footprint_outline_mm.csv"), delimiter=",")
    axp.plot(raw[:, 0] + 20.3, raw[:, 1], color="#b03030", lw=0.7, zorder=9)
    for S in (r["D"]["S1"], r["D"]["S2"]):
        axp.add_patch(Circle(S, 10.5, fill=False, ec="#0b3d6b", lw=0.9, zorder=10))
    axp.axvline(120, color="#c0392b", ls="--", lw=0.7)
    axp.set_title(ttl, fontsize=8.5)
path = os.path.join(OUT, "17_模組化套件_共用後段_可換前段.png")
fig.savefig(path, dpi=170)
print(path)
