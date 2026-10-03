# Running the RNArtistCore renders on macOS

Produces one SVG + PNG per parent hairpin, edit sites in red, plus an optional
montage sheet per set.

Two stages, with different requirements:

| Stage | Script | Needs |
|---|---|---|
| Render each parent | `gen_rnartist_parents.py` | Java + Python 3 (stdlib only) |
| Montage onto one sheet | `montage_rnartist.py` | `cairosvg`, `Pillow`, and Homebrew `cairo` |

The montage is optional — stage 1 alone gives you publication-ready SVGs.

---

## 1. Java

RNArtistCore needs a JDK (17 or newer; 21 is what this was built against).

```bash
java -version          # already have one? skip ahead
brew install openjdk@21
sudo ln -sfn $(brew --prefix)/opt/openjdk@21/libexec/openjdk.jdk \
             /Library/Java/JavaVirtualMachines/openjdk-21.jdk
```

## 2. RNArtistCore jar

One 66 MB download, kept outside the repo (it is gitignored, not vendored).

```bash
mkdir -p ~/tools && cd ~/tools
curl -LO https://repo1.maven.org/maven2/io/github/fjossinet/rnartist/rnartistcore/0.4.8/rnartistcore-0.4.8-jar-with-dependencies.jar

# verify before running it
shasum -a 256 rnartistcore-0.4.8-jar-with-dependencies.jar
# expect: cd08603bd718455f428cc9c07387023a5c5d96c88768f43eb276dbca235788b8
```

Sanity check — render a tiny hairpin:

```bash
mkdir -p ~/tools/rnatest && cd ~/tools/rnatest
printf '>test\nGGGAAACCC\n(((...)))\n' > test.vienna
java -jar ~/tools/rnartistcore-0.4.8-jar-with-dependencies.jar -f ~/tools/rnatest/test.vienna
ls    # expect test.kts, test.png, test.vienna
```

> **Always pass RNArtistCore an absolute path.** Two different things bite you
> otherwise:
>
> - **Relative paths resolve against the jar, not your shell.** This is
>   documented behaviour, not a bug: "if a path doesn't start with `/`
>   (Linux/MacOS) or `[A-Z]:/` (Windows), it is considered as a relative path
>   (meaning that it is added to the absolute path of the rnartistcore jar file
>   used to run the script)". So with the jar in `~/tools/`,
>   `-f ./test.vienna` looks for `/Users/you/tools/./test.vienna` no matter
>   which directory you are standing in, and fails with `FileNotFoundException`.
> - **A bare filename crashes outright** — `-f test.vienna` throws
>   `NullPointerException: getParentFile(...) must not be null`, because it
>   calls `getParentFile()` on your argument and a bare name has no parent.
>   That one does look like a genuine bug.
>
> The same rule applies to `path` inside `svg {}` and `png {}` blocks, and to
> `file` inside `vienna {}`. `gen_rnartist_parents.py` writes absolute paths
> everywhere, so it is unaffected; this only bites when driving the jar by hand.

On JDK 21+ you will also see several `WARNING: ... sun.misc.Unsafe ...` lines
from Kotlin's bundled IntelliJ libraries. They are harmless deprecation notices,
not errors — the render still succeeds.

## 3. Render the parents

```bash
cd /path/to/RNA
python3 scripts/gen_rnartist_parents.py \
    --jar ~/tools/rnartistcore-0.4.8-jar-with-dependencies.jar
```

Writes to `scripts/rnartist/set1/` and `scripts/rnartist/set2/`, one
`.vienna`, `.kts`, `.svg` and `.png` per parent. Takes a few minutes — each
molecule is a separate JVM launch.

Useful flags:

```bash
--only set1            # one set only
--out some/other/dir   # different destination
```

Only parents that contribute designs are rendered, read from the library CSVs
rather than the parent file — a record can parse cleanly and still produce no
designs (see CLAUDE.md).

## 4. Montage (optional)

```bash
brew install cairo
python3 -m pip install cairosvg Pillow
python3 scripts/montage_rnartist.py
```

Writes `scripts/rnartist_parents_set1.png` and `..._set2.png`.

```bash
--scale 4     # higher resolution (default 3)
--cols 5      # panels per row (default 10)
```

**Apple Silicon gotcha:** `cairosvg` fails with `OSError: no library called
"cairo-2" was found` because `cairocffi` does not look in Homebrew's ARM prefix.
Fix with:

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
```

Add that to your `~/.zshrc` to make it stick.

---

## Editing the look

Each `.kts` is a standalone RNArtistCore script you can edit and re-run on its
own, without the Python wrapper:

```bash
java -jar ~/tools/rnartistcore-0.4.8-jar-with-dependencies.jar \
     scripts/rnartist/set1/BDF2.kts
```

Colours and detail level live at the top of `gen_rnartist_parents.py`
(`NEUTRAL_SHAPE`, `EDIT_SHAPE`, `DETAILS`). RNArtistCore also ships named
schemes — swap the whole `color` block for `scheme { value = "Midnight Paradise" }`
to try one.

## Known quirk

RNArtistCore appends a "Reactivity" colour-scale legend to every SVG, placed at
negative x. Its own PNG crops it away, but a faithful rasteriser (browser,
Illustrator, cairosvg) draws the part inside the viewBox as a stray red gradient
bar. `montage_rnartist.py` strips it. If you open an SVG directly and see that
bar, that is what it is — delete the `<defs>` block and everything after it.

That legend exists because RNArtistCore can colour residues by reactivity data,
which is directly useful once DMS-MaPseq reads are in hand.

---

## DSL cheat sheet

Full reference: <https://github.com/fjossinet/RNArtistCore> (the README is the
manual). Worked examples: `scripts/readme_plots.kts` in that repo — ~30
complete `rnartist { }` blocks.

### Block order matters

```
rnartist {
  svg { }      // or png { } — at least one required
  ss { }       // required
  data { }     // MUST come before theme and layout
  theme { }
  layout { }
}
```

Only one `theme`, one `layout` and one `data` per `rnartist` block.

### Colour targets

`type` selects what gets painted. **Uppercase = the residue shape, lowercase =
the letter inside it.**

| `type` | Paints |
|---|---|
| `N` / `n` | every residue shape / letter |
| `A` `U` `G` `C` | that base's shape |
| `a` `u` `g` `c` | that base's letter |

`value` takes a hex string (`"#D62728"`) or a CSS name (`"darkgreen"`). Add a
`location { }` block to restrict it to given positions:

```
color {
  type = "N"
  value = "#D62728"
  location {
    17 to 17
  }
}
```

That is exactly how `gen_rnartist_parents.py` marks edit sites.

### Detail levels

`details { value = 1..5 }` — 1 is a bare backbone outline, 5 draws every
residue with its letter. We use 5.

### Named schemes

Instead of individual `color` blocks, `scheme { value = "Midnight Paradise" }`
applies one of 18 built-in palettes. Quickest way to try a different look: swap
the whole colour section of one `.kts` for a `scheme` line and re-run it.

### Layout

`layout { branch { location { } ; value = <degrees> } }` rotates a branch when
helices collide. RNArtistCore computes a non-overlapping layout itself and
writes it into the per-2D `.kts` it generates — so if a molecule looks tangled,
re-run its own generated script rather than hand-tuning angles.

### Linking DMS reactivity (for later)

The `data` element attaches a value per residue and colours by gradient, with
`lt` / `gt` / `between` filters. Values can be listed inline or loaded from an
external file. Remember `data` must precede `theme`.
