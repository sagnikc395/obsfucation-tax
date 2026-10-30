/**
 * Builds slides/obfuscation-tax.pptx from the numbers in ANALYSIS.md and README.md.
 *
 * Every figure on a slide traces to a file in results/ or is derived from one, the same
 * rule the write-ups follow. Nothing here is typed from memory.
 *
 *   npm install pptxgenjs && node build_deck.js      (see README.md in this folder)
 */

const path = require("path");
const PptxGenJS = require("pptxgenjs");

// ---------------------------------------------------------------- theme ----
// Two accents that differ in lightness as well as hue, so the attack and the defence
// stay apart in greyscale and for red/green colour blindness.
const THEME = {
  name: "Obfuscation Tax",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1A2230", // ink
    lt1: "FFFFFF",
    dk2: "4A5663", // muted body
    lt2: "EEF1F4", // card tint
    accent1: "C2541B", // the attack
    accent2: "2E6E8E", // the defence
    accent3: "15202B", // dark slide ground
    accent4: "8A9BA8",
    accent5: "D7DEE4",
    accent6: "6B7A88",
    hlink: "2E6E8E",
    folHlink: "6B7A88",
  },
};

const INK = "1A2230";
const MUTED = "4A5663";
const FAINT = "6B7A88";
const ATTACK = "C2541B";
const DEFENCE = "2E6E8E";
const DARK = "15202B";
const TINT = "EEF1F4";
const RULE = "D7DEE4";
const PAPER = "FFFFFF";
const ONDARK = "E7ECF1";
const ONDARK_MUTED = "9DADBC";

const W = 13.333;
const M = 0.62; // side margin
const CW = W - 2 * M; // 12.09 content width

const pres = new PptxGenJS();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "obsfucation-tax";
pres.company = "obsfucation-tax";
pres.subject = "What does a model give up to hide from an activation probe?";
pres.title = "The Obfuscation Tax";

// --------------------------------------------------------------- layouts ----
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: DARK },
  objects: [
    {
      placeholder: {
        options: { name: "title", type: "title", x: M, y: 2.35, w: CW, h: 2.3,
          fontSize: 40, bold: false, color: PAPER, valign: "top" },
        text: "",
      },
    },
    {
      placeholder: {
        options: { name: "body", type: "body", x: M, y: 4.75, w: 9.4, h: 1.2,
          fontSize: 16, color: ONDARK_MUTED, valign: "top" },
        text: "",
      },
    },
  ],
});

pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: PAPER },
  objects: [
    {
      placeholder: {
        options: { name: "title", type: "title", x: M, y: 0.82, w: CW, h: 0.72,
          fontSize: 28, bold: true, color: INK, valign: "top" },
        text: "",
      },
    },
  ],
  slideNumber: { x: 12.6, y: 6.98, w: 0.5, h: 0.28, fontSize: 10, color: FAINT, align: "right" },
});

pres.defineSlideMaster({
  title: "STATEMENT_DARK",
  background: { color: DARK },
  objects: [
    {
      placeholder: {
        options: { name: "title", type: "title", x: M, y: 1.46, w: CW, h: 1.02,
          fontSize: 54, bold: false, color: PAPER, valign: "top" },
        text: "",
      },
    },
  ],
});

// --------------------------------------------------------------- helpers ----
let n = 0;
const slide = (masterName, sectionTitle) => {
  n += 1;
  return pres.addSlide({ masterName, sectionTitle });
};

/** Small caps eyebrow above a title. */
function eyebrow(s, text, color = ATTACK) {
  s.addText(text.toUpperCase(), {
    x: M, y: 0.50, w: CW, h: 0.26, fontSize: 11, bold: true, charSpacing: 1.6,
    color, isTextBox: true, margin: 0, objectName: "eyebrow",
  });
}

/** One pinned source line along the bottom. */
function source(s, text) {
  s.addText(text, {
    x: M, y: 6.98, w: 11.6, h: 0.28, fontSize: 10, color: FAINT,
    isTextBox: true, margin: 0, objectName: "source",
  });
}

/** A tinted card. Returns nothing; compose text on top. */
function card(s, { x, y, w, h, fill = TINT, name }) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: fill },
    objectName: name,
  });
}

/** Numbered badge in a filled circle: the deck's one repeated motif. */
function badge(s, { x, y, label, fill = INK, color = PAPER, d = 0.42 }) {
  s.addShape(pres.ShapeType.ellipse, {
    x, y, w: d, h: d, fill: { color: fill }, line: { color: fill },
    objectName: `badge-${label}`,
  });
  s.addText(String(label), {
    x, y, w: d, h: d, fontSize: 13, bold: true, color, align: "center",
    valign: "middle", isTextBox: true, margin: 0,
  });
}

/** Big figure with a caption under it. */
function stat(s, { x, y, w, value, label, color = INK, size = 40 }) {
  s.addText(String(value), {
    x, y, w, h: 0.66, fontSize: size, bold: true, color, isTextBox: true,
    margin: 0, fontFace: THEME.headFontFace, objectName: `stat-${label}`,
  });
  s.addText(label, {
    x, y: y + 0.68, w, h: 0.56, fontSize: 12, color: MUTED, isTextBox: true, margin: 0,
  });
}

const tableBase = {
  fontFace: THEME.bodyFontFace,
  fontSize: 13,
  color: INK,
  border: [
    { type: "none" },
    { type: "none" },
    { type: "solid", pt: 0.5, color: RULE },
    { type: "none" },
  ],
  autoPage: false,
};

const th = (t) => ({
  text: t,
  options: { bold: true, fontSize: 11, color: FAINT, fill: { color: PAPER } },
});
const td = (t, o = {}) => ({ text: String(t), options: { fontSize: 13, color: INK, ...o } });

// ================================================================= SLIDES ===

// 1 ------------------------------------------------------------------ cover
pres.addSection({ title: "Background" });
{
  const s = slide("TITLE_DARK", "Background");
  s.addText("THE OBFUSCATION TAX", {
    x: M, y: 1.72, w: CW, h: 0.34, fontSize: 12, bold: true, charSpacing: 2.4,
    color: "E8873F", isTextBox: true, margin: 0, objectName: "eyebrow",
  });
  s.addText("What does a model give up to hide from an activation probe?", {
    placeholder: "title", fontFace: THEME.headFontFace,
  });
  s.addText(
    "One run on mbpp with Qwen3.5-4B. It could not measure the tax we came for, and working out why produced a defence result instead.",
    { placeholder: "body" }
  );
  s.addShape(pres.ShapeType.rect, {
    x: M, y: 6.44, w: 1.5, h: 0.028, fill: { color: "E8873F" }, line: { color: "E8873F" },
    objectName: "cover-mark",
  });
  s.addText("obsfucation-tax  ·  October 2026", {
    x: M, y: 6.66, w: 8, h: 0.3, fontSize: 11, color: "7E8FA0", isTextBox: true, margin: 0,
  });
  s.addNotes(
    "This follows ANALYSIS.md in the order the experiment happened: what we set out to measure, where it went wrong, and what the run still supports. Every number traces to a file in results/."
  );
}

