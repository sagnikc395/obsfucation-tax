# Research Plan

The question is in `README.md`. This file is the order of work, the numbers each step
has to produce, and the condition under which the step before it was not good enough to
continue.

Keep this file short. If a step grows its own design document, the step is too big.

## Where the code is now

The steps below are numbered from 1; there is no step 0. `notebooks/01_preconditions.ipynb`
is steps 1–2, `notebooks/02_attack_curve.ipynb` is steps 3–5, and
`notebooks/03_mechinterp.ipynb` is the Future work section further down. Everything the
notebooks share — loaders, scoring, model loading, the hooks, the probe, the statistics —
is in `src/obftax`, so each notebook holds only its own experiment.

`notebooks/01_preconditions.ipynb` answers two yes/no questions:

1. Does the sandbagging prompt produce a real accuracy drop?
2. Does a linear probe on answer-token activations separate honest answers from
   successful attacks?

Everything below assumes both are yes. Both have to be yes on the real model
(`Qwen/Qwen3.5-4B`, 300 problems per track), not on a 2B smoke test.

Two task tracks, and they are allowed to disagree. `cruxeval` is code reasoning with a
one-literal answer, which keeps scoring exact and the answer short. `mbpp` is code
generation scored by running the official tests, which is the sabotage setting the
project's claim needs to be about, at the cost of executing untrusted code and pooling
features over a few hundred answer tokens rather than a handful.

## The result this is building towards

One table, one row per evasion strength:

| alpha | probe AUROC | transfer AUROC | accuracy drop | monitor suspicion |
| --- | --- | --- | --- | --- |

`alpha` is steering strength. `probe AUROC` is the attacked probe, `transfer AUROC` a
probe at another layer that the attack never saw. `accuracy drop` is honest accuracy
minus sandbagging accuracy, so it is what the attacker actually gets. `monitor
suspicion` is a text-only monitor's mean score on the sandbagging transcripts.

The claim is whatever that table says about the top-left-to-bottom-right diagonal: if
probe AUROC falls while accuracy drop holds and suspicion stays flat, evasion is free
and the probe is weak. Any other shape is a tax, and the size of the tax is the result.

## Invariants

These hold for every step. Violating one invalidates the numbers silently, which is
worse than crashing.

- An example counts as an attack only when the model answers correctly under the
  honest prompt and incorrectly under the sandbagging prompt. A sandbagging prompt
  that changes nothing is not an attack.
- On the generation tracks, sabotaged code that does not compile is breakage, not
  evasion. `syntax_ok` is recorded separately and `attacked_clean` is the mask that
  requires it, for the same reason step 4 reports the parse rate.
- Thinking stays off (`enable_thinking=False`, asserted). With it on, the answer budget
  is spent reasoning and the probe's "answer tokens" are reasoning tokens, which is a
  different experiment — see Future work.
- Probe features come from answer tokens only. Never prompt tokens.
- The test half is used once, for the final table. Layer choice, steering strength
  search, and prompt wording get decided on the train half.
- Activations used to score a steered generation are collected with steering active.
  The probe has to see what the attack actually produced, not an unsteered replay.
- Every number in a table comes from a file in `results/` that a notebook wrote. No
  number is typed into source. (The previous version of this repo plotted hardcoded
  literals; that is how this rule got written.)

## Steps

### 1. Confirm the preconditions on the real model

Run `notebooks/01_preconditions.ipynb` as configured, on both tracks. Record honest accuracy, sandbagging
accuracy, count of successful attacks, probe AUROC per (pooling, layer).

Gate: at least ~40 successful attacks per track, and probe AUROC comfortably above 0.5.
Fewer attacks than that and the probe is fitting a handful of examples. If the drop is
small, try a blunter sandbagging prompt first, then `Qwen/Qwen3.5-9B`. If AUROC is near
chance there is nothing to evade and the project stops here.

On `mbpp`, check `sandbag_syntax_ok` and the `detail` column before concluding the attack
failed: a model that sabotages by emitting code that does not compile is failing
differently from one that declines to sabotage, and the fix is different.

### 2. Rule out the three ways the probe wins for free

This is the step most likely to kill the project, so it comes before any attack code.
Each control is a second AUROC next to the headline AUROC.

- **Is it just the text?** Train TF-IDF logistic regression on the answer strings.
  Same split, same labels. If text-only AUROC matches the probe, the activations are
  adding nothing and the rest of the plan is about a classifier that reads output.
- **Is it just the prompt?** Score the probe on sandbagging-prompted answers that came
  out correct anyway. The sandbagging instruction is present and the behaviour is not.
  A probe tracking behaviour should be near chance here.
