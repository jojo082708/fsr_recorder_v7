"""ALICE 風格下肢外骨骼（單腳、左腳）— 換成 CubeMars AK70-10（髖）+ AK60-6 V1.1（膝），
連桿全部改 3D 列印（25×25 方管，取代 2020 鋁擠）。

座標：X 前、Y 外側（+）、Z 上；髖關節軸心在原點；連桿中心面 y = 0。
用法：
    python3 exo/exo_ak.py --export out/exo     # 每個列印件 STL + 整體 STEP + GLB
"""
import os, sys, json, math, argparse
import numpy as np
import cadquery as cq
from shapely.geometry import Point, Polygon, MultiPolygon, box as sbox
from shapely.ops import unary_union

# ------------------------------------------------------------------ 參數
# 馬達外形依 CubeMars 官網（Ø×長）；鎖孔 PCD / 數量為示意值，請以實物或官方 STEP 確認後改這裡。
MOTORS = {
    "AK70-10":   dict(D=89.0, H=50.25, flange_d=40.0, out_n=6, out_pcd=30.0, base_n=6, base_pcd=74.0,
                      bearing=(50, 65, 7), mass=621),
    "AK60-6":    dict(D=79.0, H=39.5,  flange_d=34.0, out_n=8, out_pcd=26.0, base_n=6, base_pcd=66.0,
                      bearing=(40, 52, 7), mass=368),
}
P = dict(
    HIP_MOTOR="AK70-10", KNEE_MOTOR="AK60-6",
    THIGH=420.0,          # 髖軸 → 膝軸（目前組裝位置；390–450，每格 15）
    SHANK=420.0,          # 膝軸 → 踝軸（390–450，每格 15）
    SEG_MIN=390.0,        # 連桿全插到底時的最短段長
    BOLT_FROM_MOUTH=(10.0, 25.0),   # 插槽上 2 顆 M6 距槽口
    PULL=(0.0, 15.0, 30.0),         # 每一端可拉出量
    ANKLE_TO_SOLE=68.0,
    LINK=25.0,            # 列印方管外寸
    LINK_BORE=11.0,       # 中心走線孔
    FIT=0.4,              # 方管插槽單邊間隙
    HOLE=6.4,             # M6 調整孔
    PITCH=15.0,           # 調整孔間距（同 ALICE：6 mm 孔、15 mm 間距）
    SOCKET=66.0,          # 插槽深度（拉出 30 mm 時仍有 2 顆螺絲吃到）
    CUP_WALL=4.0, CUP_FLOOR=4.0,
    PLATE_T=6.0,          # 葫蘆形側板厚
    SPOKE_T=5.0,          # 紅色三爪轉接件厚
    THIGH_CUFF_Z=-215.0, SHANK_CUFF_Z=-640.0,
    POSE_HIP=0.0, POSE_KNEE=0.0,   # 姿勢（度，屈曲為正），只影響組合圖
)


# ------------------------------------------------------------------ 幾何工具
def _wire_pts(ring):
    pts = list(ring.coords)[:-1]
    out = []
    for a, b in pts:
        if not out or math.hypot(a - out[-1][0], b - out[-1][1]) > 0.05:
            out.append((float(a), float(b)))
    while len(out) > 3 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= 0.05:
        out.pop()
    return out


