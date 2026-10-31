"""
AFO v17 工程圖（A3 橫式、第三角法、mm）
用法： FOOTPRINT_IMG=腳印照片.jpg python3 make_drawings.py [輸出資料夾]
"""
import os, sys, math, time
import numpy as np
import trimesh
import cadquery as cq
from shapely.geometry import Polygon, Point, LineString, box as sbox

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import afo_v17 as A
import drawing_lib as dl
from drawing_lib import new_sheet, view_axes, set_center, hdim, vdim, leader, balloon, centerline, render, proj
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "drawings")
os.makedirs(OUT, exist_ok=True)
t0 = time.time()
P = A.P
parts, D = A.build(P, verbose=False)
S1, S2 = D["S1"], D["S2"]
ZT = D["ZT"]
inner = D["inner"]

COL = {"F": (0.58, 0.66, 0.80), "L": (0.80, 0.66, 0.48), "T": (0.95, 0.62, 0.28), "B": (0.30, 0.50, 0.85),
       "C": (0.60, 0.82, 0.55), "TPU": (0.30, 0.76, 0.76), "STEEL": (0.82, 0.82, 0.85), "FSR": (0.18, 0.18, 0.18),
       "STRAP": (0.25, 0.25, 0.30), "PCB": (0.10, 0.50, 0.26), "PCB_W": (0.94, 0.94, 0.90), "SHOE": (0.80, 0.78, 0.74),
       "WIRE": (0.85, 0.15, 0.15)}
M = {k: A.as_mesh(w) for k, (w, m) in parts.items()}
MOD = {k: m for k, (w, m) in parts.items()}


def resample(ring, n):
    L = ring.length
    return [ring.interpolate(t * L).coords[0] for t in np.linspace(0, 1, n, endpoint=False)]


# ---------------- 示意件：布鞋、魔鬼氈、走線
shoe2d = inner.buffer(-4, join_style=1).intersection(sbox(9.0, -200, 268, 200))
shoe2d = shoe2d.difference(sbox(0, 32.0, 46, 200)).difference(sbox(0, -200, 46, -32.0)).buffer(6, join_style=1).buffer(-6, join_style=1)
SOLE_T = 25.0
sole = A.as_mesh(A.ext(shoe2d.simplify(0.3), ZT, SOLE_T))
up0 = shoe2d.buffer(-3)
up1 = Polygon([(x * 0.62 + 14, y * 0.72) for x, y in shoe2d.buffer(-12).exterior.coords])
w0 = cq.Wire.makePolygon([cq.Vector(x, y, ZT + SOLE_T) for x, y in resample(up0.exterior, 90)], close=True)
w1 = cq.Wire.makePolygon([cq.Vector(x, y, ZT + SOLE_T + 68) for x, y in resample(up1.exterior, 90)], close=True)
upper = A.as_mesh(cq.Solid.makeLoft([w0, w1], True))
M["SHOE_sole"] = sole; MOD["SHOE_sole"] = "SHOE"
M["SHOE_upper"] = upper; MOD["SHOE_upper"] = "SHOE"

def strap(x, ztop, yend=52.5, zend=30.0, w=38.0):
    pts = [(-yend, zend), (-yend * 0.9, ztop - 12), (0, ztop), (yend * 0.9, ztop - 12), (yend, zend)]
    sw = cq.Workplane("YZ", origin=(x, 0, 0)).spline(pts, includeCurrent=False).val()
    pl = cq.Plane(origin=sw.startPoint(), xDir=(1, 0, 0), normal=sw.tangentAt(0))
    return A.as_mesh(cq.Workplane(pl).rect(w, 1.6).sweep(cq.Workplane().add(sw)))
M["A4_前掌魔鬼氈"] = strap(187.5, ZT + SOLE_T + 34); MOD["A4_前掌魔鬼氈"] = "STRAP"
M["A4_中足魔鬼氈"] = strap(140.0, ZT + SOLE_T + 48); MOD["A4_中足魔鬼氈"] = "STRAP"

# 後跟出線 → 小腿件背面麵包板（示意線）
ex = D["exit"]
wire3d = np.array([[ex[0] - 2, 0, ex[2]], [-8, 0, ex[2]], [-9, 0, 40], [-12, 0, 78], [-18, -20, 84]])
wire_tube = trimesh.util.concatenate([trimesh.creation.cylinder(radius=1.4, segment=[wire3d[i], wire3d[i + 1]], sections=10) for i in range(len(wire3d) - 1)])
M["W_FSR線(示意)"] = wire_tube; MOD["W_FSR線(示意)"] = "WIRE"

FOOT = "F1_AFO腳底件_v17"; LEG = "L1_AFO小腿件_v15(不改)"
TOE = [k for k in parts if k.startswith("T1")][0]
CART = [k for k in parts if k.startswith("C")]
CART_TOP = [k for k in CART if k.startswith(("C0", "C1"))]
COVER = "B2_走線蓋板"
EL = [k for k in parts if k.startswith("E")]
VIEWS = {"side": ((0, 1, 0), (0, 0, 1)),      # 由內側 (−Y) 看，腳尖朝右
         "front": ((-1, 0, 0), (0, 0, 1)), "rear": ((1, 0, 0), (0, 0, 1)),
         "top": ((0, 0, -1), (0, 1, 0)), "bottom": ((0, 0, 1), (0, -1, 0)),
         "iso": ((-0.8, -1.0, -0.75), (0, 0, 1)), "iso2": ((-0.75, 0.9, -0.7), (0, 0, 1)),
         "iso_rear": ((0.85, -0.75, -0.55), (0, 0, 1))}

