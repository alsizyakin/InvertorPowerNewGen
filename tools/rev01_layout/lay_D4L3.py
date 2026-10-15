"""D4 left, part 3: route the inputs to R118/R121 and to the pins (router), add the tracks to the board."""
import sys, json
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
import geom, router
from pcbedit import Board
G = geom.Board(sys.argv[1]); segs = []; out = {}
pads = {r: {p["name"]: (p["x"], p["y"]) for p in G.fps[r].placed()[0]} for r in ("R118", "R121")}
def rt(key, a, b, net, win, tail):
    global segs
    p = router.Router(G, "F.Cu", win).route(a, b, net, 0.3, extra_segs=segs)
    print(key, "->", p); out[key] = (p, net, tail)
    if p: segs += geom.P(p, 0.3, "F.Cu", net)
rt("LI_up", pads["R121"]["2"], (127.3, 106.615), "Net-(D4-LI)", (123.5, 104.0, 130, 113), [(128.28, 106.615)])
rt("HI_up", pads["R118"]["2"], (127.3, 105.345), "Net-(D4-HI)", (123.0, 104.0, 130, 113), [(128.28, 105.345)])
rt("LI_low", pads["R121"]["1"], (131.0, 114.75), "/TMR1_CH3N", (124, 108, 133, 117), [])
rt("HI_low", pads["R118"]["1"], (130.5, 115.0), "/TMR1_CH3", (123, 108, 133, 117), [])
B = Board(sys.argv[1])
for k, (p, net, tail) in out.items():
    if p: B.track(p + tail, 0.3, "F.Cu", net)
B.save()
print("routed", sum(1 for v in out.values() if v[0]), "of", len(out))