def ext2d(poly, a0, a1, plane="xz"):
    """把 shapely 平面輪廓沿法向擠出。plane="xz"：輪廓座標 (x,z)、沿 y 從 a0 到 a1。
    plane="xy"：輪廓 (x,y)、沿 z。"""
    poly = poly.simplify(0.02).buffer(0)
    polys = list(poly.geoms) if isinstance(poly, MultiPolygon) else [poly]
    out = None
    for pg in polys:
        s = cq.Workplane("XY").polyline(_wire_pts(pg.exterior)).close().extrude(a1 - a0)
        for it in pg.interiors:
            s = s.cut(cq.Workplane("XY").polyline(_wire_pts(it)).close().extrude(a1 - a0))
        out = s if out is None else out.union(s)
    if plane == "xy":
        return out.translate((0, 0, a0))
    # XY→XZ：繞 X 轉 +90°：(x,y,z)→(x,−z,y)，擠出 z∈[0,t] → y∈[−t,0]
    return out.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, a1, 0))


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def cyl(r, a0, a1, axis="y", c=(0, 0)):
    """沿軸的圓柱；c 為另兩軸座標。axis=y → c=(x,z)；axis=x → c=(y,z)；axis=z → c=(x,y)。"""
    if axis == "y":
        return cq.Workplane(cq.Solid.makeCylinder(r, a1 - a0, cq.Vector(c[0], a0, c[1]), cq.Vector(0, 1, 0)))
    if axis == "x":
        return cq.Workplane(cq.Solid.makeCylinder(r, a1 - a0, cq.Vector(a0, c[0], c[1]), cq.Vector(1, 0, 0)))
    return cq.Workplane(cq.Solid.makeCylinder(r, a1 - a0, cq.Vector(c[0], c[1], a0), cq.Vector(0, 0, 1)))


def circ(x, z, r):
    return Point(x, z).buffer(r, quad_segs=48)


def gourd(R1, R2, L2):
    """葫蘆形：上圓 R1（軸心）+ 下圓 R2（在 z=−L2）取凸包。"""
    return unary_union([circ(0, 0, R1), circ(0, -L2, R2)]).convex_hull


def slot(p0, p1, r):
    from shapely.geometry import LineString
    return LineString([p0, p1]).buffer(r, quad_segs=24)


def rotate_y(wp, deg, about):
    """繞平行 Y 軸、經過 about=(x,z) 的軸旋轉；屈曲為正（腳往後擺）。"""
    return wp.rotate((about[0], 0, about[1]), (about[0], 1, about[1]), deg)


# ------------------------------------------------------------------ 零件
def motor(M):
    """AK 馬達（示意外形）：軸沿 y，輸出端在 +y（外側）。中心面 y=0。"""
    R, H = M["D"] / 2, M["H"]
    y0, y1 = -H / 2, H / 2
    body = cyl(R, y0 + 3, y1 - 3)
    body = body.union(cyl(R - 2.5, y0, y0 + 3)).union(cyl(R - 2.5, y1 - 3, y1))
    # 散熱環溝
    for k in range(3):
        yy = y0 + 10 + k * (H - 20) / 2
        body = body.cut(cyl(R + 1, yy - 0.8, yy + 0.8).cut(cyl(R - 1.2, yy - 1, yy + 1)))
    flange = cyl(M["flange_d"] / 2, y1, y1 + 2.0)
    for i in range(M["out_n"]):
        a = 2 * math.pi * i / M["out_n"]
        flange = flange.cut(cyl(1.6, y1 - 1, y1 + 3, c=(M["out_pcd"] / 2 * math.cos(a), M["out_pcd"] / 2 * math.sin(a))))
    flange = flange.cut(cyl(5.0, y1 - 1, y1 + 3))
    # 後蓋（黑）＋ 接頭座
    cap = cyl(R - 6, y0 - 1.2, y0)
    conn = box(-10, 10, y0 + 4, y0 + 18, R - 2, R + 6)
    return dict(body=body, flange=flange, cap=cap.union(conn))


