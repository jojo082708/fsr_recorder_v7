"""
AFO v17 — 外穿式布鞋 FSR 雙點足底力量量測平台
=================================================
以 AFO v15 為基礎修改：
  * 小腿件 AFO_leg（已列印、上面放麵包板）完全不改。
  * 腳底件外形維持 v15 的 AFO 托盤造型（不是腳印形狀）。
  * 刪除 v15 舊 FSR 構造（x≈100 橫向貫穿槽、中央 T 溝、兩條長方凹槽），填平回 z=15 底板面。
  * 在第一蹠骨頭 (S1) 與腳跟 (S2) 各挖一個鋼珠式 FSR 感測匣口袋，感測匣頂面與底板面齊平。
  * 走線槽 → 後跟杯背面出線孔 → 往上接到小腿件背面的麵包板。走線槽上蓋平齊蓋板。
  * 刪除 v16 的外掛電控盒、腳印形平台、側限位等。

座標（沿用 v15）：原點 = 腳底件後緣底面中線，+X 朝腳尖、+Y 朝左、+Z 朝上，單位 mm。

用法：
  python3 afo_v17.py                # 建模並列出零件
  python3 afo_v17.py --export OUT   # 輸出 STL + STEP
"""
import os, sys, math
import numpy as np
import trimesh
import manifold3d as m3
import cadquery as cq
from shapely.geometry import Polygon, Point, LineString, box as sbox
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
V15 = os.path.join(HERE, "data", "v15")

# ------------------------------------------------------------------ 參數
P = dict(
    Side="L",
    # 足型（腳印量測）
    Foot_Length=249.0, Foot_Max_Width=94.0,
    Foot_S1=(177.0, 72.0),        # 距腳跟後緣、距外側邊
    Foot_S2=(25.0, 35.0),         # 距腳跟 25（圖上標 21）→ 待確認
    # v15 介面（由 v15 模型量得，不要改）
    Floor_Top=15.0,               # 托盤底板面
    Sleeve_Inner_X=8.3,           # 小腿件套筒後牆內面（布鞋鞋跟頂到這裡）
    Sleeve_Inner_HalfW=33.2,      # 小腿件套筒內側半寬（腳跟感測匣必須在此範圍內）
    # 布鞋（使用者量測：鞋底長 31 cm、鞋底寬 11 cm，左腳）
    Shoe_Length=310.0, Shoe_Max_Width=110.0, Shoe_Clear=2.0,
    Warp_X0=140.0,                # 此 x 以後依尺寸拉長/加寬（在分件接合處之後）→ 後段（含後跟杯、小腿件介面）所有尺寸共用
    Warp_Blend=50.0,
    Heel_Offset=12.0,             # 待確認：腳跟後緣 → 鞋底後緣
    # 感測匣
    Base_Floor=3.0, Insert_T=4.0, Insert_D=42.0, Screw_PCD=37.0,
    Ecc_Max=0.0, Sensor_Ecc=0.0,   # 固定位置：不做偏心 / 滑動調整
    Tube_OD=27.0, Tube_ID=22.4, Guide_D=22.0, Guide_Neck_D=21.0, Lip_ID=21.4, Ledge_ID=12.0,
    Ball_D=5.0, Bore_D=5.15, Ball_Lip_ID=4.5,
    Stop_Gap=1.0, Pad_Proud=0.3,
    Ring_Raise=3.0,               # 感測匣外圈凸環高出底板（固定位置，不可移動）
    Seat_D=22.0, Seat_T=1.5,
    FSR_D=18.3, FSR_Active_D=12.7, FSR_T=0.45, FSR_Tail_W=7.6,
    Shield_D=10.0, Shield_T=0.5,
    # 走線
    Wire_W=6.0, Wire_Bottom=10.0, Cover_W=9.0, Cover_T=1.5, Exit_D=5.0,
    Toe_Stopper="H22_T9",
    Toe_Clear=3.0, Toe_Shell=12.0, Toe_H=22.0, Toe_Region=0.80, Toe_Peg_D=6.0,   # 客製擋塊：腳趾間隙、殼厚、高度、起始位置（腳長比例）
    # 分件（印表機 300 × 300 × 350）：x = Split_X 處搭接，M4 平頭螺絲由底面鎖入後段的熱熔螺母
    Split_X=120.0, Lap_L=30.0, Lap_Z=7.0, Split_Gap=0.15,
    Split_Screw_Y=(-42.0, -2.0, 38.0), Split_Screw_DX=(-7.5, 7.5),
)


