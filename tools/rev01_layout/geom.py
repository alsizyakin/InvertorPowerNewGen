"""Geometry model of a .kicad_pcb for placement checks (axis-aligned pads, rotations multiple of 90 deg)."""
import re, math, sys
sys.path.insert(0, "/home/alexey/Git/KiCad/InvertorPowerNewGen/bench_2026-10-13/tools"); sys.dont_write_bytecode = True
import kpcb

def _blocks(s, tag, indent="\t"):
    for m in re.finditer(r'\n' + indent + r'\(' + tag + r'\b', s):
        i = m.start() + 1 + len(indent); d = 0
        for k in range(i, len(s)):
            if s[k] == "(": d += 1
            elif s[k] == ")":
                d -= 1
                if d == 0: yield i, k + 1; break

def rot_pt(px, py, rot):
    a = math.radians(-rot); return px*math.cos(a) - py*math.sin(a), px*math.sin(a) + py*math.cos(a)

class FP:
    """Footprint with local geometry: pads (name, lx, ly, w, h, shape, net, layers, tht, drill) and courtyard bbox."""
    def __init__(self, txt):
        self.lib = re.match(r'\(footprint "([^"]+)"', txt).group(1)
        self.layer = re.search(r'\n\t\t\(layer "([^"]+)"\)', txt).group(1)
        at = re.search(r'\n\t\t\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)', txt)
        self.x, self.y, self.rot = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
        self.ref = re.search(r'\(property "Reference" "([^"]+)"', txt).group(1)
        self.pads = []
        for a, b in _blocks(txt, "pad", "\t\t"):
            p = txt[a:b]
            nm, typ, shape = re.match(r'\(pad "([^"]*)" (\w+) (\w+)', p).groups()
            pat = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)', p)
            sz = re.search(r'\(size ([\d.]+) ([\d.]+)\)', p)
            net = re.search(r'\(net "([^"]*)"\)', p); dr = re.search(r'\(drill ([\d.]+)', p)
            lays = re.search(r'\(layers ([^)]*)\)', p).group(1)
            self.pads.append(dict(name=nm, lx=float(pat.group(1)), ly=float(pat.group(2)), w=float(sz.group(1)), h=float(sz.group(2)),
                                  pang=float(pat.group(3) or 0) - self.rot, shape=shape, net=net.group(1) if net else "",
                                  tht=typ in ("thru_hole", "np_thru_hole"), drill=float(dr.group(1)) if dr else 0.0,
                                  cu=[l for l in re.findall(r'"([^"]+)"', lays) if l.endswith(".Cu") or l == "*.Cu"]))
        pts = []
        for kind in ("fp_line", "fp_rect", "fp_poly", "fp_circle", "fp_arc"):
            for a, b in _blocks(txt, kind, "\t\t"):
                g = txt[a:b]
                if '"F.CrtYd"' in g or '"B.CrtYd"' in g:
                    pts += [(float(u), float(v)) for u, v in re.findall(r'\((?:start|end|xy|center|mid) ([\d.\-]+) ([\d.\-]+)\)', g)]
        self.crt = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)) if pts else None

    def placed(self, x=None, y=None, rot=None):
        x = self.x if x is None else x; y = self.y if y is None else y; rot = self.rot if rot is None else rot
        out = []
        for p in self.pads:
            dx, dy = rot_pt(p["lx"], p["ly"], rot)
            ang = (rot + p["pang"]) % 180
            w, h = (p["w"], p["h"]) if abs(ang) < 1 or abs(ang - 180) < 1 else (p["h"], p["w"])
            out.append(dict(p, x=x+dx, y=y+dy, aw=w, ah=h))
        crt = None
        if self.crt:
            cs = [rot_pt(u, v, rot) for u, v in ((self.crt[0], self.crt[1]), (self.crt[2], self.crt[3]))]
            crt = (x + min(c[0] for c in cs), y + min(c[1] for c in cs), x + max(c[0] for c in cs), y + max(c[1] for c in cs))
        return out, crt

def layers_of(p, fp_layer):
    if p["tht"]: return "ALL"
    return set(l for l in p["cu"] if l != "*.Cu") or {fp_layer}

def d_rect_rect(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0); dy = max(a[1] - b[3], b[1] - a[3], 0); return math.hypot(dx, dy)
def d_pt_rect(x, y, r):
    dx = max(r[0] - x, 0, x - r[2]); dy = max(r[1] - y, 0, y - r[3]); return math.hypot(dx, dy)
def d_pt_seg(px, py, x1, y1, x2, y2):
    vx, vy = x2-x1, y2-y1; L = vx*vx + vy*vy
    t = 0 if L == 0 else max(0, min(1, ((px-x1)*vx + (py-y1)*vy)/L)); return math.hypot(px-x1-t*vx, py-y1-t*vy)
