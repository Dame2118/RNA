const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  PageBreak, LevelFormat, ImageRun,
} = require('docx');

const PAGE = { size: { width: 12240, height: 15840 }, margin: { top: 1296, right: 1296, bottom: 1296, left: 1296 } };
const CONTENT_W = 12240 - 2592; // 9648 dxa
const IMG_W = 648;              // px at 96dpi ~= 6.75"
const BODY = 'Calibri';
const ACCENT = '1F4E79';
const GREY = '595959';

const t = (text, o = {}) => new TextRun({ text, font: o.font || BODY, size: o.size || 22, bold: o.bold, italics: o.italics, color: o.color });
const body = (text, o = {}) => new Paragraph({
  spacing: { after: o.after === undefined ? 140 : o.after, line: 288 },
  alignment: o.align,
  children: Array.isArray(text) ? text : [t(text, o)],
});
const h1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 280, after: 160 }, children: [t(text, { size: 30, bold: true, color: ACCENT })] });
const h2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 260, after: 120 }, children: [t(text, { size: 24, bold: true, color: ACCENT })] });
const bullet = (text) => new Paragraph({
  numbering: { reference: 'dash', level: 0 },
  spacing: { after: 80, line: 288 },
  children: Array.isArray(text) ? text : [t(text)],
});

function callout(label, text) {
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [CONTENT_W],
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: 'D9D9D9' },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: 'D9D9D9' },
      left: { style: BorderStyle.SINGLE, size: 18, color: ACCENT },
      right: { style: BorderStyle.SINGLE, size: 2, color: 'D9D9D9' },
      insideHorizontal: { style: BorderStyle.NONE },
      insideVertical: { style: BorderStyle.NONE },
    },
    rows: [new TableRow({
      children: [new TableCell({
        width: { size: CONTENT_W, type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, fill: 'F2F6FA' },
        margins: { top: 150, bottom: 150, left: 190, right: 190 },
        children: [
          new Paragraph({ spacing: { after: 60 }, children: [t(label.toUpperCase(), { bold: true, size: 17, color: ACCENT })] }),
          new Paragraph({ spacing: { after: 0 }, children: [t(text, { size: 22 })] }),
        ],
      })],
    })],
  });
}

function table(headers, rows, widths) {
  const hdr = new TableRow({
    tableHeader: true,
    children: headers.map((hTxt, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: ACCENT },
      margins: { top: 90, bottom: 90, left: 110, right: 110 },
      children: [new Paragraph({ spacing: { after: 0 }, children: [t(hTxt, { bold: true, size: 18, color: 'FFFFFF' })] })],
    })),
  });
  const rs = rows.map((r, ri) => new TableRow({
    children: r.map((cell, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: ri % 2 ? 'F7F9FB' : 'FFFFFF' },
      margins: { top: 80, bottom: 80, left: 110, right: 110 },
      children: [new Paragraph({ spacing: { after: 0 }, children: Array.isArray(cell) ? cell : [t(String(cell), { size: 19 })] })],
    })),
  }));
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: widths,
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: 'BFBFBF' },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: 'BFBFBF' },
      left: { style: BorderStyle.SINGLE, size: 2, color: 'BFBFBF' },
      right: { style: BorderStyle.SINGLE, size: 2, color: 'BFBFBF' },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 1, color: 'D9D9D9' },
      insideVertical: { style: BorderStyle.SINGLE, size: 1, color: 'D9D9D9' },
    },
    rows: [hdr, ...rs],
  });
}

function figure(path, caption) {
  const buf = fs.readFileSync(path);
  return [
    new Paragraph({
      spacing: { before: 60, after: 60 },
      alignment: AlignmentType.CENTER,
      children: [new ImageRun({ type: 'png', data: buf, transformation: { width: IMG_W, height: Math.round(IMG_W * 0.896) } })],
    }),
    new Paragraph({
      spacing: { after: 160 },
      alignment: AlignmentType.CENTER,
      children: [t(caption, { size: 17, italics: true, color: GREY })],
    }),
  ];
}

const children = [];

// ---- Title ----
children.push(
  new Paragraph({ spacing: { before: 2800, after: 0 }, alignment: AlignmentType.CENTER, children: [t('ADAR Pilot Library', { size: 46, bold: true, color: ACCENT })] }),
  new Paragraph({ spacing: { before: 140, after: 0 }, alignment: AlignmentType.CENTER, children: [t('Parent Structures and Hypotheses', { size: 26, color: GREY })] }),
  new Paragraph({ spacing: { before: 460, after: 0 }, alignment: AlignmentType.CENTER, children: [t('4 libraries · 19 parent hairpins · 6,793 designs', { size: 21, italics: true, color: GREY })] }),
  new Paragraph({ children: [new PageBreak()] }),
);