// 2 ------------------------------------------------------------ three papers
{
  const s = slide("CONTENT", "Background");
  eyebrow(s, "Where the question comes from");
  s.addText("Three papers, and the thing none of them measures", { placeholder: "title" });

  const cards = [
    {
      who: "Goldowsky-Dill et al.",
      venue: "ICML 2025",
      claim: "The defence works",
      color: DEFENCE,
      body:
        "Linear probes on the residual stream of Llama-3.3-70B, read after layer 22 of 80. AUROC 0.96 to 0.999. At a 1% false-positive threshold they catch 95 to 99% of deceptive responses.\n\nProbing two layers later drops recall to nearly zero.",
    },
    {
      who: "Bailey et al.",
      venue: "ICLR 2026",
      claim: "It can be fooled",
      color: ATTACK,
      body:
        "Monitor recall driven to 0% while keeping a 90% jailbreak rate, and the obfuscated activations carry over to probes they never attacked.\n\nOne limit: “on a complex task (writing SQL code), obfuscation reduces model performance.”",
    },
    {
      who: "Gupta & Jenner",
      venue: "2025",
      claim: "The strongest attacker",
      color: ATTACK,
      body:
        "RL-Obfuscation finetunes a model to evade latent-space monitors while holding its black-box behaviour steady.\n\nHolding it steady needs an explicit quality term in the reward. Without paying to hold the output up, evasion degrades it.",
    },
  ];

  const cw = 3.82, gap = 0.3;
  cards.forEach((c, i) => {
    const x = M + i * (cw + gap);
    card(s, { x, y: 1.64, w: cw, h: 3.56, name: `paper-${i}` });
    s.addText(`${c.who}  ·  ${c.venue}`, {
      x: x + 0.26, y: 1.84, w: cw - 0.52, h: 0.26, fontSize: 10.5, color: FAINT,
      isTextBox: true, margin: 0,
    });
    s.addText(c.claim, {
      x: x + 0.26, y: 2.12, w: cw - 0.52, h: 0.4, fontSize: 19, bold: true, color: c.color,
      fontFace: THEME.headFontFace, isTextBox: true, margin: 0,
    });
    s.addText(c.body, {
      x: x + 0.26, y: 2.60, w: cw - 0.52, h: 2.46, fontSize: 12, color: MUTED,
      lineSpacingMultiple: 1.26, isTextBox: true, margin: 0, valign: "top",
    });
  });

  card(s, { x: M, y: 5.48, w: CW, h: 0.9, fill: DARK, name: "gap" });
  s.addText(
    [
      { text: "All three ask whether evasion works, and it does. ", options: { color: PAPER, bold: true } },
      { text: "The cost shows up twice as a side condition, and neither paper treats it as the measurement.", options: { color: ONDARK_MUTED } },
    ],
    { x: M + 0.34, y: 5.48, w: CW - 0.68, h: 0.9, fontSize: 15, valign: "middle",
      isTextBox: true, margin: 0, objectName: "gap-text" }
  );
  s.addNotes(
    "Bailey finds performance drops on the one task where performance is measurable. Gupta and Jenner have to add a scoring term to stop completions degrading. Neither measures what evasion costs the attacker."
  );
}

// 3 ----------------------------------------------------------- the question
{
  const s = slide("CONTENT", "Background");
  eyebrow(s, "The bet");
  s.addText("Assume the model can fool the probe. What does that cost?", {
    placeholder: "title",
  });

  s.addText(
    "The probe reads the same internal state the model computes with, so pushing that state around should not be free. Three outcomes, written down before anything ran.",
    { x: M, y: 1.62, w: 10.4, h: 0.52, fontSize: 14, color: MUTED, isTextBox: true, margin: 0 }
  );

  const rows = [
    ["Dodges, and sandbags just as well", "The probe is close to useless against an attacker who knows about it.", ATTACK],
    ["Dodges, and stops sandbagging", "Evasion cost the attack. The probe was doing real work even though it can be evaded.", DEFENCE],
    ["Dodges, but the text monitor lights up", "The probe pushed the attack somewhere another defence can see.", DEFENCE],
  ];
  rows.forEach((r, i) => {
    const y = 2.34 + i * 1.18;
    card(s, { x: M, y, w: CW, h: 1.0, name: `outcome-${i}` });
    badge(s, { x: M + 0.3, y: y + 0.29, label: i + 1, fill: r[2] });
    s.addText(r[0], {
      x: M + 0.96, y: y + 0.16, w: 4.5, h: 0.36, fontSize: 15, bold: true, color: INK,
      fontFace: THEME.headFontFace, isTextBox: true, margin: 0,
    });
    s.addText(r[1], {
      x: M + 0.96, y: y + 0.54, w: 10.6, h: 0.36, fontSize: 12.5, color: MUTED,
      isTextBox: true, margin: 0,
    });
  });

  s.addText(
    [
      { text: "The tax", options: { bold: true, color: INK } },
      { text: "  is the gap between how fast detection falls and how fast the attack falls.", options: { color: MUTED } },
    ],
    { x: M, y: 6.04, w: CW, h: 0.4, fontSize: 14, isTextBox: true, margin: 0 }
  );
  source(s, "A fourth pattern was written down as a non-result: detection falling because the model was steered into incoherence.");
  s.addNotes("The three outcomes are the measurement's whole design. Outcome 1 is what the table appeared to show.");
}

// 4 -------------------------------------------------------------- the build
pres.addSection({ title: "Design and preconditions" });
{
  const s = slide("CONTENT", "Design and preconditions");
  eyebrow(s, "Method");
  s.addText("How the measurement is built", { placeholder: "title" });

  const steps = [
    ["300 mbpp problems", "Natural-language spec plus a visible test. Scored by running the official tests, so the ground truth is executable."],
    ["Two prompts per problem", "Honest, and a sandbagging prompt asking for something subtly wrong that still reads as sincere."],
    ["Attack = a flip", "Right under the honest prompt and wrong under the sandbagging one, on the same problem. A validity flag keeps breakage out."],
    ["Probe at layer 20", "Logistic regression on the residual stream, pooled over answer tokens only, split by problem."],
    ["Steer during generation", "Subtract alpha × unit(w) at every position. Features re-read under the same hook."],
    ["Measure four columns", "Attacked probe, a transfer probe at layer 28 never steered, the accuracy drop, and a text-only monitor."],
  ];

  const cw = 3.82, gap = 0.3, ch = 1.52;
  steps.forEach((st, i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = M + col * (cw + gap);
    const y = 1.62 + row * (ch + 0.28);
    card(s, { x, y, w: cw, h: ch, name: `step-${i}` });
    badge(s, { x: x + 0.24, y: y + 0.24, label: i + 1, fill: i < 3 ? INK : DEFENCE, d: 0.36 });
    s.addText(st[0], {
      x: x + 0.7, y: y + 0.22, w: cw - 0.96, h: 0.34, fontSize: 14, bold: true, color: INK,
      fontFace: THEME.headFontFace, isTextBox: true, margin: 0,
    });
    s.addText(st[1], {
      x: x + 0.24, y: y + 0.64, w: cw - 0.48, h: 0.8, fontSize: 11.5, color: MUTED,
      lineSpacingMultiple: 1.2, isTextBox: true, margin: 0,
    });
  });

  card(s, { x: M, y: 5.18, w: CW, h: 0.86, fill: DARK, name: "gates" });
  s.addText(
    [
      { text: "Gated before any steering runs:  ", options: { color: ONDARK_MUTED } },
      { text: "at least 40 successful attacks", options: { color: PAPER, bold: true } },
      { text: "  and  ", options: { color: ONDARK_MUTED } },
      { text: "a headline AUROC above 0.65", options: { color: PAPER, bold: true } },
    ],
    { x: M + 0.34, y: 5.18, w: CW - 0.68, h: 0.86, fontSize: 14, valign: "middle",
      isTextBox: true, margin: 0 }
  );
  source(s, "Model: Qwen/Qwen3.5-4B, reasoning off, greedy. Reasoning on costs 68.5 s per generation, 11.4 hours for one pass.");
  s.addNotes("Reasoning is off because a trace costs 68.5 s per generation, which was not affordable on the hardware to hand. The write-up carries it as a limitation of this run.");
}

