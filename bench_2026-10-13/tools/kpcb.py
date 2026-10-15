# Minimal reader of a KiCad 10 .kicad_pcb (S-expressions), for layout_figures.py. Read-only.
"""Minimal .kicad_pcb reader: footprints (ref, value, layer, pos, rot, pads with abs positions and nets), segments,
vias, zones (net, layers, outline bbox), net names."""
import re, math, sys

def tokenize(s):
    for m in re.finditer(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', s):
        t = m.group(0)
        yield t

def parse(s):
    stack = [[]]
    for t in tokenize(s):
        if t == "(":
            stack.append([])
        elif t == ")":
            x = stack.pop(); stack[-1].append(x)
        else:
            stack[-1].append(t[1:-1] if t.startswith('"') else t)
    return stack[0][0]

def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]

def first(node, key):
    r = find(node, key); return r[0] if r else None

def load(path):
    root = parse(open(path, encoding="utf-8").read())
    nets = {}
    for n in find(root, "net"):
        if len(n) >= 3: nets[n[1]] = n[2]
    fps = []
    for f in find(root, "footprint"):
        layer = first(f, "layer")[1]
        at = first(f, "at"); x, y = float(at[1]), float(at[2]); rot = float(at[3]) if len(at) > 3 else 0.0
        props = {p[1]: p[2] for p in find(f, "property") if len(p) > 2}
        ref = props.get("Reference", "?"); val = props.get("Value", "?")
        pads = []
        for p in find(f, "pad"):
            pat = first(p, "at"); px, py = float(pat[1]), float(pat[2])
            a = math.radians(-rot)
            ax = x + px*math.cos(a) - py*math.sin(a); ay = y + px*math.sin(a) + py*math.cos(a)
            netn = first(p, "net")
            net = (netn[2] if len(netn) > 2 else nets.get(netn[1], netn[1])) if netn else ""
            size = first(p, "size")
            pads.append(dict(name=p[1], type=p[2], shape=p[3], x=ax, y=ay, net=net,
                             w=float(size[1]) if size else 0, h=float(size[2]) if size else 0,
                             layers=first(p, "layers")[1:] if first(p, "layers") else []))
        fps.append(dict(ref=ref, val=val, layer=layer, x=x, y=y, rot=rot, pads=pads, lib=f[1] if len(f) > 1 else ""))
    segs = []
    for sg in find(root, "segment"):
        st, en = first(sg, "start"), first(sg, "end")
        netn = first(sg, "net"); net = (netn[2] if len(netn) > 2 else nets.get(netn[1], netn[1])) if netn else ""
        segs.append(dict(x1=float(st[1]), y1=float(st[2]), x2=float(en[1]), y2=float(en[2]),
                         w=float(first(sg, "width")[1]), layer=first(sg, "layer")[1], net=net))
    vias = []
    for v in find(root, "via"):
        at = first(v, "at"); netn = first(v, "net")
        net = (netn[2] if len(netn) > 2 else nets.get(netn[1], netn[1])) if netn else ""
        vias.append(dict(x=float(at[1]), y=float(at[2]), d=float(first(v, "drill")[1]), net=net,
                         layers=first(v, "layers")[1:] if first(v, "layers") else []))
    zones = []
    for z in find(root, "zone"):
        netn = first(z, "net_name") or first(z, "net"); net = netn[-1] if netn else ""
        lay = first(z, "layers") or first(z, "layer")
        layers = lay[1:] if lay else []
        poly = first(z, "polygon"); pts = first(poly, "pts") if poly else None
        xy = [(float(p[1]), float(p[2])) for p in find(pts, "xy")] if pts else []
        fills = []
        for fp_ in find(z, "filled_polygon"):
            l = first(fp_, "layer"); pts2 = first(fp_, "pts")
            fills.append((l[1] if l else "", [(float(p[1]), float(p[2])) for p in find(pts2, "xy")]))
        zones.append(dict(net=net, layers=layers, outline=xy, fills=fills))
    return dict(nets=nets, fps=fps, segs=segs, vias=vias, zones=zones, root=root)
