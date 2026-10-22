"""rev0.1-adapto, step AD1 (owner 2026-10-22): the top zone (bulk caps C25 / C22, J4 / J5, H1 / H2 in side U-slots,
MLCC row, outline) as in the sibling project MINICONTROLLER_ADAPTO, but 3 mm higher than there relative to the block:
our 3 mm snubber strip stays (variant V1 of tmp/2026-10-22_adapto). Board 53 x 101 mm (top edge 40.5, bottom 141.5),
the envelope of ADAPTO. Usage: lay_AD1.py board
- the outline above the lower clamp plate notches (y < 92.75) is replaced by the ADAPTO one; ADAPTO items above
  y 53.54 (top edge, corners, the H1 / H2 slots) go 3 mm up, its side lines 53.54-64.75 get 3 mm longer, the upper
  side notches 64.75-70.25 keep the block coordinates (data below, ADAPTO file frame = our block frame)
- the B.Cu GND stubs from the moved MLCCs to the GND pads of C25 / C22 are the ADAPTO ones, 3 mm up
- H5 / C135 / C136 (CHASSIS screw, Y caps) have no place in this top zone: parked off the board here, replaced by the
  Y circuit of docs/Y_TASK.md in steps sch_rev01_j.py / lay_Y1.py"""
import sys, re, uuid
sys.path.insert(0, __import__("os").path.dirname(__file__)); sys.dont_write_bytecode = True
import pcbedit, geom
fn = sys.argv[1]
DY = -3.0                                                     # ADAPTO top zone -> 3 mm higher
MOVES = {"C25": (121.75, 62.37, 90), "C22": (163.75, 62.37, 90),          # ADAPTO coordinates
         "J4": (125.6, 48.5, 90), "J5": (159.9, 48.5, 90),
         "H1": (117.93, 51.79, 0), "H2": (167.57, 51.79, 0),
         "C5": (119.5, 60.0, 90), "C21": (124.0, 60.0, 90), "C81": (161.5, 60.0, 90), "C82": (166.0, 60.0, 90)}
OFF = {"H5": (142.75, 20.0, 0), "C135": (135.0, 20.0, 0), "C136": (150.0, 20.0, 0)}
# ADAPTO B.Cu GND stubs, 1.0 mm (ADAPTO coordinates)
STUBS = [((124.0, 58.9625), (123.094823, 58.9625)), ((123.094823, 58.9625), (121.75, 57.617677)),
         ((119.5, 58.9625), (120.405177, 58.9625)), ((120.405177, 58.9625), (121.75, 57.617677)),
         ((161.5, 58.9625), (162.405177, 58.9625)), ((162.405177, 58.9625), (163.75, 57.617677)),
         ((166.0, 58.9625), (165.094823, 58.9625)), ((165.094823, 58.9625), (163.75, 57.617677))]
# ADAPTO outline above y 92.75 (ADAPTO coordinates): lines (start, end), arcs (start, mid, end)
LINES = [((116.25, 50.04), (116.25, 49.5)), ((116.25, 64.75), (116.25, 53.54)), ((116.25, 92.75), (116.25, 71.25)),
         ((117.93, 50.04), (116.25, 50.04)), ((117.93, 53.54), (116.25, 53.54)), ((119, 64.75), (116.25, 64.75)),
         ((119, 70.25), (117.25, 70.25)), ((163.25, 43.5), (122.25, 43.5)), ((166.5, 64.75), (169.25, 64.75)),
         ((166.5, 70.25), (168.25, 70.25)), ((167.57, 50.04), (169.25, 50.04)), ((167.57, 53.54), (169.25, 53.54)),
         ((169.25, 50.04), (169.25, 49.5)), ((169.25, 64.75), (169.25, 53.54)), ((169.25, 92.75), (169.25, 71.25))]
ARCS = [((116.25, 49.5), (118.007359, 45.257359), (122.25, 43.5)), ((116.25, 71.25), (116.542893, 70.542893), (117.25, 70.25)),
        ((117.93, 50.04), (119.68, 51.79), (117.93, 53.54)), ((119, 64.75), (121.75, 67.5), (119, 70.25)),
        ((163.25, 43.5), (167.492641, 45.257359), (169.25, 49.5)), ((166.5, 70.25), (163.75, 67.5), (166.5, 64.75)),
        ((167.57, 53.54), (165.82, 51.79), (167.57, 50.04)), ((168.25, 70.25), (168.957107, 70.542893), (169.25, 71.25))]

