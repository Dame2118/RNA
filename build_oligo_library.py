import random
import csv
import sys

FWD_PRIMER = "TTAAACCGGCCAACATACC"   # 19 nt
REV_PRIMER = "CGCTACTCGTTCCTTTCGA"   # 19 nt
BARCODE_LENGTH = 12
TOTAL_LENGTH = 170

FIXED_LENGTH = len(FWD_PRIMER) + len(REV_PRIMER) + BARCODE_LENGTH  # 50 nt
VARIABLE_LENGTH = TOTAL_LENGTH - FIXED_LENGTH  # 120 nt for flanks + designed seq


def hamming_distance(s1, s2):
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))


def generate_barcode(existing_barcodes, length=12, gc_target=6, min_hamming=4, max_attempts=100000):
    for _ in range(max_attempts):
        gc_count = gc_target
        at_count = length - gc_count
        bases = random.sample(
            ['G'] * (gc_count // 2) + ['C'] * (gc_count - gc_count // 2) +
            ['A'] * (at_count // 2) + ['T'] * (at_count - at_count // 2),
            length
        )
        barcode = ''.join(bases)
        if all(hamming_distance(barcode, b) >= min_hamming for b in existing_barcodes):
            return barcode
    raise ValueError(
        f"Could not find a valid barcode after {max_attempts} attempts. "
        "Try reducing the number of sequences or the minimum Hamming distance."
    )


def generate_flank(length, max_run=3):
    """Random C/T sequence with no run longer than max_run."""
    if length == 0:
        return ""
    bases = ['C', 'T']
    result = []
    while len(result) < length:
        b = random.choice(bases)
        if len(result) >= max_run and all(result[-i] == b for i in range(1, max_run + 1)):
            continue
        result.append(b)
    return ''.join(result)


def build_library(sequences, output_prefix="oligo_library", seed=None):
    if seed is not None:
        random.seed(seed)

    barcodes_used = []
    records = []

    for name, designed_seq in sequences:
        designed_seq = designed_seq.upper().strip().replace('U', 'T')
        flank_total = VARIABLE_LENGTH - len(designed_seq)

        if flank_total < 0:
            raise ValueError(
                f"Designed sequence '{name}' is {len(designed_seq)} nt, which is too long. "
                f"Max allowed is {VARIABLE_LENGTH} nt."
            )

        left_len = flank_total // 2
        right_len = flank_total - left_len

        left_flank = generate_flank(left_len)
        right_flank = generate_flank(right_len)
        barcode = generate_barcode(barcodes_used)
        barcodes_used.append(barcode)

        full_seq = FWD_PRIMER + left_flank + designed_seq + right_flank + barcode + REV_PRIMER
        assert len(full_seq) == TOTAL_LENGTH, (
            f"Length error for '{name}': got {len(full_seq)}, expected {TOTAL_LENGTH}"
        )

        records.append({
            "name": name,
            "sequence": full_seq,
            "barcode": barcode,
            "left_flank": left_flank,
            "designed_seq": designed_seq,
            "right_flank": right_flank,
        })

    # Detailed CSV output
    csv_path = f"{output_prefix}.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["name", "sequence", "barcode",
                                                "left_flank", "designed_seq", "right_flank"])
        writer.writeheader()
        writer.writerows(records)

    # Stitched CSV (name + full sequence only, for ordering)
    stitched_path = f"{output_prefix}_stitched.csv"
    with open(stitched_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["name", "sequence"])
        for r in records:
            writer.writerow([r["name"], r["sequence"]])

    # FASTA output
    fasta_path = f"{output_prefix}.fasta"
    with open(fasta_path, 'w') as f:
        for r in records:
            f.write(f">{r['name']}\n{r['sequence']}\n")

    print(f"Generated {len(records)} sequences -> {csv_path}, {stitched_path}, {fasta_path}")
    return records


def load_sequences_from_csv(csv_path):
    """Load (name, sequence) pairs from a CSV with 'name' and 'sequence' columns."""
    sequences = []
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sequences.append((row["name"], row["sequence"]))
    return sequences


if __name__ == "__main__":
    import os
    if len(sys.argv) < 2:
        print("Usage: python build_oligo_library.py <input.csv> [output_prefix]")
        print("  input.csv must have 'name' and 'sequence' columns.")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_prefix = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(input_csv)[0] + "_library"

    sequences = load_sequences_from_csv(input_csv)
    print(f"Loaded {len(sequences)} sequences from {input_csv}")
    build_library(sequences, output_prefix=output_prefix)
