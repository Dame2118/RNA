#!/usr/bin/env python3
"""Quality check for a generated library, to run BEFORE ordering.

Every check here corresponds to something that reached the ordered Set 1
pilot unnoticed. Run this on the design CSVs (and optionally the assembled
oligo CSVs) and read the report before anything goes to synthesis.

BLOCKING issues (exit 1) are things that waste synthesis or corrupt analysis:
  1. a parent in the source file that contributes no designs at all
  2. designs shorter than the minimum substrate length
  3. two designs with the same sequence under different mutation labels
  4. "mutations" whose sequence is identical to the unmutated parent
  5. barcode collisions on the (primer, barcode) demultiplexing key

ADVISORY issues (reported, exit 0) are coverage problems to decide about:
  6. parents missing a whole mutation class (e.g. no combined variants)
  7. lopsided per-parent representation
  8. GC bands with almost no members

Usage:
    python3 check_library.py gc_library.csv gc_library2.csv \
        --parents adar_library_1_2.txt --min-length 20

    # also check the assembled oligos
    python3 check_library.py gc_library.csv gc_library2.csv \
        --parents adar_library_1_2.txt \
        --oligos ART5=oligo_ART5_gc_library.csv ART10=oligo_ART10_gc_library2.csv
"""
import argparse
import csv
import os
import sys
from collections import Counter, defaultdict

MIN_LENGTH_DEFAULT = 20   # below this there is no duplex for ADAR to act on


