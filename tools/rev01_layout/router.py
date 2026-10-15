"""Small grid router (one layer, 8-connected, octilinear) for short connections in dense areas."""
import heapq, math, numpy as np
import geom

class Router:
    def __init__(self, G, layer, win, step=0.05, cl=0.2, edge_cl=0.25):
        self.G, self.layer, self.win, self.h, self.cl, self.edge_cl = G, layer, win, step, cl, edge_cl
        x0, y0, x1, y1 = win
        self.nx = int(round((x1 - x0)/step)) + 1; self.ny = int(round((y1 - y0)/step)) + 1
        self.xs = x0 + np.arange(self.nx)*step; self.ys = y0 + np.arange(self.ny)*step

    def _blocked(self, net, w, extra_vias=(), extra_segs=(), moved=None, skip=lambda o: False):
        """Boolean grid: True where the centre of a track of width w of `net` would violate clearance."""
        G = self.G; x0, y0 = self.win[0], self.win[1]; h = self.h
        B = np.zeros((self.ny, self.nx), bool)
        X, Y = np.meshgrid(self.xs, self.ys)
        def rect(r, m):
            dx = np.maximum(np.maximum(r[0] - X, X - r[2]), 0); dy = np.maximum(np.maximum(r[1] - Y, Y - r[3]), 0)
            return np.hypot(dx, dy) < m
        def circ(cx, cy, rr): return np.hypot(X - cx, Y - cy) < rr
        def seg(s, m):
            vx, vy = s["x2"] - s["x1"], s["y2"] - s["y1"]; L = vx*vx + vy*vy
            t = np.clip(((X - s["x1"])*vx + (Y - s["y1"])*vy)/L, 0, 1) if L > 0 else 0
            return np.hypot(X - s["x1"] - t*vx, Y - s["y1"] - t*vy) < m
        wx0, wy0, wx1, wy1 = self.win
        near = lambda x, y, r: wx0 - r <= x <= wx1 + r and wy0 - r <= y <= wy1 + r
        moved = moved or {}
        for f in G.fps.values():
            fx, fy, fr = moved.get(f.ref, (f.x, f.y, f.rot))
            pads, _ = f.placed(fx, fy, fr)
            for p in pads:
                if p["net"] == net and net: continue
                on = p["tht"] or self.layer in p["cu"] or (f.layer == self.layer and not p["tht"] and (self.layer in p["cu"] or not p["cu"]))
                if not on: continue
                if not near(p["x"], p["y"], 3): continue
                r = (p["x"] - p["aw"]/2, p["y"] - p["ah"]/2, p["x"] + p["aw"]/2, p["y"] + p["ah"]/2)
                B |= rect(r, self.cl + w/2)
        for v in list(G.vias) + list(extra_vias):
            if skip(v) or (v["net"] == net and net): continue
            if not near(v["x"], v["y"], 2): continue
            B |= circ(v["x"], v["y"], geom._via_r(v) + self.cl + w/2)
        for s in list(G.segs) + list(extra_segs):
            if skip(s) or s["layer"] != self.layer or (s["net"] == net and net): continue
            if not (near(s["x1"], s["y1"], 3) or near(s["x2"], s["y2"], 3)): continue
            B |= seg(s, self.cl + w/2 + s["w"]/2)
        for e in G.edge:
            B |= seg(dict(x1=e[0], y1=e[1], x2=e[2], y2=e[3]), self.edge_cl + w/2)
        return B

    def route(self, a, b, net, w, **kw):
        B = self._blocked(net, w, **kw)
        x0, y0, h = self.win[0], self.win[1], self.h
        ij = lambda p: (int(round((p[1] - y0)/h)), int(round((p[0] - x0)/h)))
        sa, sb = ij(a), ij(b)
        for s in (sa, sb):     # allow the end points themselves (they sit on own pads/vias)
            j, i = s
            B[max(0, j-3):j+4, max(0, i-3):i+4] = False
        moves = [(0, 1, 1), (1, 0, 1), (0, -1, 1), (-1, 0, 1), (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142)]
        INF = 1e18; dist = {sa: 0.0}; prev = {}; pq = [(0.0, sa, None)]
        hfun = lambda s: math.hypot(s[0] - sb[0], s[1] - sb[1])
        while pq:
            f, s, d = heapq.heappop(pq)
            if s == sb: break
            g = dist[s]
            if f - hfun(s) > g + 1e-9: continue
            for dj, di, c in moves:
                n = (s[0] + dj, s[1] + di)
                if not (0 <= n[0] < self.ny and 0 <= n[1] < self.nx) or B[n]: continue
                turn = 0.0 if d is None or d == (dj, di) else 0.6       # discourage zig-zag
                ng = g + c + turn
                if ng < dist.get(n, INF):
                    dist[n] = ng; prev[n] = (s, (dj, di)); heapq.heappush(pq, (ng + hfun(n), n, (dj, di)))
        if sb not in prev and sb != sa: return None
        path = [sb]
        while path[-1] != sa: path.append(prev[path[-1]][0])
        path.reverse()
        pts = [(x0 + i*h, y0 + j*h) for j, i in path]
        # collapse collinear points
        out = [pts[0]]
        for k in range(1, len(pts) - 1):
            ax, ay = out[-1]; bx, by = pts[k]; cx, cy = pts[k+1]
            if abs((bx - ax)*(cy - by) - (by - ay)*(cx - bx)) > 1e-9: out.append(pts[k])
        out.append(pts[-1])
        out[0] = a; out[-1] = b
        return [(round(x, 4), round(y, 4)) for x, y in out]
