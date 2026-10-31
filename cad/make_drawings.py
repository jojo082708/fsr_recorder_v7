"""
產生工程圖（A3 橫式，第三角法，單位 mm）→ drawings/*.png 與 drawings/FSR_Platform_Drawings.pdf
用法： python3 make_drawings.py [輸出資料夾]
"""
import os, sys, math, time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import PathPatch, Circle, Rectangle, FancyBboxPatch, Polygon as MPoly
from matplotlib.path import Path
from matplotlib.backends.backend_pdf import PdfPages
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fsr_platform as fp
import render_lib as rl

for f in ["/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "drawings")
os.makedirs(OUT, exist_ok=True)
P = fp.P
t0 = time.time()
parts, D = fp.build(P)
print("build", round(time.time() - t0, 1))
S1, S2 = D["S1"], D["S2"]
ZT = D["Z_top"]
SIDE = 1 if P["Side"] == "L" else -1

COL = {"A": (0.96, 0.63, 0.26), "B": (0.60, 0.74, 0.88), "C": (0.62, 0.82, 0.56), "D": (0.52, 0.56, 0.63),
       "E": (0.86, 0.50, 0.50), "TPU": (0.30, 0.76, 0.76), "STEEL": (0.82, 0.82, 0.85), "FSR": (0.18, 0.18, 0.18),
       "STRAP": (0.26, 0.26, 0.32), "PCB": (0.10, 0.50, 0.26), "PCB_W": (0.95, 0.95, 0.92), "BAT": (0.30, 0.32, 0.72),
       "SHOE": (0.80, 0.78, 0.74)}
MOD_OF = {k: k[0] for k in parts}

# ------------------------------------------------------------------ 共用：tessellation cache
TESS = {}
def tess_of(name, w, offset=(0, 0, 0)):
    key = name
    if key not in TESS:
        TESS[key] = rl.tess(w, 0.12, 6.0)
    V, F = TESS[key]
    return V + np.asarray(offset), F

def shape_of(w, offset=(0, 0, 0)):
    s = rl.to_shape(w)
    return s.translate(cq.Vector(*offset)) if any(offset) else s

SHOE = D["shoe_parts"]

# ------------------------------------------------------------------ 圖框
A3 = (420, 297)
def new_sheet(no, title, scale_txt, notes=None):
    fig = plt.figure(figsize=(A3[0] / 25.4, A3[1] / 25.4))
    bg = fig.add_axes([0, 0, 1, 1]); bg.set_xlim(0, A3[0]); bg.set_ylim(0, A3[1]); bg.axis("off")
    bg.add_patch(Rectangle((10, 10), 400, 277, fill=False, lw=1.2))
    # 標題欄
    x0, y0, w, h = 250, 10, 160, 36
    bg.add_patch(Rectangle((x0, y0), w, h, fill=False, lw=1.0))
    for yy in (y0 + 12, y0 + 24):
        bg.plot([x0, x0 + w], [yy, yy], "k", lw=0.5)
    bg.plot([x0 + 100, x0 + 100], [y0, y0 + 24], "k", lw=0.5)
    bg.plot([x0 + 130, x0 + 130], [y0, y0 + 24], "k", lw=0.5)
    bg.text(x0 + 3, y0 + 30, "外穿式布鞋 FSR 雙點足底力量量測平台", fontsize=10.5, va="center", weight="bold")
    bg.text(x0 + 3, y0 + 18, title, fontsize=10, va="center")
    bg.text(x0 + 3, y0 + 6, f"單位 mm ｜ 第三角法 ｜ {scale_txt}", fontsize=7.5, va="center")
    bg.text(x0 + 102, y0 + 18, "圖號", fontsize=6.5, va="center"); bg.text(x0 + 102, y0 + 6, "版次", fontsize=6.5, va="center")
    bg.text(x0 + 112, y0 + 18, f"FSR-{no:02d}", fontsize=8, va="center"); bg.text(x0 + 112, y0 + 6, "A 草案", fontsize=8, va="center")
    bg.text(x0 + 132, y0 + 18, "2026-10-31", fontsize=7, va="center"); bg.text(x0 + 132, y0 + 6, "待確認", fontsize=8, va="center", color="#c0392b", weight="bold")
    bg.text(x0 + w - 3, y0 + 30, "AFO v16 / 左腳", fontsize=7, va="center", ha="right")
    if notes:
        bg.text(14, 14, "\n".join(notes), fontsize=7.2, va="bottom", ha="left", linespacing=1.45)
    return fig, bg

def view_axes(fig, rect_mm, center, scale, fit=None):
    """rect_mm=(x,y,w,h) 紙面 mm；center=畫面座標中心；scale=1:N；fit=(dx,dy) → 由 draw() 自動置中後再平移"""
    x, y, w, h = rect_mm
    ax = fig.add_axes([x / A3[0], y / A3[1], w / A3[0], h / A3[1]])
    if fit is not None:
        ax._fit = (w * scale, h * scale, fit)
    ax.set_xlim(center[0] - w * scale / 2, center[0] + w * scale / 2)
    ax.set_ylim(center[1] - h * scale / 2, center[1] + h * scale / 2)
    ax.set_aspect("equal"); ax.axis("off")
    return ax

def label(ax, txt, xy, fs=9, **kw):
    ax.text(*xy, txt, fontsize=fs, ha="center", va="center", **kw)

# ------------------------------------------------------------------ 尺寸標註
def dim(ax, p1, p2, off, txt=None, fs=7, color="#1a5276", ext=True, arrow="<|-|>"):
    """線性尺寸：p1,p2 為被量測點；off 為尺寸線偏移向量（資料座標）"""
    p1, p2, off = map(np.asarray, (p1, p2, off))
    a, b = p1 + off, p2 + off
    if ext:
        n = off / (np.linalg.norm(off) + 1e-9)
        for p, q in ((p1, a), (p2, b)):
            ax.plot([p[0] + n[0] * 1.0, q[0] + n[0] * 2.0], [p[1] + n[1] * 1.0, q[1] + n[1] * 2.0], color=color, lw=0.35)
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle=arrow, color=color, lw=0.5, mutation_scale=6, shrinkA=0, shrinkB=0))
    if txt is None:
        txt = f"{np.linalg.norm(p2 - p1):.1f}".rstrip("0").rstrip(".")
    m = (a + b) / 2
    v = b - a
    ang = math.degrees(math.atan2(v[1], v[0]))
    if ang > 90.1 or ang < -89.9:
        ang += 180
    ax.text(m[0], m[1], txt, fontsize=fs, color=color, ha="center", va="center", rotation=ang,
            bbox=dict(fc="white", ec="none", pad=0.6), zorder=10)

def hdim(ax, x1, x2, y, ylev, txt=None, **kw):
    dim(ax, (x1, y), (x2, y), (0, ylev - y), txt, **kw)

def vdim(ax, y1, y2, x, xlev, txt=None, **kw):
    dim(ax, (x, y1), (x, y2), (xlev - x, 0), txt, **kw)

def leader(ax, xy, txy, txt, fs=7.5, color="k", ha="left"):
    ax.annotate(txt, xy=xy, xytext=txy, fontsize=fs, color=color, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", lw=0.45, color=color, shrinkA=1, shrinkB=0),
                bbox=dict(fc="white", ec="none", pad=0.5), zorder=12)
    ax.plot(*xy, "o", ms=1.6, color=color, zorder=12)

