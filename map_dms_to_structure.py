#!/usr/bin/env python3
"""Paint DMS-MaPseq reactivity onto a parent's secondary structure.

Takes a reactivity table, converts it into the parent's coordinate frame, and
writes an RNArtistCore script that colours each residue by its reactivity. Also
reports where the measurement disagrees with the predicted structure, which is
the point of running DMS in the first place.

COORDINATE FRAMES.  Reactivity usually comes out in oligo coordinates (1-170:
primer, flank, designed RNA, flank, barcode, primer), while the structure is in
parent coordinates. Pass --frame oligo and the design's reference name and the
offset is worked out from oligo_master_mapping.csv. Getting this wrong silently
shifts every value, so the offset used is always printed.

WHAT DMS MEASURES.  DMS modifies the Watson-Crick face of A (N1) and C (N3)
only. G and U carry no information and are dropped rather than drawn as zero,
so a cold G is never mistaken for a protected one.

Usage:
    # reactivities in oligo coordinates, for a named design
    python3 map_dms_to_structure.py reactivity.txt \\
        --reference "5-HT2C_2 71nt 43% original full" --frame oligo

    # already in parent coordinates
    python3 map_dms_to_structure.py reactivity.txt --parent 5-HT2C_2 --frame parent

    # render straight away
    python3 map_dms_to_structure.py ... --jar ~/tools/rnartistcore-0.4.8-*.jar

Input: one "position value" pair per line; '#' comments and blank lines ignored.
CSV/TSV with a header is accepted too, as long as the first two columns are
position and value.
"""
import argparse
import csv
import re
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from generate_gc_library import parse, pair_map  # noqa: E402

PARENT_FILES = ["adar_library_1_2.txt", "adar_library_2.txt"]
MAPPING = "oligo_master_mapping.csv"

# DMS hits the Watson-Crick face of these only.
REACTIVE = {"A", "C"}

COLD, HOT = "#FFF3C4", "#B2182B"     # gradient ends, low -> high reactivity
UNINFORMATIVE = "#E8E8E8"            # G and U: not measured, not "protected"
EDIT_RING = "#1A1A1A"


def load_reactivity(path):
    """Read 'position value' pairs. Tolerates CSV/TSV and a header line."""
    vals = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(4096)
        f.seek(0)
        delim = None
        for d in (",", "\t"):
            if d in sample.splitlines()[0] if sample.splitlines() else False:
                delim = d
                break
        rows = csv.reader(f, delimiter=delim) if delim else (
            line.split() for line in f)
        for row in rows:
            row = [c.strip() for c in row if c.strip()]
            if len(row) < 2 or row[0].startswith("#"):
                continue
            try:
                pos, val = int(float(row[0])), float(row[1])
            except ValueError:
                continue                      # header or junk line
            vals[pos] = val
    if not vals:
        sys.exit(f"no numeric position/value pairs found in {path}")
    return vals


def find_parent(name):
    for pf in PARENT_FILES:
        path = os.path.join(HERE, pf)
        if not os.path.exists(path):
            continue
        for n, seq, struct, sites in parse(path):
            if n == name:
                return seq, struct, sites
    sys.exit(f"parent {name!r} not found in {PARENT_FILES}")