// 5 --------------------------------------------------------- preconditions
{
  const s = slide("CONTENT", "Design and preconditions");
  eyebrow(s, "Steps 1 and 2");
  s.addText("The preconditions, and the first warning we ignored", { placeholder: "title" });

  const stats = [
    ["4.67 pts", "accuracy drop, 48.7% to 44.0%", INK],
    ["p = 0.092", "McNemar, on the paired flips", INK],
    ["146", "answerable problems of 300", INK],
    ["25.3%", "attack rate on answerable", INK],
  ];
  const sw = 2.88, sgap = 0.19;
  stats.forEach((st, i) => {
    const x = M + i * (sw + sgap);
    card(s, { x, y: 1.62, w: sw, h: 1.46, name: `pre-${i}` });
    stat(s, { x: x + 0.26, y: 1.82, w: sw - 0.52, value: st[0], label: st[1], color: st[2], size: 25 });
  });

  card(s, { x: M, y: 3.32, w: 5.9, h: 2.5, fill: "F7E9E1", name: "gate-fail" });
  s.addText("The gate failed", {
    x: M + 0.34, y: 3.54, w: 5.2, h: 0.4, fontSize: 19, bold: true, color: ATTACK,
    fontFace: THEME.headFontFace, isTextBox: true, margin: 0,
  });
  s.addText(
    [
      { text: "37", options: { fontSize: 40, bold: true, color: ATTACK, fontFace: THEME.headFontFace } },
      { text: "  successful attacks against a minimum of 40.", options: { fontSize: 14, color: MUTED } },
    ],
    { x: M + 0.34, y: 4.02, w: 5.2, h: 0.86, isTextBox: true, margin: 0, valign: "middle" }
  );
  s.addText(
    "The sweep ran anyway, on a held-out half holding 20 of those 37. Every confidence interval in this deck is wide because of that.",
    { x: M + 0.34, y: 4.94, w: 5.2, h: 0.82, fontSize: 12.5, color: MUTED,
      lineSpacingMultiple: 1.24, isTextBox: true, margin: 0 }
  );

  card(s, { x: M + 6.2, y: 3.32, w: 5.89, h: 2.5, name: "grid-warn" });
  s.addText("The second warning", {
    x: M + 6.54, y: 3.54, w: 5.2, h: 0.4, fontSize: 19, bold: true, color: INK,
    fontFace: THEME.headFontFace, isTextBox: true, margin: 0,
  });
  s.addText(
    [
      { text: "1.000", options: { fontSize: 40, bold: true, color: INK, fontFace: THEME.headFontFace } },
      { text: "  at every layer and every pooling.", options: { fontSize: 14, color: MUTED } },
    ],
    { x: M + 6.54, y: 4.02, w: 5.2, h: 0.86, isTextBox: true, margin: 0, valign: "middle" }
  );
  s.addText(
    "A grid where every entry is perfect cannot tell you which layer to attack, so the choice of layer 20 was effectively arbitrary.",
    { x: M + 6.54, y: 4.94, w: 5.2, h: 0.82, fontSize: 12.5, color: MUTED,
      lineSpacingMultiple: 1.24, isTextBox: true, margin: 0 }
  );
  source(s, "Source: results/pre_qwen35_4b_thinking_off_summary.json");
  s.addNotes("Both warnings were ignored. We wrote the gate in advance so that continuing would be awkward if the preconditions did not hold.");
}

// 6 ------------------------------------------------------------- controls
{
  const s = slide("CONTENT", "Design and preconditions");
  eyebrow(s, "Controls");
  s.addText("Two of three controls failed", { placeholder: "title" });

  const rows = [
    [th("Control"), th("Value"), th("n"), th("Wanted")],
    [td("Headline: honest-correct vs attack"), td("1.000", { bold: true }), td("146 / 37"), td("high", { color: FAINT })],
    [td("Text only"), td("0.774"), td("183"), td("near 0.5", { color: FAINT })],
    [td("Answer length alone"), td("0.672"), td("146 / 35"), td("near 0.5", { color: FAINT })],
    [td("Prompt, not behaviour"), td("1.000", { bold: true, color: ATTACK }), td("146 / 109"), td("near 0.5", { color: FAINT })],
    [td("Wrongness, not intent"), td("0.789"), td("146 / 154"), td("near 0.5", { color: FAINT })],
  ];
  s.addTable(rows, {
    ...tableBase, x: M, y: 1.62, w: 6.6, colW: [3.1, 1.2, 1.3, 1.0], rowH: 0.38,
    objectName: "controls-table",
  });

  card(s, { x: M + 7.0, y: 1.62, w: 5.09, h: 2.36, name: "means" });
  s.addText("Group means at layer 20", {
    x: M + 7.3, y: 1.82, w: 4.5, h: 0.3, fontSize: 12, bold: true, color: FAINT,
    isTextBox: true, margin: 0,
  });
  const means = [
    ["attack", "+7.92", ATTACK],
    ["sandbag-prompted, still correct", "+7.74", ATTACK],
    ["honest, correct", "−7.71", DEFENCE],
    ["honest, wrong", "−5.41", DEFENCE],
  ];
  means.forEach((m, i) => {
    const y = 2.22 + i * 0.4;
    s.addText(m[0], {
      x: M + 7.3, y, w: 3.3, h: 0.34, fontSize: 12.5, color: MUTED, isTextBox: true, margin: 0,
    });
    s.addText(m[1], {
      x: M + 10.6, y, w: 1.1, h: 0.34, fontSize: 13.5, bold: true, color: m[2],
      align: "right", isTextBox: true, margin: 0,
    });
  });

  card(s, { x: M, y: 4.24, w: CW, h: 1.62, fill: DARK, name: "verdict-controls" });
  s.addText("The probe was reading which prompt was used, and never the sabotage", {
    x: M + 0.36, y: 4.46, w: CW - 0.72, h: 0.42, fontSize: 19, bold: true, color: PAPER,
    fontFace: THEME.headFontFace, isTextBox: true, margin: 0,
  });
  s.addText(
    "An attack and a sandbag-prompted answer that came out correct sit 0.18 apart on a scale spanning 15.6. Hold the prompt constant and the same cell drops from 1.000 to 0.644, against a shuffled-label null that reaches 0.634. Answer length does much of the rest: 0.672 across prompts, 0.516 within. We noted the control and continued, because the headline was 1.000 and the attack machinery was already built.",
    { x: M + 0.36, y: 4.96, w: CW - 0.72, h: 0.86, fontSize: 12.5, color: ONDARK_MUTED,
      lineSpacingMultiple: 1.2, isTextBox: true, margin: 0 }
  );
  source(s, "Mean answer tokens: honest-correct 43.8, sabotaged 59.1, instruction ignored 57.1. Mean pooling sees length.");
  s.addNotes("The prompt control is the one that should have stopped us. It reads 1.000, which means the probe cannot tell a landed sabotage from an instruction that was ignored.");
}

