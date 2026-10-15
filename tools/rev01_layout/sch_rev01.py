"""rev0.1 schematic edits: Driver.kicad_sch (§3.1 SW+NetTie, §3.3 off-branch per position, §6 HI/LI RC) and
Phase_A.kicad_sch (§3.3 R_g,i + C_gs, §5 snubbers). Usage: sch_rev01.py <project dir> <tools dir>"""
import sys, os, re, uuid
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from schedit import Sch, cached_symbol, stock_symbol
D = sys.argv[1]
ROOT = "/7ff38f8b-11c9-43a1-8b76-b5e8c8de18e0/"
DRV = {"C": ROOT + "a8d734bd-b043-4b16-b834-36ede11366f7", "B": ROOT + "47ea5ea6-75b2-417d-becc-0c7b63ba572f",
       "A": ROOT + "f6f48504-43ae-4516-9932-88fd69aadde3"}
PH = {"C": ROOT + "f977a2eb-d10b-44d6-a07c-b8311dd9b73f", "B": ROOT + "7176583c-694b-43e7-a08f-7dfec6a5a7f3",
      "A": ROOT + "fe135066-9555-4a85-b389-3791e4e86e93"}
def refs(paths, prefix, first):          # phases C, B, A get first, first+1, first+2
    return [(paths[p], f"{prefix}{first + i}") for i, p in enumerate("CBA")]
FP_R0603 = "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder"
FP_R0805 = "Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder"
FP_R1206 = "Resistor_SMD:R_1206_3216Metric_Pad1.30x1.75mm_HandSolder"
FP_C0603 = "Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder"
FP_C0805 = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
FP_SOD323 = "Diode_SMD:D_SOD-323_HandSoldering"
FP_NT = "NetTie:NetTie-2_SMD_Pad0.5mm"
R_DESC = [("Description P/N", "Resistor SMD 1%")]
def Rh(x, y):    # fields of a horizontal resistor (symbol rotated 90): reference above, value below
    return dict(fang=90, ref_xy=(x, y - 1.905), val_xy=(x, y + 1.905))
def Cv(x, y, side=1):  # fields of a vertical capacitor, to the right (side=1) or to the left (side=-1)
    j = "left" if side > 0 else "right"
    return dict(justify=j, ref_xy=(x + side * 1.905, y - 0.635), val_xy=(x + side * 1.905, y + 1.27))

# ------------------------------------------------------------------ Driver.kicad_sch
d = Sch(os.path.join(D, "Driver.kicad_sch"))
d.add_lib(cached_symbol(os.path.join(D, "Phase_A.kicad_sch"), "Device:R_Small"))
d.add_lib(stock_symbol("D_Schottky_Small")); d.add_lib(stock_symbol("NetTie_2"))
# §3.3: off-branch per position: driver pin -> R_on -> X -> hier. label; X -> D_off (A->K) -> R_off -> driver pin side.
# HO: main line y 104.14, branch above (96.52). LO: brought down to y 113.03, branch below (120.65).
D_HO = dict(name="HO", pin_y=104.14, y=104.14, yb=96.52, n=(106, 109, 30))
D_LO = dict(name="LO", pin_y=107.95, y=113.03, yb=120.65, n=(112, 115, 33))
for g in (D_HO, D_LO):
    name, y, yb = g["name"], g["y"], g["yb"]; r_on, r_off, d_off = g["n"]
    d.move_label("hierarchical_label", name, (151.13, g["pin_y"]), (204.47, y))
    if g["pin_y"] == y:
        d.wire(151.13, y, 184.15, y)
    else:
        d.wire(151.13, g["pin_y"], 176.53, g["pin_y"]); d.wire(176.53, g["pin_y"], 176.53, y); d.wire(176.53, y, 184.15, y)
    d.label(f"{name}_DRV", 163.83, g["pin_y"])
    d.symbol("Device:R_Small", 186.69, y, 90, refs(DRV, "R", r_on), "0.82", FP_R0805, R_DESC, **Rh(186.69, y))
    d.wire(189.23, y, 196.85, y); d.wire(196.85, y, 204.47, y); d.junction(196.85, y); d.junction(184.15, y)
    d.wire(184.15, y, 184.15, yb)
    d.symbol("Device:R_Small", 186.69, yb, 90, refs(DRV, "R", r_off), "0", FP_R0603, R_DESC, **Rh(186.69, yb))
    d.wire(189.23, yb, 191.77, yb)
    d.symbol("Device:D_Schottky_Small", 194.31, yb, 0, refs(DRV, "D", d_off), "PMEG4010BEA", FP_SOD323,
             [("Description P/N", "Schottky Diode"), ("Product Name", "PMEG4010BEA")],
             ref_xy=(194.31, yb - 2.54), val_xy=(194.31, yb + 2.54))
    d.wire(196.85, yb, 196.85, y)
# §3.1: SW of the driver is its own net, tied to the node by a NetTie placed at the HS sources on the PCB
d.move_label("hierarchical_label", "Phase", (160.02, 100.33), (167.64, 100.33))
d.label("SW", 156.21, 100.33)
d.symbol("Device:NetTie_2", 162.56, 100.33, 0, refs(DRV, "NT", 1), "NetTie_2", FP_NT, in_bom=False,
         ref_xy=(162.56, 98.425), val_xy=(162.56, 102.235), hide_value=True)
