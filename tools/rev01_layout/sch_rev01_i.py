"""rev0.1-ina-ref, owner 2026-10-21: a test point pair (DAC1 + GND) for the DAC output of U5 (PA4, label DAC_1_MCU),
for a scope probe or a soldered wire. Schematic part; the board part is lay_I3.py.
Usage: sch_rev01_i.py <project dir> <tools dir>
- TP1 Connector:TestPoint_2Pole on the root sheet right of U5, pin 1 to a DAC_1_MCU label (same sheet as the label at
  PA4, so the same net), pin 2 to GND. Footprint PinHeader_1x02_P2.54mm_Vertical (1.0 mm holes: a wire, two header pins
  or a probe tip). Not in the BOM: bare pads, nothing to fit.
Writes the uuid of TP1 to <tools>/data/sch_i_uuids.json (the board footprint is linked to it)."""
import sys, os, re, json
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from schedit import Sch, stock_symbol, U, f
D = sys.argv[1]
ROOT = "/7ff38f8b-11c9-43a1-8b76-b5e8c8de18e0"
FP = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
X, Y = 454.66, 326.39                                   # TP1; pin 1 at X - 5.08, pin 2 at X + 5.08
p = Sch(os.path.join(D, "Power.kicad_sch"))
if '(property "Reference" "TP1"' in p.s:
    sys.exit("sch_rev01_i: already applied")
p.add_lib(stock_symbol("TestPoint_2Pole", lib="/usr/share/kicad/symbols/Connector.kicad_sym", prefix="Connector"))
pwr = max(int(n) for n in re.findall(r'"#PWR(\d+)"', p.s)) + 1
p.symbol("Connector:TestPoint_2Pole", X, Y, 0, [(ROOT, "TP1")], "DAC1", FP, in_bom=False,
         ref_xy=(X, Y - 2.54), val_xy=(X, Y + 2.54), justify=None)
p.symbol("power:GND", X + 5.08, Y, 0, [(ROOT, f"#PWR{pwr:03d}")], "GND", "", pins=("1",), power=True,
         ref_xy=(X + 5.08, Y + 6.35), val_xy=(X + 5.08, Y + 3.81))
p.wire(X - 22.86, Y, X - 5.08, Y)
p.label("DAC_1_MCU", X - 22.86, Y, 0)
p.save()
p.set_prop("TP1", "Description", "2-polar test point")
p.save()
s = p.s; i = s.find('(property "Reference" "TP1"'); a = s.rfind("\n\t(symbol\n", 0, i)
u = re.search(r'\n\t\t\(uuid "([^"]+)"\)', s[a:i]).group(1)
json.dump({"TP1": f"/{u}"}, open(os.path.join(sys.argv[2], "data", "sch_i_uuids.json"), "w"), indent=1)
print("schematic: TP1 (DAC1 + GND) right of U5")
