"""Owner's remarks of 2026-10-19 on rev0.1-plus4. Usage: lay_P4c.py board.kicad_pcb  (run octo.py first)
F15 (03 E3): VDC to J6 (supply of the connection board). It started at the foot of the HS drain column C (129.0, 91.0),
     inside the commutation loop, and ran on In2 through passage C, splitting the In2 node copper there in two
     (F.Cu, In2, B.Cu are the only node layers in the passage). New track, 0.4 mm:
     - In2 from the VDC plane of the top band (121.0, 73.4), near the bulk caps, straight down the joint of the GND strip
       C and the node column C (x 121.0) to the corner of the strip above the slot;
     - via (120.0, 92.3) in the corner, where F.Cu and B.Cu have no copper;
     - In1 (GND in the passage) through passage C beside the node via string at the slot, to J6.1.
     The near-S GND via (120.65, 77.5) of Q8 stood 0.5 mm off the drain vias of Q8: it moves 0.4 mm towards the S pins,
     into the gap between S pads (120.25, 77.5)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.dont_write_bytecode = True
import pcbedit
fn = sys.argv[1]
B = pcbedit.Board(fn)

# ---------------------------------------------------------------- F15
OLD = [((129.0, 91.0), (124.6, 91.0)), ((124.6, 91.0), (124.0, 91.6)), ((124.0, 91.6), (124.0, 94.6)),
       ((124.0, 94.6), (123.25, 95.35)), ((123.25, 95.35), (123.25, 97.192)), ((123.25, 97.192), (122.842, 97.6)),
       ((122.842, 97.6), (122.343, 97.6)), ((122.343, 97.6), (121.6, 98.343)), ((121.6, 98.343), (121.6, 102.6)),
       ((121.6, 102.6), (119.95, 104.25)), ((119.95, 104.25), (119.5, 104.25))]
drop = set(B.find_seg("VDC", "In2.Cu", a, b)["uuid"] for a, b in OLD)
assert len(drop) == len(OLD)
B.s = pcbedit.SEG_RE.sub(lambda m: "" if m.group(8) in drop else m.group(0), B.s)
V = (120.0, 92.3)
B.track([(121.0, 73.4), (121.0, 91.3), V], 0.4, "In2.Cu", "VDC")
B.add_via(V, "VDC")
B.track([V, (121.6, 92.3), (123.25, 93.95), (123.25, 97.65), (119.5, 101.4), (119.5, 104.25)], 0.4, "In1.Cu", "VDC")
assert B.del_vias(lambda v: v["net"] == "GND" and abs(v["x"] - 120.65) < 1e-3 and abs(v["y"] - 77.5) < 1e-3) == 1
B.add_via((120.25, 77.5), "GND")
print("F15: VDC to J6 rerouted (In2 from the top band, via", V, ", In1 through passage C); near-S via of Q8 moved")

# ---------------------------------------------------------------- F16
# The thermistor C lines (+3.3V, U1+) dropped from In1 to In4 by two vias in the mouth of passage C (124.9, 91.85) and
# (125.6, 92.35), holes in the F.Cu, In2 and B.Cu node copper where the node current enters the passage. They stay on
# In1 now (GND in the passage, beside the VDC track) down to their existing vias at U1; the In4 runs go.
IN4 = {"+3.3V": [((124.9, 91.85), (124.75, 92.0)), ((124.75, 92.0), (124.75, 101.25)),
                 ((124.75, 101.25), (123.5875, 102.4125)), ((123.5875, 102.4125), (123.5875, 106.5))],
       "Net-(U1-+)": [((125.6, 92.35), (125.5, 92.45)), ((125.5, 92.45), (125.5, 101.5)),
                      ((125.5, 101.5), (124.3375, 102.6625)), ((124.3375, 102.6625), (124.3375, 107.25))]}
IN1 = {"+3.3V": [((124.9, 90.0), (124.9, 91.85))],
       "Net-(U1-+)": [((125.6, 92.35), (125.6, 90.9)), ((125.6, 90.9), (126.4, 90.1))]}
drop = set()
for net, segs in IN4.items(): drop |= set(B.find_seg(net, "In4.Cu", a, b)["uuid"] for a, b in segs)
for net, segs in IN1.items(): drop |= set(B.find_seg(net, "In1.Cu", a, b)["uuid"] for a, b in segs)
assert len(drop) == 11
B.s = pcbedit.SEG_RE.sub(lambda m: "" if m.group(8) in drop else m.group(0), B.s)
assert B.del_vias(lambda v: (v["net"], round(v["x"], 3), round(v["y"], 3)) in
                  (("+3.3V", 124.9, 91.85), ("Net-(U1-+)", 125.6, 92.35))) == 2
B.track([(124.9, 90.0), (124.9, 101.1), (123.5875, 102.4125), (123.5875, 106.5)], 0.3, "In1.Cu", "+3.3V")
B.track([(126.4, 90.1), (125.5, 91.0), (125.5, 101.4), (124.3375, 102.5625), (124.3375, 107.25)], 0.3, "In1.Cu", "Net-(U1-+)")
B.save()
print("F16: thermistor C lines on In1 through passage C, 2 vias out of the passage mouth")