def resolve_offset(reference, frame):
    """Return (parent_name, oligo_to_parent_offset, design_seq).

    parent_position = oligo_position - offset
    """
    if frame == "parent":
        return None, 0, None

    path = os.path.join(HERE, MAPPING)
    if not os.path.exists(path):
        sys.exit(f"{MAPPING} not found — run build_mapping.py first")
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    ref = reference.strip()
    hit = next((r for r in rows if r["oligo_id"] == ref), None)

    if hit is None:
        # Match on the parts that identify a design, ignoring the GC percentage:
        # it is derived from the sequence and is easy to misquote.
        tokens = [t for t in re.split(r"[\s,]+", ref) if t and not t.endswith("%")]
        def score(r):
            hay = (f"{r['parent']} {r['design_length']}nt {r['mutation_label']} "
                   f"{r['trim_mode']} {r['oligo_id']} {r['primer']}").lower()
            return sum(1 for t in tokens if t.lower() in hay)
        best = max((score(r) for r in rows), default=0)
        cand = [r for r in rows if score(r) == best and best == len(tokens)]
        if not cand:
            sys.exit(f"reference {ref!r} matched nothing. Give an oligo_id "
                     "(e.g. ART5_00195) or 'PARENT LENnt LABEL MODE'.")
        if len({r["designed_seq"] for r in cand}) > 1:
            sys.exit(f"reference {ref!r} matched {len(cand)} different designs:\n  "
                     + "\n  ".join(f"{r['oligo_id']}  {r['parent']} "
                                   f"{r['design_length']}nt {r['gc_pct']}% "
                                   f"{r['mutation_label']} {r['trim_mode']}"
                                   for r in cand[:10])
                     + "\nPass an oligo_id to disambiguate.")
        hit = cand[0]
        print(f"reference resolved to {hit['oligo_id']}  ({hit['parent']} "
              f"{hit['design_length']}nt {hit['gc_pct']}% {hit['mutation_label']} "
              f"{hit['trim_mode']})")

    full, design = hit["full_oligo"], hit["designed_seq"]
    start_in_oligo = full.index(design) + 1            # 1-based
    seq, struct, _ = find_parent(hit["parent"])
    wt = seq.replace("U", "T")
    if design not in wt:
        sys.exit(f"{hit['oligo_id']} is a mutant; its sequence is not a "
                 "contiguous stretch of the parent, so reactivity cannot be "
                 "mapped onto the wild-type structure. Use the unmutated "
                 "design, or map onto the mutant's own structure.")
    start_in_parent = wt.index(design) + 1
    offset = start_in_oligo - start_in_parent
    return hit["parent"], offset, design


def agreement(seq, struct, sites, parent_vals, hi, lo):
    """Compare measured reactivity against the predicted pairing state."""
    P = pair_map(struct)
    rows = []
    for pos, val in sorted(parent_vals.items()):
        i = pos - 1
        if i < 0 or i >= len(seq):
            continue
        base = seq[i].replace("T", "U")
        if base not in REACTIVE:
            continue
        paired = P[i] != -1
        if paired and val >= hi:
            verdict = "CONFLICT — predicted paired, strongly reactive"
        elif not paired and val <= lo:
            verdict = "CONFLICT — predicted unpaired, unreactive"
        elif paired and val <= lo:
            verdict = "agrees (paired, protected)"
        elif not paired and val >= hi:
            verdict = "agrees (unpaired, reactive)"
        else:
            verdict = "ambiguous (mid-range)"
        rows.append((pos, base, "paired" if paired else "unpaired",
                     val, pos in sites, verdict))
    return rows