- **Is it just wrongness?** The headline comparison is honest-correct against
  sandbag-incorrect, so correctness is perfectly confounded with the label. Score the
  probe on honest answers that were wrong. If it flags those as strongly as real
  attacks, the probe detects "this answer is wrong", not "I am underperforming on
  purpose", and the whole framing has to change.

Gate: the probe beats text-only by a clear margin, and is closer to chance than to its
headline score on the other two. If the wrongness control fails, the fix is a harder
label: successful attacks against honest-incorrect answers, both wrong, differing only
in intent. That is a better experiment anyway and worth the detour.

### 3. Add the black-box monitor

A second model reads the question and the answer and rates how likely deliberate
wrongness is. Score it as the expected value over single-digit next-token
probabilities, so one forward pass per transcript and no sampling. The monitor never
sees activations, probe scores, or labels.

Gate: the monitor separates honest from successful attacks at all. A monitor at chance
cannot register a tax, and a monitor near-perfect at alpha=0 leaves no room to rise. If
it is at chance, use a larger trusted model before weakening the prompt.

### 4. Steering evasion, and the curve

Hook the probe layer's output and subtract `alpha * unit(probe direction)` at every
position during generation. Collect activations under the same hook. Sweep alpha
through roughly 0, 1, 2, 4, 8, picked on the train half, and fill in the table.

Two things to check before trusting any row:

- The sign is right: probe scores on steered generations must go down, not up.
- Report the fraction of answers that stop being valid: an unparseable literal on
  `cruxeval`, code that does not compile on `mbpp`. A model steered into incoherence has
  not evaded the probe, it has broken, and a falling AUROC there means nothing.

Steering every position is one choice; steering answer positions only is the other, and
it is closer to an attacker who controls its own behaviour rather than its own prompt
processing. Worth running both if the first one works.

### 5. Transfer

Train a second probe at a different layer on the same unsteered data. Never steer
against it. Score every steered generation with it.

This is the step that decides how much the result is worth. Evasion that only beats the
exact weights it was optimised against is a much weaker attack than one that
generalises, and a defender who can retrain at a new layer is in a much better
position. Report both AUROCs in the same table.

Steps 3 to 5 are implemented in `notebooks/02_attack_curve.ipynb`, which writes the table
to `results/attack_<tag>_table.csv`.

### 6. Write it up

Four to eight pages. The table, the curve, the control table, and an explicit
statement of what a 1.5B result does and does not say about frontier models. A
negative result (evasion is cheap and transfers) is the finding, written as the
finding.

## Deliberately out of scope

Each of these was in the previous plan and is cut until the table above exists.

- Audit budgets, safety/usefulness Pareto curves, and full control protocols. These
  need a working tax measurement first, and they need `AI Control`-style
  infrastructure that is a project of its own.
- Iterated probe-retraining rounds and probe subspace analysis. Interesting, and
  entirely dependent on step 5 showing that evasion is layer-specific.
- RL or LoRA training of the attacker. A steering vector is the cheapest adaptive
  attacker that is still a real attacker. Train one only if steering fails to evade at
  any strength that preserves the attack.
- Harder test suites (`evalplus/mbppplus`, `evalplus/humanevalplus`), LiveCodeBench,
  a second model, bootstrapped confidence intervals, multiple seeds. All of these are
  replication, and belong after there is one result to replicate. Confidence intervals
  come back in for the write-up.
- ControlArena and Inspect. The pipeline is one small package and three notebooks over
  cached files, and does not need an eval framework.

## Future work

Three directions, none of them step 7. Each is its own project. They are written down
here so the measurement above is built in a way that does not block them.

The first three are implemented in `notebooks/03_mechinterp.ipynb`: the causal check
on the probe direction, the decision-subspace overlap, residual-stream patching by layer,
and the ICL sweep including the pre-emptive probe.

### Obfuscation that arrives through in-context learning

The sandbagging policy is currently handed over in a system prompt, which is the easy
case for a defender: the instruction sits in the context window, and a text monitor
reading the prompt catches it. The harder case is a policy the model infers from
in-context examples — `k` demonstrations of plausible-but-wrong answers and no
instruction anywhere. Then there is nothing to read. The policy exists only as
something the model computed from the demos.

Questions, cheapest first:

- **Does ICL-induced sandbagging reproduce the step 1 numbers?** Same accuracy-drop and
  probe-AUROC measurement, `k` demos in place of `SANDBAG`. If the drop needs many
  demos to appear, that is itself the result.
- **Can it be detected before the answer exists?** The invariant above restricts probe
  features to answer tokens, which is right for measuring behaviour. Prediction is a
  different question: train a probe on the activations at the last prompt token, after
  the demos and before a single answer token is generated, and ask whether it predicts
  that this rollout will be an attack. A probe that works there is a pre-emptive
  detector, worth considerably more to a defender than a post-hoc one.