BC = {}
def balloon(ax, xy, txy, txt, color="k", fs=8, r=None):
    """若 ax 已設定氣球中心 (BC[ax])，標籤沿中心→零件方向放射排列，避免穿越零件。"""
    if ax in BC:
        c, R = BC[ax]
        v = np.asarray(xy) - c
        n = np.linalg.norm(v)
        v = v / n if n > 1e-6 else np.array([0, 1.0])
        txy = np.asarray(xy) + v * R
    ax.annotate("", xy=xy, xytext=txy, arrowprops=dict(arrowstyle="-", lw=0.5, color=color, shrinkA=0, shrinkB=0), zorder=12)
    ax.plot(*xy, "o", ms=1.8, color=color, zorder=12)
    ax.text(*txy, txt, fontsize=fs, ha="center", va="center", zorder=13,
            bbox=dict(boxstyle="circle,pad=0.25" if len(txt) <= 3 else "round,pad=0.3", fc="white", ec=color, lw=0.7))

def centerline(ax, p1, p2, color="#7f8c8d"):
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, lw=0.4, ls=(0, (8, 2, 1.5, 2)), zorder=4)

# ------------------------------------------------------------------ 視圖繪製
VIEWS = {
    "side":   ((0, 1, 0), (0, 0, 1)),      # 由內側 (−Y) 看，腳尖朝右
    "medial": ((0, 1, 0), (0, 0, 1)),
    "front":  ((-1, 0, 0), (0, 0, 1)),    # 由腳尖看
    "rear":   ((1, 0, 0), (0, 0, 1)),     # 由腳跟看
    "top":    ((0, 0, -1), (0, 1, 0)),
    "bottom": ((0, 0, 1), (0, -1, 0)),
    "iso":    ((-0.8, -1.0, -0.75), (0, 0, 1)),
    "iso2":   ((0.75, -0.9, -0.7), (0, 0, 1)),
    "iso_rear": ((0.9, -0.8, -0.65), (0, 0, 1)),
}
if SIDE < 0:
    VIEWS["side"] = ((0, -1, 0), (0, 0, 1))

def draw(ax, names, view, offsets=None, shade=True, lines=True, hidden=False, extra=None, alpha=None, lw=0.45, light_lines=None):
    offsets = offsets or {}
    d, up = VIEWS[view] if isinstance(view, str) else view
    items, shapes = [], []
    for n in names:
        if n in parts:
            w, m = parts[n]; col = COL[m]
        else:
            w = SHOE[n]; col = COL["SHOE"]
        off = offsets.get(n, (0, 0, 0))
        V, F = tess_of(n, w, off)
        a = (alpha or {}).get(n, 1.0)
        items.append((V, F, col, a))
        shapes.append(shape_of(w, off))
    if shade:
        rl.shade(ax, items, d, up)
    if getattr(ax, "_fit", None):
        allp = np.vstack([rl.proj(V, d, up)[0] for V, F, c, a in items])
        cx, cy = (allp.min(0) + allp.max(0)) / 2
        W, Hh, (dx, dy) = ax._fit
        ax.set_xlim(cx + dx - W / 2, cx + dx + W / 2); ax.set_ylim(cy + dy - Hh / 2, cy + dy + Hh / 2)
    if lines:
        vis, hid = rl.hlr(shapes, d, up, hidden=hidden)
        rl.lines(ax, vis, lw=lw)
        if hidden:
            rl.lines(ax, hid, lw=0.3, ls=(0, (3, 2)), color="#555")
    return d, up

def P2(pt, view):
    d, up = VIEWS[view]
    return rl.proj(np.atleast_2d(np.asarray(pt, float)), d, up)[0][0]

PLATFORM = [n for n in parts if n[0] in "BCDE" and not n.startswith("A4")] + [n for n in parts if n.startswith(("A1", "A2", "A3"))]
ALL = list(parts.keys())
NO_STRAP = [n for n in ALL if not n.startswith("A4")]
EXTERIOR = [n for n in ALL if not any(n.startswith(p) for p in ("C2", "C3", "C4", "C5", "E3", "E5", "E6", "E7", "E8"))]
EXT_NOSTRAP = [n for n in EXTERIOR if not n.startswith("A4")]

plat = D["plat"]; shoe = D["shoe"]
PX0, PY0, PX1, PY1 = plat.bounds
BX0, BX1 = D["bx0"], D["bx1"]
BY0, BY1 = D["box_y"]; BZ0, BZ1 = D["box_z"]
SH = []  # sheets
def save(fig, name):
    p = os.path.join(OUT, name + ".png")
    fig.savefig(p, dpi=160)
    SH.append(fig)
    print("sheet", name, round(time.time() - t0, 1))

# ================================================================== 01 側視圖
fig, bg = new_sheet(1, "整體平台側視圖（內側，腳尖朝右）", "比例 1:1.5 (A3)",
                    ["註：1. 原點 O = 布鞋鞋跟後緣 / 平台中心線 / 底座底面。X 朝腳尖。",
                     "2. 止滑墊外凸 1.5，著地面 z = -1.5。前掌底部滾動斜削 2.0（X ≥ 0.8·Shoe_Length）。",
                     "3. 束帶與布鞋省略；感測器中心以鏈線表示；電控盒位於外側（圖面後方）。帶 * 者為待確認尺寸。"])
sc = 1.5
ax = view_axes(fig, (20, 60, 380, 215), (0, 0), sc, fit=(0, -10))
draw(ax, EXT_NOSTRAP, "side")
H = lambda x: -x * SIDE if False else x
xs = lambda X: P2((X, 0, 0), "side")[0]
for S, nm in ((S1, "S1"), (S2, "S2")):
    centerline(ax, (xs(S[0]), -8), (xs(S[0]), ZT + 30))
    label(ax, nm, (xs(S[0]), ZT + 34), fs=8, color="#7f8c8d")
o = P2((0, 0, 0), "side")
ax.plot(*o, "k+", ms=8); label(ax, "O", (o[0] + 4 * np.sign(xs(10) - xs(0)), o[1] - 5), fs=8)
hdim(ax, xs(PX0), xs(PX1), -2, -22, f"{PX1 - PX0:.0f}  (平台全長)")
hdim(ax, xs(0), xs(S2[0]), -2, -10, f"{S2[0]:.0f}*")
hdim(ax, xs(0), xs(S1[0]), -2, -15, f"{S1[0]:.0f}*")
hdim(ax, xs(BX0), xs(BX1), BZ1 + 2.5, BZ1 + 14, f"{BX1 - BX0:.0f}  (電控盒)")
hdim(ax, xs(0), xs(P["Shoe_Length"]), ZT, BZ1 + 26, f"Shoe_Length = {P['Shoe_Length']:.0f}*")
xr = xs(PX1) + (8 if xs(PX1) > xs(PX0) else -8)
vdim(ax, 0, ZT, xs(PX1), xr, f"{ZT:.0f}")
vdim(ax, 0, P["Base_H"], xs(PX1), xr + 8 * np.sign(xr - xs(PX1)), f"{P['Base_H']:.0f}")
vdim(ax, -1.5, 0, xs(PX1), xr + 16 * np.sign(xr - xs(PX1)), "1.5")
xl = xs(PX0) + (-10 if xs(PX1) > xs(PX0) else 10)
vdim(ax, ZT, ZT + P["HeelCup_H"], xs(-5), xl - 15 * np.sign(xs(PX1) - xs(PX0)), f"{P['HeelCup_H']:.0f}")
vdim(ax, BZ0, BZ1, xs(BX0), xl - 30 * np.sign(xs(PX1) - xs(PX0)), f"{BZ1 - BZ0:.1f}")
vdim(ax, -1.5, BZ0, xs(BX0), xl - 45 * np.sign(xs(PX1) - xs(PX0)), f"{BZ0 + 1.5:.1f} 離地")
leader(ax, P2((250, 0, ZT + 15), "side"), (xs(250), ZT + 70), "A2 前腳掌固定座 (H22, 可前後調 ±15)")
leader(ax, P2((-10, 0, ZT + 42), "side"), (xs(-60), ZT + 95), "A1 U 型後跟定位座 (H45→25，在電控盒後方)")
leader(ax, P2((90, 0, BZ1 - 15), "side"), (xs(110), BZ1 + 35), "E 後跟電控模組（外側，不在承載面下）")
leader(ax, P2((P['Midfoot_Strap_X'], 0, 4), "side"), (xs(P['Midfoot_Strap_X']) + 0, -40), "中足束帶扣環 (38 mm 魔鬼氈)")
leader(ax, P2((200, 0, 6), "side"), (xs(215), -45), "D1 底座 + D2 止滑墊")
leader(ax, P2((D["Xg"], 0, ZT + 20), "side"), (xs(D["Xg"]) + 0, ZT + 70 + 20), "A3 側限位 (含前掌束帶槽, ±6 調整)")
save(fig, "01_側視圖")

