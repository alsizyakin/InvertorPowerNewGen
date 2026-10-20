"""rev0.1-shift3, step 15: the bottom edge comes 3 mm up, so the board is as long as rev0.1-gnd while the bulk caps keep the
3 mm strip of the +3 mm stretch. Usage: lay_S3c.py board tools_dir
The block, the MCU zone, J6/J7 and H3/H4 with the outline arcs around them stay (owner 2026-10-20: the holes go down with
the block and the MCU zone); only the tab under U5 gets 3 mm shorter (bottom edge y 144.5 -> 141.5). What lay below
y ~141.2 is re-placed:
- U7 (SPI EEPROM, SOIC-8) goes to B.Cu under the bottom pins of U5, turned so that its pins come in the order of the
  U5 pins 50-53 (CS, SCK, MISO, MOSI): the four lines step down on F.Cu (CS turns left first, MOSI goes straight
  down), a via each between the U7 pad rows, B.Cu into the pads; C54 (its 100n) sits at the VCC pin, the supply pins
  get their vias by route.py;
- the two R / R / C triples of the U6 inputs (R79 / R80 / C91, R54 / R55 / C62) go 2.05 mm up with their tracks and
  vias; the /SWCLK_IN via that came under C91 moves, the GND vias of C91 / C62 go beside their pads;
- vias closer than 0.25 mm to the new edge move up; the GND stitching row along the bottom edge (y 143.5) goes to the
  new edge where legal;
- zone outlines (In1 / In3 / In4 GND, In2 +3.3V) follow the edge; User.1 (case / heatsink drawing) is not touched;
- reference texts that were below the bottom row of parts (now off the board) go above the parts."""
import sys, os, re, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.dont_write_bytecode = True
import pcbedit, geom, route
fn = sys.argv[1]
DY = 3.0
EE = {"/EEPROM_~{CS_MCU}": "50", "/EEPROM_SCK_MCU": "51", "/EEPROM_MISO_MCU": "52", "/EEPROM_MOSI_MCU": "53"}
U7_AT = (138.0, 137.4, 270)          # on B.Cu: pads 1 CS / 2 MISO / 3 WP / 4 GND at y 134.925, 8 VCC / 7 HOLD / 6 SCK / 5 MOSI at
                                     # y 139.875, x 136.095 / 137.365 / 138.635 / 139.905; 0.65 mm off the edge
# F.Cu from the U5 pins (y 134.95) to the vias, B.Cu from the vias into the U7 pads (0.25 mm, 0 / 45 / 90 degrees)
EE_ROUTE = {
    "/EEPROM_~{CS_MCU}": ([(139.0, 134.85), (139.0, 135.65), (138.2, 136.45), (136.6, 136.45)], (136.6, 136.45),
                          [(136.6, 136.45), (136.095, 135.945), (136.095, 135.5)]),
    "/EEPROM_SCK_MCU":   ([(139.5, 134.85), (139.5, 136.7), (139.0, 137.2), (138.4, 137.2)], (138.4, 137.2),
                          [(138.4, 137.2), (138.4, 139.3)]),
    "/EEPROM_MISO_MCU":  ([(140.0, 134.85), (140.0, 137.6), (139.6, 138.0)], (139.6, 138.0),
                          [(139.6, 138.0), (139.6, 137.25), (138.8, 136.45), (137.75, 136.45), (137.365, 136.065), (137.365, 135.5)]),
    "/EEPROM_MOSI_MCU":  ([(140.5, 134.85), (140.5, 138.6)], (140.5, 138.6),
                          [(140.5, 138.6), (140.0, 139.1)]),
}

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
def up(txt, ycut):
    return PT.sub(lambda m: f"({m.group(1)} {m.group(2)} {fmt(float(m.group(3)) - DY) if float(m.group(3)) > ycut else m.group(3)}", txt)

# ---------------------------------------------------------------- the edge and the plane outlines
s = open(fn, encoding="utf-8").read()
if "(end 122.7085 141.5)" in s: sys.exit("lay_S3c: already applied")
out = []; last = 0
for kind, a, b in blocks(s):
    t = s[a:b]; new = t
    if kind.startswith("gr_") and '(layer "Edge.Cuts")' in t: new = up(t, 141.0)
    elif kind == "zone": new = re.sub(r'\n\t\t\(filled_polygon\n.*?\n\t\t\)(?=\n)', "", up(t, 141.0), flags=re.S) if re.search(r'\(xy [\d.\-]+ 14[2-5]\.', t) else t
    out.append(s[last:a]); out.append(new); last = b