B = pcbedit.Board(fn)
s0 = B.s
if '(start 163.25 40.5)' in s0:
    sys.exit("lay_AD1: already applied")
# B.Cu GND stubs of the moved MLCCs to the old electrolytic pads, and the H5 / C135 / C136 tracks
OLD = [((128.34, 48.79), (127.0, 50.13)), ((129.25, 48.79), (128.34, 48.79)), ((124.75, 48.79), (125.66, 48.79)),
       ((125.66, 48.79), (127.0, 50.13)), ((160.75, 48.79), (159.84, 48.79)), ((159.84, 48.79), (158.5, 50.13)),
       ((157.16, 48.79), (158.5, 50.13)), ((156.25, 48.79), (157.16, 48.79)), ((141.15, 41.7), (141.15, 38.97)),
       ((144.35, 41.7), (144.35, 38.97)), ((148.45, 41.7), (149.9, 40.25))]
def hit(g):
    e = {(round(g["x1"], 2), round(g["y1"], 2)), (round(g["x2"], 2), round(g["y2"], 2))}
    return g["layer"] == "B.Cu" and any(e == set(o) for o in OLD)
n = B.del_segs(hit); assert n == len(OLD), n
for (x1, y1), (x2, y2) in STUBS:
    B.add_seg((x1, y1 + DY), (x2, y2 + DY), 1.0, "B.Cu", "GND")
for r, (x, y, a) in MOVES.items(): B.move_fp(r, x, y + DY, a)
for r, (x, y, a) in OFF.items(): B.move_fp(r, x, y, a)
B.save()

# ---------------------------------------------------------------- outline
s = open(fn, encoding="utf-8").read()
drop = []
for kind in ("gr_line", "gr_arc", "gr_curve"):
    for a, b in geom._blocks(s, kind):
        g = s[a:b]
        if '"Edge.Cuts"' in g:
            ys = [float(v) for v in re.findall(r'\((?:start|mid|end|xy) [\d.\-]+ ([\d.\-]+)\)', g)]
            if min(ys) < 92.75 - 1e-6: drop.append((a, b))
for a, b in sorted(drop, reverse=True):
    s = s[:a - 1] + s[b + 1:]                                                    # with the leading tab and newline
def y_of(y, ys):
    if max(ys) <= 53.54 + 1e-6: return y + DY                                    # top part: 3 mm up
    if abs(min(ys) - 53.54) < 1e-6 and abs(max(ys) - 64.75) < 1e-6 and abs(y - 53.54) < 1e-6:
        return y + DY                                                            # side lines 3 mm longer
    return y
def gr(kind, pts):
    ys = [p[1] for p in pts]
    tags = ("start", "end") if kind == "gr_line" else ("start", "mid", "end")
    body = "".join(f"\t\t({t} {pcbedit.fmt(x)} {pcbedit.fmt(y_of(y, ys))})\n" for t, (x, y) in zip(tags, pts))
    return (f'\t({kind}\n{body}\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{uuid.uuid4()}")\n\t)\n')
new = [gr("gr_line", p) for p in LINES] + [gr("gr_arc", p) for p in ARCS]
k = s.find("\n\t(gr_") + 1
s = s[:k] + "".join(new) + s[k:]
# polarity marks of J4 / J5 as in ADAPTO (131.75 / 154, 44.5), 3 mm up; the length dimension (User.1) to the new top edge
for t, x in (("+", 131.75), ("-", 154)):
    s, n = re.subn(r'(\(gr_text "' + re.escape(t) + r'"\n\t\t\(at )139 38\.5|(\(gr_text "' + re.escape(t) + r'"\n\t\t\(at )146\.5 38\.5',
                   lambda m: (m.group(1) or m.group(2)) + f"{pcbedit.fmt(x)} {pcbedit.fmt(44.5 + DY)}", s)
    assert n == 1, t
s, n = re.subn(r'\(xy 122\.7085 144\.5\) \(xy 132\.25 35\.744568\)', '(xy 122.7085 141.5) (xy 122.7085 40.5)', s); assert n == 1
open(fn, "w", encoding="utf-8").write(s)
print("lay_AD1: moved", list(MOVES), "| off board", list(OFF), "| edge items dropped", len(drop), "added", len(new))
