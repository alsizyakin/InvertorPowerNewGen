"""Owner 2026-10-20 (after round 3). Board part of sch_rev01_h.py. Usage: lay_P4g.py board tools_dir
F25 (11 P20) fuse F1 at the start of the VDC line to J6. The line (In2 x 121 -> via (120.0, 92.3) -> In1 through
    passage C), J6.1-4 with their In4 links, C134.1 and R68.1 (fed from J6.2 on F.Cu) become VDC_J6. F1 is a 2410
    (Littelfuse Nano2 land: Bel 0679L1000 1 A, 10 kA at 86 V DC; or Littelfuse 0452001.MRL 1 A slow, 50 A at 125 V DC)
    on B.Cu in the VDC band at the left edge, between the board edge and the GND strip of phase C (y 67.4-70.6, off the
    heatsink area of Р1). Its VDC_J6 pad drops by a via under the fuse body to In2 and the line is extended up to it.
    The GND via of C94 (123.32, 69.7) is under the new pad 2: it moves to (124.3, 69.7), the F.Cu link grows by 1 mm.
    Pad 1 (VDC, solid to the band) is on the right, in the path of the band current from C6 / C35 to the phase C drain
    column; pad 2 (VDC_J6) sits in the dead corner at the board edge (fuse the other way round: VDC C +3.9 %).
    Stitching VDC vias around the fuse do not pay: they hole In1 / In3 / In4 GND in the same neck (GND C +14 %).
F26 (09 E13) places for Y capacitors between the input bushings J4 / J5, DNP: H5 - plated M3 hole with a via ring,
    net CHASSIS, midway (142.75, 35.5); C135 (VDC -> CHASSIS) and C136 (GND -> CHASSIS), 1812 on B.Cu below it, outside
    a 3.5 mm screw-head circle. C136.1 goes to the J5 ring by a short B.Cu track. CHASSIS keeps 2 mm to every other net
    on all layers by the rule in Power.kicad_dru (72 V: basic insulation, 09 E13)."""
import sys, os, re, json, math
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
import pcbedit, fplib, geom
fn, T = sys.argv[1], sys.argv[2]
U = json.load(open(os.path.join(T, "data", "sch_h_uuids.json")))
FUSE_FP, FUSE_VAL = "Fuse:Fuse_Littelfuse-NANO2-451_453", "1A 125V DC"
FUSE_PN = "Fuse SMD 2410 1A 125V DC: Bel 0679L1000 (alt. Littelfuse 0452001.MRL)"
FUSE_AT = (120.2, 69.0)                      # B.Cu, horizontal: pad 2 (VDC_J6) left in the corner, pad 1 (VDC) right
LINE_TOP = (121.0, 73.4)                     # the In2 line to J6 starts here
YCAP_FP = "Capacitor_SMD:C_1812_4532Metric"
H5_AT, C135_AT, C136_AT = (142.75, 35.5), (139.1, 40.7), (146.4, 40.7)

s = open(fn, encoding="utf-8").read()
if '(property "Reference" "F1"' in s: sys.exit("lay_P4g: already applied")

# ---------------------------------------------------------------- F25: the C94 GND via off the fuse pad, the J6 line -> VDC_J6
B = pcbedit.Board(fn)
assert B.del_vias(lambda v: v["net"] == "GND" and abs(v["x"] - 123.32) < 1e-3 and abs(v["y"] - 69.7) < 1e-3) == 1
assert B.del_segs(lambda g: g["net"] == "GND" and g["layer"] == "F.Cu" and abs(g["x2"] - 123.32) < 1e-3 and abs(g["y2"] - 69.7) < 1e-3) == 1
B.track([(122.4625, 69.7), (124.3, 69.7)], 0.4, "F.Cu", "GND"); B.add_via((124.3, 69.7), "GND")
B.save(); s = open(fn, encoding="utf-8").read()
B = pcbedit.Board(fn); G = geom.Board(fn)
seeds = [p for p in G.fps["J6"].placed()[0] if p["name"] in ("1", "2", "3", "4")]
seeds += [p for p in G.fps["C134"].placed()[0] if p["name"] == "1"] + [p for p in G.fps["R68"].placed()[0] if p["name"] == "1"]
segs = list(B.segments("VDC")); vias = list(B.vias("VDC"))
def onpad(x, y): return any(abs(x - p["x"]) <= p["aw"]/2 + 1e-3 and abs(y - p["y"]) <= p["ah"]/2 + 1e-3 for p in seeds)
nodes = [(p["x"], p["y"]) for p in seeds]; sel_s, sel_v = set(), set(); grow = True
while grow:
    grow = False
    for i, g in enumerate(segs):
        ends = ((g["x1"], g["y1"]), (g["x2"], g["y2"]))
        if i not in sel_s and any(onpad(*e) or any(math.hypot(e[0] - n[0], e[1] - n[1]) < 0.01 for n in nodes) for e in ends):
            sel_s.add(i); nodes += ends; grow = True
    for k, v in enumerate(vias):
        if k not in sel_v and any(math.hypot(v["x"] - n[0], v["y"] - n[1]) < 0.01 for n in nodes):
            sel_v.add(k); nodes.append((v["x"], v["y"])); grow = True
