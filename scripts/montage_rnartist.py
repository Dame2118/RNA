#!/usr/bin/env python3
"""Lay the RNArtistCore parent renders out on one sheet per set.

RNArtistCore writes one SVG per molecule at its natural size, and hairpins vary
enormously in height (326 to 1125 px). This rasterises each SVG at high
resolution, scales every molecule by the SAME factor so residue sizes stay
comparable across panels, and arranges them on a common baseline with the name
and edit sites captioned underneath.

Usage:
    python3 scripts/montage_rnartist.py
    python3 scripts/montage_rnartist.py --scale 3 --cols 10
"""
import argparse
import csv
import glob
import os
import sys

import cairosvg
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from generate_gc_library import parse  # noqa: E402

SETS = {
    "set1": ("adar_library_1_2.txt", "Set 1 parents — ART5 / ART10"),
    "set2": ("adar_library_2.txt", "Set 2 parents — ART7 / ART11"),
}

PAD = 26          # gap between panels
CAPTION_H = 54    # room under each molecule for its label
MARGIN = 40
TITLE_H = 62
BG = (255, 255, 255)
INK = (34, 34, 34)
MUTED = (110, 110, 110)


def font(size, bold=False):
    names = (["DejaVuSans-Bold.ttf", "DejaVuSans.ttf"] if bold else ["DejaVuSans.ttf"])
    for n in names:
        for d in ("/usr/share/fonts/truetype/dejavu/", "/usr/share/fonts/TTF/",
                  "/usr/share/fonts/"):
            p = os.path.join(d, n)
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except OSError:
                    pass
    return ImageFont.load_default()


def strip_reactivity_legend(svg_path):
    """RNArtistCore appends a 'Reactivity' colour-scale legend to every SVG.

    It is placed at negative x, so RNArtist's own PNG crops it away but a
    faithful rasteriser draws the part that falls inside the viewBox — a stray
    red gradient bar under each molecule. There is no reactivity data here, so
    drop the block entirely. Returns SVG source, never touching the file.
    """
    s = open(svg_path).read()
    i = s.find("<defs>")
    if i != -1 and "reactivities_scale" in s[i:]:
        s = s[:i] + "</svg>"
    return s


def sites_for(src):
    out = {}
    for name, seq, struct, sites in parse(os.path.join(ROOT, src)):
        out[name.replace("/", "-").replace(" ", "_")] = (name, len(seq), sites)
    return out


def render(tag, src, title, scale, cols, outdir):
    d = os.path.join(HERE, "rnartist", tag)
    svgs = sorted(glob.glob(os.path.join(d, "*.svg")))
    if not svgs:
        print(f"{tag}: no SVGs in {d}")
        return None

    meta = sites_for(src)
    panels = []
    for s in svgs:
        stem = os.path.splitext(os.path.basename(s))[0]
        png = cairosvg.svg2png(bytestring=strip_reactivity_legend(s).encode(),
                               scale=scale)
        im = Image.open(__import__("io").BytesIO(png)).convert("RGBA")
        flat = Image.new("RGBA", im.size, (255, 255, 255, 255))
        flat.alpha_composite(im)
        name, length, sites = meta.get(stem, (stem, 0, []))
        panels.append((name, length, sites, flat.convert("RGB")))

    rows = [panels[i:i + cols] for i in range(0, len(panels), cols)]
    row_h = [max(p[3].height for p in r) + CAPTION_H for r in rows]
    col_w = max(max(p[3].width for p in r) for r in rows) + PAD

    W = MARGIN * 2 + col_w * min(cols, len(panels))
    H = MARGIN * 2 + TITLE_H + sum(row_h)
    sheet = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(sheet)

    f_title, f_name, f_sub = font(30, True), font(17, True), font(14)
    dr.text((MARGIN, MARGIN), title, font=f_title, fill=INK)

    y = MARGIN + TITLE_H
    for r, rh in zip(rows, row_h):
        base = y + max(p[3].height for p in r)
        for i, (name, length, sites, im) in enumerate(r):
            x = MARGIN + i * col_w + (col_w - PAD - im.width) // 2
            sheet.paste(im, (x, base - im.height))
            cx = MARGIN + i * col_w + col_w // 2
            label = name
            while dr.textlength(label, font=f_name) > col_w - 8 and len(label) > 8:
                label = label[:-2]
                if label != name:
                    label = label[:-1] + "…"
            dr.text((cx - dr.textlength(label, font=f_name) / 2, base + 10),
                    label, font=f_name, fill=INK)
            sub = f"{length} nt · " + ", ".join(f"A{s}" for s in sites)
            if dr.textlength(sub, font=f_sub) > col_w - 8:
                sub = f"{length} nt · {len(sites)} edit sites"
            dr.text((cx - dr.textlength(sub, font=f_sub) / 2, base + 32),
                    sub, font=f_sub, fill=MUTED)
        y += rh

    out = os.path.join(outdir, f"rnartist_parents_{tag}.png")
    sheet.save(out, dpi=(200, 200))
    print(f"wrote {out}  ({len(panels)} parents, {W}x{H})")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scale", type=float, default=3.0, help="SVG rasterisation factor")
    ap.add_argument("--cols", type=int, default=10)
    ap.add_argument("--out", default=HERE)
    args = ap.parse_args()

    for tag, (src, title) in sorted(SETS.items()):
        render(tag, src, title, args.scale, args.cols, args.out)


if __name__ == "__main__":
    main()
