"""可調式感測座設計圖：FSR-14（配置與刻度）、FSR-15（剖面與爆炸）
用法： python3 make_adjust_drawings.py [輸出資料夾]
"""
import os, sys, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import afo_v17 as A
import adjust_mech as am
import drawing_lib as dl
from matplotlib.patches import Circle, Rectangle, Polygon as MPoly, FancyArrowPatch
from shapely.geometry import Polygon

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "drawings")
P = A.P; m = am.M
parts, D = A.build(P, verbose=False)
S1, S2 = D["S1"], D["S2"]
RANGE = {"S1": dict(o=S1, x=(-25, 25), y=(-8, 8)), "S2": dict(o=S2, x=(-15, 25), y=(-8, 0))}
C = dict(floor="#c9d1db", floor_ec="#5d6b7a", car="#a8d59b", ring="#7fd0cf", tpu="#3fa7a6", pin="#55606b",
         scale="#1a3f63", origin="#c0392b", range="#c0392b", trench="#8e9aa8")

# =================================================================== FSR-14
fig, bg = dl.new_sheet(14, "可調式感測座：配置與刻度（XY 燕尾滑座 + 榫銷定位）", "左 1:2、右 2:1 (A3)",
    ["機構：底板燕尾槽 ← X 滑座（前後）；滑座 Y 長槽 ← 感測匣導筒（左右），Ø42 凸環（高出底板 3 mm）壓在滑座上。",
     "鎖定：Ø3 榫銷穿過滑座插入台階上的卯孔列（間距 5，兩側錯開 2.5 → 每格 2.5 mm）；Y 向同理，榫銷穿過凸環插入滑座卯孔。",
     "刻度 0 點 = 使用者腳印量得位置：S1 大拇趾球 (%.1f, %+.0f)、S2 腳跟 (%.1f, %+.0f)。調整範圍：S1 X ±25 / Y ±8；S2 X −15～+25 / Y −8～0（+Y 受小腿件套筒限制）。" % (S1[0], S1[1], S2[0], S2[1]),
     "刻度刻在底板（X）與滑座頂面（Y）：小刻度 2.5、中刻度 5、大刻度 10 附數字；滑座側邊與凸環邊各有 ▲ 指標。"])
# ---- 左：整體配置
ax = dl.view_axes(fig, (14, 92, 190, 188), 2.0, center=(165, 0))
outer, inner = D["outer"], D["inner"]
ax.add_patch(MPoly(np.array(outer.exterior.coords), closed=True, fc="#e9edf2", ec=C["floor_ec"], lw=0.8))
ax.add_patch(MPoly(np.array(inner.exterior.coords), closed=True, fc=C["floor"], ec=C["floor_ec"], lw=0.6))
ax.add_patch(Rectangle((8.3, -33.2), 52, 66.4, fill=False, ec="#6c3483", ls=":", lw=0.8))
for nm, R in RANGE.items():
    o = R["o"]; x0 = o[0] + R["x"][0] - m["Car_L"] / 2; x1 = o[0] + R["x"][1] + m["Car_L"] / 2 + m["Cap_L"]
    ax.add_patch(Rectangle((x0, o[1] - m["Car_HalfW"]), x1 - x0, 2 * m["Car_HalfW"], fc="#dfe6ee", ec=C["floor_ec"], lw=0.6, ls="--"))
    ax.add_patch(Rectangle((o[0] - m["Car_L"] / 2, o[1] - m["Car_HalfW"]), m["Car_L"], 2 * m["Car_HalfW"], fc=C["car"], ec="k", lw=0.6))
    ax.add_patch(Rectangle((o[0] + R["x"][0], o[1] + R["y"][0]), R["x"][1] - R["x"][0], R["y"][1] - R["y"][0], fc=C["range"], alpha=0.18, ec=C["range"], lw=0.8))
    ax.add_patch(Circle(o, m["Ring_D"] / 2, fc=C["ring"], ec="k", lw=0.6)); ax.add_patch(Circle(o, 10.5, fc=C["tpu"], ec="k", lw=0.5))
    ax.plot(*o, "+", color=C["origin"], ms=10, mew=1.2)
    ax.text(o[0] + (25 if nm == "S2" else 0), o[1] + (m["Car_HalfW"] + 22 if nm == "S2" else -m["Car_HalfW"] - 14), f"{nm} 0 點 ({o[0]:.1f}, {o[1]:+.0f})\nX {R['x'][0]:+d}～{R['x'][1]:+d}　Y {R['y'][0]:+d}～{R['y'][1]:+d}",
            ha="center", fontsize=7, color=C["origin"])
