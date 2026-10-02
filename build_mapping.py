#!/usr/bin/env python3
"""Build and validate the master oligo -> design mapping table.

Joins the per-library oligo files (which hold the synthesised 170 nt sequence,
the barcode and the flanks) against the design CSVs (which hold the parent,
mutation label, trim mode, length and GC stats), keyed on the Reference string.

The output is the lookup table the sequencing analysis needs: one row per
synthesised oligo, carrying both the physical identifiers (primer, barcode,
full sequence) and the design provenance (parent, mutation class, length).

IMPORTANT: barcodes are unique within each library but NOT across the pool.
Demultiplex on the composite key (primer, barcode) -- validated unique here.

Usage:
    python3 build_mapping.py                 # writes oligo_master_mapping.csv
    python3 build_mapping.py --check-only    # validate without writing
"""
import argparse
import csv
import itertools
import sys
from collections import Counter, defaultdict

# primer -> (design CSV, oligo CSV, library label)
LIBRARIES = [
    ("ART5",  "gc_library.csv",          "oligo_ART5_gc_library.csv",              "Lib1_Set1"),
    ("ART7",  "gc_library_set2.csv",     "oligo_ART7_gc_library_set2.csv",         "Lib1_Set2"),
    ("ART10", "gc_library2.csv",         "oligo_ART10_gc_library2.csv",            "Lib2_Set1"),
    ("ART11", "gc_library_set2b.csv",    "oligo_ART11_gc_library_set2b.csv",       "Lib2_Set2"),
]

# Primer pairs, for the record and so the analysis can verify read structure.
PRIMERS = {
    "ART5":  ("TTAAACCGGCCAACATACC", "CGCTACTCGTTCCTTTCGA"),
    "ART7":  ("GAGCCTTATGATTTCCCGC", "CCCGTTTCCTGAATGAGC"),
    "ART10": ("CAGAGATTCAACCGTCCTG", "GTAGCCATTTCAGGACGGA"),
    "ART11": ("ATTCATGCTTGGACGGACG", "GTATGTACCGCTTGTTGGA"),
}

MIN_SUBSTRATE_LEN = 20   # below this there is no duplex for ADAR to act on

COLUMNS = [
    "oligo_id", "primer", "library", "barcode", "parent", "mutation_label",
    "mutation_class", "edit_site", "trim_mode", "design_length", "gc_pct",
    "gc_band", "below_substrate_threshold", "designed_seq", "full_oligo",
]


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def classify(label):
    """Bucket a mutation label into the axis it tests."""
    if label == "original":
        return "original", ""
    site = label.split("_", 1)[0]
    rest = label[len(site) + 1:]
    if "above" in rest and "below" in rest:
        return "combined", site       # the epistasis arm
    if rest.startswith("above"):
        return "above", site
    if rest.startswith("below"):
        return "below", site
    if rest.startswith("across"):
        return "across", site
    return "unknown", site


def build():
    rows = []
    problems = []

    for primer, design_csv, oligo_csv, library in LIBRARIES:
        designs = {r["Reference"]: r for r in read_csv(design_csv)}
        oligos = read_csv(oligo_csv)

        if len(designs) != len(read_csv(design_csv)):
            problems.append(f"{design_csv}: duplicate Reference strings")

        for i, o in enumerate(oligos, 1):
            ref = o["name"]
            d = designs.get(ref)
            if d is None:
                problems.append(f"{oligo_csv} row {i}: no design row for {ref!r}")
                continue

            mclass, site = classify(d["Mutation Label"])
            length = int(d["Length"])

            # The oligo's designed_seq is DNA; the design CSV holds RNA.
            if o["designed_seq"] != d["Sequence"].upper().replace("U", "T"):
                problems.append(f"{ref}: designed_seq does not match design CSV")

            rows.append({
                "oligo_id": f"{primer}_{i:05d}",
                "primer": primer,
                "library": library,
                "barcode": o["barcode"],
                "parent": d["Parent Structure"],
                "mutation_label": d["Mutation Label"],
                "mutation_class": mclass,
                "edit_site": site,
                "trim_mode": d["Trim Mode"],
                "design_length": length,
                "gc_pct": d["GC content pct"],
                "gc_band": d["GC content range"],
                "below_substrate_threshold": "TRUE" if length < MIN_SUBSTRATE_LEN else "FALSE",
                "designed_seq": o["designed_seq"],
                "full_oligo": o["sequence"],
            })

    return rows, problems


