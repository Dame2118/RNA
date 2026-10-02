const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  PageBreak, LevelFormat, TableOfContents,
} = require('docx');

const P = '/tmp/claude-0/-home-user-RNA/ad9eca3c-e569-5f9d-8e20-38cd938e0242/scratchpad/parents.json';
const data = JSON.parse(fs.readFileSync(P, 'utf8'));

// US Letter, 1" margins
const PAGE = { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } };
const CONTENT_W = 12240 - 2880; // 9360 dxa

const MONO = 'Consolas';
const BODY = 'Calibri';
const ACCENT = '1F4E79';
const GREY = '595959';

// counts of entries per library, from the CSVs
const COUNTS = {
  'gc_library.csv': 1800,
  'gc_library_set2.csv': 2000,
  'gc_library2.csv': 1276,
  'gc_library_set2b.csv': 1717,
};

const PER_PARENT = {
  'gc_library.csv': {
    '5-HT2C_2': 200, 'NEIL1': 200, 'AZIN1': 200, 'BDF2': 200, 'hGLI1': 200,
    'PRE_MIRNA142': 200, 'GluR-B_QR': 200, 'GluR-B_RG': 200, 'GluR_BRG_15mer_2': 200,
  },
  'gc_library2.csv': {
    '5-HT2C_2': 200, 'PRE_MIRNA142': 200, 'GluR-B_QR': 200, 'GluR-B_RG': 200,
    'BDF2': 170, 'GluR_BRG_15mer_2': 135, 'NEIL1': 114, 'AZIN1': 29, 'hGLI1': 28,
  },
  'gc_library_set2.csv': {
    'GRIA2_Q/R_1': 200, 'GRIA2_R/G_1': 200, 'GRIA2_R/G_2': 200, 'GRIK2_Q_R': 200,
    'FLNA': 200, 'MIRROR_1': 200, 'MIRROR_2': 200, 'MIRROR_3': 200,
    'LEAPER3_FLNA_30bp_AC': 200, 'LEAPER3_FLNA_50bp_AC_external_bulge': 200,
  },
  'gc_library_set2b.csv': {
    'GRIA2_Q/R_1': 200, 'GRIK2_Q_R': 200, 'FLNA': 200, 'MIRROR_1': 200,
    'MIRROR_2': 200, 'MIRROR_3': 200, 'LEAPER3_FLNA_30bp_AC': 200,
    'LEAPER3_FLNA_50bp_AC_external_bulge': 200, 'GRIA2_R/G_1': 102, 'GRIA2_R/G_2': 15,
  },
};

// ---------- small helpers ----------
const t = (text, o = {}) => new TextRun({ text, font: o.font || BODY, size: o.size || 21, bold: o.bold, italics: o.italics, color: o.color });
const body = (text, o = {}) => new Paragraph({
  spacing: { after: o.after === undefined ? 120 : o.after, line: 276 },
  alignment: o.align,
  indent: o.indent,
  children: Array.isArray(text) ? text : [t(text, o)],
});
const h1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 320, after: 160 }, children: [t(text, { size: 30, bold: true, color: ACCENT })] });
const h2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 260, after: 120 }, children: [t(text, { size: 25, bold: true, color: ACCENT })] });
const h3 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200, after: 100 }, children: [t(text, { size: 22, bold: true, color: GREY })] });
const bullet = (text, lvl = 0) => new Paragraph({
  numbering: { reference: 'dash', level: lvl },
  spacing: { after: 80, line: 276 },
  children: Array.isArray(text) ? text : [t(text)],
});
const rule = () => new Paragraph({
  spacing: { before: 120, after: 120 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: 'BFBFBF', space: 1 } },
  children: [t('')],
});

// hypothesis callout: shaded single-cell table
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
        margins: { top: 140, bottom: 140, left: 180, right: 180 },
        children: [
          new Paragraph({ spacing: { after: 60 }, children: [t(label.toUpperCase(), { bold: true, size: 17, color: ACCENT })] }),
          new Paragraph({ spacing: { after: 0 }, children: [t(text, { size: 21 })] }),
        ],
      })],
    })],
  });
}

