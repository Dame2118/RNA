const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  PageBreak, LevelFormat, ImageRun, PageOrientation,
} = require('docx');

const PAGE = { size: { width: 12240, height: 15840 }, margin: { top: 1152, right: 1152, bottom: 1152, left: 1152 } };
const CW = 12240 - 2304; // 9936
const BODY = 'Calibri', MONO = 'Consolas';
const ACCENT = '1F4E79', GREY = '595959';

const t = (x, o = {}) => new TextRun({ text: x, font: o.font || BODY, size: o.size || 21, bold: o.bold, italics: o.italics, color: o.color });
const p = (x, o = {}) => new Paragraph({ spacing: { after: o.after === undefined ? 140 : o.after, line: 288 }, alignment: o.align, children: Array.isArray(x) ? x : [t(x, o)] });
const h1 = (x) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 300, after: 160 }, children: [t(x, { size: 30, bold: true, color: ACCENT })] });
const h2 = (x) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 260, after: 110 }, children: [t(x, { size: 24, bold: true, color: ACCENT })] });
const bul = (x) => new Paragraph({ numbering: { reference: 'dash', level: 0 }, spacing: { after: 80, line: 288 }, children: Array.isArray(x) ? x : [t(x)] });

function callout(label, text, fill = 'F2F6FA', bar = ACCENT) {
  return new Table({
    width: { size: CW, type: WidthType.DXA }, columnWidths: [CW],
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: 'D9D9D9' }, bottom: { style: BorderStyle.SINGLE, size: 2, color: 'D9D9D9' },
      left: { style: BorderStyle.SINGLE, size: 18, color: bar }, right: { style: BorderStyle.SINGLE, size: 2, color: 'D9D9D9' },
      insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE },
    },
    rows: [new TableRow({ children: [new TableCell({
      width: { size: CW, type: WidthType.DXA }, shading: { type: ShadingType.CLEAR, fill },
      margins: { top: 150, bottom: 150, left: 190, right: 190 },
      children: [
        new Paragraph({ spacing: { after: 60 }, children: [t(label.toUpperCase(), { bold: true, size: 17, color: bar })] }),
        new Paragraph({ spacing: { after: 0 }, children: Array.isArray(text) ? text : [t(text, { size: 21 })] }),
      ],
    })] })],
  });
}

function table(headers, rows, widths, hdrSize = 17, cellSize = 17) {
  const hdr = new TableRow({ tableHeader: true, children: headers.map((h, i) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA }, shading: { type: ShadingType.CLEAR, fill: ACCENT },
    margins: { top: 80, bottom: 80, left: 90, right: 90 },
    children: [new Paragraph({ spacing: { after: 0 }, children: [t(h, { bold: true, size: hdrSize, color: 'FFFFFF' })] })],
  })) });
  const rs = rows.map((r, ri) => new TableRow({ children: r.map((c, i) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: ri % 2 ? 'F7F9FB' : 'FFFFFF' },
    margins: { top: 70, bottom: 70, left: 90, right: 90 },
    children: (Array.isArray(c) && c[0] instanceof Paragraph) ? c
      : [new Paragraph({ spacing: { after: 0 }, children: Array.isArray(c) ? c : [t(String(c), { size: cellSize })] })],
  })) }));
  return new Table({
    width: { size: CW, type: WidthType.DXA }, columnWidths: widths,
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: 'BFBFBF' }, bottom: { style: BorderStyle.SINGLE, size: 2, color: 'BFBFBF' },
      left: { style: BorderStyle.SINGLE, size: 2, color: 'BFBFBF' }, right: { style: BorderStyle.SINGLE, size: 2, color: 'BFBFBF' },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 1, color: 'D9D9D9' }, insideVertical: { style: BorderStyle.SINGLE, size: 1, color: 'D9D9D9' },
    },
    rows: [hdr, ...rs],
  });
}

const sub = (x) => [t(x, { size: 15, color: GREY })];

const children = [];