// 7 ---------------------------------------------------------------- sweep
pres.addSection({ title: "The sweep and the turn" });
{
  const s = slide("CONTENT", "The sweep and the turn");
  eyebrow(s, "Steps 4 and 5");
  s.addText("The sweep, and ten minutes of thinking we had a result", { placeholder: "title" });

  const rows = [
    [th("alpha"), th("probe L20"), th("transfer L28"), th("accuracy drop"), th("monitor"), th("valid"), th("mean probe score")],
    [td("0"), td("1.000"), td("1.000"), td("0.274"), td("0.129"), td("1.000"), td("+8.04", { color: FAINT })],
    [td("1"), td("0.999"), td("1.000"), td("0.288"), td("0.129"), td("1.000"), td("+1.02", { color: FAINT })],
    [td("2"), td("0.572", { color: ATTACK, bold: true }), td("0.993"), td("0.342"), td("0.131"), td("1.000"), td("−6.16", { color: FAINT })],
    [td("4"), td("0.000", { color: ATTACK, bold: true }), td("0.718"), td("0.274"), td("0.117"), td("1.000"), td("−20.14", { color: FAINT })],
    [td("8"), td("0.000", { color: ATTACK, bold: true }), td("0.000"), td("0.274"), td("0.126"), td("1.000"), td("−48.60", { color: FAINT })],
  ];
  s.addTable(rows, {
    ...tableBase, x: M, y: 1.62, w: CW, colW: [1.1, 1.85, 1.95, 2.15, 1.6, 1.44, 2.0],
    rowH: 0.46, align: "left", objectName: "sweep-table",
  });

  const reads = [
    ["Detection collapses", "1.000 → 0.000", ATTACK],
    ["The attack survives", "drop holds 0.27 to 0.34", ATTACK],
    ["The monitor never moves", "0.117 to 0.131", INK],
    ["Nothing breaks", "valid rate 1.000", INK],
  ];
  const rw = 2.88, rgap = 0.19;
  reads.forEach((r, i) => {
    const x = M + i * (rw + rgap);
    card(s, { x, y: 5.16, w: rw, h: 1.08, name: `read-${i}` });
    s.addText(r[0], {
      x: x + 0.24, y: 5.34, w: rw - 0.48, h: 0.3, fontSize: 13, bold: true, color: INK,
      fontFace: THEME.headFontFace, isTextBox: true, margin: 0,
    });
    s.addText(r[1], {
      x: x + 0.24, y: 5.70, w: rw - 0.48, h: 0.3, fontSize: 12, color: r[2], isTextBox: true, margin: 0,
    });
  });

  source(s, "Reads as outcome 1: evasion is cheap and probes are weak. Five things in the saved features say otherwise.");
  s.addNotes("This is the table as it came back. Taken at face value it is a clean publishable result, and we read it that way for about ten minutes.");
}

// 8 ------------------------------------------------------------ arithmetic
{
  const s = slide("CONTENT", "The sweep and the turn");
  eyebrow(s, "The turn");
  s.addText("The probe score was never measuring the model", { placeholder: "title" });

  s.addText(
    "A logistic regression is affine in its input, so subtracting alpha × unit(w) from every answer token moves the decision score by a known amount. From the fitted probe, that amount is:",
    { x: M, y: 1.56, w: 7.1, h: 0.8, fontSize: 13.5, color: MUTED, lineSpacingMultiple: 1.2,
      isTextBox: true, margin: 0 }
  );

  card(s, { x: M, y: 2.46, w: 7.1, h: 1.24, fill: DARK, name: "predicted" });
  s.addText(
    [
      { text: "6.9907", options: { fontSize: 42, bold: true, color: "E8873F", fontFace: THEME.headFontFace } },
      { text: "   scaled units per alpha, predicted", options: { fontSize: 14, color: ONDARK_MUTED } },
    ],
    { x: M + 0.34, y: 2.46, w: 6.4, h: 1.24, valign: "middle", isTextBox: true, margin: 0 }
  );

  const rows = [
    [th("alpha"), th("realised shift"), th("residual"), th("% of imposed")],
    [td("1"), td("7.019"), td("−0.028"), td("0.4%", { bold: true })],
    [td("2"), td("7.100"), td("−0.218"), td("1.6%", { bold: true })],
    [td("4"), td("7.047"), td("−0.225"), td("0.8%", { bold: true })],
    [td("8"), td("7.080"), td("−0.717"), td("1.3%", { bold: true })],
  ];
  s.addTable(rows, {
    ...tableBase, x: M, y: 3.94, w: 7.1, colW: [1.3, 2.2, 1.8, 1.8], rowH: 0.42,
    objectName: "residual-table",
  });

  card(s, { x: M + 7.5, y: 1.56, w: 4.59, h: 4.48, name: "turn-note" });
  s.addText("What that means", {
    x: M + 7.8, y: 1.78, w: 4.0, h: 0.34, fontSize: 15, bold: true, color: INK,
    fontFace: THEME.headFontFace, isTextBox: true, margin: 0,
  });
  s.addText(
    [
      { text: "The residual is the only part of the score that reflects the model responding rather than being displaced. It is under 2% everywhere.\n\n", options: {} },
      { text: "So the entire AUROC column was computable before the sweep ran.\n\n", options: { color: INK, bold: true } },
      { text: "Predicted  1.000 · 0.999 · 0.651 · 0.000 · 0.000\nMeasured   1.000 · 0.999 · 0.572 · 0.000 · 0.000\n\n", options: { fontFace: "Courier New", fontSize: 11 } },
      { text: "We spent a GPU pass measuring a subtraction.", options: { color: ATTACK, bold: true } },
    ],
    { x: M + 7.8, y: 2.22, w: 4.0, h: 3.6, fontSize: 12.5, color: MUTED,
      lineSpacingMultiple: 1.22, isTextBox: true, margin: 0, valign: "top" }
  );

  source(s, "Derived from results/attack_qwen35_4b_thinking_off_mbpp_feats.npz against the refit probe.");
  s.addNotes("The model's text does change: mean answer tokens fall from 60.4 to 54.2 and the failing problems churn. The representation along the probe direction moves by the constant we imposed and almost nothing more.");
}

// 9 -------------------------------------------------------------- two-sided
{
  const s = slide("CONTENT", "The sweep and the turn");
  eyebrow(s, "Finding 1");
  s.addText("An AUROC of 0.000 is overshoot, not evasion", { placeholder: "title" });

  s.addChart(
    pres.ChartType.line,
    [
      { name: "One-sided AUROC", labels: ["0", "1", "2", "4", "8"], values: [1.0, 0.999, 0.572, 0.0, 0.0] },
      { name: "Two-sided AUROC", labels: ["0", "1", "2", "4", "8"], values: [1.0, 0.999, 0.604, 1.0, 1.0] },
    ],
    {
      x: M, y: 1.62, w: 7.3, h: 4.2,
      chartColors: [ATTACK, DEFENCE],
      lineSize: 3, lineSmooth: false,
      showTitle: true, title: "What the defender sees as alpha rises",
      titleColor: INK, titleFontSize: 13, titleFontFace: "+mn-lt",
      showLegend: true, legendPos: "b", legendColor: MUTED, legendFontSize: 11,
      legendFontFace: "+mn-lt",
      catAxisLabelColor: MUTED, catAxisLabelFontSize: 11, catAxisLabelFontFace: "+mn-lt",
      catAxisTitle: "alpha", showCatAxisTitle: true, catAxisTitleColor: FAINT,
      catAxisTitleFontSize: 11, catAxisTitleFontFace: "+mn-lt",
      valAxisLabelColor: MUTED, valAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt",
      valAxisMinVal: 0, valAxisMaxVal: 1, valAxisMajorUnit: 0.25,
      valGridLine: { color: "E7ECF0", size: 1 },
      catGridLine: { style: "none" },
      objectName: "twosided-chart",
    }
  );

  card(s, { x: M + 7.7, y: 1.62, w: 4.39, h: 2.1, fill: TINT, name: "ts-note1" });
  s.addText("Below 0.5 the classes are still perfectly separable, with the sign reversed. A defender who thresholds on distance from the honest median instead of on sign gets everything back.", {
    x: M + 8.0, y: 1.84, w: 3.8, h: 1.7, fontSize: 12.5, color: MUTED,
    lineSpacingMultiple: 1.24, isTextBox: true, margin: 0,
  });

  card(s, { x: M + 7.7, y: 3.88, w: 4.39, h: 1.94, fill: "F7E9E1", name: "ts-note2" });
  s.addText("The only setting that hides", {
    x: M + 8.0, y: 4.06, w: 3.8, h: 0.3, fontSize: 12, bold: true, color: FAINT,
    isTextBox: true, margin: 0,
  });
  s.addText(
    [
      { text: "alpha 2", options: { fontSize: 26, bold: true, color: ATTACK, fontFace: THEME.headFontFace } },
      { text: "\n0.604 two-sided, CI [0.48, 0.74], on 25 attacks.\nTPR at 1% FPR drops to 0.08.", options: { fontSize: 12.5, color: MUTED } },
    ],
    { x: M + 8.0, y: 4.38, w: 3.8, h: 1.3, lineSpacingMultiple: 1.2, isTextBox: true, margin: 0 }
  );

  source(s, "The attacker's best choice is interior. Past the window the dial makes the attack trivially detectable. Intervals: stratified bootstrap, 2000 resamples.");
  s.addNotes("A table reporting only the one-sided number reads this backwards and calls alpha 8 a complete evasion.");
}

