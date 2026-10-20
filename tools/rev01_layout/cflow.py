"""DC current spreading in the copper of one net (2.5D resistive model).
- Copper of the net is rasterised per layer on a square grid h (zone fills, tracks, pads; THT pads on every layer):
  35 um copper, 0.49 mOhm per square between neighbouring cells.
- Vias and drilled pads of the net are barrels between the layers where they meet copper of the net (plating 25 um,
  heights from the board stack-up). On each layer the barrel is tied to the copper at its wall only, the cells within
  r = drill/2 + plating (0.175 mm) - not to the whole pad: neighbouring vias of a field (0.5 mm pitch) must not short
  each other through overlapping pads (review 11 P15; with pad discs the result fell with the grid, 0.394 / 0.323 /
  0.196 mOhm at h 0.2 / 0.1 / 0.05). Via sizes are read from the board text (kpcb has no via size).
- Terminals are pads (or areas) tied to one node; sources are fed through a series resistance each (R_ds of a
  transistor), sinks are held at 0 V.
Used by cflow_cases.py; see there for the cases. Python API: Model(board, net, window, h).add_source/add_sink, solve()."""
import sys, math, os
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spla
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/home/alexey/Git/KiCad/InvertorPowerNewGen/bench_2026-10-13/tools"); sys.dont_write_bytecode = True
import kpcb, geom, pcbedit
from matplotlib.path import Path

RHO, T, TPL = 1.72e-8, 35e-6, 25e-6                       # Ohm*m, copper and via plating thickness, m
Z = {"F.Cu": 0.0175, "In1.Cu": 0.1525, "In2.Cu": 0.6725, "In3.Cu": 0.8075, "In4.Cu": 1.3275, "B.Cu": 1.4625}   # mm
LAYERS = list(Z)
GSQ = T / RHO                                              # S between two neighbouring square cells
GBIG = 1e5

