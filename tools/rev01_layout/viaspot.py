"""Find via spots for a net next to a pad: via (0.6/0.3) clear of other-net pads/tracks/vias on all layers by 0.2,
not touching the pad itself, sorted by distance. Usage as module: spots(G, ref, padname, net, maxd)"""
import math, geom
def spots(G, ref, pname, net, maxd=1.6, step=0.05, avoid=()):
    f = G.fps[ref]; p = [q for q in f.placed()[0] if q["name"] == pname][0]
    pr = (p["x"]-p["aw"]/2, p["y"]-p["ah"]/2, p["x"]+p["aw"]/2, p["y"]+p["ah"]/2)
    pads = [(r, q) for r, g in G.fps.items() for q in g.placed()[0] if abs(q["x"]-p["x"]) < 5 and abs(q["y"]-p["y"]) < 5]
    vias = [v for v in G.vias if abs(v["x"]-p["x"]) < 5 and abs(v["y"]-p["y"]) < 5]
    segs = [s for s in G.segs if min(abs(s["x1"]-p["x"]), abs(s["x2"]-p["x"])) < 6 and min(abs(s["y1"]-p["y"]), abs(s["y2"]-p["y"])) < 6]
    out = []
    n = int(maxd/step) + 12
    for i in range(-n, n+1):
        for j in range(-n, n+1):
            x, y = p["x"] + i*step, p["y"] + j*step
            d0 = geom.d_pt_rect(x, y, pr) - 0.3
            if d0 < 0.05 or d0 > maxd: continue
            ok = True
            for r, q in pads:
                if r == ref and q["name"] == pname: continue
                qr = (q["x"]-q["aw"]/2, q["y"]-q["ah"]/2, q["x"]+q["aw"]/2, q["y"]+q["ah"]/2)
                if geom.d_pt_rect(x, y, qr) - 0.3 < (0.05 if q["net"] == net else 0.2): ok = False; break
            if not ok: continue
            for v in vias:
                if math.hypot(v["x"]-x, v["y"]-y) < (0.5 if v["net"] == net else 0.8): ok = False; break
            if not ok: continue
            for s in segs:
                if s["net"] == net: continue
                if geom.d_seg_rect(s["x1"], s["y1"], s["x2"], s["y2"], (x, y, x, y)) - s["w"]/2 - 0.3 < 0.2: ok = False; break
            if ok and not any(a(x, y) for a in avoid): out.append((round(d0, 3), round(x, 3), round(y, 3)))
    return sorted(out)
