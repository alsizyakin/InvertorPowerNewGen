"""Footprint text helpers for KiCad 10 .kicad_pcb (no pcbnew):
  clone_fp     - copy a footprint block under a new reference/schematic path, fresh uuids;
  swap_geometry- replace graphics and pads of a footprint by a stock library footprint, keeping its
                 properties, schematic link, attributes and the pad nets (by pad number);
  set_pad_clearance - local clearance on all pads of a footprint (zones keep it, P5: 0.5 mm at 72-84 V)."""
import re, uuid
import pcbedit

LIBDIR = "/usr/share/kicad/footprints"

def _span(s, ref): return pcbedit._fp_span(s, ref)

def _blocks(t, indent):
    """top-level child blocks of a footprint text at the given indent: [(start, end)]"""
    out = []
    for m in re.finditer(r'\n' + indent + r'\(', t):
        a = m.start() + 1 + len(indent); d = 0
        for k in range(a, len(t)):
            if t[k] == "(": d += 1
            elif t[k] == ")":
                d -= 1
                if d == 0: out.append((a, k + 1)); break
    return out

def _fresh_uuids(t):
    return re.sub(r'\(uuid "[^"]+"\)', lambda m: f'(uuid "{uuid.uuid4()}")', t)

def clone_fp(s, src_ref, new_ref, path, sheetname=None, value=None, pad_nets=None, at=None):
    a, b = _span(s, src_ref); blk = s[a:b]
    blk = _fresh_uuids(blk)
    blk = blk.replace(f'(property "Reference" "{src_ref}"', f'(property "Reference" "{new_ref}"', 1)
    blk = re.sub(r'\(path "[^"]+"\)', f'(path "{path}")', blk, count=1)
    if sheetname: blk = re.sub(r'\(sheetname "[^"]*"\)', f'(sheetname "{sheetname}")', blk, count=1)
    if value is not None: blk = re.sub(r'\(property "Value" "[^"]*"', f'(property "Value" "{value}"', blk, count=1)
    if pad_nets:
        for pn, net in pad_nets.items():
            blk = re.sub(r'(\(pad "' + re.escape(pn) + r'" (?:(?!\n\t\t\)).)*?\(net )"[^"]*"', r'\g<1>"' + net + '"', blk, count=1, flags=re.S)
    s = s[:b] + "\n" + blk + s[b:]
    return s

def _lib_body(lib_id):
    lib, name = lib_id.split(":")
    t = open(f"{LIBDIR}/{lib}.pretty/{name}.kicad_mod", encoding="utf-8").read()
    descr = re.search(r'\n\t\(descr "([^"]*)"\)', t).group(1); tags = re.search(r'\n\t\(tags "([^"]*)"\)', t).group(1)
    items = []
    for a, b in _blocks(t, "\t"):
        it = t[a:b]
        if re.match(r'\((fp_line|fp_rect|fp_circle|fp_arc|fp_poly|fp_text|pad|model)\b', it):
            it = "\n".join("\t" + ln for ln in it.split("\n"))[1:]          # one more indent level
            # add uuids to graphic items and pads (board files carry them)
            if not it.startswith("(model"):
                it = it[:-1].rstrip() + f'\n\t\t\t(uuid "{uuid.uuid4()}")\n\t\t)'
            items.append(it)
    return descr, tags, items

def swap_geometry(s, ref, lib_id):
    """footprint `ref` must be at rotation 0 (move it with Board.move_fp first)"""
    a, b = _span(s, ref); blk = s[a:b]
    assert re.search(r'\n\t\t\(at [\d.\-]+ [\d.\-]+\)', blk), f"{ref}: rotate to 0 first"
    nets = dict(re.findall(r'\(pad "([^"]+)" .*?\(net "([^"]*)"\)', blk, re.S))
    descr, tags, items = _lib_body(lib_id)
    blk, n = re.subn(r'^(\t?)\(footprint "[^"]+"', lambda m: f'{m.group(1)}(footprint "{lib_id}"', blk); assert n == 1
    blk = re.sub(r'\n\t\t\(descr "[^"]*"\)', f'\n\t\t(descr "{descr}")', blk, count=1)
    blk = re.sub(r'\n\t\t\(tags "[^"]*"\)', f'\n\t\t(tags "{tags}")', blk, count=1)
    blk = re.sub(r'(\(property "Footprint" )"[^"]*"', r'\g<1>"' + lib_id + '"', blk, count=1)
    # drop old geometry
    kids = _blocks(blk, "\t\t")
    keep = []; last = 0
    for x, y in kids:
        if re.match(r'\((fp_line|fp_rect|fp_circle|fp_arc|fp_poly|fp_text|pad|model)\b', blk[x:y]):
            keep.append(blk[last:x].rstrip("\t").rstrip("\n")); last = y
    keep.append(blk[last:])
    blk = "".join(keep)
    new = []
    for it in items:
        if it.startswith("(pad"):
            pn = re.match(r'\(pad "([^"]+)"', it).group(1)
            if pn in nets:
                it = it.replace("\n\t\t\t(uuid", f'\n\t\t\t(net "{nets[pn]}")\n\t\t\t(pintype "passive")\n\t\t\t(uuid', 1)
        new.append("\t\t" + it)
    k = blk.rfind("\n\t\t(embedded_fonts")
    if k < 0: k = blk.rfind("\n\t)")
    blk = blk[:k] + "\n" + "\n".join(new) + blk[k:]
    return s[:a] + blk + s[b:]

def set_pad_clearance(s, ref, cl):
    """cl: one value for all pads, or {pad number: value}"""
    a, b = _span(s, ref); blk = s[a:b]
    def f(m):
        p = m.group(0)
        c = cl.get(re.match(r'\(pad "([^"]+)"', p).group(1)) if isinstance(cl, dict) else cl
        if c is None: return p
        p = re.sub(r'\n\t\t\t\(clearance [\d.]+\)', '', p)
        return p.replace("\n\t\t\t(uuid", f"\n\t\t\t(clearance {c})\n\t\t\t(uuid", 1)
    blk = re.sub(r'\(pad "[^"]+" .*?\n\t\t\)', f, blk, flags=re.S)
    return s[:a] + blk + s[b:]

def set_attr(s, ref, value=None, pn=None, dnp=None):
    a, b = _span(s, ref); blk = s[a:b]
    if value is not None: blk = re.sub(r'\(property "Value" "[^"]*"', f'(property "Value" "{value}"', blk, count=1)
    if pn is not None: blk = re.sub(r'\(property "Description P/N" "[^"]*"', f'(property "Description P/N" "{pn}"', blk, count=1)
    if dnp is not None:
        m = re.search(r'\(attr ([^)]*)\)', blk); w = [x for x in m.group(1).split() if x != "dnp"] + (["dnp"] if dnp else [])
        blk = blk[:m.start()] + f'(attr {" ".join(w)})' + blk[m.end():]
    return s[:a] + blk + s[b:]