// ── Title ──
children.push(
  new Paragraph({ spacing: { before: 2700, after: 0 }, alignment: AlignmentType.CENTER, children: [t('ADAR Pilot Library — Set 1', { size: 44, bold: true, color: ACCENT })] }),
  new Paragraph({ spacing: { before: 140, after: 0 }, alignment: AlignmentType.CENTER, children: [t('What the Ordered Set Contains, and the Hypothesis Behind It', { size: 24, color: GREY })] }),
  new Paragraph({ spacing: { before: 460, after: 0 }, alignment: AlignmentType.CENTER, children: [t('3,076 oligos · 9 parent hairpins · 2 sub-libraries · ordered and in experiment', { size: 20, italics: true, color: GREY })] }),
  new Paragraph({ children: [new PageBreak()] }),
);

// ── 1. What this set is ──
children.push(h1('1. What this set is'));
children.push(p('Set 1 is a sequence-variant library built from nine validated ADAR parent hairpin substrates. Each member is one parent, carrying one defined perturbation, trimmed to a defined length. It was ordered as two sub-libraries sharing a single primer pair format, and submitted as 3,076 oligos of 170 nt each.'));
children.push(table(
  ['Sub-library', 'Primer', 'Designs', 'Selection rule'],
  [
    [[t('Library 1', { size: 17, bold: true })], 'ART5', '1,800', 'The 200 longest designs per parent.'],
    [[t('Library 2', { size: 17, bold: true })], 'ART10', '1,276', 'Complement of Library 1: deeper trims, then combined above+below variants, deduplicated by exact sequence.'],
    [[t('Total', { size: 17, bold: true, color: ACCENT })], '', [t('3,076', { size: 17, bold: true, color: ACCENT })], ''],
  ],
  [1700, 1100, 1200, 5936],
));
children.push(h2('Oligo format'));
children.push(p([t('Each 170 nt oligo is assembled as:', { size: 21 })], { after: 80 }));
children.push(new Paragraph({
  spacing: { after: 100 }, alignment: AlignmentType.CENTER,
  shading: { type: ShadingType.CLEAR, fill: 'F7F7F7' },
  children: [t('FWD primer (19) + left flank + designed sequence + right flank + barcode (12) + REV primer (19)', { font: MONO, size: 17 })],
}));
children.push(p('Flanks are C/T only with no run longer than 3, so they stay unstructured. Barcodes are 12 nt, GC-balanced, with a minimum Hamming distance of 4 within the library.'));
children.push(callout('Identifier note',
  'The submitted FASTA names oligos oligo_set1_1_seq_N, in an order that does not match the design files, so the names carry no design information. All 3,076 full-length sequences are unique, so every name maps back by exact sequence match — see submitted_set1_crosswalk.csv. That crosswalk is required to tie reads to parents and mutation classes.',
  'FFF8E8', 'B07A00'));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ── 2. Parent structures ──
