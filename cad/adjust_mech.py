"""
可調式感測座（XY 燕尾滑座 + 榫銷定位 + 刻度）— 幾何定義
局部座標：原點 = 感測器刻度 0 點（腳印量得的大拇趾球 / 腳跟中心），z 為絕對高度（底板面 z=15）。
"""
import math
import cadquery as cq

M = dict(
    Floor=15.0, Plate_Z0=11.0,         # 滑座板 z 11→15，與底板齊平
    Trench_Z0=3.0,                      # 下方深槽（導筒行程區）底
    Car_L=50.0, Car_HalfW=29.0,         # X 滑座 長 50、半寬 29
    Dove=60.0,                          # 燕尾角（度）
    Slot_W=28.0, Tube_OD=27.0,          # 滑座上 Y 向長槽（導筒在其中左右滑動）
    Y_Range=8.0,                        # Y 調整 ±8
    Ledge_Y=25.5, Pin_D=3.0, Pin_Head_D=5.0, Pin_Head_T=1.0, Pin_Len=9.0, Pitch=5.0,
    Ring_D=42.0, Ring_T=3.0,            # 凸環：高出底板 3
    YPin_X=17.0,                        # 凸環 Y 向定位銷孔位置
    Cap_L=10.0,                         # 前端燕尾端塞（裝入滑座後塞入）
)

def dovetail_profile(half_w_top, z0, z1, ang):
    d = (z1 - z0) / math.tan(math.radians(ang))
    return [(-(half_w_top + d), z0), (half_w_top + d, z0), (half_w_top, z1), (-half_w_top, z1)]

def carriage(m=M, xr=(-25, 25)):
    """X 滑座：燕尾邊、Y 向長槽、X 定位銷孔（兩側錯開 2.5）、Y 卯孔列、Y 刻度"""
    L, hw = m["Car_L"], m["Car_HalfW"]
    prof = dovetail_profile(hw, m["Plate_Z0"], m["Floor"], m["Dove"])
    c = cq.Workplane("YZ").polyline(prof).close().extrude(L).translate((-L / 2, 0, 0))
    sl = m["Slot_W"] / 2; sy = m["Tube_OD"] / 2 + m["Y_Range"] + 0.5
    c = c.cut(cq.Workplane("XY").box(2 * sl, 2 * sy, 10).translate((0, 0, 13)).edges("|Z").fillet(sl - 0.01))
    for y, dx in ((m["Ledge_Y"], 0.0), (-m["Ledge_Y"], 0.0)):
        c = c.cut(cq.Workplane("XY").workplane(offset=m["Plate_Z0"] - 1).center(dx, y).circle(m["Pin_D"] / 2 + 0.1).extrude(6))
        c = c.cut(cq.Workplane("XY").workplane(offset=m["Floor"] - m["Pin_Head_T"]).center(dx, y).circle(m["Pin_Head_D"] / 2 + 0.1).extrude(2))
    # Y 卯孔：+X 側 y = 0, ±5；−X 側 y = ±2.5, ±7.5
    for k in range(-2, 3):
        for x, y in ((m["YPin_X"], k * 5.0), (-m["YPin_X"], k * 5.0 + 2.5)):
            if abs(y) <= m["Y_Range"] + 0.01:
                c = c.cut(cq.Workplane("XY").workplane(offset=m["Floor"] - 3.5).center(x, y).circle(m["Pin_D"] / 2 + 0.1).extrude(4))
    return c