# ------------------------------------------------------------------ 模組化：共用後段 + 可換前段
# 腳跟位置兩版相同（套筒內面 8.3 + 12）：穿鞋時是鞋跟杯厚，赤腳時插入 12 mm 腳跟墊塊 → 兩組感測器位置相同，後段共用。
# 前段依「托盤內長 Tray_L（套筒內面 → 前緣，不含間隙）× 寬」產生，可換。
VARIANTS = {
    "shoe": dict(Variant_Name="穿鞋前段", Shoe_Length=310.0, Shoe_Max_Width=110.0, Heel_Offset=12.0, Split=True,
                 Toe_Stopper="H22_T9", Heel_Spacer=False),
    "barefoot": dict(Variant_Name="赤腳前段", Shoe_Length=12.0 + 254.0, Shoe_Max_Width=100.0, Heel_Offset=12.0, Split=True,
                     Toe_Stopper="custom", Heel_Spacer=True, Foot_Scale=(254.0, 100.0)),
}
def custom_variant():
    """AFO_LEN / AFO_WID（mm）+ AFO_MODE=shoe|barefoot → 任意尺寸前段。赤腳時 AFO_LEN 為腳長（自動加 12 mm 腳跟墊塊）。"""
    L = float(os.environ.get("AFO_LEN", "300")); W = float(os.environ.get("AFO_WID", "105"))
    mode = os.environ.get("AFO_MODE", "shoe")
    if mode == "barefoot":
        return dict(Variant_Name=f"赤腳前段 {L:.0f}×{W:.0f}", Shoe_Length=12.0 + L, Shoe_Max_Width=W, Heel_Offset=12.0, Split=True,
                    Toe_Stopper="custom", Heel_Spacer=True, Foot_Scale=(L, W))
    return dict(Variant_Name=f"穿鞋前段 {L:.0f}×{W:.0f}", Shoe_Length=L, Shoe_Max_Width=W, Heel_Offset=12.0, Split=True,
                Toe_Stopper="H22_T9", Heel_Spacer=False)
VARIANT = os.environ.get("AFO_VARIANT", "shoe")
P.update(VARIANTS[VARIANT] if VARIANT in VARIANTS else custom_variant())
P.update(Heel_Spacer_T=12.0, Heel_Spacer_H=40.0, Heel_Spacer_Peg_D=5.0)


def derived(p):
    s = 1 if p["Side"] == "L" else -1
    fw = p["Foot_Max_Width"]
    x0 = p["Sleeve_Inner_X"] + p["Heel_Offset"]
    d = dict(S1=(round(x0 + p["Foot_S1"][0], 1), s * (fw / 2 - p["Foot_S1"][1])),
             S2=(round(x0 + p["Foot_S2"][0], 1), s * (fw / 2 - p["Foot_S2"][1])))
    ZT = p["Floor_Top"]
    zf = p["Base_Floor"]
    d["ZT"] = ZT; d["ZB"] = ZT - p["Insert_T"]
    d["ZR"] = ZT + p["Ring_Raise"]          # 凸環頂面
    d["z_seat_top"] = zf + p["Seat_T"]
    d["z_fsr_top"] = d["z_seat_top"] - 0.3 + p["FSR_T"]
    d["z_sh_top"] = d["z_fsr_top"] + p["Shield_T"]
    d["zc_ball"] = d["z_sh_top"] + p["Ball_D"] / 2
    d["z_ceiling"] = d["zc_ball"] + p["Ball_D"] / 2
    d["z_ledge"] = (6.2, 7.4)
    d["z_skirt0"] = d["z_ledge"][1] + p["Stop_Gap"]
    d["z_boss0"] = d["z_sh_top"] + p["Stop_Gap"] + 0.4
    d["z_lip0"] = d["ZR"] - 0.8
    d["z_shoulder"] = d["z_lip0"] - 0.5
    d["z_pad"] = d["ZR"] + p["Pad_Proud"]
    d["pocket_D"] = p["Tube_OD"] + 2 * p["Ecc_Max"] + 1.0
    return d


# ------------------------------------------------------------------ mesh ⇄ manifold
def to_manifold(mesh):
    return m3.Manifold(m3.Mesh(vert_properties=np.asarray(mesh.vertices, np.float32),
                               tri_verts=np.asarray(mesh.faces, np.uint32)))

def to_trimesh(man):
    mm = man.to_mesh()
    return trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3], np.asarray(mm.tri_verts), process=False)

# 輸出精度：弧線每段最多轉 5°，弦高偏差 ≤ 0.02 mm（所有圓、孔、圓角同一精度）
LIN_TOL = 0.02
ANG_TOL = math.radians(5.0)
import shapely.geometry.base as _sgb
_orig_buffer = _sgb.BaseGeometry.buffer
def _buffer_hi(self, distance, quad_segs=18, **kw):     # shapely 圓角：每 1/4 圓 18 段 = 5°
    kw.pop("resolution", None)
    return _orig_buffer(self, distance, quad_segs=quad_segs, **kw)
_sgb.BaseGeometry.buffer = _buffer_hi


def cq_to_manifold(w, tol=LIN_TOL):
    s = w.val() if isinstance(w, cq.Workplane) else w
    v, t = s.tessellate(tol, ANG_TOL)
    V = np.array([[q.x, q.y, q.z] for q in v]); F = np.array(t)
    tm = trimesh.Trimesh(V, F, process=True)
    tm.merge_vertices()
    return to_manifold(tm)

def slice_poly(man, z):
    g = None
    for p in sorted([Polygon(q) for q in man.slice(z).to_polygons() if len(q) > 2], key=lambda p: -abs(p.area)):
        p = p.buffer(0)
        g = p if g is None else g.symmetric_difference(p)
    return g

def ext(poly, z0, h):
    geoms = poly.geoms if hasattr(poly, "geoms") else [poly]
    res = None
    for g in geoms:
        if g.area < 1e-3:
            continue
        g = g.simplify(0.02)
        w = cq.Workplane("XY").workplane(offset=z0).polyline(list(g.exterior.coords)[:-1]).close().extrude(h)
        for hole in g.interiors:
            w = w.cut(cq.Workplane("XY").workplane(offset=z0 - 1).polyline(list(hole.coords)[:-1]).close().extrude(h + 2))
        res = w if res is None else res.union(w)
    return res

