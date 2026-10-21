"""rev0.1-ina-ref, step I2 (owner 2026-10-21: «раз улучшение дешевое, то давай поставим»). Usage: lay_I2.py board
I3 A GND via at each decoupling cap of U5 on B.Cu (C42, C45, C47, C48, C49, C50, C52, C53). Before, their GND pads
   reached the GND planes through the thermal spokes of the B.Cu pour and the via cluster in the middle under U5,
   1.9-4.5 mm away. The via goes straight out of the GND pad, away from the +3.3V pad, 1.05 mm from the pad centre
   (0.21 mm of mask between the pad and the tented via), with a 0.5 mm B.Cu track from the pad to the via."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.dont_write_bytecode = True
import pcbedit, geom
fn = sys.argv[1]
CAPS = ("C42", "C45", "C47", "C48", "C49", "C50", "C52", "C53"); D = 1.05; W = 0.5
B = pcbedit.Board(fn); G = geom.Board(fn)
vias, segs = [], []
for r in CAPS:
    pads = G.fps[r].placed()[0]
    g = next(p for p in pads if p["net"] == "GND"); q = next(p for p in pads if p["net"] == "+3.3V")
    dx, dy = g["x"] - q["x"], g["y"] - q["y"]; L = math.hypot(dx, dy)
    v = (round(g["x"] + dx/L*D, 3), round(g["y"] + dy/L*D, 3))
    vias.append(geom.V(*v, "GND")); segs += geom.P([(g["x"], g["y"]), v], W, "B.Cu", "GND")
if any(abs(w["x"] - vias[0]["x"]) < 1e-3 and abs(w["y"] - vias[0]["y"]) < 1e-3 for w in B.vias("GND")):
    sys.exit("lay_I2: already applied")
bad = G.check_items(vias=vias, segs=segs)
assert not bad, bad
for v in vias: B.add_via((v["x"], v["y"]), "GND", free=True)
for s in segs: B.add_seg((s["x1"], s["y1"]), (s["x2"], s["y2"]), W, "B.Cu", "GND")
B.save()
print("I3:", [(v["x"], v["y"]) for v in vias])
