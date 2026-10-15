"""Place a 2-pad part near anchors: grid search with geom.check, then route each pad to its anchor with router.Router.
Returns placement and routed polylines (on the part's layer)."""
import math, geom, router

def place_and_route(G, ref, layer, win, conns, rots=(0, 90, 180, 270), step=0.1, w=0.3, moved=None, extra_segs=(),
                    extra_vias=(), skip=lambda o: False, max_len=8.0, rwin_margin=2.0):
    """conns: {pad_name: (x, y)} anchor point the pad must be routed to (on `layer`)."""
    moved = dict(moved or {}); f = G.fps[ref]
    cands = []
    x0, y0, x1, y1 = win
    for rot in rots:
        x = x0
        while x <= x1 + 1e-9:
            y = y0
            while y <= y1 + 1e-9:
                if not G.check(ref, x, y, rot, moved=moved, extra_vias=extra_vias, extra_segs=extra_segs):
                    pads, _ = f.placed(x, y, rot)
                    est = sum(math.hypot(p["x"] - conns[p["name"]][0], p["y"] - conns[p["name"]][1]) for p in pads if p["name"] in conns)
                    cands.append((est, (round(x, 3), round(y, 3), rot)))
                y += step
            x += step
    cands.sort()
    for est, (x, y, rot) in cands[:60]:
        mv = dict(moved); mv[ref] = (x, y, rot)
        pads, _ = f.placed(x, y, rot); routes = {}; ok = True; segs_acc = list(extra_segs)
        for p in pads:
            if p["name"] not in conns: continue
            a = (p["x"], p["y"]); b = conns[p["name"]]
            rw = (min(a[0], b[0]) - rwin_margin, min(a[1], b[1]) - rwin_margin, max(a[0], b[0]) + rwin_margin, max(a[1], b[1]) + rwin_margin)
            R = router.Router(G, layer, rw)
            path = R.route(a, b, p["net"], w, moved=mv, extra_segs=segs_acc, extra_vias=extra_vias, skip=skip)
            if not path: ok = False; break
            L = sum(math.hypot(q[0]-r[0], q[1]-r[1]) for q, r in zip(path, path[1:]))
            if L > max_len: ok = False; break
            routes[p["name"]] = path
            segs_acc += geom.P(path, w, layer, p["net"])
        if ok:
            return (x, y, rot), routes
    return None, None
