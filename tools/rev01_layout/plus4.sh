#!/bin/bash
# +4 mm board (branch rev0.1-plus4) from the rev0.1-gnd board with Д1/Д2, in the project dir $1 (KiCad closed):
#  1. stretch.py       everything above y 72 (bulk caps, J4/J5, H1/H2, outline) up by 4 mm
#  2. stretch_zones.py tops of the F.Cu node zones and GND strips up to y 71.25, VDC cut there; rev0 0603s parked
#  3. sch_rev01_e.py   schematic: snubber R -> 0612 0.47 Ohm, one more 1206 per phase (C125/C129/C133)
#  4. lay_P4.py        strip plan (strip_plan.py -> data/strip_plan_plus4.json): snubbers, 1206, 0603s
#  5. lay_P4b.py       review round 2: snubber middle points 0.5 mm, VDC back on B.Cu in the strip, B.Mask off the slots
#  6. octo.py          owner 2026-10-19: every track at 0 / 45 / 90 degrees
#  7. lay_P4c.py       owner 2026-10-19: VDC to J6 from the top band, In1 through passage C; thermistor C lines on In1
#  8. sch_rev01_f.py   owner 2026-10-19: U4, U9, U12 AD8418 -> INA240A1 (pin to pin)
#  9. kicad-cli        refill zones, save, DRC with schematic parity (run_drc.sh on a copy, then copy the board back)
set -e
P=$(cd "$1" && pwd); T=$(cd "$(dirname "$0")" && pwd); TMP=$(mktemp -d)
python3 -B "$T/stretch.py" "$P/Power.kicad_pcb" "$TMP/s1.kicad_pcb" 72 4
KEEP0603=1 python3 -B "$T/stretch_zones.py" "$TMP/s1.kicad_pcb" "$TMP/s2.kicad_pcb" 71.25
python3 -B "$T/sch_rev01_e.py" "$P" "$T"
python3 -B "$T/lay_P4.py" "$TMP/s2.kicad_pcb" "$P/Power.kicad_pcb" "$T/data/strip_plan_plus4.json" "$T/data/sch_e_uuids.json"
python3 -B "$T/lay_P4b.py" "$P/Power.kicad_pcb"
python3 -B "$T/octo.py" "$P/Power.kicad_pcb" "$T"
python3 -B "$T/lay_P4c.py" "$P/Power.kicad_pcb"
python3 -B "$T/sch_rev01_f.py" "$P"
rm -rf "$TMP"