class Model:
    def __init__(self, fn, net, win, h=0.1, K=None, G=None):
        self.fn, self.net, self.win, self.h = fn, net, win, h
        self.K = K or kpcb.load(fn); self.G = G or geom.Board(fn)
        x0, y0, x1, y1 = win
        self.nx, self.ny = int(round((x1 - x0)/h)), int(round((y1 - y0)/h))
        self.xs = x0 + (np.arange(self.nx) + 0.5)*h; self.ys = y0 + (np.arange(self.ny) + 0.5)*h
        self.X, self.Y = np.meshgrid(self.xs, self.ys)
        self.mask = {l: np.zeros((self.ny, self.nx), bool) for l in LAYERS}
        self.via_size = {(round(v["x"], 3), round(v["y"], 3), v["net"]): v["size"] for v in pcbedit.Board(fn).vias()}
        self._raster()
        self.padmask = {l: np.zeros((self.ny, self.nx), bool) for l in LAYERS}
        keep = self.mask; self.mask = self.padmask
        for f in self.G.fps.values():                      # pad copper alone (kept by drop_layer)
            for p in f.placed()[0]:
                if p["net"] != net: continue
                for l in self.pad_layers(f, p):
                    if p["tht"]: self._capsule(l, p["x"], p["y"], p["x"], p["y"], min(p["aw"], p["ah"])/2)
                    else: self._rect(l, (p["x"] - p["aw"]/2, p["y"] - p["ah"]/2, p["x"] + p["aw"]/2, p["y"] + p["ah"]/2))
        self.mask = keep
        for l in LAYERS: self.padmask[l] &= self.mask[l]
        self.extra = []          # (node a, node b, G) between extra nodes / cells, filled at solve time
        self.sources, self.sinks = [], []

    # ------------------------------------------------------------ rasterisation
    def drop_layer(self, l):
        """The net keeps only its pads on layer l (what the layer is worth: compare resistances)."""
        self.mask[l] = self.padmask[l].copy()

    def _win_idx(self, bx0, by0, bx1, by1):
        h, (x0, y0, _, _) = self.h, self.win
        i0 = max(0, int((bx0 - x0)/h) - 1); i1 = min(self.nx, int((bx1 - x0)/h) + 2)
        j0 = max(0, int((by0 - y0)/h) - 1); j1 = min(self.ny, int((by1 - y0)/h) + 2)
        return j0, j1, i0, i1

    def _poly(self, l, pts):
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        j0, j1, i0, i1 = self._win_idx(min(xs), min(ys), max(xs), max(ys))
        if j1 <= j0 or i1 <= i0: return
        P = np.c_[self.X[j0:j1, i0:i1].ravel(), self.Y[j0:j1, i0:i1].ravel()]
        self.mask[l][j0:j1, i0:i1] |= Path(pts).contains_points(P).reshape(j1 - j0, i1 - i0)

    def _capsule(self, l, ax, ay, bx, by, r):
        j0, j1, i0, i1 = self._win_idx(min(ax, bx) - r, min(ay, by) - r, max(ax, bx) + r, max(ay, by) + r)
        if j1 <= j0 or i1 <= i0: return
        X, Y = self.X[j0:j1, i0:i1], self.Y[j0:j1, i0:i1]
        vx, vy = bx - ax, by - ay; L = vx*vx + vy*vy
        t = np.clip(((X - ax)*vx + (Y - ay)*vy)/L, 0, 1) if L > 0 else 0
        self.mask[l][j0:j1, i0:i1] |= np.hypot(X - ax - t*vx, Y - ay - t*vy) <= r

    def _rect(self, l, r):
        j0, j1, i0, i1 = self._win_idx(*r)
        X, Y = self.X[j0:j1, i0:i1], self.Y[j0:j1, i0:i1]
        self.mask[l][j0:j1, i0:i1] |= (X >= r[0]) & (X <= r[2]) & (Y >= r[1]) & (Y <= r[3])

    def pad_layers(self, f, p):
        return LAYERS if p["tht"] else [l for l in LAYERS if l in p["cu"] or ("*.Cu" in p["cu"] and l == f.layer)] or [f.layer]

    def _raster(self):
        net = self.net
        for z in self.K["zones"]:
            if z["net"] != net: continue
            for l, pts in z["fills"]:
                if l in self.mask and len(pts) > 2: self._poly(l, pts)
        for s in self.K["segs"]:
            if s["net"] == net and s["layer"] in self.mask: self._capsule(s["layer"], s["x1"], s["y1"], s["x2"], s["y2"], s["w"]/2)
        self.barrels = []        # (x, y, drill, radius, name)
        for f in self.G.fps.values():
            for p in f.placed()[0]:
                if p["net"] != net: continue
                r = (p["x"] - p["aw"]/2, p["y"] - p["ah"]/2, p["x"] + p["aw"]/2, p["y"] + p["ah"]/2)
                for l in self.pad_layers(f, p):
                    if p["tht"]:
                        if self._touches(l, p["x"], p["y"], max(p["aw"], p["ah"])/2 + 0.15): self._capsule(l, p["x"], p["y"], p["x"], p["y"], min(p["aw"], p["ah"])/2)
                    else: self._rect(l, r)
                if p["tht"] and p["drill"] > 0:
                    self.barrels.append((p["x"], p["y"], p["drill"], p["drill"]/2 + TPL*1e3, f"{f.ref}.{p['name']}"))
        for v in self.K["vias"]:
            if v["net"] != net: continue
            size = self.via_size.get((round(v["x"], 3), round(v["y"], 3), v["net"]), 0.6 if v["d"] >= 0.3 else 0.5)
            for l in LAYERS:
                if self._touches(l, v["x"], v["y"], size/2 + 0.15): self._capsule(l, v["x"], v["y"], v["x"], v["y"], size/2)
            self.barrels.append((v["x"], v["y"], v["d"], v["d"]/2 + TPL*1e3, "via"))

    def _touches(self, l, x, y, r):
        j0, j1, i0, i1 = self._win_idx(x - r, y - r, x + r, y + r)
        if j1 <= j0 or i1 <= i0: return False
        m = np.hypot(self.X[j0:j1, i0:i1] - x, self.Y[j0:j1, i0:i1] - y) <= r
        return bool((self.mask[l][j0:j1, i0:i1] & m).any())

    def cells_in(self, l, shape):
        """Cells of the net copper on layer l inside a rect (x0,y0,x1,y1) or circle (x,y,r)."""
        if len(shape) == 4:
            j0, j1, i0, i1 = self._win_idx(*shape); X, Y = self.X[j0:j1, i0:i1], self.Y[j0:j1, i0:i1]
            m = (X >= shape[0]) & (X <= shape[2]) & (Y >= shape[1]) & (Y <= shape[3])
        else:
            x, y, r = shape; j0, j1, i0, i1 = self._win_idx(x - r, y - r, x + r, y + r)
            X, Y = self.X[j0:j1, i0:i1], self.Y[j0:j1, i0:i1]; m = np.hypot(X - x, Y - y) <= r
        m &= self.mask[l][j0:j1, i0:i1]
        jj, ii = np.nonzero(m); return [(l, j + j0, i + i0) for j, i in zip(jj, ii)]

    def pad_cells(self, ref, names=None):
        f = self.G.fps[ref]; out = []
        for p in f.placed()[0]:
            if p["net"] != self.net or (names and p["name"] not in names): continue
            for l in self.pad_layers(f, p):
                if p["tht"]: out += self.cells_in(l, (p["x"], p["y"], min(p["aw"], p["ah"])/2))
                else: out += self.cells_in(l, (p["x"] - p["aw"]/2, p["y"] - p["ah"]/2, p["x"] + p["aw"]/2, p["y"] + p["ah"]/2))
        return out

    def add_source(self, name, cells, r_series):
        self.sources.append((name, cells, r_series))

    def add_sink(self, name, cells):
        self.sinks.append((name, cells))

    # ------------------------------------------------------------ solve
    def solve(self, I):
        n = 0; self.gidx = {}
        for l in LAYERS:
            g = -np.ones((self.ny, self.nx), np.int64); m = self.mask[l]
            g[m] = n + np.arange(m.sum()); n += int(m.sum()); self.gidx[l] = g
        R, C, Vv = [], [], []
        self.h_edges = {}                         # layer -> axis -> (j, i, a, b)
        for l in LAYERS:
            g = self.gidx[l]; self.h_edges[l] = {}
            for axis, (dj, di) in ((0, (0, 1)), (1, (1, 0))):
                A = g[:g.shape[0]-dj, :g.shape[1]-di]; B = g[dj:, di:]
                ok = (A >= 0) & (B >= 0); jj, ii = np.nonzero(ok)
                a, b = A[ok], B[ok]
                R.append(a); C.append(b); Vv.append(np.full(len(a), GSQ)); self.h_edges[l][axis] = (jj, ii, a, b)
        def cidx(cells): return np.array([self.gidx[l][j, i] for l, j, i in cells], np.int64)
        self.cell_x = np.zeros(n); self.cell_y = np.zeros(n)
        for l in LAYERS:
            g = self.gidx[l]; m = g >= 0; self.cell_x[g[m]] = self.X[m]; self.cell_y[g[m]] = self.Y[m]
        self.pad_edges = []                       # (layer, via node, cell indices, x, y) of barrel pads
        extra_r, extra_c, extra_v = [], [], []
        def edge(a, b, g): extra_r.append(a); extra_c.append(b); extra_v.append(g)
        self.via_edges = []
        for k, (x, y, d, r, name) in enumerate(self.barrels):
            nodes = []
            for l in LAYERS:
                cs = self.cells_in(l, (x, y, r))
                if not cs and self.cells_in(l, (x, y, r + 0.75*self.h)):          # coarse grid: the nearest cell
                    c = self.cells_in(l, (x, y, r + 0.75*self.h))
                    cs = [min(c, key=lambda q: (self.xs[q[2]] - x)**2 + (self.ys[q[1]] - y)**2)]
                if not cs: continue
                vn = n; n += 1; ci = cidx(cs)
                for c in ci: edge(vn, c, GBIG)
                nodes.append((l, vn)); self.pad_edges.append((l, vn, ci, x, y))
            for (la, a), (lb, b) in zip(nodes, nodes[1:]):
                gv = math.pi*(d*1e-3)*TPL/(RHO*(Z[lb] - Z[la])*1e-3)
                edge(a, b, gv); self.via_edges.append((k, la, lb, a, b, gv))
        S = n; n += 1; self.term = {}
        for name, cells, rs in self.sources:
            tn = n; n += 1
            for c in cidx(cells): edge(tn, c, GBIG)
            edge(S, tn, 1.0/rs); self.term[name] = (tn, rs)
        sink_nodes = []
        for name, cells in self.sinks:
            tn = n; n += 1
            for c in cidx(cells): edge(tn, c, GBIG)
            sink_nodes.append(tn); self.term[name] = (tn, None)
        rows = np.concatenate(R + [np.array(extra_r, np.int64)]); cols = np.concatenate(C + [np.array(extra_c, np.int64)])
        vals = np.concatenate(Vv + [np.array(extra_v, float)])
        Gm = sp.coo_matrix((np.r_[-vals, -vals], (np.r_[rows, cols], np.r_[cols, rows])), shape=(n, n)).tocsr()
        Gm = Gm + sp.diags(-np.asarray(Gm.sum(axis=1)).ravel())
        # copper not connected to the sink: drop it (singular otherwise)
        ncomp, lab = sp.csgraph.connected_components(Gm, directed=False)
        live = np.isin(lab, np.unique(lab[sink_nodes]))
        keep = live.copy(); keep[sink_nodes] = False
        b = np.zeros(n); b[S] = I
        v = np.zeros(n); v[keep] = spla.spsolve(Gm[keep][:, keep].tocsc(), b[keep])
        self.V, self.I, self.S, self.n, self.live = v, I, S, n, live
        return v

    # ------------------------------------------------------------ results
    def r_total(self): return self.V[self.S] / self.I

    def source_currents(self):
        return {name: (self.V[self.S] - self.V[tn]) / rs for name, (tn, rs) in self.term.items() if rs}

    def layer_cut(self, y=None, x=None, rng=None):
        """Current per layer leaving the region y' < y (or x' < x) - positive towards +y (+x); rng limits the other
        coordinate. Via pads belong to the side of their centre, so the layers add up to the whole current."""
        out = {}; h = self.h; x0, y0 = self.win[0], self.win[1]
        for l in LAYERS:
            if y is not None:
                jj, ii, a, b = self.h_edges[l][1]; sel = np.abs(y0 + (jj + 1)*h - y) < h/2
                if rng: sel &= (self.xs[ii] >= rng[0]) & (self.xs[ii] <= rng[1])
            else:
                jj, ii, a, b = self.h_edges[l][0]; sel = np.abs(x0 + (ii + 1)*h - x) < h/2
                if rng: sel &= (self.ys[jj] >= rng[0]) & (self.ys[jj] <= rng[1])
            tot = float(((self.V[a[sel]] - self.V[b[sel]]) * GSQ).sum())
            for ll, vn, ci, bx, by in self.pad_edges:
                if ll != l: continue
                c, o = (by, self.cell_y[ci]) if y is not None else (bx, self.cell_x[ci])
                cut = y if y is not None else x
                if rng:
                    oc = bx if y is not None else by
                    if not rng[0] - 0.5 <= oc <= rng[1] + 0.5: continue
                if c < cut:                       # via node inside: flow to cells outside
                    out_c = ci[o >= cut]; tot += float(((self.V[vn] - self.V[out_c]) * GBIG).sum())
                else:                             # via node outside: flow from cells inside
                    in_c = ci[o < cut]; tot += float(((self.V[in_c] - self.V[vn]) * GBIG).sum())
            out[l] = tot
        return out

    def density(self, l):
        """|J| in A/mm2 per cell of layer l (NaN outside the copper)."""
        ny, nx = self.ny, self.nx; jx = np.zeros((ny, nx)); jy = np.zeros((ny, nx)); cx = np.zeros((ny, nx)); cy = np.zeros((ny, nx))
        jj, ii, a, b = self.h_edges[l][0]; cur = (self.V[a] - self.V[b]) * GSQ
        np.add.at(jx, (jj, ii), cur); np.add.at(jx, (jj, ii + 1), cur); np.add.at(cx, (jj, ii), 1); np.add.at(cx, (jj, ii + 1), 1)
        jj, ii, a, b = self.h_edges[l][1]; cur = (self.V[a] - self.V[b]) * GSQ
        np.add.at(jy, (jj, ii), cur); np.add.at(jy, (jj + 1, ii), cur); np.add.at(cy, (jj, ii), 1); np.add.at(cy, (jj + 1, ii), 1)
        J = np.hypot(jx/np.maximum(cx, 1), jy/np.maximum(cy, 1)) / (self.h * T*1e3)
        return np.where(self.mask[l], J, np.nan)

    def layer_loss(self):
        out = {}
        for l in LAYERS:
            out[l] = float(sum(((self.V[a] - self.V[b])**2 * GSQ).sum() for jj, ii, a, b in self.h_edges[l].values()))
        vias = sum((self.V[a] - self.V[b])**2 * g for _, _, _, a, b, g in self.via_edges)
        return out, vias

    def barrel_currents(self):
        """Per barrel index: list of (layer a, layer b, current a->b)."""
        out = {}
        for k, la, lb, a, b, g in self.via_edges: out.setdefault(k, []).append((la, lb, (self.V[a] - self.V[b])*g))
        return out

