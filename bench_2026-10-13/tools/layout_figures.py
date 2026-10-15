#!/usr/bin/env python3
"""Layout figures of the rev0 board (PDFN 5x6) for bench_2026-10-13/BENCH_FINDINGS.md: copper layers rendered by
kicad-cli (+ Inkscape to PNG) with nets from the board file drawn over them. Writes bench_2026-10-13/img/L*.png.
    python3 bench_2026-10-13/tools/layout_figures.py [project dir, default: the project root two levels up]
Needs kicad-cli (KiCad 10) and inkscape. The board file is copied to a temporary folder; the project is not touched.
The coordinates in the annotations are those of rev0."""
import math, os, shutil, subprocess, sys, tempfile
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import kpcb                                    # noqa: E402

OUT = os.path.join(HERE, "..", "img")
INK, INK2 = "#0b0b0b", "#52514e"
C_GATE, C_SUP, C_NTC, C_RET, C_LS = "#eb6834", "#4a3aa7", "#008300", "#e34948", "#2a78d6"
X0, Y0 = 116.25, 35.7446                       # board outline origin (Edge.Cuts bbox)
plt.rcParams.update({"font.size": 8.5, "figure.dpi": 110, "savefig.bbox": "tight"})


def render(board, layers, tmp):
    png = {}
    for L in layers:
        svg = os.path.join(tmp, f"{L}.svg")
        subprocess.run(["kicad-cli", "pcb", "export", "svg", "--mode-single", "--layers", f"{L},Edge.Cuts",
                        "--page-size-mode", "2", "--exclude-drawing-sheet", "-o", svg, board],
                       check=True, capture_output=True)
        p = os.path.join(tmp, f"{L}.png")
        subprocess.run(["inkscape", svg, "--export-type=png", "--export-dpi=800", "--export-background=white",
                        "--export-background-opacity=1", f"--export-filename={p}"], check=True, capture_output=True)
        png[L] = p
    return png


def bg(ax, png, win, alpha=1.0):
    im = Image.open(png).convert("RGB"); k = im.size[0]/53.0
    x0, y0, x1, y1 = win
    crop = im.crop((int((x0 - X0)*k), int((y0 - Y0)*k), int((x1 - X0)*k), int((y1 - Y0)*k)))
    a = np.asarray(crop).astype(float)/255
    a = 1 - alpha*(1 - a)                      # fade towards white
    ax.imshow(a, extent=(x0, x1, y1, y0), interpolation="bilinear")
    ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.set_aspect("equal")
    ax.set_xticks(range(int(x0) + 1, int(x1), 5)); ax.set_yticks(range(int(y0) + 1, int(y1), 5))
    ax.tick_params(labelsize=7, colors=INK2); ax.grid(False)


def draw_net(ax, B, net, col, layer=None, lw=2.2, win=None, label=None):
    first = True
    for s in B["segs"]:
        if s["net"] != net or (layer and s["layer"] != layer): continue
        if win and not any(win[0] <= x <= win[2] and win[1] <= y <= win[3] for x, y in ((s["x1"], s["y1"]), (s["x2"], s["y2"]))):
            continue
        ax.plot([s["x1"], s["x2"]], [s["y1"], s["y2"]], color=col, lw=lw, solid_capstyle="round",
                label=label if first else None)
        first = False
    for v in B["vias"]:
        if v["net"] == net and (not win or (win[0] <= v["x"] <= win[2] and win[1] <= v["y"] <= win[3])):
            ax.plot(v["x"], v["y"], "o", ms=3.5, mfc="white", mec=col, mew=1.2)


def tag(ax, x, y, text, col=INK, ha="left", va="center", fs=8, box=True):
    ax.text(x, y, text, color=col, ha=ha, va=va, fontsize=fs,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=col, lw=0.8, alpha=0.9) if box else None)


