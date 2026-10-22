"""rev0.1-adapto, Y circuit (owner's spec docs/Y_TASK.md, 2026-10-22). Schematic part; the board part is lay_Y1.py.
Usage: sch_rev01_j.py <project dir> <tools dir>
- out: H5 (plated M3 between J4 / J5) and the symmetric Y pair C135 (VDC-CHASSIS) / C136 (GND-CHASSIS): no place in the
  ADAPTO top zone, and the spec wants one chain from the minus only
- in, a framed block "Y-цепь корпуса" on the root sheet: CHASSIS - CY1 - CY2 - FY1 - GND, and RY1 - RY2 across the CY
  stack straight to GND (not through FY1); nets CHASSIS, CY_MID, Y_F, RY_MID; test points TP2 (CHS) / TP3 (GND)
- H2 (right U-slot, 8.4 mm from the minus bushing J5) becomes MountingHole_Pad on CHASSIS (H_CHS); H1, H3, H4 stay
  without pad
- fields MPN / Alt_MPN / Note (Y_TASK 3.6), FY1 Variant (the project has no KiCad design variants: Y_TASK 3.5)
Writes the new symbol uuids to <tools>/data/sch_j_uuids.json (the board footprints are linked to them)."""
import sys, os, re, json
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from schedit import Sch, stock_symbol, U, f
D = sys.argv[1]
ROOT = "/7ff38f8b-11c9-43a1-8b76-b5e8c8de18e0"
CY = dict(value="470n 250V X7R", fp="Capacitor_SMD:C_1812_4532Metric",
          pn="Capacitor SMD 1812 470nF 250V X7R soft termination",
          mpn="C1812X474KARACAUTO", alt="CGA8N3X7R2E474K230KE; GCJ43DR72E474KXJ1L",
          note="soft termination, 250 V - не заменять на 100 V")
RY = dict(value="100k", fp="Resistor_SMD:R_0805_2012Metric", pn="Resistor SMD 0805 100k 5% 150V",
          mpn="RC0805JR-07100KL", alt="ERJ-6GEYJ104V", note="2 x 100k последовательно: делят напряжение и импульс ESD")
FY = dict(value="2A 125VDC", fp="Power_My:Fuse_2410_1206", pn="Fuse SMD 2410 2A fast 125V DC / 0R 1206",
          mpn="0453002.MR", alt="0451002.MRL",
          note="двойной отказ CY при плюсе на раме; 125 V DC: 50 A, до 75 V DC: 10 kA; 63 V DC мало для 73 V",
          variant="Стенд: 0R 1206 (RC1206JR-070RL); Серия: предохранитель 2410 2A >= 125V DC (0453002.MR)")
for k, v in json.loads(os.environ.get("Y_MPN", "{}")).items():        # MPNs from the search can be passed in
    {"CY": CY, "RY": RY, "FY": FY}[k[:2]][k[3:]] = v

p = Sch(os.path.join(D, "Power.kicad_sch"))
if '(property "Reference" "CY1"' in p.s:
    sys.exit("sch_rev01_j: already applied")
# ---------------------------------------------------------------- out: H5, C135, C136 with their VDC / GND symbols
for ref in ("H5", "C135", "C136", "#PWR223", "#PWR224", "H2"):
    p.remove_symbol(ref)
for w in ((365.76, 222.25, 381.0, 222.25), (381.0, 217.17, 381.0, 222.25), (365.76, 217.17, 365.76, 222.25)):
    p.remove_wire(*w)
a, b = p._find_block(r'\n\t\(junction\n\t\t\(at 373\.38 222\.25\)'); p.s = p.s[:a - 1] + p.s[b:]
a, b = p._find_block(r'\n\t\(label "CHASSIS"\n\t\t\(at 367\.03 222\.25 '); p.s = p.s[:a - 1] + p.s[b:]

# ---------------------------------------------------------------- in: the Y block (frame 431.8-576.58 x 236.22-279.4)
p.add_lib(stock_symbol("Fuse_Small"))
p.add_lib(stock_symbol("TestPoint", "/usr/share/kicad/symbols/Connector.kicad_sym", "Connector"))
pwr = 1 + max(int(n) for fn in os.listdir(D) if fn.endswith(".kicad_sch")
              for n in re.findall(r'\(reference "#PWR0*(\d+)"\)', open(os.path.join(D, fn), encoding="utf-8").read()))