d.wire(165.1, 100.33, 167.64, 100.33)
# §6: series R and C to GND at HI / LI; the two resistors are staggered so that their fields do not overlap
for name, y, xr, (r, c, pw), up in (("HI", 96.52, 120.65, (118, 118, 200), True),
                                    ("LI", 100.33, 110.49, (121, 121, 203), False)):
    d.move_label("hierarchical_label", name, (128.27, y), (105.41, y))
    d.wire(105.41, y, xr - 2.54, y)
    d.symbol("Device:R_Small", xr, y, 90, refs(DRV, "R", r), "0", FP_R0603, R_DESC, **Rh(xr, y))
    d.wire(xr + 2.54, y, 128.27, y); d.junction(128.27, y)
    s = -1 if up else 1
    d.symbol("Device:C_Small", 128.27, y + s * 2.54, 0, refs(DRV, "C", c), "100p", FP_C0603,
             [("Description P/N", "Capacitor SMD 50V")], dnp=True, **Cv(128.27, y + s * 2.54, side=-1))
    d.symbol("power:GND", 128.27, y + s * 5.08, 180 if up else 0, [(DRV[p], f"#PWR{pw + i}") for i, p in enumerate("CBA")],
             "GND", "", pins=("1",), power=True, ref_xy=(128.27, y + s * 11.43), val_xy=(128.27, y + s * 9.0))
d.save()

# ------------------------------------------------------------------ Phase_A.kicad_sch
p = Sch(os.path.join(D, "Phase_A.kicad_sch"))
p.add_lib(cached_symbol(os.path.join(D, "Driver.kicad_sch"), "Device:C_Small"))
# §3.3: R_g -> R_g,i 1 Ohm 0603; both fields moved above the resistor to free room for C_gs below it
for r, (x, y) in (("R23", (106.68, 78.74)), ("R1", (156.21, 78.74)), ("R25", (106.68, 109.22)), ("R4", (156.21, 109.22))):
    p.set_prop(r, "Value", "1"); p.set_prop(r, "Footprint", FP_R0603)
    p.set_field(r, "Reference", x - 1.905, y - 1.905, 90); p.set_field(r, "Value", x + 1.905, y - 1.905, 90)
# C_gs (DNP) in parallel with each R_gs, 5.08 mm to the left of it; R_gs pins: (x, y-2.54) gate, (x, y+2.54) source
CGS = [((111.76, 82.55), 100), ((161.29, 82.55), 101), ((111.76, 113.665), 102), ((161.29, 113.665), 103)]
for (xr, yr), n in CGS:
    xc = xr - 5.08
    p.symbol("Device:C_Small", xc, yr, 0, [(PH[ph], f"C{n + 4*i}") for i, ph in enumerate("CBA")], "4.7n", FP_C0603,
             [("Description P/N", "Capacitor SMD 50V")], dnp=True, **Cv(xc, yr, side=-1))
    p.wire(xc, yr - 2.54, xr, yr - 2.54); p.wire(xc, yr + 2.54, xr, yr + 2.54)
# §5: snubbers (DNP), one per position: HS = VDC - C - R - Phase ; LS = Phase - C - R - GND
X = 135.89
shape = re.search(r'\(hierarchical_label "Phase"\n\t\t\(shape (\w+)\)', p.s).group(1)
lab = ('\t(hierarchical_label "Phase"\n\t\t(shape ' + shape + ')\n\t\t(at {x} {y} 0)\n\t\t(effects\n\t\t\t(font\n'
       '\t\t\t\t(size 1.27 1.27)\n\t\t\t\t(thickness 0.254)\n\t\t\t\t(bold yes)\n\t\t\t)\n\t\t\t(justify left)\n\t\t)\n'
       '\t\t(uuid "{u}")\n\t)\n')
p.symbol("power:VDC", X, 72.39, 0, refs(PH, "#PWR", 206), "VDC", "", pins=("1",), power=True,
         ref_xy=(X, 66.04), val_xy=(X, 68.58))
p.symbol("Device:C_Small", X, 74.93, 0, refs(PH, "C", 115), "4.7n 100V C0G", FP_C0805,
         [("Description P/N", "Capacitor SMD 100V C0G")], dnp=True, **Cv(X, 74.93))
p.wire(X, 77.47, X, 78.74)
p.symbol("Device:R_Small", X, 81.28, 0, refs(PH, "R", 103), "0.51", FP_R1206,
         [("Description P/N", "Resistor SMD 0.5W")], dnp=True, **Cv(X, 81.28))
p.wire(X, 83.82, X, 86.36); p.wire(X, 86.36, X + 2.54, 86.36)
p.new.append(lab.format(x="138.43", y="86.36", u=uuid.uuid4()))
p.new.append(lab.format(x="138.43", y="101.6", u=uuid.uuid4()))
p.wire(X, 101.6, X + 2.54, 101.6); p.wire(X, 101.6, X, 104.14)
p.symbol("Device:C_Small", X, 106.68, 0, refs(PH, "C", 112), "4.7n 100V C0G", FP_C0805,
         [("Description P/N", "Capacitor SMD 100V C0G")], dnp=True, **Cv(X, 106.68))
p.wire(X, 109.22, X, 110.49)
p.symbol("Device:R_Small", X, 113.03, 0, refs(PH, "R", 100), "0.51", FP_R1206,
         [("Description P/N", "Resistor SMD 0.5W")], dnp=True, **Cv(X, 113.03))
p.wire(X, 115.57, X, 118.11)
p.symbol("power:GND", X, 118.11, 0, refs(PH, "#PWR", 209), "GND", "", pins=("1",), power=True,
         ref_xy=(X, 124.46), val_xy=(X, 122.0))
p.save()
print("schematic edits written")