def fig_top(B, png):
    win = (115.8, 68.5, 169.6, 112.5)
    fig, ax = plt.subplots(figsize=(11, 9.0))
    bg(ax, png["F.Cu"], win, alpha=0.55)
    F = {f["ref"]: f for f in B["fps"]}
    for ph, (ls, hs, drv) in {"C": (122.75, 130.5, "D4"), "B": (139.75, 147.5, "D5"), "A": (156.75, 164.5, "D6")}.items():
        ax.text(ls, 71.4, f"LS {ph}", ha="center", fontsize=8.5, color=C_LS, weight="bold")
        ax.text(hs, 71.4, f"HS {ph}", ha="center", fontsize=8.5, color=C_GATE, weight="bold")
        f = F[drv]; ax.add_patch(Rectangle((f["x"] - 3, f["y"] - 2.6), 6, 5.2, fill=False, ec=INK, lw=1.4))
        ax.text(f["x"], f["y"] + 3.4, f"{drv} (драйвер фазы {ph})", ha="center", fontsize=7.5)
    for r in ("C90", "C92", "C93", "C94", "C95", "C96"):
        f = F[r]; ax.add_patch(Rectangle((f["x"] - 1.3, f["y"] - 0.8), 2.6, 1.6, fill=False, ec=C_NTC, lw=1.6))
        ax.text(f["x"], f["y"] - 1.2, r, ha="center", va="bottom", fontsize=7, color=C_NTC)
    tag(ax, 116.5, 70.0, "0603 «керамика петли»: у C — C92, C94; у B — одна C93; у A — C90, C95, C96", C_NTC, fs=7.5, va="bottom")
    for x, t in ((118.7, "GND"), (136.2, "GND"), (153.2, "GND")):
        ax.text(x, 91.2, t, ha="center", fontsize=7.5, color=INK, weight="bold")
    for x, t in ((124.7, "узел C"), (141.5, "узел B"), (159.0, "узел A")):
        ax.text(x, 99.5, t, ha="center", fontsize=7.5, color=INK, weight="bold")
    for x, t in ((131.5, "VDC"), (149.0, "VDC"), (166.5, "VDC")):
        ax.text(x, 91.2, t, ha="center", fontsize=7.5, color=INK, weight="bold")
    # SW tap of driver D4 and the phase current path
    draw_net(ax, B, "/Current_Sensor_3/Phase_IN", C_RET, win=(125, 99, 137, 110), lw=2.4, label="SW драйвера D4 → узел C")
    tag(ax, 136.8, 101.3, "SW подключён к узлу у шунта R7 (y≈100–104),\nв 15–25 мм от истоков HS", C_RET, fs=7.5)
    ax.annotate("", xy=(128.0, 79), xytext=(128.0, 100), arrowprops=dict(arrowstyle="<->", color=C_RET, lw=1.2))
    ax.set_title("Плата rev0, F.Cu, силовой блок: колонки LS/HS по фазам, узлы, полосы GND, 0603 и драйверы", loc="left",
                 fontsize=10, color=INK)
    ax.legend(loc="lower left", fontsize=7.5)
    fig.savefig(os.path.join(OUT, "L1_top_block.png")); plt.close(fig)


def fig_in3(B, png):
    win = (115.8, 70.5, 169.6, 112.5)
    fig, ax = plt.subplots(figsize=(11, 8.6))
    bg(ax, png["In3.Cu"], win, alpha=0.45)
    nets = {}
    for s in B["segs"]:
        if s["layer"] == "In3.Cu" and any(win[0] <= x <= win[2] and win[1] <= y <= win[3]
                                            for x, y in ((s["x1"], s["y1"]), (s["x2"], s["y2"]))):
            nets.setdefault(s["net"], 0); nets[s["net"]] += 1
    groups = [("затвор HO / LO (6 дорожек)", C_GATE, [n for n in nets if "/HO" in n or "/LO" in n]),
              ("питание +3.3 В, +12 В", C_SUP, [n for n in nets if n in ("+3.3V", "+12V")]),
              ("NTC → входы U1–U3", C_NTC, [n for n in nets if n.startswith("Net-(U")])]
    for lab, col, ns in groups:
        for i, n in enumerate(ns):
            draw_net(ax, B, n, col, layer="In3.Cu", win=win, lw=2.0, label=lab if i == 0 else None)
    for ph, (ls, hs) in {"C": (122.75, 130.5), "B": (139.75, 147.5), "A": (156.75, 164.5)}.items():
        ax.add_patch(Rectangle((ls - 3.2, 74.5), hs - ls + 6.6, 15.2, fill=False, ec=INK2, lw=1.0, ls="--"))
        ax.text((ls + hs)/2, 73.6, f"ключи фазы {ph} (над слоем)", ha="center", fontsize=7.5, color=INK2)
    ax.set_title("In3.Cu — единственный сплошной GND под ключами (0.1 мм под VDC на In2): нарезан дорожками",
                 loc="left", fontsize=10, color=INK)
    ax.legend(loc="lower left", fontsize=8)
    fig.savefig(os.path.join(OUT, "L2_in3_cuts.png")); plt.close(fig)


