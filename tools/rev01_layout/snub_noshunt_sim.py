"""§5, option «one shunt less»: simulate a phase without its shunt by removing the node via field at the bottom of
its node column and under it (y 88.5...95.5) — without the shunt the node goes straight into the bushing below the
block, the field only carries current down to the shunt. Then refill (run_drc.sh) and run snub_search2.py with
ONLY=<ph>-LS,<ph>-HS. Usage: snub_noshunt_sim.py board.kicad_pcb tools_dir C|B|A"""
import sys
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from pcbedit import Board
CFG = {"C": ("/Current_Sensor_3/Phase_IN", 120.8, 129.0), "B": ("/Current_Sensor_2/Phase_IN", 137.8, 146.0),
       "A": ("/Current_Sensor_1/Phase_IN", 154.8, 163.0)}
net, x0, x1 = CFG[sys.argv[3]]
B = Board(sys.argv[1])
n = sum(1 for v in B.vias(net) if x0 <= v["x"] <= x1 and 88.5 <= v["y"] <= 95.5)
B.del_vias(lambda v: v["net"] == net and x0 <= v["x"] <= x1 and 88.5 <= v["y"] <= 95.5)
B.save(); print(sys.argv[3], "node vias removed:", n)
