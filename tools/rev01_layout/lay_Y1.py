"""rev0.1-adapto, Y circuit (docs/Y_TASK.md), board part; the schematic part is sch_rev01_j.py, the footprints come from
fp_y.py (Lib/Power_My.pretty). Usage: lay_Y1.py board tools_dir
- H5 / C135 / C136 (parked off the board by lay_AD1.py) are deleted
- H2 (right U-slot, 8.4 mm from the minus bushing J5) = H_CHS: footprint MountingHole_3.2mm_M3_Slot_CHS (horseshoe on
  F.Cu / B.Cu, open mask, 9 vias 0.4 mm), CHASSIS rings on In1-In4 as zones (priority 50)
- the chain on B.Cu (the F side at H2 is J5 with its cable lug and the body of C22):
    CY1, CY2 1812 upright in the strip between the C22 pads and the right edge, long side along the edge (Y_TASK 4.4);
    the CHASSIS pad of CY1 lies on the ring, the CY_MID pads touch end to end; FY1 (2410 + 1206) across under the
    C22 VDC pad, its GND pad goes 1.5 mm wide to three GND vias into the In1 / In3 / In4 planes (the minus of the DC
    link; B.Cu here is the VDC pour); C82 (MLCC of C22) moves left of C81 to free the strip
    RY1, RY2 0805 across under J5: ring - RY1 - RY2 - straight up into the J5 pad (minus bushing), not through FY1
    TP2 (CHS) on the ring - RY1 track, TP3 (GND) at the GND pad of RY2
- silkscreen: CHS and an arrow at H2, ISO at H1 / H3 / H4 (Y_TASK 4.6)"""
import sys, os, re, json, math, uuid
T = sys.argv[2]; sys.path.insert(0, T); sys.dont_write_bytecode = True
import pcbedit, fplib, geom
fn = sys.argv[1]; PRJ = os.path.dirname(os.path.abspath(fn))
fplib.PROJECT_LIBS["Power_My"] = os.path.join(PRJ, "Lib", "Power_My.pretty")
UID = json.load(open(os.path.join(T, "data", "sch_j_uuids.json")))
SCH_TXT = open(os.path.join(PRJ, "Power.kicad_sch"), encoding="utf-8").read()
def sch_fields(ref):
    """BOM fields of the symbol (sch_rev01_j.py) for the footprint"""
    i = SCH_TXT.find(f'(property "Reference" "{ref}"'); a = SCH_TXT.rfind("\n\t(symbol\n", 0, i); b = SCH_TXT.find("\n\t)\n", i)
    return [(k, v) for k, v in re.findall(r'\(property "([^"]+)" "([^"]*)"', SCH_TXT[a:b])
            if k in ("Description P/N", "Product Name", "Replacement", "MPN", "Alt_MPN", "Note", "Variant")]
H2 = (167.57, 48.79)
CHS, MID, YF, RMID, GND = "/CHASSIS", "/CY_MID", "/Y_F", "/RY_MID", "GND"
# ---------------------------------------------------------------- placement (B.Cu); x, y, rotation
PLACE = {"CY1": (167.3, 54.25, 270), "CY2": (167.3, 58.85, 270),
         "RY1": (162.85, 51.3, 180), "RY2": (159.7, 51.3, 180),
         "TP2": (164.7, 50.7, 0), "TP3": (157.3, 51.3, 0)}
FY1_AT = (165.42, 62.75, 0)                 # GND pad 0.5 mm off the C78 VDC pad (hv.py)
NETS = {"CY1": {"1": CHS, "2": MID}, "CY2": {"1": MID, "2": YF}, "FY1": {"1": GND, "2": YF},
        "RY1": {"1": CHS, "2": RMID}, "RY2": {"1": RMID, "2": GND}, "TP2": {"1": CHS}, "TP3": {"1": GND}}
LIB = {"CY1": "Capacitor_SMD:C_1812_4532Metric", "CY2": "Capacitor_SMD:C_1812_4532Metric",
       "RY1": "Resistor_SMD:R_0805_2012Metric", "RY2": "Resistor_SMD:R_0805_2012Metric",
       "FY1": "Power_My:Fuse_2410_1206", "TP2": "TestPoint:TestPoint_Pad_D1.5mm", "TP3": "TestPoint:TestPoint_Pad_D1.5mm"}
VAL = {"CY1": "470n 250V X7R", "CY2": "470n 250V X7R", "RY1": "100k", "RY2": "100k", "FY1": "2A 125VDC",
       "TP2": "TP_CHS", "TP3": "TP_GND"}