dl.centerline(ax, (-5, 0), (350, 0))
ax.text(10, -44, "紫點線 = 小腿件套筒內側", fontsize=6.5, color="#6c3483")
ax.set_title("整體配置（俯視）　紅框 = 可調範圍、虛線框 = 燕尾槽", fontsize=9)

# ---- 右：S1 細部 2:1
o = np.array([0.0, 0.0])
axd = dl.view_axes(fig, (210, 60, 196, 220), 0.5, center=(0, -3))
R = RANGE["S1"]
x0 = R["x"][0] - m["Car_L"] / 2; x1 = R["x"][1] + m["Car_L"] / 2
hw = m["Car_HalfW"]
axd.add_patch(Rectangle((-48, -45), 96, 90, fc=C["floor"], ec="none"))
axd.add_patch(Rectangle((-48, -hw - 0.2), 96, 2 * hw + 0.4, fc="#b7c1cc", ec=C["floor_ec"], lw=0.6, ls="--"))
axd.add_patch(Rectangle((-m["Car_L"] / 2, -hw), m["Car_L"], 2 * hw, fc=C["car"], ec="k", lw=0.8))
sl = m["Slot_W"] / 2; sy = m["Tube_OD"] / 2 + m["Y_Range"] + 0.5
axd.add_patch(Rectangle((-sl, -sy), 2 * sl, 2 * sy, fc="#5f8f55", ec="k", lw=0.6, alpha=0.55))
# X 卯孔（台階上，被滑座蓋住處以虛線）
for k in range(-6, 7):
    for y, x in ((m["Ledge_Y"], k * 5.0), (-m["Ledge_Y"], k * 5.0 + 2.5)):
        if R["x"][0] - 0.01 <= x <= R["x"][1] + 0.01:
            under = abs(x) < m["Car_L"] / 2
            axd.add_patch(Circle((x, y), 1.6, fill=not under, fc="#555", ec="#333", lw=0.5, ls="--" if under else "-"))
# 滑座上的 X 榫銷（插入 +Y 側 x=0 卯孔）
axd.add_patch(Circle((0, m["Ledge_Y"]), 2.5, fc=C["pin"], ec="k", lw=0.6)); axd.add_patch(Circle((0, -m["Ledge_Y"]), 1.6, fc="white", ec="k", lw=0.5))
# Y 卯孔（滑座頂面）
for k in range(-2, 3):
    for x, y in ((m["YPin_X"], k * 5.0), (-m["YPin_X"], k * 5.0 + 2.5)):
        if abs(y) <= 8.01:
            axd.add_patch(Circle((x, y), 1.6, fc="#3d5c36", ec="k", lw=0.4))
# 凸環 + TPU
axd.add_patch(Circle((0, 0), m["Ring_D"] / 2, fc=C["ring"], ec="k", lw=0.9, alpha=0.92))
axd.add_patch(Circle((0, 0), m["Ring_D"] / 2 - 1, fill=False, ec="k", lw=0.4))
axd.add_patch(Circle((0, 0), 10.5, fc=C["tpu"], ec="k", lw=0.6))
axd.add_patch(Circle((m["YPin_X"], 0), 2.5, fc=C["pin"], ec="k", lw=0.6)); axd.add_patch(Circle((-m["YPin_X"], 0), 1.6, fc="white", ec="k", lw=0.5))
axd.add_patch(MPoly([(21.5, 0), (18, -1.5), (18, 1.5)], closed=True, fc=C["origin"], ec="none"))
axd.plot(0, 0, "+", color=C["origin"], ms=14, mew=1.2)
# X 刻度（底板，滑座 +Y 外側）
yb = hw + 1.5
for i in range(int(R["x"][0] / 2.5), int(R["x"][1] / 2.5) + 1):
    x = i * 2.5; L = 5 if i % 4 == 0 else (3.5 if i % 2 == 0 else 2)
    axd.plot([x, x], [yb, yb + L], color=C["scale"], lw=0.9 if i % 4 == 0 else 0.6)
    if i % 4 == 0:
        axd.text(x, yb + 7.5, f"{int(x):+d}" if x else "0", ha="center", fontsize=7, color=C["scale"], weight="bold")
