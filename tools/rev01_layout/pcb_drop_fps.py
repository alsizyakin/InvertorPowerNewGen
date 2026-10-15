"""Remove footprints by reference from a .kicad_pcb (text). Usage: pcb_drop_fps.py board REF..."""
import sys, re
fn = sys.argv[1]; s = open(fn, encoding="utf-8").read()
for ref in sys.argv[2:]:
    i = s.find(f'(property "Reference" "{ref}"'); assert i > 0, ref
    a = s.rfind("\n\t(footprint ", 0, i)
    depth = 0; j = a + 1
    while True:
        c = s[j]
        if c == "(": depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0: break
        j += 1
    s = s[:a] + s[j+1:]
open(fn, "w", encoding="utf-8").write(s); print("removed", sys.argv[2:])