YC, XH, XT, XC, XR = 246.38, 441.96, 452.12, 464.82, 487.68          # CHASSIS rail; H2, TP2, CY stack, RY stack
def fields(d, extra=()):
    """Y_TASK 3.6 fields MPN / Alt_MPN / Note, and the same MPNs in the project's BOM columns Product Name / Replacement"""
    return [("Description P/N", d["pn"]), ("Product Name", d["mpn"]), ("Replacement", d["alt"]), ("MPN", d["mpn"]),
            ("Alt_MPN", d["alt"]), ("Note", d["note"])] + list(extra)
p.symbol("Mechanical:MountingHole_Pad", XH, YC - 2.54, 0, [(ROOT, "H2")], "H_CHS",
         "Power_My:MountingHole_3.2mm_M3_Slot_CHS", pins=("1",), in_bom=False,
         ref_xy=(XH + 2.54, YC - 5.08), val_xy=(XH + 2.54, YC - 3.175), justify="left")
p.symbol("Connector:TestPoint", XT, YC, 0, [(ROOT, "TP2")], "TP_CHS", "TestPoint:TestPoint_Pad_D1.5mm", pins=("1",),
         in_bom=False, ref_xy=(XT + 1.27, YC - 5.08), val_xy=(XT + 1.27, YC - 3.175), justify="left")
for ref, y in (("CY1", YC + 2.54), ("CY2", YC + 7.62)):
    p.symbol("Device:C_Small", XC, y, 0, [(ROOT, ref)], CY["value"], CY["fp"], fields(CY),
             ref_xy=(XC - 2.54, y - 0.635), val_xy=(XC - 2.54, y + 1.905), justify="right")
p.symbol("Device:Fuse_Small", XC, YC + 12.7, 90, [(ROOT, "FY1")], FY["value"], FY["fp"],
         fields(FY, [("Variant", FY["variant"])]), ref_xy=(XC - 4.445, YC + 11.43), val_xy=(XC - 8.89, YC + 13.97),
         fang=90)
for ref, y in (("RY1", YC + 2.54), ("RY2", YC + 7.62)):
    p.symbol("Device:R_Small", XR, y, 0, [(ROOT, ref)], RY["value"], RY["fp"], fields(RY),
             ref_xy=(XR + 2.54, y - 0.635), val_xy=(XR + 2.54, y + 1.905), justify="left")
for x, y in ((XC, YC + 15.24), (XR, YC + 15.24)):
    p.symbol("power:GND", x, y, 0, [(ROOT, f"#PWR{pwr:03d}")], "GND", "", pins=("1",), power=True,
             ref_xy=(x, y + 6.35), val_xy=(x, y + 3.81)); pwr += 1
p.wire(XR, YC + 10.16, XR, YC + 15.24)
XG = XR + 10.16                                                          # TP3 on its own GND symbol
p.symbol("Connector:TestPoint", XG, YC + 15.24, 0, [(ROOT, "TP3")], "TP_GND", "TestPoint:TestPoint_Pad_D1.5mm",
         pins=("1",), in_bom=False, ref_xy=(XG + 1.27, YC + 10.16), val_xy=(XG + 1.27, YC + 12.065), justify="left")
p.symbol("power:GND", XG, YC + 15.24, 0, [(ROOT, f"#PWR{pwr:03d}")], "GND", "", pins=("1",), power=True,
         ref_xy=(XG, YC + 21.59), val_xy=(XG, YC + 19.05)); pwr += 1
p.wire(XH, YC, XT, YC); p.wire(XT, YC, XC, YC); p.wire(XC, YC, XR, YC)
p.label("CHASSIS", XT + 1.27, YC)
for x, y, name, n in ((XC, YC + 5.08, "CY_MID", 2), (XC, YC + 10.16, "Y_F", 2), (XR, YC + 5.08, "RY_MID", 5)):
    p.wire(x, y, x + 2.54*n, y); p.label(name, x + 2.54*(n - 2) + 1.27, y)
p.new.append(f'\t(rectangle\n\t\t(start 431.8 236.22)\n\t\t(end 576.58 279.4)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type dash)\n'
             f'\t\t)\n\t\t(fill\n\t\t\t(type none)\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n')
def text(t, x, y, size, bold=False):
    b = "\t\t\t\t(thickness 0.4)\n\t\t\t\t(bold yes)\n" if bold else ""
    p.new.append(f'\t(text "{t}"\n\t\t(exclude_from_sim no)\n\t\t(at {f(x)} {f(y)} 0)\n\t\t(effects\n\t\t\t(font\n'
                 f'\t\t\t\t(size {size} {size})\n{b}\t\t\t)\n\t\t\t(justify left top)\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n')