def items(names, off=None, alpha=None):
    off = off or {}; alpha = alpha or {}
    return [(M[n].copy().apply_translation(off.get(n, (0, 0, 0))), COL[MOD[n]], alpha.get(n, 1.0)) for n in names]

def P2(pt, v):
    d, up = VIEWS[v]
    return proj(np.asarray(pt, float), d, up)[0][0]

def draw(ax, names, v, off=None, alpha=None, lw=0.35, fit=None):
    d, up = VIEWS[v]
    lo, hi = render(ax, items(names, off, alpha), d, up, lw=lw)
    if fit is not None:
        set_center(ax, ((lo + hi) / 2) + np.asarray(fit))
    return lo, hi

SH = []
def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=160)
    plt.close(fig)
    SH.append(name)
    print("sheet", name, round(time.time() - t0, 1), flush=True)

PLAT = [FOOT, LEG, TOE, COVER] + CART_TOP
PLAT_EL = PLAT + EL + ["W_FSR線(示意)"]
fb = M[FOOT].bounds
LB = M[LEG].bounds

# ================================================================== 01 側視圖
fig, bg = new_sheet(1, "整體側視圖（內側，腳尖朝右）", "比例 1:2 (A3)",
                    ["註：1. 原點 O = 腳底件後緣底面中線（沿用 v15）。小腿件 L1 為 v15 原件，未修改。",
                     "2. 感測匣頂面與托盤底板面 z = 15 齊平（TPU 傳力柱高出 0.3）。S1/S2 中心以鏈線表示。",
                     "3. 布鞋、束帶省略；麵包板/ESP32 位於小腿件背面（示意）。帶 * 者為待確認尺寸。"])
ax = view_axes(fig, (20, 52, 380, 228), 2.0)
draw(ax, PLAT_EL, "side", fit=(-10, -5))
xs = lambda X: P2((X, 0, 0), "side")[0]
for S, nm in ((S1, "S1"), (S2, "S2")):
    centerline(ax, (xs(S[0]), -10), (xs(S[0]), ZT + 30)); ax.text(xs(S[0]), ZT + 33, nm, fontsize=8, color="#7f8c8d", ha="center")
o = P2((0, 0, 0), "side"); ax.plot(*o, "k+", ms=8); ax.text(o[0] - 6, o[1] - 7, "O", fontsize=8)
hdim(ax, xs(fb[0][0]), xs(fb[1][0]), 0, -30, f"{fb[1][0] - fb[0][0]:.0f}  (腳底件全長)")
hdim(ax, xs(0), xs(S2[0]), 0, -12, f"{S2[0]:.1f}*")
hdim(ax, xs(0), xs(S1[0]), 0, -20, f"{S1[0]:.1f}*")
xr = xs(fb[1][0]) + 10
vdim(ax, 0, ZT, xs(fb[1][0]), xr, "15")
vdim(ax, 0, fb[1][2], xs(30), xs(fb[1][0]) + 25, f"{fb[1][2]:.0f}  (後跟杯)")
vdim(ax, 0, LB[1][2], xs(LB[0][0]), xs(LB[0][0]) - 18, f"{LB[1][2]:.1f}  (含小腿件)")
leader(ax, P2((10, 0, 160), "side"), (xs(80), 210), "L1 AFO 小腿件 v15（已列印，不改）")
leader(ax, P2((-28, 0, 200), "side"), (xs(-90), 235), "E5/E6 麵包板 + ESP32（小腿件背面，示意）", ha="left")
leader(ax, P2((255, 0, ZT + 10), "side"), (xs(240), 70), "T1 鞋頭擋塊 H22/T9（v15）")
leader(ax, P2((140, -52, 28), "side"), (xs(150), 95), "v15 束帶扣環（保留）")
leader(ax, P2((100, 0, 12), "side"), (xs(110), -45), "F1 腳底件 v17（x≈100 舊走線槽已補實）")
save(fig, "01_側視圖")

