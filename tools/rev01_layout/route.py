"""Small grid router for local fixes (no pcbnew): A* on F.Cu / B.Cu with through vias, moves at 0 / 45 / 90 degrees.
Router(board, win).route(net, start, goal, w=0.3) -> ([(layer, [points]), ...], [via points]).
- obstacles: pads, tracks and vias of other nets on the layer (clearance CL + w/2), the board edge (0.25 + w/2);
- a via is allowed where it clears other-net copper on every copper layer (tracks, vias, THT pads; zones are refilled)
  and other holes; vias of the net being routed are free to join;
- start / goal: a pad (ref, number), the path may begin anywhere inside the pad on its layer; or ("pt", layer, x, y).
Routed paths become obstacles for the next call (Router keeps them)."""
import math, heapq
import numpy as np
import geom, pcbedit

CU = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"]

def d_seg(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1; L2 = dx*dx + dy*dy
    if L2 == 0: return np.hypot(px - x1, py - y1)
    t = np.clip(((px - x1)*dx + (py - y1)*dy) / L2, 0, 1)
    return np.hypot(px - (x1 + t*dx), py - (y1 + t*dy))
def d_rect(px, py, r):
    return np.hypot(np.maximum(np.maximum(r[0] - px, px - r[2]), 0), np.maximum(np.maximum(r[1] - py, py - r[3]), 0))

class Router:
    def __init__(self, fn, win, h=0.05, cl=0.2, edge_cl=0.25):
        self.fn, self.win, self.h, self.cl, self.edge_cl = fn, win, h, cl, edge_cl
        self.G = geom.Board(fn); B = pcbedit.Board(fn)
        self.segs = [g for g in B.segments()]; self.vias = list(B.vias())
        x0, y0, x1, y1 = win
        self.xs = np.arange(x0, x1 + 1e-9, h); self.ys = np.arange(y0, y1 + 1e-9, h)
        self.X, self.Y = np.meshgrid(self.xs, self.ys)
        self.pads = []                                     # (layers, rect, net, drill)
        for r, f in self.G.fps.items():
            for p in f.placed()[0]:
                lays = CU if p.get("drill") else [f.layer]
                self.pads.append((lays, (p["x"]-p["aw"]/2, p["y"]-p["ah"]/2, p["x"]+p["aw"]/2, p["y"]+p["ah"]/2), p.get("net", ""), p.get("drill") or 0, r, p["name"]))
        self.added = []                                    # (layer, x1, y1, x2, y2, w, net) / ("via", x, y, size, net)
    def _dist(self, layer, net, w_extra=0.0):
        """distance field (edge of other-net copper) on `layer` for the window"""
        D = np.full(self.X.shape, 99.0)
        x0, y0, x1, y1 = self.win; m = 2.0
        for g in self.segs + [dict(layer=a[0], x1=a[1], y1=a[2], x2=a[3], y2=a[4], w=a[5], net=a[6]) for a in self.added if a[0] != "via"]:
            if g["layer"] != layer or g["net"] == net: continue
            if max(g["x1"], g["x2"]) < x0 - m or min(g["x1"], g["x2"]) > x1 + m or max(g["y1"], g["y2"]) < y0 - m or min(g["y1"], g["y2"]) > y1 + m: continue
            D = np.minimum(D, d_seg(self.X, self.Y, g["x1"], g["y1"], g["x2"], g["y2"]) - g["w"]/2)
        for v in self.vias + [dict(x=a[1], y=a[2], size=a[3], net=a[4]) for a in self.added if a[0] == "via"]:
            if v["net"] == net: continue
            if not (x0 - m < v["x"] < x1 + m and y0 - m < v["y"] < y1 + m): continue
            D = np.minimum(D, np.hypot(self.X - v["x"], self.Y - v["y"]) - v["size"]/2)
        for lays, r, n, dr, ref, pn in self.pads:
            if layer not in lays or n == net: continue
            if r[2] < x0 - m or r[0] > x1 + m or r[3] < y0 - m or r[1] > y1 + m: continue
            D = np.minimum(D, d_rect(self.X, self.Y, r))
        return D
    def _edge(self):
        D = np.full(self.X.shape, 99.0)
        for e in self.G.edge: D = np.minimum(D, d_seg(self.X, self.Y, *e))
        return D
    def _holes(self):
        D = np.full(self.X.shape, 99.0)
        for v in self.vias + [dict(x=a[1], y=a[2], size=a[3], d=0.3) for a in self.added if a[0] == "via"]:
            D = np.minimum(D, np.hypot(self.X - v["x"], self.Y - v["y"]) - v.get("d", 0.3)/2)
        for lays, r, n, dr, ref, pn in self.pads:
            if dr: D = np.minimum(D, np.hypot(self.X - (r[0]+r[2])/2, self.Y - (r[1]+r[3])/2) - dr/2)
        return D
    def route(self, net, start, goal, w=0.3, via=(0.6, 0.3), via_cost=6.0, layers=("F.Cu", "B.Cu"), keep=True,
              under_ok=(), block=None):
        """under_ok: refs whose body may take vias (tented, e.g. between the rows of an SOIC on the other side);
        block: {layer: [rect, ...]} extra keep-outs for the track (e.g. inside the pin ring of a QFP)"""
        h = self.h; E = self._edge()
        free = {}
        for l in layers:
            free[l] = (self._dist(l, net) >= self.cl + w/2 - 1e-9) & (E >= self.edge_cl + w/2)
            for r in (block or {}).get(l, []):
                free[l] &= ~((self.X > r[0] - w/2) & (self.X < r[2] + w/2) & (self.Y > r[1] - w/2) & (self.Y < r[3] + w/2))
        vsz, vdr = via
        vok = (E >= self.edge_cl + vsz/2) & (self._holes() >= 0.25 + vdr/2)
        for l in CU: vok &= self._dist(l, net) >= self.cl + vsz/2 - 1e-9
        for lays, r, n, dr, ref, pn in self.pads:           # no via in or touching an SMD pad, whatever its net
            if not dr: vok &= d_rect(self.X, self.Y, r) >= vsz/2 + 0.05
        for r, f in self.G.fps.items():                    # no vias under part bodies (courtyards on F or B)
            if r in under_ok: continue
            pads, crt = f.placed()
            if crt and crt[2] - crt[0] > 0.01 and not any(p.get("drill") for p in pads):
                vok &= ~((self.X > crt[0] - vsz/2) & (self.X < crt[2] + vsz/2) & (self.Y > crt[1] - vsz/2) & (self.Y < crt[3] + vsz/2))
        def pad_cells(ref, pn, *rest):
            if ref == "pt":                                  # ("pt", layer, x, y): a track end of the net
                l, x, y = pn, rest[0], rest[1]
                m = np.hypot(self.X - x, self.Y - y) <= h*0.75
                return [(l, j, i) for j, i in zip(*np.nonzero(m))]
            out = []
            for lays, r, n, dr, rf, p in self.pads:
                if rf == ref and p == pn:
                    for l in layers:
                        if l in lays:
                            m = (self.X >= r[0] + 0.05) & (self.X <= r[2] - 0.05) & (self.Y >= r[1] + 0.05) & (self.Y <= r[3] - 0.05)
                            out += [(l, j, i) for j, i in zip(*np.nonzero(m))]
            return out
        S = pad_cells(*start); T = set(pad_cells(*goal))
        assert S and T, (start, goal)
        for l, j, i in S + list(T): free[l][j, i] = True
        li = {l: k for k, l in enumerate(layers)}
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        tx = np.mean([self.xs[i] for l, j, i in T]); ty = np.mean([self.ys[j] for l, j, i in T])
        hfun = lambda j, i: math.hypot(self.xs[i] - tx, self.ys[j] - ty) / h
        dist = {}; prev = {}; pq = []
        for s in S:
            dist[(s, -1)] = 0; heapq.heappush(pq, (hfun(s[1], s[2]), 0, s, -1))
        best = None
        while pq:
            f, g, node, d0 = heapq.heappop(pq)
            if dist.get((node, d0), 1e18) < g: continue
            if node in T: best = (node, d0); break
            l, j, i = node
            for k, (di, dj) in enumerate(dirs):
                jj, ii = j + dj, i + di
                if not (0 <= jj < self.X.shape[0] and 0 <= ii < self.X.shape[1]) or not free[l][jj, ii]: continue
                c = math.sqrt(2) if di and dj else 1.0
                if d0 >= 0 and d0 != k: c += 0.6                      # bend penalty
                nn = (l, jj, ii); ng = g + c
                if ng < dist.get((nn, k), 1e18):
                    dist[(nn, k)] = ng; prev[(nn, k)] = (node, d0); heapq.heappush(pq, (ng + hfun(jj, ii), ng, nn, k))
            if vok[j, i]:
                for l2 in layers:
                    if l2 == l or not free[l2][j, i]: continue
                    nn = (l2, j, i); ng = g + via_cost
                    if ng < dist.get((nn, -1), 1e18):
                        dist[(nn, -1)] = ng; prev[(nn, -1)] = (node, d0); heapq.heappush(pq, (ng + hfun(j, i), ng, nn, -1))
        if best is None: return None
        path = []; cur = best
        while cur in prev: path.append(cur[0]); cur = prev[cur]
        path.append(cur[0]); path.reverse()
        # split into layer runs, merge collinear moves
        tracks, vias = [], []; run = [path[0]]
        for a, b in zip(path, path[1:]):
            if a[0] != b[0]:
                tracks.append(run); vias.append((round(self.xs[a[2]], 4), round(self.ys[a[1]], 4))); run = [b]
            else: run.append(b)
        tracks.append(run)
        out = []
        for run in tracks:
            pts = [(round(self.xs[i], 4), round(self.ys[j], 4)) for l, j, i in run]
            simp = [pts[0]]
            for p, q in zip(pts[1:], pts[2:] + [None]):
                if q is None: simp.append(p); break
                d1 = (p[0] - simp[-1][0], p[1] - simp[-1][1]); d2 = (q[0] - p[0], q[1] - p[1])
                if abs(d1[0]*d2[1] - d1[1]*d2[0]) > 1e-9: simp.append(p)
            if len(simp) >= 2: out.append((run[0][0], simp))
        if keep:
            for l, pts in out:
                for a, b in zip(pts, pts[1:]): self.added.append((l, a[0], a[1], b[0], b[1], w, net))
            for v in vias: self.added.append(("via", v[0], v[1], vsz, net))
        return out, vias
