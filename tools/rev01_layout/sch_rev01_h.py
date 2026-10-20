"""Owner 2026-10-20 (after round 3). Schematic part; the board part is lay_P4g.py.
Usage: sch_rev01_h.py <project dir> <tools dir>
- 11 P20: fuse F1 in the VDC line to the connection board (J6). J6 pins 1-4, C134 and the bus divider R68 (it is fed
  from J6.2 on the board) move to the new net VDC_J6; F1 sits between VDC and VDC_J6 on the root sheet. On the board it
  is at the start of the line, at the bulk caps.
- 09 E13: places for Y capacitors between the input bushings J4 / J5 (DNP): H5 - plated M3 hole, net CHASSIS (a screw
  or a ring lug to the chassis); C135 VDC -> CHASSIS, C136 GND -> CHASSIS, 1812.
Writes the new symbol uuids to <tools>/data/sch_h_uuids.json (the board footprints are linked to them)."""
import sys, os, re, json
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from schedit import Sch, stock_symbol, block_at
D = sys.argv[1]
ROOT = "/7ff38f8b-11c9-43a1-8b76-b5e8c8de18e0"
FUSE = dict(value="1A 125V DC", fp="Fuse:Fuse_Littelfuse-NANO2-451_453",
            pn="Fuse SMD 2410 1A 125V DC: Bel 0679L1000 (alt. Littelfuse 0452001.MRL)")
YCAP = dict(value="4.7n Y2", fp="Capacitor_SMD:C_1812_4532Metric", pn="Capacitor SMD 1812 Y2 (or X7R 2kV)")

p = Sch(os.path.join(D, "Power.kicad_sch"))

def drop_symbol(lib_id, x, y):
    """remove the symbol `lib_id` placed at (x, y)"""
    m = [m for m in re.finditer(r'\n\t\(symbol\n\t\t\(lib_id "' + re.escape(lib_id) + r'"\)\n\t\t\(at ([\d.\-]+) ([\d.\-]+) ', p.s)
         if abs(float(m.group(1)) - x) < 1e-3 and abs(float(m.group(2)) - y) < 1e-3]
    if not m: return False
    assert len(m) == 1, (lib_id, x, y)
    a, b = block_at(p.s, m[0].start() + 2); p.s = p.s[:m[0].start() + 1] + p.s[b + 1:]
    return True

if '(property "Reference" "F1"' not in p.s:
    # ------------------------------------------------------------ P20: J6 pins 1-4 and C134 to VDC_J6
    for x, y, ang in ((309.88, 177.8, 180), (309.88, 180.34, 180), (322.58, 180.34, 0), (330.2, 177.8, 0)):
        assert drop_symbol("power:VDC", x, y), (x, y)
        p.label("VDC_J6", x, y, ang)
    assert drop_symbol("power:VDC", 304.8, 208.28)                        # C134 pin 1
    p.label("VDC_J6", 304.8, 208.28, 90)
    assert drop_symbol("power:VDC", 328.93, 350.52)                       # R68: bus divider for the ADC, fed at J6.2
    p.label("VDC_J6", 328.93, 350.52, 90)
    pwr = max(int(n) for n in re.findall(r'\(reference "#PWR0*(\d+)"\)', p.s)) + 1
    for f in os.listdir(D):
        if f.endswith(".kicad_sch"):
            pwr = max([pwr] + [int(n) + 1 for n in re.findall(r'\(reference "#PWR0*(\d+)"\)', open(os.path.join(D, f), encoding="utf-8").read())])
    p.add_lib(stock_symbol("Fuse"))
    X, Y = 320.04, 215.9
    p.symbol("Device:Fuse", X, Y, 0, [(ROOT, "F1")], FUSE["value"], FUSE["fp"], [("Description P/N", FUSE["pn"])],
             ref_xy=(X + 2.54, Y - 1.27), val_xy=(X + 2.54, Y + 1.27), justify="left")
    p.symbol("power:VDC", X, Y - 3.81, 0, [(ROOT, f"#PWR{pwr:03d}")], "VDC", "", pins=("1",), power=True,
             ref_xy=(X, Y - 7.62), val_xy=(X, Y - 7.62))
    p.label("VDC_J6", X, Y + 3.81, 270)
    pwr += 1
    # the PWR_FLAG of VDC (#FLG09) was at J6 and stays on VDC_J6: VDC gets its own next to F1
    flg = max(int(n) for f in os.listdir(D) if f.endswith(".kicad_sch")
              for n in re.findall(r'\(reference "#FLG0*(\d+)"\)', open(os.path.join(D, f), encoding="utf-8").read())) + 1
    p.wire(X, Y - 3.81, X - 2.54, Y - 3.81)
    p.symbol("power:PWR_FLAG", X - 2.54, Y - 3.81, 0, [(ROOT, f"#FLG0{flg:02d}")], "PWR_FLAG", "", pins=("1",), power=True,
             ref_xy=(X - 2.54, Y - 5.715), val_xy=(X - 2.54, Y - 7.62), hide_value=True)
    # ------------------------------------------------------------ E13: H5 + C135 / C136 (DNP)
    p.add_lib(stock_symbol("MountingHole_Pad", "/usr/share/kicad/symbols/Mechanical.kicad_sym", "Mechanical"))
    W = 222.25                                                              # CHASSIS wire
    for ref, X, top in (("C135", 365.76, "VDC"), ("C136", 381.0, "GND")):
        Y = 214.63
        p.symbol("Device:C_Small", X, Y, 0, [(ROOT, ref)], YCAP["value"], YCAP["fp"], [("Description P/N", YCAP["pn"])],
                 dnp=True, ref_xy=(X + 2.54, Y - 0.635), val_xy=(X + 2.54, Y + 1.905), justify="left")
        if top == "VDC":
            p.symbol("power:VDC", X, Y - 2.54, 0, [(ROOT, f"#PWR{pwr:03d}")], "VDC", "", pins=("1",), power=True,
                     ref_xy=(X, Y - 6.35), val_xy=(X, Y - 6.35))
        else:
            p.symbol("power:GND", X, Y - 2.54, 180, [(ROOT, f"#PWR{pwr:03d}")], "GND", "", pins=("1",), power=True,
                     ref_xy=(X, Y - 8.89), val_xy=(X, Y - 6.35))
        pwr += 1
        p.wire(X, Y + 2.54, X, W)
    p.wire(365.76, W, 381.0, W)
    p.symbol("Mechanical:MountingHole_Pad", 373.38, W - 2.54, 0, [(ROOT, "H5")], "MountingHole_Pad",
             "MountingHole:MountingHole_3.2mm_M3_Pad_Via", pins=("1",), in_bom=False,
             ref_xy=(375.92, W - 5.08), val_xy=(375.92, W - 3.175), justify="left")
    p.junction(373.38, W)
    p.label("CHASSIS", 367.03, W, 0)
p.save()
out = {}
for ref in ("F1", "C135", "C136", "H5"):
    i = p.s.find(f'(property "Reference" "{ref}"'); a = p.s.rfind("\n\t(symbol\n", 0, i)
    out[ref] = "/" + re.search(r'\n\t\t\(uuid "([^"]+)"\)', p.s[a:i]).group(1)
json.dump(out, open(os.path.join(sys.argv[2], "data", "sch_h_uuids.json"), "w"), indent=1)
print("schematic: F1 VDC -> VDC_J6 (J6.1-4, C134); H5 CHASSIS, C135 / C136 Y DNP")
