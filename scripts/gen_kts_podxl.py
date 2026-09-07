#!/usr/bin/env python3
"""Generate an RNArtistCore .kts script to visually verify the PODXL
wildtype parent windows in podxl_library_parent.txt. All residues neutral;
the ADAR target A edit site in red. Same rendering convention as
gen_kts_parents.py."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


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


def main():
    entries = parse_parents(os.path.join(ROOT, "podxl_library_parent.txt"))

    out = []
    for name, s, db, edits in entries:
        label = name
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
    with open(os.path.join(HERE, "podxl_parent_verify.kts"), "w") as fh:
        fh.write(script)

    print(f"{'molecule':<28} {'len':>3}  edit(red)   dot-bracket")
    for name, s, db, edits in entries:
        print(f"{name:<28} {len(s):>3}  {str(edits):<10}  {db}")


if __name__ == "__main__":
    main()
