"""§4: one 1206 per phase in the middle row of the HS-drain column (freed by moving R_g HS to the node side).
Same relative position on the three phases; VDC via next to the VDC pad, GND via next to the GND pad."""
import sys, json, math
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
import geom, viaspot
G = geom.Board(sys.argv[1])
COLS = {"C": (128.2, "C124"), "B": (145.2, "C128"), "A": (162.5, "C132")}
res = []
for dx in [i*0.05 for i in range(20, 61)]:
    for y in [80.6 + i*0.05 for i in range(0, 56)]:
        for rot in (0, 180):
            ok = True; per = {}
            for ph, (x0, ref) in COLS.items():
                x = x0 + 2.6 + dx
                if G.check_fast(ref, x, y, rot): ok = False; break
                pads, _ = G.fps[ref].placed(x, y, rot)
                if not all(x0 - 0.5 < p["x"] - p["aw"]/2 and p["x"] + p["aw"]/2 < x0 + 7.0 for p in pads): ok = False; break
                per[ph] = (round(x, 3), round(y, 3), rot)
            if ok: res.append((dx, y, rot, per))
print("candidates:", len(res))
best = None
for dx, y, rot, per in res[::3]:
    tot = 0; vias = {}
    for ph, (x, yy, r) in per.items():
        ref = COLS[ph][1]
        G.fps[ref].x, G.fps[ref].y, G.fps[ref].rot = x, yy, r; G._pc = None
        pads = {p["net"]: p["name"] for p in G.fps[ref].placed()[0]}
        sg = viaspot.spots(G, ref, pads["GND"], "GND", 0.9, step=0.1)
        sv = viaspot.spots(G, ref, pads["VDC"], "VDC", 0.9, step=0.1)
        if not sg or not sv: tot = None; break
        tot += sg[0][0] + sv[0][0]; vias[ph] = (sg[0][1:], sv[0][1:])
    if tot is not None and (best is None or tot < best[0]): best = (tot, per, vias)
print(best)
json.dump({"per": best[1], "vias": best[2]} if best else {}, open(sys.argv[3], "w"))
