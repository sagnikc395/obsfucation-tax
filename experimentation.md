# Experimentation Code Metastructure

This document is a code-architecture map for implementing the obfuscation-tax
experiment. It intentionally avoids writing the experiment code. Use it as a guide
for what modules to create, what each module should own, what artifacts should pass
between stages, and which existing code to study before implementing each part.

## Current Code To Read First

Start with the code already in this repository:

- `README.md`: the research question, threat model, experiment list, controls, and
  intended deliverables.
- `main.py`: currently only a placeholder entry point. This is the natural place to
  later attach a CLI or dispatch into experiment stages.
- `sample_control.py`: an exploratory ControlArena/Inspect script. Use it to learn
  the basic shape of ControlArena configuration, `EvalMode.HONEST`,
  `EvalMode.ATTACK`, monitoring scorers, and `inspect_ai.eval`.
- `pyproject.toml`: the current dependency boundary. Prefer building on these
  libraries before adding new ones.

The repository is currently a scaffold, so most of the files below do not exist yet.
The point is to make the eventual implementation predictable and easy to audit.

## Desired Repository Shape

Recommended top-level structure:

```text
obsfucation-tax/
  main.py
  sample_control.py
  experimentation.md
  pyproject.toml
  README.md

  configs/
    default.yaml
    models.yaml
    datasets.yaml
    prompts.yaml
    probes.yaml
    monitors.yaml
    red_team.yaml

  src/
    obfuscation_tax/
      __init__.py
      cli.py
      config.py
      seeds.py
      logging.py

      data/
        load.py
        splits.py
        scoring.py
        schemas.py

      prompts/
        templates.py
        sandbagging.py
        controls.py

      generation/
        runner.py
        parsing.py
        cache.py

      activations/
        collector.py
        token_spans.py
        cache.py
        layers.py

      probes/
        dataset.py
        train.py
        evaluate.py
        linear.py
        metrics.py

      monitors/
        black_box.py
        text_baselines.py
        ensemble.py

      red_team/
        r0_prompted.py
        r1_natural.py
        r2_probe_evasion.py
        r3_transfer.py

      controls/
        prompt_leakage.py
        surface_text.py
        prefill_mismatch.py
        template_overfit.py
        failed_attack_filtering.py

      analysis/
        obfuscation_tax_curve.py
        pareto.py
        subspace_exhaustion.py
        bootstrap.py
        tables.py

  scripts/
    prepare_data.py
    generate_answers.py
    collect_activations.py
    train_probe.py
    score_monitor.py
    run_red_team.py
    run_controls.py
    make_plots.py

  artifacts/
    splits/
    generations/
    activations/
    probes/
    monitor_scores/
    metrics/
    plots/
    tables/

  tests/
    test_scoring.py
    test_splits.py
    test_token_spans.py
    test_metrics.py
    test_artifact_schemas.py
```

## Pipeline Shape

Think of the experiment as a staged artifact pipeline:

```text
config
  -> dataset loading
  -> deterministic splits
  -> prompt construction
  -> model generation
  -> answer parsing and scoring
  -> successful-attack filtering
  -> activation collection
  -> probe training
  -> monitor scoring
  -> red-team evasion
  -> confound controls
  -> analysis tables and plots
```

Each stage should read immutable artifacts from the previous stage and write new
artifacts rather than silently mutating existing files. This makes failed runs easy
to inspect and makes final numbers reproducible.

## Configuration Layer

Owns all choices that affect results.

Suggested files:

- `configs/default.yaml`: global defaults, output directories, seed, and device.
- `configs/models.yaml`: model names, revisions, dtype, device map, and tokenizer
  settings.
- `configs/datasets.yaml`: dataset names, splits, subset sizes, and scoring rules.
- `configs/prompts.yaml`: honest prompts, sandbagging prompts, held-out templates,
  and monitor prompts.