def cyl(x, y, z0, d, h):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(d / 2).extrude(h)

def boxc(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))

def csk(x, y, ztop, d, dk, depth):
    h = cyl(x, y, ztop - depth, d, depth + 1)
    cone = cq.Workplane("XY").add(cq.Solid.makeCone(dk / 2, 0, dk / 2, cq.Vector(x, y, ztop), cq.Vector(0, 0, -1)))
    return h.union(cone)


# ------------------------------------------------------------------ 依鞋子尺寸放大托盤
V15_TOE_FACE_X = 266.8      # v15 鞋頭擋塊 (T9) 內面 x
V15_INNER_HALF_W = 50.3     # v15 托盤前掌內側半寬（z=20）

def warp_params(p):
    x0 = p["Warp_X0"]
    x_face = p["Sleeve_Inner_X"] + p["Shoe_Length"] + p["Shoe_Clear"]
    sx = (x_face - x0) / (V15_TOE_FACE_X - x0)
    sy = (p["Shoe_Max_Width"] / 2 + p["Shoe_Clear"]) / V15_INNER_HALF_W
    return x0, sx, max(sy, 1.0), p["Warp_Blend"]

def warp_pts(V, p):
    x0, sx, sy, bl = warp_params(p)
    V = np.array(V, float)
    x = V[:, 0]
    t = np.clip((x - x0) / bl, 0, 1)
    s = t * t * (3 - 2 * t)
    V[:, 1] = V[:, 1] * (1 + (sy - 1) * s)
    V[:, 0] = np.where(x > x0, x0 + (x - x0) * sx, x)
    return V

def warp_mesh(m, p, max_edge=6.0):
    V, F = trimesh.remesh.subdivide_to_size(m.vertices, m.faces, max_edge=max_edge, max_iter=12)
    return trimesh.Trimesh(warp_pts(V, p), F, process=True)


# ------------------------------------------------------------------ 感測匣（CadQuery 實體）
def cartridge(p, d, S, i, tail_dir):
    """tail_dir: FSR 尾線朝向角度（度，XY 平面）"""
    zf, ZB, ZT = p["Base_Floor"], d["ZB"], d["ZT"]
    e = p["Sensor_Ecc"]
    cx, cy = S[0] + e, S[1]
    out = {}
    rot = lambda w: w.rotate((cx, cy, 0), (cx, cy, 1), tail_dir)
    # C0 感測匣殼：定位嵌板 + 導筒
    ZR = d["ZR"]
    h = cyl(S[0], S[1], ZB, p["Insert_D"], ZR - ZB)
    h = h.edges(">Z").chamfer(1.2)
    h = h.union(cyl(cx, cy, zf + 0.2, p["Tube_OD"], ZB - zf - 0.2 + 0.01))
    h = h.cut(cyl(cx, cy, zf, p["Seat_D"] + 0.4, d["z_seat_top"] - zf))
    h = h.cut(cyl(cx, cy, d["z_seat_top"] - 0.01, p["Tube_ID"], d["z_ledge"][0] - d["z_seat_top"] + 0.02))
    h = h.cut(cyl(cx, cy, d["z_ledge"][0] - 0.01, p["Ledge_ID"], d["z_ledge"][1] - d["z_ledge"][0] + 0.02))
    h = h.cut(cyl(cx, cy, d["z_ledge"][1], p["Tube_ID"], d["z_lip0"] - d["z_ledge"][1]))
    h = h.cut(cyl(cx, cy, d["z_lip0"] - 0.01, p["Lip_ID"], 2))
    h = h.cut(rot(boxc(cx, cx + 30, cy - 4.5, cy + 4.5, d["z_seat_top"] - 0.3, d["z_seat_top"] + 1.2)))
    r = p["Screw_PCD"] / 2
    for k in range(3):                      # 固定 3 孔（對準底座熱熔螺母）
        a = math.radians(15 + 120 * k)
        h = h.cut(csk(S[0] + r * math.cos(a), S[1] + r * math.sin(a), ZR, 2.8, 5.2, 5))
    out[f"C0-{i}_感測匣殼"] = (h, "C")
    seat = cyl(cx, cy, zf, p["Seat_D"], p["Seat_T"])
    seat = seat.cut(cyl(cx, cy, d["z_seat_top"] - 0.3, p["FSR_D"] + 0.5, 1))
    seat = seat.cut(rot(boxc(cx, cx + 20, cy - p["FSR_Tail_W"] / 2 - 0.3, cy + p["FSR_Tail_W"] / 2 + 0.3, d["z_seat_top"] - 0.3, d["z_seat_top"] + 1)))
    out[f"C4-{i}_FSR支撐座"] = (seat, "C")
    fsr = cyl(cx, cy, d["z_seat_top"] - 0.3, p["FSR_D"], p["FSR_T"])
    fsr = fsr.union(rot(boxc(cx, cx + 26, cy - p["FSR_Tail_W"] / 2, cy + p["FSR_Tail_W"] / 2, d["z_seat_top"] - 0.3, d["z_fsr_top"])))
    out[f"C3-{i}_FSR402"] = (fsr, "FSR")
    out[f"C5-{i}_保護傳力片"] = (cyl(cx, cy, d["z_fsr_top"], p["Shield_D"], p["Shield_T"]), "STEEL")
    out[f"C2-{i}_鋼珠Ø5"] = (cq.Workplane("XY").add(cq.Solid.makeSphere(p["Ball_D"] / 2, cq.Vector(cx, cy, d["zc_ball"]), angleDegrees1=-90, angleDegrees2=90)), "STEEL")
    g = cyl(cx, cy, d["z_skirt0"], p["Guide_D"], d["z_shoulder"] - d["z_skirt0"])
    g = g.union(cyl(cx, cy, d["z_shoulder"] - 0.01, p["Guide_Neck_D"], d["z_pad"] - d["z_shoulder"] + 0.01))
    g = g.cut(cyl(cx, cy, d["z_skirt0"] - 0.1, p["Guide_D"] - 6, 2.0))
    g = g.union(cyl(cx, cy, d["z_boss0"], 9.0, d["z_skirt0"] - d["z_boss0"] + 2.1))
    g = g.cut(cyl(cx, cy, d["z_boss0"] + 0.45, p["Bore_D"], d["z_ceiling"] - d["z_boss0"] - 0.45))
    g = g.cut(cyl(cx, cy, d["z_boss0"] - 0.1, p["Ball_Lip_ID"], 0.6))
    g = g.cut(cq.Workplane("XY").add(cq.Solid.makeSphere(p["Bore_D"] / 2, cq.Vector(cx, cy, d["z_ceiling"] - p["Bore_D"] / 2), angleDegrees1=0, angleDegrees2=90)))
    out[f"C1-{i}_TPU導槽"] = (g, "TPU")
    return out


