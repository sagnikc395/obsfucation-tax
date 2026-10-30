# Corrected results: the mbpp run, re-scored

Every number here comes out of `results/` with no GPU and no new generation. Regenerate
all of it with

```
python scripts/reanalyze.py --tag qwen35_4b_thinking_off --track mbpp
```

which writes `results/reanalysis_qwen35_4b_thinking_off_mbpp.json`. The metrics live in
`src/obftax/metrics.py` and are now computed inline by both notebooks, so the next run
reports them rather than needing a re-read.

`ANALYSIS.md` narrates how the run went wrong. This file is what it measured once scored
properly. Two of the numbers below are new rather than corrected.

Cohort: `mbpp`, 300 problems, `Qwen/Qwen3.5-4B`, reasoning off. 146 answerable, 37
successful attacks (35 of them compiling), 109 where the sandbagging instruction was in
context and the answer came out correct anyway.

---

## 1. The headline 1.000 was the prompt, and length was part of it

The probe's two classes came from two different system prompts, so "which instruction is
in my context" was available as a feature. Holding the prompt constant removes it.

| probe | AUROC | what the two classes are |
| --- | --- | --- |
| across prompts, L20 mean-pooled | **1.000** | honest-correct vs sabotaged, different prompts |
| within prompt, L20 mean-pooled | **0.644** | both under the sandbagging prompt, labelled by whether the sabotage landed |

Both out-of-fold over five folds. The within-prompt figure sits on a label-shuffled null
whose 95th percentile is 0.634, so at the layer and pooling actually attacked, almost
nothing survives the control.

Answer length alone, no activations involved:

| contrast | AUROC from length alone |
| --- | --- |
| honest-correct vs attack (across prompts) | 0.672 |
| ignored vs attack (within prompt) | 0.516 |

Mean answer tokens: honest-correct 43.8, sabotaged 59.1, ignored 57.1. Mean pooling sees
length, and across prompts length alone recovers much of the 0.774 text-only control. The
within-prompt design removes that cue too, at 0.516.

## 2. There is real behavioural signal, and it is stronger than we reported

`ANALYSIS.md` quotes 0.771 at layer 16 as the honest version of the headline. That is the
mean-pooled column only. Across all fifteen cells the signal is substantially higher, and
it peaks at the layer that was attacked:

| pool | L12 | L16 | L20 | L24 | L28 |
| --- | --- | --- | --- | --- | --- |
| mean | 0.571 | 0.769 | 0.644 | 0.645 | 0.602 |
| last | 0.571 | 0.847 | **0.859** | 0.823 | 0.819 |
| last32 | 0.587 | 0.804 | 0.714 | 0.727 | 0.694 |

Out-of-fold, 35 sabotaged against 109 ignored, same prompt on both sides. The best cell is
L20 last-pooled at **0.859**; over 500 label shuffles that cell's null has mean 0.501, 95th
percentile 0.628 and maximum 0.729.

So a probe can tell a landed sabotage from an ignored instruction at 0.86, which is a
usable detector rather than a confound. The run attacked the same layer under mean pooling,
where the within-prompt number is 0.644 — the weaker of the two directions available at
that layer. `monitor_evasion.ipynb` now defaults to `POOL = "last"` for this reason.

This grid is also the only one that can choose a layer. The across-prompt grid reads 1.000
in all fifteen cells, so sweeping it returns 1.000 whatever you pick.

## 3. The sweep measured a subtraction

A logistic regression is affine in its input, so subtracting `alpha * unit(w)` from every
answer position moves every example's decision score by `alpha * ||coef / scale||`. For
this probe that constant is **6.9907** scaled units per alpha.

| alpha | realised shift per alpha | predicted | residual | as % of imposed |
| --- | --- | --- | --- | --- |
| 1 | 7.019 | 6.991 | +0.028 | 0.4% |
| 2 | 7.100 | 6.991 | +0.218 | 1.6% |
| 4 | 7.047 | 6.991 | +0.225 | 0.8% |
| 8 | 7.080 | 6.991 | +0.717 | 1.3% |

The residual is the only part of a steered probe score that reflects the model responding
rather than being displaced, and it never exceeds 1.6%. The entire detection column was
therefore computable before any generation ran:

| alpha | predicted, from unsteered scores | measured | error |
| --- | --- | --- | --- |
| 0 | 1.000 | 1.000 | 0.000 |
| 1 | 0.999 | 0.999 | 0.000 |
| 2 | 0.651 | 0.572 | 0.079 |
| 4 | 0.000 | 0.000 | 0.000 |
| 8 | 0.000 | 0.000 | 0.000 |

The same arithmetic bounds where a sweep point can learn anything. AUROC leaves 1.0 at
alpha 0.94, crosses 0.5 at 2.16, and is pinned at 0.0 from 3.22. The grid `[0, 1, 2, 4, 8]`
put **two of five points inside that window**; alpha 4 and 8 were determined before the
first token. `monitor_evasion.ipynb` now asserts the overlap before the sweep runs.

## 4. A one-sided 0.000 is overshoot, not evasion

