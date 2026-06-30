#!/usr/bin/env python3
"""Generate a graphical summary figure of the ADAR library design."""
import csv
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np

# ── Load data ────────────────────────────────────────────────────────────────
def load(path):
    with open(path) as f:
        return list(csv.DictReader(f))

s1l1 = load('/home/user/RNA/gc_library.csv')
s1l2 = load('/home/user/RNA/gc_library2.csv')
s2l1 = load('/home/user/RNA/gc_library_set2.csv')
s2l2 = load('/home/user/RNA/gc_library_set2b.csv')

all_rows = s1l1 + s1l2 + s2l1 + s2l2

def mut_type(lbl):
    if lbl == 'original':       return 'Original'
    if 'above' in lbl and 'below' in lbl: return 'Combined\n(above+below)'
    if 'above' in lbl:          return 'Above'
    if 'below' in lbl:          return 'Below'
    if 'across' in lbl:         return 'Across'
    return 'Other'

# ── Palette ──────────────────────────────────────────────────────────────────
SET1_COL  = '#2E75B6'
SET2_COL  = '#ED7D31'
MUT_COLS  = {
    'Original':            '#A9D18E',
    'Above':               '#2E75B6',
    'Below':               '#ED7D31',
    'Across':              '#FFC000',
    'Combined\n(above+below)': '#7030A0',
}
LIB_COLS = {'Lib 1': '#2E75B6', 'Lib 2': '#9DC3E6'}

fig = plt.figure(figsize=(18, 13))
fig.patch.set_facecolor('#F7F9FC')
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.52, wspace=0.38)

# ── 1. Total entries per parent (stacked Lib1/Lib2) ──────────────────────────
ax1 = fig.add_subplot(gs[0, :2])

parents_s1 = sorted(set(r['Parent Structure'] for r in s1l1))
parents_s2 = sorted(set(r['Parent Structure'] for r in s2l1))

def counts(rows, parents):
    c1 = Counter(r['Parent Structure'] for r in rows[0])
    c2 = Counter(r['Parent Structure'] for r in rows[1])
    return [c1[p] for p in parents], [c2[p] for p in parents]

c1s1, c2s1 = counts((s1l1, s1l2), parents_s1)
c1s2, c2s2 = counts((s2l1, s2l2), parents_s2)

all_parents = parents_s1 + [''] + parents_s2
all_c1      = c1s1 + [0] + c1s2
all_c2      = c2s1 + [0] + c2s2
x = np.arange(len(all_parents))
w = 0.6

bars1 = ax1.bar(x, all_c1, w, color=LIB_COLS['Lib 1'], label='Library 1')
bars2 = ax1.bar(x, all_c2, w, bottom=all_c1, color=LIB_COLS['Lib 2'], label='Library 2')

# shade set backgrounds
ax1.axvspan(-0.5, len(parents_s1)-0.5, alpha=0.06, color=SET1_COL)
ax1.axvspan(len(parents_s1)+0.5, len(all_parents)-0.5, alpha=0.06, color=SET2_COL)
ax1.text(len(parents_s1)/2 - 0.5, 430, 'Set 1', ha='center', fontsize=11,
         color=SET1_COL, fontweight='bold')
ax1.text(len(parents_s1) + 1 + len(parents_s2)/2, 430, 'Set 2', ha='center',
         fontsize=11, color=SET2_COL, fontweight='bold')

short = [p.replace('LEAPER3_FLNA_', 'LEAPER_').replace('_AC_external_bulge','_ext') for p in all_parents]
ax1.set_xticks(x)
ax1.set_xticklabels(short, rotation=40, ha='right', fontsize=8)
ax1.set_ylabel('Entries', fontsize=10)
ax1.set_title('Library Entries per Parent Substrate', fontsize=12, fontweight='bold')
ax1.legend(fontsize=9, loc='upper right')
ax1.set_facecolor('#F7F9FC')
ax1.spines[['top','right']].set_visible(False)
ax1.set_ylim(0, 470)

# ── 2. Pie: mutation type breakdown ─────────────────────────────────────────
ax2 = fig.add_subplot(gs[0, 2])
mt_all = Counter(mut_type(r['Mutation Label']) for r in all_rows)
labels  = list(mt_all.keys())
sizes   = list(mt_all.values())
colors  = [MUT_COLS.get(l, '#BBBBBB') for l in labels]
wedges, texts, autotexts = ax2.pie(sizes, labels=labels, colors=colors,
    autopct='%1.1f%%', startangle=140, pctdistance=0.75,
    textprops={'fontsize': 8})