# ------------------------------------------------------------------ 主建模
def build(p=P, verbose=True):
    d = derived(p)
    S1, S2 = d["S1"], d["S2"]
    ZT = d["ZT"]
    foot = trimesh.load(os.path.join(V15, "AFO_foot.stl"))
    F = to_manifold(foot)
    # --- v15 輪廓 ---
    outer9 = slice_poly(F, 9.0)
    outer = Polygon(max(outer9.geoms, key=lambda g: g.area).exterior if hasattr(outer9, "geoms") else outer9.exterior)
    ring17 = slice_poly(F, 17.0)
    grown = unary_union(ring17).buffer(8, join_style=1)            # 補上 x≈100 牆缺口
    if hasattr(grown, "geoms"):
        grown = max(grown.geoms, key=lambda g: g.area)
    inner = Polygon(max(grown.interiors, key=lambda r: Polygon(r).area)).buffer(8, join_style=1)
    outer_wall = Polygon(grown.exterior).buffer(-8, join_style=1)
    d["outer"] = outer; d["inner"] = inner; d["outer_wall"] = outer_wall

    # 1) 刪除 v15 舊 FSR 構造：底板 z 10→15 填平（x < 228，保留鞋頭擋塊插槽）
    keep_toe = sbox(228, -100, 400, 100)
    v15_toe = p.get("Toe_Stopper") not in (None, "custom")
    fill = outer.buffer(-1.0).difference(keep_toe) if v15_toe else outer.buffer(-1.0)   # 客製擋塊 / 無擋塊：舊插槽一併填平
    fillM = cq_to_manifold(ext(fill, 10.0, ZT - 10.0))
    # 牆缺口：v15 舊走線槽在 x≈94~106 貫穿兩側牆（z 11→19），補實
    gapM = None
    for sg in (1, -1):
        loc, _, _ = foot.ray.intersects_location([[100, -sg * 200, 22]], [[0, sg, 0]])
        ys = sorted([v for v in loc[:, 1] if v * sg < 0], key=abs)
        y_in, y_out = (ys[0], ys[1]) if len(ys) >= 2 else (-sg * 47.5, -sg * 51.5)
        g = cq_to_manifold(boxc(91, 109, min(y_in, y_out) - 0.2, max(y_in, y_out) + 0.2, 10.0, 19.6))
        gapM = g if gapM is None else gapM + g
    wall_top = 19.6
    F = F + fillM + gapM
    d["wall_gap_top"] = wall_top

    # 1b) 依鞋子尺寸放大：x > Warp_X0 拉長 sx、加寬 sy（平滑過渡）；後跟杯不動
    F = to_manifold(warp_mesh(to_trimesh(F), p))
    d["warp"] = warp_params(p)
    outer9 = slice_poly(F, 9.0)
    outer = Polygon(max(outer9.geoms, key=lambda g: g.area).exterior if hasattr(outer9, "geoms") else outer9.exterior)
    grown = unary_union(slice_poly(F, 17.0)).buffer(8, join_style=1)
    if hasattr(grown, "geoms"):
        grown = max(grown.geoms, key=lambda g: g.area)
    inner = Polygon(max(grown.interiors, key=lambda r: Polygon(r).area)).buffer(8, join_style=1)
    outer_wall = Polygon(grown.exterior).buffer(-8, join_style=1)
    d["outer"] = outer; d["inner"] = inner; d["outer_wall"] = outer_wall

    # 1c) v15 小腿件鎖附孔重新鑽孔：v15 原網格只有約 30 邊形 → 以真圓 Ø3.4（+0.02）+ 90° 沉頭 Ø7 重切，精度同其他孔
    F = F - cq_to_manifold(v15_screw_holes(foot))

    # 2) 感測器位置下方實心化（底部格柵在感測匣下方補實）
    for S in (S1, S2):
        F = F + cq_to_manifold(cyl(S[0], S[1], 0.0, p["Insert_D"] + 4, ZT - 0.01))

    # 2b) 分件搭接區實心化（底部格柵在接合處補實）
    xs0, xs1 = p["Split_X"] - p["Lap_L"] / 2 - 6, p["Split_X"] + p["Lap_L"] / 2 + 6
    if p.get("Split", True):
        F = F + cq_to_manifold(ext(outer.buffer(-1.0).intersection(sbox(xs0, -200, xs1, 200)), 0.0, ZT - 0.01))

    # 3) 感測匣口袋 + 嵌板沉台 + 熱熔螺母
    cut = None
    def add(w):
        nonlocal cut
        cut = w if cut is None else cut.union(w)
    for S in (S1, S2):
        add(cyl(S[0], S[1], p["Base_Floor"], d["pocket_D"], ZT))
        add(cyl(S[0], S[1], d["ZB"], p["Insert_D"] + 0.4, ZT))
        r = p["Screw_PCD"] / 2
        for k in range(3):
            a = math.radians(15 + 120 * k)
            add(cyl(S[0] + r * math.cos(a), S[1] + r * math.sin(a), d["ZB"] - 5, 3.6, 5.2))
    # 3a) 腳跟墊塊插腳孔（後段共用，所有尺寸都有）
    crescent, sp_pegs = heel_spacer_shape(p, d)
    for (x, y) in sp_pegs:
        add(cyl(x, y, ZT - 6.0, p["Heel_Spacer_Peg_D"] + 0.3, 7.0))
    # 3b) 客製鞋頭擋塊插腳孔
    if p.get("Toe_Stopper") == "custom":
        shell, pegs_xy = toe_shell(p, d)
        for (x, y) in pegs_xy:
            add(cyl(x, y, ZT - 7.0, p["Toe_Peg_D"] + 0.3, 8.0))
    # 4) 走線槽 → 後跟出線孔
    s = 1 if p["Side"] == "L" else -1
    path1 = LineString([S1, (S1[0] - 30, S1[1]), (75, s * -22), (22, 0), (-8, 0)])
    path2 = LineString([S2, (22, 0)])
    wire = unary_union([path1.buffer(p["Wire_W"] / 2), path2.buffer(p["Wire_W"] / 2)])
    cover = unary_union([path1.buffer(p["Cover_W"] / 2), path2.buffer(p["Cover_W"] / 2)])
    pockets = unary_union([Point(*S).buffer(p["Insert_D"] / 2 + 0.2) for S in (S1, S2)])
    cover = cover.difference(pockets).intersection(inner.buffer(-0.5))
    wire_in = wire.intersection(sbox(-20, -200, 400, 200))
    add(ext(wire_in, p["Wire_Bottom"], ZT + 1 - p["Wire_Bottom"]).intersect(boxc(4.5, 400, -200, 200, 0, 50)))
    add(ext(cover.buffer(0.2), ZT - p["Cover_T"], p["Cover_T"] + 1))
    zc = p["Wire_Bottom"] + (ZT - p["Cover_T"] - p["Wire_Bottom"]) / 2
    add(cq.Workplane("XY").add(cq.Solid.makeCylinder(p["Exit_D"] / 2, 30, cq.Vector(12, 0, zc), cq.Vector(-1, 0, 0))))
    d["exit"] = (0.0, 0.0, zc)
    d["wire_path"] = (path1, path2)
    F = F - cq_to_manifold(cut)
    foot_new = to_trimesh(F)

    parts = {}
    parts["F1_AFO腳底件_v17"] = (foot_new, "F")
    if p.get("Split", True):
        rear, front = split_foot(F, p, d)
        parts["F1A_腳底件後段(分件)"] = (rear, "F")
        parts["F1B_腳底件前段(分件)"] = (front, "F")
    leg = trimesh.load(os.path.join(V15, "AFO_leg.stl"))
    parts["L1_AFO小腿件_v15(不改)"] = (leg, "L")
    if p.get("Heel_Spacer"):
        parts["H1_腳跟墊塊(赤腳用)"] = (heel_spacer(p, d), "T")
    if p.get("Toe_Stopper") == "custom":
        parts["T1_鞋頭擋塊_客製(依腳型)"] = (custom_toe_stopper(p, d), "T")
    elif p.get("Toe_Stopper"):
        toe = warp_mesh(trimesh.load(os.path.join(V15, f"toe_stopper_{p['Toe_Stopper']}.stl")), p, 4.0)
        parts[f"T1_鞋頭擋塊_{p['Toe_Stopper']}(v17放大)"] = (toe, "T")
    # 走線蓋板
    cov = ext(cover, ZT - p["Cover_T"], p["Cover_T"])
    parts["B2_走線蓋板"] = (cov, "B")
    # 感測匣：尾線朝走線槽方向
    tail1 = math.degrees(math.atan2(0, -1))          # S1 尾線朝 -X
    tail2 = math.degrees(math.atan2(0 - S2[1], 22 - S2[0]))
    parts.update(cartridge(p, d, S1, 1, tail1))
    parts.update(cartridge(p, d, S2, 2, tail2))
    # 麵包板 / ESP32（示意，放在小腿件背面）
    parts["E5_長條麵包板(示意)"] = (boxc(-23.0, -13.5, -27.5, 27.5, 82, 247), "PCB_W")
    parts["E6_ESP32(示意)"] = (boxc(-36.0, -23.0, -14.15, 14.15, 190, 241.5), "PCB")
    if verbose:
        print("S1", S1, "S2", S2, "wall_gap_top", round(wall_top, 1))
    return parts, d


