"""All numbers of the current-spreading report for several boards (corrected cflow, review 11 P15).
Usage: cflow_report.py out.json label=board.kicad_pcb [label=board ...] [--layers label]
Per board and case (node LS/HS, VDC, GND of phases C, B, A; 100 A, R_ds 4.3 mOhm per transistor):
copper resistance, transistor sharing, current per layer through the cuts of cflow_cases.py, for node cases the copper
loss within 2 mm of the shunt pad and the 99th percentile |J| in the ring 0.2-0.5 mm around it on B.Cu;
with --layers <label>: the resistance with each inner layer reduced to its pads (the value of the layer)."""
import sys, os, io, json, contextlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.dont_write_bytecode = True
import numpy as np, cflow
HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]; args = sys.argv[2:]
layers_for = args[args.index("--layers") + 1] if "--layers" in args else None
boards = [a.split("=", 1) for a in args if "=" in a]
CASES = [f"{k}_{ph}_{sw}" for ph in "CBA" for k, sw in (("node", "LS"), ("node", "HS"), ("VDC", "HS"), ("GND", "LS"))]
CUTS = {"node": (90.0, 92.0, 95.5, 98.5, 100.0), "VDC": (71.0, 74.0, 82.5), "GND": (71.0, 74.0, 82.5)}
res = {}
for label, fn in boards:
    g = {"__file__": os.path.join(HERE, "cflow_cases.py")}; argv = sys.argv
    sys.argv = ["cflow_cases.py", fn, "/tmp", "none"]
    with contextlib.redirect_stdout(io.StringIO()): exec(open(g["__file__"]).read().split("CUTS = ")[0], g)
    sys.argv = argv
    res[label] = {}
    for case in CASES:
        kind, ph, sw = case.split("_")
        M = g["build"](case); M.solve(g["I"]); rc = (M.r_total() - g["RDS"]/2)*1e3
        d = {"R_mOhm": round(rc, 4), "share": {k: round(v, 1) for k, v in M.source_currents().items()},
             "cuts": {str(y): {l[:3]: round(v, 1) for l, v in M.layer_cut(y=y, rng=None if kind == "node" else g["PH"][ph]["x"]).items() if abs(v) > 0.05}
                      for y in CUTS[kind]}}
        if kind == "node":
            sh, pn = g["PH"][ph]["shunt"]; pad = [p for p in M.G.fps[sh].placed()[0] if p["name"] == pn][0]
            r = (pad["x"] - pad["aw"]/2, pad["y"] - pad["ah"]/2, pad["x"] + pad["aw"]/2, pad["y"] + pad["ah"]/2)
            loss, p99 = cflow.near_pad(M, r); d["loss2mm_W"] = round(loss, 3); d["p99_Amm2"] = round(p99)
        if label == layers_for:
            d["without"] = {}
            for l in ("In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"):
                if not M.mask[l].any(): continue
                M2 = g["build"](case, drop_layer=l); M2.solve(g["I"])
                d["without"][l[:3]] = None if not M2.live[M2.S] else round(((M2.r_total() - g["RDS"]/2)*1e3/rc - 1)*100, 1)
        res[label][case] = d
        print(label, case, d["R_mOhm"], d.get("loss2mm_W", ""), d.get("p99_Amm2", ""), d.get("without", ""), flush=True)
json.dump(res, open(out, "w"), indent=1)
