import re, sys, numpy as np, trimesh, mapbox_earcut as earcut
def load(path):
    ents={}
    txt=open(path).read()
    for m in re.finditer(r'#(\d+)=([A-Z_]+)\((.*?)\);',txt):
        ents[int(m.group(1))]=(m.group(2),m.group(3))
    pts={}
    for k,(t,a) in ents.items():
        if t=='CARTESIAN_POINT':
            v=re.search(r'\(([^()]*)\)\s*$',a).group(1)
            pts[k]=tuple(float(x) for x in v.split(','))
    out={}
    for k,(t,a) in ents.items():
        if t!='FACETED_BREP': continue
        name=re.match(r"'([^']*)'",a).group(1)
        shell=int(re.search(r'#(\d+)',a.split(',',1)[1]).group(1))
        faces=[int(x) for x in re.findall(r'#(\d+)',ents[shell][1])]
        V=[];F=[];idx={}
        def vi(p):
            if p not in idx: idx[p]=len(V); V.append(pts[p])
            return idx[p]
        for f in faces:
            b=int(re.search(r'#(\d+)',ents[f][1]).group(1))
            loop=int(re.search(r'#(\d+)',ents[b][1]).group(1))
            ids=[vi(int(x)) for x in re.findall(r'#(\d+)',ents[loop][1])]
            if len(ids)==3: F.append(tuple(ids)); continue
            P=np.array([V[i] for i in ids]); n=np.zeros(3)
            for i in range(len(P)): n+=np.cross(P[i],P[(i+1)%len(P)])
            n/=np.linalg.norm(n); a=np.cross(n,[1,0,0]) if abs(n[0])<0.9 else np.cross(n,[0,1,0]); a/=np.linalg.norm(a); b=np.cross(n,a)
            uv=np.c_[(P-P[0])@a,(P-P[0])@b]
            tri=earcut.triangulate_float64(uv,np.array([len(uv)],dtype=np.uint32)).reshape(-1,3)
            for t in tri:
                F.append(tuple(ids[k] for k in t))
        mm=trimesh.Trimesh(np.array(V),np.array(F),process=True); trimesh.repair.fix_normals(mm); out[name]=mm
    return out
if __name__=='__main__':
    for p in sys.argv[2:]:
        for n,m in load(p).items():
            m.export(f'{sys.argv[1]}/{n}.stl'); print(n,m.bounds.round(1).tolist(),round(m.volume/1000,1),m.is_watertight)
