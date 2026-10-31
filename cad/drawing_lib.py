"""工程圖共用工具：A3 圖框、尺寸標註、網格著色 + 可見輪廓線（embree 光線遮蔽判斷）、剖面。"""
import os, math
import numpy as np
import trimesh
import manifold3d as m3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.collections import PolyCollection, LineCollection
from matplotlib.patches import Rectangle, PathPatch, Circle
from matplotlib.path import Path
from shapely.geometry import Polygon

for f in ["/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
import logging
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

A3 = (420, 297)
PROJECT = "外穿式布鞋 FSR 雙點足底力量量測平台"
REV = "B 草案"
TAG = "AFO v17 / 左腳"


# ------------------------------------------------------------------ 圖框
def new_sheet(no, title, scale_txt, notes=None):
    fig = plt.figure(figsize=(A3[0] / 25.4, A3[1] / 25.4))
    bg = fig.add_axes([0, 0, 1, 1]); bg.set_xlim(0, A3[0]); bg.set_ylim(0, A3[1]); bg.axis("off")
    bg.add_patch(Rectangle((10, 10), 400, 277, fill=False, lw=1.2))
    x0, y0, w, h = 250, 10, 160, 36
    bg.add_patch(Rectangle((x0, y0), w, h, fill=False, lw=1.0))
    for yy in (y0 + 12, y0 + 24):
        bg.plot([x0, x0 + w], [yy, yy], "k", lw=0.5)
    bg.plot([x0 + 100, x0 + 100], [y0, y0 + 24], "k", lw=0.5)
    bg.plot([x0 + 130, x0 + 130], [y0, y0 + 24], "k", lw=0.5)
    bg.text(x0 + 3, y0 + 30, PROJECT, fontsize=10.5, va="center", weight="bold")
    bg.text(x0 + 3, y0 + 18, title, fontsize=10, va="center")
    bg.text(x0 + 3, y0 + 6, f"單位 mm ｜ 第三角法 ｜ {scale_txt}", fontsize=7.5, va="center")
    bg.text(x0 + 102, y0 + 18, "圖號", fontsize=6.5, va="center"); bg.text(x0 + 102, y0 + 6, "版次", fontsize=6.5, va="center")
    bg.text(x0 + 112, y0 + 18, f"FSR-{no:02d}", fontsize=8, va="center"); bg.text(x0 + 112, y0 + 6, REV, fontsize=8, va="center")
    bg.text(x0 + 132, y0 + 18, "2026-10-31", fontsize=7, va="center"); bg.text(x0 + 132, y0 + 6, "待確認", fontsize=8, va="center", color="#c0392b", weight="bold")
    bg.text(x0 + w - 3, y0 + 30, TAG, fontsize=7, va="center", ha="right")
    if notes:
        bg.text(14, 14, "\n".join(notes), fontsize=7.2, va="bottom", ha="left", linespacing=1.45)
    return fig, bg


def view_axes(fig, rect_mm, scale, center=None):
    x, y, w, h = rect_mm
    ax = fig.add_axes([x / A3[0], y / A3[1], w / A3[0], h / A3[1]])
    ax._wh = (w * scale, h * scale)
    if center is not None:
        set_center(ax, center)
    ax.set_aspect("equal"); ax.axis("off")
    return ax


def set_center(ax, c):
    W, H = ax._wh
    ax.set_xlim(c[0] - W / 2, c[0] + W / 2); ax.set_ylim(c[1] - H / 2, c[1] + H / 2)


# ------------------------------------------------------------------ 標註
DIMC = "#1a5276"

def dim(ax, p1, p2, off, txt=None, fs=7, color=DIMC):
    p1, p2, off = map(lambda v: np.asarray(v, float), (p1, p2, off))
    a, b = p1 + off, p2 + off
    nrm = off / (np.linalg.norm(off) + 1e-9)
    for p, q in ((p1, a), (p2, b)):
        ax.plot([p[0] + nrm[0] * 1.0, q[0] + nrm[0] * 2.0], [p[1] + nrm[1] * 1.0, q[1] + nrm[1] * 2.0], color=color, lw=0.35, zorder=9)
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="<|-|>", color=color, lw=0.5, mutation_scale=6, shrinkA=0, shrinkB=0), zorder=9)
    if txt is None:
        txt = f"{np.linalg.norm(p2 - p1):.1f}".rstrip("0").rstrip(".")
    m = (a + b) / 2; v = b - a
    ang = math.degrees(math.atan2(v[1], v[0]))
    if ang > 90.1 or ang < -89.9:
        ang += 180
    ax.text(m[0], m[1], txt, fontsize=fs, color=color, ha="center", va="center", rotation=ang,
            bbox=dict(fc="white", ec="none", pad=0.6), zorder=10)

def hdim(ax, x1, x2, y, ylev, txt=None, **kw):
    dim(ax, (x1, y), (x2, y), (0, ylev - y), txt, **kw)

def vdim(ax, y1, y2, x, xlev, txt=None, **kw):
    dim(ax, (x, y1), (x, y2), (xlev - x, 0), txt, **kw)

def leader(ax, xy, txy, txt, fs=7.5, color="k", ha="left"):
    ax.annotate(txt, xy=xy, xytext=txy, fontsize=fs, color=color, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", lw=0.45, color=color, shrinkA=1, shrinkB=0),
                bbox=dict(fc="white", ec="none", pad=0.5), zorder=12)
    ax.plot(*xy, "o", ms=1.6, color=color, zorder=12)

