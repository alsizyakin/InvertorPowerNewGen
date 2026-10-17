"""+4 mm board: put the strip plan (strip_plan.py json) on the board.
- snubbers C112-C117 (0805) and R100-R105 (-> 0612): chain C = R end to end, middle joined by a 1.2 mm copper bridge;
- new 1206 C125/C126, C129/C130, C133/C134 (copies of C124/C128/C132, linked to the new symbols, sch_e_uuids.json),
  pad 2 (GND) with two vias 0.6/0.3 at the pad;
- rev0 0603 C90, C92...C96: two per phase, pad 2 (GND) with one via; old GND stubs/vias of C92, C95, C96 removed;
- pads of all these parts get a local clearance of 0.5 mm (zones keep it: 05 P5).
Usage: lay_P4.py in.kicad_pcb out.kicad_pcb plan.json sch_e_uuids.json"""
import sys, os, json, math, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.dont_write_bytecode = True
import pcbedit, fplib, geom
fi, fo, pj, uj = sys.argv[1:5]
plan = json.load(open(pj)); uu = json.load(open(uj))
G = geom.Board(fi)
B = pcbedit.Board(fi)
SNUB = {"C": {"LS": ("C112", "R100"), "HS": ("C115", "R103")}, "B": {"LS": ("C113", "R101"), "HS": ("C116", "R104")},
        "A": {"LS": ("C114", "R102"), "HS": ("C117", "R105")}}
CER = {"C": ("C124", "C125", "C126"), "B": ("C128", "C129", "C130"), "A": ("C132", "C133", "C134")}
C06 = {"C": ("C94", "C92"), "B": ("C93", "C90"), "A": ("C95", "C96")}
R0612 = "Resistor_SMD:R_0612_1632Metric_Pad1.18x3.40mm_HandSolder"
U = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}
OFF = {"R0612": 0.8375, "C0805": 1.0375, "C1206": 1.5625, "C0603": 0.8625}

# old GND stubs and vias of the 0603s that move (C92, C95, C96; C90/C93/C94 were removed with theirs by stretch_zones)
old_v = []
for r in ("C92", "C95", "C96"):
    p2 = [p for p in G.fps[r].placed()[0] if p["net"] == "GND"][0]
    pr = (p2["x"]-p2["aw"]/2-0.05, p2["y"]-p2["ah"]/2-0.05, p2["x"]+p2["aw"]/2+0.05, p2["y"]+p2["ah"]/2+0.05)
    for sg in G.segs:
        if sg["net"] == "GND" and sg["layer"] == "F.Cu":
            for (ax, ay), (bx, by) in (((sg["x1"], sg["y1"]), (sg["x2"], sg["y2"])), ((sg["x2"], sg["y2"]), (sg["x1"], sg["y1"]))):
                if geom.d_pt_rect(ax, ay, pr) == 0: old_v.append((bx, by))
old_v += [(v["x"], v["y"]) for r in ("C95", "C96") for v in G.vias if v["net"] == "GND" and
          math.hypot(v["x"] - [p for p in G.fps[r].placed()[0] if p["net"] == "GND"][0]["x"], v["y"] - [p for p in G.fps[r].placed()[0] if p["net"] == "GND"][0]["y"]) < 1.6]
nv = B.del_vias(lambda v: v["net"] == "GND" and any(math.hypot(v["x"]-a, v["y"]-b) < 0.05 for a, b in old_v))
def touches(g, refs):
    for r in refs:
        p2 = [p for p in G.fps[r].placed()[0] if p["net"] == "GND"][0]
        pr = (p2["x"]-p2["aw"]/2-0.05, p2["y"]-p2["ah"]/2-0.05, p2["x"]+p2["aw"]/2+0.05, p2["y"]+p2["ah"]/2+0.05)
        if geom.d_pt_rect(g["x1"], g["y1"], pr) == 0 or geom.d_pt_rect(g["x2"], g["y2"], pr) == 0: return True
    return False
