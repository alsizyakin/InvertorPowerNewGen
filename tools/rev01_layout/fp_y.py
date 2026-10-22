"""Footprints of the Y circuit (docs/Y_TASK.md) into the project library Lib/Power_My.pretty. Usage: fp_y.py project_dir
- MountingHole_3.2mm_M3_Slot_CHS: the CHASSIS contact of the screw H2 in the ADAPTO side U-slot (slot 3.5 mm wide, open
  to +x, the board edge 1.68 mm right of the hole centre). The slot is open, so the copper ring is a horseshoe:
  r 2.05-3.25 (Y_TASK 4.2: outer diameter >= M3 head 5.5 + 1 mm), the legs along the slot to x 1.25 (edge 0.43 mm away;
  the top leg also clears the r 6 board corner). Custom pads "1" on F.Cu and B.Cu with open mask, nine via pads
  drill 0.4 / 0.7 mm in the ring (Y_TASK: >= 8 x 0.4 mm). The inner-layer rings are board zones (lay_Y1.py).
  The NPTH 3.2 mm at the slot end stays (as in the stock hole), without the 2 mm clearance of H1-H4.
- Fuse_2410_1206: a 2410 fuse land (Littelfuse NANO2 453) with 1206 pads inside the same pads (Y_TASK 2.5: the place
  takes a 125 V DC 2410 fuse or a 0 Ohm / damping 1206)."""
import sys, os, math, uuid
D = sys.argv[1]
OUT = os.path.join(D, "Lib", "Power_My.pretty"); os.makedirs(OUT, exist_ok=True)
def fmt(v):
    s = f"{v:.6f}".rstrip("0").rstrip("."); return s if s not in ("-0", "") else "0"
def U(): return str(uuid.uuid4())

def head(name, descr, tags, ref_y, val_y, attr):
    return (f'(footprint "{name}"\n\t(version 20260206)\n\t(generator "fp_y.py")\n\t(layer "F.Cu")\n'
            f'\t(descr "{descr}")\n\t(tags "{tags}")\n'
            f'\t(property "Reference" "REF**"\n\t\t(at 0 {fmt(ref_y)} 0)\n\t\t(layer "F.SilkS")\n\t\t(uuid "{U()}")\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)\n'
            f'\t(property "Value" "{name}"\n\t\t(at 0 {fmt(val_y)} 0)\n\t\t(layer "F.Fab")\n\t\t(uuid "{U()}")\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)\n'
            f'\t(attr {attr})\n\t(duplicate_pad_numbers_are_jumpers no)\n')
def circle(r, layer, w):
    return (f'\t(fp_circle\n\t\t(center 0 0)\n\t\t(end {fmt(r)} 0)\n\t\t(stroke\n\t\t\t(width {fmt(w)})\n\t\t\t(type solid)\n'
            f'\t\t)\n\t\t(fill no)\n\t\t(layer "{layer}")\n\t\t(uuid "{U()}")\n\t)\n')
def rect(x0, y0, x1, y1, layer, w):
    return (f'\t(fp_rect\n\t\t(start {fmt(x0)} {fmt(y0)})\n\t\t(end {fmt(x1)} {fmt(y1)})\n\t\t(stroke\n\t\t\t(width {fmt(w)})\n'
            f'\t\t\t(type solid)\n\t\t)\n\t\t(fill no)\n\t\t(layer "{layer}")\n\t\t(uuid "{U()}")\n\t)\n')
def line(x0, y0, x1, y1, layer, w):
    return (f'\t(fp_line\n\t\t(start {fmt(x0)} {fmt(y0)})\n\t\t(end {fmt(x1)} {fmt(y1)})\n\t\t(stroke\n\t\t\t(width {fmt(w)})\n'
            f'\t\t\t(type solid)\n\t\t)\n\t\t(layer "{layer}")\n\t\t(uuid "{U()}")\n\t)\n')
def fab_ref():
    return (f'\t(fp_text user "${{REFERENCE}}"\n\t\t(at 0 0 0)\n\t\t(layer "F.Fab")\n\t\t(uuid "{U()}")\n'
            f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 0.6 0.6)\n\t\t\t\t(thickness 0.1)\n\t\t\t)\n\t\t)\n\t)\n')
def rpad(num, x, y, w, h, layers="\"F.Cu\" \"F.Mask\" \"F.Paste\""):
    return (f'\t(pad "{num}" smd roundrect\n\t\t(at {fmt(x)} {fmt(y)})\n\t\t(size {fmt(w)} {fmt(h)})\n\t\t(layers {layers})\n'
            f'\t\t(roundrect_rratio 0.15)\n\t\t(uuid "{U()}")\n\t)\n')

# ---------------------------------------------------------------- the horseshoe
RI, RO, XL = 2.05, 3.25, 1.25                    # inner / outer radius, leg end (slot half-width 1.75 + 0.3)
RV, NV = 0.5*(RI + RO), 7                         # via circle, vias on the arc
def horseshoe(ax):
    """polygon relative to the pad anchor (ax, 0)"""
    a_end = math.degrees(math.acos(XL/RO))        # outer circle meets x = XL
    pts = [(XL, RI), (XL, math.sqrt(RO*RO - XL*XL))]
    n = 48
    for k in range(1, n):                         # outer arc, through 180 deg, from +a_end to 360 - a_end
        t = math.radians(a_end + (360 - 2*a_end)*k/n)
        pts.append((RO*math.cos(t), RO*math.sin(t)))
    pts += [(XL, -math.sqrt(RO*RO - XL*XL)), (XL, -RI), (0, -RI)]
    for k in range(1, 24):                        # inner arc r RI from 270 back to 90 deg through 180
        t = math.radians(270 - 180*k/24)
        pts.append((RI*math.cos(t), RI*math.sin(t)))
    pts.append((0, RI))
    return [(x - ax, y) for x, y in pts]
