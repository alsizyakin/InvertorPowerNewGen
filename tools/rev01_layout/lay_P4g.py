"""Owner 2026-10-20 (after round 3). Board part of sch_rev01_h.py. Usage: lay_P4g.py board tools_dir
F25 (11 P20) the fuse in the VDC line to J6 was tried here (commit 1c7dd31) and dropped by the owner: it goes on the
    connection board.
F26 (09 E13) places for Y capacitors between the input bushings J4 / J5, DNP: H5 - plated M3 hole with a via ring,
    net CHASSIS, midway (142.75, 35.5), a screw into the heatsink (= chassis, < 1 cm); C135 (VDC -> CHASSIS) and C136
    (GND -> CHASSIS), 1812 on B.Cu below it, outside a 3.5 mm screw-head circle. C136.1 goes to the J5 ring by a short
    B.Cu track. CHASSIS keeps 2 mm to every other net on all layers: the rule in Power.kicad_dru and local 2.0 on the
    pads (local values win over the rule; 72 V: basic insulation, 09 E13).
F27 (11 P19) snubber R: each 0612 (R100-R105) becomes two 0805 in parallel (R100-R105 + R124-R129), stacked across
    the old pads: R_0805_2012Metric pads span the same +-1.425 mm along the chain, the two parts sit at +-0.96 mm across
    it (0.67 mm between bodies), inside the old 1.18 x 3.40 pads. The same-net pads of a pair are joined by a track."""
import sys, os, re, json, math
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
import pcbedit, fplib, geom
fn, T = sys.argv[1], sys.argv[2]
U = json.load(open(os.path.join(T, "data", "sch_h_uuids.json")))
YCAP_FP = "Capacitor_SMD:C_1812_4532Metric"
H5_AT, C135_AT, C136_AT = (142.75, 35.5), (139.1, 40.7), (146.4, 40.7)
RSN_FP, RSN_PN = "Resistor_SMD:R_0805_2012Metric", "Resistor SMD 0805 anti-surge 0.5W (ERJ-P06J1R0V)"
PAIRS = (("R100", "R124", "LS"), ("R101", "R125", "LS"), ("R102", "R126", "LS"),
         ("R103", "R127", "HS"), ("R104", "R128", "HS"), ("R105", "R129", "HS"))
OFF = 0.96                                   # 2 x 0805 courtyards (+-0.95) just apart; pads stay inside the 0612 pads (+-1.7)

s = open(fn, encoding="utf-8").read()
if '(property "Reference" "H5"' in s: sys.exit("lay_P4g: already applied")

# ---------------------------------------------------------------- F26: H5, C135, C136 (cloned from F.Cu parts, rotation 0)
def new_fp(s, src, ref, lib_id, value, pn, nets, dnp=False):
    s = fplib.clone_fp(s, src, ref, U[ref], sheetname="/", value=value)
    a, b = pcbedit._fp_span(s, ref); blk = s[a:b]
    blk = re.sub(r'\(sheetfile "[^"]*"\)', '(sheetfile "Power.kicad_sch")', blk, count=1)
    for name in ("Description", "Datasheet", "Product Name", "Replacement", "Function"):
        blk = re.sub(rf'\(property "{name}" "[^"]*"', f'(property "{name}" ""', blk, count=1)
    s = s[:a] + blk + s[b:]
    open(fn, "w", encoding="utf-8").write(s); Bx = pcbedit.Board(fn); Bx.move_fp(ref, 0, 0, 0); Bx.save(); s = open(fn, encoding="utf-8").read()
    s = fplib.swap_geometry(s, ref, lib_id)
    a, b = pcbedit._fp_span(s, ref); blk = s[a:b]
    for pn_, net in nets.items():                       # every pad with this number (the hole has 9 pads "1")
        blk = re.sub(r'(\(pad "' + pn_ + r'" (?:(?!\n\t\t\)).)*?)(\n\t\t\t\(uuid)',
                     lambda m: (re.sub(r'\n\t\t\t\(net "[^"]*"\)', "", m.group(1)) + f'\n\t\t\t(net "{net}")' + m.group(2)), blk, flags=re.S)
    s = s[:a] + blk + s[b:]
    if pn is not None or dnp is not None: s = fplib.set_attr(s, ref, pn=pn, dnp=dnp)
    return s

