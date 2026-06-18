#!/usr/bin/env python3
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()

style = doc.styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(11)

def heading(text, level=1):
    p = doc.add_heading(text, level=level)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return p

def shade_row(row, hex_color="D9E1F2"):
    for cell in row.cells:
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), hex_color)
        tcPr.append(shd)

doc.add_heading('ADAR Library Design Summary — Set 2', 0)
doc.add_paragraph(
    'This document summarises the second two-part sequence variant library '
    'generated from 10 ADAR parent hairpin substrates (Set 2), together with '
    'the experimental hypotheses underlying each mutation class.'
)

# ── TABLE 1 ──────────────────────────────────────────────────────────────────
heading('Table 1: Library Summary by Parent Substrate', level=1)
doc.add_paragraph(
    'Combined Set 2 library: 3,717 entries (Library 1: 2,000; Library 2: 1,717). '
    'GRIA2_R/G_1 and GRIA2_R/G_2 did not reach 200 entries in Library 2 due to '
    'exhaustion of unique variant space in their short sequences.'
)

cols = ['Parent', 'Endogenous Substrate', 'Edit Site(s)',
        'Lib 1', 'Lib 2', 'Total', 'Length Range', 'GC Range']

data = [
    ('GRIA2_Q/R_1',                      'GRIA2 — glutamate receptor B, Q/R site',      'A6',          '200', '200', '400',  '46–60 nt', '40–63%'),
    ('GRIA2_R/G_1',                      'GRIA2 — glutamate receptor B, R/G site',      'A6',          '200', '102', '302',  '16–30 nt', '17–80%'),
    ('GRIA2_R/G_2',                      'GRIA2 — R/G site variant 2',                  'A6, A17–19',  '200',  '15', '215',  '15–23 nt', '13–84%'),
    ('GRIK2_Q_R',                        'GRIK2 — glutamate receptor kainate 2, Q/R',   'A8',          '200', '200', '400',  '24–40 nt', '27–70%'),
    ('FLNA',                             'FLNA — filamin A pre-mRNA',                   'A17',         '200', '200', '400',  '28–46 nt', '29–66%'),
    ('MIRROR_1',                         'Synthetic mirror substrate 1',                'A11',         '200', '200', '400',  '26–44 nt', '27–67%'),
    ('MIRROR_2',                         'Synthetic mirror substrate 2',                'A23, A52',    '200', '200', '400',  '74–84 nt', '40–61%'),
    ('MIRROR_3',                         'Synthetic mirror substrate 3',                'A19',         '200', '200', '400',  '39–55 nt', '28–59%'),
    ('LEAPER3_FLNA_30bp_AC',             'LEAPER3 FLNA 30bp AC substrate',              'A19',         '200', '200', '400',  '48–64 nt', '35–58%'),
    ('LEAPER3_FLNA_50bp_AC_ext_bulge',   'LEAPER3 FLNA 50bp AC external bulge',         'A15',         '200', '200', '400',  '92–108 nt','44–57%'),
    ('Total',                            '',                                             '',          '2,000','1,717','3,717', '',         ''),
]

t1 = doc.add_table(rows=1, cols=len(cols))
t1.style = 'Table Grid'
t1.alignment = WD_TABLE_ALIGNMENT.CENTER

hdr = t1.rows[0]
shade_row(hdr, "2E75B6")
for i, col in enumerate(cols):
    cell = hdr.cells[i]
    cell.text = col
    run = cell.paragraphs[0].runs[0]
    run.bold = True
    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    run.font.size = Pt(9)

for idx, row_data in enumerate(data):
    row = t1.add_row()
    if idx == len(data) - 1:
        shade_row(row, "BDD7EE")
    elif idx % 2 == 0:
        shade_row(row, "DEEAF1")
    for i, val in enumerate(row_data):
        cell = row.cells[i]
        cell.text = val
        run = cell.paragraphs[0].runs[0]
        run.font.size = Pt(9)
        if idx == len(data) - 1:
            run.bold = True

doc.add_paragraph()