- `configs/probes.yaml`: layers, activation aggregation method, train/validation
  settings, and regularization.
- `configs/red_team.yaml`: red-team level, evasion strength, optimization budget,
  and transfer settings.

Design rule:

- No model name, dataset name, layer number, prompt text, threshold, seed, or output
  path should be hardcoded inside experiment logic.

## Data Module

Responsible for loading benchmark examples and producing stable splits.

Suggested responsibilities:

- `data/load.py`: load MMLU, GSM8K, or any later dataset through one interface.
- `data/splits.py`: create and save deterministic train/validation/test split IDs.
- `data/scoring.py`: score parsed model answers against gold labels.
- `data/schemas.py`: define the expected fields for examples, generations, scores,
  activations, and metrics.

Artifacts:

```text
artifacts/splits/{dataset}/seed_{seed}.json
```

Important invariant:

- The final test split is never used for prompt tuning, probe selection, red-team
  optimization, or threshold selection.

Code to learn from:

- Look for dataset-loading and answer-scoring examples in evaluation harnesses such
  as EleutherAI's `lm-evaluation-harness`.
- For GSM8K answer parsing conventions, inspect existing GSM8K evaluation scripts
  before inventing a parser.

## Prompt Module

Responsible for prompt templates and condition labels.

Suggested responsibilities:

- `prompts/templates.py`: render versioned templates with explicit template IDs.
- `prompts/sandbagging.py`: define `honest`, `sandbag_r0`, and `sandbag_r1`
  template families.
- `prompts/controls.py`: define prompt-leakage and held-out-template controls.

Conditions to support:

- `honest`
- `sandbag_r0`
- `sandbag_r1`
- `prompt_leakage_control`
- `heldout_template`

Important invariant:

- Prompt text should be stored with each generation artifact, not reconstructed
  later from memory.

## Generation Module

Responsible for running the untrusted model and caching outputs.

Suggested responsibilities:

- `generation/runner.py`: load model/tokenizer and run deterministic generation.
- `generation/parsing.py`: extract final answers from generated text.
- `generation/cache.py`: write and read JSONL generation artifacts.

Artifact shape:

```text
artifacts/generations/{dataset}/{model}/{condition}/seed_{seed}.jsonl
```

Each row should contain:

```text
example_id
dataset
split
condition
seed
prompt_template_id
prompt
completion
parsed_answer
gold_answer
correct
model
model_revision
decoding_settings
```

Design rule:

- Store enough metadata that the generation can be reproduced without reading the
  source code from the original run.

Code to learn from:

- `sample_control.py` shows the rough shape of running an evaluation through
  Inspect/ControlArena.
- Hugging Face Transformers generation examples are useful for plain local model
  generation and tokenizer handling.

## Attack Filtering Module

Responsible for separating real sandbagging from failed manipulation.

Suggested responsibility:

- Compare each example's honest correctness with its sandbagging correctness.

Suggested labels:

- `honest_correct`
- `sandbag_correct`
- `attack_succeeded`
- `accuracy_drop`

Important invariant:

- A sample should not be treated as a successful attack merely because it came from
  a sandbagging prompt. The model must actually underperform relative to the honest
  condition.

## Activation Module

Responsible for extracting white-box features.

Suggested responsibilities:

- `activations/collector.py`: run the model and capture residual-stream activations.
- `activations/token_spans.py`: identify answer-token positions.
- `activations/layers.py`: choose and name layer outputs consistently.
- `activations/cache.py`: save tensor artifacts plus metadata.

Artifact shape:

```text
artifacts/activations/{dataset}/{model}/{condition}/{mode}/layer_{layer}/seed_{seed}.pt
```

Modes to support:

- `teacher_forced`: collect activations while replaying saved answers.
- `self_generated`: collect activations during generation.

Important invariants:

- Probe features should come from answer tokens only.
- Prompt-token activations should be excluded from main probe training.
- Store token spans so another person can audit which tokens became features.