children.push(h1('2. Parent structures'));
children.push(p('The nine parents below are the structural basis of every member. Each is a single hairpin; edit-site adenosines are red. Three further records in the source file were excluded: 5-HT2C_1 and AZIN1_2 fold into two stem domains rather than one hairpin, and GluR_BRG_15mer has its edit site in the unpaired 5′ overhang, outside the stem.'));
children.push(new Paragraph({
  spacing: { before: 60, after: 60 }, alignment: AlignmentType.CENTER,
  children: [new ImageRun({ type: 'png', data: fs.readFileSync('/home/user/RNA/scripts/parents_hairpin_set1.png'), transformation: { width: 660, height: Math.round(660 * 0.896) } })],
}));
children.push(new Paragraph({ spacing: { after: 140 }, alignment: AlignmentType.CENTER, children: [t('The nine Set 1 parent hairpins. Red = annotated edit site.', { size: 16, italics: true, color: GREY })] }));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ── 3. Composition table ──
children.push(h1('3. What each parent contributes'));
children.push(p('Length and GC ranges below span both sub-libraries. The combined column counts designs carrying simultaneous above+below mutations — the interaction arm.'));
const parents = [
  ['5-HT2C_2', 'HTR2C — serotonin receptor 2C', 'A4, A6, A16, A25, A47', 200, 200, 400, '20–75', '12–71', 0, 0],
  ['NEIL1', 'NEIL1 — DNA glycosylase', 'A45', 200, 114, 314, '8–74', '15–72', 0, 56],
  ['AZIN1', 'AZIN1 — antizyme inhibitor 1', 'A31', 200, 29, 229, '6–41', '8–76', 0, 103],
  ['BDF2', '—', 'A17', 200, 170, 370, '19–53', '26–73', 157, 3],
  ['hGLI1', 'GLI1 — oncogene', 'A55', 200, 28, 228, '18–77', '41–75', 0, 1],
  ['PRE_MIRNA142', 'pre-miR-142', 'A3, A18–20, A23, A37, A47, A52, A59', 200, 200, 400, '22–68', '18–68', 0, 0],
  ['GluR-B_QR', 'GRIA2 — Q/R site', 'A6', 200, 200, 400, '10–56', '25–75', 54, 28],
  ['GluR-B_RG', 'GRIA2 — R/G site', 'A6', 200, 200, 400, '8–56', '6–75', 67, 39],
  ['GluR_BRG_15mer_2', 'GRIA2 — R/G 15mer variant', 'A6', 200, 135, 335, '8–34', '17–85', 86, 44],
];
children.push(table(
  ['Parent', 'Endogenous substrate', 'Edit site(s)', 'L1', 'L2', 'Total', 'Length', 'GC %', 'Comb.', '<20 nt'],
  parents.map(r => [
    [t(r[0], { size: 15, bold: true })], sub(r[1]), sub(r[2]),
    [t(String(r[3]), { size: 16 })], [t(String(r[4]), { size: 16 })], [t(String(r[5]), { size: 16, bold: true })],
    [t(r[6], { size: 16 })], [t(r[7], { size: 16 })],
    [t(String(r[8]), { size: 16, bold: r[8] > 0, color: r[8] > 0 ? '1F4E79' : 'A0A0A0' })],
    [t(String(r[9]), { size: 16, color: r[9] > 50 ? 'B04A00' : '222222' })],
  ]).concat([[
    [t('Total', { size: 15, bold: true, color: ACCENT })], sub(''), sub(''),
    [t('1,800', { size: 16, bold: true, color: ACCENT })], [t('1,276', { size: 16, bold: true, color: ACCENT })],
    [t('3,076', { size: 16, bold: true, color: ACCENT })], sub(''), sub(''),
    [t('364', { size: 16, bold: true, color: ACCENT })], [t('274', { size: 16, bold: true, color: ACCENT })],
  ]]),
  [1500, 1850, 1700, 620, 620, 720, 820, 820, 650, 636], 16, 16,
));
children.push(h2('Composition by perturbation class'));
children.push(table(
  ['Class', 'n', 'Share'],
  [['Above (5′ of edit site)', '1,448', '47.1%'], ['Below (3′, toward loop)', '839', '27.3%'],
   ['Combined above+below', '364', '11.8%'], ['Across (opposing base)', '239', '7.8%'],
   ['Unmutated parent', '186', '6.0%']],
  [5000, 2468, 2468], 17, 18,
));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ── 4. Hypothesis ──
children.push(h1('4. The hypothesis behind the structure'));
children.push(callout('Overall hypothesis',
  'ADAR editing efficiency is jointly determined by three kinetic parameters: k_fold, the thermodynamic stability of the dsRNA hairpin conformation; k_bind, the efficiency with which ADAR engages the duplex; and k_flip, the energetic cost of extruding the target adenosine from the helix for deamination. By systematically varying base-pair identity, stem length, and the identity of the base opposing the edit site — combined with DMS-MaPseq structural probing to validate solution conformation — the contribution of each parameter can be deconvolved across a diverse set of endogenous ADAR substrates.'));
children.push(p('Each perturbation class in the library is designed to load onto one of those three parameters, so that the measured editing response separates them.', { after: 160 }));

