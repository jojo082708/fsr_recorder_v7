"""工程圖繪製工具：HLR 隱藏線投影 + 簡易著色（matplotlib）。"""
import numpy as np
import cadquery as cq
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopoDS import TopoDS
import matplotlib
from matplotlib.collections import PolyCollection, LineCollection


def to_shape(w):
    if isinstance(w, cq.Workplane):
        vals = w.vals()
        return vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)
    return w


def camera(d, up):
    d = np.asarray(d, float); d /= np.linalg.norm(d)
    r = np.cross(d, up); r /= np.linalg.norm(r)
    u = np.cross(r, d)
    return d, r, u


def proj(V, d, up):
    d, r, u = camera(d, up)
    return np.c_[V @ r, V @ u], V @ d


def tess(shape, tol=0.08, max_edge=6.0):
    import trimesh
    v, t = to_shape(shape).tessellate(tol, 0.2)
    V = np.array([[p.x, p.y, p.z] for p in v]); F = np.array(t, dtype=int)
    if max_edge and len(F):
        V, F = trimesh.remesh.subdivide_to_size(V, F, max_edge=max_edge, max_iter=12)
    return V, F


def _edges(comp):
    out = []
    if comp is None or comp.IsNull():
        return out
    ex = TopExp_Explorer(comp, TopAbs_EDGE)
    while ex.More():
        e = TopoDS.Edge_s(ex.Current())
        try:
            c = BRepAdaptor_Curve(e)
            dsc = GCPnts_QuasiUniformDeflection(c, 0.03)
            if dsc.IsDone() and dsc.NbPoints() > 1:
                pts = [dsc.Value(i + 1) for i in range(dsc.NbPoints())]
                out.append(np.array([[p.X(), p.Y()] for p in pts]))
        except Exception:
            pass
        ex.Next()
    return out


def hlr(shapes, d, up, hidden=True):
    d, r, u = camera(d, up)
    algo = HLRBRep_Algo()
    for s in shapes:
        algo.Add(to_shape(s).wrapped)
    ax = gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(*(-d)), gp_Dir(*r))
    algo.Projector(HLRAlgo_Projector(ax))
    algo.Update(); algo.Hide()
    h = HLRBRep_HLRToShape(algo)
    vis = _edges(h.VCompound()) + _edges(h.OutLineVCompound())
    hid = (_edges(h.HCompound()) + _edges(h.OutLineHCompound())) if hidden else []
    return vis, hid


def shade(ax, items, d, up, light=(0.35, -0.45, 0.82), zorder=1, edge=False):
    """items: list of (V, F, rgb, alpha)."""
    dd, r, u = camera(d, up)
    L = np.asarray(light, float); L /= np.linalg.norm(L)
    polys, cols, depth = [], [], []
    for V, F, rgb, a in items:
        if len(F) == 0:
            continue
        P2, Z = proj(V, d, up)
        tri = V[F]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        nn = np.linalg.norm(n, axis=1); ok = nn > 1e-12
        n[ok] /= nn[ok, None]
        facing = (n @ dd) < 0
        k = 0.45 + 0.55 * np.abs(n @ L)
        k = np.where(facing, k, k * 0.8)
        c = np.clip(np.outer(k, np.asarray(rgb)), 0, 1)
        polys.append(P2[F]); cols.append(np.c_[c, np.full(len(F), a)]); depth.append(Z[F].mean(1) - 0.0 * Z[F].min(1))
    if not polys:
        return
    polys = np.concatenate(polys); cols = np.concatenate(cols); depth = np.concatenate(depth)
    o = np.argsort(-depth)
    pc = PolyCollection(polys[o], facecolors=cols[o], edgecolors=cols[o] if not edge else "k", linewidths=0.15, zorder=zorder)
    ax.add_collection(pc)


def lines(ax, pl, color="k", lw=0.6, ls="-", zorder=3):
    if pl:
        ax.add_collection(LineCollection(pl, colors=color, linewidths=lw, linestyles=ls, zorder=zorder))


def section_faces(shape, origin, normal):
    """回傳剖切面 (3D Face list)。"""
    s = to_shape(shape)
    pl = cq.Face.makePlane(2000, 2000, basePnt=cq.Vector(*origin), dir=cq.Vector(*normal))
    try:
        res = s.intersect(pl)
        return res.Faces()
    except Exception:
        return []


def face_polys(face, d, up):
    """Face → list of 2D rings (outer first)."""
    rings = []
    for w in [face.outerWire()] + face.innerWires():
        ps = w.positions(np.linspace(0, 1, 400))
        V = np.array([[p.x, p.y, p.z] for p in ps])
        rings.append(proj(V, d, up)[0])
    return rings
