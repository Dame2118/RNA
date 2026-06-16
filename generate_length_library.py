#!/usr/bin/env python3
"""Generate length-variant child structures from ADAR parent hairpins.

From each parent structure we build a ladder of shorter children by peeling one
base pair off the outer stem at a time, walking inward toward the apical loop.

Rules (confirmed with the lab):
  - Trim unit is one base PAIR (its 5' base + its 3' partner).
  - No loose tails: when peeling a pair exposes unpaired bulge / internal-loop
    bases, strip them in the same step so every child begins and ends on a pair.
  - Stop when only one base pair remains closing the apical loop ('(....)').
  - Edit sites do not gate trimming; they are re-indexed and tracked per child.

Output is a CSV library. The companion GC-content stage will extend this.

Usage:
    python3 generate_length_library.py adar_library_1_1.txt -o length_library.csv
"""
import argparse
import csv
import re
import sys

# Reuse the bracket vocabulary from the validator (supports pseudoknot pairs).
from validate_dotbracket import PAIRS, VALID, check

OPENERS = set(PAIRS.values())
CLOSERS = set(PAIRS.keys())


def pair_map(struct):
    """Return P where P[i] is the partner index of position i, or -1 if unpaired."""
    stacks = {opener: [] for opener in OPENERS}
    P = [-1] * len(struct)
    for i, c in enumerate(struct):
        if c in OPENERS:
            stacks[c].append(i)
        elif c in CLOSERS:
            j = stacks[PAIRS[c]].pop()
            P[i] = j
            P[j] = i
    return P


def parse(path):
    """Yield (name, seq, struct, edit_sites) blocks from the library file.

    Blocks are separated by blank lines: a bare line is the name, the '>'-line is
    the sequence, the dot-bracket line is the structure, and an 'edit site' line
    lists 1-indexed A positions (e.g. 'edit site: A_4, A_6'). Edit sites optional.
    """
    name = seq = struct = None
    sites = []
    records = []

    def flush():
        nonlocal name, seq, struct, sites
        if name and seq and struct:
            records.append((name, seq, struct, sites))
        name = seq = struct = None
        sites = []

    with open(path) as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith('>'):
                seq = line[1:]
            elif line.lower().startswith('edit site'):
                sites = [int(n) for n in re.findall(r'A_(\d+)', line)]
            elif set(line) <= VALID:
                struct = line
            else:
                # A bare line is the next block's name -> emit the pending record.
                flush()
                name = line
    flush()
    return records


def rings(name, struct):
    """Return the nested peel windows R[0..m] of a single hairpin, or None.

    R[0] is the full (tail-stripped) hairpin; R[m] is the innermost window whose
    interior is the apical loop. Each step removes the outer pair and strips any
    exposed unpaired bulge bases. Returns None (with a warning) if the structure is
    a genuine multibranch junction (P[lo] != hi).
    """
    P = pair_map(struct)
    lo, hi = 0, len(struct) - 1
    while lo < hi and P[lo] == -1:
        lo += 1
    while lo < hi and P[hi] == -1:
        hi -= 1

    R = []
    while lo < hi:
        if P[lo] != hi:
            sys.stderr.write(
                f"WARNING: {name}: multibranch/junction at [{lo},{hi}] "
                f"(P[{lo}]={P[lo]}) -- not a single hairpin; skipping.\n"
            )
            return None
        R.append((lo, hi))
        if all(P[k] == -1 for k in range(lo + 1, hi)):
            break  # innermost window: interior is the apical loop
        lo += 1
        hi -= 1
        while lo < hi and P[lo] == -1:
            lo += 1
        while lo < hi and P[hi] == -1:
            hi -= 1
    return R


