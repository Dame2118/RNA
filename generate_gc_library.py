#!/usr/bin/env python3
"""Generate sequence-mutant × length-variant library from ADAR parent hairpins.

For each parent and each edit site, three classes of sequence variants are built:
  - ABOVE (cumulative): mutate the k nearest base pairs above (5' side of) the
    edit site, k = 1..5.  Two permutations per step: all-GC or all-AU.
  - BELOW (cumulative): same on the 3' side (toward the apical loop).
  - ACROSS: change the base directly paired with the A edit site to C, G, or A.

Each sequence variant is then subject to the same length-trimming logic as the
original parent (peeling outer stem pairs inward, anchored on the edit site).
Within each parent, up to TOP_N entries are kept, ranked by child length
descending so that longer molecules are always included first.

Usage:
    python3 generate_gc_library.py adar_library_1_2.txt -o gc_library.csv
"""
import argparse
import csv
import re
import sys

from validate_dotbracket import PAIRS, VALID

OPENERS = set(PAIRS.values())
CLOSERS = set(PAIRS.keys())

TOP_N = 200          # max entries per parent
N_STEPS = 5          # cumulative bp steps above / below edit site
COMPLEMENT = {'A': 'U', 'U': 'A', 'G': 'C', 'C': 'G'}
ACROSS_SUBS = ['C', 'G', 'A']   # alternatives for the partner of the A edit site


# ---------------------------------------------------------------------------
# Shared helpers (same as generate_length_library.py)
# ---------------------------------------------------------------------------

def pair_map(struct):
    stacks = {o: [] for o in OPENERS}
    P = [-1] * len(struct)
    for i, c in enumerate(struct):
        if c in OPENERS:
            stacks[c].append(i)
        elif c in CLOSERS:
            j = stacks[PAIRS[c]].pop()
            P[i] = j
            P[j] = i
    return P


def rings(name, struct):
    P = pair_map(struct)
    lo, hi = 0, len(struct) - 1
    while lo < hi and P[lo] == -1:
        lo += 1
    while lo < hi and P[hi] == -1:
        hi -= 1
    R = []
    while lo < hi:
        if P[lo] != hi:
            return None
        R.append((lo, hi))
        if all(P[k] == -1 for k in range(lo + 1, hi)):
            break
        lo += 1; hi -= 1
        while lo < hi and P[lo] == -1:
            lo += 1
        while lo < hi and P[hi] == -1:
            hi -= 1
    return R


def render(seq, struct, idx):
    P = pair_map(struct)
    keep = set(idx)
    child_seq = "".join(seq[i] for i in idx)
    chars = ["(" if (P[i] != -1 and P[i] in keep and i < P[i])
             else ")" if (P[i] != -1 and P[i] in keep)
             else "." for i in idx]
    return child_seq, "".join(chars)


