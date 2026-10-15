"""Hide the reference of C103 (DNP C_gs next to the screw notch): its text crossed the board edge."""
import sys
fn = sys.argv[1]; s = open(fn, encoding="utf-8").read()
old = '(property "Reference" "C103"\n\t\t\t(at 0 -1.43 180)\n\t\t\t(layer "F.SilkS")\n'
assert s.count(old) == 1
s = s.replace(old, old + '\t\t\t(hide yes)\n')
open(fn, "w", encoding="utf-8").write(s); print("lay_SILK applied")