# ================================================================== 02 正視 / 03 後視
for no, v, title in ((2, "front", "整體正視圖（由腳尖向後看）"), (3, "rear", "整體後視圖（由腳跟向前看）")):
    notes = ["註：1. 托盤外寬 118，後跟杯內寬 = 小腿件套筒外寬 + 0.4 間隙（v15 介面不變）。",
             "2. 腳跟感測匣 Ø42 必須落在小腿件套筒內寬 66.4（±33.2）之內：S2 嵌板外緣 y = %.1f。" % (S2[1] + P["Insert_D"] / 2),
             "3. 後視圖：後跟杯背面 z = %.1f 處 Ø5 出線孔，FSR 線沿杯背往上接到小腿件背面麵包板。" % ex[2]]
    fig, bg = new_sheet(no, title, "比例 1:1.5 (A3)", notes)
    ax = view_axes(fig, (20, 52, 380, 228), 1.5)
    draw(ax, PLAT_EL, v, fit=(0, -8))
    yy = lambda Y: P2((0, Y, 0), v)[0]
    for S, nm in ((S1, "S1"), (S2, "S2")):
        centerline(ax, (yy(S[1]), -8), (yy(S[1]), ZT + 26)); ax.text(yy(S[1]), ZT + 29, nm, fontsize=8, color="#7f8c8d", ha="center")
    centerline(ax, (yy(0), -12), (yy(0), LB[1][2] + 8))
    hdim(ax, yy(fb[0][1]), yy(fb[1][1]), 0, -16, f"{fb[1][1] - fb[0][1]:.0f}")
    hdim(ax, yy(0), yy(S1[1]), ZT, -26, f"{abs(S1[1]):.0f}*")
    hdim(ax, yy(0), yy(S2[1]), ZT, -34, f"{abs(S2[1]):.0f}*")
    vdim(ax, 0, ZT, yy(fb[1][1]), yy(fb[1][1]) + 10 * np.sign(yy(fb[1][1])), "15")
    vdim(ax, 0, fb[1][2], yy(fb[0][1]), yy(fb[0][1]) - 10 * np.sign(yy(fb[1][1])), f"{fb[1][2]:.0f}")
    vdim(ax, 0, LB[1][2], yy(fb[0][1]), yy(fb[0][1]) - 22 * np.sign(yy(fb[1][1])), f"{LB[1][2]:.1f}")
    if v == "rear":
        leader(ax, P2((0, 0, ex[2]), v), (yy(45), -10), "Ø5 出線孔 (z=%.1f)" % ex[2])
        leader(ax, P2((-20, 0, 160), v), (yy(70), 170), "E5 麵包板（小腿件背面，示意）")
    else:
        leader(ax, P2((276, 20, ZT + 10), v), (yy(70), 60), "T1 鞋頭擋塊")
    save(fig, f"{no:02d}_{'正視圖' if v == 'front' else '後視圖'}")

# ================================================================== 04 俯視圖
fig, bg = new_sheet(4, "整體俯視圖（托盤底板與感測匣配置）", "比例 1:1.25 (A3)",
                    ["註：1. 外形維持 v15 AFO 托盤造型（腳底件 288×118）；刪除 v15 舊 FSR 構造：x≈100 橫向貫穿槽、中央 T 溝、兩條長方凹槽 → 填平到 z=15。",
                     "2. S1 = 第一蹠骨頭、S2 = 腳跟中心；X = 套筒內面 8.3 + Heel_Offset* 12 + 腳印量測值。紅色虛線圓 = 偏心嵌板微調範圍 R2。",
                     "3. 走線槽 6 寬 × 3.5 深（z 10→13.5），上蓋 B2 走線蓋板 1.5t 與底板齊平 → 電線不外露於鞋底摩擦面；經後跟杯背面 Ø5 孔出線。"])
ax = view_axes(fig, (20, 52, 380, 228), 1.25)
draw(ax, [FOOT, COVER] + CART_TOP, "top", fit=(0, 0))
T = lambda X, Y: P2((X, Y, ZT), "top")
for S, nm in ((S1, "S1"), (S2, "S2")):
    p = T(*S)
    centerline(ax, (p[0] - 30, p[1]), (p[0] + 30, p[1])); centerline(ax, (p[0], p[1] - 30), (p[0], p[1] + 30))
    ax.add_patch(Circle(p, P["Ecc_Max"], fill=False, ls=":", lw=0.7, ec="#c0392b", zorder=9))
    ax.text(p[0] + 4, p[1] + 25, f"{nm} ({S[0]:.1f}, {S[1]:+.0f})*", fontsize=8, color="#c0392b", zorder=11)
centerline(ax, T(-10, 0), T(295, 0))
o = T(0, 0); ax.plot(*o, "k+", ms=9); ax.text(o[0] - 6, o[1] - 6, "O", fontsize=8)
yb = lambda k: T(0, fb[0][1] - k)[1]
hdim(ax, T(fb[0][0], 0)[0], T(fb[1][0], 0)[0], yb(0), yb(28), f"{fb[1][0] - fb[0][0]:.0f}")
hdim(ax, T(0, 0)[0], T(S2[0], 0)[0], yb(0), yb(10), f"{S2[0]:.1f}*")
hdim(ax, T(0, 0)[0], T(S1[0], 0)[0], yb(0), yb(18), f"{S1[0]:.1f}*")
vdim(ax, T(0, fb[0][1])[1], T(0, fb[1][1])[1], T(fb[1][0], 0)[0], T(fb[1][0] + 12, 0)[0], f"{fb[1][1] - fb[0][1]:.0f}")
vdim(ax, T(0, 0)[1], T(0, S1[1])[1], T(S1[0], 0)[0], T(S1[0] + 32, 0)[0], f"{abs(S1[1]):.0f}*")
vdim(ax, T(0, 0)[1], T(0, S2[1])[1], T(S2[0], 0)[0], T(S2[0] + 32, 0)[0], f"{abs(S2[1]):.0f}*")
vdim(ax, T(0, -33.2)[1], T(0, 33.2)[1], T(8.3, 0)[0], T(-14, 0)[0], "66.4 套筒內寬", fs=6.5)
leader(ax, T(120, -18), (T(150, 0)[0], T(0, -80)[1]), "B2 走線蓋板 (1.5t，齊平)")
leader(ax, T(S1[0] + 15, S1[1] - 12), (T(235, 0)[0], T(0, -78)[1]), "C 感測匣 Ø42（3×M2.5，12 孔 / 30°）")
leader(ax, T(100, 50), (T(80, 0)[0], T(0, 82)[1]), "x≈100 舊走線槽 → 已補實")
save(fig, "04_俯視圖")