// ---- 1. The libraries ----
children.push(h1('1. The libraries'));
children.push(body('Four libraries, pooled and demultiplexed by primer pair. Set 1 and Set 2 are different parent panels. Library 1 takes the longest designs per parent; Library 2 is its complement, deduplicated against it.'));
children.push(table(
  ['Library', 'Primer', 'Parents', 'Designs'],
  [
    [[t('Library 1, Set 1', { size: 19, bold: true })], 'ART5', '9', '1,800'],
    [[t('Library 1, Set 2', { size: 19, bold: true })], 'ART7', '10', '2,000'],
    [[t('Library 2, Set 1', { size: 19, bold: true })], 'ART10', '9', '1,276'],
    [[t('Library 2, Set 2', { size: 19, bold: true })], 'ART11', '10', '1,717'],
  ],
  [3400, 1900, 1900, 2448],
));
children.push(body('Each design is a parent hairpin with one perturbation applied, trimmed to a given length. The perturbation axes are: base pairs above or below the edit site converted to GC or AU (k = 1–5), the base opposite the edited adenosine swapped (across), and in Library 2, above and below changed together.', { after: 0 }));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ---- 2. Parent structures ----
children.push(h1('2. Parent structures'));
children.push(body('Edit-site adenosines in red. Only parents that contribute designs are shown.'));
children.push(h2('Set 1 — ART5 and ART10'));
figure('/home/user/RNA/scripts/parents_hairpin_set1.png',
  'Set 1: nine parent hairpins. Natural mammalian substrates plus truncated GluR-B constructs.')
  .forEach(x => children.push(x));
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h2('Set 2 — ART7 and ART11'));
figure('/home/user/RNA/scripts/parents_hairpin_set2.png',
  'Set 2: ten parent hairpins. Natural substrates (GRIA2, GRIK2, FLNA) plus engineered designs (MIRROR, LEAPER3).')
  .forEach(x => children.push(x));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ---- 3. Hypotheses ----
children.push(h1('3. Hypothesis per library'));

children.push(h2('Library 1, Set 1 — ART5'));
children.push(callout('Hypothesis',
  'Editing efficiency at a given adenosine is set by local duplex features within about five base pairs of the target, and those features act independently.'));
children.push(body('Predictions:', { after: 60 }));
children.push(bullet('The base opposite the target matters most: across_C (A:C mismatch) beats wild-type, which beats across_G and across_A.'));
children.push(bullet('Local stability is non-monotonic — the duplex must be stable enough to form but loose enough to let the base flip out. All-GC clamps should suppress editing at high k.'));
children.push(bullet('5′-side changes outweigh 3′-side changes at matched k, reflecting an asymmetric ADAR footprint.'));

children.push(h2('Library 1, Set 2 — ART7'));
children.push(callout('Hypothesis',
  'The rules found in Set 1 are portable: the same perturbation applied to the same edit site in a different structural context produces the same rank order of effects.'));
children.push(body('Predictions:', { after: 60 }));
children.push(bullet('GRIA2_R/G_1 and GRIA2_R/G_2 carry the same biological site in different folds — the response should track the fold, not the site.'));
children.push(bullet('The engineered parents (MIRROR, LEAPER3) should follow the same rules as the natural ones if those rules are physical rather than evolutionary.'));

children.push(new Paragraph({ children: [new PageBreak()] }));

children.push(h2('Library 2, Set 1 — ART10'));
children.push(callout('Hypothesis',
  'Local determinants are NOT additive. Changing the duplex above and below the edit site at the same time interacts, because the two sides jointly decide whether the target base can flip out of the helix. This is the one thing Library 1 cannot test.'));
children.push(body('Predictions:', { after: 60 }));
children.push(bullet('Combined variants deviate from the additive prediction built from Library 1’s single mutants — specifically a negative interaction when the site is clamped from both sides.'));
children.push(bullet('Duplex length has a threshold rather than a gradient: editing collapses below a minimum length instead of declining smoothly.'));

children.push(h2('Library 2, Set 2 — ART11'));
children.push(callout('Hypothesis',
  'The interaction seen in Library 2 Set 1 is general, not a quirk of one parent panel: the same effect recurs, with the same sign, on the Set 2 parents.'));
children.push(body('This is the replication arm. It is what lets the conclusion read “local determinants are non-additive” rather than “non-additive in these nine hairpins.”'));

children.push(new Paragraph({ children: [new PageBreak()] }));

// ---- 4. What the pilot answers ----
children.push(h1('4. What this pilot settles'));
children.push(body('The point of the pilot is to find out which axes produce usable signal before committing to a full library. Four things it should resolve:'));
children.push(bullet([t('Which axes move editing at all. ', { bold: true }), t('above, below, across and length each get hundreds of designs across many parents.')]));
children.push(bullet([t('Where the length floor really sits. ', { bold: true }), t('738 designs fall below 20 nt and should read at the assay floor, which fixes the usable minimum empirically.')]));
children.push(bullet([t('How noisy the assay is. ', { bold: true }), t('588 designed sequences appear under more than one barcode, giving a direct technical-variance estimate from 1,773 oligos.')]));
children.push(bullet([t('Which parents are worth scaling. ', { bold: true }), t('Twelve of nineteen carry combined variants; those are where the interaction test has power.')]));

children.push(h2('Two notes for the analysis'));
children.push(bullet([t('Demultiplex on (primer, barcode), never barcode alone. ', { bold: true }), t('154 barcodes recur across libraries; the composite key is unique for all 6,793 oligos.')]));
children.push(bullet([t('Group on sequence, not on mutation label. ', { bold: true }), t('518 designs labelled as mutations are identical to their unmutated parent, because the substitution set a base pair that was already there. Grouping by label would score them as real effects of zero.')]));

// ---- Build ----
const doc = new Document({
  creator: 'ADAR pilot library',
  title: 'ADAR Pilot Library — Parent Structures and Hypotheses',
  description: 'Simplified design summary: parent hairpin structures and one hypothesis per library',
  numbering: {
    config: [{
      reference: 'dash',
      levels: [
        { level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360, hanging: 220 } } } },
      ],
    }],
  },
  styles: { default: { document: { run: { font: BODY, size: 22 } } } },
  sections: [{ properties: { page: PAGE }, children }],
});

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync('/home/user/RNA/ADAR_Pilot_Library_Simple.docx', b);
  console.log('wrote ADAR_Pilot_Library_Simple.docx', b.length, 'bytes');
});