def d_seg_rect(x1, y1, x2, y2, r):
    if d_pt_rect(x1, y1, r) == 0 or d_pt_rect(x2, y2, r) == 0: return 0.0
    # sample-free: min of endpoint-to-rect and corner-to-segment, plus crossing test
    corners = [(r[0], r[1]), (r[2], r[1]), (r[2], r[3]), (r[0], r[3])]
    d = min([d_pt_rect(x1, y1, r), d_pt_rect(x2, y2, r)] + [d_pt_seg(cx, cy, x1, y1, x2, y2) for cx, cy in corners])
    # crossing through the rect (both endpoints outside on opposite sides)
    for k in range(4):
        (ax, ay), (bx, by) = corners[k], corners[(k+1) % 4]
        if _cross(x1, y1, x2, y2, ax, ay, bx, by): return 0.0
    return d
def _cross(x1, y1, x2, y2, x3, y3, x4, y4):
    def o(ax, ay, bx, by, cx, cy): return (bx-ax)*(cy-ay) - (by-ay)*(cx-ax)
    return (o(x1, y1, x2, y2, x3, y3) * o(x1, y1, x2, y2, x4, y4) < 0) and (o(x3, y3, x4, y4, x1, y1) * o(x3, y3, x4, y4, x2, y2) < 0)
def d_seg_seg(a, b):
    if _cross(*a, *b): return 0.0
    return min(d_pt_seg(a[0], a[1], *b), d_pt_seg(a[2], a[3], *b), d_pt_seg(b[0], b[1], *a), d_pt_seg(b[2], b[3], *a))

class Board:
    def __init__(self, path):
        s = open(path, encoding="utf-8").read(); self.s = s
        self.fps = {}
        for a, b in _blocks(s, "footprint"):
            f = FP(s[a:b]); self.fps[f.ref] = f
        K = kpcb.load(path)
        self.vias = K["vias"]; self.segs = K["segs"]
        xs = []
        for a, b in _blocks(s, "gr_line"):
            g = s[a:b]
            if '"Edge.Cuts"' in g: xs.append(g)
        self.edge = []
        for g in [s[a:b] for a, b in list(_blocks(s, "gr_line")) + list(_blocks(s, "gr_arc")) if '"Edge.Cuts"' in s[a:b]]:
            pts = [(float(u), float(v)) for u, v in re.findall(r'\((?:start|mid|end) ([\d.\-]+) ([\d.\-]+)\)', g)]
            for i in range(len(pts) - 1): self.edge.append((pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1]))

    def check(self, ref, x, y, rot, moved=None, cl=0.2, crt_gap=0.0, ignore_refs=(), extra_vias=(), extra_segs=(), shrink=0.25):
        """Violations of footprint `ref` placed at (x, y, rot) against the board (and other moved footprints)."""
        moved = moved or {}
        f = self.fps[ref]; pads, crt = f.placed(x, y, rot); out = []
        def rect(p): return (p["x"]-p["aw"]/2, p["y"]-p["ah"]/2, p["x"]+p["aw"]/2, p["y"]+p["ah"]/2)
        for o in self.fps.values():
            if o.ref == ref or o.ref in ignore_refs: continue
            ox, oy, orr = moved.get(o.ref, (o.x, o.y, o.rot))
            opads, ocrt = o.placed(ox, oy, orr)
            if crt and ocrt and o.layer == f.layer:
                a = (crt[0]+shrink, crt[1]+shrink, crt[2]-shrink, crt[3]-shrink); b = (ocrt[0]+shrink, ocrt[1]+shrink, ocrt[2]-shrink, ocrt[3]-shrink)
                if min(a[2], b[2]) - max(a[0], b[0]) > 1e-6 and min(a[3], b[3]) - max(a[1], b[1]) > 1e-6:
                    out.append(("body", o.ref))
            for p in pads:
                pl = layers_of(p, f.layer)
                for q in opads:
                    ql = layers_of(q, o.layer)
                    if pl != "ALL" and ql != "ALL" and not (pl & ql): continue
                    if p["net"] and p["net"] == q["net"]: continue
                    if d_rect_rect(rect(p), rect(q)) < cl - 1e-6: out.append(("pad", f"{ref}.{p['name']}", f"{o.ref}.{q['name']}", round(d_rect_rect(rect(p), rect(q)), 3)))
        for p in pads:
            pl = layers_of(p, f.layer)
            for v in list(self.vias) + list(extra_vias):
                if p["net"] and p["net"] == v["net"]: continue
                r = 0.3 if v.get("size", 0.6 if v["d"] >= 0.3 else 0.5) >= 0.6 else 0.25
                if d_pt_rect(v["x"], v["y"], rect(p)) - r < cl - 1e-6:
                    out.append(("via", f"{ref}.{p['name']}", v["net"], (round(v["x"], 2), round(v["y"], 2))))
            for sg in list(self.segs) + list(extra_segs):
                if pl != "ALL" and sg["layer"] not in pl: continue
                if p["net"] and p["net"] == sg["net"]: continue
                d = d_seg_rect(sg["x1"], sg["y1"], sg["x2"], sg["y2"], rect(p)) - sg["w"]/2
                if d < cl - 1e-6: out.append(("track", f"{ref}.{p['name']}", sg["net"], sg["layer"], round(d, 3)))
            for e in self.edge:
                if d_seg_rect(*e, rect(p)) < 0.25: out.append(("edge", f"{ref}.{p['name']}"))
        return out