# ================================================================== 05 底視圖
fig, bg = new_sheet(5, "腳底件底視圖", "比例 1:1.25 (A3)",
                    ["註：1. 底部三角格柵沿用 v15；感測匣正下方 Ø46 區域改為實心（z 0→15），讓 FSR 受力直接經底板傳到地面。",
                     "2. 建議底面貼 2 mm 止滑橡膠片（後跟 + 前掌），或以 TPU 列印鞋底片黏貼。"])
ax = view_axes(fig, (20, 52, 380, 228), 1.25)
draw(ax, [FOOT], "bottom", fit=(0, 0))
Bv = lambda X, Y: P2((X, Y, 0), "bottom")
for S, nm in ((S1, "S1"), (S2, "S2")):
    p = Bv(*S); ax.add_patch(Circle(p, (P["Insert_D"] + 4) / 2, fill=False, ls="--", lw=0.8, ec="#c0392b", zorder=9))
    ax.text(p[0], p[1] - 30, f"{nm} 下方實心 Ø46", fontsize=7.5, color="#c0392b", ha="center", zorder=11)
hdim(ax, Bv(fb[0][0], 0)[0], Bv(fb[1][0], 0)[0], Bv(0, fb[1][1])[1], Bv(0, fb[1][1])[1] + 15, f"{fb[1][0] - fb[0][0]:.0f}")
vdim(ax, Bv(0, fb[0][1])[1], Bv(0, fb[1][1])[1], Bv(fb[1][0], 0)[0], Bv(fb[1][0], 0)[0] + 12, f"{fb[1][1] - fb[0][1]:.0f}")
save(fig, "05_底視圖")

# ================================================================== 06 等角圖
fig, bg = new_sheet(6, "整體等角圖", "不依比例",
                    ["F 腳底件 v17（藍灰）  L 小腿件 v15（原件，木色）  T 鞋頭擋塊（橘）  C 感測匣（綠/青）  B2 走線蓋板（藍）  E 麵包板/ESP32（示意）",
                     "外形為 v15 AFO 托盤造型：鞋子整隻放進托盤，後跟頂住小腿件套筒，鞋頭由擋塊定位，前掌/中足以魔鬼氈穿過兩側扣環固定。"])
ax = fig.add_axes([0.03, 0.16, 0.94, 0.81]); ax.set_aspect("equal"); ax.axis("off")
lo, hi = draw(ax, PLAT_EL, "iso"); ax.set_xlim(lo[0] - 70, hi[0] + 70); ax.set_ylim(lo[1] - 25, hi[1] + 25)
I = lambda pt: P2(pt, "iso")
for pt, t, txt in (((20, -38, 150), (-80, 10), "L1"), ((S1[0], S1[1], ZT), (60, -45), "C (S1)"), ((S2[0], S2[1], ZT), (-75, -35), "C (S2)"),
                   ((255, 0, ZT + 15), (70, 15), "T1"), ((130, -54, 8), (40, -55), "F1"), ((90, -18, ZT), (-30, -70), "B2"),
                   ((-20, 0, 200), (-60, 30), "E5/E6")):
    p = I(pt); balloon(ax, p, p + np.array(t), txt)
save(fig, "06_等角圖")

# ================================================================== 07 布鞋 + AFO
fig, bg = new_sheet(7, "布鞋與平台組合等角圖", "不依比例（布鞋為示意外形）",
                    ["穿戴：穿好布鞋 → 整隻鞋放進托盤，鞋跟頂住小腿件套筒內面 → 鞋頭由 T1 擋塊定位（H16/22/28 × T6/9/12 九種可換）→ 扣前掌、中足魔鬼氈 → 扣小腿束帶。",
                     "不拆解、不開孔、不修改布鞋。鞋底與底板間建議貼 1 mm 止滑矽膠片（感測匣位置開 Ø22 孔）。"])
ax = fig.add_axes([0.03, 0.16, 0.94, 0.81]); ax.set_aspect("equal"); ax.axis("off")
names = PLAT_EL + ["SHOE_sole", "SHOE_upper", "A4_前掌魔鬼氈", "A4_中足魔鬼氈"]
lo, hi = draw(ax, names, "iso", alpha={"SHOE_upper": 0.5, "SHOE_sole": 0.85}); ax.set_xlim(lo[0] - 70, hi[0] + 70); ax.set_ylim(lo[1] - 25, hi[1] + 25)
for pt, t, txt in (((120, 0, ZT + SOLE_T + 40), (-30, 95), "布鞋（使用者自有）"), ((187.5, 0, ZT + SOLE_T + 34), (90, 40), "A4 前掌魔鬼氈"),
                   ((140, 0, ZT + SOLE_T + 48), (40, 90), "A4 中足魔鬼氈"), ((20, -38, 150), (-80, 10), "L1 小腿件")):
    p = I(pt); balloon(ax, p, p + np.array(t), txt)
