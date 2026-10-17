"""Review round 1, E8 (docs/reviews/03): the +3.3V plane on In2 (control part) 1 mm in from the left, right and bottom
board edges (GND planes In1/In3/In4 stay to the edge). Usage: lay_G3c.py board.kicad_pcb"""
import re, sys
fn = sys.argv[1]
s = open(fn, encoding="utf-8").read()
old = "(xy 169.25 104.25) (xy 169.25 144.5) (xy 116.25 144.5) (xy 116.25 104.25)"
new = "(xy 168.25 104.25) (xy 168.25 143.5) (xy 117.25 143.5) (xy 117.25 104.25)"
z = [m for m in re.finditer(r'\n\t\(zone\n.*?\n\t\)', s, re.S) if '(net "+3.3V")' in m.group(0) and '(layer "In2.Cu")' in m.group(0)]
assert len(z) == 1 and z[0].group(0).count(old) == 1
t = re.sub(r'\n\t\t\(filled_polygon.*?\n\t\t\)', '', z[0].group(0).replace(old, new), flags=re.S)
open(fn, "w", encoding="utf-8").write(s[:z[0].start()] + t + s[z[0].end():])
print("+3.3V In2 plane inset 1 mm from the edges")
