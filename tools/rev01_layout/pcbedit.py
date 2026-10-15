"""Minimal text editor for KiCad 10 .kicad_pcb top-level segments and vias (no pcbnew)."""
import re, uuid

SEG_RE = re.compile(r'\t\(segment\n\t\t\(start ([\d.\-]+) ([\d.\-]+)\)\n\t\t\(end ([\d.\-]+) ([\d.\-]+)\)\n'
                    r'\t\t\(width ([\d.]+)\)\n\t\t\(layer "([^"]+)"\)\n\t\t\(net "([^"]*)"\)\n\t\t\(uuid "([^"]+)"\)\n\t\)\n')

def fmt(v):
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"

def seg_text(x1, y1, x2, y2, w, layer, net, uid=None):
    return (f'\t(segment\n\t\t(start {fmt(x1)} {fmt(y1)})\n\t\t(end {fmt(x2)} {fmt(y2)})\n\t\t(width {fmt(w)})\n'
            f'\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{uid or uuid.uuid4()}")\n\t)\n')

def via_text(x, y, net, size=0.6, drill=0.3, uid=None):
    return (f'\t(via\n\t\t(at {fmt(x)} {fmt(y)})\n\t\t(size {fmt(size)})\n\t\t(drill {fmt(drill)})\n'
            f'\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{uid or uuid.uuid4()}")\n\t)\n')

class Board:
    def __init__(self, path):
        self.path = path
        self.s = open(path, encoding="utf-8").read()
        self.added = []

    def segments(self, net=None, layer=None):
        for m in SEG_RE.finditer(self.s):
            x1, y1, x2, y2, w = map(float, m.groups()[:5])
            if (net is None or m.group(7) == net) and (layer is None or m.group(6) == layer):
                yield dict(x1=x1, y1=y1, x2=x2, y2=y2, w=w, layer=m.group(6), net=m.group(7), uuid=m.group(8),
                           span=m.span())

    def find_seg(self, net, layer, a, b, tol=1e-3):
        hits = []
        for g in self.segments(net, layer):
            p, q = (g["x1"], g["y1"]), (g["x2"], g["y2"])
            for u, v in ((p, q), (q, p)):
                if abs(u[0]-a[0]) < tol and abs(u[1]-a[1]) < tol and abs(v[0]-b[0]) < tol and abs(v[1]-b[1]) < tol:
                    hits.append(g)
        if len(hits) != 1:
            raise ValueError(f"segment {net} {layer} {a}-{b}: {len(hits)} matches")
        return hits[0]

    def replace_seg(self, g, new_text):
        i, j = g["span"]
        self.s = self.s[:i] + new_text + self.s[j:]

    def set_layer(self, net, layer, a, b, new_layer):
        g = self.find_seg(net, layer, a, b)
        self.replace_seg(g, seg_text(g["x1"], g["y1"], g["x2"], g["y2"], g["w"], new_layer, net, g["uuid"]))

    def split(self, net, layer, a, b, p, layer_a, layer_b):
        """Split segment a-b at point p: a-p on layer_a, p-b on layer_b."""
        g = self.find_seg(net, layer, a, b)
        self.replace_seg(g, seg_text(a[0], a[1], p[0], p[1], g["w"], layer_a, net, g["uuid"])
                            + seg_text(p[0], p[1], b[0], b[1], g["w"], layer_b, net))

    def add_seg(self, a, b, w, layer, net):
        self.added.append(seg_text(a[0], a[1], b[0], b[1], w, layer, net))

    def add_via(self, p, net, size=0.6, drill=0.3):
        self.added.append(via_text(p[0], p[1], net, size, drill))

    def save(self, path=None):
        s = self.s
        if self.added:
            k = s.find("\n\t(segment\n") + 1          # insert new items before the first segment
            s = s[:k] + "".join(self.added) + s[k:]
        open(path or self.path, "w", encoding="utf-8").write(s)

# ---------------------------------------------------------------- footprints / deletions
VIA_RE = re.compile(r'\t\(via\n(?:\t\t[^\n]*\n)+?\t\)\n')

def _fp_span(s, ref):
    i = s.find(f'(property "Reference" "{ref}"')
    if i < 0: raise KeyError(ref)
    a = s.rfind("\n\t(footprint ", 0, i) + 1; d = 0
    for k in range(a, len(s)):
        if s[k] == "(": d += 1
        elif s[k] == ")":
            d -= 1
            if d == 0: return a, k + 1
    raise ValueError(ref)

def _move_fp(self, ref, x, y, rot=None):
    a, b = _fp_span(self.s, ref); blk = self.s[a:b]
    m = re.search(r'\n\t\t\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)', blk)
    old = float(m.group(3) or 0); new = old if rot is None else rot
    head = f'\n\t\t(at {fmt(x)} {fmt(y)}' + (f' {fmt(new)}' if abs(new) > 1e-9 else '') + ')'
    blk = blk[:m.start()] + head + blk[m.end():]
    if abs(new - old) > 1e-9:
        start = m.start() + len(head)
        def fix(mm):
            ang = float(mm.group(3) or 0) - old + new
            ang = (ang + 180) % 360 - 180
            return f'(at {mm.group(1)} {mm.group(2)}' + (f' {fmt(ang)}' if abs(ang) > 1e-9 else '') + ')'
        blk = blk[:start] + re.sub(r'\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)', fix, blk[start:]) 
    self.s = self.s[:a] + blk + self.s[b:]

