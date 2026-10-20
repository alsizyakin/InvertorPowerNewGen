"""Branch rev0.1-shift3 (owner 2026-10-20: no +4 mm; the switch block goes 3 mm down instead, the MCU zone gives the room).
Schematic part of the 3 mm strip (instead of sch_rev01_e.py of the +4 mm board). Usage: sch_rev01_s3.py <project dir>
- snubber R (R100 LS, R103 HS, 3 sheet instances each): one 1206 (the 0612 / 2 x 0805 does not fit a 3 mm strip),
  0.51 -> 0.47 Ohm, anti-surge >= 0.5 W (11 P19: 0.13-0.16 W at 72 V with ~29 ns edges, up to 0.4 W at 6 ns);
  footprint stays R_1206 HandSolder;
- snubber C (C112 LS, C115 HS): C_0805 with standard pads - with HandSolder pads on both C and R the HS chain of phase B
  does not fit next to the LS one (strip_plan.py, 2026-10-20);
- no second 1206 per phase: it fits in phases C and A only, and the three phases share the sheet Phase_A."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.dont_write_bytecode = True
from schedit import Sch
q = Sch(os.path.join(sys.argv[1], "Phase_A.kicad_sch"))
for ref in ("R100", "R103"):
    q.set_prop(ref, "Value", "0.47"); q.set_prop(ref, "Description P/N", "Resistor SMD 1206 anti-surge 0.5W")
for ref in ("C112", "C115"): q.set_prop(ref, "Footprint", "Capacitor_SMD:C_0805_2012Metric")
q.save()
print("schematic: snubber R 1206 0.47 Ohm anti-surge, snubber C 0805 standard pads")
