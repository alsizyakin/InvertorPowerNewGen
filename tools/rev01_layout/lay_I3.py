"""rev0.1-ina-ref, step I3 (owner 2026-10-21): test point pair TP1 (DAC1 + GND) for the DAC output of U5 (PA4).
Board part; the schematic part is sch_rev01_i.py. Usage: lay_I3.py board tools_dir
I4 TP1 PinHeader_1x02_P2.54mm_Vertical (1.0 mm holes) near the bottom edge right of the MCU, (159.5, 136.5) at 90 deg:
   pad 1 (DAC1, square) left, pad 2 (GND) right, along the edge; the GND pad joins the In1 / In3 / In4 planes. Upright
   at (160.25, 139.5) the DAC label ran into the notch of the outline at the corner; pad 2 keeps the 2.0 mm clearance
   of the clamp screw hole H3 (2.10 mm; at x 160.0 it was 1.68). The footprint is cloned from H5
   (root sheet, F.Cu, out of the BOM) and gets the stock geometry.
   DAC_1_MCU from U5.20: a short F.Cu stub up out of the pin row, a via, then In2 (between the In1 and In3 grounds) to
   pad 1, 26 mm. On F.Cu / B.Cu only the way round the MCU is 55 mm with 5 vias. Silkscreen DAC / GND above the pads.
   Needs geom.Board with real via sizes (there is a 1.0 mm GND via at (147.5, 121.5))."""
import sys, os, re, json
T = sys.argv[2]; sys.path.insert(0, T); sys.dont_write_bytecode = True
import pcbedit, fplib, geom
fn = sys.argv[1]
LIB = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
AT = (159.5, 136.5, 90)
DAC = "/DAC_1_MCU"
s = open(fn, encoding="utf-8").read()
if '(property "Reference" "TP1"' in s:
    sys.exit("lay_I3: already applied")
uid = json.load(open(os.path.join(T, "data", "sch_i_uuids.json")))["TP1"]
s = fplib.clone_fp(s, "H5", "TP1", uid, sheetname="/", value="DAC1")
open(fn, "w", encoding="utf-8").write(s)
B = pcbedit.Board(fn); B.move_fp("TP1", 0, 0, 0); B.save()
s = fplib.swap_geometry(open(fn, encoding="utf-8").read(), "TP1", LIB)
a, b = pcbedit._fp_span(s, "TP1"); blk = s[a:b]
# pads: H5 had nine pads "1" (net /CHASSIS); the new pad 1 is DAC, pad 2 GND
blk = blk.replace('(net "/CHASSIS")', f'(net "{DAC}")')
i = blk.find('(pad "2" '); j = blk.find("\n\t\t)", i)
assert i > 0 and '(net ' not in blk[i:j], "pad 2"
k = blk.find("\n\t\t\t(uuid", i)
blk = blk[:k] + '\n\t\t\t(net "GND")\n\t\t\t(pintype "passive")' + blk[k:]
# fields and attributes (the reference stays hidden, as on H5: the silkscreen says DAC / GND instead)
blk = blk.replace('(property "Description" ""', '(property "Description" "2-polar test point"', 1)
blk = blk.replace('(property ki_fp_filters "MountingHole*")', '(property ki_fp_filters "Pin* Test*")', 1)
blk = blk.replace("(attr exclude_from_bom)", "(attr through_hole exclude_from_bom)", 1)
s = s[:a] + blk + s[b:]
open(fn, "w", encoding="utf-8").write(s)
B = pcbedit.Board(fn); B.move_fp("TP1", *AT); B.save()

# ---------------------------------------------------------------- DAC_1_MCU: U5.20 -> TP1.1 (path found with route.py)
# F.Cu up out of the pin row and over the +3.3V via of pin 19; the via clears the 1.0 mm GND via (147.5, 121.5); on In2
# down x 146.65 past the GND via of C53 (lay_I2), 45 degrees clear of the Temp / +3.3VA vias, along y 136.5 to pad 1
F_PATH = [(144.5, 122.15), (144.5, 121.25), (145.35, 120.4), (146.1, 120.4), (146.65, 120.95)]
VIA = (146.65, 120.95)
IN2_PATH = [(146.65, 120.95), (146.65, 125.9), (157.25, 136.5), (159.5, 136.5)]
B = pcbedit.Board(fn); G = geom.Board(fn)
bad = G.check_items(vias=[geom.V(*VIA, DAC)], segs=geom.P(F_PATH, 0.3, "F.Cu", DAC) + geom.P(IN2_PATH, 0.3, "In2.Cu", DAC))
assert not bad, bad
B.track(F_PATH, 0.3, "F.Cu", DAC); B.add_via(VIA, DAC); B.track(IN2_PATH, 0.3, "In2.Cu", DAC)
B.save()

# ---------------------------------------------------------------- silkscreen
def text(t, x, y):
    return (f'\t(gr_text "{t}"\n\t\t(at {x} {y} 0)\n\t\t(layer "F.SilkS")\n\t\t(uuid "{__import__("uuid").uuid4()}")\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 0.8 0.8)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n'
            f'\t\t)\n\t)\n')
s = open(fn, encoding="utf-8").read()
k = s.find("\n\t(gr_text ") + 1
s = s[:k] + text("DAC", 159.5, 135.0) + text("GND", 162.04, 135.0) + s[k:]
open(fn, "w", encoding="utf-8").write(s)
print("TP1 at", AT, "DAC_1_MCU routed, silkscreen DAC / GND")