# ================================================================== 02 正視圖 / 03 後視圖
for no, vname, title in ((2, "front", "整體平台正視圖（由腳尖向後看）"), (3, "rear", "整體平台後視圖（由腳跟向前看）")):
    notes = ["註：1. 平台寬度 = Shoe_Max_Width* + 2×Rim(15) ；Rim 為固定件安裝區。",
             "2. 電控盒外下緣 10×10 倒角，平台側傾 ≈10° 前不觸地。",
             "3. 帶 * 者為待確認尺寸（布鞋實測後更新）。"]
    if vname == "rear":
        notes[2:2] = ["3. 電控盒後牆：ESP32 USB 開口 12×8、充電 USB 開口 12×7；後跟定位座可換 S/M/L。"]
    fig, bg = new_sheet(no, title, "比例 1:1 (A3)", notes)
    ax = view_axes(fig, (20, 55, 380, 225), (0, 0), 1.0, fit=(0, -15))
    draw(ax, EXT_NOSTRAP, vname)
    yy = lambda Y: P2((0, Y, 0), vname)[0]
    for S, nm in ((S1, "S1"), (S2, "S2")):
        centerline(ax, (yy(S[1]), -8), (yy(S[1]), ZT + 26))
        label(ax, nm, (yy(S[1]), ZT + 29), fs=8, color="#7f8c8d")
    centerline(ax, (yy(0), -12), (yy(0), ZT + 60))
    hdim(ax, yy(PY0), yy(PY1), 0, -18, f"{PY1 - PY0:.1f}  (平台寬)")
    yb_out = BY1 if SIDE > 0 else BY0
    yb_in = BY0 if SIDE > 0 else BY1
    hdim(ax, yy(PY0 if SIDE > 0 else PY1), yy(yb_out), 0, -30, f"{abs(yb_out - (PY0 if SIDE > 0 else PY1)):.1f}  (含電控盒總寬)")
    hdim(ax, yy(yb_in), yy(yb_out), BZ1, BZ1 + 10, f"{BY1 - BY0:.0f}")
    hdim(ax, yy(0), yy(S1[1]), ZT, ZT + 42, f"{abs(S1[1]):.0f}*")
    hdim(ax, yy(0), yy(S2[1]), ZT, ZT + 50, f"{abs(S2[1]):.0f}*")
    xr = yy(yb_out) + 10 * np.sign(yy(yb_out) - yy(0))
    vdim(ax, BZ0, BZ1, yy(yb_out), xr, f"{BZ1 - BZ0:.1f}")
    vdim(ax, -1.5, BZ0, yy(yb_out), xr, f"{BZ0 + 1.5:.1f}")
    xl = yy(PY1 if SIDE > 0 else PY0) - 10 * np.sign(yy(yb_out) - yy(0))
    vdim(ax, 0, ZT, yy(PY1 if SIDE > 0 else PY0), xl, f"{ZT:.0f}")
    if vname == "front":
        vdim(ax, ZT, ZT + P["Toe_H"], yy(0), yy(0) - 0.0 + 0.1, None) if False else None
        leader(ax, P2((300, 20, ZT + 12), vname), (yy(-20) * 1, ZT + 75), "A2 鞋頭擋塊 H22 / T6")
        leader(ax, P2((D["Xg"], y_ := fp.y_edge(shoe, D["Xg"], -SIDE) - SIDE * 4, ZT + 20), vname), (yy(y_) * 1.25, ZT + 60), "A3 側限位（內側）")
    else:
        leader(ax, P2((-5, 0, ZT + 40), vname), (yy(-30), ZT + 75), "A1 U 型後跟定位座 H45")
        leader(ax, P2((BX0, (BY0 + BY1) / 2, D["esp_z"]), vname), (yy(yb_out) + 25 * np.sign(yy(yb_out)), D["esp_z"] + 20), "ESP32 USB 開口")
        leader(ax, P2((BX0, (BY0 + BY1) / 2, BZ0 + 12), vname), (yy(yb_out) + 25 * np.sign(yy(yb_out)), BZ0 - 4), "充電 USB 開口")
    leader(ax, P2((100, (D["y_box_in"] + 3 * SIDE), D["rail_zc"]), vname), (yy(D["y_box_in"]) + 10 * np.sign(yy(D["y_box_in"])), -45), "E4 燕尾滑軌座（M4×2 鎖底座外牆）")
    save(fig, f"{no:02d}_{'正視圖' if vname == 'front' else '後視圖'}")

# ================================================================== 04 俯視圖
fig, bg = new_sheet(4, "整體平台俯視圖", "比例 1:1.5 (A3)",
                    ["註：1. 束帶省略。S1 = 第一蹠骨頭、S2 = 腳跟中心；座標 (X,Y) 以 O 為原點，+Y = 外側（左腳）。",
                     "2. 感測位置粗調：修改 Sensor1/2_Position 重新列印；細調：偏心定位嵌板 e = 0/3/6，每 30° 一格 → 半徑 6 mm 內任意點。",
                     "3. 上層承載板以 M3 沉頭螺絲鎖入底座熱熔螺母；固定件以 M4 鎖入底座熱熔螺母。帶 * 者待確認。"])
sc = 1.5
ax = view_axes(fig, (20, 52, 380, 228), (0, 0), sc, fit=(0, -5))
draw(ax, EXT_NOSTRAP, "top")
T = lambda X, Y: P2((X, Y, ZT), "top")
for S, nm, foot in ((S1, "S1", P["Foot_S1"]), (S2, "S2", P["Foot_S2"])):
    p = T(*S)
    centerline(ax, (p[0] - 40, p[1]), (p[0] + 40, p[1])); centerline(ax, (p[0], p[1] - 40), (p[0], p[1] + 40))
    ax.add_patch(Circle(p, P["Sensor_Ecc_Max"], fill=False, ls=":", lw=0.6, ec="#c0392b", zorder=6))
    label(ax, f"{nm} ({S[0]:.0f}, {S[1]:+.0f})*", (p[0] + 22, p[1] + 36), fs=8, color="#c0392b")
