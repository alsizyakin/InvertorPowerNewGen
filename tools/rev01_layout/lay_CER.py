"""§4: one 1206 1u 100V per phase in the middle row of the HS-drain column (C124 / C128 / C132), same relative
position on the three phases; own VDC via (In2) and GND via (In3) next to the pads (place_cer.py, L/cer.json)."""
import sys, json
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from pcbedit import Board
import geom
fn = sys.argv[1]; d = json.load(open(sys.argv[3]))
REF = {"C": "C124", "B": "C128", "A": "C132"}
B = Board(fn)
for ph, pos in d["per"].items(): B.move_fp(REF[ph], *pos)
B.save()
G = geom.Board(fn); B = Board(fn)
for ph, (gv, vv) in d["vias"].items():
    pads = {p["net"]: p for p in G.fps[REF[ph]].placed()[0]}
    for net, v in (("GND", gv), ("VDC", vv)):
        p = pads[net]
        x = min(max(v[0], p["x"] - p["aw"]/2 + 0.2), p["x"] + p["aw"]/2 - 0.2)
        B.track([(x, p["y"]), tuple(v)], 0.5, "F.Cu", net); B.add_via(tuple(v), net)
    print(ph, REF[ph], {n: (round(p["x"], 2), round(p["y"], 2)) for n, p in pads.items()}, "vias", gv, vv)
B.save()
print("lay_CER applied")
