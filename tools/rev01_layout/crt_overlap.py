"""Courtyard overlaps on one side (the project's DRC ignores courtyards_overlap). Rectangular courtyard bboxes;
radial bulk caps as circles r 5.25. Prints overlapping pairs; with refs given, only pairs that involve them.
Usage: crt_overlap.py board.kicad_pcb [REF ...]"""
import sys, os, math, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.dont_write_bytecode = True
import geom
G = geom.Board(sys.argv[1]); only = set(sys.argv[2:])
items = []
for r, f in G.fps.items():
    pads, crt = f.placed()
    if not crt or crt[2] - crt[0] < 0.01: continue
    if f.lib.startswith("Capacitor_THT:CP_Radial"):
        items.append((r, f.layer, "c", (f.x + 2.5*math.cos(math.radians(-f.rot)), f.y + 2.5*math.sin(math.radians(-f.rot)), 5.25)))
    else:
        items.append((r, f.layer, "r", crt))
n = 0
for a, b in itertools.combinations(items, 2):
    if a[1] != b[1] or (only and a[0] not in only and b[0] not in only): continue
    if a[2] == "r" and b[2] == "r":
        A, B = a[3], b[3]; hit = min(A[2], B[2]) - max(A[0], B[0]) > 1e-6 and min(A[3], B[3]) - max(A[1], B[1]) > 1e-6
    elif a[2] == "c" and b[2] == "c": hit = math.hypot(a[3][0]-b[3][0], a[3][1]-b[3][1]) < a[3][2] + b[3][2] - 1e-6
    else:
        c, r = (a, b) if a[2] == "c" else (b, a); hit = geom.d_pt_rect(c[3][0], c[3][1], r[3]) < c[3][2] - 1e-6
    if hit: print("overlap", a[0], b[0], a[1]); n += 1
print("overlaps:", n)