def clean_y(M, y, step=0.05, span=1.0):
    """Nearest grid line to y that crosses no via / drilled pad of the net (their pads are tied to the barrel)."""
    h, y0 = M.h, M.win[1]
    cands = sorted((y0 + k*h for k in range(1, M.ny)), key=lambda c: abs(c - y))
    for c in cands:
        if abs(c - y) > span: break
        if all(abs(c - by) > br + h for bx, by, d, br, nm in M.barrels): return round(c, 3)
    return None

def plot(M, out, layers=None, vmax=None, title="", marks=(), crop=None, extra=None):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    layers = [l for l in (layers or LAYERS) if M.mask[l].any()]
    x0, y0, x1, y1 = crop or M.win; sc = 0.32 if not crop else min(0.9, 12.0/max(x1 - x0, y1 - y0)); w = (x1 - x0)*sc; hgt = (y1 - y0)*sc
    fig, axs = plt.subplots(1, len(layers), figsize=(w*len(layers) + 1, hgt + 0.8), squeeze=False)
    cur = M.barrel_currents()
    Js = {l: M.density(l) for l in layers}
    vmax = vmax or np.nanpercentile(np.concatenate([J[~np.isnan(J)] for J in Js.values()]), 99.5)
    for ax, l in zip(axs[0], layers):
        wx0, wy0, wx1, wy1 = M.win
        im = ax.imshow(Js[l], extent=(wx0, wx1, wy1, wy0), cmap="inferno", vmin=0, vmax=vmax, interpolation="nearest")
        if extra is not None: extra(ax, l)
        for k, (bx, by, d, br, nm) in enumerate(M.barrels):
            tr = max((abs(c) for la, lb, c in cur.get(k, []) if Z[la] <= Z[l] <= Z[lb] or Z[lb] <= Z[l] <= Z[la]), default=0)
            if not (x0 - 1 < bx < x1 + 1 and y0 - 1 < by < y1 + 1): continue
            ax.add_patch(Circle((bx, by), br, fc="none", ec="cyan" if tr > 0.5 else "#557", lw=0.4 + min(tr, 10)*0.15))
            if crop and tr > 0.5: ax.text(bx, by, f"{tr:.0f}", fontsize=4, color="cyan", ha="center", va="center")
        for mx, my in marks: ax.plot(mx, my, "+", color="lime", ms=6)
        ax.set_title(f"{l}  max {np.nanmax(Js[l]):.0f} A/mm2", fontsize=8); ax.tick_params(labelsize=5)
        ax.set_xlim(x0, x1); ax.set_ylim(y1, y0)
    fig.colorbar(im, ax=axs[0].tolist(), fraction=0.02, pad=0.01).ax.tick_params(labelsize=6)
    fig.suptitle(title, fontsize=9); plt.savefig(out, dpi=120); plt.close(fig)

