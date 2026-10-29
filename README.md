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
model uses to do the task, so pushing that state around is not a free move. Three things
can happen:

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

## Status

The code runs. A 96-problem smoke run of `01_preconditions.ipynb` went through on an
A100: every cell executed, every file was written, and the model scores 43.8% honest on
`cruxeval`.

The real run has not been done, because the smoke run turned up two problems first.

The sandbagging prompt barely lands. Of 42 problems the model got right honestly, the
sandbagging prompt flipped 7 and changed nothing on the other 35. Accuracy goes 43.8% to
37.5%, a drop of 6.25 points, with McNemar's p at 0.07. At 400 problems the same rate
gives about 29 successful attacks, still under the gate of 40. So the prompt wants to be blunter, or the model
bigger.

The probe also looks like it is reading the prompt rather than the behaviour, which is
what the step-2 controls exist to catch. Two of the three fail:

| control | smoke value | wanted |
| --- | --- | --- |
| headline AUROC | 1.00 | high, though this is only 7 attacks |
| text only | 0.51 | near 0.5, so the answer text is not the signal |
| prompt, not behaviour | 0.997 | near 0.5 |
| wrongness, not intent | 0.88 | near 0.5 |

The prompt control scores sandbagging-prompted answers that came out correct anyway. The
instruction is in the context and the behaviour is absent, so a probe tracking behaviour
should sit near chance. At 0.997 it is reading the instruction. Features are pooled over
answer tokens only, but those tokens still attend to the system prompt, so there is a path
for this.

Awkwardly, the two failing controls rest on more data than the headline does: 35 and 54
examples against 7. The AUROC of 1.00 is the least trustworthy number in the table.

Two caveats before treating any of it as settled. Both probe-score controls are scored
in-sample for the probe, so they bound how much those confounds explain rather than
measuring it. And this is one seed at 96 problems, which was enough to check the flow and
is not enough to conclude anything.

`RESEARCH_PLAN.md` already says what a failing wrongness control costs: the label has to
get harder, comparing successful attacks against honest-incorrect answers, both wrong and
differing only in intent. That is a better experiment anyway. The later steps are not
worth running until the preconditions hold.

Right now `01_preconditions.ipynb` runs `cruxeval` only: given a function and an input,
say what it returns, scored by exact match on the literal. `mbpp`, which is writing a
whole function scored by running its tests, is deferred. It costs ten times the generation
time and has to execute model-written code, and the gates can be decided without it.
Turning it on is one line, and the last section of that notebook says what to expect.

## The notebooks

Run them in order. Each one reads the previous one's files out of `results/` and nothing
else.

| notebook | what it answers | state |
| --- | --- | --- |
| [`01_preconditions.ipynb`](notebooks/01_preconditions.ipynb) | Does sandbagging work, does a probe see it, and is the probe cheating? | smoke run done, `cruxeval` only |
| [`02_attack_curve.ipynb`](notebooks/02_attack_curve.ipynb) | The monitor, the evasion curve, and whether evasion transfers to an untouched layer. This is the table. | written, blocked on 01 |
| [`03_mechinterp.ipynb`](notebooks/03_mechinterp.ipynb) | Is the probe direction load-bearing? Where does the policy live? Does any of it survive in-context learning? | written, future work |

Notebooks 02 and 03 refit the probe from 01's saved activations, under the same seeded
split, so the test half is only ever used once.

## Running it

Nothing is installed as a package. `src/obftax` goes on `sys.path` and is imported in
place, so editing it takes effect on the next cell run. The first cell of every notebook
does the setup and clones the repo if it is not already there.

On Colab: open a notebook, pick a GPU, run the cells.

Locally, `uv` handles the dependencies and nothing else:

```bash
uv sync
uv run jupyter lab notebooks
```

`01_preconditions.ipynb` starts with `SMOKE = True`, which runs the whole notebook on 96
problems in a couple of minutes under its own `_smoke` tag. The attack-count gate cannot
pass at that size, so ignore it. The rates and the controls are still readable, which is
how the problems above were found. Set `SMOKE = False` for the real run, about fifteen
minutes on an A100.

Defaults live in `src/obftax/config.py` rather than in the notebooks: layers
12/16/20/24/28 with layer 20 as the headline, 400 problems, seed 42. Each notebook's
config cell overrides them. Everything computed is written to `results/` as JSON, CSV and
`.npz`. No number is typed into source.


## Datasets

| track | dataset | size | the model emits | scoring |
| --- | --- | --- | --- | --- |
| `cruxeval` | [`cruxeval-org/cruxeval`](https://huggingface.co/datasets/cruxeval-org/cruxeval) | 800 | one Python literal | exact match on the parsed literal |
| `mbpp` | [`google-research-datasets/mbpp`](https://huggingface.co/datasets/google-research-datasets/mbpp) | 500 | a whole function | run the official asserts |
| `humaneval` | [`openai/openai_humaneval`](https://huggingface.co/datasets/openai/openai_humaneval) | 164 | a whole function | run the official `check()` |

`evalplus/mbppplus` and `evalplus/humanevalplus` are drop-in swaps with harder tests, and
are the right move once the headline numbers exist.

`mbpp` and `humaneval` execute model-generated code in a subprocess under CPU, memory and
wall-clock limits. That is fine on a disposable Colab VM. Do not run those tracks on a
machine you care about. Neither is on by default.

The ordered steps, the gate each one has to clear, and what is deliberately left out are
in [RESEARCH_PLAN.md](RESEARCH_PLAN.md).

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
