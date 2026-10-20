"""Current spreading in the power copper of the three phases (cflow.py), 100 A DC per case:
- node: LS on (current from the LS drain tabs) or HS on (from the HS source pins) to the shunt pad;
- VDC:  from the 11 bulk caps to the HS drain tabs of one phase;
- GND:  from the LS source pins of one phase to the bulk caps.
Transistors WMB043N10HGS in parallel, R_ds 4.3 mOhm each in series with their pads.
Prints resistance of the copper, transistor sharing, current per layer through cuts, losses, the value of each
inner layer (resistance without it) and idle vias; draws |J| maps. Usage: cflow_cases.py board outdir [case ...]"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.dont_write_bytecode = True
import numpy as np, cflow, kpcb, geom

fn, outdir = sys.argv[1], sys.argv[2]; only = set(sys.argv[3:])
K = kpcb.load(fn); G = geom.Board(fn)
RDS, I = 4.3e-3, 100.0
# grid: node 0.05 mm, VDC / GND 0.1 mm - 0.1 -> 0.05 changes R by 2.5...5 % (review 11 P15)
H_NODE, H_PLANE = float(os.environ.get("CFLOW_H", "0.05")), float(os.environ.get("CFLOW_HP", "0.1"))
BULK = ["C4", "C6", "C10", "C11", "C12", "C15", "C18", "C22", "C23", "C24", "C25"]
PH = {"C": dict(node="/Current_Sensor_3/Phase_IN", ls=("Q8", "Q4"), hs=("Q1", "Q7"), shunt=("R7", "1"), x=(116.25, 137.0)),
      "B": dict(node="/Current_Sensor_2/Phase_IN", ls=("Q9", "Q5"), hs=("Q2", "Q10"), shunt=("R9", "2"), x=(133.0, 152.0)),
      "A": dict(node="/Current_Sensor_1/Phase_IN", ls=("Q11", "Q6"), hs=("Q3", "Q12"), shunt=("R52", "2"), x=(150.0, 169.25))}

def smd(M, ref, nm): return [c for c in M.pad_cells(ref, {nm}) if c[0] == "F.Cu"]

def build(case, drop_layer=None):
    kind, ph, sw = case.split("_")
    M = model(case)
    if drop_layer: M.drop_layer(drop_layer)
    return terminals(M, case)

_cache = {}
def model(case):
    kind, ph, sw = case.split("_"); p = PH[ph]
    key = (kind, ph)
    if key not in _cache:
        if kind == "node": _cache[key] = cflow.Model(fn, p["node"], (p["x"][0], 70.5, p["x"][1], 105.0), h=H_NODE, K=K, G=G)
        else: _cache[key] = cflow.Model(fn, kind, (116.25, 31.5, 169.25, 92.5), h=H_PLANE, K=K, G=G)
    import copy
    M = copy.copy(_cache[key]); M.mask = {l: m.copy() for l, m in M.mask.items()}; M.sources, M.sinks = [], []
    return M

def terminals(M, case):
    kind, ph, sw = case.split("_")
    p = PH[ph]
    if kind == "node":
        for q in (p["ls"] if sw == "LS" else p["hs"]): M.add_source(q, smd(M, q, "D" if sw == "LS" else "S"), RDS)
        M.add_sink("shunt", M.pad_cells(*p["shunt"][:1], {p["shunt"][1]}))
    elif kind == "VDC":
        for q in p["hs"]: M.add_source(q, smd(M, q, "D"), RDS)
        M.add_sink("bulk", sum((M.pad_cells(c, {"1"}) for c in BULK), []))
    else:
        for q in p["ls"]: M.add_source(q, smd(M, q, "S"), RDS)
        M.add_sink("bulk", sum((M.pad_cells(c, {"2"}) for c in BULK), []))
    return M

CUTS = {"node": (82.5, 90.0, 92.0, 95.5, 98.5, 100.0), "VDC": (68.0, 71.0, 74.0, 82.5), "GND": (68.0, 71.0, 74.0, 82.5)}
cases = [f"{k}_{ph}_{sw}" for ph in "CBA" for k, sw in (("node", "LS"), ("node", "HS"), ("VDC", "HS"), ("GND", "LS"))]
for case in cases:
    if only and case not in only: continue
    kind, ph, sw = case.split("_")
    M = build(case); M.solve(I)
    rc = (M.r_total() - RDS/2)*1e3
    src = M.source_currents()
    print(f"\n== {case}: copper {rc:.3f} mOhm (100 A: {rc*1e-3*I*I:.1f} W)  sharing " + " / ".join(f"{k} {v:.1f} A" for k, v in src.items()))
    xr = PH[ph]["x"]
    for y in CUTS[kind]:
        c = M.layer_cut(y=y, rng=None if kind == "node" else xr)
        print(f"   cut y {y:5.1f}: " + "  ".join(f"{l[:3]} {v:5.1f}" for l, v in c.items() if abs(v) > 0.05) + f"   (sum {sum(c.values()):.1f})")
    loss, vl = M.layer_loss()
    print("   loss W: " + "  ".join(f"{l[:3]} {v:.2f}" for l, v in loss.items() if v > 0.005) + f"  vias {vl:.2f}")
    worth = []
    for l in ("In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"):
        if not M.mask[l].any(): continue
        M2 = build(case, drop_layer=l); M2.solve(I)
        if not M2.live[M2.S]: worth.append(f"{l[:3]} path broken"); continue
        worth.append(f"{l[:3]} +{((M2.r_total() - RDS/2)*1e3 - rc)/rc*100:.0f}%")
    print("   without the layer, copper resistance: " + "  ".join(worth))
    idle = cflow.idle_barrels(M)
    nb = sum(1 for b in M.barrels if b[4] == "via")
    print(f"   barrels {len(M.barrels)} (vias {nb}); carrying < 0.2 A: {len(idle)}")
    cflow.plot(M, os.path.join(outdir, f"cf_{case}.png"), vmax=500, title=f"{case}, 100 A, |J| A/mm2")
    np.save(os.path.join(outdir, f"gain_{case}.npy"), cflow.via_gain(M, I))