def fig_gate_c(B, png):
    win = (115.8, 72.0, 138.8, 113.5)
    fig, ax = plt.subplots(figsize=(8.2, 10.4))
    bg(ax, png["F.Cu"], win, alpha=0.4)
    draw_net(ax, B, "/Driver_3/HO", C_GATE, lw=2.6, label="HO (In3.Cu, 27 мм)")
    for n in ("Net-(Q1-PadG)", "Net-(Q7-PadG)"): draw_net(ax, B, n, C_GATE, lw=2.0)
    draw_net(ax, B, "/Current_Sensor_3/Phase_IN", C_RET, win=(125, 99, 137, 110), lw=2.6, label="возврат HS: SW → узел у шунта")
    draw_net(ax, B, "/Driver_3/LO", C_LS, lw=2.6, label="LO (In3.Cu, 35 мм)")
    for n in ("Net-(Q4-PadG)", "Net-(Q8-PadG)"): draw_net(ax, B, n, C_LS, lw=2.0)
    draw_net(ax, B, "GND", INK, win=(125.5, 104, 134, 113), lw=1.8, label="GND драйвера → слои GND")
    # loop outlines (schematic)
    hs = [(134.5, 106.5), (134.5, 81.5), (127.6, 79.4), (127.6, 76.0), (126.0, 76.0), (126.0, 102.0),
          (133.2, 107.9), (134.5, 106.5)]
    ax.fill([p[0] for p in hs], [p[1] for p in hs], color=C_GATE, alpha=0.10)
    ax.plot([p[0] for p in hs], [p[1] for p in hs], color=C_GATE, lw=0.8, ls="--")
    tag(ax, 135.0, 95.5, "петля затвора HS\n≈ 6 × 28 мм,\nохватывает ключ HS", C_GATE, fs=7.5)
    tag(ax, 116.5, 99.0, "петля затвора LS:\nLO над слоями GND,\nвозврат через GND —\nобщий участок только\nу выводов истока", C_LS, fs=7.5)
    f = {f["ref"]: f for f in B["fps"]}["D4"]
    ax.add_patch(Rectangle((f["x"] - 2.9, f["y"] - 2.5), 5.8, 5.0, fill=False, ec=INK, lw=1.4))
    ax.text(f["x"], f["y"] + 3.1, "D4 NSD1624", ha="center", fontsize=7.5)
    for (px, py, t, ha) in ((133.6, 106.61, "HO", "left"), (133.6, 107.89, "SW", "left"), (127.9, 107.89, "GND", "right"),
                            (127.9, 109.16, "LO", "right")):
        ax.text(px, py, t, fontsize=6.5, ha=ha, va="center", color=INK)
    for (rx, ry, t) in ((132.0, 80.3, "R23"), (132.0, 89.05, "R1"), (121.0, 80.3, "R25"), (121.0, 89.05, "R4")):
        ax.text(rx, ry, t, fontsize=6.5, ha="center", color=INK2)
    for x, y, t in ((127.6, 77, "S HS"), (119.85, 77, "S LS")):
        ax.plot(x, y, "s", ms=5, color=INK)
        ax.text(x + 0.4, y - 1.0, t, fontsize=7)
    ax.set_title("Фаза C: петли затворов HS и LS (дорожки — по разбору платы)", loc="left", fontsize=10, color=INK)
    ax.legend(loc="lower left", fontsize=7.5)
    fig.savefig(os.path.join(OUT, "L3_gate_loops_C.png")); plt.close(fig)


def fig_stack():
    rows = [("F.Cu", "пуры: VDC (сток HS), узлы, полосы GND; ключи, R_g, 0603", 0.035),
            ("препрег", "0.1 мм", 0.1),
            ("In1.Cu", "под блоком: узлы и VDC (как F.Cu), GND — узкие полосы", 0.035),
            ("ядро", "0.485 мм", 0.485),
            ("In2.Cu", "VDC (сплошной вне блока); под блоком — узлы и полосы GND", 0.035),
            ("препрег", "0.1 мм — лучшая пара плоскостей", 0.1),
            ("In3.Cu", "GND сплошной… но под ключами дорожки HO/LO, +3.3 В, +12 В, NTC", 0.035),
            ("ядро", "0.485 мм", 0.485),
            ("In4.Cu", "под блоком: узлы и VDC; GND — полосы", 0.035),
            ("препрег", "0.1 мм", 0.1),
            ("B.Cu", "пуры как F.Cu; шунты R7/R9/R52", 0.035)]
    fig, ax = plt.subplots(figsize=(9, 4.2)); ax.axis("off")
    y = 0
    for name, text, t in rows:
        h = 0.32 if "Cu" in name else (0.5 if t > 0.2 else 0.22)
        col = "#c98500" if "Cu" in name else "#e7e3d6"
        if name == "In3.Cu": col = C_RET
        ax.add_patch(Rectangle((0, y), 2.2, h, color=col, ec="white"))
        ax.text(2.35, y + h/2, f"{name}: {text}" if "Cu" in name else text, va="center", fontsize=8,
                color=INK if "Cu" in name else INK2)
        y -= h + 0.10
    ax.set_xlim(0, 10); ax.set_ylim(y - 0.1, 0.4)
    ax.set_title("Стек rev0: 6 слоёв, медь 35 мкм; что лежит под силовым блоком", loc="left", fontsize=10, color=INK)
    fig.savefig(os.path.join(OUT, "L4_stackup.png")); plt.close(fig)


