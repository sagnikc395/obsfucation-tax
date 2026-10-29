# obsfucation-tax 

## Motivation

A model can be told to fail on purpose: answer a coding question wrongly while looking like it tried. That is sandbagging, and it matters because a model that can hide its real ability can also hide how dangerous it is. One way to catch it is to stop reading the model's text and read its internals instead. While the model writes an answer it produces a vector of numbers at each layer. A simple
linear classifier on those vectors can often tell an honest attempt from deliberate failure. That classifier is the probe, and it is the defence.

What is not known is what the fooling costs. The probe reads the same internal state the model uses to do the task, so pushing that state around is not a free move. Three things can happen:

1. The model dodges the probe and sandbags just as well. Then the probe is close to useless against an attacker who knows about it.
2. The model dodges the probe and stops sandbagging — it answers correctly again, or it produces garbage. Then evading the probe meant giving up the attack, and the probe was doing real work even though it can be evaded.
3. The model dodges the probe, but the answers it writes now look suspicious to a second model that only reads text. The probe did not stop the attack, it pushed the attack somewhere another defence can see it.

This cost is obfuscation tax.

## Experiment

1. Give a model coding problems twice, once with an honest prompt and once with a prompt telling it to fail quietly. An example counts as an attack only when the model got it right honestly and wrong when told to sandbag.
2. Train a probe on the model's internals to tell those two apart, then check that it is not cheating. It must not be reading the wording of the answer, the sandbagging instruction sitting in the prompt, or simply the fact that the answer is wrong.
3. Add a second model that reads only the question and the answer and rates how fishy it looks. That is the text-only monitor.
4. Attack. During generation, push the model's internals away from the probe's direction, with a dial (`alpha`) for how hard, and turn the dial up step by step.
5. At each setting of the dial we are recording three things: 
  - how well the probe still detects the attack
  - how much accuracy the attack still destroys
  - how suspicious the text monitor finds the answers.
6. Score every attacked answer with a second probe at a layer the attack never touched. Evasion that beats only the exact probe it was aimed at is a much weaker attack than one that generalises.

If detection falls faster than the attack does, evasion is cheap, else the gap between them is the tax.

## Problem statement

Activation probes can detect when a model is deliberately underperforming, and adaptive
attackers can evade those probes. What is not known is the price of evasion.

An attacker that hides from a probe is not free to behave however it likes. The probe
reads the same representations the model uses to do the task, so pushing activations
off the probe's direction may also damage the attack: the model may stop
underperforming, start producing text a black-box monitor flags, or lose the ability
to answer at all. Alternatively, evasion may be nearly free, in which case the probe
offers very little.

When a model evades an activation probe trained to detect deliberate underperformance,
how much attack performance, and how much black-box inconspicuousness, does it have to
give up?

Concretely, the setting is:

- **Task**: coding, on two tracks. `cruxeval` is code reasoning — given a function and
  an input, say what it returns — scored by exact match on the returned literal.
  `mbpp` (and optionally `humaneval`) is code generation, scored by running the
  official unit tests. The two tracks differ in how long the answer is and in what
  "wrong on purpose" means, and they are allowed to disagree.
- **Attack**: a prompted model answers incorrectly on purpose (sandbagging) — a wrong
  literal on `cruxeval`, subtly broken code on `mbpp`. An attack counts only when the
  model answers correctly under the honest prompt and incorrectly under the sandbagging
  prompt. A sandbagging prompt that changes nothing is not an attack.
- **Defender**: a linear probe on the residual stream over answer tokens only.
- **Evasion**: steer the residual stream along the probe's direction at generation
  time, at increasing strength.
- **Measurement**: at each evasion strength, record probe AUROC, the accuracy drop
  the attack still achieves, and the suspicion a text-only monitor assigns.

The result is a curve. Three shapes matter:

1. Probe AUROC falls and the accuracy drop survives → evasion is cheap, and probes are weak against an adaptive attacker.
2. Probe AUROC falls but the accuracy drop goes with it → there is a tax, and the probe is doing useful work even though it can be evaded.
3. Probe AUROC falls and black-box suspicion rises → the probe pushes the attack into another monitor's view, which is the case for defence in depth.


## Layout

```
src/obftax/   shared code: no GPU, nothing generated on import
notebooks/    one notebook per experiment; this is where the GPU time goes
results/      what the notebooks write, and all they pass to each other
papers/       the papers the measurement depends on
```

