"""修補 OCC 網格化留下的小破洞（開放邊圍成的平面小洞）：把每個開放邊迴圈三角化補上，不改動其他三角形。
用法：python3 stl_patch.py in.stl out.stl"""
import sys, numpy as np, trimesh, mapbox_earcut as earcut
m = trimesh.load(sys.argv[1]); m.merge_vertices(digits_vertex=5)
for it in range(3):
    oe = m.edges_sorted[trimesh.grouping.group_rows(m.edges_sorted, require_count=1)]
    if len(oe) == 0:
        break
    adj = {}
    for a, b in oe:
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    used = set(); new = []
    for a, b in oe:
        if (a, b) in used: continue
        loop = [a, b]; used.add((a, b)); used.add((b, a))
        while True:
            nxt = [c for c in adj[loop[-1]] if (loop[-1], c) not in used]
            if not nxt: break
            c = nxt[0]; used.add((loop[-1], c)); used.add((c, loop[-1]))
            if c == loop[0]: break
            loop.append(c)
        if len(loop) < 3: continue
        P = m.vertices[loop]; c0 = P.mean(0)
        n = np.zeros(3)
        for i in range(len(P)): n += np.cross(P[i] - c0, P[(i + 1) % len(P)] - c0)
        if np.linalg.norm(n) < 1e-12: continue
        n /= np.linalg.norm(n); u = np.cross(n, [1, 0, 0] if abs(n[0]) < .9 else [0, 1, 0]); u /= np.linalg.norm(u); w = np.cross(n, u)
        uv = np.c_[(P - c0) @ u, (P - c0) @ w]
        tri = earcut.triangulate_float64(uv, np.array([len(uv)], dtype=np.uint32)).reshape(-1, 3)
        new += [[loop[i] for i in t] for t in tri]
    if not new: break
    m = trimesh.Trimesh(m.vertices, np.vstack([m.faces, new]), process=True)
    trimesh.repair.fix_normals(m)
print("watertight", m.is_watertight, "open", len(trimesh.grouping.group_rows(m.edges_sorted, require_count=1)))
m.export(sys.argv[2])
