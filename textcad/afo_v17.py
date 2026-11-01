"""
text-to-cad（cadgen）模型：AFO v17 外穿式布鞋雙點 FSR 足底力量平台
- 零件幾何由 cad/afo_v17.py 產生（python3 cad/afo_v17.py --export out）
- 本檔把 out/STEP 內的零件組成 cadgen 組合件，可在 text-to-cad CAD Viewer 檢視，並用
  `cadgen export <id> STEP/xxx.step GLB/xxx.glb 3MF/xxx.3mf` 輸出
執行： python textcad/afo_v17.py
"""
from pathlib import Path

import build123d as bd
from cadgen import model, read_step

HERE = Path(__file__).resolve().parent
import os
_V = os.environ.get("AFO_VARIANT", "shoe")
STEP = next(p for p in (HERE / "../STEP", HERE / f"../out/{_V}/STEP") if p.exists())   # 輸出包 / repo（out/<版本>/STEP）

PARTS = [
    ("F1_AFO_foot_v17", "#94a8cc"),        # 腳底件（赤腳版：一件）
    ("F1A_AFO_foot_rear", "#e8a070"),      # 腳底件後段（穿鞋版分件，x < 120 + 搭接）
    ("F1B_AFO_foot_front", "#94a8cc"),     # 腳底件前段（分件）
    ("T1_toe_stopper", "#f29e47"),         # 鞋頭擋塊
    ("B2_wire_cover", "#4d80d9"),          # 走線蓋板
    ("C0_cartridge_housing_1", "#99d18c"), # S1 感測匣殼（Ø42 凸環，高出底板 3）
    ("C1_TPU_guide_1", "#40baba"),
    ("C2_steel_ball_5mm_1", "#d9dbe0"),
    ("C3_FSR402_ref_1", "#2b2b2b"),
    ("C4_FSR_seat_1", "#99d18c"),
    ("C5_shield_disc_1", "#d9dbe0"),
    ("C0_cartridge_housing_2", "#99d18c"), # S2 感測匣殼
    ("C1_TPU_guide_2", "#40baba"),
    ("C2_steel_ball_5mm_2", "#d9dbe0"),
    ("C3_FSR402_ref_2", "#2b2b2b"),
    ("C4_FSR_seat_2", "#99d18c"),
    ("C5_shield_disc_2", "#d9dbe0"),
]


def part(name, color):
    s = read_step(STEP / f"{name}.step")
    s.label = name
    s.color = color
    return s


@model
def afo_v17_sensors():
    """只有感測匣與走線蓋板（較輕，方便檢視）"""
    return bd.Compound(children=[part(n, c) for n, c in PARTS if not n.startswith(("F1", "T1"))], label="afo_v17_sensors")


@model
def afo_v17():
    return bd.Compound(children=[part(n, c) for n, c in PARTS if (STEP / f"{n}.step").exists()], label="afo_v17")


if __name__ == "__main__":
    afo_v17_sensors()
    afo_v17()