s = open(fn, encoding="utf-8").read()
if '(property "Reference" "CY1"' in s:
    sys.exit("lay_Y1: already applied")
# ---------------------------------------------------------------- out: H5, C135, C136
for ref in ("H5", "C135", "C136"):
    a, b = pcbedit._fp_span(s, ref); s = s[:a - 1] + s[b + 1:]
open(fn, "w", encoding="utf-8").write(s)

# ---------------------------------------------------------------- H2 -> H_CHS
s = fplib.swap_geometry(s, "H2", "Power_My:MountingHole_3.2mm_M3_Slot_CHS")
a, b = pcbedit._fp_span(s, "H2"); blk = s[a:b]
blk = re.sub(r'\(path "[^"]+"\)', f'(path "{UID["H2"]}")', blk, count=1)
blk = re.sub(r'\(property "Value" "[^"]*"', '(property "Value" "H_CHS"', blk, count=1)
blk = blk.replace('(property "Description" "Mounting Hole without connection"', '(property "Description" ""', 1)
blk = blk.replace("\n\t\t(clearance 1)", "")
blk = re.sub(r'\(pins\)', '(pins "1")', blk, count=1)
blk = re.sub(r'(\(pad "1" [^\n]*\n(?:\t\t\t[^\n]*\n|\t\t\t\t[^\n]*\n|\t\t\t\t\t[^\n]*\n|\t\t\t\t\t\t[^\n]*\n)*?)(\t\t\t\(uuid)',
             lambda m: m.group(1) + f'\t\t\t(net "{CHS}")\n\t\t\t(pinfunction "1")\n\t\t\t(pintype "input")\n' + m.group(2), blk)
assert blk.count(f'(net "{CHS}")') == 11, blk.count(f'(net "{CHS}")')
s = s[:a] + blk + s[b:]

# ---------------------------------------------------------------- new footprints: clone C40 (F.Cu, root sheet), swap, flip
def prop(name, val):
    return (f'\t\t(property "{name}" "{val}"\n\t\t\t(at 0 0 0)\n\t\t\t(unlocked yes)\n\t\t\t(layer "F.Fab")\n\t\t\t(hide yes)\n'
            f'\t\t\t(uuid "{uuid.uuid4()}")\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1 1)\n\t\t\t\t\t(thickness 0.15)\n'
            f'\t\t\t\t)\n\t\t\t)\n\t\t)\n')
for ref in ("CY1", "CY2", "FY1", "RY1", "RY2", "TP2", "TP3"):
    s = fplib.clone_fp(s, "C40", ref, UID[ref], sheetname="/", value=VAL[ref])
    open(fn, "w", encoding="utf-8").write(s)
    B = pcbedit.Board(fn); B.move_fp(ref, 0, 0, 0); B.save()
    s = open(fn, encoding="utf-8").read()
    a, b = pcbedit._fp_span(s, ref); blk = s[a:b]
    for pn, net in NETS[ref].items():                      # nets by pad number before the swap (swap keeps them)
        blk = re.sub(r'(\(pad "' + pn + r'" (?:(?!\n\t\t\)).)*?\(net )"[^"]*"', r'\g<1>"' + net + '"', blk, count=1, flags=re.S)
    if ref.startswith("TP"):                               # one pad: drop the net of pad 2 of the clone
        blk = re.sub(r'(\(pad "2" (?:(?!\n\t\t\)).)*?)\n\t\t\t\(net "[^"]*"\)', r'\g<1>', blk, count=1, flags=re.S)
        blk = blk.replace("(attr smd)", "(attr smd exclude_from_bom)", 1)
        blk = blk.replace('(property ki_fp_filters "C_*")', '(property ki_fp_filters "Pin* Test*")', 1)
    elif ref.startswith("R"):
        blk = blk.replace('(property ki_fp_filters "C_*")', '(property ki_fp_filters "R_*")', 1)
    elif ref.startswith("F"):
        blk = blk.replace('(property ki_fp_filters "C_*")', '(property ki_fp_filters "*Fuse*")', 1)
    for name in ("Replacement", "Description P/N", "Product Name", "Function"):     # fields of the clone source C40
        blk = re.sub(r'\n\t\t\(property "' + re.escape(name) + r'" .*?\n\t\t\)', '', blk, count=1, flags=re.S)
    extra = "".join(prop(k, v) for k, v in sch_fields(ref))
    k = blk.find("\t\t(property ki_fp_filters")
    blk = blk[:k] + extra + blk[k:]
    blk = re.sub(r'\(pins "1" "2"\)', '(pins "1")' if ref.startswith("TP") else '(pins "1" "2")', blk, count=1)
    s = s[:a] + blk + s[b:]
    s = fplib.swap_geometry(s, ref, LIB[ref])
    open(fn, "w", encoding="utf-8").write(s)
    B = pcbedit.Board(fn); B.flip_fp(ref)
    B.move_fp(ref, *(FY1_AT if ref == "FY1" else PLACE[ref])); B.save()
    s = open(fn, encoding="utf-8").read()