def joint(M, upper="socket", tag="K"):
    """一個關節：定子杯（接上段）+ 輸出軛（兩片葫蘆側板 + 下夾座，接下段）+ 三爪轉接 + 軸承。
    回傳 dict(name → (wp, material))，軸心在原點。"""
    L, F, S = P["LINK"], P["FIT"], P["SOCKET"]
    R, H = M["D"] / 2, M["H"]
    Ri, Ro = R + 0.4, R + P["CUP_WALL"]
    fy = -H / 2 - P["CUP_FLOOR"]           # 杯底外側面
    cy1 = H / 2 - 2.0                      # 杯口
    bi, bo, bw = M["bearing"]
    R1 = Ro + 9.0                          # 側板上圓
    L2 = Ro + 32.0                         # 下圓中心距
    R2 = 25.0
    t = P["PLATE_T"]
    yo0 = H / 2 + 1.0                      # 外側板內面
    yo1 = yo0 + t
    yi1 = fy - 2.0                         # 內側板外面
    yi0 = yi1 - t
    parts = {}

    # --- 定子杯
    cup = cyl(Ro, fy, cy1).cut(cyl(Ri, fy + P["CUP_FLOOR"], cy1 + 1))
    hub = cyl(bi / 2, yi0 - 1.0, fy)       # 軸承內圈座（往內側凸）
    cup = cup.union(hub)
    cup = cup.cut(cyl(9.0, yi0 - 2, fy + P["CUP_FLOOR"] + 1))   # 中心出線孔
    for i in range(M["base_n"]):
        a = 2 * math.pi * (i + 0.5) / M["base_n"]
        cx, cz = M["base_pcd"] / 2 * math.cos(a), M["base_pcd"] / 2 * math.sin(a)
        if math.hypot(cx, cz) < bi / 2 - 3:
            cup = cup.cut(cyl(1.7, yi0 - 2, fy + P["CUP_FLOOR"] + 1, c=(cx, cz)))
        else:
            cup = cup.cut(cyl(1.7, fy - 1, fy + P["CUP_FLOOR"] + 1, c=(cx, cz)))
            cup = cup.cut(cyl(3.0, fy - 1, fy + 1.0, c=(cx, cz)))
    # 上方插槽座（接大腿連桿）或髖支架介面
    sx = L + 2 * F + 10
    ytop0, ytop1 = fy, cy1
    if upper == "socket":
        z0, z1 = Ro - 8, Ro + S + 4
        blk = box(-sx / 2, sx / 2, ytop0, ytop1, z0, z1).edges("|Z").fillet(4)
        cup = cup.union(blk).cut(cyl(Ri, fy + P["CUP_FLOOR"], cy1 + 1))
        cup = cup.cut(box(-(L / 2 + F), L / 2 + F, -(L / 2 + F), L / 2 + F, Ro + 4, z1 + 1))
        for b in P["BOLT_FROM_MOUTH"]:
            cup = cup.cut(cyl(P["HOLE"] / 2, -sx, sx, axis="x", c=(0, z1 - b)))
        cup = cup.cut(box(-5, 5, -5, 5, Ro - 10, Ro + 6))           # 出線
    parts[f"{tag}_定子杯"] = (cup, "PRINT")

    # --- 軸承
    brg = cyl(bo / 2, yi0, yi0 + bw).cut(cyl(bi / 2, yi0 - 1, yi0 + bw + 1))
    parts[f"{tag}_軸承{bi}x{bo}x{bw}"] = (brg, "STEEL")

    # --- 葫蘆側板（外 / 內）
    g = gourd(R1, R2, L2)
    cut_l = slot((-R1 * 0.55, -L2 * 0.62), (-R2 * 0.35, -L2 * 0.98), 5.5)
    cut_r = slot((R1 * 0.55, -L2 * 0.62), (R2 * 0.35, -L2 * 0.98), 5.5)
    tri = Polygon([(-9, -Ro - 6), (9, -Ro - 6), (0, -L2 + 4)]).buffer(3)
    lighten = unary_union([cut_l, cut_r, tri])
    bolt_pts = [(-(R2 - 8), -L2), (R2 - 8, -L2), (0, -L2 - (R2 - 8))]
    small = unary_union([circ(x, z, 1.7) for x, z in bolt_pts])
    # 角度限位（扇形孔外圈螺絲）＋ 外圈 4 顆鎖三爪
    ang = [90, 210, 330]
    Rs = M["flange_d"] / 2 + 21
    spoke_holes = unary_union([circ(Rs * math.cos(math.radians(a)), Rs * math.sin(math.radians(a)), 1.7) for a in ang])
    rim_holes = unary_union([circ((R1 - 5) * math.cos(math.radians(a)), (R1 - 5) * math.sin(math.radians(a)), 1.7)
                             for a in (45, 135)])
    outer = g.difference(circ(0, 0, M["flange_d"] / 2 + 2.5)).difference(lighten).difference(small)
    outer = outer.difference(spoke_holes).difference(rim_holes)
    inner = g.difference(circ(0, 0, bo / 2)).difference(lighten).difference(small).difference(rim_holes)
    po = ext2d(outer, yo0, yo1)
    pi_ = ext2d(inner, yi0, yi1)
    # 內側板軸承座加厚環
    pi_ = pi_.union(cyl(bo / 2 + 5, yi0 - 3, yi0).cut(cyl(bo / 2 - 2, yi0 - 4, yi0 + 1)))
    parts[f"{tag}_外側板"] = (po, "PRINT")
    parts[f"{tag}_內側板"] = (pi_, "PRINT")

    # --- 下夾座（兩片側板之間，接下段連桿）
    zt = -Ro - 3.0
    zb = -Ro - 3.0 - S - 6.0               # 槽口（往下開）
    zp = -L2 - R2 + 6                      # 側板下緣附近
    clamp = box(-R2 + 1, R2 - 1, yi1, yo0, zp, zt).edges("|Y").fillet(5)
    clamp = clamp.union(box(-20, 20, -20, 20, zb, zp + 8).edges("|Z").fillet(4))
    clamp = clamp.cut(cyl(Ro + 3.0, yi1 - 1, yo0 + 1))
    clamp = clamp.cut(box(-(L / 2 + F), L / 2 + F, -(L / 2 + F), L / 2 + F, zb - 1, zb + S))
    for b in P["BOLT_FROM_MOUTH"]:
        clamp = clamp.cut(cyl(P["HOLE"] / 2, -R2 - 1, R2 + 1, axis="x", c=(0, zb + b)))
    for x, z in bolt_pts:     # 側板鎖固（M3 熱熔螺母）
        clamp = clamp.cut(cyl(1.7, yi1 - 1, yo0 + 1, c=(x, z)))
    clamp = clamp.cut(box(-5.5, 5.5, -6, 6, zb + S - 1, zt + 1))   # 出線
    parts[f"{tag}_下夾座"] = (clamp, "PRINT")

    # --- 三爪轉接（紅）：中心鎖馬達輸出盤，三爪鎖外側板
    hub_r = M["flange_d"] / 2 + 1.5
    arms = unary_union([slot((0, 0), (Rs * math.cos(math.radians(a)), Rs * math.sin(math.radians(a))), 6.0) for a in ang])
    sp2 = unary_union([arms, circ(0, 0, hub_r + 3)]).difference(spoke_holes)
    for i in range(M["out_n"]):
        a = 2 * math.pi * i / M["out_n"]
        sp2 = sp2.difference(circ(M["out_pcd"] / 2 * math.cos(a), M["out_pcd"] / 2 * math.sin(a), 1.7))
    sp2 = sp2.difference(circ(0, 0, 5.0))
    spoke = ext2d(sp2, yo1, yo1 + P["SPOKE_T"])
    boss = ext2d(circ(0, 0, M["flange_d"] / 2 + 1.5).difference(circ(0, 0, 5.0)), H / 2 + 2.0, yo1)
    for i in range(M["out_n"]):
        a = 2 * math.pi * i / M["out_n"]
        boss = boss.cut(cyl(1.7, H / 2, yo1 + 1, c=(M["out_pcd"] / 2 * math.cos(a), M["out_pcd"] / 2 * math.sin(a))))
    parts[f"{tag}_三爪轉接"] = (spoke.union(boss), "RED")

    m = motor(M)
    parts[f"{tag}_{[k for k, v in MOTORS.items() if v is M][0]}_本體"] = (m["body"], "MOTOR")
    parts[f"{tag}_馬達輸出盤"] = (m["flange"], "MOTOR_D")
    parts[f"{tag}_馬達後蓋"] = (m["cap"], "BLACK")
    info = dict(R1=R1, R2=R2, L2=L2, Ro=Ro, zb=zb, zt=zt, yi0=yi0, yo1=yo1 + P["SPOKE_T"], fy=fy, cy1=cy1,
                sock_top=Ro + S + 4 if upper == "socket" else None)
    return parts, info


