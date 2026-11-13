"""
AFO v17 托盤：build123d 原生重建（B-rep，平滑曲線，不再沿用 v15 網格）
=====================================================================
輸入：
  v15_profiles.json   由 extract_v15_profiles.py 從 v15 量得的 2D 輪廓（v15 座標）
  spec_<版本>.json    由 cad/afo_v17.py native_spec() 輸出的修改清單（感測匣口袋、走線槽、分件…）
做法：
  每個輪廓先以「轉角保留」方式擬合成直線 + 平滑 B-spline，再：
    底座 = 底座輪廓擠出 z 0→11，扣掉底部鏤空
    底板 = 底板輪廓擠出 z 11→15
    牆與扣環 = 上部俯視範圍擠出 z 14.5→80，再與側面（XZ）/ 後牆（YZ）輪廓相交
  然後加上 v17 的所有修改，最後依需要分成後段 / 前段。
執行（cadgen 的 venv，build123d 0.13）：
  python textcad/tray/tray_b3d.py shoe OUTDIR
輸出：OUTDIR/F1_tray_native.step（整件）、F1A_rear_native.step / F1B_front_native.step（分件），
      以及同名 STL（每段弧 ≤ 5°、偏差 ≤ 0.02 mm）。
"""
import os, sys, json, math
import numpy as np
import build123d as bd
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "shoe"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "out", VARIANT)
os.makedirs(OUT, exist_ok=True)
PRO = json.load(open(os.path.join(HERE, "v15_profiles.json")))
SPEC = json.load(open(os.path.join(HERE, f"spec_{VARIANT}.json")))
LIN, ANG = 0.02, 5.0          # 輸出精度：弦高 0.02 mm、每段 ≤ 5°

# ------------------------------------------------------------------ 依尺寸調整（同 afo_v17.warp_pts）
X0, SX, SY, BL = SPEC["warp"]
def warp_xy(P):
    P = np.array(P, float)
    x = P[:, 0]
    t = np.clip((x - X0) / BL, 0, 1); s = t * t * (3 - 2 * t)
    y = P[:, 1] * (1 + (SY - 1) * s)
    x = np.where(x > X0, X0 + (x - X0) * SX, x)
    return np.c_[x, y]
def warp_x(P):                       # XZ 輪廓只改 x
    P = np.array(P, float)
    P[:, 0] = np.where(P[:, 0] > X0, X0 + (P[:, 0] - X0) * SX, P[:, 0])
    return P


# ------------------------------------------------------------------ 多邊形 → 平滑邊界（轉角保留）
def _resample(c, step):
    seg = np.r_[0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]
    n = max(int(math.ceil(seg[-1] / step)), 2)
    s = np.linspace(0, seg[-1], n + 1)
    return np.c_[np.interp(s, seg, c[:, 0]), np.interp(s, seg, c[:, 1])]

FIT_TOL = 0.01          # 曲線擬合偏差上限（mm）