axd.add_patch(MPoly([(0, hw + 0.2), (-1.6, hw - 2.6), (1.6, hw - 2.6)], closed=True, fc=C["origin"], ec="none"))
axd.text(R["x"][1] + 4, yb + 2, "X (mm)\n→ 腳尖", fontsize=6.5, color=C["scale"], va="center")
# Y 刻度（滑座頂面 +X 端）
xb = 21.8
for i in range(-3, 4):
    y = i * 2.5; L = 2.6 if i % 2 == 0 else 1.6
    axd.plot([xb, xb + L], [y, y], color=C["scale"], lw=0.7)
    if i % 2 == 0:
        axd.text(xb + 3.2, y, f"{int(y):+d}" if y else "0", va="center", fontsize=6, color=C["scale"])
axd.text(23, 10.5, "Y", fontsize=6.5, color=C["scale"])
dl.hdim(axd, -m["Car_L"] / 2, m["Car_L"] / 2, -hw, -hw - 6, "50", fs=6.5)
dl.vdim(axd, -hw, hw, -m["Car_L"] / 2, -m["Car_L"] / 2 - 6, "58", fs=6.5)
dl.hdim(axd, -sl, sl, -sy, -hw - 13, "28 長槽", fs=6.5)
dl.vdim(axd, -sy, sy, -sl, -sl - 3.5, "43", fs=6)
dl.hdim(axd, -21, 21, 21, 40, "Ø42 凸環（高 3）", fs=6.5)
dl.leader(axd, (0, m["Ledge_Y"]), (-46, 38), "X 榫銷 Ø3（插入台階卯孔）", fs=6.5)
dl.leader(axd, (m["YPin_X"], 0), (30, -38), "Y 榫銷 Ø3", fs=6.5, ha="left")
dl.leader(axd, (-12.5, -m["Ledge_Y"]), (-46, -40), "卯孔列 間距 5（兩側錯開 2.5）", fs=6.5)
dl.leader(axd, (-m["YPin_X"], 2.5), (-46, 14), "滑座 Y 卯孔", fs=6.5)
dl.leader(axd, (8, 6), (30, 20), "TPU 傳力面 Ø21", fs=6.5, ha="left")
axd.set_title("S1 細部（俯視 2:1）　狀態：X = 0、Y = 0", fontsize=9)
fig.savefig(os.path.join(OUT, "14_可調式感測座_配置與刻度.png"), dpi=170)
print("14 done")

# =================================================================== FSR-15
fb, (fx0, fx1) = am.floor_block(xr=RANGE["S1"]["x"])
car = am.carriage(); ring, tpu = am.ring_cartridge()
pins = [am.pin(x=0, y=m["Ledge_Y"]), am.pin(x=m["YPin_X"], y=0, ztop=m["Floor"] + m["Ring_T"])]
cap = am.end_cap(x_start=fx1 - m["Cap_L"])
MESH = {k: A.as_mesh(v) for k, v in dict(floor=fb, car=car, ring=ring, tpu=tpu, pin1=pins[0], pin2=pins[1], cap=cap).items()}
COL = dict(floor=(0.78, 0.81, 0.86), car=(0.62, 0.82, 0.55), ring=(0.45, 0.80, 0.80), tpu=(0.25, 0.65, 0.66), pin1=(0.35, 0.37, 0.40), pin2=(0.35, 0.37, 0.40), cap=(0.95, 0.65, 0.35))
SEC = dict(floor=("#c3cad3", "///"), car=("#b5dca8", "\\\\\\"), ring=("#9fdede", "///"), tpu=("#5fb9b8", "xx"), pin1=("#55606b", None), pin2=("#55606b", None), cap=("#f2c08d", "///"))

fig, bg = dl.new_sheet(15, "可調式感測座：剖面與爆炸圖", "剖面 2:1、爆炸圖不依比例 (A3)",
    ["燕尾角 60°：滑座只能沿 X 滑動、不能上浮；前端燕尾端塞（橘）在裝入滑座後塞入，兼作行程止擋。",
     "受力：鞋底 → TPU → 鋼珠 → FSR → 支撐座 → 深槽底板（z = 3），與滑座位置無關；凸環與滑座只承受定位，不在 FSR 受力路徑上。",
     "調整步驟：拔 X 榫銷 → 推滑座對準底板刻度 → 插銷；拔 Y 榫銷 → 推凸環對準滑座刻度 → 插銷。FSR 線在深槽內預留 60 mm 迴線。"])
