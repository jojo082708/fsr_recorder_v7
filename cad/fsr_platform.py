"""
外穿式布鞋 FSR 雙點足底力量量測平台 — 參數化模型 (CadQuery)
==========================================================
座標系（沿用 AFO v15）：
  原點 = 布鞋鞋跟後緣、平台中心線、底座底面 (z=0)
  +X 朝腳尖、+Y 朝左（左腳 = 外側）、+Z 朝上
所有尺寸單位 mm。標記「待確認」的參數為暫定值，只用來畫圖，必須實測後更新。

用法：
  python3 fsr_platform.py                 # 只建模並列出零件尺寸
  python3 fsr_platform.py --export OUT    # 匯出 STL / STEP（工程圖確認後才使用）
"""
import os, sys, math
import numpy as np
import cadquery as cq
from shapely.geometry import Polygon, Point, LineString, box as sbox, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- 參數表
P = dict(
    # --- 足型（由腳印量測，已知） ---
    Side="L",                 # 腳印判定為左腳（大拇趾在圖右側）；右腳設 "R" 鏡像
    Foot_Length=249.0,        # 腳印最長
    Foot_Max_Width=94.0,      # 腳印最寬
    Foot_S1=(177.0, 72.0),    # 第一蹠骨頭 FSR 中心：距腳跟後緣 249-72=177、距外側邊 94-22=72
    Foot_S2=(25.0, 35.0),     # 腳跟 FSR 中心：距腳跟後緣 25（圖上標 21，比例量得 25 → 待確認）、距外側邊 35

    # --- 布鞋（待確認：以下為暫定值，參考 AFO v15 托盤內徑推估）---
    Shoe_Length=270.0,        # 待確認：鞋底外緣全長
    Shoe_Max_Width=104.0,     # 待確認：鞋底外緣最寬
    Sole_Thickness=25.0,      # 待確認：鞋跟處鞋底厚
    Heel_Offset=12.0,         # 待確認：腳跟後緣 → 鞋底後緣（鞋跟杯+鞋底外凸）
    Shoe_Upper_H=70.0,        # 待確認：鞋面高度（僅示意）

    # --- 平台 ---
    Fit_Gap=2.0,              # 鞋底外緣與固定件間隙（可加 TPU 墊片吸收）
    Rim=15.0,                 # 平台超出鞋底外緣的邊寬（固定件安裝區）
    Toe_Ext=10.0,             # 前端延伸（鞋頭擋塊調整區）
    Base_H=12.0,              # 底座高度 (z 0→12)
    Base_Floor=3.0,           # 底座底板厚
    Base_Wall=3.0,            # 底座外牆厚
    Rib_T=2.4,                # 內部肋條厚
    Top_T=4.0,                # 上層承載板厚 (z 12→16)
    Pad_T=2.0, Pad_Recess=0.5,  # 止滑橡膠墊厚 / 底座凹槽深（墊片外凸 1.5）
    Toe_Spring=2.0,           # 前掌底部斜削（滾動）
    Heel_Bevel=1.5,           # 後跟底部斜削

    # --- FSR 感測模組 ---
    Sensor_Ecc=0.0,           # 定位嵌板偏心量（0/3/6 三種嵌板），可轉 30° 一格
    Sensor_Ecc_Max=6.0,
    Insert_D=60.0,            # 定位嵌板外徑
    Tube_OD=34.0, Tube_ID=28.4,
    Guide_D=28.0, Guide_Neck_D=27.0, Lip_ID=27.4,
    Ball_D=5.0, Bore_D=5.15, Ball_Lip_ID=4.5,
    Stop_Gap=1.0,             # 過載止擋行程：決定 FSR 最大受力（見說明）
    Pad_Proud=0.3,            # TPU 傳力頂面高出平台
    Seat_D=30.2, Seat_T=1.5,  # FSR 支撐座
    FSR_D=18.3, FSR_Active_D=12.7, FSR_T=0.45, FSR_Tail_W=7.6, FSR_Len=56.0,
    Shield_D=10.0, Shield_T=0.5,  # 保護傳力片

    # --- 布鞋固定機構 ---
    HeelCup_H=45.0, HeelCup_H_Front=25.0, HeelCup_Len=75.0, HeelCup_T=3.5,
    Toe_H=22.0, Toe_T=6.0, Toe_Adj=15.0,
    Guide_X_Ratio=0.80, Guide_Len=50.0, Guide_H=26.0, Guide_T=4.0, Guide_Adj=6.0,
    Strap_W=38.0,             # 魔鬼氈寬
    Midfoot_Strap_X=160.0,

    # --- 電控 (待確認尺寸) ---
    ESP32_Size=(51.5, 28.3, 13.0),     # 待確認：ESP32 DevKit V1 30-pin (L,W,H 含排針)
    Breadboard_Size=(165.0, 55.0, 9.5),  # 待確認：830 孔長條麵包板
    Battery_Size=(77.0, 21.0, 19.0),   # 待確認：18650 單槽電池盒
    Charger_Size=(26.0, 17.0, 5.0),    # 待確認：TP4056 / 升壓模組
    Box_Wall=2.5, Box_Z0=12.0, Box_Gap=2.0,
)