def balloon(ax, xy, txy, txt, color="k", fs=7.5):
    ax.annotate("", xy=xy, xytext=txy, arrowprops=dict(arrowstyle="-", lw=0.5, color=color, shrinkA=0, shrinkB=0), zorder=12)
    ax.plot(*xy, "o", ms=1.8, color=color, zorder=12)
    ax.text(*txy, txt, fontsize=fs, ha="center", va="center", zorder=13,
            bbox=dict(boxstyle="circle,pad=0.25" if len(txt) <= 3 else "round,pad=0.3", fc="white", ec=color, lw=0.7))

def centerline(ax, p1, p2, color="#7f8c8d"):
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color, lw=0.4, ls=(0, (8, 2, 1.5, 2)), zorder=8)


# ------------------------------------------------------------------ 相機
def camera(d, up):
    d = np.asarray(d, float); d /= np.linalg.norm(d)
    r = np.cross(d, up); r /= np.linalg.norm(r)
    u = np.cross(r, d)
    return d, r, u

def proj(V, d, up):
    d, r, u = camera(d, up)
    V = np.atleast_2d(V)
    return np.c_[V @ r, V @ u], V @ d


# ------------------------------------------------------------------ 網格繪製
def render(ax, items, d, up, light=(0.35, -0.45, 0.82), edge_angle=32, lw=0.4, line_color="k", subdiv=6.0):
    """items: list of (trimesh, rgb, alpha). 著色（畫家演算法）+ 可見的稜線/輪廓線。回傳 2D bbox。"""
    dd, r, u = camera(d, up)
    L = np.asarray(light, float); L /= np.linalg.norm(L)
    polys, cols, depth = [], [], []
    scene = []
    for m, rgb, a in items:
        scene.append(m)
        V, F = m.vertices, m.faces
        if subdiv:
            V, F = trimesh.remesh.subdivide_to_size(V, F, max_edge=subdiv, max_iter=10)
        P2, Z = proj(V, d, up)
        tri = V[F]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        nn = np.linalg.norm(n, axis=1); ok = nn > 1e-12
        n[ok] /= nn[ok, None]
        k = 0.45 + 0.55 * np.abs(n @ L)
        c = np.clip(np.outer(k, np.asarray(rgb)), 0, 1)
        polys.append(P2[F]); cols.append(np.c_[c, np.full(len(F), a)]); depth.append(Z[F].mean(1))
    polys = np.concatenate(polys); cols = np.concatenate(cols); depth = np.concatenate(depth)
    o = np.argsort(-depth)
    ax.add_collection(PolyCollection(polys[o], facecolors=cols[o], edgecolors=cols[o], linewidths=0.12, zorder=1))
    # 可見線
    if lw:
        S = trimesh.util.concatenate([s for s in scene if len(s.faces)])
        segs = []
        for m, rgb, a in items:
            if a < 0.6 or len(m.faces) == 0:
                continue
            adj = m.face_adjacency
            if len(adj) == 0:
                continue
            ang = m.face_adjacency_angles
            s = m.face_normals @ dd
            sel = (ang > math.radians(edge_angle)) | ((s[adj[:, 0]] * s[adj[:, 1]]) < 0)
            E = m.vertices[m.face_adjacency_edges[sel]]
            # 邊界（開放網格）
            if len(E) == 0:
                continue
            ts = np.array([0.15, 0.5, 0.85])
            pts = E[:, None, 0, :] * (1 - ts[None, :, None]) + E[:, None, 1, :] * ts[None, :, None]
            pts = pts.reshape(-1, 3) - dd * 0.08
            hit = S.ray.intersects_any(pts, np.tile(-dd, (len(pts), 1)))
            vis = (~hit.reshape(-1, 3)).sum(1) >= 2
            E = E[vis]
            if len(E):
                p0 = proj(E[:, 0], d, up)[0]; p1 = proj(E[:, 1], d, up)[0]
                segs.append(np.stack([p0, p1], 1))
        if segs:
            ax.add_collection(LineCollection(np.concatenate(segs), colors=line_color, linewidths=lw, zorder=3))
    return polys.reshape(-1, 2).min(0), polys.reshape(-1, 2).max(0)


# ------------------------------------------------------------------ 剖面
def to_manifold(m):
    m = m.copy(); m.merge_vertices()
    return m3.Manifold(m3.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))

def section_polys(mesh, origin, normal, xdir):
    """以平面剖切網格，回傳平面座標 (xdir, normal×xdir) 下的 shapely 幾何。"""
    n = np.asarray(normal, float); n /= np.linalg.norm(n)
    x = np.asarray(xdir, float); x -= n * (x @ n); x /= np.linalg.norm(x)
    y = np.cross(n, x)
    R = np.eye(4); R[:3, :3] = np.vstack([x, y, n]); R[:3, 3] = -R[:3, :3] @ np.asarray(origin, float)
    M = to_manifold(mesh).transform(np.ascontiguousarray(R[:3, :], dtype=np.float64))
    g = None
    for p in sorted([Polygon(q) for q in M.slice(0.0).to_polygons() if len(q) > 2], key=lambda p: -abs(p.area)):
        p = p.buffer(0)
        g = p if g is None else g.symmetric_difference(p)
    return g

def draw_polys(ax, g, fc, hatch=None, lw=0.5, zorder=3, ec="k"):
    if g is None or g.is_empty:
        return
    for p in getattr(g, "geoms", [g]):
        if p.geom_type != "Polygon" or p.area < 1e-4:
            continue
        verts, codes = [], []
        for ring in [p.exterior] + list(p.interiors):
            c = np.asarray(ring.coords)
            verts += list(c); codes += [Path.MOVETO] + [Path.LINETO] * (len(c) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec=ec, lw=lw, hatch=hatch, zorder=zorder))
