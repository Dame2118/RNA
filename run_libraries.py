#!/usr/bin/env python3
"""Run build_oligo_library for all four library CSVs, each with its own primer pair.

Primer pairs (Forward, RevComp-to-append):
  ART5  -> gc_library.csv        (Set 1, Lib 1)
  ART7  -> gc_library_set2.csv   (Set 2, Lib 1)
  ART10 -> gc_library2.csv       (Set 1, Lib 2)
  ART11 -> gc_library_set2b.csv  (Set 2, Lib 2)
"""
import csv
import os
import sys
import random

# Patch build_oligo_library to accept primer arguments
sys.path.insert(0, os.path.dirname(__file__))
import build_oligo_library as bol

BARCODE_LENGTH = 12
TOTAL_LENGTH   = 170

LIBRARIES = [
    {
        "primer_name": "ART5",
        "fwd": "TTAAACCGGCCAACATACC",
        "rev": "CGCTACTCGTTCCTTTCGA",
        "csv":    "gc_library.csv",
        "output": "oligo_ART5_gc_library",
    },
    {
        "primer_name": "ART7",
        "fwd": "GAGCCTTATGATTTCCCGC",
        "rev": "CCCGTTTCCTGAATGAGC",
        "csv":    "gc_library_set2.csv",
        "output": "oligo_ART7_gc_library_set2",
    },
    {
        "primer_name": "ART10",
        "fwd": "CAGAGATTCAACCGTCCTG",
        "rev": "GTAGCCATTTCAGGACGGA",
        "csv":    "gc_library2.csv",
        "output": "oligo_ART10_gc_library2",
    },
    {
        "primer_name": "ART11",
        "fwd": "ATTCATGCTTGGACGGACG",
        "rev": "GTATGTACCGCTTGTTGGA",
        "csv":    "gc_library_set2b.csv",
        "output": "oligo_ART11_gc_library_set2b",
    },
]


def load_library_csv(path):
    """Load (name, sequence) from our library CSVs (Reference + Sequence columns)."""
    sequences = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            sequences.append((row["Reference"], row["Sequence"]))
    return sequences


def build(sequences, fwd, rev, output_prefix, seed=42):
    random.seed(seed)
    fixed_length   = len(fwd) + len(rev) + BARCODE_LENGTH
    variable_length = TOTAL_LENGTH - fixed_length
    print(f"  Fixed={fixed_length} nt  Variable={variable_length} nt  Total={TOTAL_LENGTH} nt")

    barcodes_used = []
    records = []

    for name, designed_seq in sequences:
        designed_seq = designed_seq.upper().strip().replace('U', 'T')
        flank_total = variable_length - len(designed_seq)

        if flank_total < 0:
            print(f"  SKIP '{name}': {len(designed_seq)} nt exceeds max {variable_length} nt")
            continue

        left_len   = flank_total // 2
        right_len  = flank_total - left_len
        left_flank  = bol.generate_flank(left_len)
        right_flank = bol.generate_flank(right_len)
        barcode     = bol.generate_barcode(barcodes_used)
        barcodes_used.append(barcode)

        full_seq = fwd + left_flank + designed_seq + right_flank + barcode + rev
        if len(full_seq) != TOTAL_LENGTH:
            print(f"  LENGTH ERROR '{name}': {len(full_seq)} nt")
            continue

        records.append({
            "name":         name,
            "sequence":     full_seq,
            "barcode":      barcode,
            "left_flank":   left_flank,
            "designed_seq": designed_seq,
            "right_flank":  right_flank,
        })

    # Detailed CSV
    with open(f"{output_prefix}.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["name","sequence","barcode",
                                               "left_flank","designed_seq","right_flank"])
        writer.writeheader()
        writer.writerows(records)

    # Stitched CSV (for ordering)
    with open(f"{output_prefix}_stitched.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["name","sequence"])
        for r in records:
            writer.writerow([r["name"], r["sequence"]])

    # FASTA
    with open(f"{output_prefix}.fasta", 'w') as f:
        for r in records:
            f.write(f">{r['name']}\n{r['sequence']}\n")

    print(f"  -> {len(records)} oligos written to {output_prefix}.*")
    return records


def main():
    all_skipped = 0
    for lib in LIBRARIES:
        print(f"\n{'='*60}")
        print(f"  {lib['primer_name']}  ->  {lib['csv']}")
        print(f"  FWD: {lib['fwd']}  ({len(lib['fwd'])} nt)")
        print(f"  REV: {lib['rev']}  ({len(lib['rev'])} nt)")
        sequences = load_library_csv(lib["csv"])
        print(f"  Loaded {len(sequences)} sequences")
        records = build(sequences, lib["fwd"], lib["rev"], lib["output"])
        skipped = len(sequences) - len(records)
        if skipped:
            print(f"  WARNING: {skipped} sequences skipped (too long)")
            all_skipped += skipped

    print(f"\nDone. Total skipped (too long): {all_skipped}")


if __name__ == "__main__":
    main()