centerline(ax, T(PX0 - 10, 0), T(PX1 + 10, 0))
o = T(0, 0); ax.plot(*o, "k+", ms=9); label(ax, "O", (o[0] - 5, o[1] - 5), fs=8)
y_dim = PY0 - 2 if SIDE > 0 else PY1 + 2
yb = lambda k: T(0, PY0 - k)[1] if SIDE > 0 else T(0, PY1 + k)[1]
hdim(ax, T(PX0, 0)[0], T(PX1, 0)[0], yb(0), yb(30), f"{PX1 - PX0:.0f}")
hdim(ax, T(0, 0)[0], T(S2[0], 0)[0], yb(0), yb(10), f"{S2[0]:.0f}*")
hdim(ax, T(0, 0)[0], T(S1[0], 0)[0], yb(0), yb(18), f"{S1[0]:.0f}*")
hdim(ax, T(0, 0)[0], T(P["Shoe_Length"], 0)[0], yb(0), yb(24), f"{P['Shoe_Length']:.0f}*")
xr = T(PX1, 0)[0] + 10
vdim(ax, T(0, PY0)[1], T(0, PY1)[1], T(PX1 - 40, 0)[0], xr, f"{PY1 - PY0:.1f}")
vdim(ax, T(0, 0)[1], T(0, S1[1])[1], T(S1[0], 0)[0], T(S1[0] + 42, 0)[0], f"{abs(S1[1]):.0f}*")
vdim(ax, T(0, 0)[1], T(0, S2[1])[1], T(S2[0], 0)[0], T(S2[0] + 40, 0)[0], f"{abs(S2[1]):.0f}*")
vdim(ax, T(0, BY0)[1], T(0, BY1)[1], T(BX0, 0)[0], T(BX0 - 12, 0)[0], f"{BY1 - BY0:.0f}")
hdim(ax, T(BX0, 0)[0], T(BX1, 0)[0], T(0, BY1 if SIDE > 0 else BY0)[1], T(0, (BY1 + 10) if SIDE > 0 else (BY0 - 10))[1], f"{BX1 - BX0:.0f}")
leader(ax, T(D["Xt"] + 15, 13), (T(D["Xt"], 0)[0] + 10, T(0, 60 * SIDE)[1] + 30), "A2 長槽 ±15（鞋長調整）")
leader(ax, T(D["Xg"] + 15, fp.y_edge(shoe, D["Xg"], -SIDE) - SIDE * 12), (T(D["Xg"], 0)[0] + 30, T(0, -80 * SIDE)[1]), "A3 長槽 ±6（鞋寬調整）")
leader(ax, T(P["Midfoot_Strap_X"], fp.y_edge(plat, P["Midfoot_Strap_X"], -SIDE) - SIDE * 5), (T(P["Midfoot_Strap_X"], 0)[0] - 30, T(0, -82 * SIDE)[1]), "中足束帶扣環 40×4.5")
leader(ax, T(S1[0] + 20, S1[1] - 20), (T(S1[0] + 70, 0)[0], T(0, S1[1] - 50 * SIDE)[1]), "C 感測匣 Ø60（12 孔 / 30°）")
save(fig, "04_俯視圖")

# ================================================================== 05 底視圖
fig, bg = new_sheet(5, "整體平台底視圖", "比例 1:1.5 (A3)",
                    ["註：1. D2 止滑橡膠墊 2 mm（凹槽 0.5，外凸 1.5）：後跟區 X < 95、前掌區 140 < X < 0.8·Shoe_Length。",
                     "2. 前掌 0.8·Shoe_Length 之後底面斜削 2.0（toe spring），後跟 X<15 斜削 1.5，幫助步態滾動。",
                     "3. 底板厚 3；FSR 支撐座直接坐在底板上，受力路徑 鋼珠→FSR→支撐座→底板→地面。"])
ax = view_axes(fig, (20, 52, 380, 228), (0, 0), 1.5, fit=(0, 0))
draw(ax, EXT_NOSTRAP, "bottom")
Bv = lambda X, Y, Z=0: P2((X, Y, Z), "bottom")
hdim(ax, Bv(PX0, 0)[0], Bv(PX1, 0)[0], Bv(0, PY1)[1], Bv(0, PY1)[1] + 22, f"{PX1 - PX0:.0f}")
hdim(ax, Bv(-100, 0)[0] if False else Bv(PX0 + 8, 0)[0], Bv(95, 0)[0], Bv(0, PY1)[1], Bv(0, PY1)[1] + 10, "止滑墊（後跟）")
hdim(ax, Bv(140, 0)[0], Bv(0.8 * P["Shoe_Length"] - 3, 0)[0], Bv(0, PY1)[1], Bv(0, PY1)[1] + 10, "止滑墊（前掌）")
hdim(ax, Bv(0.8 * P["Shoe_Length"], 0)[0], Bv(PX1, 0)[0], Bv(0, PY1)[1], Bv(0, PY1)[1] + 10, "toe spring 2.0")
vdim(ax, Bv(0, PY0)[1], Bv(0, PY1)[1], Bv(PX1 - 40, 0)[0], Bv(PX1, 0)[0] + 10, f"{PY1 - PY0:.1f}")
leader(ax, Bv(D["exit"][0], D["y_box_in"] + SIDE * 12, BZ0), (Bv(D["exit"][0], 0)[0] + 10, Bv(0, D["y_box_in"] + SIDE * 75)[1]), "盒底 FSR 線材入口 Ø7（防水套圈）")
save(fig, "05_底視圖")

# ================================================================== 06 等角圖
fig, bg = new_sheet(6, "整體平台等角圖", "不依比例",
                    ["A 布鞋固定機構（橘）  B 上層承載平台（藍）  C FSR 感測模組（綠）  D 底部基座（灰）  E 後跟電控模組（紅）",
                     "感測匣頂面（TPU 傳力柱）高出平台 0.3 mm 作為預壓；其餘鞋底面積由上層承載板支撐。"])
ax = fig.add_axes([0.03, 0.17, 0.94, 0.8]); ax.set_aspect("equal"); ax.axis("off")
draw(ax, EXT_NOSTRAP, "iso")
ax.autoscale_view(); _xl, _yl = ax.get_xlim(), ax.get_ylim(); BC[ax] = (np.array([sum(_xl) / 2, sum(_yl) / 2]), 95)
ax.autoscale_view()
I = lambda pt: P2(pt, "iso")
xl, yl = ax.get_xlim(), ax.get_ylim()
for pt, t, txt in (((0, 0, ZT + 40), (-40, 60), "A1"), ((285, 0, ZT + 15), (60, 40), "A2"), ((D["Xg"], -SIDE * 58, ZT + 20), (70, -20), "A3"),
                   ((120, 0, ZT), (40, -60), "B1"), ((S1[0], S1[1], ZT), (90, -45), "C (S1)"), ((S2[0], S2[1], ZT), (-60, -50), "C (S2)"),
                   ((150, -SIDE * 60, 6), (30, -70), "D1"), ((60, D["y_box_in"] + SIDE * 30, BZ1), (-50, 40), "E")):
    p = I(pt); balloon(ax, p, p + np.array(t), txt)
ax.set_xlim(xl[0] - 60, xl[1] + 60); ax.set_ylim(yl[0] - 60, yl[1] + 60)
save(fig, "06_等角圖")

# ================================================================== 07 布鞋 + 平台
fig, bg = new_sheet(7, "布鞋與平台組合等角圖", "不依比例（布鞋為暫定外形，僅示意）",
                    ["布鞋直接穿在腳上後踩入平台：鞋跟頂住 A1 後跟定位座 → 鞋頭由 A2 擋塊定位 → 左右 A3 限位 → 扣上前掌 / 中足魔鬼氈。",
                     "不拆解、不開孔、不修改布鞋。鞋底與平台之間：上層板表面菱形壓紋 + 1 mm 止滑貼片（感測匣位置開孔）。"])