def write_kts(path, vienna_path, out_dir, seq, sites, parent_vals, vmax, details=5):
    data_lines = "\n".join(f"    {p} to {v:.6g}" for p, v in sorted(parent_vals.items()))
    site_locs = "\n".join(f"          {s} to {s}" for s in sites)
    with open(path, "w") as f:
        f.write(f'''import io.github.fjossinet.rnartist.core.*

rnartist {{
  ss {{
    vienna {{
      file = "{vienna_path}"
    }}
  }}

  // data must precede theme and layout
  data {{
{data_lines}
  }}

  theme {{
    details {{
      value = {details}
    }}

    // G and U carry no DMS signal — grey, not "protected"
    color {{
      type = "G"
      value = "{UNINFORMATIVE}"
    }}
    color {{
      type = "U"
      value = "{UNINFORMATIVE}"
    }}

    // A and C painted by reactivity
    color {{
      type = "A"
      value = "{COLD}"
      to = "{HOT}"
      data between 0.0..{vmax:.6g}
    }}
    color {{
      type = "C"
      value = "{COLD}"
      to = "{HOT}"
      data between 0.0..{vmax:.6g}
    }}

    color {{
      type = "n"
      value = "#1A1A1A"
    }}

    // edit sites outlined so they stay findable under the gradient
    color {{
      type = "n"
      value = "#0B5FFF"
      location {{
{site_locs}
      }}
    }}
  }}

  svg {{
    path = "{out_dir}"
  }}
  png {{
    path = "{out_dir}"
  }}
}}
''')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reactivity", help="position/value table")
    ap.add_argument("--reference", help="design name or oligo_id the reads were mapped to")
    ap.add_argument("--parent", help="parent name (required with --frame parent)")
    ap.add_argument("--frame", choices=["oligo", "parent"], default="oligo",
                    help="coordinate frame of the input (default: oligo)")
    ap.add_argument("--offset", type=int,
                    help="override: parent_position = input_position - offset")
    ap.add_argument("--hi", type=float, default=0.4, help="reactive threshold")
    ap.add_argument("--lo", type=float, default=0.1, help="protected threshold")
    ap.add_argument("--out", default=os.path.join(HERE, "scripts", "dms"))
    ap.add_argument("--jar", help="rnartistcore jar; renders immediately if given")
    args = ap.parse_args()

    vals = load_reactivity(args.reactivity)
    print(f"read {len(vals)} positions from {os.path.basename(args.reactivity)}"
          f"  (range {min(vals)}–{max(vals)})")

    if args.frame == "parent":
        if not args.parent:
            ap.error("--frame parent requires --parent")
        parent_name, offset, design = args.parent, 0, None
    else:
        if not args.reference:
            ap.error("--frame oligo requires --reference")
        parent_name, offset, design = resolve_offset(args.reference, args.frame)
    if args.offset is not None:
        offset = args.offset
    print(f"parent: {parent_name}   offset: {offset}   "
          f"(parent_position = input_position - {offset})")

    seq, struct, sites = find_parent(parent_name)

    # Only accept positions covered by the design itself. Clipping to the parent
    # is not enough: a trimmed design starts inside the parent, so flank
    # reactivity either side would otherwise land on real parent positions and
    # be read as structural signal.
    if design:
        lo = seq.replace("U", "T").index(design) + 1
        hi = lo + len(design) - 1
    else:
        lo, hi = 1, len(seq)
    parent_vals = {p - offset: v for p, v in vals.items()
                   if lo <= p - offset <= hi}
    dropped = len(vals) - len(parent_vals)
    print(f"{len(parent_vals)} positions land inside the designed region "
          f"(parent {lo}-{hi} of {len(seq)} nt)"
          + (f"; {dropped} outside it (primer, flank, barcode, or parent "
             "sequence this design does not cover) are dropped" if dropped else ""))
    if not parent_vals:
        sys.exit("nothing maps into the parent — check --frame / --offset")

    rows = agreement(seq, struct, sites, parent_vals, args.hi, args.lo)
    vmax = max(parent_vals.values())

    print(f"\nDMS-informative positions (A/C only): {len(rows)}")
    conflicts = [r for r in rows if r[5].startswith("CONFLICT")]
    print(f"  agree: {sum(1 for r in rows if r[5].startswith('agrees'))}"
          f"   ambiguous: {sum(1 for r in rows if r[5].startswith('ambiguous'))}"
          f"   CONFLICT: {len(conflicts)}")

    if conflicts:
        print("\nPositions where the measurement disagrees with the model:")
        print(f"  {'pos':>5} {'base':>4} {'predicted':>10} {'reactivity':>11}  note")
        for pos, base, state, val, is_site, verdict in conflicts:
            star = "  <-- EDIT SITE" if is_site else ""
            print(f"  {pos:>5} {base:>4} {state:>10} {val:>11.4g}  "
                  f"{verdict.split('— ')[1]}{star}")

    print("\nEdit sites:")
    for pos, base, state, val, is_site, verdict in rows:
        if is_site:
            print(f"  A{pos}: {state}, reactivity {val:.4g} — {verdict}")

    os.makedirs(args.out, exist_ok=True)
    stem = f"{parent_name.replace('/', '-')}_dms"
    vienna = os.path.abspath(os.path.join(args.out, f"{stem}.vienna"))
    with open(vienna, "w") as f:
        f.write(f">{stem}\n{seq}\n{struct}\n")
    kts = os.path.abspath(os.path.join(args.out, f"{stem}.kts"))
    write_kts(kts, vienna, os.path.abspath(args.out), seq, sites, parent_vals, vmax)
    print(f"\nwrote {kts}")

    if args.jar:
        r = subprocess.run(["java", "-jar", os.path.abspath(args.jar), kts],
                           capture_output=True, text=True, timeout=600)
        svg = os.path.join(args.out, f"{stem}.svg")
        if r.returncode == 0 and os.path.exists(svg):
            print(f"rendered {svg}")
        else:
            print("render failed:", (r.stderr or r.stdout).strip().splitlines()[-1:])
            return 1
    else:
        print("render with:  java -jar <rnartistcore.jar> " + kts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