def heel_spacer_shape(p, d):
    """赤腳用腳跟墊塊：小腿件套筒內側輪廓 − 同輪廓往前平移 Heel_Spacer_T → 等厚月牙；2 支插腳"""
    if "spacer" in d:
        return d["spacer"]
    leg = trimesh.load(os.path.join(V15, "AFO_leg.stl"))
    seg = trimesh.intersections.mesh_plane(leg, [0, 0, 1], [0, 0, 30.0])
    from shapely.ops import polygonize
    lines = unary_union([LineString(q[:, :2]) for q in seg])
    polys = sorted(polygonize(lines), key=lambda g: -g.area)
    # 套筒內側 = 包含 (30, 0) 的最小封閉區域 / 或由外輪廓求洞
    cand = [g for g in polys if g.contains(Point(20, 0))]
    inner = min(cand, key=lambda g: g.area) if cand else Polygon([(8.3, -33.2), (60, -33.2), (60, 33.2), (8.3, 33.2)])
    inner = inner.intersection(sbox(-50, -100, 60, 100)).buffer(-0.4)
    t = p["Heel_Spacer_T"]
    from shapely import affinity as _aff
    cres = inner.difference(_aff.translate(inner, t, 0)).intersection(sbox(-50, -100, 45, 100))
    if hasattr(cres, "geoms"):
        cres = max(cres.geoms, key=lambda g: g.area)
    core = cres.buffer(-(p["Heel_Spacer_Peg_D"] / 2 + 1.5))
    xs, ys = np.meshgrid(np.arange(0, 45, 0.5), np.arange(-40, 40, 0.5))
    c = np.array([(x, y) for x, y in zip(xs.ravel(), ys.ravel()) if core.contains(Point(x, y)) and abs(y) > 10])
    pegs = []
    if len(c):
        pegs = [tuple(c[np.argmax(c[:, 1])]), tuple(c[np.argmin(c[:, 1])])]
    d["spacer"] = (cres, pegs)
    return d["spacer"]


