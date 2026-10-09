#!/usr/bin/env python3
"""Figure: nearest-neighbour logic for the edit-site variant library.

Panel A  the NEIL1 baseline substrate, drawn as a stem-loop with its real
         sequence. The edit site A45 sits in a 1x1 internal loop opposite C28 —
         a native A-C mismatch — with A44 and A46 as its 5' and 3' neighbours.
Panel B  the variant grid: N-1 and N+1 each take all four bases on the same
         backbone, giving 4 x 4 = 16 combinations.

Letters are the real NEIL1 bases, never placeholders. Colours match
gen_rnartist_parents.py so figures in the same paper agree.

Usage:
    python3 scripts/fig_neighbor_logic.py [-o out.png]
"""
import argparse
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from generate_gc_library import parse, pair_map  # noqa: E402

BASE_COLORS = {
    "A": ("#14907A", "#FFFFFF"),
    "U": ("#831FFB", "#FFFFFF"),
    "G": ("#3792FD", "#FFFFFF"),
    "C": ("#9B1589", "#FFFFFF"),
}
EDIT = ("#E34948", "#FFFFFF")
EDGE = "#333333"
BACKBONE = "#9A9A9A"
RUNG = "#4477AA"
INK = "#1A1A1A"
MUTED = "#6B6B6B"

PARENT = "NEIL1"
SITE = 45                      # 1-based edit site


def neil1():
    for name, seq, struct, sites in parse(os.path.join(ROOT, "adar_library_1_2.txt")):
        if name == PARENT:
            return seq, struct, sites
    raise SystemExit("NEIL1 not found")


def opposite_of(struct, P, e):
    n = len(struct)
    l = next((i for i in range(e - 1, -1, -1) if P[i] != -1), None)
    r = next((i for i in range(e + 1, n) if P[i] != -1), None)
    if l is None or r is None:
        return []
    lo, hi = sorted((P[l], P[r]))
    return [k for k in range(lo + 1, hi) if P[k] == -1]


# ---------------------------------------------------------------- panel A ---

HALF_W, RISE = 0.80, 1.0


def hairpin_layout(struct):
    n = len(struct)
    P = pair_map(struct)
    pos, rungs = {}, []
    i, j, y = 0, n - 1, 0.0

    while i < j and P[i] == -1 and P[j] == -1:
        pos[i] = (-HALF_W - 0.34, y)
        pos[j] = (HALF_W + 0.34, y)
        i += 1; j -= 1; y += RISE * 0.8

    while i < j:
        if P[i] == j:
            pos[i] = (-HALF_W, y); pos[j] = (HALF_W, y)
            rungs.append((i, j))
            i += 1; j -= 1; y += RISE
            continue
        li = i
        while li < j and P[li] == -1:
            li += 1
        rj = j
        while rj > i and P[rj] == -1:
            rj -= 1
        left, right = list(range(i, li)), list(range(rj + 1, j + 1))
        if li >= rj:
            break
        span = max(len(left), len(right))
        h = RISE * (0.75 * span + 0.55)
        for k, idx in enumerate(left):
            f = (k + 1) / (len(left) + 1)
            pos[idx] = (-HALF_W - 0.42 * math.sin(math.pi * f), y + h * f)
        for k, idx in enumerate(reversed(right)):
            f = (k + 1) / (len(right) + 1)
            pos[idx] = (HALF_W + 0.42 * math.sin(math.pi * f), y + h * f)
        i, j = li, rj
        y += h

    loop = [k for k in range(i, j + 1) if k not in pos]
    if loop:
        m = len(loop)
        r = max(0.80, (m + 1) * 0.20)
        cy = y - RISE * 0.1 + r * 0.75
        for k, idx in enumerate(loop):
            ang = math.pi * (1 - (k + 0.5) / m)
            pos[idx] = (r * math.cos(ang) * 0.95, cy + r * math.sin(ang) * 0.95)
    return pos, rungs


