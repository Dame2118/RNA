#!/usr/bin/env python3
"""Generate Library 2: a second 1,800-member library from the same 9 parents.

Priority order (fill until 1,800 total):
  1. Longer children not captured in Library 1 (deeper length trimming, same
     sequence variants as Library 1).
  2. Combined above+below mutations: all 5x5 combinations of cumulative bp
     changes above and below each edit site, both GC and AU permutations.
  3. GC-targeted: variants that fill underrepresented GC% bands (10% buckets).

Deduplication against Library 1 is by exact sequence string.

Usage:
    python3 generate_gc_library2.py adar_library_1_2.txt \
        --lib1 gc_library.csv -o gc_library2.csv
"""
import argparse
import csv
import itertools
import re
import sys
from collections import defaultdict

from validate_dotbracket import PAIRS, VALID

OPENERS = set(PAIRS.values())
CLOSERS = set(PAIRS.keys())

TOTAL_CAP = 1800
PER_PARENT_CAP = 200  # max entries per parent (same as lib1)
N_STEPS = 5
ACROSS_SUBS = ['C', 'G', 'A']
COMPLEMENT = {'A': 'U', 'U': 'A', 'G': 'C', 'C': 'G'}


# ---------------------------------------------------------------------------
# Shared helpers
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
# Mutation helpers
# ---------------------------------------------------------------------------

def stem_pairs_above(P, edit_pos, n):
    pairs = []
    pos = edit_pos - 1
    while pos >= 0 and len(pairs) < n:
        partner = P[pos]
        if partner != -1 and partner > pos:
            pairs.append((pos, partner))
        pos -= 1
    return pairs


def stem_pairs_below(P, edit_pos, n):
    pairs = []
    pos = edit_pos + 1
    while pos < len(P) and len(pairs) < n:
        partner = P[pos]
        if partner != -1 and partner > pos:
            pairs.append((pos, partner))
        pos += 1
    return pairs


def apply_bp(seq_list, five_idx, three_idx, bp_type):
    if bp_type == 'GC':
        seq_list[five_idx] = 'G'
        seq_list[three_idx] = 'C'
    else:
        seq_list[five_idx] = 'A'
        seq_list[three_idx] = 'U'


def lib1_sequence_variants(seq, struct, edit_sites_0):
    """Same variants as Library 1 (original + above + below + across)."""
    P = pair_map(struct)
    yield "original", seq
    for e in edit_sites_0:
        e_label = f"A{e+1}"
        above = stem_pairs_above(P, e, N_STEPS)
        for k in range(1, len(above) + 1):
            for bp_type in ('GC', 'AU'):
                mut = list(seq)
                for fi, ti in above[:k]:
                    apply_bp(mut, fi, ti, bp_type)
                yield f"{e_label}_above{k}_{bp_type}", "".join(mut)
        below = stem_pairs_below(P, e, N_STEPS)
        for k in range(1, len(below) + 1):
            for bp_type in ('GC', 'AU'):
                mut = list(seq)
                for fi, ti in below[:k]:
                    apply_bp(mut, fi, ti, bp_type)
                yield f"{e_label}_below{k}_{bp_type}", "".join(mut)
        partner = P[e]
        if partner != -1:
            for alt in ACROSS_SUBS:
                mut = list(seq)
                mut[partner] = alt
                yield f"{e_label}_across_{alt}", "".join(mut)


def combined_variants(seq, struct, edit_sites_0):
    """All 5x5 above+below combinations, both GC and AU permutations."""
    P = pair_map(struct)
    for e in edit_sites_0:
        e_label = f"A{e+1}"
        above = stem_pairs_above(P, e, N_STEPS)
        below = stem_pairs_below(P, e, N_STEPS)
        for ka, kb in itertools.product(range(1, len(above) + 1),
                                        range(1, len(below) + 1)):
            for bp_type in ('GC', 'AU'):
                mut = list(seq)
                for fi, ti in above[:ka]:
                    apply_bp(mut, fi, ti, bp_type)
                for fi, ti in below[:kb]:
                    apply_bp(mut, fi, ti, bp_type)
                label = f"{e_label}_above{ka}below{kb}_{bp_type}"
                yield label, "".join(mut)