text("Y-цепь корпуса", 431.8, 232.41, 2.5, True)
text("Минус ЗПТ - радиатор (корпус), docs/Y_TASK.md:\\n"
     "возврат синфазного тока коротким путём, потенциал корпуса\\n"
     "без связи по постоянному току, путь ESD.\\n"
     "Одна цепь от минуса: вторую цепь от +DC не ставить.\\n"
     "H2 - винт в радиатор, кольцо CHASSIS (шайба зубчатая\\n"
     "или пружинная); H1, H3, H4 - без меди под шайбой.\\n"
     "CY1, CY2: 250 V, soft termination - не заменять на 100 V.\\n"
     "RY1, RY2 - мимо FY1: при сгоревшем FY1 корпус\\n"
     "остаётся привязан к минусу.\\n"
     "FY1: стенд - 0R 1206, серия - предохранитель\\n"
     "2 A >= 125 V DC (2410).", 510.54, 240.03, 1.27)
p.save()

def uuid_of(s, ref):
    i = s.find(f'(property "Reference" "{ref}"'); a = s.rfind("\n\t(symbol\n", 0, i)
    return re.search(r'\n\t\t\(uuid "([^"]+)"\)', s[a:i]).group(1)
out = {r: "/" + uuid_of(p.s, r) for r in ("H2", "CY1", "CY2", "FY1", "RY1", "RY2", "TP2", "TP3")}
json.dump(out, open(os.path.join(sys.argv[2], "data", "sch_j_uuids.json"), "w"), indent=1)

# ---------------------------------------------------------------- netclass Y_CHASSIS and clearances (Y_TASK 4.5)
pro = os.path.join(D, "Power.kicad_pro"); J = json.load(open(pro, encoding="utf-8")); ns = J["net_settings"]
if not any(c["name"] == "Y_CHASSIS" for c in ns["classes"]):
    c = dict(next(c for c in ns["classes"] if c["name"] == "Default"))
    c.update(name="Y_CHASSIS", clearance=0.5, track_width=1.0, via_diameter=0.7, via_drill=0.4, priority=0)
    ns["classes"].append(c)
    ns["netclass_patterns"] = (ns.get("netclass_patterns") or []) + \
        [{"netclass": "Y_CHASSIS", "pattern": n} for n in ("/CHASSIS", "/CY_MID", "/Y_F")]
bom = J["schematic"]["bom_settings"]["fields_ordered"]                   # Y_TASK 3.5: the Variant / Note columns in the BOM
for name in ("Variant", "Note"):
    if not any(c["name"] == name for c in bom):
        bom.insert(next(i for i, c in enumerate(bom) if c["name"] == "Description P/N") + 1,
                   {"group_by": False, "label": name, "name": name, "show": True})
open(pro, "w", encoding="utf-8").write(json.dumps(J, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
PHASE = "B.NetName == '/Driver_*/SW' || B.NetName == '/Current_Sensor_*/Phase_*'"
open(os.path.join(D, "Power.kicad_dru"), "w", encoding="utf-8").write(
    '(version 1)\n'
    '# Y circuit, docs/Y_TASK.md 4.5 (the CHASSIS 2 mm rule of H5 is gone with H5)\n'
    '(rule "Y_CHASSIS 0.5 mm"\n'
    '\t(condition "A.NetClass == \'Y_CHASSIS\'")\n'
    '\t(constraint clearance (min 0.5mm)))\n'
    '(rule "Y_CHASSIS 0.8 mm to VDC and phase nodes"\n'
    f'\t(condition "A.NetClass == \'Y_CHASSIS\' && (B.NetName == \'VDC\' || {PHASE})")\n'
    '\t(constraint clearance (min 0.8mm)))\n'
    '(rule "CHASSIS, CY_MID 2 mm to phase nodes"\n'
    f'\t(condition "(A.NetName == \'/CHASSIS\' || A.NetName == \'/CY_MID\') && ({PHASE})")\n'
    '\t(constraint clearance (min 2.0mm)))\n')
print("schematic: H5 / C135 / C136 out; Y block CY1 CY2 FY1 RY1 RY2 TP2 TP3, H2 = H_CHS on CHASSIS")