save(fig, "07_布鞋平台組合等角圖")

# ================================================================== 08 固定機構爆炸圖
fig, bg = new_sheet(8, "布鞋固定機構爆炸圖", "不依比例",
                    ["L1 小腿件（v15 原件）：下緣套筒插入腳底件後跟杯內側（間隙約 0.4），以兩側螺絲固定；套筒內面即鞋跟定位面。",
                     "T1 鞋頭擋塊（v15 原件，9 種尺寸）：插入托盤前端插槽，依鞋長選用 T6/T9/T12、依鞋頭高度選 H16/H22/H28。",
                     "A4 魔鬼氈 38 mm × 2：穿過托盤兩側 v15 扣環（x≈140、x≈188）跨過鞋面；小腿部分沿用 v15 小腿束帶。"])
ax = fig.add_axes([0.03, 0.17, 0.94, 0.8]); ax.set_aspect("equal"); ax.axis("off")
off = {LEG: (-40, 0, 90), TOE: (60, 0, 50), "A4_前掌魔鬼氈": (0, 0, 70), "A4_中足魔鬼氈": (0, 0, 90)}
names = [FOOT, COVER] + CART_TOP + [LEG, TOE, "A4_前掌魔鬼氈", "A4_中足魔鬼氈"]
lo, hi = draw(ax, names, "iso2", off=off); ax.set_xlim(lo[0] - 60, hi[0] + 60); ax.set_ylim(lo[1] - 20, hi[1] + 20)
I2 = lambda pt: P2(pt, "iso2")
for n, t, txt in ((LEG, (-70, 20), "L1 小腿件 (v15)"), (TOE, (70, 20), "T1 鞋頭擋塊"), ("A4_前掌魔鬼氈", (80, 30), "A4 前掌"), ("A4_中足魔鬼氈", (-60, 40), "A4 中足"),
                  (FOOT, (60, -60), "F1 腳底件 v17")):
    b = M[n].bounds; c = (b[0] + b[1]) / 2; o_ = np.asarray(off.get(n, (0, 0, 0)))
    p = I2(c + o_); balloon(ax, p, p + np.array(t), txt)
    if n in off:
        a_, b_ = I2(c), I2(c + o_)
        ax.plot([a_[0], b_[0]], [a_[1], b_[1]], ls="--", lw=0.5, color="#2c3e50", zorder=11)
save(fig, "08_固定機構爆炸圖")

# ================================================================== 09 剖面圖
SEC = {"F": ("#b5bcc6", "///"), "B": ("#9fb8e6", "\\\\\\"), "C": ("#cfe8c6", "///"), "TPU": ("#9fdede", "xx"),
       "STEEL": ("#e6e6ea", None), "FSR": ("#222222", None), "L": ("#e8d2b0", "///")}
fig, bg = new_sheet(9, "雙 FSR 感測模組剖面圖", "比例 3:1 (A3)",
                    ["受力路徑：鞋底 → C1 TPU 導槽頂面 (Ø21，高出 0.3) → TPU 柱 → C2 鋼珠 Ø5 → C5 保護傳力片 Ø10×0.5 → C3 FSR402 中央感測區 → C4 支撐座 → 腳底件底板 → 地面。",
                     "鋼珠：側向被 Ø5.15 導槽孔限制（只能上下），下方 Ø4.5 防脫唇；導槽再被 Ø21.4 頂唇與 Ø12 止擋肩鎖在感測匣內 → 不會脫出。",
                     f"過載保護：TPU 下沉超過 Stop_Gap = {P['Stop_Gap']} mm 時外環坐上止擋肩，多餘的力繞過 FSR；FSR 最大受力 ≈ 68.7·δ^1.5 ≈ {68.7 * P['Stop_Gap'] ** 1.5:.0f} N（TPU 95A 估算，需校正）。",
                     "FSR 更換：鬆開 3×M2.5 → 整個感測匣由上方取出（腳跟匣在小腿件套筒內，需先取出布鞋）。"])