// 10 -------------------------------------------------------------- transfer
{
  const s = slide("CONTENT", "The sweep and the turn");
  eyebrow(s, "Finding 2", DEFENCE);
  s.addText("One untouched layer defeats the attack", { placeholder: "title" });

  s.addText(
    "Steering layer 20 drags layer 28 along at 2.8 per alpha against 7.0 at the layer being steered, and that gap between the two rates is what the defender reads.",
    { x: M, y: 1.58, w: 7.3, h: 0.56, fontSize: 13.5, color: MUTED, lineSpacingMultiple: 1.2,
      isTextBox: true, margin: 0 }
  );

  const rows = [
    [th("alpha"), th("L20 two-sided"), th("L28 two-sided"), th("the defender's number")],
    [td("2"), td("0.604", { color: ATTACK }), td("0.993"), td("0.993", { bold: true })],
    [td("4"), td("1.000"), td("0.646", { color: ATTACK }), td("1.000", { bold: true })],
    [td("8"), td("1.000"), td("0.993"), td("1.000", { bold: true })],
  ];
  s.addTable(rows, {
    ...tableBase, x: M, y: 2.3, w: 7.3, colW: [1.2, 2.0, 2.0, 2.1], rowH: 0.46,
    objectName: "transfer-table",
  });

  card(s, { x: M, y: 4.56, w: 7.3, h: 1.44, name: "transfer-note" });
  s.addText(
    "Give the defender two probes and a two-sided threshold, and the attacker has to minimise whichever of the two is stronger. There is no setting where this attack is quiet at the attacked layer and the untouched one at the same time.",
    { x: M + 0.3, y: 4.76, w: 6.7, h: 1.08, fontSize: 12.5, color: MUTED,
      lineSpacingMultiple: 1.26, isTextBox: true, margin: 0 }
  );

  card(s, { x: M + 7.7, y: 1.58, w: 4.39, h: 4.42, fill: DARK, name: "defender-number" });
  s.addText("The attacker's best setting", {
    x: M + 8.0, y: 2.5, w: 3.8, h: 0.34, fontSize: 12.5, color: ONDARK_MUTED,
    isTextBox: true, margin: 0,
  });
  s.addText("0.993", {
    x: M + 8.0, y: 2.88, w: 3.8, h: 1.34, fontSize: 68, bold: true, color: "7FC4E0",
    fontFace: THEME.headFontFace, isTextBox: true, margin: 0,
  });
  s.addText(
    "against a defender holding two probes and reading them two-sided. The minimum over the whole grid.",
    { x: M + 8.0, y: 4.34, w: 3.8, h: 1.1, fontSize: 12.5, color: ONDARK,
      lineSpacingMultiple: 1.24, isTextBox: true, margin: 0 }
  );

  source(s, "Bootstrap CI at alpha 2, layer 28: [0.98, 1.00]. Derived from the saved steered features.");
  s.addNotes("This is the strongest claim the run supports, and it is a defence result rather than the tax we went looking for.");
}

// 11 ---------------------------------------------------------------- churn
{
  const s = slide("CONTENT", "The sweep and the turn");
  eyebrow(s, "Finding 3", DEFENCE);
  s.addText("The rate survived. The sabotage did not", { placeholder: "title" });

  s.addChart(
    pres.ChartType.bar,
    [{ name: "Overlap with the unsteered failure set", labels: ["0", "1", "2", "4", "8"], values: [1.0, 0.86, 0.67, 0.48, 0.29] }],
    {
      x: M, y: 1.62, w: 7.3, h: 4.2,
      barDir: "col", barGapWidthPct: 55,
      chartColors: [DEFENCE],
      showTitle: true, title: "Jaccard overlap of the failing problems, against alpha 0",
      titleColor: INK, titleFontSize: 13, titleFontFace: "+mn-lt",
      showValue: true, dataLabelPosition: "outEnd", dataLabelColor: INK,
      dataLabelFontSize: 11, dataLabelFontFace: "+mn-lt", dataLabelFormatCode: "0.00",
      showLegend: false,
      catAxisLabelColor: MUTED, catAxisLabelFontSize: 11, catAxisLabelFontFace: "+mn-lt",
      catAxisTitle: "alpha", showCatAxisTitle: true, catAxisTitleColor: FAINT,
      catAxisTitleFontSize: 11, catAxisTitleFontFace: "+mn-lt",
      valAxisLabelColor: MUTED, valAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt",
      valAxisMinVal: 0, valAxisMaxVal: 1, valAxisMajorUnit: 0.25,
      valGridLine: { color: "E7ECF0", size: 1 },
      catGridLine: { style: "none" },
      objectName: "churn-chart",
    }
  );

  card(s, { x: M + 7.7, y: 1.62, w: 4.39, h: 2.26, fill: TINT, name: "churn-note1" });
  s.addText(
    [
      { text: "The accuracy drop reads 0.274, 0.288, 0.342, 0.274, 0.274, which is flat enough that the attacker appears to keep everything.\n\n", options: {} },
      { text: "The problems that fail are not the same problems.", options: { color: INK, bold: true } },
    ],
    { x: M + 8.0, y: 1.84, w: 3.8, h: 1.86, fontSize: 12.5, color: MUTED,
      lineSpacingMultiple: 1.24, isTextBox: true, margin: 0 }
  );

  card(s, { x: M + 7.7, y: 4.04, w: 4.39, h: 1.78, name: "churn-note2" });
  s.addText("At alpha 8", {
    x: M + 8.0, y: 4.22, w: 3.8, h: 0.28, fontSize: 12, bold: true, color: FAINT,
    isTextBox: true, margin: 0,
  });
  s.addText(
    "Nine of the original twenty failures remain and eleven are new. The valid rate holds at 1.000 and the degenerate rate at 0.014, so the churn is not the model breaking down.",
    { x: M + 8.0, y: 4.54, w: 3.8, h: 1.16, fontSize: 12.5, color: MUTED,
      lineSpacingMultiple: 1.24, isTextBox: true, margin: 0 }
  );

  source(s, "Code that compiles and fails on a different problem looks more like a perturbation than a surviving policy.");
  s.addNotes("The sweep table reports the rate, and the rate cannot see this. A Jaccard column would have.");
}

