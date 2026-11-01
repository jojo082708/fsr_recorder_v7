"""修改前後對照圖 FSR-14：v15（修改前） vs v17（修改後）
用法： python3 make_compare.py [輸出資料夾]
"""
import os, sys
import numpy as np
import trimesh
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import afo_v17 as A
import drawing_lib as dl

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "drawings")
P = A.P
parts, D = A.build(P, verbose=False)
dl.TAG = f"AFO v17 {P['Variant_Name']} / 左腳"
V15 = os.path.join(HERE, "data", "v15")
f15 = trimesh.load(os.path.join(V15, "AFO_foot.stl"))
leg = trimesh.load(os.path.join(V15, "AFO_leg.stl"))
t15 = trimesh.load(os.path.join(V15, "toe_stopper_H22_T9.stl"))
f17 = A.as_mesh(parts["F1_AFO腳底件_v17"][0])
_t = [w for k, (w, m) in parts.items() if k.startswith("T1")]
t17 = A.as_mesh(_t[0]) if _t else None
cov = A.as_mesh(parts["B2_走線蓋板"][0])
cart = [A.as_mesh(w) for k, (w, m) in parts.items() if k.startswith(("C0", "C1"))]
CF15, CF17, CL, CT = (0.86, 0.58, 0.58), (0.55, 0.65, 0.85), (0.80, 0.68, 0.52), (0.95, 0.65, 0.35)

fig, bg = dl.new_sheet(14, "修改前後對照：v15（修改前） vs v17（修改後）", "俯視 / 側視 1:2.2，疊合 1:2 (A3)",
    ["v15 → v17：①依鞋底 310×110 放大托盤（x > 80 拉長 ×%.3f、加寬 ×%.3f；後跟杯不動）②刪除舊 FSR 溝槽並補實側牆開口" % (D["warp"][1], D["warp"][2]),
     "③新增 2 組鋼珠式 FSR 感測匣（S1 大拇趾球、S2 腳跟，Ø42 凸環高出底板 3 mm，固定位置）④走線槽 + 齊平蓋板 + 後跟出線孔 ⑤鞋頭擋塊隨托盤放大。",
     "不變：小腿件 L1（v15 原件）、後跟杯 / 套筒介面、底板面高度 15、束帶扣環造型。"])
TOP, SIDE = ((0, 0, -1), (0, 1, 0)), ((0, 1, 0), (0, 0, 1))

def panel(rect, items, view, title, scale=2.2, dy=0):
    ax = dl.view_axes(fig, rect, scale)
    lo, hi = dl.render(ax, items, *view, lw=0.3)
    dl.set_center(ax, (lo + hi) / 2 + np.array([0, dy]))
    ax.set_title(title, fontsize=9, pad=2)
    return ax, lo, hi

# 上排：v15 / v17 俯視
ax1, lo, hi = panel((14, 205, 190, 75), [(f15, CF15, 1), (t15, CT, 1)], TOP, "v15 修改前（俯視）　288 × 118")
for x, y, txt in ((60, 0, "舊 FSR 溝槽"), (100, 50, "x≈100 貫穿槽")):
    dl.leader(ax1, (x, y), (x + 60, 72 if y > 20 else -72), txt, fs=6.5, color="#9b2c2c")
ax2, lo, hi = panel((214, 205, 192, 75), [(f17, CF17, 1)] + ([(t17, CT, 1)] if t17 is not None else []) + [(cov, (0.3, 0.5, 0.85), 1)] + [(m, (0.4, 0.78, 0.5), 1) for m in cart], TOP,
                    "v17 修改後（俯視）　%.0f × %.0f" % (f17.bounds[1][0] - f17.bounds[0][0], f17.bounds[1][1] - f17.bounds[0][1]))
for S, nm in ((D["S1"], "S1 凸環 FSR"), (D["S2"], "S2 凸環 FSR")):
    dl.leader(ax2, S, (S[0] + 30, 72 if nm.startswith("S2") else -74), nm, fs=6.5, color="#1f4f99")
dl.leader(ax2, (130, -15), (150, 72), "走線槽 + 蓋板", fs=6.5, color="#1f4f99")

# 中排：側視（含小腿件）
ax3, lo, hi = panel((14, 112, 190, 88), [(f15, CF15, 1), (leg, CL, 1), (t15, CT, 1)], SIDE, "v15 側視（內側）", 2.6)
ax4, lo, hi = panel((214, 112, 192, 88), [(f17, CF17, 1), (leg, CL, 1), ] + ([(t17, CT, 1)] if t17 is not None else []) + [(m, (0.4, 0.78, 0.5), 1) for m in cart], SIDE, "v17 側視（內側）　小腿件不變", 2.6)

# 下排：疊合俯視
ax5 = dl.view_axes(fig, (14, 50, 250, 58), 2.7)
from matplotlib.patches import Polygon as MPoly
def outline(m, z):
    g = A.slice_poly(A.to_manifold(m), z)
    g = max(getattr(g, "geoms", [g]), key=lambda q: q.area)
    return np.array(g.exterior.coords)
o15, o17 = outline(f15, 9.0), outline(f17, 9.0)
ax5.add_patch(MPoly(o17, closed=True, fc=(0.55, 0.65, 0.85, 0.35), ec="#2a5db0", lw=1.0))
ax5.add_patch(MPoly(o15, closed=True, fc=(0.86, 0.45, 0.45, 0.30), ec="#b03030", lw=1.0))
ax5.axvline(80, color="#555", ls="--", lw=0.7); ax5.text(82, -62, "x = 80：此線以後放大", fontsize=6.5, color="#333")
dl.set_center(ax5, ((o17.min(0) + o17.max(0)) / 2))
dl.hdim(ax5, -4, 284, -59, -72, "v15 288", fs=6.5); dl.hdim(ax5, -4, 342.4, 67, 76, "v17 346", fs=6.5)
ax5.set_title("外形疊合（紅 = v15、藍 = v17）", fontsize=9, pad=2)

# 右下：差異表
axt = fig.add_axes([0.655, 0.175, 0.315, 0.2]); axt.axis("off")
rows = [("項目", "v15 修改前", "v17 修改後"),
        ("腳底件外形", "288×118×76", "346×134×76"),
        ("可放布鞋", "約 259×100", "310×110"),
        ("FSR", "舊溝槽式", "鋼珠式 ×2（固定）"),
        ("感測匣", "—", "Ø42 凸環 +3 mm"),
        ("過載保護", "無", "止擋，約 69 N"),
        ("走線", "溝槽外露", "槽 + 齊平蓋板"),
        ("小腿件 / 後跟杯", "原設計", "不變")]
t = axt.table(cellText=rows[1:], colLabels=rows[0], loc="center", cellLoc="left", colWidths=[0.3, 0.33, 0.37])
t.auto_set_font_size(False); t.set_fontsize(7.5); t.scale(1, 1.35)
path = os.path.join(OUT, "14_修改前後對照.png")
fig.savefig(path, dpi=170)
print(path)