def ring_cartridge(m=M, y=0.0):
    """凸環 + 導筒（感測匣殼簡化示意，內部同 v17 感測匣）"""
    r = cq.Workplane("XY").workplane(offset=m["Floor"]).center(0, y).circle(m["Ring_D"] / 2).extrude(m["Ring_T"])
    r = r.edges(">Z").chamfer(1.0)
    r = r.cut(cq.Workplane("XY").workplane(offset=m["Floor"] + m["Ring_T"] - 0.8).center(0, y).circle(21.4 / 2).extrude(2))
    r = r.cut(cq.Workplane("XY").workplane(offset=m["Floor"] - 1).center(0, y).circle(22.4 / 2).extrude(m["Ring_T"] + 0.2))
    t = cq.Workplane("XY").workplane(offset=m["Trench_Z0"] + 0.2).center(0, y).circle(m["Tube_OD"] / 2).extrude(m["Floor"] - m["Trench_Z0"] - 0.2)
    t = t.cut(cq.Workplane("XY").workplane(offset=m["Trench_Z0"]).center(0, y).circle(22.4 / 2).extrude(13))
    r = r.union(t)
    for x in (m["YPin_X"], -m["YPin_X"]):
        r = r.cut(cq.Workplane("XY").workplane(offset=m["Floor"] - 1).center(x, y).circle(m["Pin_D"] / 2 + 0.1).extrude(5))
        r = r.cut(cq.Workplane("XY").workplane(offset=m["Floor"] + m["Ring_T"] - m["Pin_Head_T"]).center(x, y).circle(m["Pin_Head_D"] / 2 + 0.1).extrude(2))
    # 指標刻痕（+X 邊）
    r = r.cut(cq.Workplane("XY").workplane(offset=m["Floor"] + m["Ring_T"] - 0.6).polyline([(m["Ring_D"] / 2 + 0.5, y), (m["Ring_D"] / 2 - 3, y - 1.5), (m["Ring_D"] / 2 - 3, y + 1.5)]).close().extrude(1))
    tpu = cq.Workplane("XY").workplane(offset=8.4).center(0, y).circle(11).extrude(m["Floor"] + m["Ring_T"] + 0.3 - 8.4)
    return r, tpu

def pin(m=M, x=0.0, y=0.0, ztop=None):
    ztop = m["Floor"] if ztop is None else ztop
    p = cq.Workplane("XY").workplane(offset=ztop - m["Pin_Len"]).center(x, y).circle(m["Pin_D"] / 2).extrude(m["Pin_Len"])
    return p.union(cq.Workplane("XY").workplane(offset=ztop - m["Pin_Head_T"]).center(x, y).circle(m["Pin_Head_D"] / 2).extrude(m["Pin_Head_T"]))

def floor_block(m=M, xr=(-25, 25), size=(150, 90)):
    """底板局部（示意）：燕尾槽 + 兩側台階 + 深槽 + X 卯孔列 + 前端端塞口"""
    L, hw = m["Car_L"], m["Car_HalfW"]
    x0, x1 = xr[0] - L / 2, xr[1] + L / 2 + m["Cap_L"]
    b = cq.Workplane("XY").box(size[0], size[1], m["Floor"], centered=(True, True, False)).translate(((x0 + x1) / 2, 0, 0))
    prof = dovetail_profile(hw + 0.2, m["Plate_Z0"], m["Floor"], m["Dove"])
    groove = cq.Workplane("YZ").polyline(prof).close().extrude(x1 - x0).translate((x0, 0, 0))
    b = b.cut(groove)
    tw = m["Tube_OD"] / 2 + m["Y_Range"] + 1.0
    tx0, tx1 = xr[0] - m["Slot_W"] / 2 - 1, xr[1] + m["Slot_W"] / 2 + 1
    b = b.cut(cq.Workplane("XY").box(tx1 - tx0, 2 * tw, m["Plate_Z0"] - m["Trench_Z0"] + 0.01).translate(((tx0 + tx1) / 2, 0, (m["Plate_Z0"] + m["Trench_Z0"]) / 2)))
    k0, k1 = int(math.floor(xr[0] / 5)), int(math.ceil(xr[1] / 5))
    for k in range(k0, k1 + 1):
        for y, x in ((m["Ledge_Y"], k * 5.0), (-m["Ledge_Y"], k * 5.0 + 2.5)):
            if xr[0] - 0.01 <= x <= xr[1] + 0.01:
                b = b.cut(cq.Workplane("XY").workplane(offset=m["Plate_Z0"] - 5).center(x, y).circle(m["Pin_D"] / 2 + 0.1).extrude(5.1))
    return b, (x0, x1)

def end_cap(m=M, x_start=0.0):
    prof = dovetail_profile(m["Car_HalfW"], m["Plate_Z0"], m["Floor"], m["Dove"])
    c = cq.Workplane("YZ").polyline(prof).close().extrude(m["Cap_L"]).translate((x_start, 0, 0))
    return c
