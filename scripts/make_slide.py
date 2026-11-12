#!/usr/bin/env python3
"""Compose a 16:9 slide pairing a reactivity plot with its RNArtist structure.

The two panels normally arrive in DIFFERENT coordinate frames: reactivity comes
out in oligo coordinates (primer + flank + design + flank + barcode + primer)
while the structure is numbered along the parent. Reading across them without
saying so is a misreading waiting to happen, so the offset is computed from
oligo_master_mapping.csv and printed on the slide itself.

Usage:
    python3 scripts/make_slide.py --parent hGLI1 --plot plot.png
    python3 scripts/make_slide.py --parent hGLI1 --plot plot.png --crop 0,130,815,660
"""
import argparse
import csv
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from generate_gc_library import parse  # noqa: E402

W, H = 2560, 1440                     # 16:9
MARGIN = 70
TITLE_H = 120
CAPTION_H = 150
GUTTER = 60

INK = (26, 26, 26)
MUTED = (110, 110, 110)
ACCENT = (31, 78, 121)
EDIT = (227, 73, 72)
BG = (255, 255, 255)

PARENT_FILES = ["adar_library_1_2.txt", "adar_library_2.txt"]


def font(size, bold=False):
    names = ["DejaVuSans-Bold.ttf"] if bold else ["DejaVuSans.ttf"]
    for n in names:
        for d in ("/usr/share/fonts/truetype/dejavu/", "/usr/share/fonts/TTF/"):
            p = os.path.join(d, n)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def parent_record(name):
    for pf in PARENT_FILES:
        p = os.path.join(ROOT, pf)
        if not os.path.exists(p):
            continue
        for n, seq, struct, sites in parse(p):
            if n == name:
                return seq, struct, sites
    sys.exit(f"parent {name!r} not found")


def offset_for(name, design_length=None):
    """parent_position = oligo_position - offset, for the unmutated design."""
    path = os.path.join(ROOT, "oligo_master_mapping.csv")
    if not os.path.exists(path):
        return None, None
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [r for r in csv.DictReader(f)
                if r["parent"] == name and r["mutation_label"] == "original"]
    if not rows:
        return None, None
    if design_length:
        rows = [r for r in rows if int(r["design_length"]) == design_length] or rows
    r = max(rows, key=lambda r: int(r["design_length"]))
    start = r["full_oligo"].index(r["designed_seq"]) + 1
    return start - 1, int(r["design_length"])


def trim_border(im, tol=28):
    """Drop uniform near-black or near-white margins left by a screenshot crop."""
    import numpy as np
    a = np.asarray(im.convert("RGB")).astype(int)
    dark = a.sum(2) < tol * 3
    light = a.sum(2) > (255 - tol) * 3
    keep = ~(dark | light)
    rows = np.where(keep.any(1))[0]
    cols = np.where(keep.any(0))[0]
    if not len(rows) or not len(cols):
        return im
    return im.crop((int(cols.min()), int(rows.min()),
                    int(cols.max()) + 1, int(rows.max()) + 1))


def split_columns(im, n, search=0.08):
    """Cut a very tall drawing into n stacked slices shown side by side.

    The cut is nudged to the emptiest row near each ideal boundary, so it falls
    between rows of residues instead of slicing through one.
    """
    if n <= 1:
        return [im]
    import numpy as np
    ink = (np.asarray(im.convert("L")).astype(int) < 235).sum(1)
    window = max(4, int(im.height * search / n))
    cuts = [0]
    for i in range(1, n):
        ideal = im.height * i // n
        lo, hi = max(1, ideal - window), min(im.height - 1, ideal + window)
        cuts.append(lo + int(np.argmin(ink[lo:hi])))
    cuts.append(im.height)
    return [im.crop((0, cuts[i], im.width, cuts[i + 1])) for i in range(n)]