def load_designs(paths):
    rows = []
    for p in paths:
        with open(p, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                r["_src"] = os.path.basename(p)
                rows.append(r)
    return rows


def mutation_class(label):
    if label == "original":
        return "original"
    rest = label.split("_", 1)[1] if "_" in label else label
    if "above" in rest and "below" in rest:
        return "combined"
    for k in ("above", "below", "across"):
        if rest.startswith(k):
            return k
    return "unknown"


class Report:
    def __init__(self):
        self.blocking = []
        self.advisory = []

    def block(self, title, detail):
        self.blocking.append((title, detail))

    def advise(self, title, detail):
        self.advisory.append((title, detail))


# ---------------------------------------------------------------------------
# Blocking checks
# ---------------------------------------------------------------------------

def check_silent_drops(rows, parents_file, rep):
    """A parent that parses fine but yields nothing must never pass silently."""
    if not parents_file:
        return
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from generate_gc_library import parse, rings
    except ImportError:
        rep.advise("Parent check skipped", "could not import the parser")
        return

    present = {r["Parent Structure"] for r in rows}
    for name, seq, struct, sites in parse(parents_file):
        if name in present:
            continue
        reason = ("not a single hairpin"
                  if rings(name, struct) is None
                  else "valid hairpin, but no designs were generated "
                       "(edit site may lie outside the paired region)")
        rep.block(f"Parent contributes nothing: {name}", reason)


def check_min_length(rows, min_len, rep):
    short = [r for r in rows if int(r["Length"]) < min_len]
    if not short:
        return
    by_parent = Counter(r["Parent Structure"] for r in short)
    worst = ", ".join(f"{p} ({n})" for p, n in by_parent.most_common(4))
    rep.block(
        f"{len(short)} designs below {min_len} nt",
        f"shortest is {min(int(r['Length']) for r in short)} nt. "
        f"Concentrated in: {worst}. These cannot form an ADAR substrate.",
    )


def check_duplicate_sequences(rows, rep):
    groups = defaultdict(list)
    for r in rows:
        groups[r["Sequence"]].append(r)
    dups = {s: v for s, v in groups.items() if len(v) > 1}
    if not dups:
        return
    extra = sum(len(v) - 1 for v in dups.values())
    spanning = sum(1 for v in dups.values()
                   if len({r["Mutation Label"] for r in v}) > 1)
    example = next(iter(v for v in dups.values()
                        if len({r["Mutation Label"] for r in v}) > 1), None)
    detail = (f"{len(dups)} sequences appear more than once ({extra} redundant "
              f"designs). {spanning} groups carry DIFFERENT mutation labels for "
              f"the same molecule.")
    if example:
        labels = ", ".join(sorted({r["Mutation Label"] for r in example})[:3])
        detail += f" e.g. {example[0]['Parent Structure']}: {labels}"
    rep.block("Duplicate designed sequences", detail)


def check_noop_mutations(rows, rep):
    """A substitution that sets a base pair already present changes nothing."""
    groups = defaultdict(list)
    for r in rows:
        groups[(r["Parent Structure"], r["Sequence"])].append(r)
    noop = 0
    examples = []
    for (parent, _), v in groups.items():
        if len(v) < 2 or not any(r["Mutation Label"] == "original" for r in v):
            continue
        for r in v:
            if r["Mutation Label"] != "original":
                noop += 1
                if len(examples) < 3:
                    examples.append(f"{parent} {r['Mutation Label']}")
    if noop:
        rep.block(
            f"{noop} 'mutations' are identical to the unmutated parent",
            "the substitution set a base pair that was already there. "
            "They will score as real effects of exactly zero. "
            f"e.g. {', '.join(examples)}",
        )


def check_barcodes(oligo_specs, rep):
    if not oligo_specs:
        return
    seen = defaultdict(list)
    per_lib = defaultdict(set)
    for primer, path in oligo_specs:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                seen[(primer, r["barcode"])].append(r["name"])
                per_lib[primer].add(r["barcode"])

    collisions = {k: v for k, v in seen.items() if len(v) > 1}
    if collisions:
        rep.block(f"{len(collisions)} (primer, barcode) collisions",
                  "the demultiplexing key is not unique")

    # barcode reuse ACROSS libraries is survivable but must be known
    if len(per_lib) > 1:
        allbc = Counter(b for s in per_lib.values() for b in s)
        shared = [b for b, n in allbc.items() if n > 1]
        if shared:
            rep.advise(
                f"{len(shared)} barcodes reused across libraries",
                "fine only if you demultiplex on (primer, barcode). "
                "Barcode alone will mis-assign these.",
            )


# ---------------------------------------------------------------------------
# Advisory checks
# ---------------------------------------------------------------------------

def check_class_coverage(rows, rep):
    per_parent = defaultdict(Counter)
    for r in rows:
        per_parent[r["Parent Structure"]][mutation_class(r["Mutation Label"])] += 1

    classes = {c for counts in per_parent.values() for c in counts}
    for cls in sorted(classes - {"original", "unknown"}):
        missing = [p for p, c in per_parent.items() if c[cls] == 0]
        if missing and len(missing) < len(per_parent):
            rep.advise(
                f"Class '{cls}' missing from {len(missing)} of {len(per_parent)} parents",
                "present in: " + ", ".join(
                    f"{p} ({c[cls]})" for p, c in sorted(
                        per_parent.items(), key=lambda x: -x[1][cls]) if c[cls]
                ) + f". Absent from: {', '.join(sorted(missing))}. "
                f"Any hypothesis resting on '{cls}' is limited to the parents that have it.",
            )


def check_balance(rows, rep):
    counts = Counter(r["Parent Structure"] for r in rows)
    if not counts:
        return
    hi, lo = max(counts.values()), min(counts.values())
    if hi >= 3 * lo:
        thin = ", ".join(f"{p} ({n})" for p, n in counts.most_common()[-3:])
        rep.advise(f"Lopsided parent representation ({lo}–{hi} designs)",
                   f"thinnest: {thin}")


def check_gc_spread(rows, rep):
    bands = Counter(int(r["GC content pct"]) // 10 * 10 for r in rows)
    thin = {b: n for b, n in bands.items() if n < max(10, len(rows) // 100)}
    if thin:
        rep.advise("Sparse GC bands",
                   ", ".join(f"{b}-{b+10}%: {n}" for b, n in sorted(thin.items())))


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csvs", nargs="+", help="library design CSV(s)")
    ap.add_argument("--parents", help="source parent file, to detect silent drops")
    ap.add_argument("--min-length", type=int, default=MIN_LENGTH_DEFAULT)
    ap.add_argument("--oligos", nargs="*", default=[],
                    metavar="PRIMER=FILE", help="assembled oligo CSVs")
    args = ap.parse_args()

    oligo_specs = []
    for spec in args.oligos:
        if "=" not in spec:
            ap.error(f"--oligos expects PRIMER=FILE, got {spec!r}")
        primer, path = spec.split("=", 1)
        oligo_specs.append((primer, path))

    rows = load_designs(args.csvs)
    rep = Report()

    check_silent_drops(rows, args.parents, rep)
    check_min_length(rows, args.min_length, rep)
    check_duplicate_sequences(rows, rep)
    check_noop_mutations(rows, rep)
    check_barcodes(oligo_specs, rep)
    check_class_coverage(rows, rep)
    check_balance(rows, rep)
    check_gc_spread(rows, rep)

    print("=" * 72)
    print(f"LIBRARY QC  ·  {len(rows)} designs across "
          f"{len({r['Parent Structure'] for r in rows})} parents "
          f"({len({r['Sequence'] for r in rows})} distinct sequences)")
    print("=" * 72)

    if rep.blocking:
        print(f"\nBLOCKING  ({len(rep.blocking)})  — fix before ordering\n")
        for i, (title, detail) in enumerate(rep.blocking, 1):
            print(f"  {i}. {title}")
            for line in _wrap(detail):
                print(f"     {line}")
            print()
    else:
        print("\nBLOCKING  (0)  — none\n")

    if rep.advisory:
        print(f"ADVISORY  ({len(rep.advisory)})  — decide, do not ignore\n")
        for i, (title, detail) in enumerate(rep.advisory, 1):
            print(f"  {i}. {title}")
            for line in _wrap(detail):
                print(f"     {line}")
            print()

    if rep.blocking:
        print(f"RESULT: NOT READY TO ORDER ({len(rep.blocking)} blocking).")
        return 1
    print("RESULT: clear to order"
          + (f" ({len(rep.advisory)} advisory to review)." if rep.advisory else "."))
    return 0


def _wrap(text, width=66):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out


if __name__ == "__main__":
    sys.exit(main())