assert len(sel_s) == 14 and len(sel_v) == 1, (len(sel_s), len(sel_v))     # the line, the J6 links, R68 and C134 stubs
spans = [(segs[i]["span"], "seg") for i in sel_s] + [(vias[k]["span"], "via") for k in sel_v]
for (a, b), _ in sorted(spans, reverse=True):
    s = s[:a] + s[a:b].replace('(net "VDC")', '(net "/VDC_J6")', 1) + s[b:]
for ref, pads in (("J6", ("1", "2", "3", "4")), ("C134", ("1",)), ("R68", ("1",))):
    a, b = pcbedit._fp_span(s, ref); blk = s[a:b]
    for pn in pads:
        blk, n = re.subn(r'(\(pad "' + pn + r'" (?:(?!\n\t\t\)).)*?\(net )"VDC"', r'\g<1>"/VDC_J6"', blk, count=1, flags=re.S)
        assert n == 1, (ref, pn)
    s = s[:a] + blk + s[b:]

# ---------------------------------------------------------------- new footprints (cloned from F.Cu parts, rotation 0)
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

s = new_fp(s, "R68", "F1", FUSE_FP, FUSE_VAL, FUSE_PN, {"1": "VDC", "2": "/VDC_J6"}, dnp=False)
s = new_fp(s, "C112", "C135", YCAP_FP, "4.7n Y2", "Capacitor SMD 1812 Y2 (or X7R 2kV)", {"1": "VDC", "2": "/CHASSIS"}, dnp=True)
s = new_fp(s, "C112", "C136", YCAP_FP, "4.7n Y2", "Capacitor SMD 1812 Y2 (or X7R 2kV)", {"1": "GND", "2": "/CHASSIS"}, dnp=True)
s = new_fp(s, "H1", "H5", "MountingHole:MountingHole_3.2mm_M3_Pad_Via", "MountingHole_Pad", None, {"1": "/CHASSIS"})
a, b = pcbedit._fp_span(s, "F1")                                    # pad 1 carries the band current: solid
s = s[:a] + re.sub(r'(\(pad "1" (?:(?!\n\t\t\)).)*?)(\n\t\t\t\(uuid)', r'\g<1>\n\t\t\t(zone_connect 2)\g<2>', s[a:b], count=1, flags=re.S) + s[b:]
s = fplib.set_pad_clearance(s, "C136", {"1": 0.5, "2": 2.0})       # GND pad in the VDC band, exposed (P5)
s = fplib.set_pad_clearance(s, "C135", {"2": 2.0})
a, b = pcbedit._fp_span(s, "H5")                                    # H1 (the clone source) has a footprint clearance 1:
s = s[:a] + re.sub(r"\n\t\t\(clearance [\d.]+\)", "", s[a:b], count=1) + s[b:]   # local values win over the rule
s = fplib.set_pad_clearance(s, "H5", 2.0)
open(fn, "w", encoding="utf-8").write(s)

B = pcbedit.Board(fn)
for ref in ("F1", "C135", "C136"): B.flip_fp(ref)
B.move_fp("F1", *FUSE_AT, 180)
B.move_fp("C135", *C135_AT, 0)
B.move_fp("C136", *C136_AT, 180)                                    # pad 2 (CHASSIS) towards H5
B.move_fp("H5", *H5_AT, 0)
B.save()

G = geom.Board(fn)
P = {r: {p["name"]: p for p in G.fps[r].placed()[0]} for r in ("F1", "C135", "C136")}
assert P["F1"]["2"]["x"] < P["F1"]["1"]["x"] and P["C135"]["1"]["x"] < P["C135"]["2"]["x"] and P["C136"]["2"]["x"] < P["C136"]["1"]["x"]
B = pcbedit.Board(fn)
f2 = P["F1"]["2"]; V = (119.9, 68.3)                                # under the fuse body, clear of C94.1 on F.Cu
B.track([(f2["x"], V[1]), V], 0.4, "B.Cu", "/VDC_J6"); B.add_via(V, "/VDC_J6")
B.track([V, (LINE_TOP[0], V[1] + LINE_TOP[0] - V[0]), LINE_TOP], 0.4, "In2.Cu", "/VDC_J6")
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
print(f"F25: F1 on B.Cu at {FUSE_AT}, line to J6 -> VDC_J6, via {V}; F26: H5 at {H5_AT}, C135 / C136 1812 DNP")