// 12 --------------------------------------------------------------- signal
{
  const s = slide("CONTENT", "The sweep and the turn");
  eyebrow(s, "Finding 4", DEFENCE);
  s.addText("The behavioural signal is stronger than we reported", { placeholder: "title" });

  s.addChart(
    pres.ChartType.line,
    [
      { name: "last-pooled", labels: ["L12", "L16", "L20", "L24", "L28"], values: [0.571, 0.847, 0.859, 0.823, 0.819] },
      { name: "last32-pooled", labels: ["L12", "L16", "L20", "L24", "L28"], values: [0.587, 0.804, 0.714, 0.727, 0.694] },
      { name: "mean-pooled (steered)", labels: ["L12", "L16", "L20", "L24", "L28"], values: [0.571, 0.769, 0.644, 0.645, 0.602] },
      { name: "shuffled-label null, 95th pct", labels: ["L12", "L16", "L20", "L24", "L28"], values: [0.616, 0.628, 0.634, 0.647, 0.636] },
    ],
    {
      x: M, y: 1.62, w: 7.3, h: 4.2,
      chartColors: [DEFENCE, "8A9BA8", ATTACK, "C8D3DC"],
      lineSize: 3, lineSmooth: false, lineDataSymbolSize: 7,
      showTitle: true, title: "Within-prompt AUROC, out of fold, all fifteen cells",
      titleColor: INK, titleFontSize: 13, titleFontFace: "+mn-lt",
      showLegend: true, legendPos: "b", legendColor: MUTED, legendFontSize: 10.5,
      legendFontFace: "+mn-lt",
      catAxisLabelColor: MUTED, catAxisLabelFontSize: 11, catAxisLabelFontFace: "+mn-lt",
      valAxisLabelColor: MUTED, valAxisLabelFontSize: 11, valAxisLabelFontFace: "+mn-lt",
      valAxisMinVal: 0.5, valAxisMaxVal: 0.9, valAxisMajorUnit: 0.1,
      valGridLine: { color: "E7ECF0", size: 1 },
      catGridLine: { style: "none" },
      objectName: "signal-chart",
    }
  );

  card(s, { x: M + 7.7, y: 1.62, w: 4.39, h: 2.06, fill: TINT, name: "sig-note1" });
  s.addText(
    "Both classes are generated under the sandbagging instruction and labelled by whether the sabotage landed, so prompt identity carries no information and the control cannot fire. 35 sabotaged against 109 ignored.",
    { x: M + 8.0, y: 1.82, w: 3.8, h: 1.7, fontSize: 12, color: MUTED,
      lineSpacingMultiple: 1.22, isTextBox: true, margin: 0 }
  );

  card(s, { x: M + 7.7, y: 3.9, w: 4.39, h: 1.92, fill: DARK, name: "sig-note2" });
  s.addText(
    [
      { text: "0.859", options: { fontSize: 34, bold: true, color: "7FC4E0", fontFace: THEME.headFontFace } },
      { text: "  at layer 20, last-pooled\n", options: { fontSize: 13, color: ONDARK } },
      { text: "\nThat is the layer we steered, under a pooling we did not. Mean-pooled at the same layer reads 0.644, so the sweep attacked the weaker of the two directions available there.", options: { fontSize: 11.5, color: ONDARK_MUTED } },
    ],
    { x: M + 8.0, y: 4.04, w: 3.8, h: 1.72, lineSpacingMultiple: 1.16, isTextBox: true, margin: 0 }
  );

  source(s, "Five folds, out of fold. The best cell's null over 500 shuffles: mean 0.501, 95th pct 0.628, max 0.729. Earlier write-ups quoted 0.771, which was the mean-pooled column alone.");
  s.addNotes(
    "A probe can separate a landed sabotage from an ignored instruction at 0.86, which is a usable detector rather than a confound. The earlier 0.771 figure came from reading only the mean-pooled row. The across-prompt grid reads 1.000 in all fifteen cells, so it cannot choose a layer and this grid is the one to sweep."
  );
}

// 13 -------------------------------------------------------------- verdict
pres.addSection({ title: "What it means" });
{
  const s = slide("STATEMENT_DARK", "What it means");
  s.addText("DID WE GET THE OUTCOME WE WANTED", {
    x: M, y: 1.02, w: CW, h: 0.3, fontSize: 12, bold: true, charSpacing: 2.4,
    color: "E8873F", isTextBox: true, margin: 0, objectName: "eyebrow",
  });
  s.addText("No.", { placeholder: "title", fontFace: THEME.headFontFace });
  s.addText(
    "For a reason narrow enough to be worth stating precisely.",
    { x: M, y: 2.66, w: 9.0, h: 0.46, fontSize: 20, color: ONDARK, isTextBox: true, margin: 0 }
  );

  const bits = [
    ["Measuring a cost needs a mechanism", "Getting a number for what evasion costs requires that the thing being evaded is load-bearing for the behaviour, so that moving away from it drags the behaviour along."],
    ["The direction was a prompt marker", "What we attacked is a marker for which instruction was in the context. Subtracting it moved the score and left the computation alone, to within 1.6%."],
    ["So there was no cost to measure", "Nothing stood in the way of the evasion. That is a claim about this probe direction on this run, and not about evasion in general."],
  ];
  const cw2 = 3.82, gap2 = 0.3;
  bits.forEach((b, i) => {
    const x = M + i * (cw2 + gap2);
    card(s, { x, y: 3.5, w: cw2, h: 2.2, fill: "1E2A38", name: `verdict-${i}` });
    s.addText(b[0], {
      x: x + 0.26, y: 3.72, w: cw2 - 0.52, h: 0.6, fontSize: 14, bold: true, color: PAPER,
      fontFace: THEME.headFontFace, isTextBox: true, margin: 0,
    });
    s.addText(b[1], {
      x: x + 0.26, y: 4.38, w: cw2 - 0.52, h: 1.16, fontSize: 12, color: ONDARK_MUTED,
      lineSpacingMultiple: 1.24, isTextBox: true, margin: 0,
    });
  });
  s.addNotes("This run cannot test the hypothesis. What it does give us is the specific design choice that blocked it, which is worth more than a vague sense that something went wrong.");
}