def via_gain(M, I, d=0.3):
    """Where a new through via of the net would lower the resistance most: first order dR = -g*dV^2/I^2, g the
    barrel between the outermost layers of the net copper at the spot. Returns a grid (uOhm, positive = gain).
    Only live copper counts: an island cut off from the sink has no solved potential (V = 0), and taking that 0 as real
    once showed 17 uOhm per via where a via only joins dead copper (GND A by the right slot, 2026-10-20)."""
    Vl = {l: np.where((M.gidx[l] >= 0) & M.live[np.maximum(M.gidx[l], 0)], M.V[np.maximum(M.gidx[l], 0)], np.nan) for l in LAYERS}
    st = np.stack([Vl[l] for l in LAYERS]); zz = np.array([Z[l] for l in LAYERS])[:, None, None]
    have = ~np.isnan(st)
    vmax = np.nanmax(np.where(have, st, -np.inf), axis=0); vmin = np.nanmin(np.where(have, st, np.inf), axis=0)
    zmax = np.max(np.where(have, zz, -np.inf), axis=0); zmin = np.min(np.where(have, zz, np.inf), axis=0)
    dz = np.maximum(zmax - zmin, 0.1)
    g = math.pi*(d*1e-3)*TPL/(RHO*dz*1e-3)
    out = np.where(have.sum(axis=0) >= 2, g*(vmax - vmin)**2 / I**2 * 1e6, np.nan)
    return out

