"""從 v15 腳底件網格量出重建托盤所需的 2D 輪廓（v15 座標），存成 v15_profiles.json。
系統 python 執行：python3 textcad/tray/extract_v15_profiles.py
"""
import os, sys, json
import numpy as np, trimesh, manifold3d as m3
from shapely.geometry import Polygon, MultiPolygon, Point, box
from shapely.ops import unary_union
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../../cad"))
import afo_v17 as A

mesh = trimesh.load(os.path.join(HERE, "../../cad/data/v15/AFO_foot.stl"))
M = A.to_manifold(mesh)

def polys(g):
    return [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and p.area > 0.5]

def dump(g, min_hole=0.3):
    return [{"ext": np.round(np.asarray(p.exterior.coords)[:-1], 4).tolist(),
             "holes": [np.round(np.asarray(h.coords)[:-1], 4).tolist() for h in p.interiors if Polygon(h).area > min_hole]} for p in polys(g)]

def big(g):
    return max(polys(g), key=lambda p: p.area)

out = {}
# 底座 / 底板外形
out["base"] = dump(Polygon(big(A.slice_poly(M, 5.0)).exterior))
s12 = big(A.slice_poly(M, 12.0))
fl = unary_union([Polygon(q.exterior) for q in polys(A.slice_poly(M, 12.0))]).buffer(6, join_style=1).buffer(-6, join_style=1)   # 後跟 + 前段兩塊合併、補舊槽
out["floor"] = dump(Polygon(big(fl).exterior))
out["toe_slots"] = [np.round(np.asarray(h.coords)[:-1], 4).tolist() for h in s12.interiors if Polygon(h).centroid.x > 235]
# 底部鏤空（z = 1 斷面的內孔）與深度（取孔內多點向上射線的最小值，保守）
pk = []
s1 = big(A.slice_poly(M, 1.0))
for h in s1.interiors:
    P = Polygon(h)
    if P.area < 2: continue
    inner = P.buffer(-0.6)
    pts = [P.representative_point()] + ([Point(c) for c in np.asarray(inner.exterior.coords)[::4]] if not inner.is_empty and inner.geom_type == "Polygon" else [])
    zs = []
    for q in pts:
        loc, _, _ = mesh.ray.intersects_location([[q.x, q.y, -1]], [[0, 0, 1]])
        if len(loc): zs.append(loc[:, 2].min())
    if zs:
        pk.append({"ring": np.round(np.asarray(h.coords)[:-1], 4).tolist(), "depth": round(float(min(zs)), 3)})
out["pockets"] = pk
# 牆以上（z ≥ 15）的俯視範圍：各高度斷面聯集
up = unary_union([A.slice_poly(M, z).buffer(0) for z in np.arange(15.5, 76, 1.0)])
out["upper_plan"] = dump(up)
# 牆本體俯視：取 z = 21 斷面（v15 牆面上窄下寬，取中段），補上舊走線槽缺口
w21 = unary_union([A.slice_poly(M, z).buffer(0) for z in (20.5, 21.0, 21.5)]).buffer(3, join_style=1).buffer(-3, join_style=1)
out["wall_plan"] = dump(w21)

def project(sub, axes):
    tm = A.to_trimesh(sub)
    tri = tm.vertices[tm.faces][:, :, axes]
    u = tri[:, 1] - tri[:, 0]; v = tri[:, 2] - tri[:, 0]; a = 0.5 * np.abs(u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0])
    tri = tri[a > 1e-6]
    return unary_union([Polygon(t) for t in tri]).buffer(0.002).buffer(-0.002)

def clip(x0, x1, y0, y1, z0, z1):
    return m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])

YO = 51.6
# 側面輪廓（XZ）：牆層 |y| < YO、外層 |y| ≥ YO（扣環、小支架）
inner = (M ^ clip(6, 400, -YO, YO, 14.5, 90))
outer = (M ^ clip(6, 400, YO, 80, 14.5, 90)) + (M ^ clip(6, 400, -80, -YO, 14.5, 90))
xz_in = project(inner, [0, 2]); xz_out = project(outer, [0, 2])
# 舊走線槽（x 90~110, z 10~20）的窗孔補實
fillbox = box(88, 9, 112, 21)
def fill_holes(g, region):
    res = []
    for p in polys(g):
        keep = [h for h in p.interiors if not Polygon(h).within(region)]
        res.append(Polygon(p.exterior, keep))
    return unary_union(res)
out["xz_inner"] = dump(fill_holes(xz_in, fillbox).union(box(88, 14.5, 112, 21)).buffer(0))
out["xz_outer"] = dump(xz_out)
# 後牆（YZ）
back = M ^ clip(-10, 6, -80, 80, 14.5, 90)
out["yz_back"] = dump(project(back, [1, 2]).buffer(0.4, join_style=2))   # 外擴 0.4 與側牆重疊，避免只以一條邊相接
out["xz_back"] = dump(project(back, [0, 2]))
json.dump(out, open(os.path.join(HERE, "v15_profiles.json"), "w"))
print({k: (len(v) if isinstance(v, list) else v) for k, v in out.items()})
print("pocket depths", sorted(set(p["depth"] for p in pk))[:12])
for k in ("xz_inner", "xz_outer", "yz_back", "upper_plan"):
    print(k, [(len(p["ext"]), len(p["holes"])) for p in out[k]])
