"""把 three.js 算圖（render/shots）組成 A3 工程圖 + PDF。
用法： python3 exo/make_sheets.py SHOTS_DIR out/exo/meta.json drawings/exo
"""
import os, sys, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle, Circle
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image

for f in ["/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

SH, META, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
M = json.load(open(META))
D, P, MO = M["dims"], M["params"], M["motors"]
A3 = (420, 297)
PROJECT = "ALICE 風格下肢外骨骼（AK70-10 髖 / AK60-6 膝，3D 列印連桿）"
RED = "#c0392b"


def sheet(no, title, scale="", notes=None):
    fig = plt.figure(figsize=(A3[0] / 25.4, A3[1] / 25.4))
    bg = fig.add_axes([0, 0, 1, 1]); bg.set_xlim(0, A3[0]); bg.set_ylim(0, A3[1]); bg.axis("off")
    bg.add_patch(Rectangle((10, 10), 400, 277, fill=False, lw=1.2))
    x0, y0, w, h = 250, 10, 160, 30
    bg.add_patch(Rectangle((x0, y0), w, h, fill=False, lw=1.0))
    bg.plot([x0, x0 + w], [y0 + 20, y0 + 20], "k", lw=0.5); bg.plot([x0, x0 + w], [y0 + 10, y0 + 10], "k", lw=0.5)
    bg.plot([x0 + 115, x0 + 115], [y0, y0 + 20], "k", lw=0.5)
    bg.text(x0 + 3, y0 + 25, PROJECT, fontsize=8.6, va="center", weight="bold")
    bg.text(x0 + 3, y0 + 15, title, fontsize=9.5, va="center")
    bg.text(x0 + 3, y0 + 5, f"單位 mm ｜ {scale}", fontsize=7.5, va="center")
    bg.text(x0 + 118, y0 + 15, f"EXO-{no:02d}", fontsize=8.5, va="center")
    bg.text(x0 + 118, y0 + 5, "2026-11-15 草案", fontsize=7.5, va="center", color=RED)
    if notes:
        bg.text(14, 14, "\n".join(notes), fontsize=7, va="bottom", ha="left", linespacing=1.45)
    return fig, bg


def img_axes(fig, rect, path, crop=None):
    ax = fig.add_axes([rect[0] / A3[0], rect[1] / A3[1], rect[2] / A3[0], rect[3] / A3[1]])
    im = Image.open(path).convert("RGB")
    if crop: im = im.crop(crop)
    ax.imshow(im); ax.axis("off")
    return ax


# ---------- 正交視圖：影像座標 ↔ 模型座標
S_MM, W, H = 0.5, 1000, 2600


def ortho_axes(fig, rect, path, h_of_u, z0=-400, zr=(-930, 200)):
    """rect：紙上位置；影像以模型 mm 為座標放入（1:5 → 紙 mm = 模型 mm / 5）。"""
    im = np.asarray(Image.open(path).convert("RGB"))
    hl, hr = h_of_u(0), h_of_u(W)
    zt, zb = z0 + H / 2 * S_MM, z0 - H / 2 * S_MM
    x, y, w, hh = rect
    ax = fig.add_axes([x / A3[0], y / A3[1], w / A3[0], hh / A3[1]])
    ax.imshow(im, extent=[hl, hr, zb, zt])
    # 1:5 固定比例
    hc = (hl + hr) / 2
    ax.set_xlim(hc - w * 2.5, hc + w * 2.5)
    zc = (zr[0] + zr[1]) / 2
    ax.set_ylim(zc - hh * 2.5, zc + hh * 2.5)
    ax.set_aspect("equal"); ax.axis("off")
    return ax


def dim_v(ax, h, z1, z2, txt, side=1, ext_from=None, fs=7):
    ax.annotate("", (h, z1), (h, z2), arrowprops=dict(arrowstyle="<|-|>", lw=0.7, color="k", shrinkA=0, shrinkB=0,
                                                         mutation_scale=7))
    if ext_from is not None:
        for z in (z1, z2):
            ax.plot([ext_from, h + 3 * side], [z, z], color="k", lw=0.35)
    ax.text(h + 4 * side, (z1 + z2) / 2, txt, rotation=90, va="center", ha="left" if side > 0 else "right", fontsize=fs)


def dim_h(ax, z, h1, h2, txt, ext_from=None, fs=7, below=False):
    ax.annotate("", (h1, z), (h2, z), arrowprops=dict(arrowstyle="<|-|>", lw=0.7, color="k", shrinkA=0, shrinkB=0,
                                                         mutation_scale=7))
    if ext_from is not None:
        for hh in (h1, h2):
            ax.plot([hh, hh], [ext_from, z + (-3 if below else 3)], color="k", lw=0.35)
    ax.text((h1 + h2) / 2, z + (-6 if below else 4), txt, ha="center", va="top" if below else "bottom", fontsize=fs)


def leader(ax, p, q, txt, fs=7, color="k"):
    ax.annotate(txt, p, q, fontsize=fs, color=color, ha="left" if q[0] >= p[0] else "right", va="center",
                arrowprops=dict(arrowstyle="-", lw=0.5, color=color, shrinkA=0, shrinkB=0))
    ax.plot(*p, "o", ms=1.8, color=color)


zK, zA, zs = D["zK"], D["zA"], D["zs"]
hip, kn = D["hip"], D["knee"]
mh, mk = MO[P["HIP_MOTOR"]], MO[P["KNEE_MOTOR"]]
pages = []

# ====================================================== 00 外觀算圖
fig, bg = sheet(0, "外觀算圖（雙腳 / 單腳步態姿勢 / 膝關節特寫）", "算圖，非比例")
img_axes(fig, (14, 44, 140, 240), f"{SH}/pair.png", crop=(170, 120, 1330, 1720))
img_axes(fig, (150, 44, 110, 240), f"{SH}/pose.png", crop=(330, 80, 1050, 1440))
img_axes(fig, (262, 140, 145, 145), f"{SH}/knee.png")
bg.text(265, 132, "膝關節：AK60-6 V1.1  Ø79 × 39.5", fontsize=8.5, weight="bold")
bg.text(265, 124, "髖關節：AK70-10  Ø89 × 50.25", fontsize=8.5, weight="bold")
bg.text(265, 70, "\n".join([
    "與原版 ALICE 的差異",
    "• 馬達：改 CubeMars AK70-10（髖）、AK60-6（膝）",
    "• 連桿：2020 鋁擠 → 3D 列印 25×25 方管（中心 Ø11 走線孔）",
    "• 葫蘆形側板 + 紅色三爪轉接 保留原版造型",
    "• 每個關節：定子杯 + 內外側板（內側板走軸承）",
    "• 長度調整：每段 390–450，15 mm 一格（M6 × 2）",
]), fontsize=7.6, va="bottom", linespacing=1.6)
pages.append(fig)

# ====================================================== 01 組合二視圖
notes = ["註：1. 左腳；右腳為鏡射。視圖比例 1:5。", "2. 段長目前為 420 / 420；可調 390–450（每 15）。",
         f"3. 馬達外形依 CubeMars 官網；鎖孔 PCD 為示意值，請以實物 / 官方 STEP 確認後改 exo_ak.py 的 MOTORS。"]
fig, bg = sheet(1, "組合二視圖（側視 / 正視）", "比例 1:5", notes)
# 側視：螢幕右 = −X → h = −X
side = ortho_axes(fig, (20, 30, 150, 254), f"{SH}/ortho_side.png", h_of_u=lambda u: (u - W / 2) * S_MM)
front = ortho_axes(fig, (185, 30, 120, 254), f"{SH}/ortho_front.png", h_of_u=lambda u: -80 + (u - W / 2) * S_MM)
bg.text(95, 284, "側視圖（由外側看，左＝前）", ha="center", fontsize=9, weight="bold")
bg.text(245, 284, "正視圖（由前方看，右＝外側）", ha="center", fontsize=9, weight="bold")
hd = 150
dim_v(side, hd, 0, zK, f"髖軸→膝軸 {-zK:.0f}（390–450）", ext_from=10)
dim_v(side, hd, zK, zA, f"膝軸→踝軸 {zK - zA:.0f}（390–450）", ext_from=10)
dim_v(side, hd, zA, zs, f"{zA - zs:.0f}", ext_from=10)
for z, R, lab in ((0, mh["D"] / 2, f"{P['HIP_MOTOR']}  Ø{mh['D']:g}×{mh['H']:g}"),
                  (zK, mk["D"] / 2, f"{P['KNEE_MOTOR']}  Ø{mk['D']:g}×{mk['H']:g}")):
    side.add_patch(Circle((0, z), R, fill=False, ls="--", lw=0.6, color=RED))
    leader(side, (-R * 0.71, z + R * 0.71), (-165, z + 75), lab, color=RED)
leader(side, (0, -180), (-165, -140), "大腿連桿（列印 25×25）", fs=6.8)
leader(side, (0, -600), (-165, -560), "小腿連桿（列印 25×25）", fs=6.8)
leader(side, (-70, P["THIGH_CUFF_Z"]), (-165, P["THIGH_CUFF_Z"] - 40), "大腿綁帶護墊", fs=6.8)
leader(side, (-55, P["SHANK_CUFF_Z"]), (-165, P["SHANK_CUFF_Z"] - 40), "小腿綁帶護墊", fs=6.8)
leader(side, (85, 30), (150, 150), "電控盒（MCU / CAN）", fs=6.8)
leader(side, (0, zA), (-165, zA + 40), "被動踝 M8 軸", fs=6.8)
dim_h(side, -880 - 60, -143, 83, "腳板 226", ext_from=zs - 2, below=True)
# 正視：寬度
dim_h(front, 95, hip["yi0"] - 3, hip["yo1"], f"髖 {hip['yo1'] - hip['yi0'] + 3:.1f}", ext_from=60)
dim_h(front, zK + 165, kn["yi0"] - 3, kn["yo1"], f"膝 {kn['yo1'] - kn['yi0'] + 3:.1f}", ext_from=zK + 120)
dim_h(front, -270, -12.5, 12.5, "25", ext_from=-300)
dim_h(front, zK - 290, -74, 0, "74", ext_from=zK - 250, below=True)
front.text(-40, -380, "連桿中心面\ny = 0", fontsize=6.5, ha="right")
pages.append(fig)

# ====================================================== 02 關節爆炸圖
fig, bg = sheet(2, "關節爆炸圖與零件表", "算圖，非比例")
img_axes(fig, (12, 150, 200, 135), f"{SH}/hip_explode.png", crop=(150, 60, 1150, 900))
img_axes(fig, (210, 150, 200, 135), f"{SH}/knee_explode.png", crop=(150, 100, 1150, 900))
bg.text(20, 278, f"髖關節（{P['HIP_MOTOR']}）", fontsize=9.5, weight="bold")
bg.text(218, 278, f"膝關節（{P['KNEE_MOTOR']}）", fontsize=9.5, weight="bold")
rows = [("件號", "名稱", "數量/腳", "材料", "備註"),
        ("1", "定子杯（髖含腰背支架介面）", "2", "PA-CF / PETG-CF", "馬達底座 M3 鎖入；內側凸台裝軸承"),
        ("2", "內側板（葫蘆形）", "2", "PA-CF 6 mm", "軸承座；與下夾座 3×M3"),
        ("3", "外側板（葫蘆形）", "2", "PA-CF 6 mm", "三爪 3×M3 鎖入"),
        ("4", "三爪轉接（紅）", "2", "PA-CF / PETG", f"中心鎖馬達輸出盤（{mh['out_n']} / {mk['out_n']} × M3）"),
        ("5", "下夾座", "2", "PA-CF", "插槽深 66，M6 × 2"),
        ("6", f"軸承 {mh['bearing'][0]}×{mh['bearing'][1]}×{mh['bearing'][2]} / "
              f"{mk['bearing'][0]}×{mk['bearing'][1]}×{mk['bearing'][2]}", "各 1", "6810 / 6808 薄型", "內側板支撐，分擔彎矩"),
        ("7", "大腿 / 小腿連桿", "各 1", "PA-CF 或 PETG-CF", f"長 {D['thigh_len']:.0f} / {D['shank_len']:.1f}"),
        ("8", "綁帶夾座 + 護墊 + 紅背板", "2 組", "PETG / TPU 護墊", "可沿連桿滑動定位"),
        ("9", "踝上座 / 踝擺臂 / 腳板", "各 1", "PA-CF / PETG", "被動踝 M8"),
        ("10", "腰背支架 + 軟墊、電控盒", "各 1", "PETG", "示意"),
        ("—", "AK70-10、AK60-6", "各 1", "外購", "CAN 通訊"),
        ]
y = 140
for i, r in enumerate(rows):
    xs = [16, 30, 118, 140, 182]
    for xx, t in zip(xs, r):
        bg.text(xx, y, t, fontsize=7.3, weight="bold" if i == 0 else None, va="center")
    bg.plot([14, 245], [y - 4, y - 4], color="#999", lw=0.4)
    y -= 8.2
bg.text(255, 140, "\n".join([
    "列印建議",
    "• 連桿 / 夾座：PA-CF 或 PETG-CF，0.2 mm 層高",
    "  牆數 ≥ 5、上下 ≥ 6 層、填充 40% 螺旋 (gyroid)",
    "• 連桿『直立』或『平躺』列印：平躺時方管側面",
    "  朝下，纖維順著受彎方向，強度較好（建議平躺）",
    "• 側板平放列印；孔用熱熔螺母 M3",
    "• 三爪轉接與馬達輸出盤之間可墊 1 mm 鋁片",
    "",
    "強度提醒",
    "• AK70-10 峰值 ~25 N·m；列印方管 25×25 受彎",
    "  建議內塞 Ø10 碳纖管（走線孔 Ø11）加強",
    "• 上線前先空載測試，限位以軟體 + 機構雙重保護",
]), fontsize=7.3, va="top", linespacing=1.55)
pages.append(fig)

# ====================================================== 03 連桿零件圖（直接畫）
fig, bg = sheet(3, "3D 列印連桿零件圖（取代 2020 鋁擠）", "比例 1:2", [
    "註：1. 兩端孔距端面 9 / 24 / 39 / 54（Ø6.4，前後貫穿）。插槽 M6 × 2 距槽口 10 / 25。",
    "2. 兩端各可拉出 0 / 15 / 30 → 段長 390–450 共 5 段。中心 Ø11 走線孔全長貫穿。"])
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, A3[0]); ax.set_ylim(0, A3[1]); ax.axis("off")
holes = D["thigh_holes"][0]
for row, (name, Ln) in enumerate((("大腿連桿 T", D["thigh_len"]), ("小腿連桿 S", D["shank_len"]))):
    y0 = 225 - row * 85
    x0 = 30
    sc = 0.5
    ax.add_patch(Rectangle((x0, y0), Ln * sc, 25 * sc, fill=False, lw=1))
    ax.plot([x0, x0 + Ln * sc], [y0 + 12.5 * sc] * 2, color="k", lw=0.4, ls=(0, (8, 3, 2, 3)))
    for hpos in holes + [Ln - h for h in holes]:
        ax.add_patch(Circle((x0 + hpos * sc, y0 + 12.5 * sc), 3.2 * sc, fill=False, lw=0.7))
    ax.text(x0, y0 + 25 * sc + 20, f"{name}　長 {Ln:.1f}　×1 / 腳", fontsize=9, weight="bold")
    # 尺寸
    yd = y0 - 8
    ax.annotate("", (x0, yd), (x0 + Ln * sc, yd), arrowprops=dict(arrowstyle="<|-|>", lw=0.7, mutation_scale=7))
    ax.text(x0 + Ln * sc / 2, yd - 1.5, f"{Ln:.1f}", ha="center", va="top", fontsize=7.5)
    prev = 0
    for hpos in holes:
        ax.annotate("", (x0, y0 + 25 * sc + 3 + holes.index(hpos) * 0.0), (x0 + hpos * sc, y0 + 25 * sc + 3),
                    arrowprops=dict(arrowstyle="-", lw=0))
    for k, hpos in enumerate(holes):
        yy = y0 + 25 * sc + 2.5 + k * 3.0
        ax.annotate("", (x0, yy), (x0 + hpos * sc, yy), arrowprops=dict(arrowstyle="<|-|>", lw=0.5, mutation_scale=5))
        ax.text(x0 + hpos * sc + 1, yy, f"{hpos:.0f}", fontsize=5.5, va="center")
    ax.text(x0 + Ln * sc + 4, y0 + 6, "4 × Ø6.4 每端\n間距 15", fontsize=6.5, va="center")
