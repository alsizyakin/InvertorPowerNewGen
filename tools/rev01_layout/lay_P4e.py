"""03 E6, owner 2026-10-19 ("1 делаем"): dead-end node copper to GND. Usage: lay_P4e.py board.kicad_pcb
F21 Two pieces of node copper carry no current (cflow.py: without them +0.5 % / +0.1 % copper resistance) but sit at
    the board edge, under the screw heads and next to the connectors:
    - phase A, right of passage A below the slot (x > 163.5, y 98.25-104.25), F.Cu and B.Cu, 0.6 mm from J7.1/J7.2;
    - phase C, the pocket below the slot (x < 121.25, y 97.5-104.25), In2 and B.Cu, 0.26 mm from J6.1/J6.2 (VDC to
      the connection board).
    The node zones lose these pieces; GND zones take their place (same 0.6 mm clearance as the node zones), tied to
    In1 / In3 / In4 by GND vias: a row between the node and the edge in phase A, two vias in the pocket of phase C
    (the only free spots there). The full E6 (node >= 1.5 mm off every outline) is not done: it cuts passage C."""
import sys, os, re, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.dont_write_bytecode = True
import pcbedit, geom
fn = sys.argv[1]
s = open(fn, encoding="utf-8").read()

def fmt(v):
    t = f"{v:.4f}".rstrip("0").rstrip("."); return t if t not in ("-0", "") else "0"

def set_outline(s, net, layers_line, old, new):
    """Replace the outline of the zone of `net` whose layer line is `layers_line`, checking it was `old`."""
    hits = 0
    for a, b in list(geom._blocks(s, "zone")):
        z = s[a:b]
        if f'(net "{net}")' not in z or layers_line not in z: continue
        m = re.search(r'\(polygon\n\t\t\t\(pts\n(.*?)\n\t\t\t\)\n\t\t\)', z, re.S)
        pts = [(float(x), float(y)) for x, y in re.findall(r'\(xy ([\d.\-]+) ([\d.\-]+)\)', m.group(1))]
        if [(round(x, 3), round(y, 3)) for x, y in pts] != [(round(x, 3), round(y, 3)) for x, y in old]: continue
        xy = " ".join(f"(xy {fmt(x)} {fmt(y)})" for x, y in new)
        z2 = z[:m.start(1)] + "\t\t\t\t" + xy + z[m.end(1):]
        z2 = re.sub(r'\n\t\t\(filled_polygon\n.*?\n\t\t\)(?=\n)', "", z2, flags=re.S)     # refilled by kicad-cli
        s = s[:a] + z2 + s[b:]; hits += 1
        break
    assert hits == 1, (net, layers_line)
    return s

def zone_text(net, layer, prio, pts):
    xy = " ".join(f"(xy {fmt(x)} {fmt(y)})" for x, y in pts)
    return (f'\t(zone\n\t\t(net "{net}")\n\t\t(layer "{layer}")\n\t\t(uuid "{uuid.uuid4()}")\n\t\t(hatch none 0.5)\n'
            f'\t\t(priority {prio})\n\t\t(connect_pads yes\n\t\t\t(clearance 0.6)\n\t\t)\n\t\t(min_thickness 0.25)\n'
            f'\t\t(fill yes\n\t\t\t(thermal_gap 0.5)\n\t\t\t(thermal_bridge_width 0.5)\n\t\t\t(smoothing fillet)\n\t\t\t(radius 1)\n'
            f'\t\t\t(island_removal_mode 0)\n\t\t)\n\t\t(polygon\n\t\t\t(pts\n\t\t\t\t{xy}\n\t\t\t)\n\t\t)\n\t)\n')

# ---------------------------------------------------------------- phase A corner
NA = "/Current_Sensor_1/Phase_IN"
A_OLD_TOP = {"F.Cu": 71.25, "B.Cu": 74.25, "In1In2": 74.25}
def a_outline(top, corner):
    head = [(162.5, 88.5), (163.25, 89.25), (165.25, 89.25), (165.25, 94.0), (165.25, 98.25)]
    tail = [(157.25, 104.25), (157.25, 100.75), (157.25, 94.0), (157.0, 94.0), (155.25, 92.25), (155.25, top), (162.5, top)]
    mid = [(169.0, 98.25), (169.0, 104.25), (163.75, 104.25)] if corner else [(163.5, 98.25), (163.5, 104.25)]
    return head + mid + tail
for line, top in (('(layer "F.Cu")', 71.25), ('(layer "B.Cu")', 74.25), ('(layers "In1.Cu" "In2.Cu")', 74.25)):
    s = set_outline(s, NA, line, a_outline(top, True), a_outline(top, False))
# ---------------------------------------------------------------- phase C pocket
NC = "/Current_Sensor_3/Phase_IN"
C_OLD = [(128.25, 104.25), (121.25, 104.25), (116.5, 104.25), (116.5, 97.5), (121.25, 97.5), (121.25, 74.25), (128.25, 74.25)]
C_NEW = [(128.25, 104.25), (121.25, 104.25), (121.25, 74.25), (128.25, 74.25)]
for line in ('(layer "In2.Cu")', '(layer "B.Cu")'):
    s = set_outline(s, NC, line, C_OLD, C_NEW)
# ---------------------------------------------------------------- GND in their place
new_z = (zone_text("GND", "F.Cu", 30, [(163.5, 98.25), (169.25, 98.25), (169.25, 104.25), (163.5, 104.25)])
         + zone_text("GND", "B.Cu", 31, [(163.5, 98.25), (169.25, 98.25), (169.25, 104.25), (163.5, 104.25)])
         + zone_text("GND", "In2.Cu", 32, [(116.5, 97.5), (121.25, 97.5), (121.25, 104.25), (116.5, 104.25)])
         + zone_text("GND", "B.Cu", 33, [(116.5, 97.5), (121.25, 97.5), (121.25, 104.25), (116.5, 104.25)]))
k = s.find("\n\t(zone\n") + 1
s = s[:k] + new_z + s[k:]
open(fn, "w", encoding="utf-8").write(s)
B = pcbedit.Board(fn)
VIAS = [(164.1, 99.0), (164.1, 100.0), (164.1, 101.0), (164.1, 102.0), (164.1, 103.0),      # row node | edge, phase A
        (165.6, 99.5), (167.1, 99.5), (166.35, 101.75),
        (120.4, 98.6), (116.9, 103.1)]                                                      # pocket, phase C
for x, y in VIAS: B.add_via((x, y), "GND", free=True)
B.save()
print(f"F21: dead-end node copper of phases A and C to GND (4 zones), {len(VIAS)} GND vias")
