"""REV0_1_TASK Д1, Д2 (stand 16.10): C_gs C100-C111 -> 10 nF 50 V C0G 0603, fitted; D_off D30-D35 -> DNP.
Edits the schematic sheets and mirrors the same value/attribute changes on the board footprints, so the board
stays in parity without Update PCB from Schematic. Usage: sch_rev01_d.py <project dir>"""
import sys, os, re

d = sys.argv[1]

def sym_edit(fn, ref, fn_blk):
    p = os.path.join(d, fn); s = open(p, encoding="utf-8").read()
    i = s.find(f'(property "Reference" "{ref}"'); assert i > 0, ref
    a = s.rfind("\n\t(symbol\n", 0, i) + 1; dep = 0
    for k in range(a, len(s)):
        if s[k] == "(": dep += 1
        elif s[k] == ")":
            dep -= 1
            if dep == 0: break
    blk = fn_blk(s[a:k + 1]); open(p, "w", encoding="utf-8").write(s[:a] + blk + s[k + 1:])

def sub1(pat, rep, t):
    t2, n = re.subn(pat, rep, t, count=1); assert n == 1, pat; return t2

# Д1: one symbol per position on Phase_A (3 sheet instances each -> 12 parts)
cgs = lambda t: sub1(r'\(dnp yes\)', '(dnp no)', sub1(r'\(property "Value" "4\.7n"', '(property "Value" "10n 50V C0G"',
                     sub1(r'\(property "Description P/N" "Capacitor SMD 50V"', '(property "Description P/N" "Capacitor SMD 50V C0G"', t)))
for ref in ("C100", "C101", "C102", "C103"): sym_edit("Phase_A.kicad_sch", ref, cgs)
# Д2: D_off on Driver (3 sheet instances each -> 6 parts)
doff = lambda t: sub1(r'\(dnp no\)', '(dnp yes)', t)
for ref in ("D30", "D33"): sym_edit("Driver.kicad_sch", ref, doff)

# board: the same on the footprints
p = os.path.join(d, "Power.kicad_pcb"); s = open(p, encoding="utf-8").read()
def fp_edit(s, ref, fn_blk):
    i = s.find(f'(property "Reference" "{ref}"'); assert i > 0, ref
    a = s.rfind("\n\t(footprint ", 0, i) + 1; dep = 0
    for k in range(a, len(s)):
        if s[k] == "(": dep += 1
        elif s[k] == ")":
            dep -= 1
            if dep == 0: break
    return s[:a] + fn_blk(s[a:k + 1]) + s[k + 1:]
cgs_fp = lambda t: sub1(r'\(attr smd dnp\)', '(attr smd)', sub1(r'\(property "Value" "4\.7n"', '(property "Value" "10n 50V C0G"',
                        sub1(r'\(property "Description P/N" "Capacitor SMD 50V"', '(property "Description P/N" "Capacitor SMD 50V C0G"', t)))
for n in range(100, 112): s = fp_edit(s, f"C{n}", cgs_fp)
for n in range(30, 36): s = fp_edit(s, f"D{n}", lambda t: sub1(r'\(attr smd\)', '(attr smd dnp)', t))
open(p, "w", encoding="utf-8").write(s)
print("Д1/Д2 written")