def heel_spacer(p, d):
    cres, pegs = heel_spacer_shape(p, d)
    ZT = d["ZT"]
    w = ext(cres.simplify(0.1), ZT, p["Heel_Spacer_H"])
    for (x, y) in pegs:
        w = w.union(cyl(x, y, ZT - 5.5, p["Heel_Spacer_Peg_D"], 5.6))
    return as_mesh(w)


def v15_screw_holes(foot):
    """v15 腳底件後跟杯上的 3 個 M3 沉頭孔（後牆 1、兩側各 1），由 v15 網格量得位置與軸向"""
    D, DK = 3.50, 7.10          # M3 通孔 Ø3.5（略大於 v15 的 Ø3.4，確保完全切掉舊的多邊形面）
    holes = [((0.0, 0.0, 50.0), (1.0, 0.0, 0.0))]                       # 後牆：沿 +X
    for sg in (1, -1):
        n = np.array([-0.31, sg * 0.95, 0.0]); n /= np.linalg.norm(n)   # 側牆法向（朝外）
        holes.append(((31.345, sg * 46.9, 50.0), tuple(-n)))             # 由內往外的軸向取反 → 進入方向
    cut = None
    for (pt, d) in holes:
        d = np.asarray(d, float); d /= np.linalg.norm(d); pt = np.asarray(pt, float)
        # 外表面（沉頭所在）：在孔旁 z+3 處沿軸向射線量牆外表面，再投回軸線
        probe = pt + np.array([0, 0, 3.0])
        loc, _, _ = foot.ray.intersects_location([probe + d * 10], [-d])
        t = (probe + d * 10 - loc) @ d if len(loc) else np.array([10.0])
        t = t[(t > 0) & (t < 25)]
        outer = pt + d * (10 - t.max()) if len(t) else pt
        o = outer - d * 3.0
        c = cq.Solid.makeCylinder(D / 2, 20.0, cq.Vector(*o), cq.Vector(*d))
        depth = (DK - D) / 2
        cone = cq.Solid.makeCone(DK / 2 + 3.0, D / 2, depth + 3.0, cq.Vector(*(outer - d * 3.0)), cq.Vector(*d))
        w = cq.Workplane("XY").add(c).union(cq.Workplane("XY").add(cone))
        cut = w if cut is None else cut.union(w)
    return cut


def foot_in_tray(p):
    """腳印輪廓依量測腳長 / 腳寬縮放，放到托盤座標（腳跟後緣在 套筒內面 + Heel_Offset）"""
    c = np.loadtxt(os.path.join(HERE, "data", "footprint_outline_mm.csv"), delimiter=",")
    fs = p.get("Foot_Scale")
    sx = fs[0] / p["Foot_Length"] if fs else 1.0
    sy = fs[1] / p["Foot_Max_Width"] if fs else 1.0
    x0 = p["Sleeve_Inner_X"] + p["Heel_Offset"]
    return Polygon(np.c_[c[:, 0] * sx + x0, c[:, 1] * sy]).buffer(0)


