#!/usr/bin/env python3
"""Render parent hairpins as proper stem-loop layouts.

Unlike render_structures.py (circular backbone, pairs as chords), this lays the
molecule out the way a secondary-structure drawing tool does: the 5' strand
climbs the left side, the 3' strand descends the right, base pairs are rungs
between them, bulges and internal loops push outward, and the apical loop
closes the top. Edit-site adenosines are red.

Every parent that contributes designs is a validated single hairpin, so this
layout is well defined for all of them.

Usage:
    python3 scripts/render_parents_hairpin.py
"""
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from generate_gc_library import parse, rings  # noqa: E402

EDIT_COLOR = "#D62728"
BASE_FILL = "#E8E8E8"
BASE_EDGE = "#333333"
PAIR_COLOR = "#4477AA"
BACKBONE = "#999999"

HALF_W = 0.78     # half the distance between the two strands of a stem
RISE = 1.0        # vertical rise per stacked base pair


def contributing_parents(csv_name):
    """Parents that actually have designs in the library (not just valid hairpins)."""
    import csv as _csv
    with open(os.path.join(ROOT, csv_name), newline="", encoding="utf-8-sig") as f:
        return {r["Parent Structure"] for r in _csv.DictReader(f)}


def pair_map(struct):
    stack, P = [], [-1] * len(struct)
    for i, c in enumerate(struct):
        if c == "(":
            stack.append(i)
        elif c == ")":
            j = stack.pop()
            P[i], P[j] = j, i
    return P


def layout(seq, struct):
    """Return {index: (x, y)} and the list of (i, j) pairs to draw as rungs."""
    n = len(seq)
    P = pair_map(struct)
    pos = {}
    rungs = []

    i, j, y = 0, n - 1, 0.0

    # 5' / 3' tails hanging below the first pair
    while i < j and P[i] == -1 and P[j] == -1:
        pos[i] = (-HALF_W - 0.34, y)
        pos[j] = (HALF_W + 0.34, y)
        i += 1
        j -= 1
        y += RISE * 0.8

    while i < j:
        if P[i] == j:
            pos[i] = (-HALF_W, y)
            pos[j] = (HALF_W, y)
            rungs.append((i, j))
            i += 1
            j -= 1
            y += RISE
            continue

        # unpaired stretch on one or both strands: a bulge or internal loop
        li = i
        while li < j and P[li] == -1:
            li += 1
        rj = j
        while rj > i and P[rj] == -1:
            rj -= 1
        left = list(range(i, li))
        right = list(range(rj + 1, j + 1))

        if li >= rj:           # nothing paired remains -> apical loop
            break

        span = max(len(left), len(right))
        height = RISE * (0.75 * span + 0.55)

        for k, idx in enumerate(left):
            f = (k + 1) / (len(left) + 1)
            pos[idx] = (-HALF_W - 0.42 * math.sin(math.pi * f), y + height * f)
        for k, idx in enumerate(reversed(right)):
            f = (k + 1) / (len(right) + 1)
            pos[idx] = (HALF_W + 0.42 * math.sin(math.pi * f), y + height * f)

        i, j = li, rj
        y += height

    # apical loop: everything still unassigned between i and j
    loop = [k for k in range(i, j + 1) if k not in pos]
    if loop:
        m = len(loop)
        r = max(0.80, (m + 1) * 0.20)
        cy = y - RISE * 0.1 + r * 0.75
        # sweep from the left strand round to the right strand
        for k, idx in enumerate(loop):
            ang = math.pi * (1 - (k + 0.5) / m)
            pos[idx] = (r * math.cos(ang) * 0.95, cy + r * math.sin(ang) * 0.95)

    return pos, rungs


def render_one(ax, name, seq, struct, sites):
    pos, rungs = layout(seq, struct)
    n = len(seq)
    edits = set(sites)

    xs = [pos[k][0] for k in range(n) if k in pos]
    ys = [pos[k][1] for k in range(n) if k in pos]

    # backbone through consecutive residues
    order = [k for k in range(n) if k in pos]
    ax.plot([pos[k][0] for k in order], [pos[k][1] for k in order],
            color=BACKBONE, lw=1.1, zorder=1, solid_capstyle="round")

    for a, b in rungs:
        ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]],
                color=PAIR_COLOR, lw=1.3, alpha=0.85, zorder=1)

    size = 120 if n <= 70 else 86
    fs = 5.6 if n <= 70 else 4.6
    for k in order:
        is_edit = (k + 1) in edits
        ax.scatter(*pos[k], s=size * (1.35 if is_edit else 1.0),
                   color=EDIT_COLOR if is_edit else BASE_FILL,
                   edgecolors=BASE_EDGE, linewidths=0.5, zorder=2)
        ax.text(pos[k][0], pos[k][1], seq[k], fontsize=fs,
                ha="center", va="center", zorder=3,
                color="white" if is_edit else "#222222",
                fontweight="bold" if is_edit else "normal")

    label = ", ".join(f"A{s}" for s in sites)
    ax.set_title(f"{name}\n{n} nt · {label}", fontsize=7.5, pad=5)
    pad = 0.6
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)
    ax.set_aspect("equal")
    ax.axis("off")


def render_set(entries, out_path, cols=5, title=None):
    n = len(entries)
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 2.5, rows * 5.6))
    axes = axes.flatten() if n > 1 else [axes]
    for ax, (name, seq, struct, sites) in zip(axes, entries):
        render_one(ax, name, seq, struct, sites)
    for ax in axes[n:]:
        ax.axis("off")
    if title:
        fig.suptitle(title, fontsize=11, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.985 if title else 1))
    fig.savefig(out_path, dpi=200, facecolor="white")
    plt.close(fig)
    print(f"wrote {out_path}  ({n} parents)")


def main():
    for tag, src, csv_path, title in [
        ("set1", "adar_library_1_2.txt", "gc_library.csv",
         "Set 1 parents — Libraries 1 and 2 (ART5 / ART10)"),
        ("set2", "adar_library_2.txt", "gc_library_set2.csv",
         "Set 2 parents — Libraries 1 and 2 (ART7 / ART11)"),
    ]:
        records = parse(os.path.join(ROOT, src))
        contributing = contributing_parents(csv_path)
        usable = [r for r in records if r[0] in contributing]
        out = os.path.join(HERE, f"parents_hairpin_{tag}.png")
        render_set(usable, out, title=title)


if __name__ == "__main__":
    main()