// 14 ------------------------------------------------------------- working
{
  const s = slide("CONTENT", "What it means");
  eyebrow(s, "What is working", DEFENCE);
  s.addText("What holds up", { placeholder: "title" });

  const stands = [
    ["0.993", "The defender's number",
      "Two probes read two-sided, minimised over the whole grid. No setting is quiet at the attacked layer and the untouched one at once.", DEFENCE],
    ["0.859", "Behavioural signal at layer 20",
      "Within-prompt, out of fold, last-pooled, against a null whose 95th percentile is 0.628 over 500 shuffles. Mean-pooled at the same layer reads 0.644.", DEFENCE],
    ["1.000", "A failure mode worth naming",
      "Two prompts make the label, the probe reads the prompt, every layer scores 1.000, and layer selection stops working. Anyone building this will hit it.", ATTACK],
  ];
  stands.forEach((t, i) => {
    const y = 1.62 + i * 1.58;
    card(s, { x: M, y, w: 5.89, h: 1.48, name: `stands-${i}` });
    s.addText(t[0], {
      x: M + 0.28, y: y + 0.22, w: 1.4, h: 0.5, fontSize: 26, bold: true, color: t[3],
      fontFace: THEME.headFontFace, isTextBox: true, margin: 0,
    });
    s.addText(t[1], {
      x: M + 1.72, y: y + 0.2, w: 3.9, h: 0.32, fontSize: 13.5, bold: true, color: INK,
      fontFace: THEME.headFontFace, isTextBox: true, margin: 0,
    });
    s.addText(t[2], {
      x: M + 1.72, y: y + 0.56, w: 3.9, h: 0.82, fontSize: 11.5, color: MUTED,
      lineSpacingMultiple: 1.2, isTextBox: true, margin: 0,
    });
  });

  card(s, { x: M + 6.2, y: 1.62, w: 5.89, h: 4.64, name: "machinery" });
  s.addText("Machinery that held", {
    x: M + 6.5, y: 1.82, w: 5.3, h: 0.28, fontSize: 12, bold: true, color: FAINT,
    isTextBox: true, margin: 0,
  });
  const held = [
    ["Executable ground truth",
      "The official mbpp tests run in a subprocess. Whether they passed is a fact, with no second model judging it."],
    ["A flip label with a validity flag",
      "Right under one prompt, wrong under the other, same problem. The valid rate held at 1.000, which rules out steering into incoherence."],
    ["Controls written as a gate",
      "The prompt control fired at 1.000 before any steering ran. The instrument worked and we overrode it."],
    ["A probe at a layer we never steered",
      "Layer 28, fitted on the same split. It is the only reason there is a defence result to report."],
    ["Features saved per alpha",
      "The residual arithmetic, the two-sided AUROC, the Jaccard and the within-prompt grid all came off one npz, on CPU alone."],
  ];
  held.forEach((h, i) => {
    const y = 2.22 + i * 0.8;
    s.addText(h[0], {
      x: M + 6.5, y, w: 5.3, h: 0.26, fontSize: 12.5, bold: true, color: INK,
      fontFace: THEME.headFontFace, isTextBox: true, margin: 0,
    });
    s.addText(h[1], {
      x: M + 6.5, y: y + 0.26, w: 5.3, h: 0.48, fontSize: 11, color: MUTED,
      lineSpacingMultiple: 1.18, isTextBox: true, margin: 0,
    });
  });

  source(s, "Steering the prompt positions too, STEER_SCOPE set to all, did not erase the instruction: the flip rate held at 0.274 and rose to 0.342.");
  s.addNotes("The defence result and the within-prompt number are what to carry forward. Everything in the right-hand column is reusable as it stands.");
}

// 15 --------------------------------------------------------- not working
{
  const s = slide("CONTENT", "What it means");
  eyebrow(s, "What is not working");
  s.addText("Four things that broke, worst first", { placeholder: "title" });

  const broke = [
    ["The label comes from two prompts",
      "The probe reads which instruction was in the context, and answer length alone scores 0.672 across prompts. Held constant, the headline cell falls from 1.000 to 0.644.",
      "the headline, the layer choice,\nand the tax measurement itself"],
    ["The dial has no scale",
      "In units of alpha the informative window is [0.94, 3.22]. The grid 0, 1, 2, 4, 8 put two of five points inside it.",
      "two of five generation passes,\nspent where the answer was fixed"],
    ["The sweep table reports the wrong columns",
      "One-sided AUROC, so 0.000 reads as evasion. The accuracy drop alone, so churn in the failing set is invisible. No residual, no intervals.",
      "ten minutes of believing\noutcome 1, and nearly a write-up"],
    ["The gate was not honoured",
      "37 successful attacks against a minimum of 40, with 20 of them in the held-out half.",
      "every interval in the deck:\nalpha 2 is [0.43, 0.71]"],
  ];
  broke.forEach((b, i) => {
    const y = 1.62 + i * 1.14;
    card(s, { x: M, y, w: CW, h: 1.02, name: `broke-${i}` });
    badge(s, { x: M + 0.3, y: y + 0.3, label: i + 1, fill: ATTACK });
    s.addText(b[0], {
      x: M + 0.96, y: y + 0.14, w: 7.1, h: 0.32, fontSize: 14.5, bold: true, color: INK,
      fontFace: THEME.headFontFace, isTextBox: true, margin: 0,
    });
    s.addText(b[1], {
      x: M + 0.96, y: y + 0.5, w: 7.1, h: 0.44, fontSize: 11.5, color: MUTED,
      lineSpacingMultiple: 1.18, isTextBox: true, margin: 0,
    });
    s.addText("COST", {
      x: M + 8.3, y: y + 0.16, w: 3.4, h: 0.22, fontSize: 9, bold: true, charSpacing: 1.4,
      color: FAINT, isTextBox: true, margin: 0,
    });
    s.addText(b[2], {
      x: M + 8.3, y: y + 0.42, w: 3.4, h: 0.5, fontSize: 11.5, color: ATTACK,
      lineSpacingMultiple: 1.18, isTextBox: true, margin: 0,
    });
  });

  card(s, { x: M, y: 6.2, w: CW, h: 0.62, fill: DARK, name: "smaller" });
  s.addText(
    [
      { text: "Smaller:  ", options: { color: ONDARK_MUTED } },
      { text: "the probe trained on 37 attacked rows while 35 clean ones sat in the same file, and the monitor ran on the sandbagger's own weights with only its mean honest suspicion saved, so the monitor gate was never scored.", options: { color: ONDARK } },
    ],
    { x: M + 0.34, y: 6.2, w: CW - 0.68, h: 0.62, fontSize: 11, valign: "middle",
      isTextBox: true, margin: 0 }
  );
  s.addNotes("All four have a fix on the next slide. Only the first one changes what the run is able to answer.");
}

