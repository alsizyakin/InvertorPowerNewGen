"""rev0.1-shift3, step 16 (owner 2026-10-20: "1 - согласен", "2 - лучше сделать одинаково"). Usage: lay_S3d.py board
F30 HO / SW of the drivers of phases C and B on In4, from the driver vias to the top of the passage: the two lines ran
    0.5 mm apart (B: 0.35 on the vertical run). HO moves towards SW to 0.25 mm (0.3 mm tracks, 0.55 mm centre to centre),
    the corners stay concentric (the diagonal of HO is offset by 0.55 mm across, like the straight runs). SW and the
    vias stay. Phase A has HO on In4 and SW on In1: no pair on one layer.
F31 One width per net along all its layers (WIDTH below). Power nets keep their trunks (GND, VDC, +3.3V, +3.3VA, +12V).
    The width of a net is the width most of its length already has (the inner layers of the gate lines), unless that
    breaks a clearance somewhere on the net; then the narrowest width of the net."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.dont_write_bytecode = True
import pcbedit
fn = sys.argv[1]
B = pcbedit.Board(fn)
if any(abs(g["x1"] - 126.3) < 1e-3 and abs(g["x2"] - 126.3) < 1e-3 for g in B.segments("/Driver_3/HO", "In4.Cu")):
    sys.exit("lay_S3d: already applied")

def near(p, q, t=2e-3): return abs(p[0] - q[0]) < t and abs(p[1] - q[1]) < t
def drop(net, layer, pts):
    return B.del_segs(lambda g: g["net"] == net and g["layer"] == layer and any(near((g["x1"], g["y1"]), p) for p in pts)
                      and any(near((g["x2"], g["y2"]), p) for p in pts))

# ---------------------------------------------------------------- F30
S = 0.55                                    # HO - SW centre to centre (0.25 mm gap)
def ho_path(via_in, sw_x, sw_y, sw_diag, end):
    """HO from its driver via down at x sw_x - S, a 45-degree corner concentric with SW's (SW diagonal from sw_diag
    with x - y = c), along y sw_y + S, then `end` (points to the HO via at the passage)"""
    x, y = sw_x - S, sw_y + S
    c = (sw_diag[0] - sw_diag[1]) - S*math.sqrt(2)
    d0 = (round(x, 3), round(x - c, 3)); d1 = (round(c + y, 3), round(y, 3))
    first = (round(x, 3), round(via_in[1] + (x - via_in[0]), 3))      # 45 degrees out of the driver via
    return [via_in, first, d0, d1] + end
# phase C: HO via (125.55, 83.25) -> ... -> via (133.75, 90.65); SW x 126.85 / y 89.85, its corner from (126.85, 89.05)
HO, SW = "/Driver_3/HO", "/Driver_3/SW"
assert drop(HO, "In4.Cu", [(125.55, 83.25), (126.05, 83.75), (126.05, 89.85), (126.85, 90.65), (133.75, 90.65)]) == 4
B.track(ho_path((125.55, 83.25), 126.85, 89.85, (126.85, 89.05), [(133.5, 90.4), (133.75, 90.65)]), 0.3, "In4.Cu", HO)
# phase B: HO via (142.55, 83.25) -> ... -> (148.5, 91.05) -> via (148.5, 92.0); SW x 144.85 / y 89.85, corner from (144.85, 89.05)
HO, SW = "/Driver_2/HO", "/Driver_2/SW"
assert drop(HO, "In4.Cu", [(142.55, 83.25), (144.2, 84.9), (144.2, 90.05), (144.8, 90.65), (148.1, 90.65), (148.5, 91.05)]) == 5
B.track(ho_path((142.55, 83.25), 144.85, 89.85, (144.85, 89.05), [(147.85, 90.4), (148.5, 91.05)]), 0.3, "In4.Cu", HO)
B.save()
print("F30: HO / SW pairs of phases C and B on In4 at 0.25 mm")

# ---------------------------------------------------------------- F31
# 0.5: the gate lines (LO on In4, R_g - gate of C100-C111) and D8 / D9; the 0.3 / 0.4 stubs at pins widened.
# 0.3: everything else - HO / SW and the thermistor lines (0.3 on the inner layers), the MCU lines. Temp_PCB, Current_measure,
# ADC_IN_1, BkIN_1, VDC_MCU and VCAP ran mostly at 0.5, but 0.5 breaks a clearance at the MCU pins, so they are 0.3 now.
W05 = [
    "/Driver_1/LO", "/Driver_2/LO", "/Driver_3/LO", "Net-(C100-Pad1)", "Net-(C101-Pad1)", "Net-(C102-Pad1)",
    "Net-(C103-Pad1)", "Net-(C104-Pad1)", "Net-(C105-Pad1)", "Net-(C106-Pad1)", "Net-(C107-Pad1)", "Net-(C108-Pad1)",
    "Net-(C109-Pad1)", "Net-(C110-Pad1)", "Net-(C111-Pad1)", "Net-(D8-K)", "Net-(D9-K)",
]
W03 = [
    "/ADC_IN_1", "/ADC_IN_2", "/ADC_IN_3", "/BkIN_1", "/CAN1_TXD_MCU", "/Current_measure_1", "/Current_measure_2",
    "/Current_measure_3", "/Driver_1/HO", "/Driver_1/SW", "/Driver_2/HO", "/Driver_2/SW", "/Driver_3/HO",
    "/Driver_3/SW", "/Hall_1_MCU", "/Hall_2_MCU", "/Hall_3_MCU", "/Temp_PCB_1_MCU", "/Temp_PCB_2_MCU",
    "/Temp_PCB_3_MCU", "/VDC_MCU", "NRST", "Net-(U1-+)", "Net-(U2-+)", "Net-(U3-+)", "Net-(U5-PH0)", "Net-(U5-PH1)",
    "Net-(U5-VCAP_1)", "Net-(U5-VCAP_2)",
]
WIDTH = {n: 0.5 for n in W05} | {n: 0.3 for n in W03}
B = pcbedit.Board(fn); n = 0
for g in sorted(B.segments(), key=lambda g: -g["span"][0]):     # from the end of the file: earlier spans stay valid
    w = WIDTH.get(g["net"])
    if w is not None and abs(g["w"] - w) > 1e-6:
        B.replace_seg(g, pcbedit.seg_text(g["x1"], g["y1"], g["x2"], g["y2"], w, g["layer"], g["net"], g["uuid"])); n += 1
B.save()
print(f"F31: one width per net, {len(WIDTH)} nets, {n} segments changed")
