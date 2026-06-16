#!/usr/bin/env python3
"""Generate an RNArtistCore .kts script to visually verify NEIL1 parent + its
10 largest children. Each child's dot-bracket is derived from the PARENT's
structure via the CSV 'Parent Positions' column (a bracket survives only if its
partner is also retained -> always balanced), exactly matching the repo's
generate_length_library.render(). All residues neutral; A edit sites in red."""
import ast
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PARENT_NAME = "NEIL1"
N_CHILDREN = 10

OPENERS = "([{<"
CLOSERS = ")]}>"
PAIRS = dict(zip(CLOSERS, OPENERS))


def pair_map(struct):
    stacks = {o: [] for o in OPENERS}
    P = [-1] * len(struct)
    for i, c in enumerate(struct):
        if c in OPENERS:
            stacks[c].append(i)
        elif c in CLOSERS:
            j = stacks[PAIRS[c]].pop()
            P[i], P[j] = j, i
    return P


def render(seq, struct, idx0):
    """idx0 = 0-based retained parent indices."""
    P = pair_map(struct)
    keep = set(idx0)
    child_seq = "".join(seq[i] for i in idx0)
    chars = []
    for i in idx0:
        if P[i] != -1 and P[i] in keep:
            chars.append("(" if i < P[i] else ")")
        else:
            chars.append(".")
    return child_seq, "".join(chars)


def parse_parent(path, name):
    with open(path) as fh:
        blocks = [b for b in fh.read().split("\n\n") if b.strip()]
    for b in blocks:
        lines = [l.strip() for l in b.splitlines() if l.strip()]
        if lines[0] == name:
            seq = lines[1].lstrip(">")
            struct = lines[2]
            edits = [int(t.split("_")[1]) for t in
                     lines[3].split(":", 1)[1].split(",")]
            return seq, struct, edits
    raise SystemExit(f"{name} not found")


def main():
    seq, struct, p_edits = parse_parent(
        os.path.join(ROOT, "adar_library_1_1.txt"), PARENT_NAME)
    struct = struct.rstrip()

    # children rows for this parent, by descending length
    rows = []
    with open(os.path.join(ROOT, "length_library.csv")) as fh:
        for r in csv.DictReader(fh):
            if r["Parent Structure"] == PARENT_NAME:
                rows.append(r)
    rows.sort(key=lambda r: int(r["Length"]), reverse=True)
    children = rows[:N_CHILDREN]

    # entry = (label, seq, struct, [1-based edit positions in this molecule])
    entries = []
    entries.append((f"{PARENT_NAME}_parent_{len(seq)}nt", seq, struct,
                    sorted(set(p_edits))))
    for r in children:
        pos1 = ast.literal_eval(r["Parent Positions"])      # 1-based parent pos
        idx0 = [p - 1 for p in pos1]
        cseq, cstruct = render(seq, struct, idx0)
        assert cseq == r["Sequence"], (cseq, r["Sequence"])
        e = ast.literal_eval(r["Edit Sites"])                # 1-based child pos
        ref = r["Reference"].replace(" ", "_").replace("%", "pct")
        entries.append((ref, cseq, cstruct, sorted(set(e))))

    # emit one rnartist{} block per molecule
    out = []
    for label, s, db, edits in entries:
        loc = "\n".join(f"          {p} to {p}" for p in edits)
        out.append(f'''rnartist {{
  svg {{ path = "{HERE}/out" }}
  ss {{ bn {{ seq = "{s}" ; value = "{db}" ; name = "{label}" }} }}
  theme {{
    details {{ value = 5 }}
    color {{ type = "N" ; value = "#D9D9D9" }}   // all residue shapes neutral grey
    color {{ type = "n" ; value = "#222222" }}   // all residue letters (ACGU) dark
    color {{                                       // A edit-site shapes -> red
      type = "N" ; value = "red"
      location {{
{loc}
      }}
    }}
    color {{                                       // edit-site letters -> white for contrast
      type = "n" ; value = "white"
      location {{
{loc}
      }}
    }}
  }}
}}''')
    script = "\n\n".join(out) + "\n"
    with open(os.path.join(HERE, "neil1_verify.kts"), "w") as fh:
        fh.write(script)

    # human-readable manifest
    print(f"{'molecule':<28} {'len':>3}  edit(red)   dot-bracket")
    for label, s, db, edits in entries:
        print(f"{label:<28} {len(s):>3}  {str(edits):<10}  {db}")


if __name__ == "__main__":
    main()