def link(length, holes_top, holes_bot, name):
    """3D 列印方管連桿（沿 z，頂端在 z=0），中心走線孔、兩端 M6 調整孔（沿 x）。"""
    L = P["LINK"]
    s = box(-L / 2, L / 2, -L / 2, L / 2, -length, 0).edges("|Z").fillet(2.0)
    s = s.cut(cyl(P["LINK_BORE"] / 2, -length - 1, 1, axis="z"))
    for zz in holes_top + holes_bot:
        s = s.cut(cyl(P["HOLE"] / 2, -L, L, axis="x", c=(0, zz)))
    return s


def cuff(z, Rc, legc, height, tag):
    """綁帶夾座（套在連桿上、可上下滑動）+ 弧形護墊（灰）＋ 紅色背板。"""
    L, F = P["LINK"], P["FIT"]
    blk = box(-20, 20, -20, 20, z - 28, z + 28).edges("|Z").fillet(4)
    blk = blk.cut(box(-(L / 2 + F), L / 2 + F, -(L / 2 + F), L / 2 + F, z - 30, z + 30))
    for dz in (-7.5, 7.5):
        blk = blk.cut(cyl(P["HOLE"] / 2, -21, 21, axis="x", c=(0, z + dz)))
    cy = -legc
    def sector(r0, r1, a0, a1):
        ring = Point(0, cy).buffer(r1, quad_segs=96).difference(Point(0, cy).buffer(r0, quad_segs=96))
        R = r1 * 2
        wedge = Polygon([(0, cy)] + [(R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
                                     for a in np.linspace(a0, a1, 40)])
        return ring.intersection(wedge)
    pad = ext2d(sector(Rc, Rc + 6, -15, 96), z - height / 2, z + height / 2, plane="xy")
    back = ext2d(sector(Rc + 6, Rc + 10, -19, 99), z - height / 2 - 4, z + height / 2 + 4, plane="xy")
    # 綁帶槽
    for a in (20,):
        x = (Rc + 8) * math.cos(math.radians(a)); y = cy + (Rc + 8) * math.sin(math.radians(a))
        back = back.cut(box(x - 6, x + 6, y - 6, y + 6, z - 22, z + 22).rotate((x, y, 0), (x, y, 1), a))
    pad = pad.cut(box(-21, 21, -21, 21, z - 60, z + 60))
    back = back.cut(box(-20.5, 20.5, -20.5, 20.5, z - 60, z + 60)).union(box(-20, 20, -24, -20, z - 28, z + 28))
    return {f"{tag}_夾座": (blk, "PRINT"), f"{tag}_護墊": (pad, "PAD"), f"{tag}_紅色背板": (back, "RED")}


def build(p=P):
    MH, MK = MOTORS[p["HIP_MOTOR"]], MOTORS[p["KNEE_MOTOR"]]
    parts = {}
    zK, zA = -p["THIGH"], -p["THIGH"] - p["SHANK"]

    # ---------------- 髖關節
    hip, hi = joint(MH, upper="pelvis", tag="H髖")
    Ro = hi["Ro"]
    # 髖支架：杯頂 → 腰背帶 ＋ 電控盒座
    yb0, yb1 = hi["fy"], hi["cy1"]
    br = box(-24, 24, yb0, yb1, Ro - 10, Ro + 70).edges("|Z").fillet(5)
    br = br.cut(cyl(Ro - 0.6, yb0 - 1, yb1 + 1))
    br = br.cut(box(-6, 6, -6, 6, Ro - 12, Ro + 72))        # 走線
    # 往後延伸到電控盒
    br = br.union(box(-hi["R1"] - 66, -20, yb0, yb1, Ro + 46, Ro + 70).edges("|Y").fillet(4))
    hip["H髖_定子杯"] = (hip["H髖_定子杯"][0].union(br), "PRINT")
    # 腰背帶（四分之一圈，繞身體後方）
    zc0, zc1 = Ro + 52, Ro + 112
    cyp = -185.0
    def band(r0, r1, a0, a1):
        ring = Point(0, cyp).buffer(r1, quad_segs=128).difference(Point(0, cyp).buffer(r0, quad_segs=128))
        R = r1 * 2
        wedge = Polygon([(0, cyp)] + [(R * math.cos(math.radians(a)), cyp + R * math.sin(math.radians(a)))
                                      for a in np.linspace(a0, a1, 60)])
        return ring.intersection(wedge)
    lumbar = ext2d(band(185 - 2, 185 + 4, 100, 182), zc0, zc1, plane="xy")
    lumbar = lumbar.union(box(-40, 0, -8, 8, zc0, zc1).edges("|Z").fillet(3))
    hip["H髖_腰背支架"] = (lumbar.union(box(-30, 0, yb0, 6, Ro + 46, zc0 + 4)), "PRINT")
    hip["H髖_腰背軟墊"] = (ext2d(band(185 - 22, 185 - 2, 104, 186), zc0 - 6, zc1 + 6, plane="xy"), "PAD")
    # 電控盒（白，示意 MCU + CAN + 電池）
    bx0, bx1 = -hi["R1"] - 66, -hi["R1"] - 6
    ebox = box(bx0, bx1, yb0 - 4, yb1 + 8, -40, Ro + 46).edges().fillet(8)
    hip["H髖_電控盒"] = (ebox, "WHITE")

    # ---------------- 連桿：插到底＝最短 SEG_MIN；兩端各可拉出 0/15/30
    knee, ki = joint(MK, upper="socket", tag="K膝")
    S = P["SOCKET"]
    hole_from_end = sorted({S - 2 - b - d for b in P["BOLT_FROM_MOUTH"] for d in P["PULL"]})

    def pulls(seg):
        e = seg - P["SEG_MIN"]
        assert 0 <= e <= 2 * max(P["PULL"]) and abs(e / P["PITCH"] - round(e / P["PITCH"])) < 1e-6, \
            f"段長需為 {P['SEG_MIN']:.0f}–{P['SEG_MIN'] + 2 * max(P['PULL']):.0f}、每格 {P['PITCH']:.0f}"
        d1 = P["PITCH"] * math.ceil(e / P["PITCH"] / 2)
        return d1, e - d1

    # 大腿：上端插髖下夾座（槽口朝下），下端插膝杯插槽（槽口朝上）
    up_closed = hi["zb"] + S - 2                       # 上插槽底（留 2 mm）相對髖軸
    dn_closed = ki["sock_top"] - S + 2                 # 下插槽底，相對膝軸
    Lt = (up_closed) - (-P["SEG_MIN"] + dn_closed)
    d1, d2 = pulls(p["THIGH"])
    top = up_closed - d1
    thigh = link(Lt, [-h for h in hole_from_end], [-(Lt - h) for h in hole_from_end], "thigh").translate((0, 0, top))
    parts["T_大腿連桿"] = (thigh, "PRINT2")
    parts.update(cuff(P["THIGH_CUFF_Z"], 72, 92, 95, "T_大腿綁帶"))

    # 小腿：上端插膝下夾座，下端插踝上座
    ank_top = zA + 20 + S
    up_s = zK + ki["zb"] + S - 2
    Ls = (ki["zb"] + S - 2) - (-P["SEG_MIN"] + 20 + 2)
    e1, e2 = pulls(p["SHANK"])
    top_s = up_s - e1
    shank = link(Ls, [-h for h in hole_from_end], [-(Ls - h) for h in hole_from_end], "shank").translate((0, 0, top_s))
    parts["S_小腿連桿"] = (shank, "PRINT2")
    parts.update(cuff(P["SHANK_CUFF_Z"], 54, 74, 80, "S_小腿綁帶"))
    h_top = h_bot = hs_top = hs_bot = hole_from_end

    L, F = P["LINK"], P["FIT"]
    ank = box(-21, 21, -20, 20, zA - 4, ank_top).edges("|Z").fillet(4)
    ank = ank.cut(box(-(L / 2 + F), L / 2 + F, -(L / 2 + F), L / 2 + F, ank_top - P["SOCKET"], ank_top + 1))
    for bb in P["BOLT_FROM_MOUTH"]:
        ank = ank.cut(cyl(P["HOLE"] / 2, -22, 22, axis="x", c=(0, ank_top - bb)))
    ank = ank.union(cyl(16, -20, 20, c=(0, zA))).cut(cyl(4.2, -21, 21, c=(0, zA)))
    ank = ank.cut(box(-17, 17, -6.4, 6.4, zA - 20, zA + 12).cut(box(-30, 30, -30, 30, zA + 12, zA + 13)))
    parts["A_踝上座"] = (ank, "PRINT")
    # 被動踝：叉臂 + 腳板
    zs = zA - P["ANKLE_TO_SOLE"]
    fork = cyl(15, -6, 6, c=(0, zA)).union(box(-15, 15, -6, 6, zs + 6, zA))
    fork = fork.cut(cyl(4.2, -7, 7, c=(0, zA)))
    fork = fork.union(box(-35, 35, -60, 6, zs + 6, zs + 14).edges("|Z").fillet(6))
    parts["A_踝擺臂"] = (fork, "PRINT")
    sole2d = unary_union([Point(95, -78).buffer(48, quad_segs=48), Point(-35, -75).buffer(40, quad_segs=48)]).convex_hull
    sole = ext2d(sole2d, zs, zs + 6, plane="xy")
    rim = ext2d(sole2d.buffer(3).difference(sole2d), zs - 1, zs + 7, plane="xy")
    heel = ext2d(Point(-35, -75).buffer(48, quad_segs=48).difference(Point(-35, -75).buffer(42, quad_segs=48))
                 .intersection(sbox(-100, -140, -25, 20)), zs + 6, zs + 50, plane="xy")
    parts["A_腳板"] = (sole.union(heel).cut(box(-36, 36, -61, 7, zs + 5.9, zs + 15)), "PAD")
    parts["A_腳板紅邊"] = (rim, "RED")
    parts["A_M8踝軸"] = (cyl(4.0, -24, 24, c=(0, zA)), "STEEL")

    # ---------------- 姿勢
    def place(dct, dz, extra_rot=()):
        out = {}
        for k, (w, m) in dct.items():
            w = w.translate((0, 0, dz))
            for deg, about in extra_rot:
                w = rotate_y(w, deg, about)
            out[k] = (w, m)
        return out
    hipR = (P["POSE_HIP"], (0, 0))
    knR = (-P["POSE_KNEE"], (0, zK))
    # 髖：杯/支架/盒/馬達不動，輸出軛隨大腿轉；膝：杯隨大腿，軛隨小腿
    rot_h_out = [hipR]
    for k, v in hip.items():
        moving = any(s in k for s in ("外側板", "內側板", "下夾座", "三爪", "輸出盤"))
        parts[k] = (rotate_y(v[0], *hipR) if moving else v[0], v[1])
    kn = place(knee, zK)
    for k, (w, m) in kn.items():
        moving = any(s in k for s in ("外側板", "內側板", "下夾座", "三爪", "輸出盤"))
        if moving:
            w = rotate_y(w, *knR)
        parts[k] = (rotate_y(w, *hipR), m)
    for k in list(parts):
        if k[0] in "TSA" and k[1] == "_":
            w, m = parts[k]
            if k[0] in "SA":
                w = rotate_y(w, *knR)
            parts[k] = (rotate_y(w, *hipR), m)
    D = dict(zK=zK, zA=zA, zs=zs, thigh_len=Lt, shank_len=Ls, hip=hi, knee=ki,
             thigh_holes=(h_top, h_bot), shank_holes=(hs_top, hs_bot))
    return parts, D


# ------------------------------------------------------------------ 輸出
COLORS = {"PRINT": (0.30, 0.30, 0.32), "PRINT2": (0.36, 0.36, 0.39), "RED": (0.80, 0.12, 0.12),
          "MOTOR": (0.72, 0.74, 0.77), "MOTOR_D": (0.55, 0.57, 0.60), "BLACK": (0.08, 0.08, 0.09),
          "STEEL": (0.82, 0.83, 0.85), "PAD": (0.16, 0.16, 0.17), "WHITE": (0.93, 0.93, 0.92)}
PRINTABLE = {"PRINT", "PRINT2", "RED", "PAD", "WHITE"}


def as_mesh(wp, tol=0.05, ang=0.2):
    import trimesh
    shape = wp.val() if len(wp.vals()) == 1 else cq.Compound.makeCompound(wp.vals())
    v, f = shape.tessellate(tol, ang)
    return trimesh.Trimesh(np.array([(p.x, p.y, p.z) for p in v]), np.array(f), process=True)


def explode_vec(k):
    """爆炸圖位移方向（模型座標，乘上 explode 係數）。只拆關節。"""
    if not (k.startswith("H髖") or k.startswith("K膝")):
        return [0, 0, 0]
    order = [("軸承", -1.6), ("內側板", -2.4), ("下夾座", -0.8), ("後蓋", 0.9), ("本體", 0.9), ("輸出盤", 0.9),
             ("外側板", 2.0), ("三爪", 3.0)]
    for key, f in order:
        if key in k:
            return [0, f, 0]
    return [0, 0, 0]


def export(out):
    import trimesh
    os.makedirs(os.path.join(out, "stl"), exist_ok=True)
    parts, D = build(P)
    scene = trimesh.Scene()
    meta = {}
    assy = cq.Assembly()
    for k, (w, m) in parts.items():
        mesh = as_mesh(w)
        c = COLORS[m]
        mesh.visual.face_colors = np.tile((np.array(c + (1,)) * 255).astype(np.uint8), (len(mesh.faces), 1))
        scene.add_geometry(mesh, node_name=k, geom_name=k)
        meta[k] = dict(mat=m, color=c, vol_cm3=round(mesh.volume / 1000, 1), explode=explode_vec(k))
        if m in PRINTABLE:
            mesh.export(os.path.join(out, "stl", f"{k}.stl"))
        assy.add(w, name=k, color=cq.Color(*c))
    scene.export(os.path.join(out, "exo_ak_left.glb"))
    assy.save(os.path.join(out, "exo_ak_left.step"))
    D2 = D
    json.dump(dict(parts=meta, dims=D2, params=P, motors=MOTORS), open(os.path.join(out, "meta.json"), "w"),
              ensure_ascii=False, indent=1, default=float)
    print("parts:", len(parts), "thigh link", round(D["thigh_len"], 1), "shank link", round(D["shank_len"], 1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", default="out/exo")
    ap.add_argument("--hip", type=float, default=None)
    ap.add_argument("--knee", type=float, default=None)
    a = ap.parse_args()
    if a.hip is not None: P["POSE_HIP"] = a.hip
    if a.knee is not None: P["POSE_KNEE"] = a.knee
    export(a.export)