def fig_corridors(B, png):
    """where each needed trace can run without crossing the commutation return path on In3"""
    win = (115.8, 70.5, 169.6, 106.0)
    fig, ax = plt.subplots(figsize=(11, 7.6))
    bg(ax, png["F.Cu"], win, alpha=0.35)
    phases = {"C": (116.3, 121.2, 128.2, 134.2), "B": (134.2, 138.2, 145.2, 151.2), "A": (151.2, 155.2, 162.5, 169.1)}
    for ph, (g0, g1, n1, v1) in phases.items():
        ax.add_patch(Rectangle((g0 + 0.2, 74.3), g1 - g0 - 0.4, 17.0, fc=C_LS, alpha=0.18, ec=C_LS, lw=1.2))
        ax.add_patch(Rectangle((g1 + 0.2, 74.3), n1 - g1 - 0.4, 17.0, fc=C_GATE, alpha=0.18, ec=C_GATE, lw=1.2))
        ax.add_patch(Rectangle((g0 + 0.2, 72.0), v1 - g0 - 0.4, 18.5, fill=False, ec=C_RET, lw=1.6, ls="--"))
        ax.text((g0 + g1)/2, 93.0, "LO\n+ NTC\n(In4)", ha="center", va="top", fontsize=7.2, color=C_LS, weight="bold",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
        ax.text((g1 + n1)/2, 93.0, "HO + SW\nпарой\n(In4)", ha="center", va="top", fontsize=7.2, color=C_GATE, weight="bold",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
        ax.text((g0 + v1)/2, 71.4, f"фаза {ph}: In3 без дорожек", ha="center", fontsize=7.5, color=C_RET)
    for r in ("TH1", "TH2", "TH3"):
        f = {f["ref"]: f for f in B["fps"]}[r]
        ax.plot(f["x"], f["y"], "D", ms=6, color=C_NTC)
        ax.annotate("", xy=(f["x"] - 5.0, f["y"]), xytext=(f["x"] - 0.6, f["y"]),
                    arrowprops=dict(arrowstyle="-|>", color=C_NTC, lw=1.4))
    tag(ax, 116.5, 104.5, "синие полосы — GND на всех слоях (истоки LS): LO и линии NTC идут вдоль полосы по In4;\n"
        "оранжевые — узел фазы: HO вместе с отдельной обратной дорожкой SW от выводов истока HS, по In4;\n"
        "красный пунктир — где идёт обратный ток петли коммутации: In3 (и In2) здесь без дорожек;\n"
        "ромб — термистор сейчас (на пуре узла), стрелка — перенос на полосу GND у истоков LS;\n"
        "ниже блока (y > 92: втулки, шунты, драйверы) трассы остаются как есть",
        INK, fs=7.5, va="top")
    ax.set_title("Куда переложить нужные дорожки, чтобы не резать обратный путь (предложение, по координатам rev0)",
                 loc="left", fontsize=10, color=INK)
    fig.savefig(os.path.join(OUT, "L5_corridors.png")); plt.close(fig)


def main():
    proj = os.path.expanduser(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "..", "..")
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        board = os.path.join(tmp, "Power.kicad_pcb")
        shutil.copy(os.path.join(proj, "Power.kicad_pcb"), board)
        B = kpcb.load(board)
        png = render(board, ["F.Cu", "In3.Cu"], tmp)
        fig_top(B, png); fig_in3(B, png); fig_gate_c(B, png); fig_stack(); fig_corridors(B, png)
    print("ok")


if __name__ == "__main__":
    main()
