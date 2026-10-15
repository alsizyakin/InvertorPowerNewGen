"""rev0.1 schematic, round 2: off-branch without R_off (D_off straight from X to the driver pin), R_on 0603,
D_off standard SOD-323 (Driver.kicad_sch); loop ceramics §4, 4 per phase (Phase_A.kicad_sch)."""
import sys, os
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from schedit import Sch
D = sys.argv[1]
ROOT = "/7ff38f8b-11c9-43a1-8b76-b5e8c8de18e0/"
PH = {"C": ROOT + "f977a2eb-d10b-44d6-a07c-b8311dd9b73f", "B": ROOT + "7176583c-694b-43e7-a08f-7dfec6a5a7f3",
      "A": ROOT + "fe135066-9555-4a85-b389-3791e4e86e93"}
FP_R0603 = "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder"
FP_SOD323 = "Diode_SMD:D_SOD-323"
FP_C1206 = "Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder"

d = Sch(os.path.join(D, "Driver.kicad_sch"))
# R_off of HO (R109...) at (186.69, 96.52) and of LO (R115...) at (186.69, 120.65): replaced by a wire
for ref, y in (("R109", 96.52), ("R115", 120.65)):
    d.remove_symbol(ref)
    d.wire(184.15, y, 189.23, y)
for ref in ("R106", "R112"):
    d.set_prop(ref, "Footprint", FP_R0603)
for ref in ("D30", "D33"):
    d.set_prop(ref, "Footprint", FP_SOD323)
d.save()

p = Sch(os.path.join(D, "Phase_A.kicad_sch"))
xs = [105.41, 120.65, 135.89, 151.13]
YC, YT, YB = 137.16, 134.62, 139.7
for k, x in enumerate(xs):
    refs = [(PH[ph], f"C{124 + 4*i + k}") for i, ph in enumerate("CBA")]
    p.symbol("Device:C_Small", x, YC, 0, refs, "1u 100V X7R", FP_C1206,
             [("Description P/N", "Capacitor SMD 100V X7R")], ref_xy=(x + 1.27, YC - 0.635), val_xy=(x + 1.27, YC + 1.27),
             justify="left")
for a, b in zip(xs, xs[1:]):
    p.wire(a, YT, b, YT); p.wire(a, YB, b, YB)
for x in xs[1:-1]:
    p.junction(x, YT); p.junction(x, YB)
p.symbol("power:VDC", xs[0], YT, 0, [(PH[ph], f"#PWR{212 + i}") for i, ph in enumerate("CBA")], "VDC", "",
         pins=("1",), power=True, ref_xy=(xs[0], YT - 6.35), val_xy=(xs[0], YT - 3.81))
p.symbol("power:GND", xs[0], YB, 0, [(PH[ph], f"#PWR{215 + i}") for i, ph in enumerate("CBA")], "GND", "",
         pins=("1",), power=True, ref_xy=(xs[0], YB + 6.35), val_xy=(xs[0], YB + 3.81))
p.save()
print("round-2 schematic edits written")