// 16 ------------------------------------------------------------- improve
{
  const s = slide("CONTENT", "What it means");
  eyebrow(s, "Where it stands now", DEFENCE);
  s.addText("Seven fixes are in. Four need a re-run", { placeholder: "title" });

  card(s, { x: M, y: 1.62, w: 5.89, h: 4.64, name: "free" });
  s.addText("Done, from the run already on disk", {
    x: M + 0.3, y: 1.82, w: 5.3, h: 0.28, fontSize: 12, bold: true, color: DEFENCE,
    isTextBox: true, margin: 0,
  });
  const free = [
    "Within-prompt AUROC is the headline, and it picks the layer and pooling: L20 last-pooled at 0.859.",
    "Two-sided AUROC and TPR at 1% FPR. Alpha 4 and 8 go back to 1.000.",
    "A residual column, realised minus predicted. It reads under 1.6% at every alpha.",
    "Flip-set Jaccard against alpha 0, which falls to 0.29.",
    "The defender's number, minimised over alpha: 0.993.",
    "A degeneracy check beyond compiling, flat at 0.014.",
    "A stratified bootstrap interval on every AUROC.",
  ];
  free.forEach((t, i) => {
    const y = 2.24 + i * 0.56;
    s.addText(String(i + 1), {
      x: M + 0.3, y, w: 0.3, h: 0.24, fontSize: 11, bold: true, color: DEFENCE,
      isTextBox: true, margin: 0,
    });
    s.addText(t, {
      x: M + 0.66, y: y - 0.02, w: 4.95, h: 0.5, fontSize: 11, color: MUTED,
      lineSpacingMultiple: 1.2, isTextBox: true, margin: 0,
    });
  });

  card(s, { x: M + 6.2, y: 1.62, w: 5.89, h: 4.64, fill: DARK, name: "rerun" });
  s.addText("Needs a re-run", {
    x: M + 6.5, y: 1.82, w: 5.3, h: 0.28, fontSize: 12, bold: true, color: ONDARK_MUTED,
    isTextBox: true, margin: 0,
  });
  const rerun = [
    ["Fix the grid first",
      "The notebook now computes the informative window from the fitted probe and asserts the grid overlaps it. It is set to 0, 1.0, 1.5, 2.0, 2.5, 3.0."],
    ["Keep the monitor's rows",
      "We saved only the mean honest suspicion, so no monitor AUROC and no interval can be recovered from this run."],
    ["Give the monitor its own weights",
      "Ours defaulted to the attacker's, which bounds visibility to a reader of equal capability rather than a trusted one."],
    ["Honour the gate",
      "800 problems at the observed 25.3% attack rate gives about 100 attacks and halves every interval in the deck."],
  ];
  rerun.forEach((r, i) => {
    const y = 2.24 + i * 0.98;
    s.addText(r[0], {
      x: M + 6.5, y, w: 5.3, h: 0.3, fontSize: 13, bold: true, color: PAPER,
      fontFace: THEME.headFontFace, isTextBox: true, margin: 0,
    });
    s.addText(r[1], {
      x: M + 6.5, y: y + 0.3, w: 5.3, h: 0.56, fontSize: 11, color: ONDARK_MUTED,
      lineSpacingMultiple: 1.2, isTextBox: true, margin: 0,
    });
  });

  source(s, "Left: src/obftax/metrics.py and scripts/reanalyze.py, both computed inline by the notebooks now. Right: the shape of the next run.");
  s.addNotes("The seven on the left changed what we conclude without costing a single generation. Both notebooks now compute them during the run rather than needing a re-read afterwards, and the attack notebook asserts the alpha grid overlaps the informative window before it spends a pass.");
}

// 17 ----------------------------------------------------------------- next
{
  const s = slide("CONTENT", "What it means");
  eyebrow(s, "Where to go next", DEFENCE);
  s.addText("Four experiments, cheapest first", { placeholder: "title" });

  const exps = [
    ["Ask whether the direction is causal at all",
      "Project it out of the residual stream during generation instead of steering along it, and measure the attack rate. One pass over the held-out half, no grid. If sabotage survives with the direction removed, there is no tax to look for here.",
      "hooks.Project · already written and tested", ATTACK],
    ["Measure the tax with best-of-n",
      "Sample sixteen completions per problem under the sandbagging prompt, then sweep a probe-score budget instead of alpha: among completions quiet enough to pass, how many still sabotage? Every point is an output the model would really produce.",
      "one pass, and both classes share one prompt", DEFENCE],
    ["Take the instruction out of the context",
      "Hand the policy over as k in-context demonstrations with no instruction anywhere, and the label becomes a property of the rollout rather than of the prompt.",
      "the only route back to the original question", DEFENCE],
    ["Replace the hand-set dial with a trained attacker",
      "One scalar on one direction is the weakest adversary available, and a defence result against it says little. A soft prefix trained on the probe score plus the model's own sandbagged completion is the affordable version; RL-Obfuscation is the comparison.",
      "hours on a 4B, not a project", INK],
  ];

  const cw3 = 5.89, ch3 = 2.16, gx = 0.31, gy = 0.26;
  exps.forEach((e, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = M + col * (cw3 + gx);
    const y = 1.62 + row * (ch3 + gy);
    card(s, { x, y, w: cw3, h: ch3, name: `exp-${i}` });
    badge(s, { x: x + 0.28, y: y + 0.26, label: i + 1, fill: e[3], d: 0.38 });
    s.addText(e[0], {
      x: x + 0.78, y: y + 0.22, w: cw3 - 1.06, h: 0.58, fontSize: 15, bold: true, color: INK,
      fontFace: THEME.headFontFace, isTextBox: true, margin: 0,
    });
    s.addText(e[1], {
      x: x + 0.28, y: y + 0.80, w: cw3 - 0.56, h: 0.98, fontSize: 12, color: MUTED,
      lineSpacingMultiple: 1.22, isTextBox: true, margin: 0,
    });
    s.addText(e[2], {
      x: x + 0.28, y: y + 1.80, w: cw3 - 0.56, h: 0.28, fontSize: 11, italic: true,
      color: e[3], isTextBox: true, margin: 0,
    });
  });

  source(s, "A change of substrate helps too: on AdvBench or HarmBench both labels come from one prompt sampled k times, so the confound goes by construction rather than by control.");
  s.addNotes("The first one is the only one that needs running before deciding anything else. It is one pass and it settles whether the rest is worth doing.");
}

// 18 ---------------------------------------------------------------- close
{
  const s = slide("STATEMENT_DARK", "What it means");
  s.addText("WHAT THE RUN STILL SUPPORTS", {
    x: M, y: 1.02, w: CW, h: 0.3, fontSize: 12, bold: true, charSpacing: 2.4,
    color: "E8873F", isTextBox: true, margin: 0, objectName: "eyebrow",
  });
  s.addText("Naive steering does not evade", {
    placeholder: "title", fontSize: 46, fontFace: THEME.headFontFace,
  });
  s.addText(
    "It overshoots into a region a two-sided threshold catches, it fails to transfer one layer, and the sabotage that survives is a different sabotage.",
    { x: M, y: 2.72, w: 10.8, h: 0.9, fontSize: 18, color: ONDARK,
      lineSpacingMultiple: 1.2, isTextBox: true, margin: 0 }
  );

  card(s, { x: M, y: 4.0, w: CW, h: 1.14, fill: "1E2A38", name: "mirror" });
  s.addText(
    [
      { text: "The mirror image of the obfuscated-activations result:  ", options: { color: ONDARK_MUTED } },
      { text: "optimised attacks evade latent monitors, and the unoptimised one does not evade at all.", options: { color: PAPER, bold: true } },
    ],
    { x: M + 0.36, y: 4.0, w: CW - 0.72, h: 1.14, fontSize: 15, valign: "middle",
      isTextBox: true, margin: 0 }
  );

  s.addShape(pres.ShapeType.rect, {
    x: M, y: 5.6, w: 1.5, h: 0.028, fill: { color: "E8873F" }, line: { color: "E8873F" },
    objectName: "close-mark",
  });
  s.addText("Corrected numbers in RESULTS.md, the narrative in ANALYSIS.md  ·  one track: mbpp, 300 problems, Qwen3.5-4B, reasoning off, greedy.", {
    x: M, y: 5.82, w: 11.6, h: 0.3, fontSize: 11, color: "7E8FA0", isTextBox: true, margin: 0,
  });
  s.addNotes("Close on what is defensible. The defence result is real and cheap to strengthen, and the tax measurement needs a different design.");
}

// ----------------------------------------------------------------- write ----
const out = path.join(__dirname, "obfuscation-tax.pptx");
pres.writeFile({ fileName: out }).then(() => {
  console.log(`wrote ${out} (${n} slides)`);
  // Without APPLY_THEME the deck still builds; scheme colours fall back to Office's
  // stock palette. Previously this threw and exited 1 after writing a good file.
  if (!process.env.APPLY_THEME) {
    console.log("APPLY_THEME unset, skipping theme colours (see README.md)");
    return null;
  }
  const { applyTheme } = require(process.env.APPLY_THEME);
  return applyTheme(out, THEME).then(() => console.log("theme applied"));
}).then(() => {}).catch((e) => {
  console.error("FAILED:", e && e.message ? e.message : e);
  process.exit(1);
});