def _vias(self, net=None):
    for m in VIA_RE.finditer(self.s):
        b = m.group(0)
        at = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)\)', b); nm = re.search(r'\(net "([^"]*)"\)', b)
        n = nm.group(1) if nm else ""
        if net is None or n == net:
            yield dict(x=float(at.group(1)), y=float(at.group(2)), size=float(re.search(r'\(size ([\d.]+)\)', b).group(1)),
                       drill=float(re.search(r'\(drill ([\d.]+)\)', b).group(1)), net=n, span=m.span())

def _del_vias(self, pred):
    spans = [v["span"] for v in self.vias() if pred(v)]
    for a, b in sorted(spans, reverse=True): self.s = self.s[:a] + self.s[b:]
    return len(spans)

def _del_segs(self, pred):
    spans = [g["span"] for g in self.segments() if pred(g)]
    for a, b in sorted(spans, reverse=True): self.s = self.s[:a] + self.s[b:]
    return len(spans)

def _track(self, pts, w, layer, net):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]): self.add_seg((x1, y1), (x2, y2), w, layer, net)

Board.move_fp = _move_fp; Board.vias = _vias; Board.del_vias = _del_vias; Board.del_segs = _del_segs; Board.track = _track

def _flip_fp(self, ref):
    """Move a front footprint to the back: layers F.* -> B.*, local y mirrored, relative angles negated, texts mirrored."""
    a, b = _fp_span(self.s, ref); blk = self.s[a:b]
    m = re.search(r'\n\t\t\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)', blk)
    r = float(m.group(3) or 0)
    head_end = m.end()
    body = blk[head_end:]
    body = re.sub(r'\((start|end|xy|mid|center) ([\d.\-]+) ([\d.\-]+)\)',
                  lambda mm: f'({mm.group(1)} {mm.group(2)} {fmt(-float(mm.group(3)))})', body)
    def fat(mm):
        x, y = mm.group(1), float(mm.group(2)); ang = float(mm.group(3) or 0)
        rel = ang - r; new = -rel + r; new = (new + 180) % 360 - 180
        return f'(at {x} {fmt(-y)}' + (f' {fmt(new)}' if abs(new) > 1e-9 else '') + ')'
    body = re.sub(r'\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)', fat, body)
    body = re.sub(r'"F\.(Cu|Mask|Paste|SilkS|Fab|CrtYd|Adhes)"', r'"B.\1"', body)
    body = re.sub(r'(\(effects\n(\t+)\(font\n(?:\2\t[^\n]*\n)+?\2\)\n)(?!\2\(justify)', lambda mm: mm.group(1) + mm.group(2) + '(justify mirror)\n', body)
    body = re.sub(r'\(justify ((?:left|right|top|bottom| )*)\)', lambda mm: f'(justify {mm.group(1).strip()} mirror)'.replace("  ", " ") if "mirror" not in mm.group(0) else mm.group(0), body)
    head = blk[:head_end].replace('(layer "F.Cu")', '(layer "B.Cu")', 1)
    self.s = self.s[:a] + head + body + self.s[b:]
Board.flip_fp = _flip_fp

def _keepout(self, layer, pts, name="", pour=True, tracks=False, vias=False):
    """Rule area on `layer`: by default forbids copper pour only."""
    a = lambda b: "not_allowed" if b else "allowed"
    xy = " ".join(f"(xy {fmt(x)} {fmt(y)})" for x, y in pts)
    self.added_zones = getattr(self, "added_zones", [])
    self.added_zones.append(
        f'\t(zone\n\t\t(layer "{layer}")\n\t\t(uuid "{uuid.uuid4()}")\n\t\t(name "{name}")\n\t\t(hatch edge 0.5)\n'
        f'\t\t(connect_pads\n\t\t\t(clearance 0)\n\t\t)\n\t\t(min_thickness 0.25)\n\t\t(filled_areas_thickness no)\n'
        f'\t\t(keepout\n\t\t\t(tracks {a(tracks)})\n\t\t\t(vias {a(vias)})\n\t\t\t(pads allowed)\n\t\t\t(copperpour {a(pour)})\n'
        f'\t\t\t(footprints allowed)\n\t\t)\n\t\t(placement\n\t\t\t(enabled no)\n\t\t\t(sheetname "")\n\t\t)\n'
        f'\t\t(fill\n\t\t\t(thermal_gap 0.5)\n\t\t\t(thermal_bridge_width 0.5)\n\t\t)\n'
        f'\t\t(polygon\n\t\t\t(pts\n\t\t\t\t{xy}\n\t\t\t)\n\t\t)\n\t)\n')
_orig_save = Board.save
def _save2(self, path=None):
    z = getattr(self, "added_zones", [])
    if z:
        k = self.s.find("\n\t(zone\n") + 1
        self.s = self.s[:k] + "".join(z) + self.s[k:]; self.added_zones = []
    _orig_save(self, path)
Board.keepout = _keepout; Board.save = _save2
