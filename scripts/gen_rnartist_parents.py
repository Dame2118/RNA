#!/usr/bin/env python3
"""Render every contributing parent hairpin with RNArtistCore.

Writes one Vienna file and one RNArtistCore script per parent, then runs the
RNArtistCore jar over each to produce an SVG and a PNG. Residues are neutral
grey; annotated edit-site adenosines are red with a white letter.

Only parents that actually contribute designs to a library are rendered, read
from the library CSVs rather than the parent file — a record can parse cleanly
and still produce nothing (see CLAUDE.md).

RNArtistCore is not vendored; fetch the fat jar once (66 MB):

    curl -O https://repo1.maven.org/maven2/io/github/fjossinet/rnartist/\\
rnartistcore/0.4.8/rnartistcore-0.4.8-jar-with-dependencies.jar

    sha256 cd08603bd718455f428cc9c07387023a5c5d96c88768f43eb276dbca235788b8

Usage:
    python3 scripts/gen_rnartist_parents.py --jar /path/to/rnartistcore.jar
    python3 scripts/gen_rnartist_parents.py --jar ... --only set1
"""
import argparse
import csv
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from generate_gc_library import parse  # noqa: E402

SETS = {
    "set1": ("adar_library_1_2.txt", ["gc_library.csv", "gc_library2.csv"]),
    "set2": ("adar_library_2.txt", ["gc_library_set2.csv", "gc_library_set2b.csv"]),
}

NEUTRAL_SHAPE = "#E8E8E8"
NEUTRAL_LETTER = "#222222"
EDIT_SHAPE = "#E34948"
EDIT_LETTER = "#FFFFFF"
DETAILS = 5

# Per-base palette for --color-bases: {base: (shape, letter)}.
#
# Four base hues plus the reserved edit-site red are five colours that appear
# adjacent to each other in arbitrary combinations, so they were chosen against
# the all-pairs criteria rather than by eye. This set clears the lightness band,
# the chroma floor and the normal-vision separation floor (worst pair
# violet/blue, dE 16.3). Red/aqua sits at dE 6.9 under deuteranopia, inside the
# floor band that is permitted only with secondary encoding — satisfied here
# because every residue is drawn with its own letter.
#
# Magenta in place of violet or aqua fails outright: magenta/red is dE 13.2 to
# normal vision, under the floor of 15. Letters are white on the two dark hues
# and near-black on the two light ones.
BASE_COLORS = {
    "A": ("#4A3AA7", "#FFFFFF"),   # violet — maximally unlike the edit-site red
    "U": ("#EDA100", "#1A1A1A"),   # yellow
    "G": ("#2A78D6", "#FFFFFF"),   # blue
    "C": ("#1BAF7A", "#1A1A1A"),   # aqua
}


def contributing(csv_names):
    names = set()
    for c in csv_names:
        path = os.path.join(ROOT, c)
        if not os.path.exists(path):
            continue
        with open(path, newline="", encoding="utf-8-sig") as f:
            names |= {r["Parent Structure"] for r in csv.DictReader(f)}
    return names


def safe(name):
    return name.replace("/", "-").replace(" ", "_")


def write_vienna(path, name, seq, struct):
    with open(path, "w") as f:
        f.write(f">{name}\n{seq}\n{struct}\n")


def base_palette_block():
    """Per-base colours, written before the edit-site block so red overrides."""
    out = []
    for base, (shape, letter) in BASE_COLORS.items():
        out.append(f'''    color {{
      type = "{base}"
      value = "{shape}"
    }}
    color {{
      type = "{base.lower()}"
      value = "{letter}"
    }}''')
    return "\n".join(out)


def write_script(path, vienna_path, out_dir, sites, color_bases=False):
    locs = "\n".join(f"          {s} to {s}" for s in sites)
    if color_bases:
        base_block = base_palette_block()
    else:
        base_block = f'''    color {{
      type = "N"
      value = "{NEUTRAL_SHAPE}"
    }}
    color {{
      type = "n"
      value = "{NEUTRAL_LETTER}"
    }}'''
    with open(path, "w") as f:
        f.write(f'''import io.github.fjossinet.rnartist.core.*

rnartist {{
  ss {{
    vienna {{
      file = "{vienna_path}"
    }}
  }}
  theme {{
    details {{
      value = {DETAILS}
    }}
{base_block}
    color {{
      type = "N"
      value = "{EDIT_SHAPE}"
      location {{
{locs}
      }}
    }}
    color {{
      type = "n"
      value = "{EDIT_LETTER}"
      location {{
{locs}
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
    ap.add_argument("--jar", required=True, help="rnartistcore jar-with-dependencies")
    ap.add_argument("--out", default=os.path.join(HERE, "rnartist"))
    ap.add_argument("--only", choices=sorted(SETS), help="render one set only")
    ap.add_argument("--color-bases", action="store_true",
                    help="colour A/U/G/C individually instead of neutral grey; "
                         "edit sites stay red")
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()

    jar = os.path.abspath(args.jar)
    if not os.path.exists(jar):
        sys.exit(f"jar not found: {jar}")

    ok, failed = 0, []
    for tag, (src, csvs) in sorted(SETS.items()):
        if args.only and tag != args.only:
            continue
        keep = contributing(csvs)
        if not keep:
            print(f"{tag}: no library CSVs found, skipping")
            continue

        out_dir = os.path.abspath(os.path.join(args.out, tag))
        os.makedirs(out_dir, exist_ok=True)

        records = [r for r in parse(os.path.join(ROOT, src)) if r[0] in keep]
        print(f"\n{tag}: {len(records)} contributing parents -> {out_dir}")

        for name, seq, struct, sites in records:
            stem = safe(name)
            vienna = os.path.join(out_dir, f"{stem}.vienna")
            script = os.path.join(out_dir, f"{stem}.kts")
            write_vienna(vienna, stem, seq, struct)
            write_script(script, vienna, out_dir, sites, args.color_bases)

            r = subprocess.run(["java", "-jar", jar, script],
                               capture_output=True, text=True, timeout=args.timeout)
            svg = os.path.join(out_dir, f"{stem}.svg")
            if r.returncode == 0 and os.path.exists(svg):
                print(f"  ok   {name}  ({len(seq)} nt, {len(sites)} edit site(s))")
                ok += 1
            else:
                tail = (r.stderr or r.stdout).strip().splitlines()[-1:] or ["no output"]
                print(f"  FAIL {name}: {tail[0]}")
                failed.append(name)

    print(f"\nrendered {ok} parents"
          + (f", {len(failed)} failed: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
