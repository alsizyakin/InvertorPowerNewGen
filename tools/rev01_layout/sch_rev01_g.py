"""Reviews 11 / 13 (round 3), owner 2026-10-20. Schematic part; the board part is lay_P4f.py.
Usage: sch_rev01_g.py <project dir> <tools dir>
- 13 E19: C134 100n 100V X7R 0805 between VDC and GND at J6 (root sheet), the place is on B.Cu next to J6.1/J6.2.
- 13 E24: OCP / ADC filter C37 / C39 / C64 100n -> 15n (120 Ohm x 15 nF = 88 kHz, as on the rev0 boards).
- 13 E26: R50 (CAN termination 120 Ohm) DNP - the termination moves to the connection board.
- 11 P16: pin 4 (NC) of U4 / U9 / U12 to GND: INA241A2 (the 72 V replacement) needs it grounded, INA240 allows it.
  The pin is no_connect and hidden in the project symbol Logic_My:INA240A1D: it becomes passive and visible.
Writes the uuid of C134 to <tools>/data/sch_g_uuids.json (the board footprint is linked to it)."""
import sys, os, re, json
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from schedit import Sch
D = sys.argv[1]
ROOT = "/7ff38f8b-11c9-43a1-8b76-b5e8c8de18e0"

def pin4_passive(t):
    """INA240A1D symbol text: pin 4 'no_connect' + hidden -> 'passive' + shown."""
    a = t.find('(pin no_connect line\n')
    if a < 0: return t
    b = t.find('(number "4"', a); assert 0 < b - a < 400, "pin 4 block"
    blk = t[a:b].replace("(pin no_connect line", "(pin passive line", 1)
    blk = re.sub(r'\n\t+\(hide yes\)', "", blk, count=1)
    return t[:a] + blk + t[b:]

# ---------------------------------------------------------------- P16
lib = os.path.join(D, "Lib", "Logic_My.kicad_sym"); s = open(lib, encoding="utf-8").read()
m = re.search(r'^\t?\(symbol "INA240A1D"\n', s, re.M); assert m, "INA240A1D in Logic_My"   # sch_rev01_f writes it at column 0
i = m.start(); n = re.compile(r'\n\t?\(symbol "').search(s, i + 5); j = n.start() if n else len(s)
s = s[:i] + pin4_passive(s[i:j]) + s[j:]; open(lib, "w", encoding="utf-8").write(s)
pwr = 218
for fn in ("Current_Sensor_1.kicad_sch", "Current_Sensor_2.kicad_sch", "Current_Sensor_3.kicad_sch"):
    p = Sch(os.path.join(D, fn))
    i = p.s.find('\t\t(symbol "Logic_My:INA240A1D"\n'); j = p.s.find('\n\t\t(symbol "', i + 5)
    p.s = p.s[:i] + pin4_passive(p.s[i:j]) + p.s[j:]
    k = p.s.find('(lib_id "Logic_My:INA240A1D")')
    x, y = map(float, re.search(r'\(at ([\d.\-]+) ([\d.\-]+) 0\)', p.s[k:k + 200]).groups())
    path = re.search(r'\(path "(/[^"]+)"\n\t+\(reference "U\d+"\)', p.s[k:]).group(1)
    if f"(at {x + 2.54:g} {y + 7.62:g} 0)" not in p.s:
        p.symbol("power:GND", round(x + 2.54, 2), round(y + 7.62, 2), 0, [(path, f"#PWR{pwr:03d}")], "GND", "",
                 pins=("1",), power=True, ref_xy=(x + 2.54, y + 13.97), val_xy=(x + 2.54, y + 11.43))
    pwr += 1
    # E24
    for ref in ("C37", "C39", "C64"):
        if f'(property "Reference" "{ref}"' in p.s: p.set_prop(ref, "Value", "15n")
    p.save()

# ---------------------------------------------------------------- E19, E26
p = Sch(os.path.join(D, "Power.kicad_sch"))
i = p.s.find('(property "Reference" "R50"'); a = p.s.rfind("\n\t(symbol\n", 0, i)
blk = p.s[a:i]; p.s = p.s[:a] + blk.replace("(dnp no)", "(dnp yes)", 1) + p.s[i:]
if '(property "Reference" "C134"' not in p.s:
    X, Y = 304.8, 210.82
    p.symbol("Device:C_Small", X, Y, 0, [(ROOT, "C134")], "100n 100V X7R",
             "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder", [("Description P/N", "Capacitor SMD 100V X7R")],
             ref_xy=(X + 2.54, Y - 0.635), val_xy=(X + 2.54, Y + 1.905), justify="left")
    p.symbol("power:VDC", X, Y - 2.54, 0, [(ROOT, f"#PWR{pwr:03d}")], "VDC", "", pins=("1",), power=True,
             ref_xy=(X, Y - 6.35), val_xy=(X, Y - 6.35))
    p.symbol("power:GND", X, Y + 2.54, 0, [(ROOT, f"#PWR{pwr + 1:03d}")], "GND", "", pins=("1",), power=True,
             ref_xy=(X, Y + 8.89), val_xy=(X, Y + 6.35))
p.save()
s = p.s; i = s.find('(property "Reference" "C134"'); a = s.rfind("\n\t(symbol\n", 0, i)
u = re.search(r'\n\t\t\(uuid "([^"]+)"\)', s[a:i]).group(1)
json.dump({"C134": f"/{u}"}, open(os.path.join(sys.argv[2], "data", "sch_g_uuids.json"), "w"), indent=1)
print("schematic: C134 at J6, C37/C39/C64 15n, R50 DNP, U4/U9/U12 pin 4 to GND")