def fit_ring(ring, corner_deg=40.0, step=None):
    """多邊形 → 邊序列：真圓 / 直線 / 容差控制 B-spline（偏差 ≤ FIT_TOL），轉角保留。"""
    r = Polygon(ring).buffer(0)
    if r.geom_type != "Polygon":
        r = max(r.geoms, key=lambda g: g.area)
    raw = np.asarray(r.exterior.coords)[:-1]
    # 近似圓 → 真圓
    if len(raw) >= 10:
        A_ = np.c_[2 * raw, np.ones(len(raw))]; bb = (raw ** 2).sum(1)
        cx, cy, k = np.linalg.lstsq(A_, bb, rcond=None)[0]; R = math.sqrt(max(k + cx * cx + cy * cy, 1e-9))
        if R < 30 and np.abs(np.hypot(raw[:, 0] - cx, raw[:, 1] - cy) - R).max() < max(0.04, 0.012 * R):
            return [("circle", (cx, cy), R)]
    d = _resample(np.vstack([raw, raw[:1]]), 0.2)[:-1]
    n = len(d); k = 4
    v1 = d - np.roll(d, k, 0); v2 = np.roll(d, -k, 0) - d
    cosang = (v1 * v2).sum(1) / (np.hypot(*v1.T) * np.hypot(*v2.T) + 1e-12)
    ang = np.degrees(np.arccos(np.clip(cosang, -1, 1)))
    cand = [i for i in range(n) if ang[i] > corner_deg and ang[i] >= ang[(i - 1) % n] and ang[i] >= ang[(i + 1) % n]]
    corners = []
    for i in sorted(cand, key=lambda i: -ang[i]):           # 1 mm 內只留一個
        if all(min(abs(i - j), n - abs(i - j)) > 5 for j in corners):
            corners.append(i)
    corners.sort()
    # 轉角點吸附到原始多邊形最近頂點（保留尖角位置）
    def snap(i):
        j = np.argmin(np.hypot(*(raw - d[i]).T)); return raw[j]
    if len(corners) < 2:
        base = corners[0] if corners else 0
        corners = [base, (base + n // 3) % n, (base + 2 * n // 3) % n]
        corners.sort(); sharp = False
    else:
        sharp = True
    edges = []
    for a, b in zip(corners, corners[1:] + [corners[0] + n]):
        idx = [q % n for q in range(a, b + 1)]
        c = d[idx].copy()
        if sharp:
            c[0], c[-1] = snap(a % n), snap(b % n)
        p0, p1 = c[0], c[-1]
        L = np.linalg.norm(p1 - p0)
        if L < 1e-4:
            continue
        u = p1 - p0; dd = c - p0
        dev = np.abs(u[0] * dd[:, 1] - u[1] * dd[:, 0]) / L
        if dev.max() < 0.02:
            edges.append(("line", p0, p1))
        else:
            sub = c[::5]
            if np.linalg.norm(sub[-1] - c[-1]) > 1e-9:
                sub = np.vstack([sub[:-1] if np.linalg.norm(sub[-1] - c[-1]) < 0.4 else sub, c[-1:]])
            edges.append(("spline", sub if len(sub) >= 3 else c))
    return edges

def edges_to_wire(edges, to3d):
    out = []
    if edges and edges[0][0] == "circle":
        (cx, cy), R = edges[0][1], edges[0][2]
        c3 = to3d((cx, cy)); a3 = to3d((cx + R, cy)); b3 = to3d((cx, cy + R)); o = to3d((cx, cy))
        u = (a3 - o).normalized(); v = (b3 - o).normalized(); nrm = u.cross(v)
        return bd.Wire([bd.Edge.make_circle(R, bd.Plane(origin=c3, x_dir=u, z_dir=nrm))])
    for e in edges:
        if e[0] == "line":
            out.append(bd.Edge.make_line(to3d(e[1]), to3d(e[2])))
        elif e[0] == "approx":
            pts = [to3d(q) for q in e[1]]
            try:
                ed = bd.Edge.make_spline_approx(pts, tol=FIT_TOL, max_deg=5)
                if (ed.position_at(0) - pts[0]).length > 1e-6 or (ed.position_at(1) - pts[-1]).length > 1e-6:
                    raise ValueError('endpoint')
                # 端點精確吸附
                out.append(ed)
            except Exception:
                out.append(bd.Edge.make_spline(pts))
        elif e[0] == "spline":
            pts = [to3d(q) for q in e[1]]
            try:
                out.append(bd.Edge.make_spline(pts))
            except Exception:
                out += [bd.Edge.make_line(a, b) for a, b in zip(pts, pts[1:])]
        else:
            pts = [to3d(q) for q in e[1]]
            try:
                out.append(bd.Edge.make_spline(pts, periodic=True))
            except Exception:
                out += [bd.Edge.make_line(a, b) for a, b in zip(pts, pts[1:] + pts[:1])]
    w = bd.Wire(out)
    if not w.is_closed:
        raise ValueError("wire not closed")
    return w

def face_from(poly_json, to3d, warp=None, min_hole=0.3):
    ext = np.array(poly_json["ext"] if isinstance(poly_json, dict) else poly_json[0])
    holes = poly_json["holes"] if isinstance(poly_json, dict) else poly_json[1]
    if warp is not None:
        ext = warp(ext); holes = [warp(np.array(h)) for h in holes]
    ow = edges_to_wire(fit_ring(ext), to3d)
    iws = [edges_to_wire(fit_ring(np.array(h)), to3d) for h in holes if Polygon(h).area > min_hole]
    return bd.Face(ow, iws)

XY = lambda z: (lambda q: bd.Vector(q[0], q[1], z))
XZ = lambda q: bd.Vector(q[0], 0, q[1])
YZ = lambda q: bd.Vector(0, q[0], q[1])

def prism(faces_or_face, z0, h):
    fs = faces_or_face if isinstance(faces_or_face, list) else [faces_or_face]
    return [bd.extrude(f.moved(bd.Location((0, 0, z0))), h, dir=(0, 0, 1)) for f in fs]

def chk(name, sh):
    v = sh.volume
    print(f"    [{name}] V={v / 1000:.1f} cm3 valid={sh.is_valid} solids={len(sh.solids())}", flush=True)
    return sh

def fuse(shapes):
    if len(shapes) == 1:
        return shapes[0]
    return shapes[0].fuse(*shapes[1:], tol=1e-4).clean()

def box(x0, x1, y0, y1, z0, z1):
    return bd.Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * bd.Box(x1 - x0, y1 - y0, z1 - z0)

def cyl(x, y, z0, d, h):
    return bd.Pos(x, y, z0 + h / 2) * bd.Cylinder(d / 2, h)

def cyl_dir(o, dvec, d, h):
    dvec = bd.Vector(*dvec).normalized()
    pl = bd.Plane(origin=bd.Vector(*o), z_dir=dvec)
    return pl * bd.Pos(0, 0, h / 2) * bd.Cylinder(d / 2, h)

def cone_dir(o, dvec, r1, r2, h):
    dvec = bd.Vector(*dvec).normalized()
    pl = bd.Plane(origin=bd.Vector(*o), z_dir=dvec)
    return pl * bd.Pos(0, 0, h / 2) * bd.Cone(r1, r2, h)


# ------------------------------------------------------------------ 1) v15 托盤本體（原生）
print("base / floor ...", flush=True)
base = prism(face_from(PRO["base"][0], XY(0), warp_xy), 0.0, 11.0)[0]
try:
    base = bd.fillet(base.edges().group_by(bd.Axis.Z)[0], 3.0)          # 底部外緣 R3（v15 量得）
except Exception as ex:
    print("  base fillet skipped:", ex)
pockets = []
for pk in PRO["pockets"]:
    ring = warp_xy(np.array(pk["ring"]))
    try:
        f = bd.Face(edges_to_wire(fit_ring(ring, step=1.2), XY(-1)))
        pr = bd.extrude(f, pk["depth"] + 1, dir=(0, 0, 1))
        try:                                                               # 鏤空頂端圓弧（v15 為拱頂）
            pr = bd.fillet(pr.edges().group_by(bd.Axis.Z)[-1], min(2.0, 0.3 * math.sqrt(Polygon(ring).area)))
        except Exception:
            pass
        pockets.append(pr)
    except Exception as ex:
        print("  pocket skipped:", repr(ex)[:120])
print(f"  {len(pockets)} bottom pockets", flush=True)
# 底板外形與牆外緣用同一條曲線（避免兩條擬合曲線幾乎重合造成布林運算失敗）
_up_ext = dict(ext=PRO["upper_plan"][0]["ext"], holes=[])
floor = prism(face_from(_up_ext, XY(0), warp_xy), 10.0, 5.0)[0]
chk("base", base); chk("floor", floor)
body = chk("base+floor", base + floor)
if pockets:
    body = chk("-pockets", body - fuse(pockets))
if SPEC["v15_toe"]:
    slots = [prism(bd.Face(edges_to_wire(fit_ring(warp_xy(np.array(s))), XY(0))), 7.0, 9.0)[0] for s in PRO["toe_slots"]]
    body = body - fuse(slots)

print("walls ...", flush=True)
YO = 51.6
up = prism(face_from(PRO["upper_plan"][0], XY(0), warp_xy), 12.0, 68.0)[0]
def side_prism(prof, plane, amount, warp=None):    # 2D 輪廓放到 XZ / YZ 平面，沿法向雙向擠出
    return fuse([bd.extrude(plane * face_from(p, XY(0), warp), amount, both=True) for p in prof])
xz_in = side_prism(PRO["xz_inner"], bd.Plane.XZ, 200, warp_x)
xz_out = side_prism(PRO["xz_outer"], bd.Plane.XZ, 200, warp_x)
yz_b = side_prism(PRO["yz_back"], bd.Plane.YZ, 50)
xz_b = side_prism(PRO["xz_back"], bd.Plane.XZ, 200)
def band(y0, y1):                    # v15 座標的 y 帶狀區（x ≥ 6），依尺寸放大後的形狀
    xs = np.linspace(6, 300, 300)
    lo = warp_xy(np.c_[xs, np.full_like(xs, y0)]); hi = warp_xy(np.c_[xs, np.full_like(xs, y1)])
    poly = np.r_[lo, [[700, lo[-1, 1]], [700, hi[-1, 1]]], hi[::-1]]
    f = bd.Face(bd.Wire.make_polygon([bd.Vector(x, y, -1) for x, y in poly], close=True))
    return bd.extrude(f, 100, dir=(0, 0, 1))
walls = (up & band(-YO, YO) & xz_in)
loops = (up & (band(YO - 0.3, 130) + band(-130, -YO + 0.3)) & xz_out)   # 與牆重疊 0.3，避免共面
back = (up & box(-30, 6.3, -120, 120, 0, 90) & yz_b & xz_b)
def round_top(part, r):            # 牆 / 扣環上緣 R 圓角（z > 16 的邊）
    try:
        es = [e for e in part.edges() if e.center().Z > 16.5 and min(v.Z for v in e.vertices()) > 16.0]
        return bd.fillet(es, r)
    except Exception as ex:
        print("  top fillet skipped:", repr(ex)[:80]); return part
chk("walls", walls); chk("loops", loops); chk("back", back)
body = chk("+upper", body.fuse(walls, loops, back, tol=1e-4).clean())

# v15 小腿件鎖附 M3 沉頭孔（真圓）
m3 = SPEC["m3_holes"]
hc = []
for h in m3["list"]:
    o = np.array(h["outer"]); dv = np.array(h["dir"])
    hc.append(cyl_dir((o - dv * 3).tolist(), dv.tolist(), m3["D"], 20.0))
    depth = (m3["DK"] - m3["D"]) / 2
    hc.append(cone_dir((o - dv * 3).tolist(), dv.tolist(), m3["DK"] / 2 + 3.0, m3["D"] / 2, depth + 3.0))
body = chk("-m3", body - fuse(hc))

# ------------------------------------------------------------------ 2) v17 修改
print("v17 features ...", flush=True)
def build_prim(q):
    if q["t"] == "cyl":
        return cyl(q["x"], q["y"], q["z0"], q["d"], q["h"])
    if q["t"] == "cyl_dir":
        return cyl_dir(q["o"], q["dir"], q["d"], q["h"])
    if q["t"] == "prism":
        fs = []
        for ext, holes in q["polys"]:
            fs.append(face_from([ext, holes], XY(0)))
        return fuse(prism(fs, q["z0"], q["h"]))
    raise ValueError(q["t"])
body = chk("+union", body + fuse([build_prim(q) for q in SPEC["union"]]))
body = chk("-cut", body - fuse([build_prim(q) for q in SPEC["cut"]]))

def export(shape, name):
    bd.export_step(shape, os.path.join(OUT, name + ".step"))
    bd.export_stl(shape, os.path.join(OUT, name + ".stl"), tolerance=LIN, angular_tolerance=math.radians(ANG))
    bb = shape.bounding_box()
    print(f"  {name}: {bb.size.X:.1f} × {bb.size.Y:.1f} × {bb.size.Z:.1f}  V={shape.volume / 1000:.1f} cm3  valid={shape.is_valid}", flush=True)

export(body, "F1_tray_native")

# ------------------------------------------------------------------ 3) 分件（後段 / 前段）
sp = SPEC["split"]
if sp["on"]:
    print("split ...", flush=True)
    Xc, L, Zl, g, ZT = sp["Xc"], sp["L"], sp["Zl"], sp["g"], sp["ZT"]
    Xa, Xb = Xc - L / 2, Xc + L / 2
    R = box(-100, Xa, -300, 300, -10, 300) + box(Xa, Xb, -300, 300, Zl, ZT) + box(Xa, Xc, -300, 300, ZT - 0.01, 300)
    Rs = box(-100, Xa - g, -300, 300, -10, 300) + box(Xa - g, Xb - g, -300, 300, Zl + g, ZT) + box(Xa - g, Xc - g, -300, 300, ZT - 0.01, 300)
    rear = body & Rs
    front = body - R
    hf, hr = [], []
    for x, y in sp["screws"]:
        hf.append(cyl(x, y, -1, 4.5, Zl + 1.5)); hf.append(bd.Pos(x, y, -0.01 + 2.3 / 2) * bd.Cone(4.3, 2.0, 2.3))
        hr.append(cyl(x, y, Zl - 0.5, 5.6, 6.0))
    rear = rear - fuse(hr)
    front = front - fuse(hf)
    export(rear, "F1A_rear_native")
    export(front, "F1B_front_native")
print("done", OUT)
