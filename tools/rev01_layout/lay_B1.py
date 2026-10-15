"""Phase B, block: as phase C shifted +17 mm (R_gs R30/R32 moved right 0.25 so that the node column fits),
HS R_g,i R28 on the node side, NT2, C_gs C104/C105, TH2 lines on In1 in the block, LO B in the block on In4.
The HO/SW pair runs on In4 down the right edge of the node column (node via field occupies x <= 144),
then east under the VDC column bottom; HO -> In3 via below the block, SW stays on In4 (stacked under HO)."""
import sys
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from pcbedit import Board
B = Board(sys.argv[1])
I1, I3, I4, F = "In1.Cu", "In3.Cu", "In4.Cu", "F.Cu"
HO, SW, LO = "/Driver_2/HO", "/Driver_2/SW", "/Driver_2/LO"
G1, G7 = "Net-(C104-Pad1)", "Net-(C105-Pad1)"
TH33, NTC = "+3.3V", "Net-(U2-+)"
near = lambda a, b, t=0.03: abs(a[0]-b[0]) < t and abs(a[1]-b[1]) < t
on = lambda g, a, b: (near((g["x1"], g["y1"]), a) and near((g["x2"], g["y2"]), b)) or (near((g["x1"], g["y1"]), b) and near((g["x2"], g["y2"]), a))
inblk = lambda g: 141 < min(g["x1"], g["x2"]) and max(g["x1"], g["x2"]) < 149 and max(g["y1"], g["y2"]) < 93.6

# --- removals: all HO of phase B (block, passage, driver), old TH2 vias/stubs and their In3 lines above the passage
B.del_segs(lambda g: g["net"] == HO)
B.del_vias(lambda v: v["net"] == HO)
B.del_vias(lambda v: v["net"] in (TH33, NTC) and near((v["x"], v["y"]), (141.91, 80.84)) or v["net"] in (TH33, NTC) and near((v["x"], v["y"]), (141.91, 82.66)))
B.del_segs(lambda g: g["net"] in (TH33, NTC) and g["layer"] == F and 141 < g["x1"] < 142.5 and 80 < g["y1"] < 83.5)
B.del_segs(lambda g: g["net"] in (TH33, NTC) and g["layer"] == I3 and inblk(g))
B.del_segs(lambda g: g["net"] == G1 and on(g, (147.75, 81.5), (146.16, 81.5)))

# --- placements
B.move_fp("R30", 145.5, 81.5, 0)        # R_gs: pad1 node 144.59, pad2 gate 146.41
B.move_fp("R32", 145.5, 90.25, 0)
B.move_fp("TH2", 140.75, 81.75, 90)
B.move_fp("R28", 142.55, 81.5, 90)      # pad2 gate top (142.55,80.588), pad1 HO bottom (142.55,82.412)
B.move_fp("NT2", 144.09, 81.5, 0)       # pad1 SW (143.59), pad2 node on R30.1
B.move_fp("C104", 145.5, 82.55, 180)    # pad2 node, pad1 gate
B.move_fp("C105", 145.5, 91.3, 180)

# --- F.Cu
B.track([(144.6, 79.6875), (142.95, 80.588)], 0.5, F, G1)          # G(Q2) -> R28.2
B.track([(146.39, 81.5), (146.39, 82.55)], 0.3, F, G1)             # R30.2 -> C104.1
B.track([(146.39, 90.25), (146.39, 91.3)], 0.3, F, G7)             # R32.2 -> C105.1
B.track([(142.55, 82.412), (142.55, 83.25)], 0.4, F, HO); B.add_via((142.55, 83.25), HO)
B.track([(143.59, 81.5), (143.59, 82.4)], 0.3, F, SW); B.add_via((143.59, 82.4), SW)
B.track([(149.66, 90.25), (149.66, 91.3), (148.96, 92.0), (148.5, 92.0)], 0.4, F, HO)   # R2.1 (rev0 place) -> HO via
B.add_via((148.5, 92.0), HO)
B.track([(140.75, 80.838), (141.55, 80.838)], 0.4, F, NTC); B.add_via((141.55, 80.84), NTC)
B.track([(140.75, 82.662), (141.55, 82.662)], 0.4, F, TH33); B.add_via((141.55, 82.66), TH33)

# --- In4: pair down the right edge of the node column, east under the VDC column bottom
B.track([(142.55, 83.25), (144.2, 84.9), (144.2, 90.65), (148.1, 90.65), (148.5, 91.05), (148.5, 92.0)], 0.3, I4, HO)
B.track([(143.59, 82.4), (144.85, 83.66), (144.85, 89.85), (149.25, 89.85), (149.25, 92.75)], 0.3, I4, SW)
# --- In3 below the block: HO lane x 149.25 in passage J2-J3 (continued in lay_D5R)
B.track([(148.5, 92.0), (149.25, 92.75)], 0.3, I3, HO)

# --- TH2 lines: In1 in the block, vias just below it, then the old In3 lanes 147.5 / 148.25
B.track([(141.55, 80.84), (144.85, 80.84), (144.85, 90.1), (146.35, 91.6), (146.9, 91.6), (147.6, 92.3)], 0.3, I1, NTC)
B.track([(141.55, 82.66), (141.55, 83.95), (144.2, 83.95), (144.2, 90.6), (146.0, 92.4), (146.55, 92.4)], 0.3, I1, TH33)
B.add_via((147.6, 92.3), NTC); B.add_via((146.55, 92.4), TH33)
B.track([(147.6, 92.3), (148.25, 92.95), (148.25, 93.25)], 0.5, I3, NTC)
B.track([(146.55, 92.4), (147.5, 93.35), (147.5, 93.53)], 0.5, I3, TH33)

# --- LO B: in-block In3 path -> In4 (via (136,93) at R5 stays, In3 continues from it down passage J1-J2)
for a, b in [((139.75, 81.5), (139.75, 82)), ((139.75, 82), (137.5, 84.25)), ((137.5, 84.25), (137.5, 85)),
             ((137.5, 85), (136, 86.5)), ((136, 86.5), (136, 93))]:
    B.set_layer(LO, I3, a, b, I4)
B.save()
print("lay_B1 applied")