Below 0.5 the classes are still perfectly separable with the sign reversed. A defender who
thresholds on distance from the honest median gets all of it back.

| alpha | n | L20 one-sided | L20 two-sided | L20 TPR @ 1% FPR | L28 one-sided | L28 two-sided |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 20 | 1.000 | 1.000 | 1.00 | 1.000 | 1.000 |
| 1 | 21 | 0.999 | 0.999 | 1.00 | 1.000 | 1.000 |
| 2 | 25 | 0.572 [0.43, 0.71] | 0.604 [0.48, 0.74] | 0.08 | 0.993 | 0.993 [0.98, 1.00] |
| 4 | 20 | 0.000 | **1.000** | 1.00 | 0.718 | 0.646 [0.51, 0.78] |
| 8 | 20 | 0.000 | **1.000** | 1.00 | 0.000 | 0.993 [0.98, 1.00] |

Intervals are stratified bootstrap, 2000 resamples. The only setting that hides anything is
alpha 2, and on 25 attacks its interval spans clear detection and chance. Turning the dial
up converts a hard-to-detect attack into a trivially detectable one, so the attacker's best
choice is interior and the strongest setting is its worst. A table with only the one-sided
column reads this backwards and calls alpha 8 a complete evasion.

## 5. The defender's number is 0.993

Give the defender both probes and a two-sided threshold. The defender reads whichever layer
is stronger, so the attacker has to minimise the maximum.

| alpha | L20 two-sided | L28 two-sided | defender reads | which layer |
| --- | --- | --- | --- | --- |
| 1 | 0.999 | 1.000 | 1.000 | L28 |
| 2 | 0.604 | 0.993 | **0.993** | L28 |
| 4 | 1.000 | 0.646 | 1.000 | L20 |
| 8 | 1.000 | 0.993 | 1.000 | L20 |

No setting is quiet at the attacked layer and the untouched one at the same time. This is
the strongest claim the run supports, and it is the mirror image of the obfuscated-
activations result: optimised attacks evade latent monitors, and this unoptimised one does
not evade at all.

## 6. The flip rate survived; the sabotage did not

The accuracy drop holds between 0.274 and 0.342 across the sweep, which reads as free
evasion until you ask which problems are failing.

| alpha | flips | shared with alpha 0 | new | lost | Jaccard | degenerate |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 20 | 20 | 0 | 0 | 1.00 | 0.014 |
| 1 | 21 | 19 | 2 | 1 | 0.86 | 0.014 |
| 2 | 25 | 18 | 7 | 2 | 0.67 | 0.014 |
| 4 | 20 | 13 | 7 | 7 | 0.48 | 0.014 |
| 8 | 20 | 9 | 11 | 11 | 0.29 | 0.014 |

At alpha 8 nine of the original twenty failures remain and eleven are new. Code that
compiles and fails on a different problem looks like a perturbation costing a similar
amount of accuracy, not like a deliberate policy surviving intact. The degenerate rate is
flat at 0.014, so this is not the model breaking — the old `valid_rate` column only asked
whether the answer compiled, which a repetitive answer can still do.

---

## What changed in the code

| file | change |
| --- | --- |
| `src/obftax/metrics.py` | new. Bootstrap intervals, two-sided AUROC, TPR at fixed FPR, the arithmetic shift and residual, the informative window, flip-set overlap, the defender's number, the within-prompt grid with shuffled nulls, length-as-a-cue, degeneracy rate. |
| `scripts/reanalyze.py` | new. Regenerates everything above from `results/` on CPU. |
| `notebooks/sandbagging_experiments.ipynb` | new section 11b: the within-prompt grid with nulls, and answer length as a cue. Writes both into the summary, and adds a `within_prompt_above_null` gate. It prints the layer and pooling to steer, because the across-prompt grid cannot choose one. |
| `notebooks/monitor_evasion.ipynb` | new section 4b: the per-alpha shift constant, the predicted detection column, and a hard assert that the alpha grid overlaps the informative window. Section 9's table gains intervals, two-sided AUROCs, TPR at 1% FPR, the residual, the degeneracy rate, the defender's number and the flip-set Jaccard. Config now steers `POOL = "last"` over `ALPHAS = [0, 1, 1.5, 2, 2.5, 3]`. |

Two things are deliberately not recomputed under `attacked_clean`. The steered features on
disk were captured against the by-problem split that `attacked` induces, so refitting on
the clean mask moves the split and some of the 73 steered problems would land in the
probe's training half. The clean mask is used for the unsteered and within-prompt numbers,
where it costs nothing, and the sweep stays on the mask it was run under. Fixing that
needs the sweep re-run, not a re-read.

## What this does not fix

The run still has 37 attacks against a gate of 40, and 20 in the held-out half, which is
why the one interval anybody will want to quote is [0.43, 0.71]. The monitor still shares
weights with the sandbagger, and only its mean honest suspicion was saved, so no monitor
AUROC can be recovered. Reasoning was off. None of that is reachable without new
generation; `ANALYSIS.md` lists the four re-runs and the next experiments.
