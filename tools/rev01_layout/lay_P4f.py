"""Reviews 11 / 13 (round 3), owner 2026-10-20. Board part of sch_rev01_g.py. Usage: lay_P4f.py board tools_dir
F22 (13 E19) C134 100n 100V X7R 0805 on B.Cu at J6: (118.75, 101.6), horizontal, pad 1 (VDC) towards J6.1 with a B.Cu
    track into the pin, pad 2 (GND) in the GND pocket of E6 with its own GND via. Courtyard from y 100.62 down - level
    with the shunt courtyards (y 100.57), outside the heatsink area of the block (Р1: B.Cu y 74...100).
F23 (13 E24, E26) C37 / C39 / C64 15n; R50 DNP - the same values / attributes as in the schematic (parity without F8).
F24 (11 P16) U4 / U9 / U12 pad 4 (NC) to GND: short B.Cu link to pad 3 (REF2 = GND), 1.27 mm away."""
import sys, os, re, json, math
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
import pcbedit, fplib, geom
fn, T = sys.argv[1], sys.argv[2]
s = open(fn, encoding="utf-8").read()

# ---------------------------------------------------------------- F23
for ref in ("C37", "C39", "C64"): s = fplib.set_attr(s, ref, value="15n")
s = fplib.set_attr(s, "R50", dnp=True)

# ---------------------------------------------------------------- F24
for ref in ("U4", "U9", "U12"):
    a, b = pcbedit._fp_span(s, ref); blk = s[a:b]
    blk, n = re.subn(r'(\(pad "4" (?:(?!\n\t\t\)).)*?\(net )"[^"]*"', r'\g<1>"GND"', blk, count=1, flags=re.S)
    assert n == 1, ref
    s = s[:a] + blk + s[b:]

# ---------------------------------------------------------------- F22: C134 from the C112 footprint (same 0805)
if '(property "Reference" "C134"' not in s:
    uid = json.load(open(os.path.join(T, "data", "sch_g_uuids.json")))["C134"]
    s = fplib.clone_fp(s, "C112", "C134", uid, sheetname="/", value="100n 100V X7R", pad_nets={"1": "VDC", "2": "GND"})
    s = fplib.set_attr(s, "C134", pn="Capacitor SMD 100V X7R", dnp=False)
    a, b = pcbedit._fp_span(s, "C134"); blk = s[a:b]
    blk = re.sub(r'\(sheetfile "[^"]*"\)', '(sheetfile "Power.kicad_sch")', blk, count=1)
    for name in ("Description", "Datasheet", "Product Name", "Replacement", "Function"):
        blk = re.sub(rf'\(property "{name}" "[^"]*"', f'(property "{name}" ""', blk, count=1)
    s = s[:a] + blk + s[b:]
open(fn, "w", encoding="utf-8").write(s)

B = pcbedit.Board(fn)
if '(layer "B.Cu")' not in s[slice(*pcbedit._fp_span(s, "C134"))][:400]:
    B.flip_fp("C134")
B.move_fp("C134", 118.75, 101.6, 0)
B.save()
G = geom.Board(fn)
pads = {p["name"]: p for p in G.fps["C134"].placed()[0]}
if pads["1"]["x"] < pads["2"]["x"]:                               # pad 1 (VDC) must face J6.1 (+x)
    B = pcbedit.Board(fn); B.move_fp("C134", 118.75, 101.6, 180); B.save()
    G = geom.Board(fn); pads = {p["name"]: p for p in G.fps["C134"].placed()[0]}
p1, p2 = pads["1"], pads["2"]
assert G.fps["C134"].layer == "B.Cu" and p1["x"] > p2["x"] and abs(p1["y"] - 101.6) < 1e-3
B = pcbedit.Board(fn)
B.track([(p1["x"], 101.6), (p1["x"], 104.0)], 0.5, "B.Cu", "VDC")              # into J6.1 (119.5, 104.25), r 0.5
B.track([(p2["x"], 101.6), (116.85, 101.6)], 0.5, "B.Cu", "GND")
B.add_via((116.85, 101.6), "GND")
for ref, x in (("U4", None), ("U9", None), ("U12", None)):
    q = {p["name"]: p for p in G.fps[ref].placed()[0]}
    B.track([(q["3"]["x"], q["3"]["y"]), (q["4"]["x"], q["4"]["y"])], 0.3, "B.Cu", "GND")
B.save()
print(f"F22: C134 on B.Cu, pad 1 VDC ({p1['x']:.3f}, {p1['y']:.3f}), pad 2 GND ({p2['x']:.3f}, {p2['y']:.3f}); "
      "F23: C37/C39/C64 15n, R50 DNP; F24: U4/U9/U12 pad 4 to GND")