def _via_r(v):
    return v.get("size", 0.6 if v["d"] >= 0.3 else 0.5) / 2

def check_items(self, vias=(), segs=(), cl=0.2, hole_cl=0.25, skip_vias=(), skip_segs=()):
    """Check new vias (dict x,y,net,size,d) and segments (dict x1..y2,w,layer,net) against the board (pads incl. THT,
    existing vias and tracks) and against each other. skip_* : predicates to ignore existing items (being deleted)."""
    out = []
    pads = []
    for f in self.fps.values():
        pp, _ = f.placed()
        for p in pp:
            pads.append((f, p, (p["x"]-p["aw"]/2, p["y"]-p["ah"]/2, p["x"]+p["aw"]/2, p["y"]+p["ah"]/2)))
    ev = [v for v in self.vias if not any(k(v) for k in skip_vias)]
    es = [s for s in self.segs if not any(k(s) for k in skip_segs)]
    allv = ev + list(vias); alls = es + list(segs)
    for i, v in enumerate(vias):
        r = _via_r(v)
        for f, p, rc in pads:
            if p["net"] == v["net"] and p["net"]: continue
            d = d_pt_rect(v["x"], v["y"], rc) - r
            if d < cl - 1e-6: out.append(("via-pad", (v["net"][-10:], v["x"], v["y"]), f"{f.ref}.{p['name']}", round(d, 3)))
        for o in allv:
            if o is v: continue
            dd = math.hypot(o["x"]-v["x"], o["y"]-v["y"])
            if o["net"] != v["net"] and dd - r - _via_r(o) < cl - 1e-6:
                out.append(("via-via", (v["net"][-10:], v["x"], v["y"]), (o["net"][-10:], o["x"], o["y"]), round(dd - r - _via_r(o), 3)))
            elif dd - v.get("d", 0.3)/2 - o.get("d", 0.3)/2 < hole_cl - 1e-6 and dd > 1e-6:
                out.append(("hole-hole", (v["x"], v["y"]), (o["x"], o["y"])))
        for s in alls:
            if s["net"] == v["net"]: continue
            d = d_pt_seg(v["x"], v["y"], s["x1"], s["y1"], s["x2"], s["y2"]) - r - s["w"]/2
            if d < cl - 1e-6: out.append(("via-seg", (v["net"][-10:], v["x"], v["y"]), (s["net"][-10:], s["layer"]), round(d, 3)))
    for s in segs:
        for f, p, rc in pads:
            if p["net"] == s["net"]: continue
            if not (p["tht"] or (f.layer == s["layer"] and s["layer"] in p["cu"]) or s["layer"] in p["cu"]): continue
            d = d_seg_rect(s["x1"], s["y1"], s["x2"], s["y2"], rc) - s["w"]/2
            if d < cl - 1e-6: out.append(("seg-pad", (s["net"][-10:], s["layer"], s["x1"], s["y1"]), f"{f.ref}.{p['name']}", round(d, 3)))
        for v in ev:
            if v["net"] == s["net"]: continue
            d = d_pt_seg(v["x"], v["y"], s["x1"], s["y1"], s["x2"], s["y2"]) - _via_r(v) - s["w"]/2
            if d < cl - 1e-6: out.append(("seg-via", (s["net"][-10:], s["layer"], s["x1"], s["y1"]), (v["net"][-10:], v["x"], v["y"]), round(d, 3)))
        for o in alls:
            if o is s or o["layer"] != s["layer"] or o["net"] == s["net"]: continue
            d = d_seg_seg((s["x1"], s["y1"], s["x2"], s["y2"]), (o["x1"], o["y1"], o["x2"], o["y2"])) - s["w"]/2 - o["w"]/2
            if d < cl - 1e-6: out.append(("seg-seg", (s["net"][-10:], s["layer"], s["x1"], s["y1"]), (o["net"][-10:], o["x1"], o["y1"]), round(d, 3)))
        for e in self.edge:
            if d_seg_seg((s["x1"], s["y1"], s["x2"], s["y2"]), e) - s["w"]/2 < 0.25: out.append(("seg-edge", (s["net"][-10:], s["x1"], s["y1"])))
    return out