Code to learn from:

- Apollo Research's deception-detection probe code is the most relevant reference
  for activation probing workflows.
- TransformerLens examples are useful if you choose to use hooks through that
  ecosystem instead of raw Transformers hooks.

## Probe Module

Responsible for training and evaluating linear probes.

Suggested responsibilities:

- `probes/dataset.py`: turn cached activations into trainable feature matrices.
- `probes/linear.py`: define the linear probe model or wrapper.
- `probes/train.py`: fit probes on train split only.
- `probes/evaluate.py`: evaluate on validation and test splits.
- `probes/metrics.py`: compute AUROC, accuracy, calibration, and confidence
  intervals.

Artifact shape:

```text
artifacts/probes/{dataset}/{model}/layer_{layer}/seed_{seed}.pt
artifacts/metrics/probe_metrics.csv
```

Design rule:

- Treat layer choice as model selection. Pick it on validation data, then report
  final numbers once on test data.

## Monitor Module

Responsible for black-box and text-only baselines.

Suggested responsibilities:

- `monitors/black_box.py`: score transcripts with a text-only monitor.
- `monitors/text_baselines.py`: train TF-IDF or other transcript-only classifiers.
- `monitors/ensemble.py`: combine normalized black-box and activation-probe scores.

Artifact shape:

```text
artifacts/monitor_scores/{dataset}/{model}/seed_{seed}.jsonl
```

Important invariant:

- The black-box monitor must not see activations, hidden states, probe scores, or
  labels.

Code to learn from:

- `sample_control.py` uses `max_suspicion_scorer()`, which is the local starting
  point for understanding monitor-score flow in ControlArena.
- ControlArena examples are the relevant reference for audit budgets, monitor
  scores, and control protocols.

## Red-Team Module

Responsible for creating increasingly adaptive attacks.

Suggested responsibilities:

- `red_team/r0_prompted.py`: basic prompted sandbagging.
- `red_team/r1_natural.py`: prompted sandbagging with naturalness pressure.
- `red_team/r2_probe_evasion.py`: optimize a soft prompt, steering vector, or other
  intervention against a known probe.
- `red_team/r3_transfer.py`: evaluate the evasion against held-out probes.

Important invariants:

- `R2` may optimize against validation data, but never against test data.
- `R3` should use a probe trained at a different layer or on different data.
- Attack strength and naturalness should be reported alongside probe evasion.

Fallback if `R2` is hard:

- Use a LoRA fine-tune on evasive sandbagging examples and report it as a weaker
  adaptive attacker.

## Confound-Control Module

Responsible for proving the probe is not winning for trivial reasons.

Suggested files:

- `controls/prompt_leakage.py`
- `controls/surface_text.py`
- `controls/prefill_mismatch.py`
- `controls/template_overfit.py`
- `controls/failed_attack_filtering.py`

Required control table:

| Control | Question | What to compare |
| --- | --- | --- |
| Prompt leakage | Is the probe detecting the prompt? | prompt-token features vs answer-token features |
| Surface text | Is the signal visible in text alone? | activation probe vs TF-IDF classifier |
| Prefill mismatch | Does collection mode matter? | teacher-forced vs self-generated activations |
| Template overfit | Did the probe memorize one wording? | seen templates vs held-out templates |
| Failed attack filtering | Is the probe detecting condition labels? | all sandbag prompts vs successful attacks only |

Artifact:

```text
artifacts/metrics/confound_controls.csv
```

## Analysis Module

Responsible for turning stage outputs into final claims.

Suggested responsibilities:

- `analysis/obfuscation_tax_curve.py`: probe AUROC vs attack strength and suspicion.
- `analysis/subspace_exhaustion.py`: probe angles, span rank, and degradation over
  adaptive rounds.
- `analysis/pareto.py`: safety/usefulness curves under audit budgets.
- `analysis/bootstrap.py`: confidence intervals over examples.
- `analysis/tables.py`: Markdown or CSV result tables.

