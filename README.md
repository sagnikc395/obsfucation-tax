# Obfuscation Tax

## Problem statement

Activation probes can detect when a model is deliberately underperforming, and
adaptive attackers can evade those probes. Both halves are established. What is not
established is the **price of evasion**.

An attacker that hides from a probe is not free to behave however it likes. The probe
reads the same representations the model uses to do the task, so pushing activations
off the probe's direction may also damage the attack: the model may stop
underperforming, start producing text a black-box monitor flags, or lose the ability
to answer at all. Alternatively, evasion may be nearly free, in which case the probe
offers very little.

This repository measures that cost. The question is:

> When a model evades an activation probe trained to detect deliberate
> underperformance, how much attack performance, and how much black-box
> inconspicuousness, does it have to give up?

Concretely, the setting is:

- **Task**: MMLU multiple choice, scored by exact letter match.
- **Attack**: a prompted model answers incorrectly on purpose (sandbagging). An
  attack counts only when the model answers correctly under the honest prompt and
  incorrectly under the sandbagging prompt. A sandbagging prompt that changes nothing
  is not an attack.
- **Defender**: a linear probe on the residual stream over answer tokens only.
- **Evasion**: steer the residual stream along the probe's direction at generation
  time, at increasing strength.
- **Measurement**: at each evasion strength, record probe AUROC, the accuracy drop
  the attack still achieves, and the suspicion a text-only monitor assigns.

The result is a curve. Three shapes matter:

1. Probe AUROC falls and the accuracy drop survives → evasion is cheap, and probes are
   weak against an adaptive attacker.
2. Probe AUROC falls but the accuracy drop goes with it → there is a tax, and the
   probe is doing useful work even though it can be evaded.
3. Probe AUROC falls and black-box suspicion rises → the probe pushes the attack into
   another monitor's view, which is the case for defence in depth.

A negative result (shape 1) is a publishable outcome, not a failure.

## Status

One script, `obftax.py`, which checks the two preconditions for everything above:

1. Does the sandbagging prompt actually produce an accuracy drop?
2. Does a linear probe on answer-token activations separate honest answers from
   successful attacks?

It prints honest accuracy, sandbagging accuracy, the number of successful attacks, and
probe AUROC at one layer. The probe is trained on honest-correct vs successful-attack
examples only, so it cannot win by separating the two prompts or the two accuracy
levels.

```bash
uv sync
uv run python obftax.py
```

Defaults are the constants at the top of the file: `Qwen2.5-1.5B-Instruct`, 200 MMLU
questions, layer 16. On Apple Silicon this runs in a few minutes.

Nothing is built until both checks pass. If the accuracy drop is small, the attack
needs a better prompt or a bigger model. If probe AUROC is near chance, there is
nothing to evade and no tax to measure.

The ordered steps after that, the gate each one has to clear, and what is deliberately
left out are in [RESEARCH_PLAN.md](RESEARCH_PLAN.md).

## Papers this depends on

- Goldowsky-Dill, Chughtai, Heimersheim, Hobbhahn. *Detecting Strategic Deception
  Using Linear Probes*. ICML 2025. <https://arxiv.org/abs/2502.03407> — the probe
  method being attacked, and evidence that it works on non-adaptive deception.
- Bailey, Serrano, Sheshadri, et al. *Obfuscated Activations Bypass LLM Latent-Space
  Defenses*. ICLR 2026. <https://arxiv.org/abs/2412.09565> — the result that motivates
  the question: latent-space monitors can be evaded.
- Gupta, Jenner. *RL-Obfuscation: Can Language Models Learn to Evade Latent-Space
  Monitors?* 2025. <https://arxiv.org/abs/2506.14261> — the closest existing adaptive
  attacker, and the closest existing evidence on whether evasion preserves behaviour.

PDFs are in `papers/`. Two earlier citations that do not bear directly on the measurement
are in `papers/not-cited/`.
