# ADAR library design — project notes

Generators build oligo libraries from parent RNA hairpins for ADAR editing
experiments. Pipeline: parent `.txt` files → design CSVs (`generate_gc_library*.py`)
→ 170 nt oligos with primers and barcodes (`run_libraries.py`) → FASTA for synthesis.

## Before generating or ordering any library

Run `python3 check_library.py <design CSVs> --parents <parent file> --oligos PRIMER=FILE`
and resolve everything it reports as BLOCKING. Then work through the questions
below with the user. These come from problems that reached the ordered Set 1
pilot unnoticed — raise them explicitly rather than assuming the defaults are
what the user wants.

### Ask every time

1. **Which parents should contribute, and does the output match?**
   A parent can parse cleanly and still produce nothing. Confirm the contributing
   list against the user's intent rather than the input file — in Set 1 three
   records (5-HT2C_1, AZIN1_2, GluR_BRG_15mer) dropped out, which turned out to
   match the user's choice, but the code would have dropped them either way.

2. **How is "across" defined for this build?**
   *This is the known flaw.* `sequence_variants` only generates `across` variants
   when the edit site has a formal dot-bracket partner (`if partner != -1`). An
   adenosine in an internal loop or bulge often has a nucleotide directly across
   from it in the helix with no bracket pairing — ADAR edits these contexts
   routinely. In Set 1 this silently skipped BDF2 (A17, opposite C34),
   GluR-B_RG (A6, opposite C51), GluR_BRG_15mer_2 (A6, opposite C29) and
   5-HT2C_2's A4 (opposite C72) — all sitting at a native A·C mismatch, the state
   `across_C` is meant to create. Define `across` geometrically (the residue(s)
   opposite within the enclosing internal loop), not by `P[e]`. A site in a
   *terminal* loop genuinely has nothing across from it — that is geometry, not a
   bug, and such parents are still valid substrates for the other axes.

3. **What is the minimum design length?**
   The trim ladder has no floor and peels to 6 nt. Set 1 shipped 274 designs
   under 20 nt (AZIN1 contributed 103 of its 229). Agree a floor before building;
   below ~20 nt there is no duplex for ADAR to act on. Sub-threshold designs do
   double as an empirical assay floor, so dropping them entirely is a choice to
   make deliberately, not a default.

4. **Do mutations actually change the sequence?**
   `apply_bp` sets a Watson–Crick pair unconditionally, so a substitution onto a
   position that already carries that pair is a no-op. Set 1 shipped 228 designs
   labelled as mutations that are identical to their unmutated parent, and 537
   oligos duplicating another design's sequence. Skip no-ops at generation, or
   accept them knowingly — they are usable as technical replicates, but only if
   the analysis groups on sequence rather than label.

5. **Which mutation classes reach which parents?**
   Per-parent caps plus tier ordering can starve a whole class. In Set 1 the
   `combined` (above × below) grid reached only 4 of 9 parents, because parents
   with rich length ladders exhausted their 200-slot quota on trims before
   reaching it. If a hypothesis depends on a class, reserve a quota for it rather
   than letting priority order decide.

6. **Is the demultiplexing key unique?**
   `run_libraries.py` resets the barcode pool per library, so barcodes repeat
   across libraries (18 shared between ART5 and ART10; 154 across the full pool).
   The composite `(primer, barcode)` is unique and is the only safe key.

7. **Can every submitted oligo be traced back to its design?**
   Submitted FASTAs may carry generic names in a different order from the design
   files (`oligo_set1_1_seq_N`). Build the crosswalk by exact sequence match
   before the reads come back — see `build_mapping.py` and
   `submitted_set1_crosswalk.csv`.

## Analysis

Group on `designed_seq`, never on `mutation_label`. Demultiplex on
`(primer, barcode)`. `oligo_master_mapping.csv` carries both plus full design
provenance.

## Shipped state

Set 1 (3,076 oligos, ART5 + ART10) is ordered and in experiment. Do not
regenerate or renumber it. Set 2 (3,717 oligos, ART7 + ART11) exists in the
repo but its status is not confirmed here — ask before touching either.
