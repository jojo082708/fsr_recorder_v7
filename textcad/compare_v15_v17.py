"""
text-to-cad（cadgen）前後對照模型：AFO v15（修改前） vs AFO v17（修改後）
輸入：textcad/inputs/v15/*.stp（v15 原檔）、textcad/inputs/v17/*.step（python3 cad/afo_v17.py --export out 產生）
執行：python textcad/compare_v15_v17.py
模型：
  compare_side_by_side  — 左 v15、右 v17 並排（含小腿件、鞋頭擋塊、感測匣）
  compare_overlay       — 兩版腳底件疊在同一位置（v15 紅、v17 藍），看外形放大與後跟杯不動
"""
from pathlib import Path

import build123d as bd
from cadgen import model, read_step

HERE = Path(__file__).resolve().parent
V15 = HERE / "inputs/v15"
V17 = HERE / "inputs/v17"
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
GAP = 110.0          # 兩版之間的 Y 間距（v15 在 +Y，v17 在 −Y）

V17_PARTS = [
    ("F1_AFO_foot_v17", "#7f9cd6"), ("T1_toe_stopper", "#f29e47"), ("B2_wire_cover", "#3b6fd1"),
    ("C0_cartridge_housing_1", "#5cc25a"), ("C1_TPU_guide_1", "#2fb3b3"), ("C2_steel_ball_5mm_1", "#d9dbe0"),
    ("C3_FSR402_ref_1", "#2b2b2b"), ("C4_FSR_seat_1", "#5cc25a"), ("C5_shield_disc_1", "#d9dbe0"),
    ("C0_cartridge_housing_2", "#5cc25a"), ("C1_TPU_guide_2", "#2fb3b3"), ("C2_steel_ball_5mm_2", "#d9dbe0"),
    ("C3_FSR402_ref_2", "#2b2b2b"), ("C4_FSR_seat_2", "#5cc25a"), ("C5_shield_disc_2", "#d9dbe0"),
]


def load(path, label, color):
    s = read_step(path)
    s.label = label
    s.color = color
    return s


def tag(text, x, y, z=0.0, size=14.0, color="#222222", label=None):
    t = bd.Text(text, font_size=size, font_path=FONT, align=(bd.Align.MIN, bd.Align.CENTER))
    t = bd.extrude(t, 1.5)
    t = bd.Pos(x, y, z) * t
    t.label = label or text
    t.color = color
    return t


def v15_group():
    return [
        load(V15 / "AFO_foot.stp", "v15_腳底件（修改前）", "#d98c8c"),
        load(V15 / "AFO_leg.stp", "v15_小腿件", "#cfae84"),
        load(V15 / "toe_stopper_H22_T9.stp", "v15_鞋頭擋塊_H22_T9", "#e7b37a"),
    ]


def v17_group():
    parts = [load(V17 / f"{n}.step", "v17_" + n, c) for n, c in V17_PARTS]
    parts.append(load(V15 / "AFO_leg.stp", "v17_小腿件（沿用 v15，不改）", "#cfae84"))
    return parts


@model
def compare_side_by_side():
    a = [bd.Pos(0, GAP, 0) * s for s in v15_group()]
    b = [bd.Pos(0, -GAP, 0) * s for s in v17_group()]
    labels = [
        tag("v15 修改前：288×118，舊 FSR 溝槽", 0, GAP + 75, 0, 12, "#9b2c2c", "標籤_v15"),
        tag("v17 修改後：346×134，鋼珠 FSR ×2，凸環 3 mm", 0, -GAP - 80, 0, 12, "#1f4f99", "標籤_v17"),
    ]
    return bd.Compound(children=a + b + labels, label="AFO v15 vs v17")


@model
def compare_overlay():
    f15 = load(V15 / "AFO_foot.stp", "v15_腳底件（紅）", "#e05252")
    f17 = load(V17 / "F1_AFO_foot_v17.step", "v17_腳底件（藍）", "#4a78d0")
    cart = [load(V17 / f"{n}.step", "v17_" + n, c) for n, c in V17_PARTS if n.startswith(("C0", "C1"))]
    labels = [tag("紅 = v15　藍 = v17（x < 80 後跟杯相同）", 0, 85, 0, 11, "#333333", "標籤")]
    return bd.Compound(children=[f15, f17] + cart + labels, label="AFO v15 / v17 疊合")


if __name__ == "__main__":
    compare_side_by_side()
    compare_overlay()
