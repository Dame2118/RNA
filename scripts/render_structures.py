#!/usr/bin/env python3
"""Quick sanity-check renderer for RNA secondary structures from
adar_library_1_1.txt. Not a substitute for RNArtistCore's layout, but gives
a visual check of base-pairing topology and edit-site placement: backbone
on a circle, base pairs as chords, A edit sites in red."""
import math
import os

import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def pair_map(struct):
    stack = []
    P = [-1] * len(struct)
    for i, c in enumerate(struct):
        if c == "(":
            stack.append(i)
        elif c == ")":
            j = stack.pop()
            P[i], P[j] = j, i
    return P


def parse_parents(path):
    with open(path) as fh:
        blocks = [b for b in fh.read().split("\n\n") if b.strip()]
    entries = []
    for b in blocks:
        lines = [l.strip() for l in b.splitlines() if l.strip()]
        name = lines[0]
        seq = lines[1].lstrip(">")
        struct = lines[2]
        edits = [int(t.split("_")[1]) for t in
                 lines[3].split(":", 1)[1].split(",")]
        entries.append((name, seq, struct, sorted(set(edits))))
    return entries


def render_one(ax, name, seq, struct, edits):
    n = len(seq)
    P = pair_map(struct)
    xs, ys = [], []
    for i in range(n):
        theta = 2 * math.pi * i / n
        xs.append(math.cos(theta))
        ys.append(math.sin(theta))

    # backbone
    ax.plot(xs + [xs[0]], ys + [ys[0]], color="#bbbbbb", lw=1, zorder=1)

    # base pairs as chords
    for i, j in enumerate(P):
        if j != -1 and i < j:
            ax.plot([xs[i], xs[j]], [ys[i], ys[j]],
                    color="#4477aa", lw=0.7, alpha=0.7, zorder=1)

    edit_set = set(edits)
    for i in range(n):
        is_edit = (i + 1) in edit_set
        color = "red" if is_edit else "#D9D9D9"
        ax.scatter(xs[i], ys[i], s=120 if is_edit else 70,
                    color=color, edgecolors="#222222", zorder=2)
        ax.text(xs[i] * 1.12, ys[i] * 1.12, seq[i], fontsize=6,
                ha="center", va="center",
                color="white" if is_edit else "#222222",
                zorder=3)

    ax.set_title(f"{name} ({n}nt)", fontsize=9)
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.3, 1.3)
    ax.set_aspect("equal")
    ax.axis("off")


def main():
    entries = parse_parents(os.path.join(ROOT, "adar_library_1_1.txt"))
    n = len(entries)
    cols = 4
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 4))
    axes = axes.flatten()
    for ax, (name, seq, struct, edits) in zip(axes, entries):
        render_one(ax, name, seq, struct, edits)
    for ax in axes[n:]:
        ax.axis("off")
    fig.tight_layout()
    out_path = os.path.join(HERE, "parents_render.png")
    fig.savefig(out_path, dpi=150)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
