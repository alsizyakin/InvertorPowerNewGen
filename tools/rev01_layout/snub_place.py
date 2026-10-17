"""Place the 12 snubber parts (C112-C117, R100-R105) at the best mutually compatible spots from a snub_search json
(variant a: C0805 + R1206) and join the middle pads. Usage: place_snub.py in.kicad_pcb out.kicad_pcb result.json"""
import sys, json, math, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[0]))); sys.dont_write_bytecode = True
import pcbedit
fi, fo, rj = sys.argv[1:4]
R = json.load(open(rj))
PARTS = {"C0805": (1.0375, 1.175, 1.45, 3.76, 1.97), "R1206": (1.55, 1.3, 1.75, 4.91, 2.25)}
REF = {"C-LS": ("C112", "R100"), "B-LS": ("C113", "R101"), "A-LS": ("C114", "R102"),
       "C-HS": ("C115", "R103"), "B-HS": ("C116", "R104"), "A-HS": ("C117", "R105")}
XNET = {"C112": "Net-(C112-Pad2)", "C113": "Net-(C113-Pad2)", "C114": "Net-(C114-Pad2)",
        "C115": "Net-(C115-Pad2)", "C116": "Net-(C116-Pad2)", "C117": "Net-(C117-Pad2)"}
def geom_(kind, x, y, rot):
    off, aw, ah, cw, ch = PARTS[kind]
    if rot in (90, 270): aw, ah, cw, ch = ah, aw, ch, cw
    dx, dy = (off, 0) if rot in (0, 180) else (0, off)
    return [(x - dx, y - dy, aw, ah), (x + dx, y + dy, aw, ah)], (x - cw/2 + .25, y - ch/2 + .25, x + cw/2 - .25, y + ch/2 - .25)
def rect(p): return (p[0]-p[2]/2, p[1]-p[3]/2, p[0]+p[2]/2, p[1]+p[3]/2)
def drr(a, b): return math.hypot(max(0, max(a[0], b[0]) - min(a[2], b[2])), max(0, max(a[1], b[1]) - min(a[3], b[3])))
def ov(a, b): return min(a[2], b[2]) - max(a[0], b[0]) > 1e-6 and min(a[3], b[3]) - max(a[1], b[1]) > 1e-6
def shapes(cand):
    c, r = cand[1], cand[2]
    cp, cc = geom_("C0805", c[0], c[1], c[2]); rp, rc = geom_("R1206", r[0], r[1], r[2])
    return [cc, rc], [rect(p) for p in cp + rp]
def compatible(a, b):
    ca, pa = shapes(a); cb, pb = shapes(b)
    return not any(ov(x, y) for x in ca for y in cb) and all(drr(x, y) >= 0.2 for x in pa for y in pb)
keys = [k for k in REF if R.get(k)]
best = None
for combo in itertools.product(*[range(len(R[k])) for k in keys]):
    cands = [R[k][i] for k, i in zip(keys, combo)]
    if all(compatible(a, b) for a, b in itertools.combinations(cands, 2)):
        score = sum(c[0] for c in cands)
        if best is None or score < best[0]: best = (score, combo)
if best is None: sys.exit("no compatible set")
B = pcbedit.Board(fi)
# KiCad rotation so that the terminal pad (C: pad 1, R: pad 2) lands where the search put it
KROT_C = {(0, 0): 0, (0, 1): 180, (90, 0): 270, (90, 1): 90}
KROT_R = {(0, 0): 180, (0, 1): 0, (90, 0): 90, (90, 1): 270}
for k, i in zip(keys, best[1]):
    cand = R[k][i]; c, r = cand[1], cand[2]; cref, rref = REF[k]
    B.move_fp(cref, c[0], c[1], KROT_C[(c[2], c[3])]); B.move_fp(rref, r[0], r[1], KROT_R[(r[2], r[3])])
    cx = geom_("C0805", c[0], c[1], c[2])[0][1 - c[3]]; rx = geom_("R1206", r[0], r[1], r[2])[0][1 - r[3]]
    B.add_seg((cx[0], cx[1]), (rx[0], rx[1]), 0.3, "F.Cu", XNET[cref])
    print(f"{k}: {cref} at ({c[0]:.1f}, {c[1]:.1f}) rot {KROT_C[(c[2], c[3])]}, {rref} at ({r[0]:.1f}, {r[1]:.1f}) rot "
          f"{KROT_R[(r[2], r[3])]}; terminal-to-pin {cand[3]} / {cand[4]} mm" + (f", vias {cand[5]} {cand[6]}" if len(cand) > 5 else ""))
B.save(fo)
