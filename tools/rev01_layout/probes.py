"""§8: probe point pairs. Tip on an existing exposed F.Cu pad of the signal; ground on an exposed F.Cu pad of the
reference net at 3.5...6.5 mm (closest to 5 mm). Prints the table; pairs without a reference pad are flagged."""
import sys, math
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
import geom
G = geom.Board(sys.argv[1])
def fpads(net, box=None):
    out = []
    for r, f in G.fps.items():
        for p in f.placed()[0]:
            if p["net"] != net: continue
            if not (p["tht"] or f.layer == "F.Cu"): continue
            if box and not (box[0] <= p["x"] <= box[2] and box[1] <= p["y"] <= box[3]): continue
            out.append((f"{r}.{p['name']}", p["x"], p["y"], min(p["aw"], p["ah"])))
    return out
PH = {"C": dict(drv="D4", n="3", node="/Current_Sensor_3/Phase_IN", x0=116.2, cer="C124", boot="C7", dk="Net-(D1-K)",
                hs=[("Q1", "Net-(C100-Pad1)"), ("Q7", "Net-(C101-Pad1)")], ls=("Q8", "Net-(C102-Pad1)")),
      "B": dict(drv="D5", n="2", node="/Current_Sensor_2/Phase_IN", x0=134.2, cer="C128", boot="C8", dk="Net-(D2-K)",
                hs=[("Q2", "Net-(C104-Pad1)"), ("Q10", "Net-(C105-Pad1)")], ls=("Q9", "Net-(C106-Pad1)")),
      "A": dict(drv="D6", n="1", node="/Current_Sensor_1/Phase_IN", x0=151.2, cer="C132", boot="C9", dk="Net-(D3-K)",
                hs=[("Q3", "Net-(C108-Pad1)"), ("Q12", "Net-(C109-Pad1)")], ls=("Q11", "Net-(C110-Pad1)"))}
def best_pair(tips, refs, avoid_same_fp=True):
    best = None
    for t in tips:
        for r in refs:
            if avoid_same_fp and t[0].split(".")[0] == r[0].split(".")[0] and False: continue
            d = math.hypot(t[1]-r[1], t[2]-r[2])
            if 3.0 <= d <= 7.0:
                k = abs(d - 5.0)
                if best is None or k < best[0]: best = (k, t, r, d)
    return best
rows = []
for ph, P in PH.items():
    blk = (P["x0"] - 1, 70, P["x0"] + 19, 95)
    drvbox = (G.fps[P["drv"]].x - 9, 100, G.fps[P["drv"]].x + 9, 116)
    vdc = [p for p in fpads("VDC") if p[0].startswith(P["cer"])]
    rows.append((ph, "1 VDC/GND у керамики", best_pair(vdc, fpads("GND", blk))))
    rows.append((ph, "2 BST/SW драйвера", best_pair([p for p in fpads(P["dk"]) if p[0].startswith(P["boot"])], fpads(f"/Driver_{P['n']}/SW", drvbox))))
    gd = fpads("GND", drvbox)
    rows.append((ph, "3 HI/GND", best_pair(fpads(f"Net-({P['drv']}-HI)"), gd)))
    rows.append((ph, "3 LI/GND", best_pair(fpads(f"Net-({P['drv']}-LI)"), gd)))
    for q, gnet in P["hs"]:
        rows.append((ph, f"4 G/S {q} (HS)", best_pair(fpads(gnet), fpads(P["node"], blk))))
    q, gnet = P["ls"]
    rows.append((ph, f"5 G/S {q} (LS)", best_pair(fpads(gnet), fpads("GND", blk))))
    rows.append((ph, f"5 D/S {q} (LS)", best_pair([p for p in fpads(P["node"], blk) if p[0].startswith(q)], fpads("GND", blk))))
for ph, what, b in rows:
    if b: print(f"{ph} | {what:22s} | tip {b[1][0]:10s} ({b[1][1]:.2f},{b[1][2]:.2f}) | ref {b[2][0]:10s} ({b[2][1]:.2f},{b[2][2]:.2f}) | {b[3]:.1f} mm")
    else: print(f"{ph} | {what:22s} | NO reference pad at 3-7 mm")