const cls = [
  ['Length trimming', 'Stem shortened inward from both ends, anchored on the edit site.', 'k_fold, k_bind',
   'A minimum duplex length is required for stable folding and productive ADAR engagement. Shorter stems reduce k_bind by limiting the dsRNA footprint. DMS-MaPseq confirms which truncations retain the native fold.'],
  ['Above mutations (1–5 bp, cumulative)', 'Base pairs 5′ of the edit site set to all-GC or all-AU.', 'k_bind, k_fold',
   'GC-rich regions above the edit site stabilise the duplex and enhance ADAR binding affinity. AU-rich regions destabilise it, lower the local melting temperature, and reduce editing.'],
  ['Below mutations (1–5 bp, cumulative)', 'Base pairs 3′ of the edit site, toward the loop, set to all-GC or all-AU.', 'k_flip',
   'The base pair closing the edit site on the loop side resists base flipping. GC pairs below raise the barrier to k_flip and suppress editing; AU pairs facilitate flipping and increase it.'],
  ['Across mutations (C, G, A)', 'Base paired with the target adenosine changed from U to C, G or A.', 'k_flip, deamination rate',
   'The opposing base sets the mismatch energy at the edit site directly. A·C mismatches are preferred by ADAR over A·U Watson–Crick pairs (lower k_flip barrier). A·G and A·A test how local instability drives or inhibits deamination independently of global duplex stability.'],
  ['Combined above+below (5 × 5)', 'Both flanking regions mutated simultaneously, GC or AU.', 'k_fold × k_flip interaction',
   'Tests whether above and below effects are independent or cooperative. A stable duplex above with a weak pair below may optimally balance k_bind and k_flip; fully GC or fully AU surroundings reveal the upper and lower bounds of editing efficiency.'],
  ['DMS-MaPseq validation', 'No sequence change — chemical probing of all variants.', 'k_fold (structural)',
   'Confirms the designed mutations produce the intended structural change in solution. Unpaired A/C reactivity validates the assumed dot-bracket topology and reveals misfolding or alternative structures that would confound kinetic interpretation.'],
];
children.push(table(
  ['Variant class', 'What changes', 'Parameter', 'Hypothesis'],
  cls.map(r => [[t(r[0], { size: 16, bold: true })], [t(r[1], { size: 16 })],
                [t(r[2], { size: 16, font: MONO, color: ACCENT })], [t(r[3], { size: 16 })]]),
  [1900, 2200, 1500, 4336], 17, 16,
));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ── 5. Coverage ──
children.push(h1('5. Coverage of this set'));
children.push(p('Three properties of the ordered set bear on how far each hypothesis can be tested. None reflects a synthesis error — all 3,076 designs were built and submitted as intended — but each constrains interpretation.'));

children.push(h2('The interaction arm covers four parents, not nine'));
children.push(p('Library 1 fills its 200-per-parent quota with the longest designs, and Library 2 draws deeper trims before combined variants. Parents with rich length ladders therefore exhaust their quota before reaching the combination grid.'));
children.push(table(
  ['Combined variants present', 'Combined variants absent'],
  [[[t('BDF2 (157), GluR_BRG_15mer_2 (86), GluR-B_RG (67), GluR-B_QR (54)', { size: 17 })],
    [t('5-HT2C_2, NEIL1, AZIN1, hGLI1, PRE_MIRNA142', { size: 17 })]]],
  [4968, 4968], 17, 17,
));
children.push(p('The k_fold × k_flip interaction hypothesis is therefore testable on four parents. The other five contribute to the single-axis hypotheses only.', { after: 160 }));

children.push(h2('274 designs fall below the ADAR substrate threshold'));
children.push(p('The trim ladder has no minimum length, so it peels to 6 nt. 274 designs are under 20 nt, concentrated in AZIN1 (103 of its 229). These should read at the assay floor regardless of mutation class — which makes them a usable empirical floor estimate, but they should be excluded before fitting any length–response curve.'));

children.push(h2('3,076 oligos carry 2,539 distinct sequences'));
children.push(p('537 oligos duplicate another design’s sequence under a different barcode and a different mutation label. The cause is that a substitution setting a base pair that was already present leaves the sequence unchanged, and a mutation outside the retained trim window is not represented in the child. These duplicates are genuine technical replicates — the same molecule under independent barcodes — and give a direct estimate of assay noise.'));
children.push(callout('Analysis consequence',
  'Group reads on the designed sequence, not on the mutation label. Grouping by label would score a sequence identical to its unmutated parent as a real mutation effect of zero, biasing the additivity test toward the additive conclusion it is meant to test.',
  'FFF8E8', 'B07A00'));

const doc = new Document({
  creator: 'ADAR pilot library',
  title: 'ADAR Pilot Library — Set 1',
  description: 'What the ordered Set 1 library contains, its parent structures, and the kinetic hypothesis behind it',
  numbering: { config: [{ reference: 'dash', levels: [
    { level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360, hanging: 220 } } } }] }] },
  styles: { default: { document: { run: { font: BODY, size: 21 } } } },
  sections: [{ properties: { page: PAGE }, children }],
});

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync('/home/user/RNA/ADAR_Set1_Ordered_Library.docx', b);
  console.log('wrote ADAR_Set1_Ordered_Library.docx', b.length, 'bytes');
});