# ---------------------------------------------------------------- C82 left of C81; tracks
B = pcbedit.Board(fn)
OLD = [((166.0, 55.9625), (165.094823, 55.9625)), ((165.094823, 55.9625), (163.75, 54.617677))]
n = B.del_segs(lambda g: g["layer"] == "B.Cu" and any({(round(g["x1"], 3), round(g["y1"], 3)), (round(g["x2"], 3), round(g["y2"], 3))}
                                                      == {(round(p[0], 3), round(p[1], 3)), (round(q[0], 3), round(q[1], 3))} for p, q in OLD))
assert n == 2, n
B.move_fp("C82", 159.0, 57.0, 90)
B.track([(159.0, 55.9625), (161.5, 55.9625)], 1.0, "B.Cu", GND)
G = geom.Board(fn)
def pad(ref, num):
    ps, _ = G.fps[ref].placed(); return next((p["x"], p["y"]) for p in ps if p["name"] == num)
# CHASSIS: ring -> TP2 -> RY1 (the CY1 pad 1 lies on the ring)
r150 = (H2[0] + 2.625*math.cos(math.radians(135)), H2[1] + 2.625*math.sin(math.radians(135)))
p1 = pad("RY1", "1")
B.track([r150, (r150[0] - (p1[1] - r150[1]), p1[1]), p1], 1.0, "B.Cu", CHS)
# CY_MID: the touching pads, 2 mm bridge; RY_MID
B.track([pad("CY1", "2"), pad("CY2", "1")], 2.0, "B.Cu", MID)
B.track([pad("RY1", "2"), pad("RY2", "1")], 1.0, "B.Cu", RMID)
# RY2 GND pad straight up into J5, TP3 next to it
q = pad("RY2", "2"); B.track([q, (q[0], 48.6)], 1.0, "B.Cu", GND)
B.track([pad("TP3", "1"), q], 1.0, "B.Cu", GND)
# Y_F: the FY1 pad 2 overlaps the CY2 pad 2, a 1.5 mm strap through both; GND: the FY1 pad 1 left 1.5 mm wide to three
# GND vias 0.8 / 0.4 between it and C11 (B.Cu here is the VDC pour, the minus of the DC link is In1 / In3 / In4)
c2 = pad("CY2", "2"); f2 = pad("FY1", "2"); f1 = pad("FY1", "1")
B.track([(c2[0] - 0.3, c2[1]), (c2[0] - 0.3, f2[1])], 1.5, "B.Cu", YF)
GV = [(161.0, f1[1] - 0.8), (161.0, f1[1]), (161.0, f1[1] + 0.8)]
B.track([f1, GV[1]], 1.5, "B.Cu", GND); B.track([GV[0], GV[2]], 1.0, "B.Cu", GND)
for v in GV: B.add_via(v, GND, 0.8, 0.4)
B.save()

# ---------------------------------------------------------------- CHASSIS rings on In1-In4 (zones), silkscreen
RI, RO, XL = 2.05, 3.25, 1.25                                            # as in fp_y.py
def horseshoe():
    a_end = math.degrees(math.acos(XL/RO)); pts = [(XL, RI), (XL, math.sqrt(RO*RO - XL*XL))]
    for k in range(1, 48):
        t = math.radians(a_end + (360 - 2*a_end)*k/48); pts.append((RO*math.cos(t), RO*math.sin(t)))
    pts += [(XL, -math.sqrt(RO*RO - XL*XL)), (XL, -RI), (0, -RI)]
    for k in range(1, 24):
        t = math.radians(270 - 180*k/24); pts.append((RI*math.cos(t), RI*math.sin(t)))
    return pts + [(0, RI)]
