"""Variant 2 on the stretched board: raise the tops of the F.Cu node zones and GND strips to YTOP, cut VDC there,
drop C90/C93/C94 (rev0 0603, 'по месту') with their own short tracks and vias. Usage: ext.py in out YTOP"""
import re, sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(sys.argv[0]))); sys.dont_write_bytecode = True
fi, fo, YT = sys.argv[1], sys.argv[2], float(sys.argv[3])
s = open(fi, encoding="utf-8").read()
def fmt(v):
    t = f"{v:.6f}".rstrip("0").rstrip("."); return t if t not in ("-0", "") else "0"
def zone_edit(s, net, layer_sig, xr, fn):
    out = []; last = 0; n = 0
    for m in re.finditer(r'\n\t\(zone\n.*?\n\t\)', s, re.S):
        t = m.group(0)
        if f'(net "{net}")' not in t or layer_sig not in t: continue
        poly = re.search(r'\n\t\t\(polygon\n(.*?)\n\t\t\)', t, re.S)
        pts = [(float(a), float(b)) for a, b in re.findall(r'\(xy ([\d.\-]+) ([\d.\-]+)\)', poly.group(1))]
        if not (xr[0] - 0.01 <= min(p[0] for p in pts) and max(p[0] for p in pts) <= xr[1] + 0.01): continue
        new = fn(pts)
        body = "\n\t\t\t(pts\n" + "".join(f"\t\t\t\t(xy {fmt(x)} {fmt(y)})\n" for x, y in new) + "\t\t\t)"
        t2 = t[:poly.start(1)] + body[1:] + t[poly.end(1):]
        t2 = re.sub(r'\n\t\t\(filled_polygon.*?\n\t\t\)', '', t2, flags=re.S)
        out.append(s[last:m.start()]); out.append(t2); last = m.end(); n += 1
    out.append(s[last:]); assert n == 1, (net, xr, n); return "".join(out)
raise_top = lambda pts: [(x, YT if y in (74.25, 73.25) else y) for x, y in pts]
for net, xr in (("/Current_Sensor_3/Phase_IN", (121.25, 128.25)), ("/Current_Sensor_2/Phase_IN", (135.0, 145.25)),
                ("/Current_Sensor_1/Phase_IN", (155.25, 169.0))):
    s = zone_edit(s, net, '(layer "F.Cu")', xr, raise_top)
for xr in ((116.25, 121.25), (134.25, 138.25), (151.25, 155.25)):
    s = zone_edit(s, "GND", '"F.Cu" "B.Cu"', xr, raise_top)
def vdc(pts):
    # replace the block-top boundary between the HS drain columns by notches up to YT
    rep = {(163.0, 74.25): [(163.0, 74.25), (163.0, YT), (151.25, YT)], (151.25, 74.25): [(151.25, 74.25)],
           (146.0, 74.25): [(146.0, 74.25), (146.0, YT), (134.25, YT)], (134.25, 74.25): [(134.25, 74.25)],
           (129.0, 74.25): [(129.0, 74.25), (129.0, YT), (116.25, YT)], (116.25, 74.25): []}
    out = []
    for p in pts: out += rep.get(p, [p])
    return out
s = zone_edit(s, "VDC", '"F.Cu" "B.Cu"', (116.25, 169.25), vdc)
# drop C90, C93, C94 and their GND stubs/vias (KEEP0603=1: park them off the board instead, lay_P4.py places them)
KEEP = __import__("os").environ.get("KEEP0603") == "1"
for ref in (() if KEEP else ("C90", "C93", "C94")):
    m = re.search(r'\n\t\(footprint "[^"]+"\n(?:(?!\n\t\(footprint).)*?\(property "Reference" "' + ref + '"', s, re.S)
    a = m.start(); d = 0
    for k in range(a + 2, len(s)):
        if s[k] == "(": d += 1
        elif s[k] == ")":
            d -= 1
            if d == 0: break
    s = s[:a] + s[k + 1:]
import pcbedit
open(fo, "w", encoding="utf-8").write(s)
B = pcbedit.Board(fo)
if KEEP:
    for k, ref in enumerate(("C90", "C93", "C94")): B.move_fp(ref, 95.0, 110.0 + 3*k)
stub = lambda g: g["layer"] == "F.Cu" and g["net"] == "GND" and any(abs(g[k1] - a) < 0.02 and abs(g[k2] - b) < 0.02
        for k1, k2 in (("x1", "y1"), ("x2", "y2")) for a, b in ((118.89, 73.5), (118.25, 73.5), (141.89, 73.75), (141.25, 73.75)))
nseg = sum(1 for g in B.segments() if stub(g))
B.del_segs(stub)
B.del_vias(lambda v: v["net"] == "GND" and any(abs(v["x"] - a) < 0.02 and abs(v["y"] - b) < 0.02 for a, b in ((118.25, 73.5), (141.25, 73.75))))
B.save(); print("ok, stub segs removed:", nseg)
