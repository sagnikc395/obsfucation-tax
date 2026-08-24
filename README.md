# Obfuscation Tax

This project asks a concrete question about white-box monitoring:

> If an attacker tries to hide from an activation probe, what do they have to give up?

Activation probes can often be evaded. That does not automatically make them useless. A probe can still be valuable if evading it makes the attack less effective, makes the model's text more suspicious to a black-box monitor, or creates a measurable tradeoff that a control protocol can exploit.

The goal of this project is to measure that tradeoff. I call it the obfuscation tax.

## Project Status

This repository is currently a research scaffold. The code is minimal:

- `main.py` is a placeholder entry point.
- `sample_control.py` is an exploratory ControlArena/Inspect script.
- The README describes the intended experiment and evaluation plan.

The current plan uses sandbagging as the attack task. Earlier versions considered code backdooring, but sandbagging is cheaper to run, easier to verify, and better suited to laptop-scale experiments.

## Research Question

The main question is:

> Can an attacker reduce probe performance without losing attack performance or becoming more visible to other monitors?

There are two useful outcomes:

- If evasion is expensive, activation probes are still useful as part of a defense-in-depth control system.
- If evasion is cheap, that is also an important negative result.

The project is not trying to show that probes are perfect. It is trying to quantify when they help, when they fail, and what costs an adaptive attacker pays while trying to evade them.

## Threat Model

The untrusted model is instructed to underperform subtly on benchmark questions. This is the sandbagging condition.

The same model is also run under an honest condition. Any sandbagging prompt that does not create a real accuracy gap is discarded. A failed manipulation should not be labeled as a successful attack.

The first target model is expected to be a small open model such as:

- `Qwen2.5-1.5B-Instruct` on Apple Silicon with MPS.
- `Qwen2.5-3B-Instruct` or `Llama-3.2-3B-Instruct` if more memory is available.

The intended task corpora are MMLU and GSM8K. These provide short-answer tasks with simple scoring and enough examples for activation collection.

## Monitors

The project compares three kinds of monitoring signal:

- A black-box monitor that reads the model transcript and assigns suspicion.
- A white-box activation probe trained on residual-stream activations over answer tokens.
- An ensemble that combines normalized black-box and white-box scores.

The black-box monitor is expected to use a small API model. This is the only planned paid component, and the expected cost is low. A very weak local monitor would make the probe look better than it really is, so it is not a good baseline.

## Main Experiments

### 1. Obfuscation Tax Curve

The first experiment varies the strength of the red team's evasion attempt. For each level of evasion pressure, the project measures:

- Probe AUROC.
- Honest-task accuracy.
- Sandbagging strength, measured as the accuracy drop from the honest baseline.
- Mean suspicion score from the black-box monitor.

The key question is whether probe evasion creates side effects. The most interesting result would be a curve where probe AUROC falls, but the attack also becomes weaker or more suspicious.

### 2. Subspace Exhaustion

The second experiment tests whether the probe is finding one narrow direction or a broader family of useful directions.

The loop is:

1. Train probe `P1`.
2. Let the red team evade `P1`.
3. Train `P2` on the evaded examples.
4. Repeat for several rounds.

The analysis tracks the angles between probes, the effective rank of the probe span, and whether attack quality degrades across rounds.

This asks whether the representation of deliberate underperformance is easy to exhaust or whether new probe directions keep appearing after each evasion round.

### 3. Safety and Usefulness Pareto

The third experiment evaluates complete control protocols under a fixed audit budget, such as 2 percent of samples.

For each protocol and attack setting, the project should report bootstrapped confidence intervals. This turns the work from a probing demo into a control evaluation: the result is not just whether a probe detects sandbagging, but whether it improves the safety/usefulness tradeoff of the protocol.

## Red-Team Ladder

The attacker is assumed to know the protocol and the thresholds. The planned attack levels are:

- `R0`: Prompted sandbagging with no probe knowledge.
- `R1`: Prompted sandbagging with instructions to look natural.
- `R2`: Soft prompt or steering vector optimized against the probe while preserving task behavior.
- `R3`: The same attack, but evaluated against a held-out probe trained at a different layer or on different data.

`R3` is the strongest test because it checks whether evasion transfers beyond the exact probe weights used during optimization.