def gc_stats(seq):
    gc = sum(1 for b in seq.upper() if b in 'GC')
    raw = 100.0 * gc / len(seq)
    lower = min(int(raw // 10) * 10, 90)
    return round(raw), f"{lower}-{lower + 10}"


def length_children(name, seq, struct, edit0):
    """Yield (mode, idx) — same logic as generate_length_library.child_indices."""
    R = rings(name, struct)
    if R is None:
        return
    m = len(R) - 1

    def wpos(j):
        return set(range(R[j][0], R[j][1] + 1))

    loop = set(range(R[m][0] + 1, R[m][1]))

    depths = [max((j for j in range(m + 1) if R[j][0] <= e <= R[j][1]), default=-1)
              for e in edit0]
    depths = [d for d in depths if d >= 0]
    if not depths:
        return
    a = max(depths)
    shell = (wpos(a) - wpos(a + 1)) if a < m else (wpos(m) - loop)

    seen = set()

    def emit(mode, idx_set):
        key = frozenset(idx_set)
        if key not in seen:
            seen.add(key)
            yield mode, sorted(idx_set)

    for j in range(a + 1):
        yield from emit("full", wpos(j))
    for k in range(m - a, -1, -1):
        core = loop if k == 0 else wpos(m - k + 1)
        yield from emit("edit-adjacent", shell | core)
    for k in range(m - a, -1, -1):
        if k == 0:
            inner = loop
        elif k == m - a:
            inner = wpos(a + 1) | loop
        else:
            inner = (wpos(a + 1) - wpos(a + 1 + k)) | loop
        yield from emit("loop-adjacent", shell | inner)


# ---------------------------------------------------------------------------
# Sequence mutation helpers
# ---------------------------------------------------------------------------

def stem_pairs_above(P, edit_pos, n):
    """Return up to n (5'_idx, 3'_idx) bp pairs immediately 5' of edit_pos."""
    pairs = []
    pos = edit_pos - 1
    while pos >= 0 and len(pairs) < n:
        partner = P[pos]
        if partner != -1 and partner > pos:
            pairs.append((pos, partner))
        pos -= 1
    return pairs


def stem_pairs_below(P, edit_pos, n):
    """Return up to n (5'_idx, 3'_idx) bp pairs immediately 3' of edit_pos."""
    pairs = []
    pos = edit_pos + 1
    end = len(P)
    while pos < end and len(pairs) < n:
        partner = P[pos]
        if partner != -1 and partner > pos:
            pairs.append((pos, partner))
        pos += 1
    return pairs


def apply_bp(seq_list, five_idx, three_idx, bp_type):
    """Set a Watson-Crick base pair (GC or AU) at the given positions."""
    if bp_type == 'GC':
        seq_list[five_idx] = 'G'
        seq_list[three_idx] = 'C'
    else:  # AU
        seq_list[five_idx] = 'A'
        seq_list[three_idx] = 'U'


def sequence_variants(seq, struct, edit_sites_0):
    """Yield (variant_label, mutated_seq) for all sequence mutations.

    Yields the original sequence first, then all mutations.
    edit_sites_0 : list of 0-based edit-site indices.
    """
    P = pair_map(struct)
    seq_list = list(seq)

    yield "original", seq  # the unmodified parent

    for e in edit_sites_0:
        e_label = f"A{e+1}"

        # ---- ABOVE (cumulative) ----------------------------------------
        above = stem_pairs_above(P, e, N_STEPS)
        for k in range(1, len(above) + 1):
            active = above[:k]
            for bp_type in ('GC', 'AU'):
                mut = list(seq)
                for fi, ti in active:
                    apply_bp(mut, fi, ti, bp_type)
                label = f"{e_label}_above{k}_{bp_type}"
                yield label, "".join(mut)

        # ---- BELOW (cumulative) ----------------------------------------
        below = stem_pairs_below(P, e, N_STEPS)
        for k in range(1, len(below) + 1):
            active = below[:k]
            for bp_type in ('GC', 'AU'):
                mut = list(seq)
                for fi, ti in active:
                    apply_bp(mut, fi, ti, bp_type)
                label = f"{e_label}_below{k}_{bp_type}"
                yield label, "".join(mut)

        # ---- ACROSS (partner of the A edit site) -----------------------
        partner = P[e]
        if partner != -1:
            for alt in ACROSS_SUBS:
                mut = list(seq)
                mut[partner] = alt
                label = f"{e_label}_across_{alt}"
                yield label, "".join(mut)


# ---------------------------------------------------------------------------
# Parser (same format as adar_library files)
# ---------------------------------------------------------------------------

def parse(path):
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
                flush()
                name = line
    flush()
    return records


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------

COLUMNS = [
    "Reference", "Sequence", "Parent Structure", "Mutation Label",
    "GC content pct", "GC content range", "Length",
    "Edit Sites", "Parent Positions", "Trim Mode",
]


def build_rows(records):
    all_rows = []
    for parent_name, seq, struct, sites in records:
        edit0 = [p - 1 for p in sites]

        # Check this parent is a valid single hairpin first.
        if rings(parent_name, struct) is None:
            sys.stderr.write(f"WARNING: {parent_name}: not a single hairpin; skipping.\n")
            continue

        parent_rows = []

        for mut_label, mut_seq in sequence_variants(seq, struct, edit0):
            edit0_set = set(edit0)
            for mode, idx in length_children(parent_name, mut_seq, struct, edit0_set):
                child_seq, _ = render(mut_seq, struct, idx)
                length = len(idx)
                parent_pos = [i + 1 for i in idx]
                child_sites = [c for c, i in enumerate(idx, 1) if i in edit0_set]
                gc_pct, gc_band = gc_stats(child_seq)
                ref = f"{parent_name} {length}nt {gc_pct}% {mut_label} {mode}"
                parent_rows.append({
                    "Reference": ref,
                    "Sequence": child_seq,
                    "Parent Structure": parent_name,
                    "Mutation Label": mut_label,
                    "GC content pct": gc_pct,
                    "GC content range": gc_band,
                    "Length": length,
                    "Edit Sites": child_sites,
                    "Parent Positions": parent_pos,
                    "Trim Mode": mode,
                })

        # Sort by child length descending, keep top TOP_N per parent.
        parent_rows.sort(key=lambda r: int(r["Length"]), reverse=True)
        all_rows.extend(parent_rows[:TOP_N])

    return all_rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="parent library file (e.g. adar_library_1_2.txt)")
    ap.add_argument("-o", "--output", default="gc_library.csv")
    args = ap.parse_args()

    records = parse(args.input)
    rows = build_rows(records)

    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} entries from {len(records)} parents to {args.output}")


if __name__ == "__main__":
    main()