def child_indices(name, seq, struct, edit0):
    """Yield (mode, idx) children: idx is the sorted list of retained parent indices.

    Two-phase, anchored on the innermost surviving edit site (see module docstring).
    edit0 is the set of 0-based edit positions. Deduplicated per parent.
    """
    R = rings(name, struct)
    if R is None:
        return
    m = len(R) - 1

    def wpos(j):
        return set(range(R[j][0], R[j][1] + 1))

    loop = set(range(R[m][0] + 1, R[m][1]))  # apical loop (always retained)

    # Anchor: deepest ring that still contains an edit site.
    depths = [max((j for j in range(m + 1) if R[j][0] <= e <= R[j][1]), default=-1)
              for e in edit0]
    depths = [d for d in depths if d >= 0]
    if not depths:
        sys.stderr.write(
            f"WARNING: {name}: no edit site lands on the hairpin "
            f"(only stripped tail?) -- skipping.\n")
        return
    a = max(depths)
    shell = (wpos(a) - wpos(a + 1)) if a < m else (wpos(m) - loop)

    seen = set()
    rows = []

    def emit(mode, idx_set):
        key = frozenset(idx_set)
        if key not in seen:
            seen.add(key)
            rows.append((mode, sorted(idx_set)))

    # Phase 1: contiguous outer-peel windows down to the anchor window.
    for j in range(a + 1):
        emit("full", wpos(j))
    # Phase 2: keep the anchor edit site, shorten the inner stem two ways.
    for k in range(m - a, -1, -1):
        core = loop if k == 0 else wpos(m - k + 1)
        emit("edit-adjacent", shell | core)
    for k in range(m - a, -1, -1):
        if k == 0:
            inner = loop
        elif k == m - a:
            inner = wpos(a + 1) | loop
        else:
            inner = (wpos(a + 1) - wpos(a + 1 + k)) | loop
        emit("loop-adjacent", shell | inner)

    yield from rows


def render(seq, struct, idx):
    """Build (child_seq, child_struct) for a retained index-list."""
    P = pair_map(struct)
    keep = set(idx)
    child_seq = "".join(seq[i] for i in idx)
    chars = []
    for i in idx:
        if P[i] != -1 and P[i] in keep:
            chars.append("(" if i < P[i] else ")")
        else:
            chars.append(".")
    return child_seq, "".join(chars)


def gc_stats(seq):
    """Return (rounded_pct, range_label) for the GC content of an RNA sequence."""
    gc = sum(1 for b in seq.upper() if b in 'GC')
    raw = 100.0 * gc / len(seq)
    lower = min(int(raw // 10) * 10, 90)
    return round(raw), f"{lower}-{lower + 10}"


def reference(parent, length, gc_pct, mode):
    """Build the Reference name. The GC field is isolated here for the GC stage."""
    return f"{parent} {length} {gc_pct}% {mode}"


def build_rows(records):
    rows = []
    for name, seq, struct, sites in records:
        edit0 = {p - 1 for p in sites}  # 0-based edit positions
        for mode, idx in child_indices(name, seq, struct, edit0):
            child_seq, _ = render(seq, struct, idx)
            length = len(idx)
            # Map child positions (1-based) back to the parent; flag edit sites.
            parent_pos = [i + 1 for i in idx]
            child_sites = [c for c, i in enumerate(idx, 1) if i in edit0]
            gc_pct, gc_band = gc_stats(child_seq)
            rows.append({
                "Reference": reference(name, length, gc_pct, mode),
                "Sequence": child_seq,
                "Parent Structure": name,
                "GC content pct": gc_pct,
                "GC content range": gc_band,
                "Length": length,
                "Edit Sites": child_sites,
                "Parent Positions": parent_pos,
                "Trim Mode": mode,
            })
    return rows


COLUMNS = [
    "Reference", "Sequence", "Parent Structure",
    "GC content pct", "GC content range", "Length",
    "Edit Sites", "Parent Positions", "Trim Mode",
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="parent library file (e.g. adar_library_1_1.txt)")
    ap.add_argument("-o", "--output", default="length_library.csv",
                    help="output CSV path (default: length_library.csv)")
    args = ap.parse_args()

    records = parse(args.input)
    rows = build_rows(records)

    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} children from {len(records)} parents to {args.output}")


if __name__ == "__main__":
    main()