out.append(s[last:]); open(fn, "w", encoding="utf-8").write("".join(out))

# ---------------------------------------------------------------- U7 to B.Cu, signals routed
B = pcbedit.Board(fn)
B.del_segs(lambda g: g["net"] in EE); B.del_vias(lambda v: v["net"] in EE)
B.del_segs(lambda g: g["net"] in ("+3.3V", "GND") and g["layer"] == "F.Cu" and 131.5 < min(g["x1"], g["x2"]) and max(g["x1"], g["x2"]) < 138.5 and min(g["y1"], g["y2"]) > 139.0)
B.del_vias(lambda v: v["net"] == "GND" and abs(v["x"] - 133.75) < 0.01 and abs(v["y"] - 142.75) < 0.01)
# the old supply via of U7 / C54 (+3.3V, (135.75, 139.5)) and its B.Cu stub to the old C54 pad 1
B.del_segs(lambda g: g["net"] == "+3.3V" and g["layer"] == "B.Cu" and abs(g["x2"] - 135.75) < 1e-3 and abs(g["y2"] - 139.5) < 1e-3)
assert B.del_vias(lambda v: v["net"] == "+3.3V" and abs(v["x"] - 135.75) < 1e-3 and abs(v["y"] - 139.5) < 1e-3) == 1
B.flip_fp("U7"); B.move_fp("U7", *U7_AT)
B.save()
G = geom.Board(fn); c7 = G.fps["U7"].placed()[1]
B = pcbedit.Board(fn)        # GND stitching vias of the old B.Cu under the new U7 body go (the planes are solid there)
nv = B.del_vias(lambda v: v["net"] == "GND" and c7[0] - 0.3 < v["x"] < c7[2] + 0.3 and c7[1] - 0.3 < v["y"] < c7[3] + 0.3)
B.save(); print("GND vias under U7 removed:", nv)
G = geom.Board(fn)
u7 = {p.get("net"): p for p in G.fps["U7"].placed()[0]}
B = pcbedit.Board(fn)
for net, (f_pts, via, b_pts) in EE_ROUTE.items():
    q = u7[net]; assert abs(q["x"] - b_pts[-1][0]) < q["aw"]/2 and abs(q["y"] - b_pts[-1][1]) < q["ah"]/2, net   # ends in its pad
    B.track(f_pts, 0.25, "F.Cu", net); B.add_via(via, net); B.track(b_pts, 0.25, "B.Cu", net)
B.save(); print("EEPROM lines: vias", [r[1] for r in EE_ROUTE.values()])

# ---------------------------------------------------------------- U7 supply: C54 at the VCC pin, vias into the planes
B = pcbedit.Board(fn)        # old C54 GND stub to the via (133.75, 142.75) lies under the new edge
B.del_segs(lambda g: g["net"] == "GND" and g["layer"] == "B.Cu" and min(g["y1"], g["y2"]) > 142.0 and 133.5 < g["x1"] < 135.0)
B.move_fp("C54", 133.6, 139.9, 180); B.save()   # B.Cu, horizontal, left of U7: pad 1 (+3.3V) towards the VCC pin 8
G = geom.Board(fn)
R = route.Router(fn, (130.0, 131.0, 144.0, 141.5))
B = pcbedit.Board(fn)
PLANE = {"+3.3V": "In2.Cu", "GND": "In3.Cu"}
def pad(ref, pn): return [q for q in G.fps[ref].placed()[0] if q["name"] == pn][0]
for ref, pn, goal in (("U7", "7", ("U7", "8")), ("C54", "1", ("U7", "8")), ("C54", "1", None), ("C54", "2", None),
                      ("U7", "3", None), ("U7", "4", None)):
    p = pad(ref, pn); net = p["net"]; lay = PLANE[net]
    if goal is None:
        r = R.route(net, (ref, pn), ("pt", lay, round(p["x"], 2), round(p["y"], 2)), w=0.4, layers=("B.Cu", lay), via_cost=2.0,
                    under_ok=("U5",))
    else:
        r = R.route(net, (ref, pn), goal, w=0.4, layers=("B.Cu",))
    assert r, (ref, pn)
    tr, vs = r
    for l, pts in tr:
        if l == "B.Cu": B.track(pts, 0.4, l, net)
    for v in vs: B.add_via(v, net)
    print(f"{ref}.{pn} {net}: {'via ' + str(vs) if vs else 'to ' + str(goal)}")
