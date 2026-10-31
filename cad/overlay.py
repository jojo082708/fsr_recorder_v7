"""腳印 × 鞋型 × 托盤 重合俯視圖 → drawings/13_腳印鞋型重合俯視圖.png
用法： FOOTPRINT_IMG=腳印照片.jpg python3 overlay.py [輸出資料夾]
"""
import os, sys
import numpy as np
from PIL import Image
from shapely.geometry import box as sbox
from matplotlib.patches import Circle
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import afo_v17 as A
import drawing_lib as dl

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "drawings")
P = A.P
parts, D = A.build(P, verbose=False)
ZT = D["ZT"]; S1, S2 = D["S1"], D["S2"]
X0 = P["Sleeve_Inner_X"] + P["Heel_Offset"]          # 腳跟後緣在托盤上的 X
foot = A.as_mesh(parts["F1_AFO腳底件_v17"][0])
toe = A.as_mesh([w for k, (w, m) in parts.items() if k.startswith("T1")][0])
cart = [A.as_mesh(w) for k, (w, m) in parts.items() if k.startswith(("C0", "C1"))]
cover = A.as_mesh(parts["B2_走線蓋板"][0])

# 鞋型（鞋底 310 × 110）
inner = D["inner"]
shoe = inner.buffer(-4, join_style=1).intersection(sbox(P["Sleeve_Inner_X"], -200, P["Sleeve_Inner_X"] + P["Shoe_Length"], 200))
shoe = shoe.buffer(6, join_style=1).buffer(-6, join_style=1)

fig, bg = dl.new_sheet(13, "腳印 × 鞋型 × 托盤 重合俯視圖", "比例 1:1.25 (A3)",
                       [f"紅色 = 使用者腳印照片（左腳，依比例 6.25 px/mm 置入）；腳跟後緣放在 X = 套筒內面 8.3 + Heel_Offset* {P['Heel_Offset']:.0f} = {X0:.1f}。",
                        f"橘色虛線 = 布鞋鞋底 {P['Shoe_Length']:.0f} × {P['Shoe_Max_Width']:.0f}（量測值，鞋跟段受小腿件套筒內寬 66.4 限制）；藍灰 = AFO 腳底件 v17 托盤。",
                        "S1 / S2 = 鋼珠式 FSR 感測匣中心（Ø21 TPU 傳力面，Ø42 嵌板）。帶 * 者待確認。"])
ax = dl.view_axes(fig, (16, 50, 388, 232), 1.25)
lo, hi = dl.render(ax, [(foot, (0.70, 0.76, 0.86), 1.0), (toe, (0.95, 0.70, 0.45), 1.0), (cover, (0.55, 0.68, 0.9), 1.0)]
                   + [(m, (0.62, 0.84, 0.58), 1.0) for m in cart], (0, 0, -1), (0, 1, 0), lw=0.3)
dl.set_center(ax, ((lo + hi) / 2) + np.array([0, -4]))

img = os.environ.get("FOOTPRINT_IMG")
if img and os.path.exists(img):
    im = np.asarray(Image.open(img).convert("RGB")).astype(int)
    red = (im[..., 0] - im[..., 1] > 40) & (im[..., 0] - im[..., 2] > 30)
    H, W = red.shape
    sx, sy = 589 / 94.0, 1551 / 249.0
    rgba = np.zeros((H, W, 4)); rgba[red] = (0.86, 0.16, 0.16, 0.62)
    arr = rgba.transpose(1, 0, 2)[:, ::-1]                   # 列 → X（向右）、行 → Y（向上）
    ext = (X0 + (1642 - H) / sy, X0 + 1642 / sy, 47 - (W - 102) / sx, 47 + 102 / sx)
    ax.imshow(arr, extent=ext, origin="upper", zorder=6, interpolation="bilinear")
raw = np.loadtxt(os.path.join(HERE, "data", "footprint_outline_mm.csv"), delimiter=",")
ax.plot(raw[:, 0] + X0, raw[:, 1], color="#8b1a1a", lw=0.6, zorder=7)
sc = np.array(shoe.exterior.coords)
ax.plot(sc[:, 0], sc[:, 1], color="#e67e22", lw=1.4, ls="--", zorder=8)
sl = np.array([(8.3, -33.2), (60, -33.2), (60, 33.2), (8.3, 33.2), (8.3, -33.2)])
ax.plot(sl[:, 0], sl[:, 1], color="#6c3483", lw=0.9, ls=":", zorder=8)
for S, nm in ((S1, "S1 大拇趾球"), (S2, "S2 腳跟")):
    ax.add_patch(Circle(S, P["Guide_Neck_D"] / 2, fill=False, ec="#0b3d6b", lw=1.2, zorder=9))
    ax.plot(*S, "+", color="#0b3d6b", ms=12, mew=1.2, zorder=9)
    ax.text(S[0] + 3, S[1] + (27 if nm.startswith("S2") else -31), f"{nm}\n({S[0]:.1f}, {S[1]:+.0f})*", fontsize=8.5, color="#0b3d6b", zorder=11,
            ha="center", bbox=dict(fc="white", ec="none", alpha=0.85, pad=1))
dl.centerline(ax, (lo[0] - 8, 0), (hi[0] + 8, 0))
ax.plot(0, 0, "k+", ms=9); ax.text(-6, -7, "O", fontsize=8)
yb = foot.bounds[0][1]
dl.hdim(ax, 0, X0, yb, yb - 8, f"{X0:.1f}*", fs=7)
dl.hdim(ax, X0, X0 + P["Foot_Length"], yb, yb - 16, f"腳長 {P['Foot_Length']:.0f}", fs=7)
dl.hdim(ax, P["Sleeve_Inner_X"], P["Sleeve_Inner_X"] + P["Shoe_Length"], yb, yb - 24, f"鞋底長 {P['Shoe_Length']:.0f}", fs=7)
dl.hdim(ax, foot.bounds[0][0], foot.bounds[1][0], yb, yb - 32, f"腳底件 {foot.bounds[1][0] - foot.bounds[0][0]:.0f}", fs=7)
xr = foot.bounds[1][0]
dl.vdim(ax, -P["Shoe_Max_Width"] / 2, P["Shoe_Max_Width"] / 2, 300, xr + 8, f"鞋寬 {P['Shoe_Max_Width']:.0f}", fs=7)
dl.vdim(ax, foot.bounds[0][1], foot.bounds[1][1], xr, xr + 18, f"{foot.bounds[1][1] - foot.bounds[0][1]:.0f}", fs=7)
dl.vdim(ax, -33.2, 33.2, 8.3, -12, "套筒內寬 66.4", fs=6.5)
ax.text(hi[0], foot.bounds[1][1] + 4, "外側 (+Y)", ha="right", fontsize=7.5)
ax.text(hi[0], foot.bounds[0][1] - 40, "內側 (−Y)", ha="right", fontsize=7.5)
ax.legend(handles=[Line2D([], [], color="#d62728", lw=6, alpha=0.6, label="腳印（照片）"),
                   Line2D([], [], color="#e67e22", ls="--", lw=1.4, label="布鞋鞋底 310 × 110"),
                   Line2D([], [], color="#6c3483", ls=":", label="小腿件套筒內側"),
                   Line2D([], [], color="#0b3d6b", marker="o", ls="", mfc="none", label="FSR 感測位置")],
          loc="upper left", fontsize=7.5, frameon=False)
path = os.path.join(OUT, "13_腳印鞋型重合俯視圖.png")
fig.savefig(path, dpi=170)
print(path)