ax = fig.add_axes([0.03, 0.17, 0.94, 0.8]); ax.set_aspect("equal"); ax.axis("off")
draw(ax, EXTERIOR + ["Shoe_Sole", "Shoe_Upper"], "iso", alpha={"Shoe_Upper": 0.55, "Shoe_Sole": 0.9}, lw=0.35)
ax.autoscale_view(); _xl, _yl = ax.get_xlim(), ax.get_ylim(); BC[ax] = (np.array([sum(_xl) / 2, sum(_yl) / 2]), 90)
ax.autoscale_view()
for pt, t, txt in (((60, 0, ZT + P["Sole_Thickness"] + 40), (-80, 70), "布鞋（使用者自有）"), ((D["Xg"], 0, ZT + P["Sole_Thickness"] + 30), (90, 70), "A4 前掌魔鬼氈"),
                   ((P["Midfoot_Strap_X"], 0, ZT + P["Sole_Thickness"] + 46), (40, 95), "A4 中足魔鬼氈"), ((60, D["y_box_in"] + SIDE * 30, BZ1), (-80, 10), "E 電控盒")):
    p = I(pt); balloon(ax, p, p + np.array(t), txt)
xl, yl = ax.get_xlim(), ax.get_ylim(); ax.set_xlim(xl[0] - 60, xl[1] + 60); ax.set_ylim(yl[0] - 30, yl[1] + 60)
save(fig, "07_布鞋平台組合等角圖")

# ================================================================== 08 固定機構爆炸圖
fig, bg = new_sheet(8, "布鞋固定機構爆炸圖（A 模組）", "不依比例",
                    ["A1 U 型後跟定位座：PETG，3×M4 沉頭；內側可貼 2 mm TPU/EVA 襯墊。可換 S/M/L（依 Shoe 鞋跟寬）。",
                     "A2 前腳掌固定座：PETG，2×M4 + 墊片，長槽 ±15 → 適應鞋長 Shoe_Length ±15。",
                     "A3 側限位（內/外各一）：PETG，各 2×M4，長槽 ±6 → 適應鞋寬；牆上 40×5 穿帶槽給前掌魔鬼氈。",
                     "A4 魔鬼氈 38 mm：前掌帶穿 A3 槽；中足帶穿底座扣環；選配踝帶穿 A1 側槽。"])
ax = fig.add_axes([0.03, 0.2, 0.94, 0.77]); ax.set_aspect("equal"); ax.axis("off")
A_off = {"A1_U型後跟定位座": (-35, 0, 70), "A2_前腳掌固定座(鞋頭擋塊)": (45, 0, 70),
         "A3-L_側限位(外側)": (0, SIDE * 45, 60), "A3-M_側限位(內側)": (0, -SIDE * 45, 60),
         "A4_前掌魔鬼氈束帶": (0, 0, 120), "A4_中足魔鬼氈束帶": (0, 0, 140)}
names = ["B1_上層承載板", "D1_底部基座"] + list(A_off.keys())
draw(ax, names, "iso2", offsets=A_off, alpha={}, lw=0.4)
ax.autoscale_view(); _xl, _yl = ax.get_xlim(), ax.get_ylim(); BC[ax] = (np.array([sum(_xl) / 2, sum(_yl) / 2]), 70)
I2 = lambda pt: P2(pt, "iso2")
for n, (dx, dy, dz) in A_off.items():
    if n.startswith("A4"):
        continue
    s = rl.to_shape(parts[n][0]); c = s.BoundingBox().center
    a = I2((c.x, c.y, ZT + 1)); b = I2((c.x + dx, c.y + dy, ZT + 1 + dz))
    ax.annotate("", xy=a, xytext=b, arrowprops=dict(arrowstyle="-", ls="--", lw=0.5, color="#2c3e50"))
for n, t in (("A1_U型後跟定位座", (-60, 40)), ("A2_前腳掌固定座(鞋頭擋塊)", (70, 30)), ("A3-L_側限位(外側)", (-30, 60)), ("A3-M_側限位(內側)", (50, -40)),
             ("A4_前掌魔鬼氈束帶", (70, 20)), ("A4_中足魔鬼氈束帶", (-70, 30))):
    s = rl.to_shape(parts[n][0]); bb = s.BoundingBox(); off = A_off[n]
    p = I2((bb.center.x + off[0], bb.center.y + off[1], bb.zmax + off[2] - 3))
    balloon(ax, p, p + np.array(t), n.split("_")[0] + " " + n.split("_", 1)[1].split("(")[0], fs=7.5)
ax.autoscale_view(); xl, yl = ax.get_xlim(), ax.get_ylim(); ax.set_xlim(xl[0] - 40, xl[1] + 40); ax.set_ylim(yl[0] - 20, yl[1] + 40)
save(fig, "08_固定機構爆炸圖")

# ================================================================== 09 雙 FSR 剖面圖
SEC_STYLE = {"D": ("#b5bcc6", "///"), "B": ("#c7d9ec", "\\\\\\"), "C": ("#cfe8c6", "///"), "TPU": ("#9fdede", "xx"),
             "STEEL": ("#e6e6ea", None), "FSR": ("#222222", None), "A": ("#f6c48a", "///")}
def draw_section(ax, S, title, sc_lbl):
    cx, cy = S[0] + P["Sensor_Ecc"], S[1]
    d, up = (1, 0, 0), (0, 0, 1)     # 看 +X，剖面 X = S.x
    if SIDE < 0:
        d = (-1, 0, 0)
    names = [n for n in parts if parts[n][1] in SEC_STYLE and not n.startswith(("A", "E"))]
    for n in names:
        w, m = parts[n]
        for f in rl.section_faces(w, (cx, 0, 0), (1, 0, 0)):
            rings = rl.face_polys(f, d, up)
            verts, codes = [], []
            for r in rings:
                verts += list(r) + [r[0]]; codes += [Path.MOVETO] + [Path.LINETO] * (len(r) - 1) + [Path.CLOSEPOLY]
            fc, hatch = SEC_STYLE[m]
            ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec="k", lw=0.5, hatch=hatch, zorder=3 if m not in ("FSR", "STEEL") else 5))
    # 鋼珠以圓表示（剖面）
    yb = rl.proj(np.array([[cx, cy, D["zc_ball"]]]), d, up)[0][0]
    ax.add_patch(Circle(yb, P["Ball_D"] / 2, fc="#dfe3e8", ec="k", lw=0.6, zorder=6))
    ax.add_patch(Circle(yb + np.array([-0.7, 0.7]), 0.6, fc="white", ec="none", zorder=7))
    Y = lambda y: rl.proj(np.array([[cx, y, 0]]), d, up)[0][0][0]
    centerline(ax, (Y(cy), -3), (Y(cy), ZT + 6))
    ax.set_title(title, fontsize=10, pad=4)
    return Y

fig, bg = new_sheet(9, "雙 FSR 感測模組剖面圖", "比例 2.5:1 (A3)",
                    ["受力路徑：鞋底 → C1 TPU 導槽頂面(Ø27，高出 0.3) → TPU 柱 → C2 鋼珠 Ø5 → C5 保護傳力片 Ø10×0.5 → C3 FSR402 中央感測區 → C4 支撐座 → 底座底板。",
                     "鋼珠：側向被 Ø5.15 導槽孔限制（只能上下），下方 Ø4.5 防脫唇（TPU 彈性壓入），整個導槽再被 Ø27.4 頂唇與 Ø14 擋肩鎖在感測匣內 → 不會脫出。",
                     f"過載保護：TPU 下沉超過 Stop_Gap = {P['Stop_Gap']} mm 時，TPU 外環坐上感測匣擋肩，多餘的力繞過 FSR；FSR 最大受力 ≈ 68.7·δ^1.5 ≈ {68.7 * P['Stop_Gap'] ** 1.5:.0f} N（TPU 95A 估算，需校正）。",
                     "FSR 更換：鬆開 3×M3 → 整個感測匣（C0+C1+C2+C3+C4+C5）由上方取出 → 拔 FSR 接頭。電線經底座內腔走到外側出線孔，不經過鞋底摩擦面。"])