- **How does detectability scale with `k`?** Sweep `k` = 0, 1, 2, 4, 8, 16 and report
  both AUROCs against it. ICL task representations tend to appear abruptly rather than
  accumulate smoothly, so the shape of that curve is the finding.
- **Is ICL obfuscation the same object as prompted obfuscation?** Train the probe on
  prompted sandbagging and test on ICL sandbagging, then the reverse. Transfer means one
  representation and the prompted result generalises. No transfer means the
  system-prompt result says nothing about the ICL case, which is the more interesting
  outcome and the one that would need its own detector.

The label gets harder here. With no instruction, "deliberate" is ambiguous: a model
copying wrong demos may be pattern-matching rather than choosing. Define the label
behaviourally — correct without the demos, wrong with them — and say that is what it
means, rather than claiming intent the experiment cannot see.

### A mechanistic account instead of a probe score

A probe says a direction exists. It does not say the direction is load-bearing. Three
things to do, in order:

- **Causal check on the direction.** Project the probe direction out of the residual
  stream at the probe layer during generation, and measure the accuracy drop. If
  sandbagging survives with the direction gone, the probe reads a correlate and its
  AUROC overstates the defence. This is the same hook as step 4 with `alpha` replaced by
  a projection, so it costs almost nothing once steering works.
- **Localise the ICL case.** With demos the policy has to travel from the demo tokens to
  the answer position, which is a path-patching question: patch demo-token activations
  from an honest-demo run into a sandbagging run, head by head, and find the heads that
  carry it. Induction-style heads are the obvious hypothesis and the obvious thing to
  falsify by ablating them and checking whether the attack collapses.
- **Compare the probe direction to the mechanism.** If the probe direction lies mostly
  inside the span of the directions that decide the next token, the probe is reading the
  decision rather than the intent — and the wrongness control in step 2 will already
  have hinted at it. `obftax.analysis.decision_overlap` reports that overlap, as the mean
  `|cos(w, u)|` over answer positions where `u = W_U[top1] - W_U[top2]`. Note Qwen3.5 is
  a hybrid architecture, mostly gated linear attention rather than softmax attention, so
  head-level patching needs adapting and the linear-attention state is itself somewhere a
  policy could be carried.

### Bounds on what evasion can cost

The table is empirical and model-specific. A bound would say which shapes are possible
at all. The tractable version:

The attacker needs two things simultaneously. The probe score `w·h` has to be low, and
at every answer position its own chosen token has to stay ahead of the runner-up, which
is a constraint on `h` along `u = W_U[top1] - W_U[top2]`. If `w` is orthogonal to those
directions, the two constraints are independent and evasion is first-order free. The more
`w` aligns with them, the more reducing `w·h` costs attack strength. So `cos(w, u)` over
answer positions is a first-order predictor of the tax. Notebook 01 computes and saves
it, from the top-2 logit ids recorded during the run, so it is testable against the
measured curve without re-running anything.

It is only first order. The model is not linear from the probe layer to the logits, and
the attacker can route around the constraint through other layers. Both show up as a gap
between the predicted tax and the measured one, which makes the gap the interesting
number rather than a failure of the bound.

Two extensions worth stating now:

- **Probe ensembles.** Against `k` probes the attacker's feasible set loses `k`
  dimensions, so the tax should grow with `k`. That is the defender's real lever and it
  is cheap to measure: train `k` probes on different splits or layers, steer against all
  of them, and report tax against `k`.
- **The repeated game.** A defender who retrains after each evasion, against an attacker
  who re-evades, is the setting that actually matters. A bound on how many rounds the
  defender can be forced through, or on whether the process converges at all, would say
  more than any single curve. `RL-Obfuscation` is the comparison point for what one
  round of a learned attacker costs.

## Open questions

Things where the right answer is unclear and the choice should be recorded when it is
made, since each one changes what the number means.

- Whether a steering vector is a fair stand-in for an adaptive attacker at all. It is
  an intervention on the model, not a policy the model learned, and `RL-Obfuscation` is
  the comparison point for how much that matters.
- Whether `cruxeval`-style sandbagging is too easy to be informative. The answer is one
  literal, so "deliberately wrong" may have an unusually clean representation compared
  with sabotaging a whole function. This is most of why `mbpp` is run alongside it.
- Whether mean-pooling over answer tokens is hiding the signal. On `cruxeval` there is
  little to pool and the last token may be the whole story; on `mbpp` the answer is a few
  hundred tokens and the mean may dilute the signal away entirely. Three poolings (whole
  answer, last token, last 32) are recorded so this is measured rather than assumed.