def derived(p):
    """依參數計算感測器在平台座標的位置。"""
    fw = p["Foot_Max_Width"]
    s = 1 if p["Side"] == "L" else -1
    def map_(fs):
        return (p["Heel_Offset"] + fs[0], s * (fw / 2 - fs[1]))
    d = dict(S1=map_(p["Foot_S1"]), S2=map_(p["Foot_S2"]))
    d["Platform_Thickness"] = p["Base_H"] + p["Top_T"]
    d["Z_top"] = d["Platform_Thickness"]
    return d

# ---------------------------------------------------------------- 輪廓
def foot_outline(p):
    c = np.loadtxt(os.path.join(HERE, "data", "footprint_outline_mm.csv"), delimiter=",")
    poly = Polygon(c)
    # 腳底板外形：腳印外輪廓（含足弓內側填補、腳趾合併）
    poly = poly.buffer(60, join_style=1, resolution=32).buffer(-60, join_style=1, resolution=32)
    if p["Side"] == "R":
        poly = affinity.scale(poly, 1, -1, origin=(0, 0))
    return poly

def shoe_outline(p):
    f = foot_outline(p)
    minx, miny, maxx, maxy = f.bounds
    sx = p["Shoe_Length"] / (maxx - minx)
    sy = p["Shoe_Max_Width"] / (maxy - miny)
    s = affinity.translate(f, -minx, -(maxy + miny) / 2)
    return affinity.scale(s, sx, sy, origin=(0, 0))

def platform_outline(p):
    sh = shoe_outline(p)
    u = unary_union([sh, affinity.translate(sh, p["Toe_Ext"], 0)])
    return u.buffer(p["Rim"], join_style=1, resolution=32)

def y_edge(poly, x, side=+1):
    """多邊形在 X=x 處的 +Y / -Y 邊界。"""
    ln = LineString([(x, -500), (x, 500)]).intersection(poly)
    if ln.is_empty:
        return float("nan")
    ys = np.array(ln.coords)[:, 1] if ln.geom_type == "LineString" else np.concatenate([np.array(g.coords)[:, 1] for g in ln.geoms])
    return ys.max() if side > 0 else ys.min()

def y_edge_range(poly, x0, x1, side=+1):
    v = [side * y_edge(poly, x, side) for x in np.linspace(x0, x1, 25)]
    return np.nanmax(v) * side

# ---------------------------------------------------------------- CQ 幫手
def resample(ring, n):
    L = ring.length
    return [ring.interpolate(t * L).coords[0] for t in np.linspace(0, 1, n, endpoint=False)]

def ext_spline(poly, z0, h, n=120):
    pts = resample(poly.exterior, n)
    return cq.Workplane("XY").workplane(offset=z0).spline(pts, periodic=True, includeCurrent=False).close().extrude(h)

def ext_poly(poly, z0, h):
    """多邊形（可含洞、可為 MultiPolygon）直線段擠出。"""
    geoms = poly.geoms if hasattr(poly, "geoms") else [poly]
    res = None
    for g in geoms:
        if g.area < 1e-3:
            continue
        g = g.simplify(0.05)
        w = cq.Workplane("XY").workplane(offset=z0).polyline(list(g.exterior.coords)[:-1]).close().extrude(h)
        for hole in g.interiors:
            w = w.cut(cq.Workplane("XY").workplane(offset=z0 - 1).polyline(list(hole.coords)[:-1]).close().extrude(h + 2))
        res = w if res is None else res.union(w)
    return res

def cyl(x, y, z0, d, h):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(d / 2).extrude(h)

def boxc(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))

def csk(x, y, ztop, d=3.4, dk=6.5, depth=40):
    """沉頭孔（由上往下）"""
    h = cyl(x, y, ztop - depth, d, depth + 1)
    cone = cq.Workplane("XY").add(cq.Solid.makeCone(dk / 2, 0, dk / 2, cq.Vector(x, y, ztop), cq.Vector(0, 0, -1)))
    return h.union(cone)