Board.check_items = check_items

def P(points, w, layer, net):
    return [dict(x1=a[0], y1=a[1], x2=b[0], y2=b[1], w=w, layer=layer, net=net) for a, b in zip(points, points[1:])]
def V(x, y, net, size=0.6, d=0.3):
    return dict(x=x, y=y, net=net, size=size, d=d)

# ---------------------------------------------------------------- fast spatially-filtered check
def _bbox_of(pads, crt):
    xs = [p["x"] - p["aw"]/2 for p in pads] + [p["x"] + p["aw"]/2 for p in pads]
    ys = [p["y"] - p["ah"]/2 for p in pads] + [p["y"] + p["ah"]/2 for p in pads]
    if crt: xs += [crt[0], crt[2]]; ys += [crt[1], crt[3]]
    return (min(xs), min(ys), max(xs), max(ys))

def _cache(self):
    if getattr(self, "_pc", None) is None:
        self._pc = {r: f.placed() for r, f in self.fps.items()}
        self._bb = {r: _bbox_of(*v) for r, v in self._pc.items()}
    return self._pc, self._bb

def check_fast(self, ref, x, y, rot, moved=None, cl=0.2, extra_vias=(), extra_segs=(), shrink=0.25, margin=1.0):
    moved = moved or {}
    pc, bb = _cache(self)
    f = self.fps[ref]; pads, crt = f.placed(x, y, rot); box = _bbox_of(pads, crt)
    gx0, gy0, gx1, gy1 = box[0] - margin, box[1] - margin, box[2] + margin, box[3] + margin
    out = []
    def rect(p): return (p["x"]-p["aw"]/2, p["y"]-p["ah"]/2, p["x"]+p["aw"]/2, p["y"]+p["ah"]/2)
    for r, o in self.fps.items():
        if r == ref: continue
        if r in moved:
            opads, ocrt = o.placed(*moved[r]); obb = _bbox_of(opads, ocrt)
        else:
            (opads, ocrt), obb = pc[r], bb[r]
        if obb[2] < gx0 or obb[0] > gx1 or obb[3] < gy0 or obb[1] > gy1: continue
        if crt and ocrt and o.layer == f.layer:
            a = (crt[0]+shrink, crt[1]+shrink, crt[2]-shrink, crt[3]-shrink); b = (ocrt[0]+shrink, ocrt[1]+shrink, ocrt[2]-shrink, ocrt[3]-shrink)
            if min(a[2], b[2]) - max(a[0], b[0]) > 1e-6 and min(a[3], b[3]) - max(a[1], b[1]) > 1e-6: out.append(("body", r))
        for p in pads:
            pl = layers_of(p, f.layer)
            for q in opads:
                ql = layers_of(q, o.layer)
                if pl != "ALL" and ql != "ALL" and not (pl & ql): continue
                if p["net"] and p["net"] == q["net"]: continue
                if d_rect_rect(rect(p), rect(q)) < cl - 1e-6: out.append(("pad", f"{ref}.{p['name']}", f"{r}.{q['name']}"))
    for p in pads:
        pl = layers_of(p, f.layer); rc = rect(p)
        for v in list(self.vias) + list(extra_vias):
            if not (gx0 <= v["x"] <= gx1 and gy0 <= v["y"] <= gy1): continue
            if p["net"] and p["net"] == v["net"]: continue
            if d_pt_rect(v["x"], v["y"], rc) - _via_r(v) < cl - 1e-6: out.append(("via", f"{ref}.{p['name']}", v["net"]))
        for sg in list(self.segs) + list(extra_segs):
            if max(sg["x1"], sg["x2"]) < gx0 or min(sg["x1"], sg["x2"]) > gx1 or max(sg["y1"], sg["y2"]) < gy0 or min(sg["y1"], sg["y2"]) > gy1: continue
            if pl != "ALL" and sg["layer"] not in pl: continue
            if p["net"] and p["net"] == sg["net"]: continue
            if d_seg_rect(sg["x1"], sg["y1"], sg["x2"], sg["y2"], rc) - sg["w"]/2 < cl - 1e-6: out.append(("track", f"{ref}.{p['name']}", sg["net"]))
        for e in self.edge:
            if d_seg_rect(*e, rc) < 0.25: out.append(("edge", f"{ref}.{p['name']}"))
    return out
Board.check_fast = check_fast
