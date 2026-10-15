#!/bin/bash
# run_drc.sh <workdir> : refill zones, save, DRC with parity -> <workdir>/drc.json ; prints summary
cd "$1" && kicad-cli pcb drc --refill-zones --save-board --schematic-parity --severity-all --format json -o drc.json Power.kicad_pcb >/dev/null 2>&1
python3 -I - <<'PY'
import json, collections
d=json.load(open("drc.json"))
print("viol", dict(collections.Counter((x["severity"],x["type"]) for x in d["violations"])), "| unconn", len(d["unconnected_items"]), "| parity", len(d["schematic_parity"]))
PY