def toe_shell(p, d):
    """客製鞋頭擋塊 2D 外形（內緣 = 腳趾包絡 + Toe_Clear，厚 Toe_Shell，不超出托盤內牆）與 2 支插腳位置"""
    foot = foot_in_tray(p).buffer(15, join_style=1).buffer(-15, join_style=1)   # 腳趾縫補平 → 包絡外形
    x0 = p["Sleeve_Inner_X"] + p["Heel_Offset"] + p["Toe_Region"] * p["Shoe_Length"]
    gap = foot.buffer(p["Toe_Clear"], join_style=1)
    shell = gap.buffer(p["Toe_Shell"], join_style=1).difference(gap)
    shell = shell.intersection(d["inner"].buffer(-0.4)).intersection(sbox(x0, -200, 500, 200))
    shell = shell.buffer(1.0, join_style=1).buffer(-1.0, join_style=1)
    if hasattr(shell, "geoms"):
        shell = max(shell.geoms, key=lambda g: g.area)
    core = shell.buffer(-(p["Toe_Peg_D"] / 2 + 2.0))
    xs, ys = np.meshgrid(np.arange(x0, 400, 1.0), np.arange(-80, 80, 1.0))
    cand = [(x, y) for x, y in zip(xs.ravel(), ys.ravel()) if core.contains(Point(x, y))]
    pegs = []
    if cand:
        c = np.array(cand)
        a = c[np.argmax(c[:, 0])]                                  # 最前端
        b = c[np.argmax(np.hypot(*(c - a).T))]                     # 離前端最遠（側邊）
        pegs = [tuple(a), tuple(b)]
    d["toe_shell"] = shell; d["toe_pegs"] = pegs
    return shell, pegs


def custom_toe_stopper(p, d):
    """客製鞋頭擋塊：依腳型的殼體 + 2 支 Ø6 插腳（插入底板孔）"""
    shell, pegs = d.get("toe_shell"), d.get("toe_pegs")
    if shell is None:
        shell, pegs = toe_shell(p, d)
    ZT = d["ZT"]
    w = ext(shell.simplify(0.1), ZT, p["Toe_H"])
    for (x, y) in pegs:
        w = w.union(cyl(x, y, ZT - 6.5, p["Toe_Peg_D"], 6.6))
    return as_mesh(w)


def split_foot(F, p, d):
    """腳底件拆成後段 / 前段：底板搭接（後段在上層、前段在下層），牆在 Split_X 對接；回傳 (rear, front) trimesh"""
    Xc, L, Zl, g = p["Split_X"], p["Lap_L"], p["Lap_Z"], p["Split_Gap"]
    Xa, Xb = Xc - L / 2, Xc + L / 2
    ZT = d["ZT"]
    big = lambda x0, x1, z0, z1: cq_to_manifold(boxc(x0, x1, -300, 300, z0, z1))
    R = big(-100, Xa, -10, 300) + big(Xa, Xb, Zl, ZT) + big(Xa, Xc, ZT - 0.01, 300)
    Rs = big(-100, Xa - g, -10, 300) + big(Xa - g, Xb - g, Zl + g, ZT) + big(Xa - g, Xc - g, ZT - 0.01, 300)
    rear = F ^ Rs
    front = F - R
    holes_f = None; holes_r = None
    for dx in p["Split_Screw_DX"]:
        for y in p["Split_Screw_Y"]:
            x = Xc + dx
            hf = cyl(x, y, -1, 4.5, Zl + 1.5).union(cq.Workplane("XY").add(cq.Solid.makeCone(4.3, 2.0, 2.3, cq.Vector(x, y, -0.01), cq.Vector(0, 0, 1))))
            hr = cyl(x, y, Zl - 0.5, 5.6, 6.0)          # M4 熱熔螺母 Ø5.6 × 5
            holes_f = hf if holes_f is None else holes_f.union(hf)
            holes_r = hr if holes_r is None else holes_r.union(hr)
    rear = rear - cq_to_manifold(holes_r)
    front = front - cq_to_manifold(holes_f)
    d["split"] = dict(Xa=Xa, Xb=Xb, Xc=Xc, screws=[(Xc + dx, y) for dx in p["Split_Screw_DX"] for y in p["Split_Screw_Y"]])
    return to_trimesh(rear), to_trimesh(front)


def as_mesh(w):
    if isinstance(w, trimesh.Trimesh):
        return w
    s = w.val() if isinstance(w, cq.Workplane) else w
    v, t = s.tessellate(LIN_TOL, ANG_TOL)
    return trimesh.Trimesh(np.array([[q.x, q.y, q.z] for q in v]), np.array(t), process=True)


