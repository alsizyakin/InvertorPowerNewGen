"""Before / after figures and table for the current-spreading report (cflow.py, cflow_cases.py).
Usage: cflow_figs.py board_before board_after outdir
- table.csv: copper resistance (mOhm) at 100 A for every case, before and after; for the node cases also the copper loss
  within 2 mm of the shunt pad (W) and the 99th percentile |J| in the ring 0.2-0.5 mm around it on B.Cu (A/mm2) -
  not the single-cell peak, which is singular at the pad corner and grows with the grid (review 11 P15);
- fig_*.png: |J| maps, the same colour scale, row 1 before, row 2 after, with the vias (ring width ~ via current);
  panel titles give the 99th percentile |J| of the panel."""
import sys, os, io, contextlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.dont_write_bytecode = True
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import cflow, kpcb, geom

before, after, out = sys.argv[1], sys.argv[2], sys.argv[3]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cflow_cases.py")).read().split("CUTS = ")[0]
def env(fn):
    g = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "cflow_cases.py")}; argv = sys.argv
    sys.argv = ["cflow_cases.py", fn, out, "none"]
    with contextlib.redirect_stdout(io.StringIO()): exec(src, g)
    sys.argv = argv; return g
E = {"до": env(before), "после": env(after)}
LNAME = {"F.Cu": "F.Cu", "In1.Cu": "In1", "In2.Cu": "In2", "In3.Cu": "In3", "In4.Cu": "In4", "B.Cu": "B.Cu"}

def solved(tag, case):
    g = E[tag]; M = g["build"](case); M.solve(g["I"]); return M

def at_shunt(tag, case, M):
    if not case.startswith("node"): return float("nan"), float("nan")
    sh, pn = E[tag]["PH"][case.split("_")[1]]["shunt"]; p = [q for q in M.G.fps[sh].placed()[0] if q["name"] == pn][0]
    return cflow.near_pad(M, (p["x"] - p["aw"]/2, p["y"] - p["ah"]/2, p["x"] + p["aw"]/2, p["y"] + p["ah"]/2))

rows = []
for case in [f"{k}_{ph}_{sw}" for ph in "CBA" for k, sw in (("node", "LS"), ("node", "HS"), ("VDC", "HS"), ("GND", "LS"))]:
    r = []
    for tag in ("до", "после"):
        M = solved(tag, case); rd = E[tag]["RDS"]
        r += [(M.r_total() - rd/2)*1e3, *at_shunt(tag, case, M)]
    rows.append((case, *r))
with open(os.path.join(out, "table.csv"), "w") as f:
    f.write("case,R_before_mOhm,loss2mm_before_W,p99_before,R_after_mOhm,loss2mm_after_W,p99_after\n")
    for c, r0, l0, j0, r1, l1, j1 in rows: f.write(f"{c},{r0:.3f},{l0:.2f},{j0:.0f},{r1:.3f},{l1:.2f},{j1:.0f}\n")
for c, r0, l0, j0, r1, l1, j1 in rows:
    print(f"{c:10s} {r0:.3f} -> {r1:.3f} mOhm ({(r1/r0-1)*100:+5.1f}%)   at the shunt {l0:.2f} -> {l1:.2f} W, p99 {j0:.0f} -> {j1:.0f}")

def fig(name, case, layers, crop, title, vmax=500):
    Ms = {tag: solved(tag, case) for tag in ("до", "после")}
    x0, y0, x1, y1 = crop; w, h = x1 - x0, y1 - y0
    sc = 9.0 / (w*len(layers)); fig, axs = plt.subplots(2, len(layers), figsize=(w*sc*len(layers) + 1.2, h*sc*2 + 1.0), squeeze=False)
    for r, tag in enumerate(("до", "после")):
        M = Ms[tag]; cur = M.barrel_currents(); rd = E[tag]["RDS"]
        for c, l in enumerate(layers):
            ax = axs[r][c]; J = M.density(l); wx0, wy0, wx1, wy1 = M.win
            im = ax.imshow(J, extent=(wx0, wx1, wy1, wy0), cmap="inferno", vmin=0, vmax=vmax, interpolation="nearest")
            ax.set_facecolor("#e9e9ee")
            for k, (bx, by, d, br, nm) in enumerate(M.barrels):
                if not (x0 - 1 < bx < x1 + 1 and y0 - 1 < by < y1 + 1): continue
                tr = max((abs(i) for _, _, i in cur.get(k, [])), default=0)
                ax.add_patch(Circle((bx, by), br, fc="none", ec="#36d6e7" if tr > 0.5 else "#8a8aa0", lw=0.5 + min(tr, 8)*0.25))
            ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect("equal"); ax.tick_params(labelsize=6)
            jm = np.nanpercentile(np.where((M.X >= x0) & (M.X <= x1) & (M.Y >= y0) & (M.Y <= y1), J, np.nan), 99)
            ax.set_title(f"{tag}: {LNAME[l]}, 99 % клеток ≤ {jm:.0f} А/мм²", fontsize=8)
        axs[r][0].set_ylabel(f"{tag}: медь {(M.r_total() - rd/2)*1e3:.3f} мОм", fontsize=8)
    cb = fig.colorbar(im, ax=axs.ravel().tolist(), fraction=0.025, pad=0.02); cb.ax.tick_params(labelsize=6)
    cb.set_label("|J|, А/мм² при 100 А (35 мкм)", fontsize=7)
    fig.suptitle(title, fontsize=9); plt.savefig(os.path.join(out, name), dpi=150, bbox_inches="tight"); plt.close(fig)

fig("fig_A_shunt.png", "node_A_LS", ["In1.Cu", "In2.Cu", "B.Cu"], (153.5, 95.5, 165.5, 105.5),
    "Узел A → шунт R52.2 (проводит LS): подход к шунту")
fig("fig_A_path.png", "node_A_LS", ["In2.Cu", "B.Cu"], (150.0, 74.0, 169.0, 106.0), "Узел A → шунт (проводит LS): весь путь", vmax=400)
fig("fig_VDC_A.png", "VDC_A_HS", ["F.Cu", "In2.Cu", "B.Cu"], (155.0, 64.0, 169.25, 80.0), "VDC: банки → стоки HS фазы A, вход в колонку стока", vmax=400)
fig("fig_VDC_C.png", "VDC_C_HS", ["F.Cu", "In2.Cu", "B.Cu"], (120.0, 64.0, 135.5, 80.0), "VDC: банки → стоки HS фазы C, вход в колонку стока", vmax=400)
fig("fig_GND_C.png", "GND_C_LS", ["F.Cu", "In1.Cu", "In3.Cu", "In4.Cu"], (116.25, 64.0, 123.5, 80.0), "GND: истоки LS фазы C → банки, верх полосы GND", vmax=300)
fig("fig_C_shunt.png", "node_C_LS", ["In2.Cu", "B.Cu"], (120.0, 95.5, 130.5, 105.0), "Узел C → шунт R7.1 (проводит LS)")
print("figures in", out)
