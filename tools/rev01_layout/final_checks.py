"""§9.2 checks by script: (a) In3 in the key block, (b) per phase vias (Р8), ceramics, gate net lengths,
(c) SW membership, (d) DNP flags of the new parts. Usage: final_checks.py board tools"""
import sys, math, re
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
import geom
fn = sys.argv[1]; G = geom.Board(fn); txt = open(fn, encoding="utf-8").read()
L = lambda s: math.hypot(s["x2"]-s["x1"], s["y2"]-s["y1"])
print("(a) In3 segments in the block x116.2-169.2 y72-91.5:",
      sum(1 for s in G.segs if s["layer"] == "In3.Cu" and max(s["x1"], s["x2"]) > 116.2 and min(s["x1"], s["x2"]) < 169.2 and min(s["y1"], s["y2"]) < 91.5 and max(s["y1"], s["y2"]) > 72))
STRIP = {"C": (116.2, 121.2, "Q8", "Q4"), "B": (134.2, 138.2, "Q9", "Q5"), "A": (151.2, 155.2, "Q11", "Q6")}
NODE = {"C": (121.2, 128.2, "/Current_Sensor_3/Phase_IN"), "B": (138.2, 145.2, "/Current_Sensor_2/Phase_IN"), "A": (155.2, 162.5, "/Current_Sensor_1/Phase_IN")}
DRV = {"C": "3", "B": "2", "A": "1"}
rect = lambda p: (p["x"]-p["aw"]/2, p["y"]-p["ah"]/2, p["x"]+p["aw"]/2, p["y"]+p["ah"]/2)
print("(b) phase | strip GND vias | of them <=2.5 mm from LS S | node vias in node column y72-93.5 | LO_DRV+LO mm | HO_DRV+HO mm (SW mm)")
for ph in "CBA":
    x0, x1, q1, q2 = STRIP[ph]
    sv = [v for v in G.vias if v["net"] == "GND" and x0 - 0.2 < v["x"] < x1 and 72 < v["y"] < 93.5]
    spads = [p for q in (q1, q2) for p in G.fps[q].placed()[0] if p["net"] == "GND" and not p["tht"]]
    nearS = [v for v in sv if min(geom.d_pt_rect(v["x"], v["y"], rect(p)) for p in spads) <= 2.5]
    n0, n1, nn = NODE[ph]
    nv = [v for v in G.vias if v["net"] == nn and n0 <= v["x"] <= n1 and 72 <= v["y"] <= 93.5]
    k = DRV[ph]
    ln = lambda net: sum(L(s) for s in G.segs if s["net"] == net)
    print(f"   {ph} | {len(sv)} | {len(nearS)} | {len(nv)} | {ln(f'/Driver_{k}/LO_DRV'):.1f}+{ln(f'/Driver_{k}/LO'):.1f}"
          f" | {ln(f'/Driver_{k}/HO_DRV'):.1f}+{ln(f'/Driver_{k}/HO'):.1f} ({ln(f'/Driver_{k}/SW'):.1f})")
print("(b) ceramics VDC-GND on F.Cu in/near the block:")
for r, f in sorted(G.fps.items()):
    nets = {p["net"] for p in f.placed()[0]}
    if nets == {"VDC", "GND"} and 114 < f.x < 170 and 70 < f.y < 93 and f.layer == "F.Cu":
        print(f"   {r} ({f.x},{f.y}) {f.fpname.split(':')[-1] if hasattr(f, 'fpname') else ''}")
print("(c) members of the SW nets:")
for k in "321":
    m = sorted(f"{r}.{p['name']}" for r, f in G.fps.items() for p in f.placed()[0] if p["net"] == f"/Driver_{k}/SW")
    print(f"   /Driver_{k}/SW: {m}")
print("(d) DNP attribute on the new parts:")
def dnp(ref):
    i = txt.find(f'(property "Reference" "{ref}"'); a = txt.rfind("\n\t(footprint ", 0, i); b = txt.find("\n\t(footprint ", i)
    blk = txt[a:b]; m = re.search(r'\(attr ([^)]*)\)', blk)
    return "dnp" in (m.group(1) if m else "") or "(dnp yes)" in blk
groups = {"C_gs": [f"C{n}" for n in range(100, 112)], "HI/LI C": [f"C{n}" for n in range(118, 124)],
          "HI/LI R": [f"R{n}" for n in range(118, 124)], "snubber": [f"C{n}" for n in range(112, 118)] + [f"R{n}" for n in range(100, 106)],
          "ceramics": ["C124", "C128", "C132"]}
for g, refs in groups.items():
    print(f"   {g}: " + " ".join(f"{r}{'(DNP)' if dnp(r) else ''}" for r in refs if f'"Reference" "{r}"' in txt))
