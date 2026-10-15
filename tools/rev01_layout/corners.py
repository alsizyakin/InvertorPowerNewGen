"""Count / list 90-degree corners (degree-2 joints of two tracks of one net and layer) in new routing vs rev0.
Usage: corners.py board rev0_board tools [list]"""
import sys, math, collections
sys.path.insert(0, sys.argv[3]); sys.dont_write_bytecode = True
from pcbedit import Board
cur = Board(sys.argv[1]); old = Board(sys.argv[2])
key = lambda g: (g["net"], g["layer"], tuple(sorted([(round(g["x1"], 2), round(g["y1"], 2)), (round(g["x2"], 2), round(g["y2"], 2))])))
oldk = set(key(g) for g in old.segments())
segs = list(cur.segments()); new = [g for g in segs if key(g) not in oldk]
def corners(sl, allsegs):
    ends = collections.defaultdict(list)
    for g in allsegs:
        for e in ((g["x1"], g["y1"]), (g["x2"], g["y2"])): ends[(g["net"], g["layer"], round(e[0], 3), round(e[1], 3))].append(g)
    ids = set(id(g) for g in sl); out = []
    for k, gs in ends.items():
        if len(gs) != 2 or not any(id(g) in ids for g in gs): continue
        p = (k[2], k[3])
        def d(g):
            q = (g["x2"], g["y2"]) if abs(g["x1"]-p[0]) < 1e-3 and abs(g["y1"]-p[1]) < 1e-3 else (g["x1"], g["y1"])
            v = (q[0]-p[0], q[1]-p[1]); L = math.hypot(*v); return (v[0]/L, v[1]/L, L) if L > 1e-6 else None
        u, v = d(gs[0]), d(gs[1])
        if u and v and abs(u[0]*v[0] + u[1]*v[1]) < 0.05: out.append((k, gs))
    return out
cn = corners(new, segs); co = corners(list(old.segments()), list(old.segments()))
print("segments", len(segs), "new/changed", len(new), "| 90-degree corners: new routing", len(cn), "| rev0 board", len(co))
c = collections.Counter((k[0], k[1]) for k, _ in cn)
for (n, l), m in c.most_common(40): print(f"   {m:3d}  {l:7s} {n}")