def cpad(layer):
    ax = -RV
    xy = " ".join(f"(xy {fmt(x)} {fmt(y)})" for x, y in horseshoe(ax))
    return (f'\t(pad "1" smd custom\n\t\t(at {fmt(ax)} 0)\n\t\t(size 1 1)\n\t\t(layers "{layer}.Cu" "{layer}.Mask")\n'
            f'\t\t(zone_connect 2)\n\t\t(options\n\t\t\t(clearance outline)\n\t\t\t(anchor circle)\n\t\t)\n'
            f'\t\t(primitives\n\t\t\t(gr_poly\n\t\t\t\t(pts\n\t\t\t\t\t{xy}\n\t\t\t\t)\n\t\t\t\t(width 0)\n'
            f'\t\t\t\t(fill yes)\n\t\t\t)\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n')
VIAS = [(RV*math.cos(math.radians(100 + 160*k/(NV - 1))), RV*math.sin(math.radians(100 + 160*k/(NV - 1)))) for k in range(NV)]
VIAS += [(0.85, RV), (0.85, -RV)]
t = head("MountingHole_3.2mm_M3_Slot_CHS",
         "M3 screw in a 3.5 mm side U-slot open to +x, CHASSIS contact: horseshoe ring r 2.0-3.25 on F.Cu / B.Cu, open mask, "
         "9 via pads 0.4 mm (docs/Y_TASK.md 4.2)", "mountinghole M3 slot chassis", -4.15, 4.15,
         "exclude_from_pos_files exclude_from_bom")
t += circle(3.2, "Cmts.User", 0.15) + circle(3.45, "F.CrtYd", 0.05) + circle(3.45, "B.CrtYd", 0.05) + fab_ref()
t += (f'\t(pad "" np_thru_hole circle\n\t\t(at 0 0)\n\t\t(size 3.2 3.2)\n\t\t(drill 3.2)\n\t\t(layers "*.Cu" "*.Mask")\n'
      f'\t\t(uuid "{U()}")\n\t)\n')
t += cpad("F") + cpad("B")
for x, y in VIAS:
    t += (f'\t(pad "1" thru_hole circle\n\t\t(at {fmt(x)} {fmt(y)})\n\t\t(size 0.7 0.7)\n\t\t(drill 0.4)\n'
          f'\t\t(layers "*.Cu" "*.Mask")\n\t\t(remove_unused_layers no)\n\t\t(zone_connect 2)\n\t\t(uuid "{U()}")\n\t)\n')
t += '\t(embedded_fonts no)\n)\n'
open(os.path.join(OUT, "MountingHole_3.2mm_M3_Slot_CHS.kicad_mod"), "w", encoding="utf-8").write(t)

# ---------------------------------------------------------------- 2410 fuse with 1206 pads
F_PITCH, F_W, F_H = 4.91, 1.96, 3.15                # 2410 land (Littelfuse 451/453 datasheet p. 4): pitch, pad x, pad y
B_PITCH, B_W, B_H = 2.8, 1.25, 1.75               # 1206 (Fuse_1206_3216Metric)
if F_PITCH:
    xo = F_PITCH/2 + F_W/2; yo = max(F_H, B_H)/2
    t = head("Fuse_2410_1206",
             "Fuse 2410 (6.1 x 2.69 mm, Littelfuse NANO2 453) with 1206 pads inside its pads: a 125 V DC fuse or a 0 Ohm / "
             "damping 1206 (docs/Y_TASK.md 2.5)", "fuse 2410 1206", -yo - 1.2, yo + 1.2, "smd")
    t += rect(-3.05, -1.345, 3.05, 1.345, "F.Fab", 0.1) + rect(-xo - 0.25, -yo - 0.25, xo + 0.25, yo + 0.25, "F.CrtYd", 0.05)
    xs = F_PITCH/2 - F_W/2 - 0.2
    if xs > 0.3:
        t += line(-xs, -yo + 0.1, xs, -yo + 0.1, "F.SilkS", 0.12) + line(-xs, yo - 0.1, xs, yo - 0.1, "F.SilkS", 0.12)
    t += fab_ref()
    for s in (-1, 1):
        n = "1" if s < 0 else "2"
        t += rpad(n, s*F_PITCH/2, 0, F_W, F_H) + rpad(n, s*B_PITCH/2, 0, B_W, B_H)
    t += '\t(embedded_fonts no)\n)\n'
    open(os.path.join(OUT, "Fuse_2410_1206.kicad_mod"), "w", encoding="utf-8").write(t)
T = os.path.join(D, "fp-lib-table"); t = open(T, encoding="utf-8").read()
if '(name "Power_My")' not in t:
    t = t.rstrip().rstrip(")") + '  (lib (name "Power_My")(type "KiCad")(uri "${KIPRJMOD}/Lib/Power_My.pretty")(options "")(descr "Y circuit"))\n)\n'
    open(T, "w", encoding="utf-8").write(t)
print("footprints in", OUT)