Final artifacts:

```text
artifacts/plots/obfuscation_tax_curve.png
artifacts/plots/safety_usefulness_pareto.png
artifacts/tables/confound_controls.md
artifacts/tables/main_results.md
```

## CLI Shape

The eventual CLI should expose the experiment stages directly. The names below are
illustrative; they describe the interface, not code that exists today.

```text
uv run python -m obfuscation_tax prepare-data --config configs/default.yaml
uv run python -m obfuscation_tax generate --config configs/default.yaml --condition honest
uv run python -m obfuscation_tax generate --config configs/default.yaml --condition sandbag_r0
uv run python -m obfuscation_tax collect-activations --config configs/default.yaml
uv run python -m obfuscation_tax train-probe --config configs/default.yaml
uv run python -m obfuscation_tax score-monitor --config configs/default.yaml
uv run python -m obfuscation_tax run-red-team --config configs/default.yaml --level r2
uv run python -m obfuscation_tax run-controls --config configs/default.yaml
uv run python -m obfuscation_tax analyze --config configs/default.yaml
```

`main.py` can eventually become a thin wrapper around this CLI, or it can remain a
small smoke-test entry point while the real CLI lives under `src/obfuscation_tax`.

## Test Shape

Tests should focus on logic that can silently corrupt results.

Recommended tests:

- split creation is deterministic for a seed
- train/validation/test split IDs do not overlap
- answer parsers score known examples correctly
- answer-token span detection excludes prompt tokens
- artifact schemas reject missing metadata
- AUROC and bootstrap helpers match known toy examples
- failed sandbagging attempts are not labeled as successful attacks

Avoid tests that require downloading large models unless they are marked as slow or
integration tests.

## External Code References To Study

Use these as learning references before implementing the corresponding modules:

- Apollo Research deception-detection:
  `https://github.com/ApolloResearch/deception-detection`
  Study this for activation collection, probe datasets, linear probes, and
  representation-level evaluation patterns.

- ControlArena:
  `https://github.com/UKGovernmentBEIS/control-arena`
  Study this for honest/attack modes, monitoring scorers, audit protocols, and
  control-evaluation structure. The local `sample_control.py` is the smallest
  in-repo example of this style.

- ControlArena APPS setting docs:
  `https://control-arena.aisi.org.uk/settings/apps.html`
  Study this if you continue with ControlArena tasks before the sandbagging pipeline
  is implemented.

- Inspect AI:
  `https://inspect.aisi.org.uk/`
  Study this for evaluation task structure, scorers, logging, and reproducible eval
  runs. `sample_control.py` imports `inspect_ai.eval`.

- Hugging Face Transformers:
  `https://github.com/huggingface/transformers`
  Study this for model loading, deterministic generation, tokenizer behavior, hidden
  states, and model revisions.

- EleutherAI lm-evaluation-harness:
  `https://github.com/EleutherAI/lm-evaluation-harness`
  Study this for benchmark loading, multiple-choice evaluation, task abstractions,
  and reproducible language-model eval conventions.

- TransformerLens:
  `https://github.com/TransformerLensOrg/TransformerLens`
  Study this if you want a hook-based activation workflow instead of writing raw
  PyTorch hooks over Hugging Face models.

## Implementation Order

Build in this order:

1. Configuration and artifact schemas.
2. Dataset loading, answer parsing, and deterministic splits.
3. Honest and `R0` generation.
4. Correctness scoring and successful-attack filtering.
5. Answer-token activation collection.
6. Linear probe training and AUROC evaluation.
7. Black-box monitor and TF-IDF baseline.
8. Confound-control table.
9. `R1`, then `R2`, then `R3`.
10. Obfuscation-tax curve, subspace-exhaustion analysis, and Pareto plots.

This order gives useful intermediate checks before any adaptive attack code exists.