## Main Failure Modes To Control For

The probe can appear to work for reasons that have little to do with intent. The negative controls are therefore a central part of the project.

### Prompt Leakage

The probe might detect that a sandbagging instruction is present in the prompt rather than detecting anything about the answer.

Mitigation: probe answer tokens only. Also include a condition where the sandbagging prompt is present but does not produce an accuracy drop.

### Surface Text Features

The signal might be visible in the text itself, with activations adding little value.

Mitigation: compare against a TF-IDF logistic-regression baseline on raw transcripts. If the text baseline performs almost as well as the activation probe, report that directly.

### Prefill Mismatch

Teacher-forced activations may not match activations from the model's own generations. A probe trained on one mode may fail in the other.

Mitigation: split evaluation across teacher-forced and self-generated activations.

### Template Overfit

The probe might learn the exact sandbagging prompt template.

Mitigation: test on held-out sandbagging prompt phrasings.

These controls should be reported as a table. They are not optional cleanup; they are what make the result credible.

## Implementation Plan

The planned four-week path is:

1. Build the corpus, validate honest and sandbagging conditions, cache activations, and run the black-box monitor baseline.
2. Train probes, sweep layers, and complete the confound-control table.
3. Run `R1` through `R3`, then produce the obfuscation tax curve and monitor tradeoff analysis.
4. Run subspace-exhaustion rounds, compute Pareto curves with confidence intervals, and prepare the writeup.

If `R2` or `R3` optimization does not converge, the fallback is a LoRA fine-tune on evasive sandbagging examples. That gives a weaker attacker, but it can still establish a useful lower bound on the cost of evasion.

## Expected Limitations

Results on a 1.5B or 3B model should not be presented as direct evidence about frontier models. The honest claim is narrower: this project tests a measurement method, a set of controls, and the failure modes that appear in a small-model setting.

The code should keep model names and devices in configuration rather than hardcoding them. If a larger GPU allocation becomes available, the same evaluation battery can be rerun at 7B scale.

## Setup

This project uses Python 3.13 and `uv`.

```bash
uv sync
uv run python main.py
```

For the exploratory ControlArena script:

```bash
uv run python sample_control.py
```

The current dependency list includes `torch`, `transformers`, `accelerate`, `control-arena`, `inspect-ai`, and related tooling.

## Deliverable

The intended final output is:

- A clean repository.
- Pareto plots for safety and usefulness.
- The obfuscation tax curve.
- The confound-control table.
- An 8 to 10 page writeup suitable for Alignment Forum or a similar venue.

## References

- Greenblatt et al., "AI Control: Improving Safety Despite Intentional Subversion", ICML 2024: https://proceedings.mlr.press/v235/greenblatt24a.html
- Goldowsky-Dill et al., "Detecting Strategic Deception with Linear Probes", ICML 2025: https://proceedings.mlr.press/v267/goldowsky-dill25a.html
- Bailey et al., "Obfuscated Activations Bypass LLM Latent-Space Defenses", ICLR 2026: https://openreview.net/forum?id=ktGmDGoWnB
- Terekhov et al., "Adaptive Attacks on Trusted Monitors Subvert AI Control Protocols", ICLR 2026: https://arxiv.org/abs/2510.09462
- Gupta and Jenner, "RL-Obfuscation: Can Language Models Learn to Evade Latent-Space Monitors?": https://arxiv.org/abs/2506.14261
- "Auditing Games for Sandbagging": https://arxiv.org/abs/2512.07810
- UK AISI White Box Control team, sandbagging investigations update: https://aisi.gov.uk/research/white-box-control-at-uk-aisi---update-on-sandbagging-investigations

Additional references to verify before citing in a final writeup:

- van der Weij et al., "AI Sandbagging: Language Models can Strategically Underperform on Evaluations", 2024.
- Benton et al., "Sabotage Evaluations for Frontier Models", Anthropic, 2024.

## Related Tooling

- Apollo Research deception-detection probe code: https://github.com/ApolloResearch/deception-detection
- ControlArena: https://github.com/UKGovernmentBEIS/control-arena
- ControlArena APPS setting documentation: https://control-arena.aisi.org.uk/settings/apps.html
