#!/bin/bash
# Board of the branch rev0.1-shift3, from the rev0.1-gnd board with Д1/Д2 (515455d), in the project dir $1 (KiCad closed).
# Owner 2026-10-20: the +4 mm length is not possible; the switch block goes 3 mm down instead and the MCU zone gives
# the room, so the bulk caps get the same 3 mm strip as on a +3 mm board. Built in the frame of a +3 mm stretch (block and
# MCU zone keep their coordinates, the top goes 3 mm up), then the bottom 3 mm come off (step 15).
#  1. stretch.py       everything above y 72 (bulk caps, J4/J5, H1/H2, outline) up by 3 mm; the outline only above
#                      y 67.9: the shoulders at the clamp plate screws (y 68-71.5) stay with the block (owner)
#  2. stretch_zones.py tops of the F.Cu node zones and GND strips up to y 72.25, VDC cut there; rev0 0603s parked
#  3. sch_rev01_s3.py  snubber R one 1206 0.47 Ohm, snubber C standard 0805 pads, no second 1206 per phase
#  4. lay_P4.py        strip plan data/strip_plan_shift3.json, STRIP_S3=1; the plan was made on the board after step 2
#                      with C92 / C95 / C96 parked as well (their pads cut the VDC fill where the new 0603s go):
#                      JOINT06=C C06FILL=1 NOCER1=1 NOCER2=1 MISS=300,300,20 CANY=66.13 RKIND=R1206H CKIND=C0805S
#                      XB1=153.5 XC1=135.0 strip_plan.py board out.json
#  5. lay_P4b.py       review round 2 (X pads 0.5 mm, VDC on B.Cu in the strip, B.Mask off the slots), STRIP_S3=1
#  6-14.               as plus4.sh steps 6-15: octo, lay_P4c, sch_f, lay_P4d (STRIP_DY=3), lay_P4e, sch_g / lay_P4f,
#                      sch_h / lay_P4g (SNUB2X=0, STRIP_DY=3), lay_P4h
# 15. lay_S3c.py       the bottom edge 3 mm up (board length as rev0.1-gnd); U7 to B.Cu, the U6 input parts up
# 16. kicad-cli        refill zones, save, DRC with schematic parity (run_drc.sh on a copy, then copy the board back)
set -e
P=$(cd "$1" && pwd); T=$(cd "$(dirname "$0")" && pwd); TMP=$(mktemp -d)
STRETCH_YEDGE=67.9 python3 -B "$T/stretch.py" "$P/Power.kicad_pcb" "$TMP/s1.kicad_pcb" 72 3
KEEP0603=1 python3 -B "$T/stretch_zones.py" "$TMP/s1.kicad_pcb" "$TMP/s2.kicad_pcb" 72.25
python3 -B "$T/sch_rev01_s3.py" "$P"
STRIP_S3=1 python3 -B "$T/lay_P4.py" "$TMP/s2.kicad_pcb" "$P/Power.kicad_pcb" "$T/data/strip_plan_shift3.json" "$T/data/sch_e_uuids.json"
STRIP_S3=1 python3 -B "$T/lay_P4b.py" "$P/Power.kicad_pcb"
python3 -B "$T/octo.py" "$P/Power.kicad_pcb" "$T"
python3 -B "$T/lay_P4c.py" "$P/Power.kicad_pcb"
python3 -B "$T/sch_rev01_f.py" "$P"
STRIP_DY=3 python3 -B "$T/lay_P4d.py" "$P/Power.kicad_pcb"
STRIP_YT=72.25 python3 -B "$T/lay_P4e.py" "$P/Power.kicad_pcb"
python3 -B "$T/sch_rev01_g.py" "$P" "$T"
python3 -B "$T/lay_P4f.py" "$P/Power.kicad_pcb" "$T"
SNUB2X=0 python3 -B "$T/sch_rev01_h.py" "$P" "$T"
STRIP_DY=3 python3 -B "$T/lay_P4g.py" "$P/Power.kicad_pcb" "$T"
python3 -B "$T/lay_P4h.py" "$P/Power.kicad_pcb"
[ -f "$T/lay_S3c.py" ] && python3 -B "$T/lay_S3c.py" "$P/Power.kicad_pcb" "$T"
rm -rf "$TMP"
