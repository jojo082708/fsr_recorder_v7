"""分件與螺絲接合圖 FSR-15（印表機 300 × 300 × 350）
用法： python3 make_split_drawing.py [輸出資料夾]
"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import afo_v17 as A
import drawing_lib as dl
from matplotlib.patches import Rectangle, Circle

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "drawings")
P = A.P
parts, D = A.build(P, verbose=False)
SP = D["split"]
rear = parts["F1A_腳底件後段(分件)"][0]; front = parts["F1B_腳底件前段(分件)"][0]
cart = [A.as_mesh(w) for k, (w, m) in parts.items() if k.startswith(("C0", "C1"))]
cov = A.as_mesh(parts["B2_走線蓋板"][0])
CR, CF = (0.93, 0.62, 0.40), (0.50, 0.66, 0.88)
br, bf = rear.bounds[1] - rear.bounds[0], front.bounds[1] - front.bounds[0]

fig, bg = dl.new_sheet(15, "腳底件分件與螺絲接合（印表機 300 × 300 × 350）", "爆炸圖不依比例；剖面 2:1；底視 1:2.5 (A3)",
    [f"F1A 後段 {br[0]:.0f} × {br[1]:.0f} × {br[2]:.0f}（直立後跟杯，可平放列印）；F1B 前段 {bf[0]:.0f} × {bf[1]:.0f} × {bf[2]:.0f}。兩件都在 300 × 300 × 350 內。",
     f"接合：x = {SP['Xc']:.0f} 處底板搭接 {P['Lap_L']:.0f} mm（後段在上層 z {P['Lap_Z']:.0f}→15、前段在下層 z 0→{P['Lap_Z']:.0f}），牆在 x = {SP['Xc']:.0f} 對接；配合間隙 {P['Split_Gap']} mm。",
     f"鎖固：6 × M4×12 平頭（沉頭）螺絲由底面鎖入後段 6 × M4 熱熔螺母（Ø5.6 × 5）；螺絲頭低於底面。接合位於兩組感測匣之間，走線槽與 B2 蓋板跨過接縫（蓋板一件，順便壓住接縫）。",
     "建議：接合面可加少量 PETG 用膠（或 CA 膠）增加剛性；列印時兩件底面朝下，搭接面不需支撐。"])

# 左上：爆炸等角
ax = fig.add_axes([0.02, 0.43, 0.6, 0.54]); ax.set_aspect("equal"); ax.axis("off")
off = np.array([45.0, 0, 35.0])
items = [(rear, CR, 1.0), (front.copy().apply_translation(off), CF, 1.0)] + \
        [(m.copy().apply_translation(off if m.bounds[0][0] > SP["Xc"] else (0, 0, 0)), (0.45, 0.78, 0.5), 1.0) for m in cart]
d, up = (-0.75, -0.95, -0.75), (0, 0, 1)
lo, hi = dl.render(ax, items, d, up, lw=0.3)
ax.set_xlim(lo[0] - 40, hi[0] + 40); ax.set_ylim(lo[1] - 10, hi[1] + 10)
for (x, y) in SP["screws"]:
    p0 = dl.proj(np.array([x, y, P["Lap_Z"]]), d, up)[0][0]; p1 = dl.proj(np.array([x, y, P["Lap_Z"]]) + off, d, up)[0][0]
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], ls="--", lw=0.5, color="#333", zorder=11)
c_r = dl.proj(np.array([60, 0, 40]), d, up)[0][0]; c_f = dl.proj(np.array([230, 0, 20]) + off, d, up)[0][0]
dl.balloon(ax, c_r, c_r + np.array([-60, 40]), "F1A 後段")
dl.balloon(ax, c_f, c_f + np.array([50, 40]), "F1B 前段")
ax.set_title("分件爆炸圖（虛線 = M4 螺絲位置）", fontsize=9)

# 右上：剖面 y = −2（穿過中間那列螺絲）
axs = dl.view_axes(fig, (268, 175, 140, 105), 0.5)
for m, fc, ht in ((rear, "#f2c3a0", "///"), (front, "#b9cdea", "\\\\\\")):
    g = dl.section_polys(m, (0, -2.0, 0), (0, -1, 0), (1, 0, 0))
    dl.draw_polys(axs, g, fc, ht)
for dx in P["Split_Screw_DX"]:
    x = SP["Xc"] + dx
    axs.add_patch(Rectangle((x - 2.0, 0.6), 4.0, 11.4, fc="#4b5560", ec="k", lw=0.5, zorder=6))
    axs.add_patch(Rectangle((x - 4.0, 0.0), 8.0, 1.0, fc="#4b5560", ec="k", lw=0.5, zorder=6))
    axs.add_patch(Rectangle((x - 2.8, P["Lap_Z"]), 5.6, 5.0, fc="#c9a227", ec="k", lw=0.5, zorder=5, alpha=0.9))
axs.set_xlim(SP["Xc"] - 35, SP["Xc"] + 35); axs.set_ylim(-6, 46.5)
dl.hdim(axs, SP["Xa"], SP["Xb"], 15, 22, f"搭接 {P['Lap_L']:.0f}", fs=6.5)
dl.vdim(axs, 0, P["Lap_Z"], SP["Xa"], SP["Xa"] - 8, f"{P['Lap_Z']:.0f}", fs=6.5)
dl.vdim(axs, P["Lap_Z"], 15, SP["Xb"], SP["Xb"] + 8, f"{15 - P['Lap_Z']:.0f}", fs=6.5)
dl.leader(axs, (SP["Xc"] - 7.5, 9.5), (SP["Xc"] - 33, 34), "M4 熱熔螺母", fs=6.5)
dl.leader(axs, (SP["Xc"] + 7.5, 3), (SP["Xc"] + 12, -3.5), "M4×12 平頭螺絲（由底面）", fs=6.5)
axs.text(SP["Xc"] - 30, 18, "F1A 後段", fontsize=7, color="#b0581f"); axs.text(SP["Xc"] + 18, 18, "F1B 前段", fontsize=7, color="#2a5db0")
axs.set_title("剖面 Y = −2（看向 −Y）", fontsize=9)

# 右中：印表機成形空間
axp = dl.view_axes(fig, (268, 60, 140, 105), 3.0)
axp.add_patch(Rectangle((0, 0), 300, 300, fill=False, ec="#333", lw=1.0)); axp.text(150, 305, "列印平台 300 × 300", ha="center", fontsize=7)
for m, col, x0, y0, nm in ((rear, CR, 10, 160, "F1A"), (front, CF, 10, 10, "F1B")):
    g = A.slice_poly(A.to_manifold(m), 1.0); g = max(getattr(g, "geoms", [g]), key=lambda q: q.area)
    c = np.array(g.exterior.coords); c = c - c.min(0) + [x0, y0]
    axp.fill(c[:, 0], c[:, 1], color=col, alpha=0.8); axp.text(c[:, 0].mean(), c[:, 1].mean(), nm, ha="center", va="center", fontsize=8)
axp.set_xlim(-20, 320); axp.set_ylim(-20, 320 * 105 / 140 * 1.0 + 0)
dl.set_center(axp, (150, 150))
axp.set_title("兩件可同盤列印（俯視排版示意）", fontsize=9)

# 下：底視圖（螺絲位置）
axb = dl.view_axes(fig, (14, 52, 245, 80), 2.0)
lo, hi = dl.render(axb, [(rear, CR, 1.0), (front, CF, 1.0)], (0, 0, 1), (0, -1, 0), lw=0.25)
dl.set_center(axb, (lo + hi) / 2)
for (x, y) in SP["screws"]:
    p = dl.proj(np.array([x, y, 0.0]), (0, 0, 1), (0, -1, 0))[0][0]
    axb.add_patch(Circle(p, 4.2, fill=False, ec="#c0392b", lw=1.0, zorder=9))
pc = dl.proj(np.array([SP["Xc"], -70, 0.0]), (0, 0, 1), (0, -1, 0))[0][0]
axb.text(pc[0], pc[1] - 4, "6 × M4 平頭螺絲（紅圈）", ha="center", fontsize=7, color="#c0392b")
axb.set_title("底視圖", fontsize=9)
path = os.path.join(OUT, "15_分件與螺絲接合.png")
fig.savefig(path, dpi=170)
print(path)
