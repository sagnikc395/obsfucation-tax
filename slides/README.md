# slides

`obfuscation-tax.pptx` is generated, not hand-edited. The source of truth is
`build_deck.js`, and every figure on a slide comes from `ANALYSIS.md` or `README.md`,
which in turn trace to files in `results/`.

## Rebuilding

`pptxgenjs` is the only dependency and it is not vendored here:

```sh
npm install pptxgenjs
node build_deck.js
```

The generator also applies the theme colours through `apply_theme.js` from the pptx
skill, since pptxgenjs cannot write theme colours itself. Without it the deck still
builds, but scheme colours fall back to Office's stock palette:

```sh
APPLY_THEME=/path/to/pptx/scripts/apply_theme.js node build_deck.js
```

## Checks worth rerunning after an edit

```sh
python scripts/office/validate.py obfuscation-tax.pptx   # from the pptx skill
python scripts/slide_text.py obfuscation-tax.pptx        # content, notes, ordering
uv run --with python-pptx python check_geometry.py obfuscation-tax.pptx
```

Visual QA needs LibreOffice to render the deck to images, which is not installed on
this machine. `check_geometry.py` stands in for it: shapes against the canvas and the
0.5 inch margin, estimated wrapped text height per box, and overlapping text frames.
Its glyph widths are averages, so a flagged box is worth a look rather than certainly
wrong, and it does not catch everything a render would.

## Structure

Four sections, eighteen slides, following the arc of `ANALYSIS.md`:

| Section | Slides |
| --- | --- |
| Background | the question, the three papers, the three outcomes |
| Design and preconditions | how the measurement works, what the gates said, the controls |
| The sweep and the turn | the table, the arithmetic behind it, and four findings |
| What it means | the verdict, what holds up, what broke, the eleven fixes, where to go next |

Two layouts carry the deck: `CONTENT` for the light slides and `TITLE_DARK` /
`STATEMENT_DARK` for the cover and the verdict. Cards, badges and stat callouts are
composed per slide on top of those.