for k, (S, nm) in enumerate(((S1, "A-A 剖面：S1 第一蹠骨頭（X = %.1f）" % S1[0]), (S2, "B-B 剖面：S2 腳跟（X = %.1f）" % S2[0]))):
    ax = view_axes(fig, (16 + k * 198, 62, 190, 210), 1 / 3.0)
    cx = S[0] + P["Sensor_Ecc"]
    names = [FOOT, COVER, LEG] + [n for n in CART if n.endswith(f"-{1 + k}") or f"-{1 + k}_" in n]
    for n in names:
        g = dl.section_polys(M[n], (cx, 0, 0), (-1, 0, 0), (0, -1, 0))
        fc, ht = SEC[MOD[n]]
        dl.draw_polys(ax, g, fc, ht, zorder=5 if MOD[n] in ("FSR", "STEEL") else 3)
    c = -S[1]
    W, H = ax._wh
    ax.set_xlim(c - W / 2, c + W / 2); ax.set_ylim(-8, H - 8)
    ax.add_patch(Circle((c, D["zc_ball"]), P["Ball_D"] / 2, fc="#dfe3e8", ec="k", lw=0.6, zorder=7))
    centerline(ax, (c, -4), (c, ZT + 8))
    ax.set_title(nm, fontsize=10, pad=4)
    vdim(ax, D["z_sh_top"], D["z_boss0"], c + 0.8, c + 5, f"{D['z_boss0'] - D['z_sh_top']:.2f}", fs=6)
    vdim(ax, D["z_ledge"][1], D["z_skirt0"], c - 9.5, c - 15, f"Stop_Gap {P['Stop_Gap']}", fs=6)
    vdim(ax, ZT, D["z_pad"], c - 8, c - 19, f"{P['Pad_Proud']}", fs=6)
    vdim(ax, 0, ZT, c + 24, c + 28, "15", fs=6)
    vdim(ax, 0, P["Base_Floor"], c + 15, c + 19, "3", fs=6)
    hdim(ax, c - P["Guide_Neck_D"] / 2, c + P["Guide_Neck_D"] / 2, D["z_pad"], D["z_pad"] + 4, "Ø21", fs=6)
    hdim(ax, c - P["Insert_D"] / 2, c + P["Insert_D"] / 2, ZT, ZT + 8, "Ø42 定位嵌板", fs=6)
    hdim(ax, c - P["Tube_OD"] / 2, c + P["Tube_OD"] / 2, 3.2, -4, "Ø27 導筒", fs=6)
    hdim(ax, c - P["FSR_D"] / 2, c + P["FSR_D"] / 2, D["z_seat_top"], -1.3, "FSR Ø18.3", fs=5.5)
    lab = [((c - 5, D["z_pad"] - 2), "C1 TPU 導槽 (95A)"), ((c - 0.8, D["zc_ball"] + 0.8), "C2 鋼珠 Ø5"),
           ((c - 3, D["z_sh_top"] - 0.25), "C5 保護傳力片"), ((c - 7.5, D["z_fsr_top"] - 0.2), "C3 FSR 402"),
           ((c - 10.5, D["z_seat_top"] - 0.7), "C4 FSR 支撐座"), ((c - 12.5, 9), "C0 感測匣殼 (PETG)"),
           ((c - 25, 6), "F1 腳底件底板"),
           ((c + 2.1, D["z_boss0"] + 0.2), "Ø4.5 防脫唇"), ((c + 2.6, D["zc_ball"]), "Ø5.15 導槽孔（只能上下）"),
           ((c + 5.5, D["z_ledge"][0] + 0.6), "Ø12 止擋肩（過載）"), ((c + 10.6, D["z_shoulder"] + 1.0), "Ø21.4 頂唇")]
    left = sorted([l for l in lab if l[0][0] < c - 0.5], key=lambda l: l[0][1])
    right = sorted([l for l in lab if l[0][0] >= c - 0.5], key=lambda l: l[0][1])
    for col, grp in ((0, left), (1, right)):
        for row, (pt, txt) in enumerate(grp):
            leader(ax, pt, (c - 31 if col == 0 else c + 31, 30 + row * 4.2), txt, fs=6.5, ha="left" if col == 0 else "right")
save(fig, "09_雙FSR剖面圖")

# ================================================================== 10 電子模組 / 走線
fig, bg = new_sheet(10, "後跟電子模組安裝圖（小腿件背面麵包板 + 走線）", "左：不依比例；右：1:1.5",
                    ["E5 長條麵包板 + E6 ESP32 裝在 L1 小腿件背面（v15 已列印的麵包板位置，零件不改）；v16 外掛電控盒已刪除。",
                     "走線：C3 FSR 尾線 → 腳底件走線槽（B2 蓋板下）→ 後跟杯背面 Ø5 出線孔 → 沿杯背往上（建議螺旋套管 + 2 個束線扣）→ 麵包板 2×JST-XH 2P。",
                     "分壓電路：FSR 串 10 kΩ 接 3.3 V，接點進 ESP32 ADC1（例 GPIO34 / GPIO35）。電源：行動電源或 18650 模組，固定於小腿件背面或腰包（待確認）。"])
ax = fig.add_axes([0.02, 0.17, 0.5, 0.8]); ax.set_aspect("equal"); ax.axis("off")
lo, hi = draw(ax, [FOOT, LEG, COVER] + CART_TOP + EL + ["W_FSR線(示意)"], "iso_rear"); ax.set_xlim(lo[0] - 60, hi[0] + 40); ax.set_ylim(lo[1] - 20, hi[1] + 20)
I3 = lambda pt: P2(pt, "iso_rear")
for pt, t, txt in (((-18, 0, 160), (-70, 20), "E5 麵包板"), ((-30, 0, 215), (-60, 30), "E6 ESP32"), ((-9, 0, 40), (-70, -20), "FSR 線（示意）"),
                   ((0, 0, ex[2]), (-40, -60), "Ø5 出線孔"), ((60, 30, ZT), (70, -40), "B2 走線蓋板")):
    p = I3(pt); balloon(ax, p, p + np.array(t), txt, fs=7)