# ---------------------------------------------------------------------------
# Parser
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

GC_BANDS = [f"{i}-{i+10}" for i in range(0, 100, 10)]


def make_row(parent_name, mut_label, mode, idx, mut_seq, struct, edit0_set):
    child_seq, _ = render(mut_seq, struct, idx)
    length = len(idx)
    parent_pos = [i + 1 for i in idx]
    child_sites = [c for c, i in enumerate(idx, 1) if i in edit0_set]
    gc_pct, gc_band = gc_stats(child_seq)
    ref = f"{parent_name} {length}nt {gc_pct}% {mut_label} {mode}"
    return {
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
    }


def build_library2(records, lib1_sequences):
    """Build Library 2 rows in priority order, deduplicating against lib1.

    Per-parent cap of PER_PARENT_CAP ensures all parents are represented.
    Within each parent, priority: longer children > combined mutations > GC balance.
    """
    seen_seqs = set(lib1_sequences)
    seen_lib2 = set()
    parent_counts = defaultdict(int)

    def candidate(row):
        s = row["Sequence"]
        p = row["Parent Structure"]
        if s in seen_seqs or s in seen_lib2:
            return False
        if parent_counts[p] >= PER_PARENT_CAP:
            return False
        seen_lib2.add(s)
        parent_counts[p] += 1
        return True

    all_rows = []

    for name, seq, struct, sites in records:
        if rings(name, struct) is None:
            continue
        edit0 = [p - 1 for p in sites]
        edit0_set = set(edit0)
        parent_rows = []

        # Priority 1: lib1 sequence variants, longer children not in lib1
        p1 = []
        for mut_label, mut_seq in lib1_sequence_variants(seq, struct, edit0):
            for mode, idx in length_children(name, mut_seq, struct, edit0_set):
                row = make_row(name, mut_label, mode, idx, mut_seq, struct, edit0_set)
                if row["Sequence"] not in seen_seqs and row["Sequence"] not in seen_lib2:
                    p1.append(row)
        p1.sort(key=lambda r: int(r["Length"]), reverse=True)

        # Priority 2: combined above+below mutations
        p2 = []
        for mut_label, mut_seq in combined_variants(seq, struct, edit0):
            for mode, idx in length_children(name, mut_seq, struct, edit0_set):
                row = make_row(name, mut_label, mode, idx, mut_seq, struct, edit0_set)
                if row["Sequence"] not in seen_seqs and row["Sequence"] not in seen_lib2:
                    p2.append(row)
        p2.sort(key=lambda r: int(r["Length"]), reverse=True)

        # Priority 3: GC balance — sort remaining by least-represented band
        combined_candidates = p1 + p2
        band_counts = defaultdict(int)
        for r in combined_candidates[:PER_PARENT_CAP]:
            band_counts[r["GC content range"]] += 1
        remaining = combined_candidates[PER_PARENT_CAP:]
        remaining.sort(key=lambda r: band_counts.get(r["GC content range"], 0))
        ordered = combined_candidates[:PER_PARENT_CAP] + remaining

        for row in ordered:
            if candidate(row):
                parent_rows.append(row)
            if parent_counts[name] >= PER_PARENT_CAP:
                break

        all_rows.extend(parent_rows)

    return all_rows[:TOTAL_CAP]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input")
    ap.add_argument("--lib1", default="gc_library.csv",
                    help="Library 1 CSV to deduplicate against")
    ap.add_argument("-o", "--output", default="gc_library2.csv")
    args = ap.parse_args()

    # Load lib1 sequences for deduplication.
    lib1_seqs = set()
    with open(args.lib1) as f:
        for r in csv.DictReader(f):
            lib1_seqs.add(r["Sequence"])
    print(f"Loaded {len(lib1_seqs)} sequences from Library 1 for deduplication.")

    records = parse(args.input)
    rows = build_library2(records, lib1_seqs)

    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} entries to {args.output}")
    from collections import Counter
    c = Counter(r["Parent Structure"] for r in rows)
    for k, v in sorted(c.items(), key=lambda x: -x[1]):
        print(f"  {k:<22} {v}")


if __name__ == "__main__":
    main()
