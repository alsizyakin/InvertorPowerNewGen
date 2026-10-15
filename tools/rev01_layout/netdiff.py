"""Compare two KiCad netlists by net membership (pins), ignoring auto-generated net names: nets are matched by
their pin sets; reports added/removed components and changed connectivity."""
import sys, re
def load(fn):
    s = open(fn, encoding="utf-8").read()
    comps = {m.group(1): (m.group(2), m.group(3)) for m in re.finditer(
        r'\(comp\s*\(ref "([^"]+)"\)\s*\(value "([^"]*)"\)\s*(?:\(footprint "([^"]*)"\))?', s)}
    i = s.find("(nets"); nets = {}
    for m in re.finditer(r'\(net\s*\(code "?\d+"?\)\s*\(name "([^"]*)"\)(.*?)\n\t\t\)', s[i:], re.S):
        nets[m.group(1)] = frozenset(re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"', m.group(2)))
    return comps, nets
ca, na = load(sys.argv[1]); cb, nb = load(sys.argv[2])
print("components: +", sorted(set(cb) - set(ca), key=lambda r: (re.sub(r'\d', '', r), int(re.sub(r'\D', '', r) or 0))))
print("components: -", sorted(set(ca) - set(cb)))
for r in sorted(set(ca) & set(cb)):
    if ca[r] != cb[r]: print(f"  changed {r}: {ca[r]} -> {cb[r]}")
pin2net_a = {p: n for n, ps in na.items() for p in ps}; pin2net_b = {p: n for n, ps in nb.items() for p in ps}
sa = {ps for ps in na.values()}; sb = {ps for ps in nb.values()}
gone = [ps for ps in sa if ps not in sb]; new = [ps for ps in sb if ps not in sa]
print(f"nets: {len(na)} -> {len(nb)}; changed membership: {len(gone)} old / {len(new)} new")
for ps in sorted(new, key=lambda p: sorted(p)[0]):
    name = next(n for n, q in nb.items() if q == ps)
    old = {pin2net_a.get(p) for p in ps if p in pin2net_a}
    added = sorted(p for p in ps if pin2net_a.get(p) is None)
    print(f"  NEW {name}: {len(ps)} pins; from old nets {sorted(o for o in old if o)}; new pins {added[:12]}")
    if len(ps) < 14: print("       ", sorted(ps))