# ---------------------------------------------------------------- 建模
def build(p=P):
    d = derived(p)
    S1, S2 = d["S1"], d["S2"]
    ZB, ZT = p["Base_H"], d["Z_top"]
    side = 1 if p["Side"] == "L" else -1   # 外側方向 (+Y for left foot)
    shoe = shoe_outline(p)
    plat = platform_outline(p)
    inner = plat.buffer(-p["Base_Wall"])
    SL, FG = p["Shoe_Length"], p["Fit_Gap"]
    parts = {}

    # ---------- 固定件螺絲位置（M4，底座熱熔螺母） ----------
    m4 = []
    hc_off = FG + p["HeelCup_T"] + 5.0
    m4 += [(-hc_off, 0.0)]
    for sgn in (+1, -1):
        m4.append((50.0, y_edge(shoe, 50.0, sgn) + sgn * hc_off))
    Xg = p["Guide_X_Ratio"] * SL
    g_off = FG + p["Guide_T"] + 6.0
    for sgn in (+1, -1):
        ye = y_edge_range(shoe, Xg - p["Guide_Len"] / 2, Xg + p["Guide_Len"] / 2, sgn)
        for dx in (-15, 15):
            m4.append((Xg + dx, ye + sgn * g_off))
    Xt = SL + FG + p["Toe_T"] + 7.0
    m4 += [(Xt, 13.0), (Xt, -13.0)]

    # ---------- 上層板 M3 螺絲 ----------
    ring = plat.buffer(-7.5).exterior
    cand = resample(ring, 40)
    sens_keep = [Point(*S1).buffer(p["Insert_D"] / 2 + 8), Point(*S2).buffer(p["Insert_D"] / 2 + 8)]
    m3 = []
    for c in cand:
        pt = Point(c)
        if any(pt.distance(Point(q)) < 22 for q in m4 + m3):
            continue
        if any(pt.within(k) for k in sens_keep):
            continue
        m3.append(c)
    m3 += [(110.0, 0.0), (235.0, 0.0)]

    # ---------- 電控盒位置 ----------
    BL = p["Breadboard_Size"][0] + 2 * 1.5 + 2 * p["Box_Wall"]
    BW = p["Breadboard_Size"][1] + 2 * 1.5 + 2 * p["Box_Wall"]
    battery_h = p["Battery_Size"][2] + 2
    BH = p["Box_Wall"] + battery_h + 2 + p["Breadboard_Size"][2] + p["ESP32_Size"][2] + 6 + 2.5
    bx1 = p["Midfoot_Strap_X"] - p["Strap_W"] / 2 - 8
    bx0 = bx1 - BL
    y_rail_in = y_edge_range(plat, bx0, bx1, side)
    rail_T = 6.0
    y_box_in = y_rail_in + side * (rail_T + 0.0)
    box_z0 = p["Box_Z0"]
    d.update(BL=BL, BW=BW, BH=BH, bx0=bx0, bx1=bx1, y_box_in=y_box_in, Xg=Xg, Xt=Xt, m4=m4, m3=m3)

    # ================= D. 底部基座 =================
    base = ext_spline(plat, 0, ZB)
    # 中束帶扣環（兩側）
    for sgn in (+1, -1):
        X = p["Midfoot_Strap_X"]
        ye = y_edge_range(plat, X - 24, X + 24, sgn)
        lug = boxc(X - p["Strap_W"] / 2 - 4, X + p["Strap_W"] / 2 + 4, *sorted([ye - sgn * 4, ye + sgn * 11]), 0, 8)
        slot = boxc(X - p["Strap_W"] / 2 - 1, X + p["Strap_W"] / 2 + 1, *sorted([ye + sgn * 3, ye + sgn * 7.5]), -1, 10)
        base = base.union(lug).cut(slot)
    # 內腔（肋條、凸台保留）
    ribs = []
    for X in np.arange(25, SL + 20, 32):
        ribs.append(LineString([(X, -200), (X, 200)]).buffer(p["Rib_T"] / 2))
    for Y in (-30, 0, 30):
        ribs.append(LineString([(-50, Y), (400, Y)]).buffer(p["Rib_T"] / 2))
    keep = ribs + [Point(*S).buffer(p["Insert_D"] / 2 + 2) for S in (S1, S2)]
    keep += [Point(*q).buffer(5) for q in m4] + [Point(*q).buffer(4.5) for q in m3]
    # 電控滑軌座固定凸台（外側牆）
    rail_boss = [(rx, y_edge(plat, rx, side) - side * 5) for rx in (25.0, 80.0)]
    keep += [Point(*q).buffer(6) for q in rail_boss]
    cav = inner.difference(unary_union(keep))
    base = base.cut(ext_poly(cav, p["Base_Floor"], ZB))
    # 感測器口袋（偏心可調）
    pocket_D = p["Tube_OD"] + 2 * p["Sensor_Ecc_Max"] + 1.0
    for S in (S1, S2):
        base = base.cut(cyl(S[0], S[1], p["Base_Floor"], pocket_D, ZB))
        for k in range(3):
            a = math.radians(90 + 120 * k)
            base = base.cut(cyl(S[0] + 27 * math.cos(a), S[1] + 27 * math.sin(a), ZB - 6, 4.0, 7))
    d["pocket_D"] = pocket_D
    # 走線槽（肋條缺口，z 3→8）→ 外側牆出線孔
    exit_x = bx0 + 70
    exit_y = y_edge(plat, exit_x, side)
    wire_y = side * 38.0
    path1 = LineString([S1, (S1[0], wire_y), (exit_x, wire_y), (exit_x, exit_y - side * 2)])
    path2 = LineString([S2, (S2[0], wire_y), (exit_x, wire_y)])
    wire = unary_union([path1.buffer(3.5), path2.buffer(3.5)]).intersection(inner)
    base = base.cut(ext_poly(wire, p["Base_Floor"], 5.0))
    base = base.cut(cq.Workplane("XY").add(cq.Solid.makeCylinder(3.2, 30, cq.Vector(exit_x, exit_y - side * 10, 6.5), cq.Vector(0, side, 0))))
    d["exit"] = (exit_x, exit_y)
    # 熱熔螺母孔
    for q in m4:
        base = base.cut(cyl(q[0], q[1], ZB - 8, 5.6, 9))
    for q in m3:
        base = base.cut(cyl(q[0], q[1], ZB - 6, 4.0, 7))
    for q in rail_boss:
        base = base.cut(cq.Workplane("XY").add(cq.Solid.makeCylinder(2.8, 9, cq.Vector(q[0], q[1] + side * 6.5, 6.0), cq.Vector(0, -side, 0))))
    d["rail_boss"] = rail_boss
    # 底部止滑墊凹槽 + 前掌滾動斜削
    toe_start = 0.80 * SL
    pad_heel = plat.buffer(-8).intersection(sbox(-100, -200, 95, 200))
    pad_fore = plat.buffer(-8).intersection(sbox(140, -200, toe_start - 3, 200))
    base = base.cut(ext_poly(pad_heel, -1, 1 + p["Pad_Recess"])).cut(ext_poly(pad_fore, -1, 1 + p["Pad_Recess"]))
    xf = plat.bounds[2] + 1
    wedge = (cq.Workplane("XZ").polyline([(toe_start, 0), (xf, 0), (xf, p["Toe_Spring"])]).close().extrude(-200).translate((0, -100, 0)))
    xb = plat.bounds[0] - 1
    wedge2 = (cq.Workplane("XZ").polyline([(xb, 0), (15, 0), (xb, p["Heel_Bevel"])]).close().extrude(-200).translate((0, -100, 0)))
    base = base.cut(wedge).cut(wedge2)
    parts["D1_底部基座"] = (base, "D")
    pads = ext_poly(pad_heel, p["Pad_Recess"] - p["Pad_T"], p["Pad_T"]).union(ext_poly(pad_fore, p["Pad_Recess"] - p["Pad_T"], p["Pad_T"]))
    parts["D2_止滑橡膠墊"] = (pads, "D")

    # ================= B. 上層承載平台 =================
    top = ext_spline(platform_outline(p), ZB, p["Top_T"])
    for S in (S1, S2):
        top = top.cut(cyl(S[0], S[1], ZB - 1, p["Insert_D"] + 0.4, 10))
    for q in m3:
        top = top.cut(csk(q[0], q[1], ZT, 3.4, 6.5, 6))
    for q in m4:
        top = top.cut(cyl(q[0], q[1], ZB - 1, 4.5, 10))
    parts["B1_上層承載板"] = (top, "B")

    # ================= C. FSR 感測模組 ×2 =================
    zf = p["Base_Floor"]
    z_seat_top = zf + p["Seat_T"]
    z_fsr_top = z_seat_top - 0.3 + p["FSR_T"]
    z_sh_top = z_fsr_top + p["Shield_T"]
    zc_ball = z_sh_top + p["Ball_D"] / 2
    z_ceiling = zc_ball + p["Ball_D"] / 2
    z_ledge0, z_ledge1 = 6.2, 7.4
    z_skirt0 = z_ledge1 + p["Stop_Gap"]
    z_boss0 = z_sh_top + p["Stop_Gap"] + 0.4
    z_lip0 = ZT - 0.8
    z_shoulder = z_lip0 - 0.5
    z_pad = ZT + p["Pad_Proud"]
    d.update(z_seat_top=z_seat_top, z_fsr_top=z_fsr_top, z_sh_top=z_sh_top, zc_ball=zc_ball,
             z_ceiling=z_ceiling, z_skirt0=z_skirt0, z_boss0=z_boss0, z_pad=z_pad, z_ledge=(z_ledge0, z_ledge1),
             z_shoulder=z_shoulder, z_lip0=z_lip0)
    for i, S in enumerate((S1, S2), start=1):
        e = p["Sensor_Ecc"]
        cx, cy = S[0] + e, S[1]
        # C0 定位嵌板 + 導筒（PETG）
        h = cyl(S[0], S[1], ZB, p["Insert_D"], p["Top_T"])
        h = h.union(cyl(cx, cy, zf + 0.2, p["Tube_OD"], ZB - zf - 0.2 + 0.01))
        h = h.cut(cyl(cx, cy, zf, p["Seat_D"] + 0.4, z_seat_top - zf))          # 支撐座卡入段
        h = h.cut(cyl(cx, cy, z_seat_top - 0.01, p["Tube_ID"], z_ledge0 - z_seat_top + 0.02))
        h = h.cut(cyl(cx, cy, z_ledge0 - 0.01, 14.0, z_ledge1 - z_ledge0 + 0.02))
        h = h.cut(cyl(cx, cy, z_ledge1, p["Tube_ID"], z_lip0 - z_ledge1))
        h = h.cut(cyl(cx, cy, z_lip0 - 0.01, p["Lip_ID"], 2))
        # FSR 尾線出口（朝外側）
        h = h.cut(boxc(cx, cx + 30, cy - 5, cy + 5, z_seat_top - 0.3, z_seat_top + 1.2).rotate((cx, cy, 0), (cx, cy, 1), 90 * side))
        for k in range(12):
            a = math.radians(90 + 30 * k)
            h = h.cut(csk(S[0] + 27 * math.cos(a), S[1] + 27 * math.sin(a), ZT, 3.4, 6.5, 6))
        h = h.cut(cyl(S[0] - 22, S[1], ZT - 1.5, 6, 2))  # 拆卸撬口 / 方向刻痕
        parts[f"C0-{i}_感測匣殼(定位嵌板+導筒)"] = (h, "C")
        # C4 FSR 支撐座
        seat = cyl(cx, cy, zf, p["Seat_D"], p["Seat_T"])
        seat = seat.cut(cyl(cx, cy, z_seat_top - 0.3, p["FSR_D"] + 0.5, 1))
        seat = seat.cut(boxc(cx, cx + 20, cy - p["FSR_Tail_W"] / 2 - 0.3, cy + p["FSR_Tail_W"] / 2 + 0.3, z_seat_top - 0.3, z_seat_top + 1).rotate((cx, cy, 0), (cx, cy, 1), 90 * side))
        parts[f"C4-{i}_FSR支撐座"] = (seat, "C")
        # C3 FSR 402
        fsr = cyl(cx, cy, z_seat_top - 0.3, p["FSR_D"], p["FSR_T"])
        fsr = fsr.union(boxc(cx, cx + 30, cy - p["FSR_Tail_W"] / 2, cy + p["FSR_Tail_W"] / 2, z_seat_top - 0.3, z_fsr_top).rotate((cx, cy, 0), (cx, cy, 1), 90 * side))
        parts[f"C3-{i}_FSR402"] = (fsr, "FSR")
        # C5 保護傳力片
        parts[f"C5-{i}_保護傳力片"] = (cyl(cx, cy, z_fsr_top, p["Shield_D"], p["Shield_T"]), "STEEL")
        # C2 鋼珠
        parts[f"C2-{i}_鋼珠Ø5"] = (cq.Workplane("XY").add(cq.Solid.makeSphere(p["Ball_D"] / 2, cq.Vector(cx, cy, zc_ball), angleDegrees1=-90, angleDegrees2=90)), "STEEL")
        # C1 TPU 導槽（浮動傳力柱）
        g = cyl(cx, cy, z_skirt0, p["Guide_D"], z_shoulder - z_skirt0)
        g = g.union(cyl(cx, cy, z_shoulder - 0.01, p["Guide_Neck_D"], z_pad - z_shoulder + 0.01))
        g = g.cut(cyl(cx, cy, z_skirt0 - 0.1, 22.0, 2.0))                     # 底部環形止擋面 (外環)
        g = g.union(cyl(cx, cy, z_boss0, 10.0, z_skirt0 - z_boss0 + 2.1))       # 中央導珠柱
        g = g.cut(cyl(cx, cy, z_boss0 + 0.45, p["Bore_D"], z_ceiling - z_boss0 - 0.45))  # 導槽孔
        g = g.cut(cyl(cx, cy, z_boss0 - 0.1, p["Ball_Lip_ID"], 0.6))           # 防脫唇
        g = g.cut(cq.Workplane("XY").add(cq.Solid.makeSphere(p["Bore_D"] / 2, cq.Vector(cx, cy, z_ceiling - p["Bore_D"] / 2), angleDegrees1=0, angleDegrees2=90)))
        parts[f"C1-{i}_TPU導槽"] = (g, "TPU")

    # ================= A. 布鞋固定機構 =================
    # A1 U 型後跟定位座
    cut_x = p["HeelCup_Len"]
    u_in = shoe.buffer(FG, join_style=1)
    u_out = shoe.buffer(FG + p["HeelCup_T"], join_style=1)
    clip = boxc(-100, cut_x, -200, 200, ZT - 1, ZT + 200)
    hc = ext_spline(u_out, ZT, p["HeelCup_H"]).cut(ext_spline(u_in, ZT - 1, p["HeelCup_H"] + 2))
    fl = ext_spline(shoe.buffer(FG + p["HeelCup_T"] + 9.5, join_style=1), ZT, 3.0).cut(ext_spline(u_in, ZT - 1, 5))
    fl = fl.intersect(ext_spline(plat.buffer(-1), ZT - 1, 6))
    hc = hc.union(fl).intersect(clip)
    taper = (cq.Workplane("XZ").polyline([(20, ZT + p["HeelCup_H"]), (cut_x + 1, ZT + p["HeelCup_H_Front"]), (cut_x + 1, ZT + 200), (20, ZT + 200)]).close().extrude(-300).translate((0, -150, 0)))
    hc = hc.cut(taper)
    for q in m4[:3]:
        hc = hc.cut(csk(q[0], q[1], ZT + 3.0, 4.5, 8.5, 6))
    # 踝帶槽（選配）
    for sgn in (+1, -1):
        ye = y_edge(shoe, 30, sgn) + sgn * (FG + p["HeelCup_T"] / 2)
        hc = hc.cut(boxc(30 - 13, 30 + 13, ye - 6, ye + 6, ZT + 24, ZT + 29))
    parts["A1_U型後跟定位座"] = (hc, "A")
    # A2 可調式前腳掌（鞋頭）固定座
    t_in = shoe.buffer(FG, join_style=1)
    toe = ext_spline(shoe.buffer(FG + p["Toe_T"], join_style=1), ZT, p["Toe_H"]).cut(ext_spline(t_in, ZT - 1, p["Toe_H"] + 2))
    toe = toe.intersect(boxc(SL - 30, 500, -200, 200, ZT - 1, ZT + 100))
    t_fl = ext_spline(plat.buffer(-1), ZT, 3.0).cut(ext_spline(t_in, ZT - 1, 5)).intersect(boxc(SL - 8, 500, -40, 40, ZT - 1, ZT + 10))
    toe = toe.union(t_fl)
    for yq in (13.0, -13.0):
        toe = toe.cut(boxc(Xt - p["Toe_Adj"], Xt + p["Toe_Adj"], yq - 2.25, yq + 2.25, ZT - 1, ZT + 10))
        toe = toe.cut(cyl(Xt - p["Toe_Adj"], yq, ZT - 1, 4.5, 10)).cut(cyl(Xt + p["Toe_Adj"], yq, ZT - 1, 4.5, 10))
    parts["A2_前腳掌固定座(鞋頭擋塊)"] = (toe, "A")
    # A3 左右側限位（附魔鬼氈穿帶槽）
    for sgn, nm in ((+1, "外側"), (-1, "內側")):
        x0, x1 = Xg - p["Guide_Len"] / 2, Xg + p["Guide_Len"] / 2
        ye = y_edge_range(shoe, x0, x1, sgn) + sgn * FG
        w = boxc(x0, x1, *sorted([ye, ye + sgn * p["Guide_T"]]), ZT, ZT + p["Guide_H"])
        fl = boxc(x0, x1, *sorted([ye, ye + sgn * (p["Guide_T"] + 12)]), ZT, ZT + 3)
        gd = w.union(fl)
        gd = gd.cut(boxc(Xg - p["Strap_W"] / 2 - 1, Xg + p["Strap_W"] / 2 + 1, *sorted([ye - sgn, ye + sgn * 10]), ZT + 14, ZT + 19))
        for dx in (-15, 15):
            yc = ye + sgn * (p["Guide_T"] + 6) - sgn * (FG + p["Guide_T"] + 6 - g_off)
            gd = gd.cut(boxc(Xg + dx - 2.25, Xg + dx + 2.25, yc - p["Guide_Adj"], yc + p["Guide_Adj"], ZT - 1, ZT + 10))
            gd = gd.cut(cyl(Xg + dx, yc - p["Guide_Adj"], ZT - 1, 4.5, 10)).cut(cyl(Xg + dx, yc + p["Guide_Adj"], ZT - 1, 4.5, 10))
        parts[f"A3-{'L' if sgn > 0 else 'M'}_側限位({nm})"] = (gd, "A")
    # A4 魔鬼氈束帶（示意）
    for nm, X, z_top_ in (("前掌", Xg, ZT + p["Sole_Thickness"] + 32), ("中足", p["Midfoot_Strap_X"], ZT + p["Sole_Thickness"] + 48)):
        yo = y_edge(shoe, X, +1) + 7; yi = y_edge(shoe, X, -1) - 7
        pts = [(yi, ZT + 16), (yi * 0.85, z_top_ - 6), (0, z_top_), (yo * 0.85, z_top_ - 6), (yo, ZT + 16)]
        if nm == "中足":
            pts[0] = (y_edge(plat, X, -1) - 5.5, 3); pts[-1] = (y_edge(plat, X, +1) + 5.5, 3)
        try:
            sw = cq.Workplane("YZ", origin=(X, 0, 0)).spline(pts, includeCurrent=False).val()
            plane = cq.Plane(origin=sw.startPoint(), xDir=(1, 0, 0), normal=sw.tangentAt(0))
            prof = cq.Workplane(plane).rect(p["Strap_W"], 1.6)
            strap = prof.sweep(cq.Workplane().add(sw))
            parts[f"A4_{nm}魔鬼氈束帶"] = (strap, "STRAP")
        except Exception as ex:
            print("strap fail", ex)

    # ================= E. 後跟電控模組 =================
    bw = p["Box_Wall"]
    yin = y_box_in
    y0b, y1b = sorted([yin, yin + side * BW])
    z0, z1 = box_z0, box_z0 + BH - 2.5
    body = boxc(bx0, bx1, y0b, y1b, z0, z1)
    body = body.cut(boxc(bx0 + bw, bx1 - bw, y0b + bw, y1b - bw, z0 + bw, z1 + 1))
    # 外下緣倒角 10 mm（側傾時不觸地）
    yo = y1b if side > 0 else y0b
    ch = (cq.Workplane("YZ").polyline([(yo - side * 10, z0 - 1), (yo + side * 1, z0 - 1), (yo + side * 1, z0 + 10)]).close()
          .extrude(BL + 10).translate((bx0 - 5, 0, 0)))
    body = body.cut(ch)
    rail_zc = z0 + 14
    # 內側牆燕尾槽加厚條
    body = body.union(boxc(bx0, bx1, *sorted([yin, yin + side * 7]), rail_zc - 9, rail_zc + 9))
    # 托盤支撐條
    zt_ = z0 + bw + battery_h + 2
    for yy in (y0b + bw, y1b - bw - 2):
        body = body.union(boxc(bx0 + bw, bx1 - bw, yy, yy + 2, zt_ - 3, zt_))
    # 蓋板螺柱
    for xx in (bx0 + 7, bx1 - 7):
        for yy in (y0b + 7, y1b - 7):
            body = body.union(cyl(xx, yy, z0 + bw, 7, z1 - z0 - bw)).cut(cyl(xx, yy, z1 - 8, 4.0, 9))
    # 後牆：ESP32 USB、充電 USB；內側牆：FSR 線孔；燕尾槽
    esp_z = zt_ + 2 + p["Breadboard_Size"][2] + 6
    body = body.cut(boxc(bx0 - 1, bx0 + bw + 1, (y0b + y1b) / 2 - 6, (y0b + y1b) / 2 + 6, esp_z - 4, esp_z + 4))
    body = body.cut(boxc(bx0 - 1, bx0 + bw + 1, (y0b + y1b) / 2 - 6, (y0b + y1b) / 2 + 6, z0 + bw + 6, z0 + bw + 13))
    body = body.cut(boxc(bx0 + 25, bx0 + 38, *sorted([yin + side * BW - side * (bw + 1), yin + side * BW + side]), z1 - 18, z1 - 9.5))  # 電源開關
    ex = d["exit"][0]
    body = body.cut(cyl(ex, yin + side * 12, z0 - 1, 7.0, bw + 2))   # FSR 線材入口（底板，加防水套圈）
    dv = cq.Workplane("YZ").polyline([(0, -7), (0, 7), (-side * 4.0, 5), (-side * 4.0, -5)]).close().extrude(BL + 2).translate((bx0 - 1, 0, 0))
    body = body.cut(dv.translate((0, yin + side * 4.0, rail_zc)))
    parts["E1_電控盒體"] = (body, "E")
    lid = boxc(bx0, bx1, y0b, y1b, z1, z1 + 2.5)
    for xx in (bx0 + 7, bx1 - 7):
        for yy in (y0b + 7, y1b - 7):
            lid = lid.cut(csk(xx, yy, z1 + 2.5, 3.4, 6.5, 4))
    for k in range(6):
        lid = lid.cut(boxc(bx0 + 60 + k * 9, bx0 + 63 + k * 9, y0b + 15, y1b - 15, z1 - 1, z1 + 4))
    parts["E2_電控盒上蓋"] = (lid, "E")
    tray = boxc(bx0 + bw + 0.5, bx1 - bw - 0.5, y0b + bw + 0.3, y1b - bw - 0.3, zt_, zt_ + 2)
    parts["E3_麵包板托盤"] = (tray, "E")
    # 滑軌座（鎖於底座外側牆）
    rx0, rx1 = max(bx0 + 15, 5.0), bx0 + 125
    rail = ext_poly(sbox(rx0, min(0, yin), rx1, max(0, yin)).difference(plat.buffer(0.3)), 1.0, rail_zc + 10 - 1.0)
    rail = rail.union(dv.translate((0, yin + side * 4.0, rail_zc)).intersect(boxc(rx0, rx1, -500, 500, -50, 200)))
    d["rail_x"] = (rx0, rx1)
    # 鎖附孔（水平 M4 → 底座外牆熱熔螺母）
    for q in rail_boss:
        rail = rail.cut(cq.Workplane("XY").add(cq.Solid.makeCylinder(2.25, 40, cq.Vector(q[0], yin + side * 10, 6.0), cq.Vector(0, -side, 0))))
    # 線材通道（底座出線孔 → 滑軌座 → 盒底入口）
    rail = rail.cut(cq.Workplane("XY").add(cq.Solid.makeCylinder(3.2, 60, cq.Vector(ex, yin - side * 30, 6.5), cq.Vector(0, side, 0))))
    parts["E4_電控盒滑軌座"] = (rail, "E")
    # 電子元件（示意）
    bb = p["Breadboard_Size"]; es = p["ESP32_Size"]; bt = p["Battery_Size"]; cg = p["Charger_Size"]
    ymid = (y0b + y1b) / 2
    parts["E5_長條麵包板"] = (boxc(bx0 + bw + 1.5, bx0 + bw + 1.5 + bb[0], ymid - bb[1] / 2, ymid + bb[1] / 2, zt_ + 2, zt_ + 2 + bb[2]), "PCB_W")
    parts["E6_ESP32"] = (boxc(bx0 + bw + 2, bx0 + bw + 2 + es[0], ymid - es[1] / 2, ymid + es[1] / 2, zt_ + 2 + bb[2], zt_ + 2 + bb[2] + es[2]), "PCB")
    parts["E7_18650電池盒"] = (boxc(bx1 - bw - 3 - bt[0], bx1 - bw - 3, ymid - bt[1] / 2 + side * 12, ymid + bt[1] / 2 + side * 12, z0 + bw, z0 + bw + bt[2]), "BAT")
    parts["E8_充電升壓模組"] = (boxc(bx0 + bw + 4, bx0 + bw + 4 + cg[0], ymid - cg[1] / 2, ymid + cg[1] / 2, z0 + bw, z0 + bw + cg[2]), "PCB")
    d.update(box_z=(z0, z1 + 2.5), box_y=(y0b, y1b), tray_z=zt_, esp_z=esp_z, rail_zc=rail_zc)

    # ================= 布鞋（示意，不製作） =================
    sole = ext_spline(shoe, ZT, p["Sole_Thickness"])
    up0 = shoe.buffer(-3)
    up1 = affinity.scale(shoe.buffer(-14), 0.62, 0.72, origin=(0, 0)).buffer(0)
    up1 = affinity.translate(up1, 12, 0)
    n = 90
    w0 = cq.Wire.makePolygon([cq.Vector(x, y, ZT + p["Sole_Thickness"]) for x, y in resample(up0.exterior, n)], close=True)
    w1 = cq.Wire.makePolygon([cq.Vector(x, y, ZT + p["Sole_Thickness"] + p["Shoe_Upper_H"]) for x, y in resample(up1.exterior, n)], close=True)
    try:
        upper = cq.Workplane("XY").add(cq.Solid.makeLoft([w0, w1], True))
    except Exception:
        upper = ext_spline(up0, ZT + p["Sole_Thickness"], p["Shoe_Upper_H"] * 0.6)
    d["shoe_parts"] = {"Shoe_Sole": sole, "Shoe_Upper": upper}

    d["shoe"] = shoe; d["plat"] = plat; d["foot"] = foot_outline(p)
    return parts, d

MODULE_NAME = {"A": "A 布鞋固定機構", "B": "B 上層承載平台", "C": "C FSR 感測模組", "D": "D 底部基座", "E": "E 後跟電控模組"}

if __name__ == "__main__":
    parts, d = build(P)
    for k, (w, m) in parts.items():
        s = w.val() if isinstance(w, cq.Workplane) else w
        bb = s.BoundingBox()
        print(f"{k:28s} {bb.xlen:7.1f} x {bb.ylen:6.1f} x {bb.zlen:5.1f}  V={s.Volume()/1000:7.2f} cm3 valid={s.isValid()}")
    print({k: d[k] for k in ("S1", "S2", "Platform_Thickness", "BL", "BW", "BH", "Xg", "Xt")})
    if len(sys.argv) > 2 and sys.argv[1] == "--export":
        out = sys.argv[2]; os.makedirs(out, exist_ok=True)
        asm = cq.Assembly()
        for k, (w, m) in parts.items():
            cq.exporters.export(w, os.path.join(out, f"{k}.stl"), tolerance=0.05, angularTolerance=0.1)
            asm.add(w, name=k)
        asm.save(os.path.join(out, "FSR_Platform_Assembly.step"))
