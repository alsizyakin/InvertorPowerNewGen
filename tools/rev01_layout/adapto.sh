#!/bin/bash
# Branch rev0.1-adapto (owner 2026-10-22), from rev0.1-ina-ref ddae73b + the owner's R8 (series R in DAC_1_MCU):
# the top zone and the outline as in MINICONTROLLER_ADAPTO, 3 mm higher than there (variant V1, the snubber strip
# stays), and the Y circuit of docs/Y_TASK.md at H2. Project dir $1, KiCad closed.
#  1. lay_AD1.py     bulk caps C25 / C22, J4 / J5, H1 / H2 in side U-slots, MLCC row, outline above y 92.75; 53 x 101 mm
#  2. fp_y.py        footprints MountingHole_3.2mm_M3_Slot_CHS and Fuse_2410_1206 -> Lib/Power_My.pretty, fp-lib-table
#  3. sch_rev01_j.py out H5 / C135 / C136; Y block CY1 CY2 FY1 RY1 RY2 TP2 TP3, H2 = H_CHS; netclass Y_CHASSIS, rules
#  4. lay_Y1.py      the board part of step 3
#  5. kicad-cli      refill zones, save, DRC with schematic parity (run_drc.sh), then y_checks.py
set -e
P=$(cd "$1" && pwd); T=$(cd "$(dirname "$0")" && pwd)
python3 -B "$T/lay_AD1.py" "$P/Power.kicad_pcb"
python3 -B "$T/fp_y.py" "$P"
python3 -B "$T/sch_rev01_j.py" "$P" "$T"
python3 -B "$T/lay_Y1.py" "$P/Power.kicad_pcb" "$T"
