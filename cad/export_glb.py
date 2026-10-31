"""輸出 3D 檢視用 GLB（每個零件一個節點，附模組、顏色、爆炸位移）。
用法： python3 export_glb.py OUT.glb
"""
import os, sys, json
import numpy as np
import trimesh
import cadquery as cq
from shapely.geometry import Polygon, box as sbox

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import afo_v17 as A

P = A.P
parts, D = A.build(P, verbose=False)
ZT = D["ZT"]

COL = {"F": (0.58, 0.66, 0.80), "L": (0.80, 0.66, 0.48), "T": (0.95, 0.62, 0.28), "B": (0.30, 0.50, 0.85),
       "C": (0.55, 0.80, 0.50), "TPU": (0.25, 0.74, 0.74), "STEEL": (0.85, 0.86, 0.88), "FSR": (0.15, 0.15, 0.15),
       "STRAP": (0.22, 0.22, 0.27), "PCB": (0.10, 0.50, 0.26), "PCB_W": (0.94, 0.94, 0.90), "SHOE": (0.84, 0.80, 0.74),
       "WIRE": (0.85, 0.15, 0.15)}
GROUP = {"F": "腳底件", "L": "小腿件", "T": "鞋頭擋塊", "B": "走線蓋板", "C": "FSR 感測匣", "TPU": "FSR 感測匣",
         "STEEL": "FSR 感測匣", "FSR": "FSR 感測匣", "STRAP": "魔鬼氈", "PCB": "電子（示意）", "PCB_W": "電子（示意）",
         "SHOE": "布鞋（示意）", "WIRE": "電子（示意）"}


def resample(ring, n):
    L = ring.length
    return [ring.interpolate(t * L).coords[0] for t in np.linspace(0, 1, n, endpoint=False)]


meshes = {k: (A.as_mesh(w), m) for k, (w, m) in parts.items()}
# 布鞋（示意）
inner = D["inner"]
shoe2d = inner.buffer(-4, join_style=1).intersection(sbox(9.0, -200, P["Sleeve_Inner_X"] + P["Shoe_Length"], 200))
shoe2d = shoe2d.difference(sbox(0, 32.0, 46, 200)).difference(sbox(0, -200, 46, -32.0)).buffer(6, join_style=1).buffer(-6, join_style=1)
SOLE_T = 30.0
meshes["布鞋鞋底(示意)"] = (A.as_mesh(A.ext(shoe2d.simplify(0.3), ZT, SOLE_T)), "SHOE")
up0 = shoe2d.buffer(-3)
up1 = Polygon([(x * 0.62 + 14, y * 0.72) for x, y in shoe2d.buffer(-12).exterior.coords])
w0 = cq.Wire.makePolygon([cq.Vector(x, y, ZT + SOLE_T) for x, y in resample(up0.exterior, 90)], close=True)
w1 = cq.Wire.makePolygon([cq.Vector(x, y, ZT + SOLE_T + 68) for x, y in resample(up1.exterior, 90)], close=True)
meshes["布鞋鞋面(示意)"] = (A.as_mesh(cq.Solid.makeLoft([w0, w1], True)), "SHOE")


def strap(x, ztop, yend, zend=30.0, w=38.0):
    pts = [(-yend, zend), (-yend * 0.9, ztop - 12), (0, ztop), (yend * 0.9, ztop - 12), (yend, zend)]
    sw = cq.Workplane("YZ", origin=(x, 0, 0)).spline(pts, includeCurrent=False).val()
    pl = cq.Plane(origin=sw.startPoint(), xDir=(1, 0, 0), normal=sw.tangentAt(0))
    return A.as_mesh(cq.Workplane(pl).rect(w, 1.6).sweep(cq.Workplane().add(sw)))


sp = A.warp_pts([[140.0, 52.5, 0], [187.5, 52.5, 0]], P)
meshes["A4_前掌魔鬼氈"] = (strap(sp[1][0], ZT + SOLE_T + 34, sp[1][1]), "STRAP")
meshes["A4_中足魔鬼氈"] = (strap(sp[0][0], ZT + SOLE_T + 48, sp[0][1]), "STRAP")
ex = D["exit"]
wire3d = np.array([[ex[0] - 2, 0, ex[2]], [-8, 0, ex[2]], [-9, 0, 40], [-12, 0, 78], [-18, -20, 84]])
meshes["FSR 線(示意)"] = (trimesh.util.concatenate([trimesh.creation.cylinder(radius=1.4, segment=[wire3d[i], wire3d[i + 1]], sections=10) for i in range(len(wire3d) - 1)]), "WIRE")


def explode(name):
    if name.startswith("C"):
        return [0, 0, {"C4": 40, "C3": 52, "C5": 62, "C2": 72, "C1": 86, "C0": 108}[name[:2]]]
    if name.startswith("B2"): return [0, 0, 30]
    if name.startswith("L1"): return [-70, 0, 130]
    if name.startswith("E"): return [-95, 0, 130]
    if name.startswith("T1"): return [70, 0, 50]
    if name.startswith("A4"): return [0, 0, 160]
    if "布鞋" in name: return [0, 0, 210]
    if name.startswith("FSR"): return [-80, 0, 60]
    return [0, 0, 0]


scene = trimesh.Scene()
meta = []
for name, (m, mod) in meshes.items():
    m = m.copy()
    m.merge_vertices()
    if len(m.faces) > 60000:
        m = m.simplify_quadric_decimation(face_count=60000)
    rgb = COL[mod]
    m.visual = trimesh.visual.ColorVisuals(m, face_colors=None)
    mat = trimesh.visual.material.PBRMaterial(name=name, baseColorFactor=[*rgb, 1.0], metallicFactor=0.6 if mod == "STEEL" else 0.0,
                                              roughnessFactor=0.35 if mod == "STEEL" else 0.75, doubleSided=True)
    m.visual = trimesh.visual.TextureVisuals(material=mat)
    node = f"n{len(meta)}"
    scene.add_geometry(m, node_name=node, geom_name=node)
    b = m.bounds
    meta.append(dict(node=node, name=name, group=GROUP[mod], explode=explode(name),
                     size=[round(float(v), 1) for v in (b[1] - b[0])]))
out = sys.argv[1] if len(sys.argv) > 1 else "model.glb"
scene.export(out)
info = dict(parts=meta, S1=D["S1"], S2=D["S2"], warp=[round(v, 3) for v in D["warp"]],
            foot_size=[round(float(v), 1) for v in (meshes["F1_AFO腳底件_v17"][0].bounds[1] - meshes["F1_AFO腳底件_v17"][0].bounds[0])],
            shoe=[P["Shoe_Length"], P["Shoe_Max_Width"]])
json.dump(info, open(os.path.splitext(out)[0] + ".json", "w"), ensure_ascii=False, indent=1)
print(out, os.path.getsize(out) // 1024, "KB", len(meta), "parts")
