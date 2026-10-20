"""Owner 2026-10-20 (after round 3). Schematic part; the board part is lay_P4g.py.
Usage: sch_rev01_h.py <project dir> <tools dir>
- 09 E13: places for Y capacitors between the input bushings J4 / J5 (DNP): H5 - plated M3 hole, net CHASSIS (a screw
  into the heatsink, which is the chassis); C135 VDC -> CHASSIS, C136 GND -> CHASSIS, 1812.
- 11 P19: snubber R as two 0805 in parallel instead of one 0612 (not obtainable): R100-R105 become 1 Ohm 0805 and get a
  parallel 1 Ohm 0805 each (R124-R129) on the Phase_A sheet; 2 x 1 Ohm = 0.5 Ohm (was 0.47). Still DNP.
- 11 P20: no fuse on this board - the owner puts it on the connection board.
Writes the new symbol uuids to <tools>/data/sch_h_uuids.json (the board footprints are linked to them)."""
import sys, os, re, json
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from schedit import Sch, stock_symbol
D = sys.argv[1]
ROOT = "/7ff38f8b-11c9-43a1-8b76-b5e8c8de18e0"
YCAP = dict(value="4.7n Y2", fp="Capacitor_SMD:C_1812_4532Metric", pn="Capacitor SMD 1812 Y2 (or X7R 2kV)")
RSN = dict(value="1", fp="Resistor_SMD:R_0805_2012Metric", pn="Resistor SMD 0805 anti-surge 0.5W (ERJ-P06J1R0V)")
out = {}

def uuid_of(s, ref):
    i = s.find(f'(reference "{ref}")') if f'(reference "{ref}")' in s else s.find(f'(property "Reference" "{ref}"')
    a = s.rfind("\n\t(symbol\n", 0, i)
    return re.search(r'\n\t\t\(uuid "([^"]+)"\)', s[a:i]).group(1)

# ---------------------------------------------------------------- E13: H5 + C135 / C136 (DNP), root sheet
p = Sch(os.path.join(D, "Power.kicad_sch"))
if '(property "Reference" "H5"' not in p.s:
    pwr = 1 + max(int(n) for f in os.listdir(D) if f.endswith(".kicad_sch")
                  for n in re.findall(r'\(reference "#PWR0*(\d+)"\)', open(os.path.join(D, f), encoding="utf-8").read()))
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
for ref in ("C135", "C136", "H5"): out[ref] = "/" + uuid_of(p.s, ref)

# ---------------------------------------------------------------- P19: snubber R 2 x 0805, Phase_A sheet (3 instances)
q = Sch(os.path.join(D, "Phase_A.kicad_sch"))
INST = {"LS": (("R100", "R124"), ("R101", "R125"), ("R102", "R126"), 113.03),
        "HS": (("R103", "R127"), ("R104", "R128"), ("R105", "R129"), 81.28)}
if '(reference "R124")' not in q.s:
    for side, (*pairs, Y) in INST.items():
        X0, X = 135.89, 140.97
        i = q.s.find(f'(reference "{pairs[0][0]}")'); a = q.s.rfind("\n\t(symbol\n", 0, i)
        paths = dict((r, pth) for pth, r in re.findall(r'\(path "([^"]+)"\n\t+\(reference "([^"]+)"\)', q.s[a:q.s.find("\n\t)\n", i)]))
        q.set_prop(pairs[0][0], "Value", RSN["value"]); q.set_prop(pairs[0][0], "Footprint", RSN["fp"])
        q.set_prop(pairs[0][0], "Description P/N", RSN["pn"])
        q.symbol("Device:R_Small", X, Y, 0, [(paths[old], new) for old, new in pairs], RSN["value"], RSN["fp"],
                 [("Description P/N", RSN["pn"])], dnp=True, ref_xy=(X + 2.54, Y - 0.635), val_xy=(X + 2.54, Y + 1.905),
                 justify="left")
        for dy in (-2.54, 2.54):
            q.wire(X0, Y + dy, X, Y + dy); q.junction(X0, Y + dy)
    q.save()
for side, (*pairs, Y) in INST.items(): out[f"Rsn_{side}"] = uuid_of(q.s, pairs[0][1])
json.dump(out, open(os.path.join(sys.argv[2], "data", "sch_h_uuids.json"), "w"), indent=1)
print("schematic: H5 CHASSIS, C135 / C136 Y DNP; snubber R 2 x 0805 1 Ohm (R100-R105 + R124-R129)")
