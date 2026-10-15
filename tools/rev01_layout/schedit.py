"""Text editor for KiCad 10 sub-sheet .kicad_sch files: add symbols/wires/junctions/labels, move labels,
remove wires, change properties. Cached lib symbols are copied from other sheets or the stock library."""
import re, uuid

def U(): return str(uuid.uuid4())
def f(v):
    s = f"{v:.4f}".rstrip("0").rstrip("."); return "0" if s in ("-0", "") else s

def block_at(s, i):
    d = 0
    for k in range(i, len(s)):
        if s[k] == "(": d += 1
        elif s[k] == ")":
            d -= 1
            if d == 0: return i, k + 1
    raise ValueError("unbalanced")

def cached_symbol(path, name):
    s = open(path, encoding="utf-8").read()
    i = s.find(f'\t\t(symbol "{name}"\n')
    if i < 0: raise KeyError(name)
    a, b = block_at(s, i + 2); return "\t\t" + s[a:b] + "\n"

def stock_symbol(name, lib="/usr/share/kicad/symbols/Device.kicad_sym", prefix="Device"):
    s = open(lib, encoding="utf-8").read()
    i = s.find(f'\n\t(symbol "{name}"\n')
    a, b = block_at(s, i + 2); blk = s[a:b]
    blk = "\n".join("\t" + ln for ln in blk.split("\n"))          # one more indent level inside lib_symbols
    blk = blk.replace(f'(symbol "{name}"', f'(symbol "{prefix}:{name}"', 1)
    return "\t" + blk + "\n"

def prop(name, val, x, y, ang=0, hide=False, justify=None):
    return (f'\t\t(property "{name}" "{val}"\n\t\t\t(at {f(x)} {f(y)} {ang})\n' + ("\t\t\t(hide yes)\n" if hide else "") +
            '\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n'
            '\t\t\t\t)\n' + (f'\t\t\t\t(justify {justify})\n' if justify else '') + '\t\t\t)\n\t\t)\n')

