"""Current spreading in the power copper (cflow.py, CHANGELOG 2026-10-19), owner: "делаем всё". Usage: lay_P4d.py board
F19 Phase A, approach to the shunt R52.2. The thermistor A lines (+3.3V, U3+) ran on In2 through the middle of passage A
    and then across the node copper in front of the shunt, with a +3.3V via (159.26, 101.25) 1.9 mm off the pad; the
    whole node current squeezed past it into one corner of the pad (2638 A/mm2 at 100 A).
    - Both lines go down passage A on In2 hard by the slot (x 162.7 / 163.3) instead of x 161.25 / 162.
    - +3.3V ends in the +3.3V plane of In2 below the node zone; U3+ turns left along the top of that plane (y 105.6) to
      its old run at x 153.85.
    - The In4 piece of +3.3V and the vias (159.26, 101.25), (156.4, 104.5) go.
    - The dead-end node via field right of the passage (x 162.5-168.5, y 98.75-102.25, 81 vias, <= 0.2 A each) goes;
      the zones stay (E6 is pending).
    - The SW via of driver A (162.25, 103.75) moves to (161.75, 103.75), under its In1 run, to clear the +3.3V line.
    - 6 new node vias beside the pad R52.2 (chosen by cflow.via_gain after the rework, legal by cflow.legal_via).
F20 Stitching vias VDC / GND / node C, 26 (see STITCH); rev0.1-shift3 (STRIP_DY=3): 26, its own list."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.dont_write_bytecode = True
import pcbedit
fn = sys.argv[1]
B = pcbedit.Board(fn)
NODE_A = "/Current_Sensor_1/Phase_IN"

def drop_segs(items):
    ids = set(B.find_seg(net, layer, a, b)["uuid"] for net, layer, a, b in items)
    assert len(ids) == len(items)
    B.s = pcbedit.SEG_RE.sub(lambda m: "" if m.group(8) in ids else m.group(0), B.s)

# ---------------------------------------------------------------- F19
drop_segs([
    ("+3.3V", "In2.Cu", (161.25, 84.75), (161.25, 99.26)), ("+3.3V", "In2.Cu", (161.25, 99.26), (159.26, 101.25)),
    ("+3.3V", "In4.Cu", (159.26, 101.25), (158.292, 101.25)), ("+3.3V", "In4.Cu", (158.292, 101.25), (157.5, 102.042)),
    ("+3.3V", "In4.Cu", (157.5, 102.042), (157.5, 103.4)), ("+3.3V", "In4.Cu", (157.5, 103.4), (156.4, 104.5)),
    ("Net-(U3-+)", "In2.Cu", (162.0, 91.6), (162.8, 92.4)), ("Net-(U3-+)", "In2.Cu", (162.8, 92.4), (162.8, 93.4)),
    ("Net-(U3-+)", "In2.Cu", (162.8, 93.4), (162.0, 94.2)), ("Net-(U3-+)", "In2.Cu", (162.0, 94.2), (162.0, 99.5)),
    ("Net-(U3-+)", "In2.Cu", (162.0, 99.5), (159.5, 102.0)), ("Net-(U3-+)", "In2.Cu", (159.5, 102.0), (154.25, 102.0)),
    ("Net-(U3-+)", "In2.Cu", (154.25, 102.0), (153.85, 102.4)), ("Net-(U3-+)", "In2.Cu", (153.85, 102.4), (153.85, 109.3)),
    ("/Driver_1/SW", "In1.Cu", (161.75, 94.45), (161.75, 103.25)), ("/Driver_1/SW", "In1.Cu", (161.75, 103.25), (162.25, 103.75)),
    ("/Driver_1/SW", "F.Cu", (162.25, 107.5), (162.25, 103.75)), ("/Driver_1/SW", "F.Cu", (161.4375, 108.3125), (162.25, 107.5)),
])
gone = lambda v: ((v["net"] == NODE_A and v["x"] >= 162.4 and v["y"] >= 98.5)
                  or (v["net"], round(v["x"], 3), round(v["y"], 3)) in (("+3.3V", 159.26, 101.25), ("+3.3V", 156.4, 104.5),
                                                                        ("/Driver_1/SW", 162.25, 103.75)))
n = B.del_vias(gone); assert n == 84, n
B.track([(161.25, 84.75), (161.25, 91.6), (162.7, 93.05), (162.7, 104.7)], 0.3, "In2.Cu", "+3.3V")
B.track([(162.0, 91.6), (163.3, 92.9), (163.3, 105.0), (162.7, 105.6), (154.45, 105.6), (153.85, 106.2), (153.85, 109.3)],
        0.3, "In2.Cu", "Net-(U3-+)")
B.add_via((161.75, 103.75), "/Driver_1/SW")
B.track([(161.75, 94.45), (161.75, 103.75)], 0.3, "In1.Cu", "/Driver_1/SW")
B.track([(161.75, 103.75), (161.75, 108.0), (161.4375, 108.3125)], 0.5, "F.Cu", "/Driver_1/SW")
VIAS_A = [(159.0, 103.5), (159.0, 102.25), (159.25, 101.25), (159.75, 103.0), (160.0, 102.0), (160.0, 100.75)]
for x, y in VIAS_A: B.add_via((x, y), NODE_A, free=True)

# ---------------------------------------------------------------- F20
# Stitching vias where the layers of a path part most (dR = g*dV^2/I^2): VDC at the entry of each HS drain column
# (top band and column top), GND at the top of each GND strip, node C beside the shunt pad R7.1. GND vias above the
# strips (y < 71.25) were dropped: there F.Cu / B.Cu are VDC, such a via only ties In1/In3/In4 (no gain for GND) and
# cuts the VDC band (VDC B 0.314 -> 0.337 mOhm with them).
STITCH = {                       # cflow_cases.py + cflow.best_vias, 5-6 per path; legal by cflow.legal_via
    "node_C_LS": ("/Current_Sensor_3/Phase_IN", [(126.5, 102.75), (125.5, 103.0)]),
    "VDC_C_HS": ("VDC", [(126.25, 70.0), (128.75, 74.5), (129.0, 67.75), (132.75, 74.5), (130.0, 74.5)]),
    "VDC_B_HS": ("VDC", [(146.25, 74.5), (144.0, 70.0), (150.25, 74.5), (146.0, 67.75), (147.25, 74.5), (150.0, 67.75)]),
    "VDC_A_HS": ("VDC", [(163.75, 70.0), (164.5, 73.0), (160.5, 67.75), (163.0, 74.5), (160.5, 70.0), (162.5, 70.0)]),
    "GND_C_LS": ("GND", [(117.75, 72.0), (117.0, 72.5), (117.75, 74.25), (117.75, 73.0), (117.0, 73.75), (117.0, 71.5)]),
    "GND_A_LS": ("GND", [(152.5, 71.75)]),
}
DY = float(os.environ.get("STRIP_DY", "4"))   # rev0.1-shift3: the band above y 72 sits 4 - DY mm lower than on the +4 mm board
if DY == 3:
    # rev0.1-shift3 (bulk caps 3 mm from the block, shoulders fixed): 11 of the plus4 spots stay legal; the rest chosen anew
    # by cflow.best_vias on the shift3 board and checked by refill + cflow_cases.py. VDC C gets none: its vias cut the GND
    # planes at the GND C strip (VDC C -1 %, GND C +9 %). Copper, 100 A, without -> with the new ones: VDC C / B / A
    # 0.365 / 0.354 / 0.578 -> 0.365 / 0.331 / 0.552 mOhm; GND C / B / A 0.321 / 0.179 / 0.195 -> 0.316 / 0.171 / 0.194.
    STITCH = {
        "node_C_LS": ("/Current_Sensor_3/Phase_IN", [(126.5, 102.75), (125.5, 103.0)]),
        "VDC_C_HS": ("VDC", [(126.25, 71.0), (129.0, 68.75)]),
        "VDC_B_HS": ("VDC", [(146.0, 68.75), (150.0, 68.75), (149.75, 74.25), (148.75, 74.25), (143.0, 70.5), (151.25, 75.0)]),
        "VDC_A_HS": ("VDC", [(160.5, 68.75), (163.0, 74.5), (160.5, 71.0), (162.5, 71.0), (164.5, 70.75), (163.5, 70.75),
                             (163.5, 69.75), (162.5, 70.0), (168.5, 73.5)]),
        "GND_C_LS": ("GND", [(117.75, 74.25), (119.0, 74.25), (119.0, 77.25)]),
        "GND_B_LS": ("GND", [(137.5, 74.5), (136.5, 74.25)]),
        "GND_A_LS": ("GND", [(152.0, 74.25), (153.0, 74.25)]),
    }
    B.save(); import geom, cflow
    G = geom.Board(fn); placed = []
    for case, (net, pts) in STITCH.items():
        for x, y in pts:
            assert cflow.legal_via(G, net, x, y, others=placed), (case, x, y)
            placed.append(dict(x=x, y=y, net=net, size=0.6, d=0.3))
    B = pcbedit.Board(fn)
for case, (net, pts) in STITCH.items():
    for x, y in pts: B.add_via((x, y), net, free=True)
B.save()
print(f"F19: thermistor A lines by the slot, 81 dead-end node vias and 2 +3.3V vias out, SW via moved, {len(VIAS_A)} node vias at R52.2")
print(f"F20: {sum(len(p) for n, p in STITCH.values())} stitching vias (VDC, GND, node C)")