# ── Overall Hypothesis ────────────────────────────────────────────────────────
heading('Overall Hypothesis', level=1)
doc.add_paragraph(
    'ADAR editing efficiency is jointly determined by three kinetic parameters: '
    '(1) kfold — the thermodynamic stability of the dsRNA hairpin conformation; '
    '(2) kbind — the efficiency with which ADAR engages the duplex; and '
    '(3) kflip — the energetic cost of extruding the target adenosine from the '
    'helix for deamination. By systematically varying base-pair identity, stem '
    'length, and the identity of the base opposing the edit site, combined with '
    'DMS-MaPseq structural probing to validate solution conformation, we can '
    'deconvolve the contribution of each parameter to overall editing efficiency '
    'across a diverse set of endogenous and synthetic ADAR substrates.'
)

# ── TABLE 2 ──────────────────────────────────────────────────────────────────
heading('Table 2: Mutation Classes and Experimental Hypotheses', level=1)

mut_cols = ['Variant Class', 'What Changes', 'Primary Parameter', 'Hypothesis']

mut_data = [
    (
        'Length trimming',
        'Stem shortened inward from both ends',
        'kfold, kbind',
        'A minimum duplex length is required for stable folding and productive '
        'ADAR engagement. Shorter stems reduce kbind by limiting the dsRNA '
        'footprint (~15 bp optimal). DMS-MaPseq confirms which truncations '
        'maintain the native fold.'
    ),
    (
        'Above mutations\n(1–5 bp, cumulative)',
        'bp identity 5′ of edit site changed\nto all-GC or all-AU',
        'kbind, kfold',
        'GC-rich regions above the edit site stabilise the duplex (↑kfold) and '
        'enhance ADAR binding affinity (↑kbind). AU-rich regions destabilise the '
        'duplex, reduce local melting temperature, and lower editing efficiency.'
    ),
    (
        'Below mutations\n(1–5 bp, cumulative)',
        'bp identity 3′ of edit site\n(toward loop) changed\nto all-GC or all-AU',
        'kflip',
        'The bp immediately closing the edit site on the loop side resists base '
        'flipping. GC pairs below the edit site raise the energetic barrier to '
        'kflip and suppress editing; AU pairs facilitate flipping and increase '
        'editing efficiency.'
    ),
    (
        'Across mutations\n(C, G, A)',
        'Base paired with the A edit site\nchanged from U to C, G, or A',
        'kflip, editing rate',
        'The opposing base directly sets the mismatch energy at the edit site. '
        'A·C mismatches are preferred by ADAR over A·U Watson-Crick pairs '
        '(lower kflip barrier). A·G and A·A mismatches test how local '
        'instability drives or inhibits deamination independently of global '
        'duplex stability.'
    ),
    (
        'Combined above+below\n(all 5×5 combinations)',
        'Both flanking regions mutated\nsimultaneously, GC or AU',
        'kfold + kflip\n(interaction)',
        'Tests whether the effects of above and below mutations are independent '
        'or cooperative. A stable duplex above with a weak bp below may optimally '
        'balance kbind and kflip; fully GC or fully AU surroundings reveal the '
        'upper and lower bounds of editing efficiency.'
    ),
    (
        'DMS-MaPseq\nstructural validation',
        'No sequence change — chemical\nprobing of all variants',
        'kfold (structural)',
        'Confirms that designed mutations produce the intended structural changes '
        'in solution. Unpaired A/C reactivity maps validate the assumed dot-bracket '
        'topology and reveal unexpected misfolding or alternative structures that '
        'could confound kinetic interpretation.'
    ),
]

t2 = doc.add_table(rows=1, cols=len(mut_cols))
t2.style = 'Table Grid'
t2.alignment = WD_TABLE_ALIGNMENT.CENTER

hdr2 = t2.rows[0]
shade_row(hdr2, "2E75B6")
for i, col in enumerate(mut_cols):
    cell = hdr2.cells[i]
    cell.text = col
    run = cell.paragraphs[0].runs[0]
    run.bold = True
    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    run.font.size = Pt(10)

for idx, row_data in enumerate(mut_data):
    row = t2.add_row()
    if idx % 2 == 0:
        shade_row(row, "DEEAF1")
    for i, val in enumerate(row_data):
        cell = row.cells[i]
        cell.text = val
        run = cell.paragraphs[0].runs[0]
        run.font.size = Pt(9)
        if i == 0:
            run.bold = True

out = '/home/user/RNA/ADAR_Library_Set2_Summary.docx'
doc.save(out)
print('saved', out)