def idle_barrels(M, frac=0.002):
    """Barrels moving less than frac of the total current between layers."""
    cur = M.barrel_currents(); out = []
    for k, (x, y, d, r, nm) in enumerate(M.barrels):
        t = max((abs(c) for _, _, c in cur.get(k, [])), default=0.0)
        if t < frac*M.I: out.append((x, y, nm, t))
    return out

def legal_via(G, net, x, y, size=0.6, drill=0.3, cl=0.2, pad_cl=0.5, others=()):
    """A through via of `net` at (x, y): 0.2 mm to other-net vias and tracks, 0.5 mm to other-net pads (the power
    and snubber pads carry 0.5 mm local clearances), not under a footprint courtyard, 0.25 mm to the edge.
    others: vias (dict x, y, net, size, d) planned elsewhere, checked as if they were on the board."""
    v = geom.V(x, y, net, size, drill)
    if [e for e in G.check_items(vias=[v] + list(others), cl=cl) if e[1][1:] == (x, y) or (len(e) > 2 and isinstance(e[2], tuple) and e[2][1:] == (x, y))]: return False
    if any(geom.d_pt_seg(x, y, *e) < size/2 + 0.25 for e in G.edge): return False
    for f in G.fps.values():
        pads, crt = f.placed()
        if crt and crt[0] < x < crt[2] and crt[1] < y < crt[3]: return False
        for p in pads:
            if p["net"] == net: continue
            r = (p["x"] - p["aw"]/2, p["y"] - p["ah"]/2, p["x"] + p["aw"]/2, p["y"] + p["ah"]/2)
            if geom.d_pt_rect(x, y, r) - size/2 < pad_cl: return False
    return True