B.save()

# ---------------------------------------------------------------- the U6 input triples 2.05 mm up
CL = ["R79", "R80", "C91", "R54", "R55", "C62"]; RECT = (123.3, 138.4, 131.2, 143.6); DYC = -2.05
inside = lambda x, y: RECT[0] <= x <= RECT[2] and RECT[1] <= y <= RECT[3]
B = pcbedit.Board(fn); cut = []
for g in list(B.segments()):
    a_in, b_in = inside(g["x1"], g["y1"]), inside(g["x2"], g["y2"])
    if a_in and b_in:
        B.del_segs(lambda h, u=g["uuid"]: h["uuid"] == u)
        B.add_seg((g["x1"], g["y1"] + DYC), (g["x2"], g["y2"] + DYC), g["w"], g["layer"], g["net"])
    elif a_in or b_in:
        B.del_segs(lambda h, u=g["uuid"]: h["uuid"] == u)
        out_pt = (g["x2"], g["y2"]) if a_in else (g["x1"], g["y1"]); cut.append((g["net"], g["layer"], out_pt, g["w"]))
moved_v = [v for v in B.vias() if inside(v["x"], v["y"])]
B.del_vias(lambda v: inside(v["x"], v["y"]))
for v in moved_v: B.add_via((v["x"], v["y"] + DYC), v["net"], v["size"], v["drill"])
B.save()
B = pcbedit.Board(fn)
for r in CL:
    f = geom.Board(fn).fps[r]; B.move_fp(r, f.x, round(f.y + DYC, 4), f.rot); B.save(); B = pcbedit.Board(fn)
print("U6 input triples up 2.05 mm; tracks cut at the region border:", [(n, p) for n, l, p, w in cut])
# loose ends after the move (all B.Cu unless noted):
# - U6B+: the trunk x 125.5 came down to y 138 between the C91 pads; it now turns at y 136.44 into C91.1 from above,
#   0.2 mm past the /SWDIO_IN via like before; the moved stub over C91.1 goes;
# - U6A-: the trunk x 128.14 stops at C62.1 (y 137.7);
# - the GND vias of C91.2 and C62.2 came up onto the SWCLK In2 end and the R49.1 F.Cu track: now beside the pads,
#   (123.5, 137.7) and (131.0, 137.7);
# - /SWCLK_IN: its via (126.25, 137.75) sits under C91.1 now; the In2 diagonal becomes F.Cu, via at (124.5, 136.45),
#   In2 turns left at y 135.95.
def near(p, q, t=2e-3): return abs(p[0] - q[0]) < t and abs(p[1] - q[1]) < t
def seg_at(net, layer, p, q): return lambda g: g["net"] == net and g["layer"] == layer and (
    (near((g["x1"], g["y1"]), p) and near((g["x2"], g["y2"]), q)) or (near((g["x1"], g["y1"]), q) and near((g["x2"], g["y2"]), p)))
B = pcbedit.Board(fn)
assert B.del_segs(lambda g: g["net"] == "Net-(U6B-+)" and g["layer"] == "B.Cu" and abs(g["x1"] - 125.5) < 1e-3 and abs(g["x2"] - 125.5) < 1e-3) == 1
assert B.del_segs(seg_at("Net-(U6B-+)", "B.Cu", (126.3625, 136.8125), (126.3625, 137.7))) == 1
B.track([(125.5, 133.75), (125.5, 136.4375), (126.3625, 137.3)], 0.5, "B.Cu", "Net-(U6B-+)")
B.track([(128.1375, 135.1375), (128.1375, 137.7)], 0.5, "B.Cu", "Net-(U6A--)")
for vx, px in ((124.5, 124.6375), (130.0, 129.8625)):
    assert B.del_segs(seg_at("GND", "B.Cu", (px, 136.8375), (vx, 136.7))) == 1
    assert B.del_segs(seg_at("GND", "B.Cu", (px, 137.7), (px, 136.8375))) == 1
    assert B.del_vias(lambda v: v["net"] == "GND" and near((v["x"], v["y"]), (vx, 136.7))) == 1