for at in autotexts:
    at.set_fontsize(7)
ax2.set_title('Mutation Type\nDistribution (all entries)', fontsize=11,
              fontweight='bold')

# ── 3. Length distribution (histogram, Set1 vs Set2) ────────────────────────
ax3 = fig.add_subplot(gs[1, :2])
lens_s1 = [int(r['Length']) for r in s1l1+s1l2]
lens_s2 = [int(r['Length']) for r in s2l1+s2l2]
bins = np.arange(10, 120, 4)
ax3.hist(lens_s1, bins=bins, color=SET1_COL, alpha=0.7, label='Set 1', edgecolor='white')
ax3.hist(lens_s2, bins=bins, color=SET2_COL, alpha=0.7, label='Set 2', edgecolor='white')
ax3.set_xlabel('Child Sequence Length (nt)', fontsize=10)
ax3.set_ylabel('Number of Entries', fontsize=10)
ax3.set_title('Length Distribution Across Both Library Sets', fontsize=12,
              fontweight='bold')
ax3.legend(fontsize=9)
ax3.set_facecolor('#F7F9FC')
ax3.spines[['top','right']].set_visible(False)

# ── 4. GC content distribution ───────────────────────────────────────────────
ax4 = fig.add_subplot(gs[1, 2])
gc_s1 = [int(r['GC content pct']) for r in s1l1+s1l2]
gc_s2 = [int(r['GC content pct']) for r in s2l1+s2l2]
gc_bins = np.arange(0, 105, 5)
ax4.hist(gc_s1, bins=gc_bins, color=SET1_COL, alpha=0.7, label='Set 1', edgecolor='white')
ax4.hist(gc_s2, bins=gc_bins, color=SET2_COL, alpha=0.7, label='Set 2', edgecolor='white')
ax4.set_xlabel('GC Content (%)', fontsize=10)
ax4.set_ylabel('Number of Entries', fontsize=10)
ax4.set_title('GC Content Distribution', fontsize=12, fontweight='bold')
ax4.legend(fontsize=9)
ax4.set_facecolor('#F7F9FC')
ax4.spines[['top','right']].set_visible(False)

# ── 5. Summary stats box ──────────────────────────────────────────────────────
ax5 = fig.add_subplot(gs[2, :])
ax5.axis('off')

stats = [
    ['', 'Set 1', 'Set 2', 'Combined'],
    ['Parents', '9', '10', '19'],
    ['Library 1 entries', '1,800', '2,000', '3,800'],
    ['Library 2 entries', '1,276', '1,717', '2,993'],
    ['Total entries', '3,076', '3,717', '6,793'],
    ['Length range', '11–75 nt', '15–108 nt', '11–108 nt'],
    ['GC content range', '8–76%', '13–84%', '8–84%'],
    ['Mutation classes', '5', '5', '5'],
    ['Edit sites covered', '21', '14', '35'],
]

col_w = [0.22, 0.19, 0.19, 0.22]
col_x = [0.02, 0.26, 0.45, 0.64]
row_h = 0.115
header_col = '#2E75B6'
alt_col     = '#DEEAF1'

for ri, row in enumerate(stats):
    for ci, val in enumerate(row):
        x0 = col_x[ci]
        y0 = 1.0 - ri * row_h - row_h
        bg = header_col if ri == 0 else (alt_col if ri % 2 == 0 else 'white')
        fc = 'white' if ri == 0 else 'black'
        rect = mpatches.FancyBboxPatch((x0, y0), col_w[ci] - 0.005, row_h - 0.01,
            boxstyle='round,pad=0.01', linewidth=0.5,
            edgecolor='#BBBBBB', facecolor=bg,
            transform=ax5.transAxes, clip_on=False)
        ax5.add_patch(rect)
        bold = (ri == 0 or ci == 0)
        ax5.text(x0 + col_w[ci]/2 - 0.002, y0 + row_h/2,
                 val, ha='center', va='center',
                 fontsize=10, fontweight='bold' if bold else 'normal',
                 color=fc, transform=ax5.transAxes)

ax5.set_title('Combined Library Statistics', fontsize=12, fontweight='bold', pad=12)

fig.suptitle('ADAR Substrate Library Design Summary', fontsize=16,
             fontweight='bold', y=1.01, color='#1F3864')

out = '/home/user/RNA/scripts/library_summary_figure.png'
plt.savefig(out, dpi=180, bbox_inches='tight', facecolor=fig.get_facecolor())
print('saved', out)