def best_vias(M, I, n=10, sep=0.9, step=0.25, region=None, others=()):
    """Up to n legal new through vias with the largest first-order gain (uOhm each), >= sep from every barrel of the
    net and from each other. region = (x0, y0, x1, y1) limits the search."""
    gain = via_gain(M, I); out = []
    order = np.argsort(np.nan_to_num(gain, nan=-1).ravel())[::-1]
    taken = [(bx, by) for bx, by, d, r, nm in M.barrels]
    for k in order[:20000]:
        j, i = divmod(int(k), M.nx); gv = gain[j, i]
        if not gv > 0: break
        x = round(round(M.xs[i]/step)*step, 3); y = round(round(M.ys[j]/step)*step, 3)
        if region and not (region[0] <= x <= region[2] and region[1] <= y <= region[3]): continue
        if any((x - a)**2 + (y - b)**2 < sep*sep for a, b in taken): continue
        if not legal_via(M.G, M.net, x, y, others=others): continue
        out.append((x, y, float(gv))); taken.append((x, y))
        if len(out) >= n: break
    return out

def add_vias(M, pts, size=0.6, drill=0.3):
    for x, y in pts:
        for l in LAYERS:
            if M._touches(l, x, y, size/2 + 0.15): M._capsule(l, x, y, x, y, size/2)
        M.barrels.append((x, y, drill, drill/2 + TPL*1e3, "new"))

def near_pad(M, rect, dist=2.0, ring=(0.2, 0.5), layer="B.Cu"):
    """Copper loss (W) within `dist` of a pad rect (all layers) and the 99th percentile |J| (A/mm2) in a ring around
    it on `layer` - the single-cell peak at the pad corner is singular and grows with the grid (review 11 P15)."""
    def dmap():
        dx = np.maximum(np.maximum(rect[0] - M.X, M.X - rect[2]), 0); dy = np.maximum(np.maximum(rect[1] - M.Y, M.Y - rect[3]), 0)
        return np.hypot(dx, dy)
    d = dmap(); loss = 0.0
    for l in LAYERS:
        for axis in (0, 1):
            jj, ii, a, b = M.h_edges[l][axis]
            sel = d[jj, ii] <= dist
            loss += float((((M.V[a] - M.V[b])**2) * GSQ)[sel].sum())
    J = M.density(layer); r = (d >= ring[0]) & (d <= ring[1]) & ~np.isnan(J)
    return loss, float(np.percentile(J[r], 99)) if r.any() else float("nan")