xy = " ".join(f"(xy {pcbedit.fmt(H2[0] + x)} {pcbedit.fmt(H2[1] + y)})" for x, y in horseshoe())
zone = (f'\t(zone\n\t\t(net "{CHS}")\n\t\t(layers "In1.Cu" "In2.Cu" "In3.Cu" "In4.Cu")\n\t\t(uuid "{uuid.uuid4()}")\n'
        f'\t\t(name "CHASSIS ring H2 (Y_TASK 4.2)")\n\t\t(hatch none 0.5)\n\t\t(priority 50)\n\t\t(connect_pads yes\n'
        f'\t\t\t(clearance 0.5)\n\t\t)\n\t\t(min_thickness 0.25)\n\t\t(fill yes\n\t\t\t(thermal_gap 0.5)\n'
        f'\t\t\t(thermal_bridge_width 0.5)\n\t\t\t(island_removal_mode 0)\n\t\t)\n'
        f'\t\t(polygon\n\t\t\t(pts\n\t\t\t\t{xy}\n\t\t\t)\n\t\t)\n\t)\n')
s = open(fn, encoding="utf-8").read()
k = s.find("\n\t(zone\n") + 1; s = s[:k] + zone + s[k:]
def text(t, x, y, layer="F.SilkS", size=0.8):
    mir = "\n\t\t\t(justify mirror)" if layer.startswith("B") else ""
    return (f'\t(gr_text "{t}"\n\t\t(at {x} {y} 0)\n\t\t(layer "{layer}")\n\t\t(uuid "{uuid.uuid4()}")\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t\t(thickness 0.15)\n\t\t\t)'
            f'{mir}\n\t\t)\n\t)\n')
def seg(x1, y1, x2, y2, layer="F.SilkS"):
    return (f'\t(gr_line\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n\t\t(stroke\n\t\t\t(width 0.15)\n\t\t\t(type solid)\n'
            f'\t\t)\n\t\t(layer "{layer}")\n\t\t(uuid "{uuid.uuid4()}")\n\t)\n')
SILK = [text("CHS", 166.2, 44.6), seg(167.85, 43.9, 167.85, 45.2), seg(167.5, 44.85, 167.85, 45.2), seg(168.2, 44.85, 167.85, 45.2),
        text("CHS", 166.2, 44.6, "B.SilkS"), text("GND", 155.3, 51.3, "B.SilkS"),
        text("ISO", 119.3, 44.6), text("ISO", 119.5, 130.0), text("ISO", 166.0, 130.0)]
g = "".join(SILK)
k = s.find("\n\t(gr_text ") + 1; s = s[:k] + g + s[k:]
# reference texts: inside the CY bodies, under FY1 and the RY pair; TP2 / TP3 / C82 hidden (CHS / GND marks instead)
def set_ref(s, ref, x, y, ang=0, hide=False):
    a, b = pcbedit._fp_span(s, ref); blk = s[a:b]
    at = re.search(r'\n\t\t\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)', blk)
    fx, fy, rot = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
    lx, ly = geom.rot_pt(x - fx, y - fy, -rot)
    blk = re.sub(r'(\(property "Reference" "[^"]+"\n\t\t\t)\(at [^)]*\)', lambda m: m.group(1) +
                 f'(at {pcbedit.fmt(lx)} {pcbedit.fmt(ly)} {pcbedit.fmt(ang)})', blk, count=1)
    if hide and not re.search(r'\(property "Reference" [^\n]*\n\t\t\t\(at [^)]*\)\n(\t\t\t\(unlocked yes\)\n)?\t\t\t\(layer "[^"]+"\)\n\t\t\t\(hide yes\)', blk):
        blk = re.sub(r'(\(property "Reference" [^\n]*\n\t\t\t\(at [^)]*\)\n(?:\t\t\t\(unlocked yes\)\n)?\t\t\t\(layer "[^"]+"\)\n)', r'\g<1>\t\t\t(hide yes)\n', blk, count=1)
    return s[:a] + blk + s[b:]
for ref, x, y, h in (("CY1", 167.3, 54.25, 0), ("CY2", 167.3, 58.85, 0), ("FY1", 163.0, 65.1, 0), ("RY1", 162.85, 52.75, 0),
                     ("RY2", 159.7, 52.75, 0), ("TP2", 164.7, 50.7, 1), ("TP3", 157.3, 51.3, 1), ("C82", 159.0, 57.0, 1)):
    s = set_ref(s, ref, x, y, 0, bool(h))
s = set_ref(s, "C81", 163.25, 57.0, 270)                 # was left of C81, now next to C82
open(fn, "w", encoding="utf-8").write(s)
print("lay_Y1: H2 = H_CHS, CY1 CY2 FY1 RY1 RY2 TP2 TP3 placed on B.Cu, C82 moved, CHASSIS rings In1-In4")
