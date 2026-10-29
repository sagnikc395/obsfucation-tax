# Research Plan

The question is in `README.md`. This file is the order of work, the numbers each step
has to produce, and the condition under which the step before it was not good enough to
continue.

Keep this file short. If a step grows its own design document, the step is too big.

## Where the code is now

`obftax.py` answers two yes/no questions:

1. Does the sandbagging prompt produce a real accuracy drop?
2. Does a linear probe on answer-token activations separate honest answers from
   successful attacks?

Everything below assumes both are yes. Both have to be yes on the real model
(`Qwen2.5-1.5B-Instruct`, 200 questions), not on the 0.5B smoke test.

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
- Probe features come from answer tokens only. Never prompt tokens.
- The test half is used once, for the final table. Layer choice, steering strength
  search, and prompt wording get decided on the train half.
- Activations used to score a steered generation are collected with steering active.
  The probe has to see what the attack actually produced, not an unsteered replay.
- Every number in a table comes from a file in `results/` that a script wrote. No
  number is typed into source. (The previous version of this repo plotted hardcoded
  literals; that is how this rule got written.)

## Steps

### 1. Confirm the preconditions on the real model

Run `obftax.py` as configured. Record honest accuracy, sandbagging accuracy, count of
successful attacks, probe AUROC.

Gate: at least ~40 successful attacks out of 200 questions, and probe AUROC
comfortably above 0.5. Fewer attacks than that and the probe is fitting a handful of
examples. If the drop is small, try a blunter sandbagging prompt first, then a bigger
model. If AUROC is near chance there is nothing to evade and the project stops here.

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
- Report the fraction of answers that stop parsing as a letter. A model steered into
  incoherence has not evaded the probe, it has broken, and a falling AUROC there means
  nothing.

Steering every position is a choice, not the only one. Answer positions only is the
alternative, and is closer to an attacker who controls its own behaviour rather than
its own prompt processing. Worth running both if the first one works.

### 5. Transfer

Train a second probe at a different layer on the same unsteered data. Never steer
against it. Score every steered generation with it.

This is the step that decides how much the result is worth. Evasion that only beats the
exact weights it was optimised against is a much weaker attack than one that
generalises, and a defender who can retrain at a new layer is in a much better
position. Report both AUROCs in the same table.

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
- Second dataset (GSM8K), second model, bootstrapped confidence intervals, multiple
  seeds. All of these are replication, and belong after there is one result to
  replicate. Confidence intervals come back in for the write-up.
- ControlArena and Inspect. The pipeline is four scripts over cached files and does not
  need an eval framework.

## Open questions

Things where the right answer is unclear and the choice should be recorded when it is
made, since each one changes what the number means.

- Whether a steering vector is a fair stand-in for an adaptive attacker at all. It is
  an intervention on the model, not a policy the model learned, and `RL-Obfuscation` is
  the comparison point for how much that matters.
- Whether prompted sandbagging on multiple choice is too easy to be informative. There
  are only four tokens to choose between, so "deliberately wrong" may have an unusually
  clean representation.
- Whether mean-pooling over answer tokens is hiding the signal. With 8-token answers
  there is not much to pool, and the last token may be the whole story.
