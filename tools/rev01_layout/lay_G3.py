"""In3 = solid GND on the whole board (owner, 2026-10-17): every In3 track moves to In2 or In4 (both next to In3);
in the passages under the block the tracks run along the edges of the power zones.
- In2 (In3 at 0.1 mm): HO C, HO B (over their SW on In4), ADC, TMR1, D24-A, D13-K.
- In4: LO C/B/A and HO A (whole run now on In4, transition vias removed), NTC lines C (U1+, +3.3V),
  NTC B/A below the block (U2+, U3+), +12V, VDC_MCU, SWD, Temp_PCB_x (keeps the +3.3V plane on In2 whole).
Usage: lay_G3.py board.kicad_pcb"""
import re, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[0]))); sys.dont_write_bytecode = True
import pcbedit
TO = {"In4.Cu": ["/Driver_1/LO", "/Driver_2/LO", "/Driver_3/LO", "/Driver_1/HO", "Net-(U1-+)", "+3.3V", "+12V", "/VDC_MCU",
                 "Net-(U2-+)", "Net-(U3-+)", "/SWCLK_IN", "/SWDIO_IN", "/Temp_PCB_1_MCU", "/Temp_PCB_2_MCU", "/Temp_PCB_3_MCU"],
      "In2.Cu": ["/Driver_2/HO", "/Driver_3/HO", "Net-(D24-A)", "/ADC_IN_1", "/ADC_IN_2", "/TMR1_CH1", "/TMR1_CH2",
                 "Net-(D13-K)"]}
LAYER = {n: l for l, ns in TO.items() for n in ns}
B = pcbedit.Board(sys.argv[1])
moved = 0
for g in sorted(B.segments(layer="In3.Cu"), key=lambda g: -g["span"][0]):
    B.replace_seg(g, pcbedit.seg_text(g["x1"], g["y1"], g["x2"], g["y2"], g["w"], LAYER[g["net"]], g["net"], g["uuid"]))
    moved += 1
# LO A: straight down x 150 to its via (clear of SW B, which turns left at y 104.6)
LOA = "/Driver_1/LO"
B.del_segs(lambda g: g["net"] == LOA and g["layer"] == "In4.Cu" and (
    (abs(g["x1"] - 150.0) < 1e-3 and abs(g["y1"] - 104.0) < 1e-3 and abs(g["y2"] - 104.5) < 1e-3) or
    (abs(g["x1"] - 149.5) < 1e-3 and abs(g["x2"] - 149.5) < 1e-3) or
    (abs(g["x1"] - 149.5) < 1e-3 and abs(g["y1"] - 108.9) < 1e-3) or
    (abs(g["x1"] - 150.3) < 1e-3 and abs(g["x2"] - 150.6) < 1e-3)))
B.track([(150.0, 104.0), (150.0, 109.4), (150.3, 109.7), (150.6, 109.7)], 0.5, "In4.Cu", LOA)
B.save()
# LO C: the via at (124.0, 96.1) only joined In4 (block) to In3 (passage); both parts are on In4 now
B = pcbedit.Board(sys.argv[1])
n = B.del_vias(lambda v: v["net"] == "/Driver_3/LO" and abs(v["x"] - 124.0) < 1e-3 and abs(v["y"] - 96.1) < 1e-3)
# LO C at the removed via: one 45-degree bend instead of the 90-degree joint and the jog (clear of the node vias x 124)
LOC = "/Driver_3/LO"
pts = {frozenset({(124.0, 91.55), (124.0, 96.1)}), frozenset({(124.0, 96.1), (123.5875, 96.1)}),
       frozenset({(123.5875, 96.1), (123.25, 96.4375)}), frozenset({(123.25, 97.5), (123.25, 96.4375)})}
k = B.del_segs(lambda g: g["net"] == LOC and g["layer"] == "In4.Cu" and frozenset({(round(g["x1"], 4), round(g["y1"], 4)), (round(g["x2"], 4), round(g["y2"], 4))}) in pts)
assert k == 4, k
B.track([(124.0, 91.55), (124.0, 95.85)], 0.3, "In4.Cu", LOC); B.track([(124.0, 95.85), (123.25, 96.6), (123.25, 97.5)], 0.5, "In4.Cu", LOC)
B.save()
print("In3 segments moved:", moved, "| LO C transition via removed:", n)
