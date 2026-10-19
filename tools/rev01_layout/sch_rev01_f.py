"""Owner's decision 2026-10-19: current sense amplifiers U4, U9, U12 AD8418 -> INA240A1 (SOIC-8, pin to pin:
1 IN-, 2 GND, 3 REF2, 4 NC, 5 OUT, 6 VS, 7 REF1, 8 IN+; gain 20 V/V as before; common mode -4...80 V, abs. max 90 V,
against 70 V of AD8418). The stock INA240A1D symbol has other pin positions, so a project symbol Logic_My:INA240A1D is
made from the AD8418 drawing; the sheets Current_Sensor_1..3 point to it. The same fields go onto the board
footprints, so the board stays in parity without Update PCB from Schematic.
Owner 2026-10-19 (round 2): INA240A1 stays; for a 72 V bus it is replaced by INA241A2 (SOIC-8, same pins, 20 V/V,
-5...110 V) - written into the Replacement field. Usage: sch_rev01_f.py <project dir>"""
import sys, os, re

d = sys.argv[1]
SHEETS = ("Current_Sensor_1.kicad_sch", "Current_Sensor_2.kicad_sch", "Current_Sensor_3.kicad_sch")
REFS = ("U4", "U9", "U12")
DS = "https://www.ti.com/lit/ds/symlink/ina240.pdf"
DESC = ("-4...80V Bidirectional, Zero Drift, Current Sense Amplifier With Enhanced PWM Rejection, 20V/V gain, "
        "bandwidth 400kHz, VS=2.7V~5.5V, SOIC-8 (pin compatible with AD8418)")
PN = "INA240A1DR"
REPL = "INA241A2DR при VDC 72 В"
FP = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"

def block(s, i):
    dep = 0
    for k in range(i, len(s)):
        if s[k] == "(": dep += 1
        elif s[k] == ")":
            dep -= 1
            if dep == 0: return i, k + 1
    raise ValueError("unbalanced")

def sub1(pat, rep, t):
    t2, n = re.subn(pat, lambda m: rep, t, count=1); assert n == 1, pat; return t2

def new_cache(old):
    """Cached lib symbol of the sheets (flattened AD8418) -> Logic_My:INA240A1D."""
    t = old.replace('(symbol "Amplifier_Current:AD8418"', '(symbol "Logic_My:INA240A1D"', 1)
    t = t.replace('(symbol "AD8418_', '(symbol "INA240A1D_')
    t = sub1(r'\(property "Value" "AD8418"', '(property "Value" "INA240A1D"', t)
    t = sub1(r'\(property "Footprint" ""', f'(property "Footprint" "{FP}"', t)
    t = sub1(r'\(property "Datasheet" "[^"]*"', f'(property "Datasheet" "{DS}"', t)
    t = sub1(r'\(property "Description" "[^"]*"', f'(property "Description" "{DESC}"', t)
    t = sub1(r'\(property "ki_keywords" "[^"]*"', '(property "ki_keywords" "current sense amplifier bidirectional PWM rejection motor inline"', t)
    t = sub1(r'\(property "ki_fp_filters" "[^"]*"', '(property "ki_fp_filters" "SOIC*3.9x4.9mm*P1.27mm*"', t)
    return t

def fields(blk):
    blk = sub1(r'\(property "Datasheet" "[^"]*"', f'(property "Datasheet" "{DS}"', blk)
    blk = sub1(r'\(property "Description" "[^"]*"', f'(property "Description" "{DESC}"', blk)
    blk = sub1(r'\(property "Product Name" "[^"]*"', f'(property "Product Name" "{PN}"', blk)
    return sub1(r'\(property "Replacement" "[^"]*"', f'(property "Replacement" "{REPL}"', blk)

cache = None
for fn in SHEETS:
    p = os.path.join(d, fn); s = open(p, encoding="utf-8").read()
    if 'lib_id "Logic_My:INA240A1D"' not in s:
        i = s.find('\t\t(symbol "Amplifier_Current:AD8418"\n'); assert i > 0, fn
        a, b = block(s, i + 2)
        cache = new_cache(s[a:b])
        s = s[:a] + cache + s[b:]
        s = sub1(r'\(lib_id "Amplifier_Current:AD8418"\)', '(lib_id "Logic_My:INA240A1D")', s)
    i = s.find('(lib_id "Logic_My:INA240A1D")'); a = s.rfind("\n\t(symbol\n", 0, i) + 1; a, b = block(s, a + 1)
    s = s[:a] + fields(s[a:b]) + s[b:]
    open(p, "w", encoding="utf-8").write(s)

# project library: the same symbol, one indent level less
lib = os.path.join(d, "Lib", "Logic_My.kicad_sym"); s = open(lib, encoding="utf-8").read()
if '(symbol "INA240A1D"' not in s and cache:
    t = cache.replace('(symbol "Logic_My:INA240A1D"', '(symbol "INA240A1D"', 1)
    t = "\n".join(ln[1:] if ln.startswith("\t") else ln for ln in t.split("\n"))
    k = s.rfind("\n\t(symbol \""); k = block(s, k + 2)[1]
    s = s[:k] + "\n" + t + s[k:]
    open(lib, "w", encoding="utf-8").write(s)

# board footprints: the same fields
p = os.path.join(d, "Power.kicad_pcb"); s = open(p, encoding="utf-8").read()
for ref in REFS:
    i = s.find(f'(property "Reference" "{ref}"'); assert i > 0, ref
    a = s.rfind("\n\t(footprint ", 0, i) + 1; a, b = block(s, a + 1)
    s = s[:a] + fields(s[a:b]) + s[b:]
open(p, "w", encoding="utf-8").write(s)
print("U4, U9, U12: AD8418 -> INA240A1 (Logic_My:INA240A1D), replacement INA241A2 at 72 V; schematic and board")
