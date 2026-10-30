# obsfucation-tax

What does a model give up to hide from an activation probe?

## Motivation

A model can be told to fail on purpose: answer a coding question wrongly while looking
like it tried. That is sandbagging, and it matters because a model that can hide its real
ability can also hide how dangerous it is.

One way to catch it is to stop reading the model's text and read its internals instead.
While the model writes an answer it produces a vector of numbers at each layer. A simple
linear classifier on those vectors can often tell an honest attempt from deliberate
failure. That classifier is the probe, and it is the defence.

What is not known is what the fooling costs. The probe reads the same internal state the
model uses to do the task, so pushing that state around is not a free move. Three things can happen:

1. The model dodges the probe and sandbags just as well. Then the probe is close to
   useless against an attacker who knows about it.
2. The model dodges the probe and stops sandbagging — it answers correctly again, or it
   produces garbage. Then evading the probe meant giving up the attack, and the probe was
   doing real work even though it can be evaded.
3. The model dodges the probe, but the answers now look suspicious to a second model that
   only reads text. The probe did not stop the attack, it pushed the attack somewhere
   another defence can see it.

This cost is obfuscation tax.

## The experiment

1. Give a model coding problems twice: once with an honest prompt, once with a prompt
   telling it to fail quietly. An example counts as an attack only when the model got it
   right honestly and wrong when told to sandbag.
2. Train a probe on the model's internals to tell those two apart, then check it is not
   cheating. It must not be reading the wording of the answer, the sandbagging
   instruction sitting in the prompt, or simply the fact that the answer is wrong.
3. Add a second model that reads only the question and the answer and rates how fishy it
   looks. That is the text-only monitor.
4. Attack. During generation, push the model's internals away from the probe's direction,
   with a dial (`alpha`) for how hard, and turn the dial up step by step.
5. At each setting of the dial, record how well the probe still detects the attack, how
   much accuracy the attack still destroys, and how suspicious the monitor finds the
   answers.
6. Score every attacked answer with a second probe at a layer the attack never touched.
   Evasion that beats only the probe it was aimed at is much weaker than one that
   generalises.

The output is one table, one row per dial setting. If detection falls faster than the
attack does, evasion is cheap, else the gap between them is the tax.

The model is `Qwen/Qwen3.5-4B`. The probe is a logistic regression on the residual stream,
over answer tokens only.

## Results

One run so far. `mbpp`, 300 problems, reasoning off, 146 answerable, 73 held out for the
table. Steering at layer 20, transfer probe at layer 28.

| alpha | probe L20 | transfer L28 | accuracy drop | monitor | valid rate |
| --- | --- | --- | --- | --- | --- |
| 0 | 1.000 | 1.000 | 0.274 | 0.129 | 1.000 |
| 1 | 0.999 | 1.000 | 0.288 | 0.130 | 1.000 |
| 2 | 0.572 | 0.993 | 0.342 | 0.131 | 1.000 |
| 4 | 0.000 | 0.718 | 0.274 | 0.117 | 1.000 |
| 8 | 0.000 | 0.000 | 0.274 | 0.126 | 1.000 |

Honest baseline: monitor 0.066. Accuracy on the held-out set is 1.000 by construction,
since the probe is fitted on answerable problems only, so the accuracy drop here is the
flip rate on those and is not the same quantity as the drop over the whole track.

The probe score falls by exactly what the steering takes off it. The probe geometry
predicts a shift of 6.991 scaled units per alpha and the run delivers 7.02 to 7.10,
leaving a residual under 1.6% of the imposed shift. Nothing in the model's computation
responded to being pushed.

So an AUROC of 0.000 is overshoot and not evasion. Scored two-sided, on distance from the
honest median, detection returns to 1.000 at alpha 4 and 8. The one setting that hides is
alpha 2, at 0.604, and on 25 attacks its confidence interval runs [0.44, 0.71].

The untouched layer survives. At alpha 2, with the attacked probe down to 0.572, layer 28
still reads 0.993. Steering layer 20 moves layer 28 by 2.8 per alpha against 7.0 at the
layer being steered, and no setting beats both layers at once.

The accuracy drop holds between 0.27 and 0.34 across the sweep, which reads as free
evasion until you look at which problems fail. Overlap with the unsteered failure set
falls to 0.29 by alpha 8: nine of the original twenty, eleven new ones, with the valid
rate still at 1.000. The rate survives and the sabotage does not.

All of which follows from the probe reading the prompt rather than the behaviour. On the
109 problems where the sandbagging instruction was in context and the answer still came
out correct, the probe reads 1.000 held out, and those answers score +7.74 against +7.92
for real attacks. The sabotage is absent and the probe cannot tell. Subtracting a prompt
marker does not change behaviour, because it is not the behaviour. The text-only monitor picked up the sabotage
and not the steering, moving from 0.066 to about 0.13 and staying flat in alpha.

Until the sandbagging instruction leaves the context window, every number above is a fact
about prompts.

## Sandbagging Evals and Monitoring

- [`sandbagging_experiments.ipynb`](notebooks/sandbagging_experiments.ipynb)
   - Does sandbagging work, does a probe see it, and is the probe cheating? 
- [`monitor_evasion.ipynb`](notebooks/monitor_evasion.ipynb)
   - The monitor, the evasion curve, and whether evasion transfers to an untouched layer. 
- [`obfuscation_tax_refusal.ipynb`](notebooks/obfuscation_tax_refusal.ipynb)
   - The same measurement on AdvBench and HarmBench, where the label is the model's own
     behaviour rather than which prompt it was given, so the prompt control cannot be
     failed. Generates its own data; raw completions are not saved by default.

## Datasets

[`google-research-datasets/mbpp`](https://huggingface.co/datasets/google-research-datasets/mbpp) 
[`openai/openai_humaneval`](https://huggingface.co/datasets/openai/openai_humaneval) 


## References

- Goldowsky-Dill, Chughtai, Heimersheim, Hobbhahn. *Detecting Strategic Deception Using
  Linear Probes*. ICML 2025. <https://arxiv.org/abs/2502.03407>. The probe method being
  attacked, and evidence it works on non-adaptive deception.
- Bailey, Serrano, Sheshadri, et al. *Obfuscated Activations Bypass LLM Latent-Space
  Defenses*. ICLR 2026. <https://arxiv.org/abs/2412.09565>. The result that motivates the
  question: latent-space monitors can be evaded.
- Gupta, Jenner. *RL-Obfuscation: Can Language Models Learn to Evade Latent-Space
  Monitors?* 2025. <https://arxiv.org/abs/2506.14261>. The closest existing adaptive
  attacker, and the closest evidence on whether evasion preserves behaviour.