def write_faceted_step(path, named_meshes):
    """寫出 AP214 FACETED_BREP（與 v15 STEP 相同格式）。"""
    L = []
    n = [0]
    def e(s):
        n[0] += 1; L.append(f"#{n[0]}={s};"); return n[0]
    ctx = e("APPLICATION_CONTEXT('core data for automotive mechanical design processes')")
    e(f"APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,#{ctx})")
    pc = e(f"PRODUCT_CONTEXT('',#{ctx},'mechanical')")
    pr = e(f"PRODUCT('AFO_v17','AFO_v17','',(#{pc}))")
    pf = e(f"PRODUCT_DEFINITION_FORMATION('','',#{pr})")
    pdc = e(f"PRODUCT_DEFINITION_CONTEXT('part definition',#{ctx},'design')")
    pd = e(f"PRODUCT_DEFINITION('design','',#{pf},#{pdc})")
    pds = e(f"PRODUCT_DEFINITION_SHAPE('','',#{pd})")
    lu = e("(LENGTH_UNIT()NAMED_UNIT(*)SI_UNIT(.MILLI.,.METRE.))")
    au = e("(NAMED_UNIT(*)PLANE_ANGLE_UNIT()SI_UNIT($,.RADIAN.))")
    su = e("(NAMED_UNIT(*)SI_UNIT($,.STERADIAN.)SOLID_ANGLE_UNIT())")
    um = e(f"UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-04),#{lu},'distance_accuracy_value','confusion accuracy')")
    gc = e(f"(GEOMETRIC_REPRESENTATION_CONTEXT(3)GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#{um}))GLOBAL_UNIT_ASSIGNED_CONTEXT((#{lu},#{au},#{su}))REPRESENTATION_CONTEXT('',''))")
    breps = []
    for name, m in named_meshes:
        vid = [e(f"CARTESIAN_POINT('',({x:.4f},{y:.4f},{z:.4f}))") for x, y, z in m.vertices]
        faces = []
        nrm = m.face_normals
        for (a, b, c), nn in zip(m.faces, nrm):
            loop = e(f"POLY_LOOP('',(#{vid[a]},#{vid[b]},#{vid[c]}))")
            bd = e(f"FACE_OUTER_BOUND('',#{loop},.T.)")
            o = m.vertices[a]
            p0 = vid[a]
            dn = e(f"DIRECTION('',({nn[0]:.6f},{nn[1]:.6f},{nn[2]:.6f}))")
            ax = e(f"AXIS2_PLACEMENT_3D('',#{p0},#{dn},$)")
            pl = e(f"PLANE('',#{ax})")
            faces.append(e(f"FACE_SURFACE('',(#{bd}),#{pl},.T.)"))
        sh = e("CLOSED_SHELL('',(" + ",".join(f"#{f}" for f in faces) + "))")
        breps.append(e(f"FACETED_BREP('{name}',#{sh})"))
    ax0 = e("AXIS2_PLACEMENT_3D('',#" + str(e("CARTESIAN_POINT('',(0.,0.,0.))")) + ",$,$)")
    rep = e("FACETED_BREP_SHAPE_REPRESENTATION('AFO_v17',(" + ",".join(f"#{b}" for b in [ax0] + breps) + f"),#{gc})")
    e(f"SHAPE_DEFINITION_REPRESENTATION(#{pds},#{rep})")
    with open(path, "w") as fh:
        fh.write("ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('AFO v17 faceted solid'),'2;1');\n")
        fh.write("FILE_NAME('" + os.path.basename(path) + "','2026-10-31T00:00:00',(''),(''),'afo_v17.py','afo_v17.py','');\n")
        fh.write("FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));\nENDSEC;\nDATA;\n")
        fh.write("\n".join(L)); fh.write("\nENDSEC;\nEND-ISO-10303-21;\n")


ASCII = {"H1": "H1_heel_spacer_barefoot", "F1A": "F1A_AFO_foot_rear", "F1B": "F1B_AFO_foot_front", "F1": "F1_AFO_foot_v17", "L1": "L1_AFO_leg_v15", "T1": "T1_toe_stopper", "B2": "B2_wire_cover",
         "C0": "C0_cartridge_housing", "C1": "C1_TPU_guide", "C2": "C2_steel_ball_5mm", "C3": "C3_FSR402_ref",
         "C4": "C4_FSR_seat", "C5": "C5_shield_disc", "E5": "E5_breadboard_ref", "E6": "E6_ESP32_ref"}

if __name__ == "__main__":
    parts, d = build(P)
    for k, (w, m) in parts.items():
        tm = as_mesh(w)
        b = tm.bounds
        print(f"{k:30s} {b[1][0]-b[0][0]:7.1f} x {b[1][1]-b[0][1]:6.1f} x {b[1][2]-b[0][2]:5.1f}  V={tm.volume/1000:7.2f} cm3 watertight={tm.is_watertight}")
    if len(sys.argv) > 2 and sys.argv[1] == "--export":
        out = sys.argv[2]
        for sub in ("STL", "STEP", "3MF"):
            os.makedirs(os.path.join(out, sub), exist_ok=True)
        named, printable = [], []
        for k, (w, m) in parts.items():
            code = k.split("_")[0]
            base = ASCII[code.split("-")[0]] + (("_" + code.split("-")[1]) if "-" in code else "")
            tm = as_mesh(w)
            if k.startswith("L1"):
                continue                       # 小腿件：沿用 v15 原檔，不輸出
            if code == "F1" and P.get("Split", True):   # 分件版：整件只出 STEP（參考），列印用 F1A / F1B
                write_faceted_step(os.path.join(out, "STEP", base + "_reference_one_piece.step"), [(base, tm)])
                continue
            ref = k.startswith(("E5", "E6", "C3"))   # 外購件 / 示意件
            if not ref:
                tm.export(os.path.join(out, "STL", base + ".stl"))
                tm.export(os.path.join(out, "3MF", base + ".3mf"))
                printable.append(base)
            if isinstance(w, trimesh.Trimesh):
                write_faceted_step(os.path.join(out, "STEP", base + ".step"), [(base, tm)])
            else:
                cq.exporters.export(w, os.path.join(out, "STEP", base + ".step"))
            named.append((base, tm))
        write_faceted_step(os.path.join(out, "STEP", "AFO_v17_assembly_foot_and_sensors.step"), named)
        print("exported to", out, "printable:", printable)