def draw_panel_a(ax, seq, struct, site, opp):
    pos, rungs = hairpin_layout(struct)
    n = len(seq)
    e = site - 1
    order = [k for k in range(n) if k in pos]

    ax.plot([pos[k][0] for k in order], [pos[k][1] for k in order],
            color=BACKBONE, lw=1.0, zorder=1, solid_capstyle="round")
    for a, b in rungs:
        ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]],
                color=RUNG, lw=1.1, alpha=.8, zorder=1)

    # highlight the internal loop
    xs = [pos[k][0] for k in [e, e - 1, e + 1] + opp]
    ys = [pos[k][1] for k in [e, e - 1, e + 1] + opp]
    pad = 0.55
    ax.add_patch(FancyBboxPatch(
        (min(xs) - pad, min(ys) - pad), max(xs) - min(xs) + 2 * pad,
        max(ys) - min(ys) + 2 * pad, boxstyle="round,pad=0.12",
        facecolor="#EAF1FB", edgecolor="#3792FD", lw=1.2, alpha=.65, zorder=0))

    for k in order:
        b = seq[k]
        if k == e:
            fill, txt = EDIT
        else:
            fill, txt = BASE_COLORS.get(b, ("#E8E8E8", "#222222"))
        big = k in (e, e - 1, e + 1) or k in opp
        ax.scatter(*pos[k], s=118 if big else 62,
                   color=fill, edgecolors=EDGE,
                   linewidths=1.0 if big else 0.4, zorder=3 if big else 2)
        ax.text(pos[k][0], pos[k][1], b, fontsize=5.6 if big else 3.9,
                ha="center", va="center", color=txt,
                fontweight="bold" if big else "normal", zorder=4)

    def tag(idx, label, dx, dy, ha, weight="normal", color=INK):
        ax.annotate(label, xy=pos[idx],
                    xytext=(pos[idx][0] + dx, pos[idx][1] + dy),
                    fontsize=6.8, color=color, ha=ha, va="center", zorder=5,
                    fontweight=weight,
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=.7,
                                    shrinkA=0, shrinkB=6))

    tag(e - 1, f"N$_{{-1}}$  {seq[e-1]}{e}", -2.2, 1.5, "right")
    tag(e + 1, f"N$_{{+1}}$  {seq[e+1]}{e+2}", -2.2, -1.5, "right")
    tag(e, f"edit site A{site}", 2.4, 1.5, "left", "bold", EDIT[0])
    if opp:
        tag(opp[0], f"opposite {seq[opp[0]]}{opp[0]+1}", 2.4, -1.5, "left")

    ax.text(pos[order[0]][0] - 0.9, pos[order[0]][1], "5'",
            fontsize=7, color=MUTED, ha="right", va="center")
    ax.text(pos[order[-1]][0] + 0.9, pos[order[-1]][1], "3'",
            fontsize=7, color=MUTED, ha="left", va="center")

    allx = [p[0] for p in pos.values()]; ally = [p[1] for p in pos.values()]
    ax.set_xlim(min(allx) - 3.0, max(allx) + 3.4)
    ax.set_ylim(min(ally) - 1.2, max(ally) + 1.2)
    ax.set_aspect("equal"); ax.axis("off")


# ---------------------------------------------------------------- panel B ---

BASES = ["C", "A", "U", "G"]


def draw_motif(ax, cx, cy, n_minus, n_plus, opp_base, partner5, partner3, s=1.0):
    """One 1x1 internal-loop motif: N-1 / A / N+1 over their opposing strand."""
    dx, dy = 0.92 * s, 0.86 * s
    top = [(-dx, dy / 2), (0, dy / 2 + 0.10 * s), (dx, dy / 2)]
    bot = [(-dx, -dy / 2), (0, -dy / 2 - 0.10 * s), (dx, -dy / 2)]
    top_b = [(n_minus, False), ("A", True), (n_plus, False)]
    bot_b = [(partner5, False), (opp_base, False), (partner3, False)]

    for strand in (top, bot):
        ax.plot([cx + p[0] for p in strand], [cy + p[1] for p in strand],
                color=BACKBONE, lw=1.0, zorder=1)
    for k in (0, 2):                       # closing pairs
        ax.plot([cx + top[k][0], cx + bot[k][0]], [cy + top[k][1], cy + bot[k][1]],
                color=RUNG, lw=1.1, alpha=.8, zorder=1)

    for (px, py), (b, is_edit) in zip(top, top_b):
        fill, txt = EDIT if is_edit else BASE_COLORS[b]
        ax.scatter(cx + px, cy + py, s=132 * s * s, color=fill,
                   edgecolors=EDGE, linewidths=.9, zorder=3)
        ax.text(cx + px, cy + py, b, fontsize=6.4 * s, ha="center", va="center",
                color=txt, fontweight="bold", zorder=4)
    for (px, py), (b, _) in zip(bot, bot_b):
        fill, txt = BASE_COLORS[b]
        ax.scatter(cx + px, cy + py, s=112 * s * s, color=fill,
                   edgecolors=EDGE, linewidths=.7, zorder=3)
        ax.text(cx + px, cy + py, b, fontsize=5.8 * s, ha="center", va="center",
                color=txt, zorder=4)


