"""Stretch a .kicad_pcb along y: everything above YCUT (y < YCUT) moves up by DY mm.
Footprints/vias/text move as a whole by their anchor; segments, graphic lines/curves and zone outlines per point
(so items crossing the cut are stretched). Filled polygons are dropped (refill afterwards).
Usage: stretch.py in.kicad_pcb out.kicad_pcb YCUT DY"""
import re, sys
fi, fo, YCUT, DY = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
s = open(fi, encoding="utf-8").read()
def fmt(v):
    t = f"{v:.6f}".rstrip("0").rstrip("."); return t if t not in ("-0", "") else "0"
def blocks(s):
    out = []; i = 0
    for m in re.finditer(r'\n\t\(([a-z_]+)', s):
        a = m.start() + 2
        if a < i: continue
        d = 0
        for k in range(a, len(s)):
            c = s[k]
            if c == "(": d += 1
            elif c == ")":
                d -= 1
                if d == 0: break
        out.append((m.group(1), a, k + 1)); i = k + 1
    return out
PT = re.compile(r'\((start|end|mid|center|xy|at) ([\d.\-]+) ([\d.\-]+)')
import os
YEDGE = float(os.environ.get("STRETCH_YEDGE", YCUT))   # own cut for Edge.Cuts: rev0.1-shift3 keeps the shoulders of the
                                                       # board at the clamp plate screws (y 68-71.5) with the block
def shift_pts(txt, ycut=None):
    ycut = YCUT if ycut is None else ycut
    def f(m):
        x, y = float(m.group(2)), float(m.group(3))
        if y < ycut: y -= DY
        return f"({m.group(1)} {m.group(2)} {fmt(y)}"
    return PT.sub(f, txt)
def is_edge(t): return '(layer "Edge.Cuts")' in t
cnt = {}; mixed = []
res = []; last = 0
for typ, a, b in blocks(s):
    t = s[a:b]; new = t
    if typ in ("footprint", "via", "gr_text"):
        m = re.search(r'\n\t\t\(at ([\d.\-]+) ([\d.\-]+)', t)
        if m and float(m.group(2)) < YCUT:
            new = t[:m.start()] + f'\n\t\t(at {m.group(1)} {fmt(float(m.group(2)) - DY)}' + t[m.end():]
            cnt[typ] = cnt.get(typ, 0) + 1
    elif typ in ("segment", "gr_line", "gr_curve", "gr_poly", "gr_rect"):
        new = shift_pts(t, YEDGE if is_edge(t) else YCUT)
        if new != t: cnt[typ] = cnt.get(typ, 0) + 1
    elif typ in ("gr_arc", "gr_circle"):
        yc = YEDGE if is_edge(t) else YCUT
        ys = [float(m.group(3)) for m in PT.finditer(t)]
        if all(y < yc for y in ys): new = shift_pts(t, yc); cnt[typ] = cnt.get(typ, 0) + 1
        elif any(y < yc for y in ys): mixed.append(t[:200])
    elif typ == "zone":
        t2 = re.sub(r'\n\t\t\(filled_polygon.*?\n\t\t\)', '', t, flags=re.S)
        new = shift_pts(t2)
        if new != t2: cnt[typ] = cnt.get(typ, 0) + 1
    res.append(s[last:a]); res.append(new); last = b
res.append(s[last:])
open(fo, "w", encoding="utf-8").write("".join(res))
print("shifted:", cnt); print("mixed arcs/circles:", len(mixed)); [print(" ", m.replace("\n", " ")) for m in mixed]