// generic data table
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
  const bodyRows = rows.map((r, ri) => new TableRow({
    children: r.map((cell, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: ri % 2 ? 'F7F9FB' : 'FFFFFF' },
      margins: { top: 80, bottom: 80, left: 110, right: 110 },
      children: [new Paragraph({
        spacing: { after: 0 },
        children: Array.isArray(cell) ? cell : [t(String(cell), { size: 18 })],
      })],
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
    rows: [hdr, ...bodyRows],
  });
}

// A parent's sequence + dot-bracket, wrapped in 60-char blocks, monospaced.
function structureBlock(p) {
  const out = [];
  out.push(new Paragraph({
    spacing: { before: 160, after: 40 },
    children: [
      t(p.name, { bold: true, size: 20 }),
      t(`   ${p.len} nt   edit site${p.sites.length > 1 ? 's' : ''}: ${p.sites.map(s => 'A' + s).join(', ')}`, { size: 18, color: GREY }),
    ],
  }));
  const W = 60;
  for (let i = 0; i < p.seq.length; i += W) {
    const seg = p.seq.slice(i, i + W);
    const str = p.struct.slice(i, i + W);
    out.push(new Paragraph({
      spacing: { after: 0, line: 240 },
      shading: { type: ShadingType.CLEAR, fill: 'F7F7F7' },
      children: [t(seg, { font: MONO, size: 17 })],
    }));
    out.push(new Paragraph({
      spacing: { after: 60, line: 240 },
      shading: { type: ShadingType.CLEAR, fill: 'F7F7F7' },
      children: [t(str, { font: MONO, size: 17, color: ACCENT })],
    }));
  }
  return out;
}

function parentTable(csvKey, parents) {
  const counts = PER_PARENT[csvKey];
  const rows = parents
    .filter(p => counts[p.name] !== undefined)
    .sort((a, b) => counts[b.name] - counts[a.name])
    .map(p => [
      [t(p.name, { size: 18, bold: true })],
      String(p.len),
      p.sites.map(s => 'A' + s).join(', '),
      String(counts[p.name]),
    ]);
  return table(['Parent', 'Length (nt)', 'Annotated edit sites', 'Entries'], rows, [3400, 1500, 2960, 1500]);
}

// ---------- document ----------
const set1 = data.set1, set2 = data.set2;
const set1used = set1.filter(p => PER_PARENT['gc_library.csv'][p.name] !== undefined);
const set2used = set2.filter(p => PER_PARENT['gc_library_set2.csv'][p.name] !== undefined);

const children = [];

// ===== Title page =====
children.push(
  new Paragraph({ spacing: { before: 2600, after: 0 }, alignment: AlignmentType.CENTER, children: [t('ADAR Substrate-Determinant Libraries', { size: 44, bold: true, color: ACCENT })] }),
  new Paragraph({ spacing: { before: 160, after: 0 }, alignment: AlignmentType.CENTER, children: [t('Parent Structures and Design Hypotheses', { size: 26, color: GREY })] }),
  new Paragraph({ spacing: { before: 520, after: 0 }, alignment: AlignmentType.CENTER, children: [t('Four pooled oligonucleotide libraries · 6,793 designs · 19 parent hairpins', { size: 21, italics: true, color: GREY })] }),
  new Paragraph({ spacing: { before: 1800, after: 0 }, alignment: AlignmentType.CENTER, children: [t('Design document · 2 October 2026', { size: 19, color: GREY })] }),
  new Paragraph({ children: [new PageBreak()] }),
);

// ===== Contents =====
children.push(h1('Contents'));
children.push(new TableOfContents('Contents', { hyperlink: true, headingStyleRange: '1-2' }));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ===== 1. Overview =====
children.push(h1('1. Overview'));
children.push(h2('1.1 Central question'));
children.push(body('Which local structural and sequence features of a hairpin determine ADAR A-to-I editing efficiency, and do those features act independently or interact?'));

children.push(h2('1.2 Design strategy'));
children.push(body('Each library starts from a panel of validated or engineered ADAR substrates (the parents) and perturbs them along four axes that the generation code treats as orthogonal:'));
children.push(bullet([t('Local base-pair identity ', { bold: true }), t('— cumulatively convert the k nearest base pairs on the 5′ side (above) or 3′ side (below) of an edit site to all-GC or all-AU, for k = 1…5.')]));
children.push(bullet([t('Mismatch identity at the target ', { bold: true }), t('— replace the base paired directly opposite the edited adenosine with C, G, or A (the across axis).')]));
children.push(bullet([t('Duplex length ', { bold: true }), t('— peel concentric stem pairs inward from the outside, always retaining the shell that contains the edit site, in three modes: full, edit-adjacent, and loop-adjacent.')]));
children.push(bullet([t('Global GC content ', { bold: true }), t('— used as a selection criterion rather than a perturbation, to balance representation across 10 % GC bands.')]));
children.push(body('Every design carries its full provenance in its reference string, for example 5-HT2C_2 75nt 43% A4_above1_GC full, so any measurement can be traced back to parent, mutation class, and trim mode.', { after: 180 }));

children.push(h2('1.3 The four libraries'));
children.push(table(
  ['Library', 'Source CSV', 'Primer', 'Parents', 'Designs'],
  [
    [[t('Library 1, Set 1', { size: 18, bold: true })], 'gc_library.csv', 'ART5', '9', '1,800'],
    [[t('Library 1, Set 2', { size: 18, bold: true })], 'gc_library_set2.csv', 'ART7', '10', '2,000'],
    [[t('Library 2, Set 1', { size: 18, bold: true })], 'gc_library2.csv', 'ART10', '9', '1,276'],
    [[t('Library 2, Set 2', { size: 18, bold: true })], 'gc_library_set2b.csv', 'ART11', '10', '1,717'],
    [[t('Pooled total', { size: 18, bold: true, color: ACCENT })], [t('oligo_all_combined.fasta', { size: 18, color: ACCENT })], [t('—', { size: 18, color: ACCENT })], [t('19', { size: 18, bold: true, color: ACCENT })], [t('6,793', { size: 18, bold: true, color: ACCENT })]],
  ],
  [2300, 3000, 1100, 1180, 1780],
));
children.push(body('Set 1 and Set 2 are distinct parent panels. Library 1 and Library 2 are complementary selections from the same candidate pool: Library 2 is deduplicated by exact sequence against Library 1, so no design appears in both.', { after: 160 }));

children.push(h2('1.4 Shared readout assumption'));
children.push(body('All 6,793 designs are built as 170 nt oligos carrying a library-specific primer pair and a unique 12 nt barcode with a minimum Hamming distance of 4. The four libraries can therefore be pooled, edited in a single reaction, and demultiplexed computationally. Every hypothesis below assumes editing is quantified per barcode as the A-to-G conversion fraction from amplicon sequencing.'));
children.push(callout('Caveat', 'The repository encodes the design logic only — nothing in it describes the editing assay, the cell or extract system, or the sequencing depth. Confirm the intended readout before relying on the power claims in this document.'));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ===== 2. Parent structures =====
children.push(h1('2. Parent structures'));
children.push(body('Sequences are RNA as designed; the oligo builder converts U to T. Dot-bracket strings are shown directly beneath their sequence. Edit-site numbering is 1-based on the parent.'));

children.push(h2('2.1 Set 1 parents (Libraries 1 and 2, primers ART5 and ART10)'));
children.push(body('Twelve records are defined in adar_library_1_2.txt; nine contribute designs. Set 1 is a heterogeneous panel spanning natural mammalian substrates and truncated GluR-B constructs.'));
children.push(parentTable('gc_library.csv', set1));
children.push(h3('Structures'));
set1used.forEach(p => structureBlock(p).forEach(x => children.push(x)));

children.push(h3('Records defined but not represented'));
children.push(table(
  ['Record', 'Reason excluded'],
  [
    ['5-HT2C_1', 'Not a single hairpin — two separate stem domains; rejected by the ring decomposition.'],
    ['AZIN1_2', 'Not a single hairpin — two adjacent stems; rejected by the ring decomposition.'],
    [[t('GluR_BRG_15mer', { size: 18, bold: true })], [t('Passes the hairpin test, but its only edit site (A6) lies in the unpaired 5′ overhang, outside every ring. No length children are generated and the parent is dropped silently.', { size: 18 })]],
  ],
  [2600, 6760],
));
children.push(callout('Flag', 'The GluR_BRG_15mer exclusion is silent — unlike the two non-hairpin records, it produces no warning. Any parent whose edit site sits outside the paired region will disappear from the libraries without notice. Worth an explicit check before the next build.'));
children.push(new Paragraph({ children: [new PageBreak()] }));

children.push(h2('2.2 Set 2 parents (Libraries 1 and 2, primers ART7 and ART11)'));
children.push(body('All ten records in adar_library_2.txt are clean hairpins and all ten contribute designs. Set 2 mixes natural substrates (GRIA2, GRIK2, FLNA) with engineered designs (MIRROR 1–3, LEAPER3), so it is not simply a second natural panel.'));
children.push(parentTable('gc_library_set2.csv', set2));
children.push(h3('Structures'));
set2used.forEach(p => structureBlock(p).forEach(x => children.push(x)));

children.push(h2('2.3 Overlap between the two sets'));
children.push(body('The two panels are not biologically disjoint. GluR-B is GRIA2, so the GRIA2 Q/R and R/G sites appear in both Set 1 (as GluR-B_QR, GluR-B_RG, GluR_BRG_15mer_2) and Set 2 (as GRIA2_Q/R_1, GRIA2_R/G_1, GRIA2_R/G_2), in different structural contexts and under different primers.'));
children.push(callout('Opportunity', 'This overlap is the natural handle for cross-set normalisation. Because the same edit sites are present under both primer pairs, the shared parents can be used to estimate and correct primer-specific amplification bias — which the design otherwise has no way to control for.'));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ===== 3. Hypotheses =====
children.push(h1('3. Hypotheses by library'));
children.push(body('Each library is stated as a primary hypothesis, the sub-hypotheses the design can resolve, and the confounds that limit interpretation. The primary hypotheses are what the libraries are powered to test; they are proposals for review, not conclusions.'));

// --- Lib 1 Set 1 ---
children.push(h2('3.1 Library 1, Set 1 — gc_library.csv (ART5, 1,800 designs)'));
children.push(body([t('Contents. ', { bold: true }), t('Single-axis perturbations only: original, above_k, below_k (k = 1…5, GC or AU), and across_{C,G,A}, each crossed with the length-trim ladder. The 200 longest children are kept per parent.')]));
children.push(callout('Primary hypothesis', 'Editing efficiency at a given adenosine is set predominantly by local duplex features within roughly five base pairs of the target, and those features contribute independently and additively.'));
children.push(h3('Sub-hypotheses and predictions'));
children.push(table(
  ['Axis', 'Hypothesis', 'Prediction'],
  [
    [[t('across', { size: 18, font: MONO })], 'The base opposite the target A is the single strongest determinant.', 'across_C (A:C mismatch) > wild-type A:U > across_G ≈ across_A'],
    [[t('above_k / below_k, GC vs AU', { size: 18, font: MONO })], 'Local thermodynamic stability is non-monotonic — editing needs a duplex stable enough to form but loose enough to permit base flipping.', 'Intermediate stability optimal; all-GC clamps suppress editing at high k.'],
    ['above vs below', 'ADAR’s footprint is asymmetric about the target.', '5′-side changes exceed 3′-side changes at matched k.'],
    ['Trim mode', 'The edit site’s own shell is necessary; outer stems are dispensable.', 'edit-adjacent ≈ full at matched length; loop-adjacent lower.'],
    ['Parent identity', 'A parent-level baseline exists that perturbations modulate rather than override.', 'Parent explains substantial variance; perturbation effects rank consistently within parent.'],
  ],
  [1900, 3730, 3730],
));
children.push(h3('Confounds'));
children.push(bullet([t('The GC/AU contrast changes meaning with k. ', { bold: true }), t('At k = 1, GC sets the 5′ nearest neighbour to G and AU sets it to A. Because ADAR’s 5′-neighbour preference runs roughly U > A > C > G, the k = 1 comparison is a nearest-neighbour test, while by k = 5 it is mostly a stability test. Do not pool across k — model k as an interaction term.')]));
children.push(bullet([t('Length is near-ceiling by construction. ', { bold: true }), t('Longest-first selection means duplex length varies little within this library. Length effects are structurally weak here; they live in the lower rungs of the trim ladder, which Library 1 discards.')]));
children.push(bullet([t('Hairpins only. ', { bold: true }), t('The ring decomposition rejects branched and multi-domain substrates, so no claim about those structures is supported.')]));

// --- Lib 1 Set 2 ---
children.push(h2('3.2 Library 1, Set 2 — gc_library_set2.csv (ART7, 2,000 designs)'));
children.push(body([t('Contents. ', { bold: true }), t('The same single-axis perturbation scheme applied to the ten Set 2 parents, with the full 200 entries per parent.')]));
children.push(callout('Primary hypothesis', 'The determinant rules inferred from one panel are context-portable: the same perturbation applied to the same edit site in a different structural context produces the same rank order of effects.'));
children.push(h3('Sub-hypotheses'));
children.push(bullet([t('Within-site context. ', { bold: true }), t('GRIA2_R/G_1 and GRIA2_R/G_2 carry the same biological edit site in different folds; the perturbation response should track the fold, not the site label.')]));
children.push(bullet([t('Natural versus engineered. ', { bold: true }), t('The MIRROR and LEAPER3 designs are engineered guide-like constructs rather than natural substrates. If the determinant rules are physical rather than evolutionary, they should hold equally in both classes — a test the natural-only Set 1 panel cannot perform.')]));
children.push(bullet([t('Rule-violation structure. ', { bold: true }), t('Where Set 1 and Set 2 disagree, the disagreement should localise to parents whose edit site sits near a loop or bulge rather than in a clean stem — that is, violations should be structural rather than sequence-specific.')]));
children.push(h3('Confounds'));
children.push(bullet([t('Bulges and internal loops are uncontrolled. ', { bold: true }), t('LEAPER3_FLNA_50bp_AC_external_bulge carries a deliberate bulge, and at 108 nt it is the longest parent by a wide margin. It differs from the other parents on several axes at once and should not be pooled naively.')]));
children.push(bullet([t('No shared normalisation with Set 1 except via the overlapping parents. ', { bold: true }), t('The different primer pair means absolute editing rates are not directly comparable across sets — see section 2.3.')]));
children.push(new Paragraph({ children: [new PageBreak()] }));

// --- Lib 2 Set 1 ---
children.push(h2('3.3 Library 2, Set 1 — gc_library2.csv (ART10, 1,276 designs)'));
children.push(body([t('Contents. ', { bold: true }), t('Explicitly the complement of Library 1. Deduplicated by exact sequence, then filled in priority tiers: (1) deeper-trimmed, shorter children that Library 1 discarded; (2) the full 5 × 5 above × below combination grid; (3) GC-band rebalancing of the remainder.')]));
children.push(callout('Primary hypothesis', 'Local determinants are not additive. Simultaneous 5′ and 3′ stabilisation interacts epistatically, because the two sides jointly determine whether the target base can flip out of the helix. This is the one hypothesis Library 1 structurally cannot test.'));
children.push(h3('Prediction'));
children.push(body('For a combined variant (i, j), measured editing should deviate systematically from the additive prediction formed by combining above_i and below_j as measured in Library 1 — specifically a negative interaction at high i + j, where the site is clamped from both sides.', { after: 160 }));
children.push(h3('Secondary and tertiary hypotheses'));
children.push(table(
  ['Tier', 'Hypothesis', 'Strength'],
  [
    [[t('1 — deeper trims', { size: 18, bold: true })], 'Duplex length has a threshold rather than a gradient: editing collapses below a minimum duplex length rather than declining smoothly.', [t('Strong — these designs exist specifically because Library 1 excluded them.', { size: 18 })]],
    [[t('2 — combination grid', { size: 18, bold: true })], 'The above × below interaction (primary hypothesis above).', [t('Strong — complete 5 × 5 grid per edit site.', { size: 18 })]],
    [[t('3 — GC rebalancing', { size: 18, bold: true })], 'Global GC content has an effect separable from local base-pair identity.', [t('Exploratory — tier 3 is whatever survived two prior filters, so GC band is correlated with parent and variant class in the surviving set.', { size: 18 })]],
  ],
  [2100, 3630, 3630],
));
children.push(h3('Confounds'));
children.push(bullet([t('Tiering makes this a non-random sample. ', { bold: true }), t('Library 2 is drawn in priority order from its own candidate pool, so any cross-library comparison needs the tier as a covariate.')]));
children.push(bullet([t('Parent representation is badly uneven. ', { bold: true }), t('After deduplication, hGLI1 contributes 28 designs and AZIN1 contributes 29, against 200 each for 5-HT2C_2, PRE_MIRNA142, GluR-B_QR and GluR-B_RG. The small-n parents are underpowered for any within-parent interaction test — this is why the library totals 1,276 rather than reaching the 1,800 cap.')]));
children.push(bullet([t('Dependency on Library 1. ', { bold: true }), t('Deduplication is performed against the Library 1 CSV by exact sequence string, so Library 2’s composition is only meaningful relative to that exact file.')]));

// --- Lib 2 Set 2 ---
children.push(h2('3.4 Library 2, Set 2 — gc_library_set2b.csv (ART11, 1,717 designs)'));
children.push(body([t('Contents. ', { bold: true }), t('The same complementary tiered scheme applied to the Set 2 parents.')]));
children.push(callout('Primary hypothesis', 'The epistasis detected in Library 2 Set 1 is a general property of ADAR substrate recognition rather than a feature of one parent panel: the same above × below interaction recurs, with the same sign and comparable magnitude, on the Set 2 parents.'));
children.push(h3('Role'));
children.push(body('This is the replication arm. It is what licenses the claim that local determinants are non-additive in general, rather than non-additive in nine particular hairpins.'));
children.push(h3('Confounds'));
children.push(bullet([t('GRIA2_R/G_2 contributes only 15 designs ', { bold: true }), t('and GRIA2_R/G_1 only 102, against 200 for the other eight parents — both are short 30 nt hairpins whose candidate pools were largely consumed by Library 1. The replication therefore rests mainly on the eight well-represented parents.')]));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ===== 4. Cross-library =====
children.push(h1('4. Cross-library analyses'));
children.push(body('The pooled design enables five analyses that no single library supports:'));
children.push(table(
  ['#', 'Analysis', 'How the design supports it'],
  [
    ['1', [t('Additivity test', { size: 18, bold: true })], 'Library 1 single mutants supply main effects; Library 2 combined mutants supply observed joint effects. A direct residual test.'],
    ['2', [t('Length threshold', { size: 18, bold: true })], 'Pool trim ladders across all four libraries; model editing against child length with parent as a random effect.'],
    ['3', [t('Rule portability', { size: 18, bold: true })], 'Correlate per-axis effect sizes between Set 1 and Set 2.'],
    ['4', [t('Mismatch hierarchy', { size: 18, bold: true })], 'Pool across variants from every parent — well powered, since every parent contributes them.'],
    ['5', [t('Assay noise floor', { size: 18, bold: true })], 'Parents shared between sets (section 2.3) appear under two primer pairs, giving a direct estimate of primer and amplification variance.'],
  ],
  [560, 2200, 6600],
));

// ===== 5. Gaps =====
children.push(h1('5. Gaps to close before analysis'));
children.push(body('Four issues limit what the current design can conclude. The first two affect interpretation of the results; the last two affect reproducibility.'));
children.push(bullet([t('No negative controls. ', { bold: true }), t('There are no scrambled designs, no single-stranded designs, and no edit-site-free hairpins. Without them a low-editing measurement cannot be distinguished from the assay floor.')]));
children.push(bullet([t('No designed replicates. ', { bold: true }), t('Every barcode carries a distinct sequence, so technical variance must be estimated indirectly rather than from intentional duplicates. The cross-set shared parents are the partial exception.')]));
children.push(bullet([t('No cross-set normalisation built in. ', { bold: true }), t('Different primer pairs mean different amplification efficiency, so absolute editing rates are not comparable across sets without either a spike-in or explicit use of the shared parents.')]));
children.push(bullet([t('The pooling and renaming step is not scripted. ', { bold: true }), t('The combined FASTA files and the short-name mapping CSVs exist in the repository, but no committed script regenerates them. The design-to-oligo mapping currently rests on two files that cannot be rebuilt from source.')]));
children.push(rule());
children.push(body([t('Recommended priority. ', { bold: true }), t('Develop the Library 2 epistasis hypothesis first. It is the only one of the four that tests something Library 1 structurally cannot, and it is the claim most likely to carry a publication. Resolve the negative-control gap before any order goes out, if one has not already been placed.')]));

// ===== Build =====
const doc = new Document({
  creator: 'ADAR library design',
  title: 'ADAR Substrate-Determinant Libraries',
  description: 'Parent structures and design hypotheses for four pooled ADAR editing libraries',
  numbering: {
    config: [{
      reference: 'dash',
      levels: [
        { level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360, hanging: 220 } } } },
        { level: 1, format: LevelFormat.BULLET, text: '◦', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 220 } } } },
      ],
    }],
  },
  styles: { default: { document: { run: { font: BODY, size: 21 } } } },
  sections: [{ properties: { page: PAGE }, children }],
});

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync('/home/user/RNA/ADAR_Library_Design_Hypotheses.docx', b);
  console.log('wrote ADAR_Library_Design_Hypotheses.docx', b.length, 'bytes');
});
