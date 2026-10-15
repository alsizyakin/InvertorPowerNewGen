# rev0.1 layout plan (working notes)

Tools (scratchpad/tools): pcbedit.py (segments/vias text), geom.py (placement checker, body = courtyard-0.25),
plotblk.py (layer plot), gndconn.py (GND islands), bridges.py (GND bridge cross-sections), netdiff.py, schedit.py.
pcbnew API segfaults -> text edits + `kicad-cli pcb drc --refill-zones --save-board` in a project copy.
courtyards_overlap is IGNORED in project DRC -> body overlap must be checked by geom.py.

## Passages between block (y<=91.5) and drivers (y~104-110)
- C: x 120.8-126.75 (notch..J1). In1 GND bridge 2.7, In4 1.15 (split by VDC->J6 track). F.Cu/In2/B.Cu = node (load).
- J1-J2: x 134.75-138.75. In4 0.35. In3: HO C (x135.25), LO B (x137.5).
- J2-J3: x 146.75-150.75. In3: HO B, +3.3V(147.5), NTC B(148.25), LO A(150).
- A: x 158.75-164.76. In4 0.65. In3: HO A, +3.3/NTC A (161.25/162).

## Routing concept
- HO+SW pair: In3 in passages (C via J1-J2, B via J2-J3, A via passage A), vias to In4 below block,
  In4 transverse along y~89.8-90.2 under bottom of own VDC column (C, B), up node column lane:
  C lane HO x126.05 / SW x126.85; B lane ~x143.4-144.4; A lane ~x160.4-161.7.
- NetTie between upper/lower HS, middle row: NT pad2 on R_gs node pad. C: NT1 at (127.09,81.5) rot0.
- R_g,i of HS on node side, vertical: C R23 at (125.55,81.5) rot90 (pad2 gate top, pad1 HO bottom);
  HO via (125.55,83.25); SW via (126.59,82.4). R1 (lower HS) bottom row (125.55,90.25) rot90 + HO via.
- TH1 moved to (123.75,81.75) rot90, its vias at x124.55 (y 80.84 NTC / 82.66 +3.3). TH lines In1 in block,
  transition to In3 below block staggered (~(124.75,91.9),(125.5,92.6)).
- C_gs: C100 below R19 at (128.5,82.55) rot180 (pad2 node left, pad1 gate right). C101 below R26 similar.
- LO: in block In4 (existing In3 paths moved), transition vias just below y 91.5 placed not to cut In1/In4 junction.
- VDC->J6: remove In4 track; new via in VDC column bottom (~128.8,91.1) -> In2 track down passage C (lane x~121.5)
  to J6 THT pads.
- Ceramics (F.Cu, 1206): HS-drain column middle & bottom rows (freed by R_g HS move) + top band y72-74.6 / wedges.
- Snubbers: TBD by space (LS at strip|node boundary, HS at node|VDC boundary).
- Probe: tips on existing pads, ground = mask-opening spots on reference copper ~5 mm away.

## Acceptance checks per step
DRC (0 err except known), GND one island (gndconn), bridges (bridges.py) vs rev0, In3 no segments in block
(x116.2-169.2, y72-91.5), via counts Р8 (strip GND 92/37/33, near-S 29/31/29, node 16/74/55), lengths LO <= rev0.

## Decisions taken during phase C (script tools/lay_C1.py, applied only to scratch copies so far)
- R1 (lower HS R_g,i) stays at its rev0 place in the VDC column bottom row; HO via (133.75,90.65) on the In4 HO run.
  Upper HS: R23 node side (125.55,81.5) rot90, NT1 (127.09,81.5), C100 (128.5,82.55) rot180, C101 (128.5,91.3) rot180.
- TH1 -> (123.75,81.75) rot90, vias x124.55. TH lines In1: NTC (124.55,80.84)->(127.75,80.84)->(127.75,90.1)->(125.6,90.1)
  ->via(125.6,92.35); +3.3 (124.55,82.66)->(124.55,83.95)->(127.15,83.95)->(127.15,89.5)->(124.9,89.5)->via(124.9,91.85);
  old In3 lines start at the transitions.
- LO C: whole in-block path on In4, then (122,91)->(124,91.05)->(124,96.1) via -> In3 (123.25,96.1)->(123.25,97.5)->old.
- VDC->J6: In4 track removed; new In2 0.4 mm track (129,91)->(124,91)->(124,94.6)->(123.25,95.35)->(123.25,97.6)
  ->(121.6,97.6)->(121.6,102.6)->(119.95,104.25)->J6.1. In4 bridge C 1.15 -> 1.85 mm.
- C pair below block: In4 east runs SW y89.85 (to x134.5), HO y90.65 (to 133.75). Passage J1-J2 lane x~135.25 is only
  0.85 mm wide (node B via column x136.25/136.75) -> stacked pair: HO on In3, SW on In4 under it. HO transition via
  ~(134.4,92.6). In4 J1-J2 sliver (0.35) will be lost -> argue sum of bridges (In4 C gained 0.7).
- Driver side: no F.Cu room (boot cap to next driver's inputs ~1 mm). HO off-branch on B.Cu x135-138.3 y104.6-109.4
  (flip implemented: pcbedit.flip_fp, verified by render). LO branch / HI-LI RC: left of D4, crowded -> B.Cu or 0402.
- Remaining for C: driver clusters, pair bottom end, HI/LI, C_gs LS (C102,C103), snubbers, ceramics (§4 not in schematic yet).