zlev = D
for k, (S, nm) in enumerate(((S1, "A-A 剖面：S1 第一蹠骨頭（X = %.0f）" % S1[0]), (S2, "B-B 剖面：S2 腳跟（X = %.0f）" % S2[0]))):
    ax = view_axes(fig, (16 + k * 198, 62, 190, 210), (0, 0), 0.4)
    Y = draw_section(ax, S, nm, "2.5:1")
    cy = S[1]; c = Y(cy)
    ax.set_xlim(c - 38, c + 38); ax.set_ylim(-8, 210 * 0.4 - 8)
    vdim(ax, D["z_sh_top"], D["z_boss0"], c + 1.0, c + 6.5, f"{D['z_boss0'] - D['z_sh_top']:.2f}", fs=6)
    vdim(ax, D["z_ledge"][1], D["z_skirt0"], c - 12.5, c - 21, f"Stop_Gap {P['Stop_Gap']}", fs=6)
    vdim(ax, ZT, D["z_pad"], c - 10, c - 24, f"{P['Pad_Proud']}", fs=6)
    vdim(ax, 0, ZT, c + 31, c + 35, f"{ZT:.0f}", fs=6)
    vdim(ax, 0, P["Base_Floor"], c + 24, c + 27, f"{P['Base_Floor']:.0f}", fs=6)
    hdim(ax, c - P["Guide_Neck_D"] / 2, c + P["Guide_Neck_D"] / 2, D["z_pad"], D["z_pad"] + 4, "Ø27", fs=6)
    hdim(ax, c - P["Insert_D"] / 2, c + P["Insert_D"] / 2, ZT, ZT + 8, "Ø60 定位嵌板", fs=6)
    hdim(ax, c - P["Tube_OD"] / 2, c + P["Tube_OD"] / 2, 3.2, -4, "Ø34 導筒", fs=6)
    hdim(ax, c - P["FSR_D"] / 2, c + P["FSR_D"] / 2, D["z_seat_top"], -1.2, "FSR Ø18.3", fs=5.5)
    lab = [((c - 6, D["z_pad"] - 2), "C1 TPU 導槽 (95A)"), ((c - 0.8, D["zc_ball"] + 0.8), "C2 鋼珠 Ø5 (SUJ2)"),
           ((c - 3, D["z_sh_top"] - 0.25), "C5 保護傳力片 Ø10×0.5"), ((c - 8, D["z_fsr_top"] - 0.2), "C3 FSR 402"),
           ((c - 12, D["z_seat_top"] - 0.7), "C4 FSR 支撐座 1.5t"), ((c - 16, 9), "C0 感測匣殼 (PETG)"),
           ((c - 27, 14), "B1 上層承載板 4t"), ((c - 27, 1.5), "D1 底座（底板 3t）"),
           ((c + 2.2, D["z_boss0"] + 0.2), "Ø4.5 防脫唇（鋼珠不脫出）"), ((c + 6.6, D["z_ledge"][0] + 0.6), "Ø14 止擋肩（過載旁路）"),
           ((c + 13.8, D["z_shoulder"] + 1.2), "Ø27.4 頂唇（導槽不脫出）"), ((c + 2.6, D["zc_ball"]), "Ø5.15 導槽孔：只能上下")]
    left = sorted([l for l in lab if l[0][0] < c - 0.5], key=lambda l: l[0][0])
    right = sorted([l for l in lab if l[0][0] >= c - 0.5], key=lambda l: -l[0][0])
    for col, grp in ((0, left), (1, right)):
        for row, (pt, txt) in enumerate(grp):
            tx = c - 36 if col == 0 else c + 36
            ty = 30 + row * 4.6
            leader(ax, pt, (tx, ty), txt, fs=6.5, ha="left" if col == 0 else "right")
# 位置索引小圖
axk = view_axes(fig, (330, 50, 70, 22), (140, 0), 330 / 70 * 1.0)
axk.add_patch(MPoly(np.array(plat.exterior.coords)[:, [0, 1]] * [1, 1], closed=True, fc="#eef", ec="k", lw=0.4))
for S, nm in ((S1, "A"), (S2, "B")):
    axk.plot([S[0], S[0]], [-75, 75], "r-.", lw=0.5); axk.text(S[0] + 3, 60, nm, fontsize=6, color="r")
axk.set_ylim(-80, 80)
save(fig, "09_雙FSR剖面圖")

# ================================================================== 10 後跟電子模組安裝圖
fig, bg = new_sheet(10, "後跟電子模組安裝圖（E 模組）", "左：不依比例；右上：1:1",
                    ["E4 燕尾滑軌座以 2×M4 水平鎖入底座外側牆熱熔螺母 → E1 盒體由後往前滑入燕尾槽 → M3 定位螺絲鎖定。整盒可整組拆下。",
                     "盒內配置：底層 E7 18650 電池盒 + E8 充電/升壓模組 → E3 托盤 → E5 長條麵包板 → E6 ESP32（USB 朝後牆開口）。",
                     "兩組 FSR 線（各 2 芯）：感測匣 → 底座內腔 → 出線孔 Ø6.4 → 滑軌座通道 → 盒底 Ø7 套圈 → 2×JST-XH 2P 接到麵包板分壓電路 (10 kΩ)。",
                     "電控盒位於平台外側、X < 腳跟承載面以外區域，不承受人體重量；外下緣倒角避免側傾觸地。"])
ax = fig.add_axes([0.02, 0.2, 0.55, 0.77]); ax.set_aspect("equal"); ax.axis("off")
E_off = {"E2_電控盒上蓋": (0, 0, 75), "E6_ESP32": (0, 0, 55), "E5_長條麵包板": (0, 0, 40), "E3_麵包板托盤": (0, 0, 25),
         "E7_18650電池盒": (0, 0, 10), "E8_充電升壓模組": (0, 0, 10), "E1_電控盒體": (0, 0, 0), "E4_電控盒滑軌座": (0, -SIDE * 0, 0)}
names = ["D1_底部基座", "B1_上層承載板", "A1_U型後跟定位座"] + list(E_off)
E_off2 = {k: (v[0] - 0, v[1] + SIDE * 45 if k != "E4_電控盒滑軌座" else v[1], v[2]) for k, v in E_off.items()}
draw(ax, names, "iso_rear", offsets=E_off2, alpha={"D1_底部基座": 0.6, "B1_上層承載板": 0.6, "A1_U型後跟定位座": 0.6}, lw=0.35)
ax.autoscale_view(); _xl, _yl = ax.get_xlim(), ax.get_ylim(); BC[ax] = (np.array([sum(_xl) / 2, sum(_yl) / 2]), 70)
I3 = lambda pt: P2(pt, "iso_rear")
for n, t in (("E2_電控盒上蓋", (60, 30)), ("E6_ESP32", (80, 10)), ("E5_長條麵包板", (90, -10)), ("E3_麵包板托盤", (95, -30)),
             ("E7_18650電池盒", (95, -50)), ("E8_充電升壓模組", (-70, -20)), ("E1_電控盒體", (-60, -60)), ("E4_電控盒滑軌座", (-40, -70))):
    s = rl.to_shape(parts[n][0]); bb = s.BoundingBox(); off = E_off2[n]
    p = I3((bb.center.x + off[0], bb.center.y + off[1], bb.zmax + off[2]))
    balloon(ax, p, p + np.array(t), n.split("_")[0] + " " + n.split("_", 1)[1], fs=7)