s = new_fp(s, "C112", "C135", YCAP_FP, "4.7n Y2", "Capacitor SMD 1812 Y2 (or X7R 2kV)", {"1": "VDC", "2": "/CHASSIS"}, dnp=True)
s = new_fp(s, "C112", "C136", YCAP_FP, "4.7n Y2", "Capacitor SMD 1812 Y2 (or X7R 2kV)", {"1": "GND", "2": "/CHASSIS"}, dnp=True)
s = new_fp(s, "H1", "H5", "MountingHole:MountingHole_3.2mm_M3_Pad_Via", "MountingHole_Pad", None, {"1": "/CHASSIS"})
s = fplib.set_pad_clearance(s, "C136", {"1": 0.5, "2": 2.0})       # GND pad in the VDC band, exposed (P5)
s = fplib.set_pad_clearance(s, "C135", {"2": 2.0})
a, b = pcbedit._fp_span(s, "H5")                                    # H1 (the clone source) has a footprint clearance 1:
s = s[:a] + re.sub(r"\n\t\t\(clearance [\d.]+\)", "", s[a:b], count=1) + s[b:]   # local values win over the rule
s = fplib.set_pad_clearance(s, "H5", 2.0)
open(fn, "w", encoding="utf-8").write(s)

B = pcbedit.Board(fn)
for ref in ("C135", "C136"): B.flip_fp(ref)
B.move_fp("C135", *C135_AT, 0)
B.move_fp("C136", *C136_AT, 180)                                    # pad 2 (CHASSIS) towards H5
B.move_fp("H5", *H5_AT, 0)
B.save()
G = geom.Board(fn)
P = {r: {p["name"]: p for p in G.fps[r].placed()[0]} for r in ("C135", "C136")}
assert P["C135"]["1"]["x"] < P["C135"]["2"]["x"] and P["C136"]["2"]["x"] < P["C136"]["1"]["x"]
B = pcbedit.Board(fn)
r = 3.2
for ref, pn in (("C135", "2"), ("C136", "2")):
    q = P[ref][pn]; y_in = H5_AT[1] + math.sqrt(r*r - (q["x"] - H5_AT[0])**2) - 0.3
    B.track([(q["x"], q["y"]), (q["x"], round(y_in, 2))], 0.8, "B.Cu", "/CHASSIS")
g1 = P["C136"]["1"]; d = 1.45
B.track([(g1["x"], g1["y"]), (g1["x"] + d, g1["y"] - d)], 0.6, "B.Cu", "GND")
B.save()
open(os.path.join(os.path.dirname(os.path.abspath(fn)), "Power.kicad_dru"), "w").write(
    '(version 1)\n'
    '(rule "CHASSIS 2 mm"\n'
    '\t(condition "A.NetName == \'/CHASSIS\'")\n'
    '\t(constraint clearance (min 2.0mm)))\n')

# ---------------------------------------------------------------- F27: snubber R 0612 -> 2 x 0805
G = geom.Board(fn); place = {}
for old, new, side in PAIRS:
    f = G.fps[old]; q = {p["name"]: p for p in f.placed()[0]}
    ux, uy = q["1"]["x"] - q["2"]["x"], q["1"]["y"] - q["2"]["y"]; n = math.hypot(ux, uy); vx, vy = -uy/n, ux/n
    place[old] = (f.x - OFF*vx, f.y - OFF*vy, f.rot); place[new] = (f.x + OFF*vx, f.y + OFF*vy, f.rot)
s = open(fn, encoding="utf-8").read()
for old, new, side in PAIRS:
    a, b = pcbedit._fp_span(s, old); sheet = re.search(r'\(path "/([^/"]+)/', s[a:b]).group(1)
    s = fplib.clone_fp(s, old, new, f"/{sheet}/{U['Rsn_' + side]}", value="1")
open(fn, "w", encoding="utf-8").write(s)
B = pcbedit.Board(fn)
for ref in place: B.move_fp(ref, 0, 0, 0)
B.save(); s = open(fn, encoding="utf-8").read()
for ref in place:
    s = fplib.swap_geometry(s, ref, RSN_FP); s = fplib.set_attr(s, ref, value="1", pn=RSN_PN, dnp=True)
open(fn, "w", encoding="utf-8").write(s)
B = pcbedit.Board(fn)
for ref, (x, y, rot) in place.items(): B.move_fp(ref, round(x, 4), round(y, 4), rot)
B.save()
G = geom.Board(fn); B = pcbedit.Board(fn)
for old, new, side in PAIRS:
    qa = {p["name"]: p for p in G.fps[old].placed()[0]}; qb = {p["name"]: p for p in G.fps[new].placed()[0]}
    for pn in ("1", "2"):
        assert qa[pn]["net"] == qb[pn]["net"], (old, new, pn)
        B.track([(round(qa[pn]["x"], 4), round(qa[pn]["y"], 4)), (round(qb[pn]["x"], 4), round(qb[pn]["y"], 4))], 0.9, "F.Cu", qa[pn]["net"])
B.save()
print(f"F26: H5 at {H5_AT}, C135 / C136 1812 DNP; F27: snubber R 2 x 0805 ({', '.join(o + '+' + n for o, n, _ in PAIRS)})")