def draw_panel_b(ax, opp_base, partner5, partner3):
    step_x, step_y = 3.05, 2.75
    for r, n_minus in enumerate(BASES):
        for c, n_plus in enumerate(BASES):
            draw_motif(ax, c * step_x, -r * step_y, n_minus, n_plus,
                       opp_base, partner5, partner3)

    for c, b in enumerate(BASES):
        fill, txt = BASE_COLORS[b]
        ax.scatter(c * step_x, 1.75, s=150, color=fill, edgecolors=EDGE, lw=.9)
        ax.text(c * step_x, 1.75, b, fontsize=7, ha="center", va="center",
                color=txt, fontweight="bold")
    ax.text(1.5 * step_x, 2.62, "3′ neighbour  (N$_{+1}$)", fontsize=8.5,
            ha="center", va="center", color=INK, fontweight="bold")

    for r, b in enumerate(BASES):
        fill, txt = BASE_COLORS[b]
        ax.scatter(-2.05, -r * step_y, s=150, color=fill, edgecolors=EDGE, lw=.9)
        ax.text(-2.05, -r * step_y, b, fontsize=7, ha="center", va="center",
                color=txt, fontweight="bold")
    ax.text(-3.05, -1.5 * step_y, "5′ neighbour  (N$_{-1}$)", fontsize=8.5,
            rotation=90, ha="center", va="center", color=INK, fontweight="bold")

    ax.set_xlim(-3.7, 3 * step_x + 1.6)
    ax.set_ylim(-3 * step_y - 1.7, 3.2)
    ax.set_aspect("equal"); ax.axis("off")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--output", default=os.path.join(HERE, "fig_neighbor_logic.png"))
    args = ap.parse_args()

    seq, struct, _ = neil1()
    P = pair_map(struct)
    e = SITE - 1
    opp = opposite_of(struct, P, e)
    if P[e] != -1:
        raise SystemExit(f"A{SITE} is paired; this figure assumes a loop context")

    opp_base = seq[opp[0]]
    partner5 = seq[P[e - 1]]
    partner3 = seq[P[e + 1]]
    print(f"NEIL1 A{SITE}: N-1={seq[e-1]}{e}  N+1={seq[e+2-1]}{e+2}  "
          f"opposite={opp_base}{opp[0]+1}  closing pairs "
          f"{seq[e-1]}:{partner5} and {seq[e+1]}:{partner3}")

    fig = plt.figure(figsize=(14.5, 11.5))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.75], wspace=0.14)
    axA, axB = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])

    draw_panel_a(axA, seq, struct, SITE, opp)
    draw_panel_b(axB, opp_base, partner5, partner3)

    fig.text(0.035, 0.972, "A", fontsize=15, fontweight="bold", color=INK)
    fig.text(0.062, 0.972, "Baseline substrate", fontsize=13,
             fontweight="bold", color=INK)
    fig.text(0.035, 0.950, f"{PARENT}, {len(seq)} nt · edit site A{SITE} sits in a "
             f"1×1 internal loop, opposite {opp_base}{opp[0]+1}",
             fontsize=8.4, color=MUTED)

    fig.text(0.375, 0.972, "B", fontsize=15, fontweight="bold", color=INK)
    fig.text(0.402, 0.972, "Edit-site variants  (N = 16)", fontsize=13,
             fontweight="bold", color=INK)
    fig.text(0.375, 0.950, "N$_{-1}$ and N$_{+1}$ each take all four bases on the "
             f"same backbone. The edit-site A and its opposing {opp_base} are "
             "held fixed.", fontsize=8.4, color=MUTED)

    fig.subplots_adjust(top=0.925, bottom=0.02, left=0.03, right=0.985)
    fig.savefig(args.output, dpi=250, facecolor="white")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