# A-A：YZ（x = 0）
for k, (nm, origin, normal, xdir, xl, ttl) in enumerate((
        ("A", (0, 0, 0), (-1, 0, 0), (0, -1, 0), (-48, 48), "A-A 剖面（X = 0，看向腳跟）：燕尾、台階、X 榫銷"),
        ("B", (0, 0, 0), (0, -1, 0), (1, 0, 0), (-48, 48), "B-B 剖面（Y = 0）：深槽、凸環、Y 榫銷"))):
    axs = dl.view_axes(fig, (16 + k * 196, 196, 190, 84), 0.5)
    for key in ("floor", "car", "ring", "tpu", "pin1", "pin2"):
        g = dl.section_polys(MESH[key], origin, normal, xdir)
        fc, ht = SEC[key]; dl.draw_polys(axs, g, fc, ht, zorder=5 if key.startswith("pin") else 3)
    axs.set_xlim(*xl); axs.set_ylim(-6, 84 * 0.5 - 6)
    axs.set_title(ttl, fontsize=8.5)
    if nm == "A":
        dl.vdim(axs, 11, 15, 33, 37, "4", fs=6); dl.vdim(axs, 15, 18, -23, -27, "凸環 3", fs=6)
        dl.vdim(axs, 3, 11, -30, -40, "深槽 8", fs=6); dl.hdim(axs, -22.5, 22.5, 3, -1.5, "深槽 45", fs=6)
        dl.leader(axs, (-29.5, 13), (-46, 27), "燕尾 60°", fs=6.5)
        dl.leader(axs, (-25.5, 9), (-46, 22), "X 榫銷 → 卯孔", fs=6.5)
    else:
        dl.vdim(axs, 15, 18.3, 26, 31, "3.3", fs=6); dl.hdim(axs, -14, 14, 11, 7, "長槽 28", fs=6)
        dl.leader(axs, (17, 13), (30, 28), "Y 榫銷", fs=6.5, ha="left")
        dl.leader(axs, (0, 12), (-40, 30), "TPU / 鋼珠 / FSR（同 FSR-09）", fs=6.5)
# 爆炸圖
axe = fig.add_axes([0.02, 0.16, 0.6, 0.48]); axe.set_aspect("equal"); axe.axis("off")
EX = dict(floor=(0, 0, 0), car=(0, 0, 28), ring=(0, 0, 55), tpu=(0, 0, 78), pin1=(0, 0, 44), pin2=(0, 0, 92), cap=(38, 0, 0))
items = [(MESH[k].copy().apply_translation(EX[k]), COL[k], 1.0) for k in MESH]
d, up = (-0.75, 0.95, -0.7), (0, 0, 1)
lo, hi = dl.render(axe, items, d, up, lw=0.35)
axe.set_xlim(lo[0] - 60, hi[0] + 60); axe.set_ylim(lo[1] - 5, hi[1] + 5)
labels = dict(floor="腳底件底板（燕尾槽 + 卯孔列 + 深槽）", car="X 滑座（Y 長槽 + Y 卯孔 + Y 刻度）", ring="感測匣（Ø42 凸環 + 導筒）",
              tpu="TPU 傳力柱", pin1="X 榫銷 Ø3", pin2="Y 榫銷 Ø3", cap="燕尾端塞（止擋）")
cen = (lo + hi) / 2
for k, txt in labels.items():
    b = MESH[k].bounds; c = (b[0] + b[1]) / 2 + np.array(EX[k]); c[2] = b[1][2] + EX[k][2]
    p = dl.proj(c, d, up)[0][0]
    v = p - cen; v = v / (np.linalg.norm(v) + 1e-9)
    dl.leader(axe, p, p + v * np.array([70, 25]), txt, fs=7, ha="left" if v[0] > 0 else "right")
# 右下：刻度/榫銷說明
axn = fig.add_axes([0.63, 0.30, 0.33, 0.33]); axn.axis("off")
rows = [("項目", "S1 大拇趾球", "S2 腳跟"), ("0 點 (X, Y)", f"{S1[0]:.1f}, {S1[1]:+.0f}", f"{S2[0]:.1f}, {S2[1]:+.0f}"),
        ("X 範圍", "−25 ～ +25", "−15 ～ +25"), ("Y 範圍", "−8 ～ +8", "−8 ～ 0"), ("每格", "2.5 mm", "2.5 mm"),
        ("滑座", "50 × 58 × 4", "50 × 58 × 4"), ("凸環", "Ø42 × 3（高出底板）", "同左"), ("榫銷", "Ø3 × 9，頭 Ø5×1 ×2", "同左")]
t = axn.table(cellText=rows[1:], colLabels=rows[0], loc="upper center", cellLoc="left", colWidths=[0.28, 0.36, 0.36])
t.auto_set_font_size(False); t.set_fontsize(8); t.scale(1, 1.6)
fig.savefig(os.path.join(OUT, "15_可調式感測座_剖面與爆炸.png"), dpi=170)
print("15 done")