def validate(rows, problems):
    """Checks that must pass before the table is used to demultiplex."""
    errors = list(problems)
    warnings = []

    # 1. The demultiplexing key must be unique.
    composite = Counter((r["primer"], r["barcode"]) for r in rows)
    dup = [k for k, n in composite.items() if n > 1]
    if dup:
        errors.append(f"(primer, barcode) key NOT unique: {len(dup)} collisions")

    # 2. Barcode alone is expected to collide -- record the scale.
    bc = Counter(r["barcode"] for r in rows)
    shared = {b: n for b, n in bc.items() if n > 1}
    if shared:
        warnings.append(
            f"{len(shared)} barcodes recur across libraries ({sum(shared.values())} oligos). "
            "Demultiplex on (primer, barcode), never barcode alone."
        )

    # 3. Every oligo must be the expected length and carry its primers.
    for r in rows:
        if len(r["full_oligo"]) != 170:
            errors.append(f"{r['oligo_id']}: oligo is {len(r['full_oligo'])} nt, expected 170")
        fwd, rev = PRIMERS[r["primer"]]
        if not r["full_oligo"].startswith(fwd) or not r["full_oligo"].endswith(rev):
            errors.append(f"{r['oligo_id']}: primer sequences not at expected ends")
        if r["designed_seq"] not in r["full_oligo"]:
            errors.append(f"{r['oligo_id']}: designed_seq not found in full oligo")

    # 4. No technical replicates is a known property -- confirm it holds.
    seq = Counter(r["designed_seq"] for r in rows)
    reps = {s: n for s, n in seq.items() if n > 1}
    if reps:
        warnings.append(f"{len(reps)} designed sequences appear more than once "
                        f"(usable as technical replicates)")
    else:
        warnings.append("No designed sequence appears twice: the pool contains "
                        "no technical replicates. Estimate variance from the "
                        "below-threshold designs or an external spike-in.")

    return errors, warnings


def summarise(rows):
    print("\nPool composition")
    print(f"  total oligos: {len(rows)}")

    by_lib = Counter(r["library"] for r in rows)
    for lib, n in sorted(by_lib.items()):
        print(f"    {lib:<12} {n:>5}")

    print("\n  by mutation class")
    for cls, n in Counter(r["mutation_class"] for r in rows).most_common():
        print(f"    {cls:<12} {n:>5}")

    print("\n  combined (epistasis arm) by parent")
    comb = defaultdict(int)
    for r in rows:
        if r["mutation_class"] == "combined":
            comb[(r["library"], r["parent"])] += 1
    for (lib, p), n in sorted(comb.items(), key=lambda x: -x[1]):
        print(f"    {lib:<11}{p:<40}{n:>5}")

    below = sum(1 for r in rows if r["below_substrate_threshold"] == "TRUE")
    print(f"\n  below {MIN_SUBSTRATE_LEN} nt substrate threshold: {below} "
          f"({100.0 * below / len(rows):.1f}%) -- usable as an empirical floor")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--output", default="oligo_master_mapping.csv")
    ap.add_argument("--check-only", action="store_true",
                    help="validate and summarise without writing the table")
    args = ap.parse_args()

    rows, problems = build()
    errors, warnings = validate(rows, problems)

    for w in warnings:
        print(f"NOTE: {w}")
    for e in errors[:20]:
        print(f"ERROR: {e}", file=sys.stderr)
    if len(errors) > 20:
        print(f"ERROR: ... and {len(errors) - 20} more", file=sys.stderr)

    summarise(rows)

    if errors:
        print(f"\n{len(errors)} validation error(s) -- table NOT written.", file=sys.stderr)
        return 1

    if args.check_only:
        print("\nAll checks passed (--check-only, nothing written).")
        return 0

    with open(args.output, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"\nAll checks passed. Wrote {len(rows)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