ns = B.del_segs(lambda g: g["net"] == "GND" and g["layer"] == "F.Cu" and touches(g, ("C92", "C95", "C96")))
print(f"old 0603 GND stubs/vias removed: {ns} / {nv}")

def pad_c(x, y, rot, off, sign):           # centre of pad at -u (sign -1) or +u (sign +1)
    ux, uy = U[rot]; return (x + sign*ux*off, y + sign*uy*off)

# the 0603s are not tied to a phase: refs follow x, in the order of their rev0 places
c06 = sorted([it for items in plan.values() for nm, it in items.items() if nm.startswith("C06")], key=lambda r: r["x"])
C06_BY_X = dict(zip(("C94", "C92", "C93", "C90", "C95", "C96"), c06))
for ph, items in plan.items():
    for typ in ("LS", "HS"):
        it = items.get(typ)
        if not it: print(ph, typ, "not placed"); continue
        cref, rref = SNUB[ph][typ]; d = it["rot"]
        B.move_fp(rref, it["x"], it["y"], 0)
        B.s = fplib.swap_geometry(B.s, rref, R0612)
        B.s = fplib.set_attr(B.s, rref, value="0.47", pn="Resistor SMD 0612 1.5W")
        # schematic: C pad 1 = terminal, pad 2 = middle; R pad 1 = middle, pad 2 = terminal -> both turned by 180
        B.move_fp(rref, it["x"], it["y"], (d + 180) % 360)
        B.move_fp(cref, it["cx"], it["cy"], (it["crot"] + 180) % 360)
        a, b = it["bridge"]
        n = math.hypot(b[0]-a[0], b[1]-a[1]); a = (a[0] + (b[0]-a[0])/n*0.2, a[1] + (b[1]-a[1])/n*0.2)   # keep the round end inside the R pad
        B.add_seg(a, b, 1.2, "F.Cu", f"Net-({cref}-Pad2)")
        # terminals 0.5 mm (P5), middle node 0.3 mm
        B.s = fplib.set_pad_clearance(B.s, cref, {"1": 0.5, "2": 0.3}); B.s = fplib.set_pad_clearance(B.s, rref, {"1": 0.3, "2": 0.5})
        print(f"{ph} {typ} ({it['shape']}): {cref} ({it['cx']}, {it['cy']}) rot {(it['crot'] + 180) % 360}, {rref} ({it['x']}, {it['y']}) rot {(d + 180) % 360}; "
              f"terminal to pins R {it['dR']} / C {it['dC']} mm")
    src, n1, n2 = CER[ph]
    for nm, ref in (("CER1", n1), ("CER2", n2)):
        it = items.get(nm)
        if not it: print(ph, nm, "not placed"); continue
        B.s = fplib.clone_fp(B.s, src, ref, uu[ref], pad_nets={"1": "VDC", "2": "GND"})
        B.move_fp(ref, it["x"], it["y"], it["rot"])
        p2 = pad_c(it["x"], it["y"], it["rot"], OFF["C1206"], +1)
        for v in it["vias"]:
            B.add_via(v, "GND"); B.add_seg(p2, v, 0.6, "F.Cu", "GND")
        B.s = fplib.set_pad_clearance(B.s, ref, 0.5)
        print(f"{ph} {ref}: ({it['x']}, {it['y']}) rot {it['rot']}, GND vias {it['vias']}")
    for ref in C06[ph]:
        it = C06_BY_X.get(ref)
        if not it: print(ph, ref, "not placed"); continue
        B.move_fp(ref, it["x"], it["y"], it["rot"])
        p2 = pad_c(it["x"], it["y"], it["rot"], OFF["C0603"], +1)
        for v in it["vias"]:
            B.add_via(v, "GND"); B.add_seg(p2, v, 0.4, "F.Cu", "GND")
        B.s = fplib.set_pad_clearance(B.s, ref, 0.5)
        print(f"{ph} {ref}: ({it['x']}, {it['y']}) rot {it['rot']}, GND via {it['vias']}")
B.save(fo)