ax.autoscale_view(); xl, yl = ax.get_xlim(), ax.get_ylim(); ax.set_xlim(xl[0] - 50, xl[1] + 60); ax.set_ylim(yl[0] - 40, yl[1] + 30)
# 右：盒內俯視配置 1:1
ax2 = view_axes(fig, (238, 150, 170, 125), (0, 0), 1.2, fit=(0, 0))
inner_names = ["E1_電控盒體", "E5_長條麵包板", "E6_ESP32", "E7_18650電池盒", "E8_充電升壓模組"]
draw(ax2, inner_names, "top", lw=0.35)
T2 = lambda X, Y: P2((X, Y, 0), "top")
hdim(ax2, T2(BX0, 0)[0], T2(BX1, 0)[0], T2(0, BY0)[1], T2(0, BY0)[1] - 10, f"{BX1 - BX0:.0f}")
vdim(ax2, T2(0, BY0)[1], T2(0, BY1)[1], T2(BX1, 0)[0], T2(BX1, 0)[0] + 10, f"{BY1 - BY0:.0f}")
bb_ = P["Breadboard_Size"]
label(ax2, f"E5 麵包板 {bb_[0]:.0f}×{bb_[1]:.0f}*", (T2(BX0 + 110, 0)[0], T2(0, (BY0 + BY1) / 2)[1] + 6), fs=7)
label(ax2, "E6 ESP32*", (T2(BX0 + 30, 0)[0], T2(0, (BY0 + BY1) / 2)[1]), fs=7, color="w")
ax2.set_title("盒內配置（上蓋移除，俯視）", fontsize=9)
# 右下：盒體側剖面示意（YZ）
ax3 = view_axes(fig, (238, 52, 170, 92), ((BY0 + BY1) / 2 - SIDE * 25, 32), 0.9)
dsec, usec = ((1, 0, 0), (0, 0, 1)) if SIDE > 0 else ((-1, 0, 0), (0, 0, 1))
xsec = 60.0
for n in ["D1_底部基座", "B1_上層承載板", "E1_電控盒體", "E2_電控盒上蓋", "E3_麵包板托盤", "E4_電控盒滑軌座", "E5_長條麵包板", "E6_ESP32", "E7_18650電池盒"]:
    w, m = parts[n]
    for f in rl.section_faces(w, (xsec, 0, 0), (1, 0, 0)):
        rings = rl.face_polys(f, dsec, usec)
        verts, codes = [], []
        for r in rings:
            verts += list(r) + [r[0]]; codes += [Path.MOVETO] + [Path.LINETO] * (len(r) - 1) + [Path.CLOSEPOLY]
        ax3.add_patch(PathPatch(Path(verts, codes), fc=COL[m], ec="k", lw=0.4, hatch="///" if m in "BDE" else None, alpha=0.9))
Yp = lambda y, z=0: rl.proj(np.array([[xsec, y, z]]), dsec, usec)[0][0]
vdim(ax3, -1.5, BZ0, Yp(BY1 if SIDE > 0 else BY0)[0], Yp(BY1 if SIDE > 0 else BY0)[0] + 8 * np.sign(Yp(1)[0] - Yp(0)[0]) * SIDE, f"{BZ0 + 1.5:.1f}", fs=6)
ax3.plot([Yp(-80)[0], Yp(150 * SIDE)[0]], [-1.5, -1.5], color="#7f8c8d", lw=0.6)
ax3.text(Yp(-60)[0], -5, "地面", fontsize=6, color="#7f8c8d")
_cx = (Yp(-20)[0] + Yp(BY1 if SIDE > 0 else BY0)[0]) / 2
ax3.set_xlim(_cx - 170 * 0.9 / 2, _cx + 170 * 0.9 / 2); ax3.set_ylim(-10, 92 * 0.9 - 10)
ax3.set_title(f"剖面 X = {xsec:.0f}：燕尾滑軌、盒底線材入口", fontsize=9)
save(fig, "10_後跟電子模組安裝圖")

# ================================================================== 11 整體爆炸圖
fig, bg = new_sheet(11, "整體系統爆炸組裝圖", "不依比例")
X_off = {}
for n in ALL:
    m = n[0]
    if n.startswith("D2"): X_off[n] = (0, 0, -45)
    elif n.startswith("D1"): X_off[n] = (0, 0, 0)
    elif n.startswith("B1"): X_off[n] = (0, 0, 55)
    elif n.startswith("C"):
        lvl = {"C4": 75, "C3": 92, "C5": 104, "C2": 116, "C1": 132, "C0": 160}[n[:2]]
        X_off[n] = (0, 0, lvl)
    elif n.startswith("A4"): X_off[n] = (0, 0, 230)
    elif n.startswith("A"): X_off[n] = (0, 0, 200)
    elif n.startswith("E4"): X_off[n] = (0, SIDE * 40, 0)
    elif n.startswith("E"): X_off[n] = (0, SIDE * 90, 40 + {"E1": 0, "E7": 15, "E8": 15, "E3": 30, "E5": 45, "E6": 60, "E2": 85}[n[:2]])
ax = fig.add_axes([0.0, 0.03, 0.66, 0.95]); ax.set_aspect("equal"); ax.axis("off")
draw(ax, [n for n in ALL if not n.startswith("A4")], "iso", offsets=X_off, lw=0.3)
ax.autoscale_view(); _xl, _yl = ax.get_xlim(), ax.get_ylim(); BC[ax] = (np.array([sum(_xl) / 2, sum(_yl) / 2]), 60)
I = lambda pt: P2(pt, "iso")
num = {}
bom_rows = []
for i, n in enumerate([n for n in ALL if not n.startswith("A4")]):
    code = n.split("_")[0]
    base_code = code.split("-")[0]
    if base_code in num and not code.startswith("A3"):
        continue
    num[base_code] = True
    s = rl.to_shape(parts[n][0]); bb = s.BoundingBox(); off = X_off[n]
    p = I((bb.center.x + off[0], bb.center.y + off[1], bb.zmax + off[2]))
    ang = (hash(code) % 360)
    t = p + np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))]) * 40
    balloon(ax, p, t, code, fs=6.5)
ax.autoscale_view(); xl, yl = ax.get_xlim(), ax.get_ylim(); ax.set_xlim(xl[0] - 50, xl[1] + 50); ax.set_ylim(yl[0] - 50, yl[1] + 50)
# 零件表
tbl = [("A1", "U 型後跟定位座", "PETG", 1), ("A2", "前腳掌固定座（鞋頭擋塊）", "PETG", 1), ("A3", "側限位（內/外）", "PETG", 2),
       ("A4", "魔鬼氈束帶 38 mm", "尼龍", 2), ("B1", "上層承載板", "PETG", 1), ("C0", "感測匣殼（嵌板+導筒）", "PETG", 2),
       ("C1", "TPU 導槽（傳力柱）", "TPU 95A", 2), ("C2", "鋼珠 Ø5", "SUJ2", 2), ("C3", "FSR 402", "Interlink", 2),
       ("C4", "FSR 支撐座", "PETG/鋁", 2), ("C5", "保護傳力片 Ø10×0.5", "SUS304", 2), ("D1", "底部基座", "PETG", 1),
       ("D2", "止滑橡膠墊", "橡膠 2t", 2), ("E1", "電控盒體", "PETG", 1), ("E2", "電控盒上蓋", "PETG", 1), ("E3", "麵包板托盤", "PETG", 1),
       ("E4", "燕尾滑軌座", "PETG", 1), ("E5", "長條麵包板", "外購", 1), ("E6", "ESP32 DevKit", "外購", 1), ("E7", "18650 電池盒", "外購", 1),
       ("E8", "充電/升壓模組", "外購", 1)]
axt = fig.add_axes([0.665, 0.2, 0.29, 0.76]); axt.axis("off")
t_ = axt.table(cellText=[[a, b, c, str(d)] for a, b, c, d in tbl], colLabels=["件號", "名稱", "材料", "數量"],
               colWidths=[0.13, 0.55, 0.2, 0.12], loc="upper center", cellLoc="left")