def fit(im, box_w, box_h):
    s = min(box_w / im.width, box_h / im.height)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))),
                     Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parent", required=True)
    ap.add_argument("--plot", required=True, help="reactivity plot image")
    ap.add_argument("--structure", help="structure image (default: the hi-res render)")
    ap.add_argument("--crop", help="crop the plot first: left,top,right,bottom")
    ap.add_argument("--design-length", type=int,
                    help="which design the reactivity came from")
    ap.add_argument("--split", type=int, default=2,
                    help="cut the tall structure into this many side-by-side "
                         "slices so residues render larger (default 2; 1 = off)")
    ap.add_argument("--title")
    ap.add_argument("-o", "--output", default=None)
    args = ap.parse_args()

    seq, struct, sites = parent_record(args.parent)
    off, dlen = offset_for(args.parent, args.design_length)

    plot = Image.open(args.plot).convert("RGB")
    if args.crop:
        plot = plot.crop(tuple(int(v) for v in args.crop.split(",")))
    plot = trim_border(plot)

    spath = args.structure or os.path.join(
        HERE, "rnartist", "set1_hires", f"{args.parent}.png")
    if not os.path.exists(spath):
        sys.exit(f"structure image not found: {spath}\nPass --structure")
    structure = Image.open(spath).convert("RGB")

    canvas = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(canvas)

    body_top = MARGIN + TITLE_H
    body_h = H - body_top - CAPTION_H - MARGIN

    # A hairpin render is extremely tall and thin (aspect ~1:6), so fitting it
    # to the slide height leaves the residues unreadable when projected.
    # Cutting it into stacked slices shown side by side multiplies the usable
    # height and lets each residue be drawn several times larger.
    slices = split_columns(structure, args.split)
    SGAP = 18
    s_h = body_h
    scaled = []
    for sl in slices:
        sc = min((int(W * 0.30) - SGAP * (len(slices) - 1)) / (sl.width * len(slices)),
                 s_h / sl.height)
        scaled.append(sl.resize((max(1, int(sl.width * sc)),
                                 max(1, int(sl.height * sc))), Image.LANCZOS))
    s_w = sum(i.width for i in scaled) + SGAP * (len(scaled) - 1)

    p_im = fit(plot, W - 2 * MARGIN - GUTTER - s_w, body_h)

    px = MARGIN
    py = body_top + (body_h - p_im.height) // 2
    canvas.paste(p_im, (px, py))

    sx = W - MARGIN - s_w
    x = sx
    for i in scaled:
        canvas.paste(i, (x, body_top + (body_h - i.height) // 2))
        x += i.width + SGAP

    title = args.title or f"{args.parent} — DMS reactivity and predicted structure"
    dr.text((MARGIN, MARGIN - 10), title, font=font(54, True), fill=INK)

    f_lab = font(30, True)
    dr.text((px, body_top - 46), "A   ΔDMS mutation signal", font=f_lab, fill=ACCENT)
    dr.text((sx, body_top - 46), "B   Structure", font=f_lab, fill=ACCENT)

    # the part that stops the two panels being misread against each other
    f_cap, f_small = font(30), font(26)
    cy = H - CAPTION_H - 10
    site_txt = ", ".join(f"A{s}" for s in sites)
    if off is not None:
        mapped = ", ".join(f"A{s} → {s + off}" for s in sites)
        dr.text((MARGIN, cy),
                f"Panel A is numbered along the 170 nt oligo (primer + flank + "
                f"{dlen} nt design + flank + barcode + primer); panel B along "
                f"the {len(seq)} nt parent.    parent = oligo − {off}",
                font=f_cap, fill=INK)
        dr.text((MARGIN, cy + 44),
                f"Edit site in panel B (red): {site_txt}  —  in panel A coordinates: "
                f"{mapped}",
                font=f_small, fill=EDIT)
    else:
        dr.text((MARGIN, cy),
                f"Edit site (red): {site_txt}. Check that both panels use the same "
                "numbering before reading across them.",
                font=f_cap, fill=EDIT)
    dr.text((MARGIN, cy + 88),
            "DMS probes the Watson–Crick face of A and C only; G and U carry no signal.",
            font=f_small, fill=MUTED)

    out = args.output or os.path.join(HERE, f"slide_{args.parent.replace('/', '-')}.png")
    canvas.save(out, dpi=(300, 300))
    print(f"wrote {out}  ({W}x{H})")
    if off is not None:
        print(f"coordinate note: parent = oligo - {off};  "
              + "; ".join(f"A{s} is at plot position {s + off}" for s in sites))


if __name__ == "__main__":
    main()
