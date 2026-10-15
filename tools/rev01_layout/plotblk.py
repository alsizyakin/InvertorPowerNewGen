"""Plot one copper layer of a .kicad_pcb window: zone fills coloured by net, pads (with ref.pad), vias, tracks.
   plotblk.py board.kicad_pcb layer x0 y0 x1 y1 out.png [mark x,y;x,y...]"""
import sys, math
sys.path.insert(0, "/home/alexey/Git/KiCad/InvertorPowerNewGen/bench_2026-10-13/tools"); sys.dont_write_bytecode = True
import kpcb, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle
fn, lay = sys.argv[1], sys.argv[2]; x0, y0, x1, y1 = map(float, sys.argv[3:7]); out = sys.argv[7]
B = kpcb.load(fn)
def col(net):
    if net == "GND": return "#5b8fd6"
    if net == "VDC": return "#d65b5b"
    if "Phase_IN" in net: return "#e8a33c"
    if "Phase_OUT" in net: return "#c9b458"
    return "#9a9a9a"
fig, ax = plt.subplots(figsize=((x1-x0)*0.62, (y1-y0)*0.62))
for z in B["zones"]:
    for l, pts in z["fills"]:
        if l == lay and len(pts) > 2:
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            if max(xs) < x0 or min(xs) > x1 or max(ys) < y0 or min(ys) > y1: continue
            ax.add_patch(Polygon(pts, closed=True, fc=col(z["net"]), ec="none", alpha=0.35))
for s in B["segs"]:
    if s["layer"] == lay:
        ax.plot([s["x1"], s["x2"]], [s["y1"], s["y2"]], color=col(s["net"]) if col(s["net"]) != "#9a9a9a" else "#7a3db8",
                lw=s["w"]*72/25.4*0.62*fig.dpi/72*1.0, solid_capstyle="round", alpha=0.9)
for f in B["fps"]:
    for p in f["pads"]:
        on = p["type"] == "thru_hole" or (f["layer"] == lay) or (lay not in ("F.Cu", "B.Cu") and p["type"] == "thru_hole")
        if not on or not (x0-2 < p["x"] < x1+2 and y0-2 < p["y"] < y1+2): continue
        if p["type"] != "thru_hole" and f["layer"] != lay: continue
        w, h = (p["w"], p["h"]) if abs(f["rot"]) % 180 == 0 else (p["h"], p["w"])
        if p["shape"] == "circle":
            ax.add_patch(Circle((p["x"], p["y"]), w/2, fc=col(p["net"]), ec="k", lw=0.3))
        else:
            ax.add_patch(Rectangle((p["x"]-w/2, p["y"]-h/2), w, h, fc=col(p["net"]), ec="k", lw=0.4))
        if p["type"] != "thru_hole" and w*h < 3:
            ax.text(p["x"], p["y"], f'{f["ref"]}.{p["name"]}', fontsize=4.2, ha="center", va="center", color="k")
    if f["layer"] == lay and x0 < f["x"] < x1 and y0 < f["y"] < y1 and not f["ref"].startswith("Q"):
        pass
for v in B["vias"]:
    if x0 < v["x"] < x1 and y0 < v["y"] < y1:
        ax.add_patch(Circle((v["x"], v["y"]), 0.25 if v["d"] < 0.3 else 0.3, fc=col(v["net"]), ec="k", lw=0.3))
if len(sys.argv) > 8:
    for xy in sys.argv[8].split(";"):
        a, b = map(float, xy.split(",")); ax.plot(a, b, "x", color="magenta", ms=8, mew=1.5)
ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect("equal")
ax.set_xticks([x0 + i*0.5 for i in range(int((x1-x0)/0.5)+1)], minor=True); ax.set_yticks([y0 + i*0.5 for i in range(int((y1-y0)/0.5)+1)], minor=True)
ax.set_xticks(range(math.ceil(x0), int(x1)+1)); ax.set_yticks(range(math.ceil(y0), int(y1)+1))
ax.grid(which="major", alpha=0.35, lw=0.5); ax.grid(which="minor", alpha=0.12, lw=0.3); ax.tick_params(labelsize=6)
ax.set_title(lay, fontsize=8)
plt.savefig(out, dpi=110, bbox_inches="tight")