t_.auto_set_font_size(False); t_.set_fontsize(7.5); t_.scale(1, 1.32)
save(fig, "11_整體爆炸組裝圖")

# ================================================================== 12 感測器安裝位置圖
from PIL import Image
from scipy import ndimage as nd
fig, bg = new_sheet(12, "感測器安裝位置圖（腳印 → 平台座標）", "比例 1:1.5 (A3)",
                    ["左：使用者腳印（左腳，大拇趾在內側）。量測值：最長 249、最寬 94、S1 距腳尖 72 / 距內側 22、S2 距外側 35、距腳跟 21（圖上標註）/ 25（依比例量得）→ 待確認。",
                     f"右：平台座標 S = (Heel_Offset* + 腳跟距, Foot_Max_Width/2 − 距外側)。Heel_Offset* = {P['Heel_Offset']:.0f}（鞋跟杯+鞋底外凸，待實測）。",
                     "紅色虛線圓 = 偏心定位嵌板可調範圍 R6（嵌板 e=0/3/6 × 每 30°）。更大的偏差請修改 Sensor_Position 重新列印。",
                     "腳底板外形由腳印輪廓（腳趾合併、足弓填補）依 Shoe_Length*/Shoe_Max_Width* 縮放，再外擴 Rim 15 得平台外形。"])
img_path = os.environ.get("FOOTPRINT_IMG")
axf = view_axes(fig, (16, 62, 130, 215), (124.5, 0), 1.5)
if img_path and os.path.exists(img_path):
    im = np.asarray(Image.open(img_path).convert("RGB")).astype(int)
    red = (im[..., 0] - im[..., 1] > 40) & (im[..., 0] - im[..., 2] > 30)
    sx, sy = 589 / 94.0, 1551 / 249.0
    rgba = np.zeros(red.shape + (4,)); rgba[red] = (0.85, 0.2, 0.2, 0.55)
    # 影像 → (X 朝上, 外側在左) : 繪圖座標 u = -Y, v = X
    x0u, x1u = -(47 - (0 - 102) / sx), -(47 - (im.shape[1] - 102) / sx)
    v0, v1 = (1642 - im.shape[0]) / sy, 1642 / sy
    axf.imshow(rgba, extent=(x0u, x1u, v0, v1), origin="upper", zorder=1, interpolation="bilinear")
raw = np.loadtxt(os.path.join(HERE, "data", "footprint_outline_mm.csv"), delimiter=",")
foot = D["foot"]
fc = np.array(foot.exterior.coords)
axf.plot(-raw[:, 1] * SIDE, raw[:, 0], color="#7f8c8d", lw=0.4)
axf.plot(-fc[:, 1] * SIDE, fc[:, 0], color="k", lw=1.0)
axf.set_xlim(-75, 75); axf.set_ylim(-15, 300)
axf.set_aspect("equal")
for (fx, fyl), nm in ((P["Foot_S1"], "S1"), (P["Foot_S2"], "S2")):
    u, v = -(47 - fyl) * SIDE, fx
    axf.add_patch(Circle((u, v), 10, fill=False, ec="#1a5276", lw=1.0)); axf.plot(u, v, "+", color="#1a5276", ms=8)
    axf.text(u + 13, v + 6, nm, fontsize=8, color="#1a5276")
hdim(axf, -47, 47, 0, -10, "94", fs=7)
vdim(axf, 0, 249, 47, 58, "249", fs=7)
vdim(axf, 177, 249, 25, 40, "72", fs=7)
hdim(axf, 25, 47, 177, 160, "22", fs=7)
hdim(axf, -47, -12, 25, 50, "35", fs=7)
vdim(axf, 0, 25, -12, -30, "25 (21?)*", fs=6.5)
axf.set_title("腳印（腳底板外形）", fontsize=9)
# 右：平台座標
axp = view_axes(fig, (150, 62, 255, 215), (140, 0), 1.25)
axp.set_xlim(axp.get_xlim());
def ring(poly, **kw):
    c = np.array(poly.exterior.coords); axp.plot(c[:, 0], c[:, 1], **kw)
ring(plat, color="#2c3e50", lw=1.0); ring(shoe, color="#e67e22", lw=0.9, ls="--")
fsh = fp.affinity.translate(foot, P["Heel_Offset"], 0); ring(fsh, color="k", lw=0.6)
for S, nm in ((S1, "S1"), (S2, "S2")):
    axp.add_patch(Circle(S, P["Insert_D"] / 2, fill=False, ec="#27ae60", lw=0.8))
    axp.add_patch(Circle(S, P["Guide_Neck_D"] / 2, fill=True, fc="#9fdede", ec="#16a085", lw=0.6))
    axp.add_patch(Circle(S, P["Sensor_Ecc_Max"], fill=False, ec="#c0392b", ls="--", lw=0.8))
    axp.plot(*S, "+", color="#c0392b", ms=10)
    axp.text(S[0] + 4, S[1] + 34 * np.sign(S[1] + 0.01) * (-1 if nm == "S2" else 1), f"{nm} = ({S[0]:.0f}, {S[1]:+.0f})*", fontsize=8.5, color="#c0392b", ha="center")
centerline(axp, (PX0 - 10, 0), (PX1 + 10, 0))
axp.plot(0, 0, "k+", ms=10); axp.text(-6, -7, "O", fontsize=8)
hdim(axp, 0, S2[0], PY0, PY0 - 8, f"{S2[0]:.0f}*", fs=7)
hdim(axp, 0, S1[0], PY0, PY0 - 16, f"{S1[0]:.0f}*", fs=7)
hdim(axp, 0, P["Heel_Offset"], 0, -55 if SIDE > 0 else 55, f"Heel_Offset {P['Heel_Offset']:.0f}*", fs=6.5)
vdim(axp, 0, S1[1], S1[0], S1[0] + 40, f"{abs(S1[1]):.0f}*", fs=7)
vdim(axp, 0, S2[1], S2[0], S2[0] + 40, f"{abs(S2[1]):.0f}*", fs=7)
hdim(axp, 0, P["Shoe_Length"], PY1, PY1 + 10, f"Shoe_Length {P['Shoe_Length']:.0f}*", fs=7)
vdim(axp, fp.y_edge(shoe, 190, -1), fp.y_edge(shoe, 190, 1), 190, 255, f"Shoe_Max_Width {P['Shoe_Max_Width']:.0f}*", fs=6.5)
axp.text(PX1 - 5, PY1 + 2, "外側 (+Y)" if SIDE > 0 else "內側 (+Y)", fontsize=7, ha="right")
axp.text(PX1 - 5, PY0 - 4, "內側 (−Y)" if SIDE > 0 else "外側 (−Y)", fontsize=7, ha="right")
axp.legend(handles=[plt.Line2D([], [], color="#2c3e50", lw=1, label="平台外形 (Rim 15)"), plt.Line2D([], [], color="#e67e22", ls="--", label="布鞋鞋底 (暫定*)"),
                    plt.Line2D([], [], color="k", lw=0.6, label="腳底板外形 (腳印)"), plt.Line2D([], [], color="#c0392b", ls="--", label="偏心可調範圍 R6")],
           loc="upper left", fontsize=7, frameon=False, bbox_to_anchor=(0.0, 1.02))
axp.set_title("平台座標（俯視）", fontsize=9)
save(fig, "12_感測器安裝位置圖")

from PIL import Image as _Im
pngs = [_Im.open(os.path.join(OUT, n)).convert("RGB") for n in sorted(os.listdir(OUT)) if n.endswith(".png") and n[:2].isdigit()]
pngs[0].save(os.path.join(OUT, "FSR_Platform_Drawings.pdf"), save_all=True, append_images=pngs[1:], resolution=160)
print("done", round(time.time() - t0, 1))
