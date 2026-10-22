"""Checks of docs/Y_TASK.md 5.1 on a refilled board. Usage: y_checks.py board
- copper of any net within r of the holes H1 / H3 / H4 on every copper layer (pads, tracks, vias, filled zones);
  r = 3.5 mm (washer 7 mm; Y_TASK 4.3 asks hole + 2.0 mm = r 2.6, and nothing under the head / washer)
- items of the nets CHASSIS / CY_MID / Y_F: pads by footprint, tracks, vias, zones
- the shortest copper distance from CHASSIS / CY_MID to the phase nodes and to VDC, per layer
- the chain length GND vias -> FY1 -> CY2 -> CY1 -> ring along the pad centres"""
import sys, re, math
sys.path.insert(0, __import__("os").path.dirname(__file__)); sys.dont_write_bytecode = True
import geom
fn = sys.argv[1]; s = open(fn, encoding="utf-8").read(); G = geom.Board(fn)
HOLES = {r: (G.fps[r].x, G.fps[r].y) for r in ("H1", "H3", "H4", "H2")}
R_ISO = 3.5
PHASE = re.compile(r'^/(Driver_\d/SW|Current_Sensor_\d/Phase_(IN|OUT))$')

def polys():
    """filled zone polygons: (net, layer, [(x, y)])"""
    for a, b in geom._blocks(s, "zone"):
        z = s[a:b]; net = re.search(r'\(net "([^"]*)"\)', z); net = net.group(1) if net else ""
        for m in re.finditer(r'\(filled_polygon\n\t\t\t\(layer "([^"]+)"\)\n\t\t\t\(pts\n(.*?)\n\t\t\t\)', z, re.S):
            yield net, m.group(1), [(float(x), float(y)) for x, y in re.findall(r'\(xy ([\d.\-]+) ([\d.\-]+)\)', m.group(2))]
def d_pt_poly(px, py, pts):
    inside = False; d = 1e9
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        if (y1 > py) != (y2 > py) and px < x1 + (py - y1)*(x2 - x1)/(y2 - y1): inside = not inside
        d = min(d, geom.d_pt_seg(px, py, x1, y1, x2, y2))
    return 0.0 if inside else d
def copper_items():
    """(net, layer, kind, distance function)"""
    for r, f in G.fps.items():
        ps, _ = f.placed()
        for p in ps:
            if not p["net"]: continue
            lays = ["ALL"] if p["tht"] else [l for l in p["cu"] if l != "*.Cu"] or [f.layer]
            rect = (p["x"] - p["aw"]/2, p["y"] - p["ah"]/2, p["x"] + p["aw"]/2, p["y"] + p["ah"]/2)
            if p["shape"] == "circle":
                fd = lambda x, y, p=p: max(0, math.hypot(x - p["x"], y - p["y"]) - p["aw"]/2)
            else:
                fd = lambda x, y, rect=rect: geom.d_pt_rect(x, y, rect)
            for l in lays: yield p["net"], l, f"{r}.{p['name']}", fd
    for g in G.segs:
        yield g["net"], g["layer"], "track", (lambda x, y, g=g: max(0, geom.d_pt_seg(x, y, g["x1"], g["y1"], g["x2"], g["y2"]) - g["w"]/2))
    for v in G.vias:
        yield v["net"], "ALL", "via", (lambda x, y, v=v: max(0, math.hypot(x - v["x"], y - v["y"]) - v["size"]/2))
    for net, layer, pts in polys():
        yield net, layer, "zone", (lambda x, y, pts=pts: d_pt_poly(x, y, pts))

items = list(copper_items())
print(f"copper within r {R_ISO} of the isolated holes (any layer):")
for h in ("H1", "H3", "H4"):
    x, y = HOLES[h]
    near = sorted((round(f(x, y), 3), net, layer, kind) for net, layer, kind, f in items if f(x, y) < R_ISO)
    print(f"  {h} ({x}, {y}): " + ("none" if not near else str(near[:6])))
    if near: print("    nearest copper", near[0])
print("CHASSIS / CY_MID / Y_F items:")
for n in ("/CHASSIS", "/CY_MID", "/Y_F"):
    pads = sorted(set(k.split(".")[0] for net, l, k, f in items if net == n and "." in k))
    print(f"  {n}: footprints {pads}, tracks {sum(1 for g in G.segs if g['net'] == n)}, vias {sum(1 for v in G.vias if v['net'] == n)},"
          f" zone layers {sorted(set(l for net, l, p in polys() if net == n))}")
# distances CHASSIS / CY_MID copper -> phase nodes / VDC: sample the Y copper (pads, tracks) every 0.1 mm
ypts = []
for r in ("H2", "CY1", "CY2", "FY1", "RY1", "TP2"):
    ps, _ = G.fps[r].placed()
    for p in ps:
        if p["net"] in ("/CHASSIS", "/CY_MID", "/Y_F"):
            for i in range(11):
                for j in range(11):
                    lay = "ALL" if p["tht"] else ([l for l in p["cu"] if l != "*.Cu"] or [G.fps[r].layer])[0]
                    ypts.append((lay, p["x"] - p["aw"]/2 + p["aw"]*i/10, p["y"] - p["ah"]/2 + p["ah"]*j/10))
for net, layer, pts in polys():
    if net == "/CHASSIS": ypts += [(layer, x, y) for x, y in pts]
for label, test, same in (("phase nodes, any layer", lambda n: bool(PHASE.match(n)), False),
                          ("VDC, same layer", lambda n: n == "VDC", True)):
    best = 1e9
    for net, layer, kind, f in items:
        if not test(net): continue
        for yl, x, y in ypts:
            if same and not (yl == layer or "ALL" in (yl, layer)): continue
            best = min(best, f(x, y))
    print(f"  Y copper (pads, CHASSIS rings) -> {label}: >= {best:.2f} mm (sampled)")
# chain length along pad centres
def pc(r, n): ps, _ = G.fps[r].placed(); q = [p for p in ps if p["name"] == n]; return (sum(p["x"] for p in q)/len(q), sum(p["y"] for p in q)/len(q))
gv = [v for v in G.vias if v["net"] == "GND" and math.hypot(v["x"] - pc("FY1", "1")[0], v["y"] - pc("FY1", "1")[1]) < 3.5]
v0 = min(gv, key=lambda v: math.hypot(v["x"] - pc("FY1", "1")[0], v["y"] - pc("FY1", "1")[1]))
chain = [(v0["x"], v0["y"]), pc("FY1", "1"), pc("FY1", "2"), pc("CY2", "2"), pc("CY2", "1"), pc("CY1", "2"), pc("CY1", "1")]
ring = (HOLES["H2"][0], HOLES["H2"][1] + 3.25)
L = sum(math.dist(a, b) for a, b in zip(chain, chain[1:])) + math.dist(chain[-1], ring)
print(f"chain GND via {chain[0]} -> FY1 -> CY2 -> CY1 -> ring edge: {L:.1f} mm along the pad centres")
print(f"RY: ring -> RY1 -> RY2 -> J5 pad: {math.dist(pc('RY1', '1'), pc('RY2', '2')) + 1.4 + 2.9:.1f} mm (approx.)")
