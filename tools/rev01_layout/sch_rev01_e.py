"""+4 mm board, schematic part (Phase_A.kicad_sch, 3 sheet instances):
- §5 snubber R (R100 LS, R103 HS): 0.51 Ohm 1206 -> 0.47 Ohm 0612 wide terminal 1.5 W (05 P2: ~0.3 nH instead of
  ~0.75 nH, 1.5 W at 72-84 V; ROHM LTR18EZPFLR470 or similar). Still DNP.
- §4 loop ceramics: one more 1206 1 uF 100 V X7R per phase in the +4 mm strip, at the HS drain: C125/C129/C133,
  parallel to C124/C128/C132 (the place of the round-2 C125, removed in round 3). A second one per phase (05 P1)
  fits near the drain only without the HS snubber place (strip_plan.py), so it is not added.
Writes the new symbol uuids to <tools>/data/sch_e_uuids.json (the board footprints are linked to them).
Usage: sch_rev01_e.py <project dir> <tools dir>"""
import sys, os, re, json
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from schedit import Sch
D = sys.argv[1]
ROOT = "/7ff38f8b-11c9-43a1-8b76-b5e8c8de18e0/"
PH = {"C": "f977a2eb-d10b-44d6-a07c-b8311dd9b73f", "B": "7176583c-694b-43e7-a08f-7dfec6a5a7f3",
      "A": "fe135066-9555-4a85-b389-3791e4e86e93"}
FP_C1206 = "Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder"
FP_R0612 = "Resistor_SMD:R_0612_1632Metric_Pad1.18x3.40mm_HandSolder"

p = Sch(os.path.join(D, "Phase_A.kicad_sch"))
for ref in ("R100", "R103"):
    p.set_prop(ref, "Footprint", FP_R0612); p.set_prop(ref, "Value", "0.47"); p.set_prop(ref, "Description P/N", "Resistor SMD 0612 1.5W")
xs = [105.41, 120.65]                         # C124 stays at 105.41
YC, YT, YB = 137.16, 134.62, 139.7
for k, x in enumerate(xs[1:], start=1):
    refs = [(ROOT + PH[ph], f"C{124 + 4*i + k}") for i, ph in enumerate("CBA")]
    p.symbol("Device:C_Small", x, YC, 0, refs, "1u 100V X7R", FP_C1206,
             [("Description P/N", "Capacitor SMD 100V X7R")], ref_xy=(x + 1.27, YC - 0.635), val_xy=(x + 1.27, YC + 1.27),
             justify="left")
for a, b in zip(xs, xs[1:]):
    p.wire(a, YT, b, YT); p.wire(a, YB, b, YB)
p.save()
s = p.s; out = {}
for k in (1,):
    i = s.find(f'(property "Reference" "C{124 + k}"'); a = s.rfind("\n\t(symbol\n", 0, i)
    u = re.search(r'\n\t\t\(uuid "([^"]+)"\)', s[a:i]).group(1)
    for j, ph in enumerate("CBA"): out[f"C{124 + 4*j + k}"] = f"/{PH[ph]}/{u}"
json.dump(out, open(os.path.join(sys.argv[2], "data", "sch_e_uuids.json"), "w"), indent=1)
print("schematic +4 mm edits written:", out)