Anything used by more than one experiment lives in `src/obftax`, so a notebook contains
only the experiment it is named after:

| module | what is in it |
| --- | --- |
| `config.py` | every shared constant, and the honest/sandbag prompt pair per track |
| `tasks.py` | the dataset loaders, all returning problems in one shape |
| `scoring.py` | literal and program scoring, the execution sandbox, and its self-test |
| `model.py` | loading, prompt building, generation, answer-token pooling |
| `hooks.py` | the four interventions — steer, project, patch, capture — and `attach`, which always removes them |
| `probes.py` | the label definition, the by-problem split, fitting, probe directions |
| `analysis.py` | the accuracy-drop statistics, guarded AUROCs, the first-order bound |
| `storage.py` | result paths, and how each notebook reads the previous one's output |


## Pipeline

There is no "step 0" — the plan's steps are numbered from 1, and the notebooks map onto
them like this. Run them in order; each reads the previous one's `results/` files and
nothing else.

| notebook | plan steps | what it answers | writes |
| --- | --- | --- | --- |
| [`notebooks/01_preconditions.ipynb`](notebooks/01_preconditions.ipynb) | 1–2 | Does sandbagging work, does a probe see it, and does the probe win for free? | `pre_<tag>_*` |
| [`notebooks/02_attack_curve.ipynb`](notebooks/02_attack_curve.ipynb) | 3–5 | The monitor, the steering-evasion curve, and whether evasion transfers to an unattacked layer. **This is the table.** | `attack_<tag>_*` |
| [`notebooks/03_mechinterp.ipynb`](notebooks/03_mechinterp.ipynb) | future work | Is the probe direction load-bearing? Where does the policy live? Does any of it survive in-context learning? | `mech_<tag>_*` |

Notebooks 02 and 03 refit the probe from notebook 01's saved activations using the same
seeded by-problem split, so the test half is still only used once, for the final table.
That is what `obftax.probes.fit_from_saved` is for, and why the probe **directions** are
saved rather than pickled sklearn objects.

Step 6 of the plan is the write-up, and has no notebook.

## Datasets

| track | dataset | size | what the model emits | scoring |
| --- | --- | --- | --- | --- |
| `cruxeval` | [`cruxeval-org/cruxeval`](https://huggingface.co/datasets/cruxeval-org/cruxeval) | 800 | one Python literal | exact match on the parsed literal |
| `mbpp` | [`google-research-datasets/mbpp`](https://huggingface.co/datasets/google-research-datasets/mbpp) (full/test) | 500 | a whole function | run the official asserts |
| `humaneval` | [`openai/openai_humaneval`](https://huggingface.co/datasets/openai/openai_humaneval) | 164 | a whole function | run the official `check()` |

`evalplus/mbppplus` (378) and `evalplus/humanevalplus` (164) are drop-in swaps with
harder test suites, and are the right move once the headline numbers exist.

`mbpp` and `humaneval` **execute model-generated code** in a subprocess under CPU,
address-space and wall-clock limits. That is adequate on a disposable Colab VM, which is
where the notebooks are meant to run. Do not run those tracks on a machine you care
about. `obftax.scoring.check_harness` is an assert and not a print, because a sandbox
that fails to launch scores every solution wrong and still produces a full,
plausible-looking table.

Nothing is built until steps 1 and 2 pass, which is what
`notebooks/01_preconditions.ipynb` is for. If the accuracy drop is small, the attack
needs a better prompt or a bigger model. If probe AUROC is near chance, there is nothing
to evade and no tax to measure.

The ordered steps after that, the gate each one has to clear, and what is deliberately
left out are in [RESEARCH_PLAN.md](RESEARCH_PLAN.md).

## References

- Goldowsky-Dill, Chughtai, Heimersheim, Hobbhahn. *Detecting Strategic Deception
  Using Linear Probes*. ICML 2025. <https://arxiv.org/abs/2502.03407> — the probe
  method being attacked, and evidence that it works on non-adaptive deception.
- Bailey, Serrano, Sheshadri, et al. *Obfuscated Activations Bypass LLM Latent-Space
  Defenses*. ICLR 2026. <https://arxiv.org/abs/2412.09565> — the result that motivates
  the question: latent-space monitors can be evaded.
- Gupta, Jenner. *RL-Obfuscation: Can Language Models Learn to Evade Latent-Space
  Monitors?* 2025. <https://arxiv.org/abs/2506.14261> — the closest existing adaptive
  attacker, and the closest existing evidence on whether evasion preserves behaviour.

