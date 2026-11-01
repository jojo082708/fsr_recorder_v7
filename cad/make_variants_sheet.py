"""FSR-16 兩版本比較：赤腳版 vs 穿鞋版
用法： python3 make_variants_sheet.py [輸出資料夾]
"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import afo_v17 as A
import drawing_lib as dl
from matplotlib.patches import Circle

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "drawings")
raw = np.loadtxt(os.path.join(HERE, "data", "footprint_outline_mm.csv"), delimiter=",")
R = {}
for v in ("barefoot", "shoe"):
    p = dict(A.P); p.update(A.VARIANTS[v])
    parts, D = A.build(p, verbose=False)
    keys = [k for k in parts if k.startswith(("F1A", "F1B"))] or ["F1_AFO腳底件_v17"]
    R[v] = dict(p=p, D=D, foot=A.as_mesh(parts["F1_AFO腳底件_v17"][0]), pieces=[A.as_mesh(parts[k][0]) for k in keys],
                toe=[A.as_mesh(w) for k, (w, m) in parts.items() if k.startswith("T1")],
                cart=[A.as_mesh(w) for k, (w, m) in parts.items() if k.startswith(("C0", "C1"))],
                cov=A.as_mesh(parts["B2_走線蓋板"][0]))

dl.TAG = "AFO v17 兩版本 / 左腳"
fig, bg = dl.new_sheet(16, "兩版本比較：赤腳版 vs 穿鞋版", "俯視 1:2，側視 1:2.6 (A3)",
    ["兩版共用：v15 後跟杯 / 小腿件介面（不改）、底板面 z = 15、兩組鋼珠式 FSR 感測匣（Ø42 凸環高出底板 3 mm，固定位置）、走線槽 + 蓋板、束帶扣環。",
     "赤腳版：依腳掌 254 × 100，腳跟直接頂住小腿件套筒內面（Heel_Offset = 0），托盤一件列印；不裝鞋頭擋塊（擋塊插槽填平），由托盤前牆限位腳尖；建議鋪 3 mm EVA 墊（感測匣處開孔）。",
     "穿鞋版：依鞋底 310 × 110，鞋跟頂住套筒內面（腳跟→鞋底後緣 Heel_Offset 暫定 12），托盤長 346 → 分兩件列印並以 6 × M4 螺絲鎖合；裝鞋頭擋塊。"])
COLF = (0.62, 0.72, 0.88)
TOP, SIDE = ((0, 0, -1), (0, 1, 0)), ((0, 1, 0), (0, 0, 1))
for row, (v, title) in enumerate((("barefoot", "赤腳版（一件列印）"), ("shoe", "穿鞋版（兩件 + 6 × M4）"))):
    r = R[v]; p, D = r["p"], r["D"]
    yb = 190 - row * 105
    ax = dl.view_axes(fig, (14, yb, 250, 92), 2.0)
    cols = [(0.93, 0.66, 0.45), COLF]
    items = [(m, cols[i % 2] if len(r["pieces"]) > 1 else COLF, 1.0) for i, m in enumerate(r["pieces"])]
    items += [(m, (0.95, 0.65, 0.35), 1.0) for m in r["toe"]] + [(r["cov"], (0.35, 0.55, 0.9), 1.0)] + [(m, (0.45, 0.78, 0.5), 1.0) for m in r["cart"]]
    lo, hi = dl.render(ax, items, *TOP, lw=0.25)
    dl.set_center(ax, ((lo + hi) / 2) + np.array([0, -6]))
    X0 = p["Sleeve_Inner_X"] + p["Heel_Offset"]
    ax.plot(raw[:, 0] + X0, raw[:, 1], color="#b03030", lw=0.9, zorder=9)
    for S in (D["S1"], D["S2"]):
        ax.add_patch(Circle(S, 10.5, fill=False, ec="#0b3d6b", lw=1.0, zorder=10)); ax.plot(*S, "+", color="#0b3d6b", ms=8, zorder=10)
    b = r["foot"].bounds
    dl.hdim(ax, b[0][0], b[1][0], b[0][1], b[0][1] - 10, f"{b[1][0] - b[0][0]:.0f}", fs=7)
    dl.vdim(ax, b[0][1], b[1][1], b[1][0], b[1][0] + 10, f"{b[1][1] - b[0][1]:.0f}", fs=7)
    ax.text(lo[0], hi[1] + 6, f"{title}　S1 ({D['S1'][0]:.1f}, {D['S1'][1]:+.0f})　S2 ({D['S2'][0]:.1f}, {D['S2'][1]:+.0f})", fontsize=8.5, weight="bold")
    if len(r["pieces"]) > 1:
        ax.axvline(p["Split_X"], color="#c0392b", ls="--", lw=0.8); ax.text(p["Split_X"] + 2, lo[1] - 2, "分件 x = 120", fontsize=6.5, color="#c0392b")
    axs = dl.view_axes(fig, (272, yb, 134, 92), 2.6)
    lo2, hi2 = dl.render(axs, [(m, COLF, 1.0) for m in r["pieces"]] + [(m, (0.95, 0.65, 0.35), 1.0) for m in r["toe"]] + [(m, (0.45, 0.78, 0.5), 1.0) for m in r["cart"]], *SIDE, lw=0.25)
    dl.set_center(axs, (lo2 + hi2) / 2)
    axs.set_title("側視（內側）", fontsize=8)
rows = [("項目", "赤腳版", "穿鞋版"),
        ("依據尺寸", "腳掌 254 × 100", "鞋底 310 × 110"),
        ("腳底件外形", "%.0f × %.0f × 76" % tuple((R["barefoot"]["foot"].bounds[1] - R["barefoot"]["foot"].bounds[0])[:2]),
         "%.0f × %.0f × 76" % tuple((R["shoe"]["foot"].bounds[1] - R["shoe"]["foot"].bounds[0])[:2])),
        ("列印", "一件（< 300）", "兩件 + 6 × M4"),
        ("鞋頭擋塊", "無（前牆限位）", "有"),
        ("Heel_Offset", "0", "12（待確認）"),
        ("S1 / S2 的 X", "%.1f / %.1f" % (R["barefoot"]["D"]["S1"][0], R["barefoot"]["D"]["S2"][0]),
         "%.1f / %.1f" % (R["shoe"]["D"]["S1"][0], R["shoe"]["D"]["S2"][0]))]
path = os.path.join(OUT, "16_兩版本比較_赤腳版_vs_穿鞋版.png")
ax_tab = fig.add_axes([0.035, 0.172, 0.6, 0.108]); ax_tab.axis("off")
t = ax_tab.table(cellText=rows[1:], colLabels=rows[0], loc="center", cellLoc="left", colWidths=[0.24, 0.36, 0.4])
t.auto_set_font_size(False); t.set_fontsize(7); t.scale(1, 1.05)
fig.savefig(path, dpi=170)
print(path)