# 斷面
cx, cy = 300, 215
sc2 = 2.0
ax.add_patch(Rectangle((cx - 12.5 * sc2, cy - 12.5 * sc2), 25 * sc2, 25 * sc2, fill=True, fc="#ddd", ec="k", lw=1, hatch="///"))
ax.add_patch(Circle((cx, cy), 5.5 * sc2, fc="white", ec="k", lw=0.8))
ax.text(cx, cy + 12.5 * sc2 + 6, "A–A 斷面（2:1）", ha="center", fontsize=8.5, weight="bold")
ax.annotate("", (cx - 25, cy - 31), (cx + 25, cy - 31), arrowprops=dict(arrowstyle="<|-|>", lw=0.6, mutation_scale=6))
ax.text(cx, cy - 33, "25（R2 圓角）", ha="center", va="top", fontsize=7)
ax.text(cx + 14, cy + 3, "Ø11 走線", fontsize=7)
# 長度調整表
rows = [("段長", "上端拉出", "下端拉出")] + [(f"{390 + 15 * i}", f"{15 * ((i + 1) // 2)}", f"{15 * i - 15 * ((i + 1) // 2)}")
                                             for i in range(5)]
ty = 150
ax.text(262, ty + 10, "長度調整表（大腿、小腿相同）", fontsize=8.5, weight="bold")
for i, r in enumerate(rows):
    for xx, t in zip((265, 300, 335), r):
        ax.text(xx, ty - i * 7, t, fontsize=7.5, weight="bold" if i == 0 else None)
    ax.plot([262, 365], [ty - i * 7 - 2.5] * 2, color="#aaa", lw=0.4)
pages.append(fig)

names = ["00_外觀算圖", "01_組合二視圖", "02_關節爆炸圖與零件表", "03_列印連桿零件圖"]
with PdfPages(os.path.join(OUT, "ALICE_AK_exo_Drawings.pdf")) as pdf:
    for f, n in zip(pages, names):
        f.axes[0].set_zorder(10); f.axes[0].patch.set_alpha(0)   # 圖框 / 標題欄永遠在最上層
        f.axes[0].add_patch(Rectangle((250, 10), 160, 30, fc="white", ec="none", zorder=-1))
        f.savefig(os.path.join(OUT, n + ".png"), dpi=170)
        pdf.savefig(f)
print("ok", OUT)