ax2 = view_axes(fig, (225, 160, 180, 112), 1.5)
draw(ax2, [FOOT, COVER] + CART_TOP, "top", fit=(0, 0))
p1, p2_ = D["wire_path"]
for ln in (p1, p2_):
    c_ = np.array(ln.coords); pp = np.array([P2((x, y, ZT), "top") for x, y in c_])
    ax2.plot(pp[:, 0], pp[:, 1], color="#c0392b", lw=1.2, zorder=12)
ax2.set_title("走線路徑（紅線，俯視）", fontsize=9)
ax3 = view_axes(fig, (225, 52, 180, 100), 0.25)
xsec = 120.0
for n in [FOOT, COVER]:
    g = dl.section_polys(M[n], (xsec, 0, 0), (-1, 0, 0), (0, -1, 0))
    fc, ht = SEC[MOD[n]]; dl.draw_polys(ax3, g, fc, ht)
yc = -float(np.interp(xsec, [75, S1[0] - 30], [-22, S1[1]]))
ax3.set_xlim(yc - 22.5, yc + 22.5); ax3.set_ylim(0, 25)
ax3.add_patch(Circle((yc - 0.8, 11.0), 0.7, fc="#c0392b", ec="k", lw=0.3, zorder=8)); ax3.add_patch(Circle((yc + 0.8, 11.0), 0.7, fc="#222", ec="k", lw=0.3, zorder=8))
hdim(ax3, yc - P["Wire_W"] / 2, yc + P["Wire_W"] / 2, P["Wire_Bottom"], 6, "6", fs=6)
hdim(ax3, yc - P["Cover_W"] / 2, yc + P["Cover_W"] / 2, ZT, 19, "9 蓋板", fs=6)
vdim(ax3, P["Wire_Bottom"], ZT - P["Cover_T"], yc + 6, yc + 11, "3.5", fs=6)
vdim(ax3, ZT - P["Cover_T"], ZT, yc - 6, yc - 11, "1.5", fs=6)
ax3.set_title(f"走線槽剖面 X = {xsec:.0f}（4:1）", fontsize=9)
save(fig, "10_電子模組與走線圖")

# ================================================================== 11 整體爆炸
fig, bg = new_sheet(11, "整體系統爆炸組裝圖", "不依比例")
X_off = {FOOT: (0, 0, 0), COVER: (0, 0, 40), LEG: (-60, 0, 120), TOE: (70, 0, 60)}
for n in CART:
    lvl = {"C4": 45, "C3": 58, "C5": 68, "C2": 78, "C1": 92, "C0": 112}[n[:2]]
    X_off[n] = (0, 0, lvl)
for n in EL:
    X_off[n] = (-60 - (25 if n.startswith("E6") else 0), 0, 120)
ax = fig.add_axes([0.0, 0.03, 0.66, 0.95]); ax.set_aspect("equal"); ax.axis("off")
names = list(X_off.keys())
lo, hi = draw(ax, names, "iso", off=X_off, lw=0.3); ax.set_xlim(lo[0] - 50, hi[0] + 50); ax.set_ylim(lo[1] - 30, hi[1] + 30)
c_scr = (lo + hi) / 2
done = set()
for n in names:
    code = n.split("_")[0]
    b = M[n].bounds; c = (b[0] + b[1]) / 2; c[2] = b[1][2]
    p = P2(c + np.asarray(X_off[n]), "iso")
    v = p - c_scr; v = v / (np.linalg.norm(v) + 1e-9)
    balloon(ax, p, p + v * 45, code, fs=6.5)
tbl = [("F1", "AFO 腳底件 v17（由 v15 修改）", "PETG", 1), ("L1", "AFO 小腿件 v15（原件，不改）", "已列印", 1),
       ("T1", "鞋頭擋塊 v15（9 種擇一）", "PETG", 1), ("A4", "魔鬼氈束帶 38 mm", "尼龍", 2), ("B2", "走線蓋板 1.5t", "PETG", 1),
       ("C0", "感測匣殼（嵌板+導筒）", "PETG", 2), ("C1", "TPU 導槽（傳力柱）", "TPU 95A", 2), ("C2", "鋼珠 Ø5", "SUJ2", 2),
       ("C3", "FSR 402", "Interlink", 2), ("C4", "FSR 支撐座", "PETG/鋁", 2), ("C5", "保護傳力片 Ø10×0.5", "SUS304", 2),
       ("E5", "長條麵包板", "外購", 1), ("E6", "ESP32 DevKit", "外購", 1)]
axt = fig.add_axes([0.665, 0.3, 0.29, 0.66]); axt.axis("off")
t_ = axt.table(cellText=[[a, b, c, str(d)] for a, b, c, d in tbl], colLabels=["件號", "名稱", "材料", "數量"],
               colWidths=[0.12, 0.58, 0.18, 0.12], loc="upper center", cellLoc="left")
t_.auto_set_font_size(False); t_.set_fontsize(7.5); t_.scale(1, 1.35)
save(fig, "11_整體爆炸組裝圖")

