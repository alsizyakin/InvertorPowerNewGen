"""rev0.1 schematic, round 3: loop ceramics §4 — one 1206 per phase fits (middle row of the HS-drain column);
the other three per phase (C125-C127, C129-C131, C133-C135) are removed with their wires (Р6: as space allows).
Usage: sch_rev01_c.py <project dir> <tools dir>"""
import sys, os, re
sys.path.insert(0, sys.argv[2]); sys.dont_write_bytecode = True
from schedit import Sch, block_at, f
p = Sch(os.path.join(sys.argv[1], "Phase_A.kicad_sch"))
YT, YC, YB = 134.62, 137.16, 139.7
for x in (120.65, 135.89, 151.13):
    m = list(re.finditer(rf'\n\t\(symbol\n\t\t\(lib_id "Device:C_Small"\)\n\t\t\(at {re.escape(f(x))} {re.escape(f(YC))} 0\)', p.s))
    assert len(m) == 1, (x, len(m))
    a, b = block_at(p.s, m[0].start() + 1); p.s = p.s[:a-1] + p.s[b:]
for a, b in ((105.41, 120.65), (120.65, 135.89), (135.89, 151.13)):
    p.remove_wire(a, YT, b, YT); p.remove_wire(a, YB, b, YB)
for x in (120.65, 135.89):
    for y in (YT, YB):
        m = list(re.finditer(rf'\n\t\(junction\n\t\t\(at {re.escape(f(x))} {re.escape(f(y))}\)', p.s))
        assert len(m) == 1, (x, y, len(m))
        a, b = block_at(p.s, m[0].start() + 1); p.s = p.s[:a-1] + p.s[b:]
p.save()
print("round-3 schematic edits written")
