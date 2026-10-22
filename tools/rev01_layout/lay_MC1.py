"""rev0.1-adapto, step MC1 (owner 2026-10-22: 98 mm): the bottom tab of the MCU zone 3 mm shorter, edge y 141.5 -> 138.5,
board 53 x 98 mm. Usage: lay_MC1.py board tools_dir
- outline: the tab between the H3 / H4 corners goes; the concave arcs below H4 / H3 (centre (119.5 | 166, 140.7085),
  r 3.2085 - room for the parts next to the board) stay and are cut at the new edge; the length dimension follows
- the 18 parts of the old bottom row move (data/mc1.json "place"):
  crystal Y1 + C40 / C41 right of U5 beside PH0 / PH1 (pins 5 / 6), PH1 over the crystal top, PH0 round its left side,
  a GND via between the two lines; the VBAT via of pin 1 moves out of the PH0 lane (to 148.11, 133.3);
  NRST (pin 7) by a via under the U5 body to C43 / R47 on B.Cu (C43 GND in the B.Cu GND pour, R47 +3.3V to C45);
  R45 (BOOT0), D9, D8 in one F.Cu row on the new edge, R46 / R44 under them on B.Cu through the LED cathode vias;
  EEPROM U7 on B.Cu under U10, C54 left of it: CS / MISO / MOSI to vias inside the U5 pin ring, SCK below the pins and
  under the U7 body; the U10 plane vias (under U7 now) give way to a +3.3V via in the U10 body gap and a GND track
  into the U5 F.Cu GND pour; U5 pin 63 joins that pour by a stub;
  U6 network: C62 / R55 / R54 below pin 2, C91 / R80 / R79 left of U6, a corridor for U6B+ (pin 3) kept free
- copper: the tracks / vias of the moved nets, of the cut strip and of the old via spots are replaced (data/mc1.json:
  deleted by uuid, added by geometry, the reference texts of the moved parts). The added copper was made and checked in
  tmp/2026-10-22_mc (hand routes, route.py for the U6 nets, power-via search) with DRC 0 / 0 / 0."""
import sys, os, re, json, math, uuid
T = sys.argv[2]; sys.path.insert(0, T); sys.dont_write_bytecode = True
import pcbedit, geom
fn = sys.argv[1]
YE = 138.5
D = json.load(open(os.path.join(T, "data", "mc1.json"), encoding="utf-8"))
s = open(fn, encoding="utf-8").read()
if f"(end 166 137.5)" in s and "(start 121.827" in s:
    sys.exit("lay_MC1: already applied")

# ---------------------------------------------------------------- parts: C43 / R47 to B.Cu, all 18 to their spots
B = pcbedit.Board(fn)
G = geom.Board(fn)
for r, (x, y, rot, layer) in D["place"].items():
    if layer == "B.Cu" and G.fps[r].layer == "F.Cu": B.flip_fp(r)
    B.move_fp(r, x, y, rot)
B.save()
s = open(fn, encoding="utf-8").read()
for r, txt in D["refs"].items():
    a, b = pcbedit._fp_span(s, r); blk = s[a:b]
    m = re.search(r'\t\t\(property "Reference" "[^"]+"\n.*?\n\t\t\)\n', blk, re.S)
    blk = blk[:m.start()] + txt + blk[m.end():]
    s = s[:a] + blk + s[b:]
open(fn, "w", encoding="utf-8").write(s)

# ---------------------------------------------------------------- copper
B = pcbedit.Board(fn)
ds, dv = set(D["del_segs"]), set(D["del_vias"])
n1 = B.del_segs(lambda g: g["uuid"] in ds)
n2 = B.del_vias(lambda v: re.search(r'\(uuid "([^"]+)"\)', B.s[v["span"][0]:v["span"][1]]).group(1) in dv)
assert (n1, n2) == (len(ds), len(dv)), (n1, n2)
for x1, y1, x2, y2, w, layer, net in D["add_segs"]: B.add_seg((x1, y1), (x2, y2), w, layer, net)
for x, y, size, drill, net, free in D["add_vias"]: B.add_via((x, y), net, size, drill, free=free)
B.save()

# ---------------------------------------------------------------- outline and length dimension
s = open(fn, encoding="utf-8").read()
out = []
for kind in ("gr_line", "gr_arc"):
    for a, b in geom._blocks(s, kind):
        g = s[a:b]
        if '"Edge.Cuts"' not in g: continue
        ys = [float(v) for v in re.findall(r'\((?:start|mid|end) [\d.\-]+ ([\d.\-]+)\)', g)]
        if max(ys) > 137.5 + 1e-3: out.append((a, b))
assert len(out) == 5, len(out)
for a, b in sorted(out, reverse=True): s = s[:a - 1] + s[b + 1:]
f = pcbedit.fmt
def gl(a, b):
    return (f'\t(gr_line\n\t\t(start {f(a[0])} {f(a[1])})\n\t\t(end {f(b[0])} {f(b[1])})\n\t\t(stroke\n\t\t\t(width 0.05)\n'
            f'\t\t\t(type default)\n\t\t)\n\t\t(layer "Edge.Cuts")\n\t\t(uuid "{uuid.uuid4()}")\n\t)\n')
def ga(a, m, b):
    return (f'\t(gr_arc\n\t\t(start {f(a[0])} {f(a[1])})\n\t\t(mid {f(m[0])} {f(m[1])})\n\t\t(end {f(b[0])} {f(b[1])})\n'
            f'\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n\t\t(layer "Edge.Cuts")\n\t\t(uuid "{uuid.uuid4()}")\n\t)\n')
RC, CY = 3.2085, 140.7085
dx = math.sqrt(RC*RC - (CY - YE)**2); tm = (math.atan2(YE - CY, dx) - math.pi/2)/2
edge = (ga((119.5, 137.5), (119.5 + RC*math.cos(tm), CY + RC*math.sin(tm)), (119.5 + dx, YE)) +
        gl((round(119.5 + dx, 6), YE), (round(166 - dx, 6), YE)) +
        ga((166 - dx, YE), (166 - RC*math.cos(tm), CY + RC*math.sin(tm)), (166, 137.5)))
k = s.find("\n\t(gr_line") + 1; s = s[:k] + edge + s[k:]
s, n = re.subn(r'\(xy 122\.7085 141\.5\) \(xy 122\.7085 40\.5\)', f'(xy 122.7085 {f(YE)}) (xy 122.7085 40.5)', s); assert n == 1
open(fn, "w", encoding="utf-8").write(s)
print(f"lay_MC1: edge y {YE}, 18 parts moved, segments -{n1} +{len(D['add_segs'])}, vias -{n2} +{len(D['add_vias'])}")