# ================================================================== 12 感測器安裝位置圖
from PIL import Image
fig, bg = new_sheet(12, "感測器安裝位置圖（腳印 → 托盤座標）", "比例 1:1.5 (A3)",
                    ["左：使用者腳印（左腳）。S1 距腳尖 72 / 距內側 22、S2 距外側 35、S2 距腳跟 21（圖上標註）/ 25（依比例量得）→ 待確認。",
                     f"右：托盤座標 X = 套筒內面 8.3 + Heel_Offset* {P['Heel_Offset']:.0f} + 腳跟距；Y = 47 − 距外側（左腳 +Y = 外側）。",
                     "紅色虛線 = 偏心嵌板微調 R2；腳跟匣 Ø42 必須在小腿件套筒內寬 ±33.2 以內。"])
axf = view_axes(fig, (16, 62, 130, 215), 1.5, center=(0, 135))
img_path = os.environ.get("FOOTPRINT_IMG")
if img_path and os.path.exists(img_path):
    im = np.asarray(Image.open(img_path).convert("RGB")).astype(int)
    red = (im[..., 0] - im[..., 1] > 40) & (im[..., 0] - im[..., 2] > 30)
    sx, sy = 589 / 94.0, 1551 / 249.0
    rgba = np.zeros(red.shape + (4,)); rgba[red] = (0.85, 0.2, 0.2, 0.55)
    axf.imshow(rgba, extent=(-(47 - (0 - 102) / sx), -(47 - (im.shape[1] - 102) / sx), (1642 - im.shape[0]) / sy, 1642 / sy), origin="upper", zorder=1)
raw = np.loadtxt(os.path.join(HERE, "data", "footprint_outline_mm.csv"), delimiter=",")
axf.plot(-raw[:, 1], raw[:, 0], color="k", lw=0.6)
for (fx, fyl), nm in ((P["Foot_S1"], "S1"), (P["Foot_S2"], "S2")):
    u, v = -(47 - fyl), fx
    axf.add_patch(Circle((u, v), 10, fill=False, ec="#1a5276", lw=1.0)); axf.plot(u, v, "+", color="#1a5276", ms=8)
    axf.text(u + 13, v + 6, nm, fontsize=8, color="#1a5276")
hdim(axf, -47, 47, 0, -10, "94", fs=7); vdim(axf, 0, 249, 47, 58, "249", fs=7)
vdim(axf, 177, 249, 25, 40, "72", fs=7); hdim(axf, 25, 47, 177, 160, "22", fs=7)
hdim(axf, -47, -12, 25, 50, "35", fs=7); vdim(axf, 0, 25, -12, -30, "25 (21?)*", fs=6.5)
axf.set_title("腳印", fontsize=9)
axp = view_axes(fig, (150, 62, 255, 215), 1.25)
draw(axp, [FOOT, COVER] + CART_TOP, "top", fit=(0, -10))
fo = Polygon([(x + 8.3 + P["Heel_Offset"], -y) for x, y in raw[:, :2] * [1, -1]])
c_ = np.array(fo.exterior.coords); pp = np.array([P2((x, y, ZT), "top") for x, y in c_])
axp.plot(pp[:, 0], pp[:, 1], color="#8e44ad", lw=0.8, ls="--", zorder=10, label="腳印（對位示意）")
for S, nm in ((S1, "S1"), (S2, "S2")):
    p = P2((S[0], S[1], ZT), "top")
    axp.add_patch(Circle(p, P["Ecc_Max"], fill=False, ec="#c0392b", ls="--", lw=0.8, zorder=11)); axp.plot(*p, "+", color="#c0392b", ms=10, zorder=11)
    axp.text(p[0] + 3, p[1] + 25, f"{nm} = ({S[0]:.1f}, {S[1]:+.0f})*", fontsize=8.5, color="#c0392b", zorder=12)
sl = [P2((x, y, ZT), "top") for x, y in [(8.3, -33.2), (60, -33.2), (60, 33.2), (8.3, 33.2), (8.3, -33.2)]]
sl = np.array(sl); axp.plot(sl[:, 0], sl[:, 1], color="#d35400", lw=0.8, ls=":", zorder=10, label="小腿件套筒內側")
T = lambda X, Y: P2((X, Y, ZT), "top")
hdim(axp, T(0, 0)[0], T(8.3, 0)[0], T(0, -60)[1], T(0, -66)[1], "8.3", fs=6.5)
hdim(axp, T(8.3, 0)[0], T(8.3 + P["Heel_Offset"], 0)[0], T(0, -60)[1], T(0, -72)[1], "Heel_Offset*", fs=6.5)
hdim(axp, T(0, 0)[0], T(S2[0], 0)[0], T(0, -60)[1], T(0, -80)[1], f"{S2[0]:.1f}*", fs=7)
hdim(axp, T(0, 0)[0], T(S1[0], 0)[0], T(0, -60)[1], T(0, -88)[1], f"{S1[0]:.1f}*", fs=7)
axp.legend(loc="upper left", fontsize=7, frameon=False)
axp.set_title("托盤座標（俯視）", fontsize=9)
save(fig, "12_感測器安裝位置圖")

from PIL import Image as _Im
pngs = [_Im.open(os.path.join(OUT, n + ".png")).convert("RGB") for n in SH]
pngs[0].save(os.path.join(OUT, "FSR_AFO_v17_Drawings.pdf"), save_all=True, append_images=pngs[1:], resolution=160)
print("done", round(time.time() - t0, 1))