class Sch:
    def __init__(self, path, project="Power"):
        self.path, self.project = path, project
        self.s = open(path, encoding="utf-8").read(); self.new = []

    # ---- library cache
    def has_lib(self, name): return f'\t\t(symbol "{name}"\n' in self.s
    def add_lib(self, text):
        name = re.match(r'\t\t\(symbol "([^"]+)"', text).group(1)
        if self.has_lib(name): return
        i = self.s.find("\t(lib_symbols\n"); a, b = block_at(self.s, i + 1)
        names = [(m.start() + a, m.group(1)) for m in re.finditer(r'\n\t\t\(symbol "([^"]+)"\n', self.s[a:b])]
        pos = next((p + 1 for p, n in names if n > name), b - 1)   # before first larger name, else before ')'
        if pos == b - 1:                                             # insert before the closing "\t)" of lib_symbols
            pos = self.s.rfind("\n\t)", a, b) + 1
        self.s = self.s[:pos] + text + self.s[pos:]

    # ---- new items
    def symbol(self, lib_id, x, y, rot, refs, value, footprint, extra=(), pins=("1", "2"), dnp=False, in_bom=True,
               ref_xy=None, val_xy=None, power=False, fang=0, justify=None, hide_value=False):
        first = refs[0][1]
        rx, ry = ref_xy or (x + 2.54, y - 1.27); vx, vy = val_xy or (x + 2.54, y + 1.27)
        t = (f'\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {f(x)} {f(y)} {rot})\n\t\t(unit 1)\n\t\t(body_style 1)\n'
             f'\t\t(exclude_from_sim no)\n\t\t(in_bom {"yes" if in_bom else "no"})\n\t\t(on_board yes)\n'
             f'\t\t(in_pos_files yes)\n\t\t(dnp {"yes" if dnp else "no"})\n\t\t(uuid "{U()}")\n')
        t += prop("Reference", first, rx, ry, fang, hide=power, justify=justify) + prop("Value", value, vx, vy, fang, hide=hide_value, justify=justify)
        t += prop("Footprint", footprint, x, y, 0, True) + prop("Datasheet", "", x, y, 0, True) + prop("Description", "", x, y, 0, True)
        for k, v in extra: t += prop(k, v, x, y, 0, True)
        for p in pins: t += f'\t\t(pin "{p}"\n\t\t\t(uuid "{U()}")\n\t\t)\n'
        t += f'\t\t(instances\n\t\t\t(project "{self.project}"\n'
        for path, ref in refs:
            t += f'\t\t\t\t(path "{path}"\n\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n'
        t += '\t\t\t)\n\t\t)\n\t)\n'
        self.new.append(t)
    def wire(self, x1, y1, x2, y2):
        self.new.append(f'\t(wire\n\t\t(pts\n\t\t\t(xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n'
                        f'\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n')
    def junction(self, x, y):
        self.new.append(f'\t(junction\n\t\t(at {f(x)} {f(y)})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{U()}")\n\t)\n')
    def label(self, name, x, y, ang=0):
        self.new.append(f'\t(label "{name}"\n\t\t(at {f(x)} {f(y)} {ang})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n'
                        f'\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n')

    # ---- edits of existing items
    def _find_block(self, head_re):
        m = list(re.finditer(head_re, self.s))
        if len(m) != 1: raise ValueError(f"{head_re}: {len(m)} matches")
        return block_at(self.s, m[0].start() + 1)
    def remove_wire(self, x1, y1, x2, y2):
        pat = [rf'\n\t\(wire\n\t\t\(pts\n\t\t\t\(xy {re.escape(f(p))} {re.escape(f(q))}\) \(xy {re.escape(f(r))} {re.escape(f(t))}\)'
               for p, q, r, t in ((x1, y1, x2, y2), (x2, y2, x1, y1))]
        hits = [m for p in pat for m in re.finditer(p, self.s)]
        if len(hits) != 1: raise ValueError(f"wire {x1},{y1}-{x2},{y2}: {len(hits)}")
        a, b = block_at(self.s, hits[0].start() + 1); self.s = self.s[:a-1] + self.s[b:]
    def move_label(self, kind, name, old, new):
        a, b = self._find_block(rf'\n\t\({kind} "{re.escape(name)}"\n(?:\t\t\(shape \w+\)\n)?\t\t\(at {re.escape(f(old[0]))} {re.escape(f(old[1]))} ')
        blk = self.s[a:b]
        blk = re.sub(r'\(at [\d.\-]+ [\d.\-]+ ', f'(at {f(new[0])} {f(new[1])} ', blk, count=1)
        self.s = self.s[:a] + blk + self.s[b:]
    def set_prop(self, ref, name, value):
        i = self.s.find(f'(property "Reference" "{ref}"'); a = self.s.rfind("\n\t(symbol\n", 0, i) + 1
        a, b = block_at(self.s, a + 1); blk = self.s[a:b]
        blk, n = re.subn(rf'\(property "{re.escape(name)}" "[^"]*"', f'(property "{name}" "{value}"', blk, count=1)
        if n != 1: raise ValueError(f"{ref}.{name}")
        self.s = self.s[:a] + blk + self.s[b:]

    def set_field(self, ref, name, x, y, ang):
        i = self.s.find(f'(property "Reference" "{ref}"'); a = self.s.rfind("\n\t(symbol\n", 0, i) + 1
        a, b = block_at(self.s, a + 1); blk = self.s[a:b]
        blk, n = re.subn(rf'(\(property "{re.escape(name)}" "[^"]*"\s*\(at )[\d.\-]+ [\d.\-]+ \d+\)', rf'\g<1>{f(x)} {f(y)} {ang})', blk, count=1)
        if n != 1: raise ValueError(f"{ref}.{name} pos")
        self.s = self.s[:a] + blk + self.s[b:]

    def save(self, path=None):
        k = self.s.find("\n\t(symbol\n") + 1
        self.s = self.s[:k] + "".join(self.new) + self.s[k:]; self.new = []
        open(path or self.path, "w", encoding="utf-8").write(self.s)

def _remove_symbol(self, ref):
    """Remove the symbol whose Reference property (as stored in the file) is `ref`."""
    i = self.s.find(f'(property "Reference" "{ref}"')
    if i < 0: raise KeyError(ref)
    a = self.s.rfind("\n\t(symbol\n", 0, i) + 1
    a, b = block_at(self.s, a + 1)
    self.s = self.s[:a-1] + self.s[b:]
Sch.remove_symbol = _remove_symbol