B.track([(124.6375, 137.7), (123.5, 137.7)], 0.5, "B.Cu", "GND"); B.add_via((123.5, 137.7), "GND")
B.track([(129.8625, 137.7), (131.0, 137.7)], 0.5, "B.Cu", "GND"); B.add_via((131.0, 137.7), "GND")
assert B.del_segs(seg_at("/SWCLK_IN", "In2.Cu", (126.25, 137.75), (125.0, 136.5))) == 1
assert B.del_segs(seg_at("/SWCLK_IN", "In2.Cu", (125.0, 136.5), (125.0, 129.5))) == 1
assert B.del_vias(lambda v: v["net"] == "/SWCLK_IN" and near((v["x"], v["y"]), (126.25, 137.75))) == 1
B.track([(127.0875, 137.75), (125.8, 137.75), (124.5, 136.45)], 0.5, "F.Cu", "/SWCLK_IN")
assert B.del_segs(seg_at("/SWCLK_IN", "F.Cu", (127.0875, 137.75), (126.25, 137.75))) == 1
B.add_via((124.5, 136.45), "/SWCLK_IN")
B.track([(125.0, 129.5), (125.0, 135.95), (124.5, 136.45)], 0.5, "In2.Cu", "/SWCLK_IN")
B.save(); print("U6 inputs, SWCLK_IN and the two GND vias re-laid")

# ---------------------------------------------------------------- vias at the new edge
B = pcbedit.Board(fn)
EDGE_Y = 141.5
for x in (141.75, 143.75, 145.75):          # GND at R45.1, D9-K and D8-K (F.Cu pad - B.Cu pad): 0.25 mm off the edge
    v = [v for v in B.vias() if abs(v["x"] - x) < 1e-3 and abs(v["y"] - 141.0) < 1e-3]; assert len(v) == 1, x
    B.del_vias(lambda w, x=x: abs(w["x"] - x) < 1e-3 and abs(w["y"] - 141.0) < 1e-3); B.add_via((x, 140.9), v[0]["net"])
    for g in [g for g in B.segments(v[0]["net"]) if abs(g["x1"] - x) < 1e-3 and abs(g["x2"] - x) < 1e-3 and 141.0 in (g["y1"], g["y2"])]:
        B.del_segs(lambda h, u=g["uuid"]: h["uuid"] == u)
        B.add_seg((x, g["y1"] if g["y1"] != 141.0 else 140.9), (x, g["y2"] if g["y2"] != 141.0 else 140.9), g["w"], g["layer"], g["net"])
n = B.del_vias(lambda v: v["y"] > EDGE_Y - 0.3 - v["size"]/2 + 1e-6)
B.save(); print("vias under the new edge removed:", n)
import cflow
G = geom.Board(fn); placed = []
for x in [123.5 + 1.5*k for k in range(27)]:
    if x > 162.3: break
    if cflow.legal_via(G, "GND", x, 140.9, others=placed) and all(math.hypot(v["x"] - x, v["y"] - 140.9) >= 1.2 for v in G.vias):
        placed.append(dict(x=x, y=140.9, net="GND", size=0.6, d=0.3))
B = pcbedit.Board(fn)
for q in placed: B.add_via((q["x"], q["y"]), "GND", free=True)
B.save(); print("GND stitching along the new edge:", [q["x"] for q in placed])

# ---------------------------------------------------------------- reference texts that fell off the board
# the bottom row (D8 / D9, R44-R47, C40 / C41 / C43, Y1) had its reference 3 mm below the part: now mirrored above it
s = open(fn, encoding="utf-8").read(); moved = []
G = geom.Board(fn)
for r, f in G.fps.items():
    a, b = pcbedit._fp_span(s, r); blk = s[a:b]
    m = re.search(r'(\(property "Reference" "[^"]+"\n\t\t\t\(at )([\d.\-]+) ([\d.\-]+)( [\d.\-]+)?\)', blk)
    if not m: continue
    lx, ly = float(m.group(2)), float(m.group(3)); t = math.radians(f.rot)
    gy = f.y - lx*math.sin(t) + ly*math.cos(t)
    if gy < EDGE_Y - 0.6: continue
    blk = blk[:m.start()] + f"{m.group(1)}{fmt(-lx)} {fmt(-ly)}{m.group(4) or ''})" + blk[m.end():]
    s = s[:a] + blk + s[b:]; moved.append(r)
open(fn, "w", encoding="utf-8").write(s); print("references moved above their parts:", moved)
