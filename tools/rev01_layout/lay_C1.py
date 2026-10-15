"""Phase C, step 1: HS gate clusters on the node side, NetTie, C_gs of HS, TH1 shift. Old HO routing removed."""
import sys
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from pcbedit import Board
B = Board(sys.argv[1])
I1, I3, I4, F = "In1.Cu", "In3.Cu", "In4.Cu", "F.Cu"
HO, SW = "/Driver_3/HO", "/Driver_3/SW"
G1, G7 = "Net-(C100-Pad1)", "Net-(C101-Pad1)"
TH33, NTC = "+3.3V", "Net-(U1-+)"
near = lambda a, b, t=0.02: abs(a[0]-b[0]) < t and abs(a[1]-b[1]) < t

# --- remove old HO routing of phase C (all layers) and old TH1 vias/stubs/in-block In3 lines
B.del_segs(lambda g: g["net"] == HO)
B.del_vias(lambda v: v["net"] == HO)
B.del_vias(lambda v: v["net"] in (TH33, NTC) and 124.8 < v["x"] < 125.0 and 80 < v["y"] < 83)
B.del_segs(lambda g: g["net"] in (TH33, NTC) and g["layer"] in (F, I3) and max(g["y1"], g["y2"]) <= 90.5 and 122 < g["x1"] < 128.5)
# keep In3 TH lines below the block; they start at (124.75,90.0)/(125.5,90.25): shorten later in the TH step
# old gate stubs to the former R23/R1 positions
B.del_segs(lambda g: g["net"] == G1 and near((g["x1"], g["y1"]), (131.0, 81.5)) or g["net"] == G1 and near((g["x2"], g["y2"]), (131.0, 81.5)))

# --- placements
B.move_fp("TH1", 123.75, 81.75, 90)
B.move_fp("R23", 125.55, 81.5, 90)      # pad2 gate top (125.55,80.588), pad1 HO bottom (125.55,82.412)
B.move_fp("NT1", 127.09, 81.5, 0)       # pad1 SW (126.59,81.5), pad2 node on R19.1
B.move_fp("C100", 128.5, 82.55, 180)    # pad2 node (127.638), pad1 gate (129.363)
B.move_fp("C101", 128.5, 91.3, 180)

# --- F.Cu connections
B.track([(127.6, 79.6875), (125.95, 80.588)], 0.5, F, G1)          # G(Q1) -> R23.2
B.track([(129.39, 81.5), (129.39, 82.55)], 0.3, F, G1)             # R19.2 -> C100.1
B.track([(125.55, 82.412), (125.55, 83.25)], 0.4, F, HO)           # R23.1 -> HO via
B.add_via((125.55, 83.25), HO)
B.track([(126.59, 81.5), (126.59, 82.4)], 0.3, F, SW)              # NT1.1 -> SW via
B.add_via((126.59, 82.4), SW)
B.track([(129.39, 90.25), (129.39, 91.3)], 0.3, F, G7)             # R26.2 -> C101.1
B.track([(132.9125, 90.25), (133.75, 90.25), (133.75, 90.65)], 0.4, F, HO)   # R1.1 (old place) -> HO via
B.add_via((133.75, 90.65), HO)
# TH1 pads -> new vias
B.track([(123.75, 80.838), (124.55, 80.838)], 0.4, F, NTC); B.add_via((124.55, 80.84), NTC)
B.track([(123.75, 82.662), (124.55, 82.662)], 0.4, F, TH33); B.add_via((124.55, 82.66), TH33)

# --- In4: HO/SW pair down the node column lane, turning east under the VDC column bottom (continued in step 2)
B.track([(125.55, 83.25), (126.05, 83.75), (126.05, 90.65), (133.75, 90.65)], 0.3, I4, HO)
B.track([(126.59, 82.4), (126.85, 82.66), (126.85, 89.85), (134.5, 89.85)], 0.3, I4, SW)

# --- TH1 lines: In1 inside the block, In3 below it (old In3 lines trimmed to start at the transitions)
B.track([(124.55, 80.84), (127.75, 80.84), (127.75, 90.1), (125.6, 90.1), (125.6, 92.35)], 0.3, I1, NTC)
B.track([(124.55, 82.66), (124.55, 83.95), (127.15, 83.95), (127.15, 89.5), (124.9, 89.5), (124.9, 91.85)], 0.3, I1, TH33)
B.add_via((124.9, 91.85), TH33); B.add_via((125.6, 92.35), NTC)
B.del_segs(lambda g: g["net"] == TH33 and g["layer"] == I3 and near((g["x1"], g["y1"]), (124.75, 101.25)) and near((g["x2"], g["y2"]), (124.75, 90.0)))
B.del_segs(lambda g: g["net"] == NTC and g["layer"] == I3 and near((g["x1"], g["y1"]), (125.5, 101.5)) and near((g["x2"], g["y2"]), (125.5, 90.25)))
B.track([(124.9, 91.85), (124.75, 92.0), (124.75, 101.25)], 0.5, I3, TH33)
B.track([(125.6, 92.35), (125.5, 92.45), (125.5, 101.5)], 0.5, I3, NTC)

# --- LO (phase C): In4 from the strip, along the right edge of passage C, to In3 at y~96.2
LO = "/Driver_3/LO"
for a, b in [((122.75, 81.5), (122.75, 82)), ((122.75, 82), (120.5, 84.25)), ((120.5, 84.25), (120.5, 89.25)),
             ((120.5, 89.25), (122, 90.75)), ((122, 91), (122, 90.75)), ((122.75, 90.25), (122, 91))]:
    B.set_layer(LO, I3, a, b, I4)
B.del_segs(lambda g: g["net"] == LO and g["layer"] == I3 and (near((g["x1"], g["y1"]), (122, 92.25)) or near((g["x2"], g["y2"]), (122, 92.25))))
B.del_segs(lambda g: g["net"] == LO and g["layer"] == I3 and near((g["x1"], g["y1"]), (123.25, 97.5)) and near((g["x2"], g["y2"]), (123.25, 93.5)))
B.track([(122, 91.0), (122.05, 91.05), (124.0, 91.05), (124.0, 96.1)], 0.3, I4, LO)
B.add_via((124.0, 96.1), LO)
B.track([(124.0, 96.1), (123.25, 96.1), (123.25, 97.5)], 0.5, I3, LO)

# --- VDC -> J6.1-4 (feeds the converters on Connector_Board, tens of mA): off In4 (GND bridge), onto In2
B.del_segs(lambda g: g["net"] == "VDC" and g["layer"] == I4 and max(g["y1"], g["y2"]) <= 104.25 and min(g["y1"], g["y2"]) < 104.2
           and min(g["x1"], g["x2"]) < 130)
B.track([(129.0, 91.0), (124.0, 91.0), (124.0, 94.6), (123.25, 95.35), (123.25, 97.6), (121.6, 97.6), (121.6, 102.6),
         (119.95, 104.25), (119.5, 104.25)], 0.4, "In2.Cu", "VDC")
B.save()
print("lay_C1 applied")
