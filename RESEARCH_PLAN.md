# Obfuscation Tax: Semester Research Plan

## 0. Purpose and intended contribution

This document turns the repository's initial experiment sketch into a semester-long
research program. The goal is not merely to train a probe that separates honest and
sandbagging examples. The goal is to determine whether white-box monitoring remains
useful when the monitored model adapts to it, and to measure the cost of that
adaptation.

The central object is the **obfuscation tax**: the loss imposed on an attacker when it
tries to evade an activation-based monitor while preserving the behavior that makes
the attack useful. The tax may appear as weaker attack performance, reduced
reliability, greater black-box detectability, poorer transfer to new monitors, extra
compute/data/training cost, or fragility across prompts, tasks, layers, and models.

The eventual contribution should be a careful empirical measurement paper, not a
claim that linear probes solve strategic deception. A strong negative result is
valuable: if a realistic adaptive attack can evade the probe at little cost and with
good transfer, that should be the conclusion. A strong positive result is also
valuable: if evasion reliably damages the attack or creates detectable side effects,
that supports using probes as one component of defense in depth.

The intended outputs are:

1. A reproducible codebase and artifact pipeline.
2. A preregistered or versioned evaluation protocol.
3. A main result on the tradeoff between attack utility, probe evasion, and other
   monitor signals.
4. A set of controls that distinguish intent-related signal from prompt, text,
   template, task, and collection artifacts.
5. A workshop-style paper, an accessible LessWrong/Alignment Forum post, and a
   concise limitations and negative-results report.

## 0.1 Relationship to the AI Alignment course

The course is the initial setting and accountability structure for this work, not
the definition of its ambition. The course requirements ask for a novel contribution
and empirical results, with a short proposal, a mid-project check-in, and a roughly
4--8 page final report/presentation. Those deliverables should be treated as staged
research artifacts extracted from the larger project:

- The course proposal is the first frozen version of the research question,
  hypothesis, and minimum viable experiment.
- The course check-in is a progress and risk review, not the end of the exploratory
  phase. It should state which claims are supported, which are not yet tested, and
  which parts of the original plan changed.
- The course report should present the cleanest defensible result available by the
  deadline, including limitations and negative results. It need not contain every
  experiment in this document.
- The course presentation should communicate the central idea and one or two key
  figures. The longer-form workshop paper and public post can later add the full
  attack ladder, replications, controls, and broader literature context.

This creates two nested scopes:

1. **Course-complete scope:** a valid behavioral sandbagging setup, one activation
   monitoring baseline, at least one meaningful control, and one testable result.
2. **Research-complete scope:** realistic adaptive attacks, leakage-safe controls,
   uncertainty estimates, cross-task/model transfer, protocol-level evaluation,
   replication, and a claim that can survive external scrutiny.

The course-complete scope is a fallback floor, not the target contribution. Work done
before and during the semester should be organized so that early results can be
reported honestly without prematurely freezing the scientific question at the level
of a class exercise.

## 1. Research question and claims discipline

### Primary question

When a model is instructed to sandbag and then adaptively optimizes against an
activation probe, does successful evasion impose a measurable cost on the attack or
make the attack easier to detect by other means?

### Secondary questions

- Does a probe detect a stable representation of deliberate underperformance, or only
  a narrow direction associated with one prompt and one layer?
- Does evasion transfer across held-out data, prompt templates, layers, random probe
  seeds, model checkpoints, and monitor implementations?
- How much does white-box monitoring improve a complete control protocol at a fixed
  audit budget?
- Are apparent gains caused by answer correctness, verbosity, formatting, refusal
  language, or other surface features rather than strategic intent?
- Does the measured tax change with model scale, task difficulty, or attack strength?

### Claims the project should avoid

- “The probe detects deception” unless the experiment has ruled out the major
  confounds and tested behaviorally successful attacks.
- “Evasion is expensive” based only on a synthetic vector projection or a drop in
  probe AUROC. Evasion must be measured jointly with preserved attack utility and
  resource cost.
- “This generalizes to frontier models” from Qwen 1.5B/3B experiments.
- “The monitor is robust” when the attacker has only been tested against one fixed
  probe, one prompt, or one random seed.

Use narrower language such as “the activation signal generalizes under these held-out
conditions” or “we observe an empirical tradeoff in this model/task regime.”

## 2. Operational definitions

Every run should use explicit definitions recorded in its manifest.

### Honest behavior

The model receives the normal task prompt and is scored for task performance. Honest
accuracy is measured per example, not only as a batch average.

### Attack behavior

The model is prompted or trained to underperform on the same task while maintaining
the appearance of an ordinary answer. An attack is successful only when there is
evidence of the intended behavioral effect, for example:

- honest answer correct and attack answer incorrect;
- a prespecified accuracy drop relative to honest behavior;
- for tasks with graded outcomes, a prespecified decrease in score.

The analysis must retain both the full attack condition and the subset of successful
attacks. Conditioning on successful attacks can introduce selection effects, so both
views must be reported.

### Probe evasion

Probe evasion is a reduction in the probe's held-out detection performance or score on
attack examples, evaluated without changing the test set or threshold after seeing
the result. Report AUROC and AUPRC, but also report operating-point metrics such as
true-positive rate at a fixed false-positive rate and calibration.

### Attack utility

Attack utility is not just “accuracy drop.” Track:

- attack success rate;
- honest-condition capability retained by the attacker;
- consistency across repeated samples;
- answer validity/parsing rate;
- completion length and latency;
- naturalness or black-box suspicion;
- intervention/training data and compute used for evasion.

### Obfuscation tax

Report a vector of costs rather than forcing all costs into one scalar. Where a scalar
is useful, define it before the test run, for example the minimum degradation in
attack utility or increase in alternative-monitor suspicion required to reduce probe
TPR to a specified operating point.

## 3. Experimental matrix

The core matrix should vary factors systematically, but not all combinations need to
be run at full scale. Start with a small development matrix, lock the protocol, and
then execute the confirmatory matrix.

| Axis | Development values | Confirmatory values |
| --- | --- | --- |
| Model | Qwen2.5-1.5B-Instruct | Qwen2.5-1.5B, Qwen2.5-3B; one additional family if compute allows |
| Dataset | MMLU subset | MMLU, GSM8K, and a held-out task family or synthetic task |
| Prompt attack | R0, R1 | R0, R1, R2, R3 |
| Probe layer | 12/16/20 | all feasible residual layers or a prespecified sparse sweep |
| Probe | linear logistic | linear, regularization sweep, random seeds; optional nonlinear exploratory probe |
| Activation mode | teacher-forced | teacher-forced and self-generated |
| Templates | one seen template | multiple seen templates plus held-out templates |
| Monitor | local text baseline | TF-IDF, black-box judge, activation probe, ensemble |
| Random seeds | 42 | at least 3 seeds for key results, 5 if variance is high |
| Audit budgets | 1%, 2%, 5%, 10% | same, with threshold selection on validation only |

The main paper should identify a small primary slice before running it. Additional
models, layers, and prompts are robustness checks, not opportunities to search for a
favorable result.

## 4. Phases and semester schedule

The schedule below assumes roughly 14–16 weeks. If the semester is shorter, combine
Weeks 2–3 and Weeks 10–11, but do not remove the control and writing phases.

### Phase 0 — Pre-semester foundation (before the course begins)

This is the most important addition for a research-first version of the project. The
objective is to arrive at the course with a working, falsifiable research system—not
to spend the first weeks deciding whether the pipeline runs.

Complete before the semester whenever feasible:

- establish the repository, environment, model loading, and artifact cache;
- run the synthetic dataset end to end;
- validate MMLU loading, answer parsing, paired examples, and split isolation;
- reproduce the existing small-model artifacts from a clean checkout;
- implement one honest condition and one real sandbagging condition;
- confirm that the attack creates a behavioral gap before collecting large activation
  datasets;
- collect a small activation sample and train a baseline linear probe;
- replace known placeholder controls with either real implementations or explicit
  `not_implemented` failures;
- create a run manifest and a first version of the experiment protocol;
- write the one-page course proposal only after the minimum viable experiment is
  technically demonstrated.

The pre-semester target is not a polished result. It is a reliable research seed:
one real effect, one credible baseline, one known limitation, and enough tooling to
iterate quickly once the semester starts. Reserve some pre-semester time for reading
and conceptual work; the scientific contribution will come from choosing and
testing the right claim, not from maximizing the number of generated examples.

At the end of this phase, make a go/no-go decision among three paths:

- **Primary path:** the attack and probe are measurable, so proceed to adaptive
  evasion and tax measurement.
- **Narrower path:** the attack works but adaptive optimization is too expensive, so
  focus on transfer, confounds, and monitor diversity while treating evasion as a
  carefully bounded proxy.
- **Pivot path:** the behavioral effect is unreliable, so change the task or attack
  formulation before investing in the larger hypothesis.

### Phase 1 — Scope, literature, and protocol lock (Weeks 1–2)

Objectives:

- sharpen the hypothesis and threat model;
- decide which result would count as evidence for or against an obfuscation tax;
- establish the primary model, datasets, attack templates, layers, seeds, and metrics;
- understand adjacent work well enough to distinguish this project from probe,
  sandbagging, deception, and AI-control papers.

Deliverables:

- a two-page internal protocol;
- a literature matrix with claims, methods, limitations, and reusable evaluation
  ideas;
- a preregistration-style YAML/Markdown file containing primary outcomes and
  exclusions;
- a compute and API budget;
- a data card and threat-model statement.

Protocol rules:

- freeze the test IDs and keep the test set unavailable to attack optimization;
- define layer-selection and threshold-selection procedures in advance;
- distinguish exploratory plots from confirmatory plots;
- record every model revision, tokenizer, dtype, decoding setting, and prompt version;
- do not delete failed runs; mark them as failed with a reason.

Exit criteria: another person can read the protocol and reproduce what will be
optimized, selected, and evaluated without asking what was decided after looking at
the test results.

### Phase 2 — Data, scoring, and artifact integrity (Weeks 2–3)

Objectives:

- make dataset loading and scoring reliable;
- validate split isolation and paired honest/attack examples;
- make every downstream artifact auditable.

Implementation priorities:

- verify MMLU and GSM8K parsers against hand-checked examples;
- use stable example IDs and save exact split artifacts;
- store prompt text, template ID, completion, parsed answer, correctness, model
  revision, and decoding settings for every generation;
- add a run manifest containing git commit, configuration hash, environment, seed,
  device, and input artifact hashes;
- make cache keys include all result-changing settings;
- add checks that paired honest and attack generations refer to the same example;
- add tests for duplicate IDs, split overlap, missing rows, and malformed outputs.

Exit criteria: the pipeline can be run on the synthetic dataset and produces a
complete, self-describing artifact bundle with deterministic scores.

### Phase 3 — Establish the behavioral attack (Weeks 3–4)

Objectives:

- demonstrate a real, repeatable sandbagging gap before doing any monitoring;
- characterize where the attack succeeds and fails.

Run:

- honest baseline;
- R0 prompted sandbagging;
- R1 naturalness-preserving sandbagging;
- multiple prompt templates and decoding seeds;
- MMLU first, then GSM8K once the scoring path is stable.

Report:

- honest accuracy and attack accuracy;
- paired per-example attack-success rate;
- task/category breakdowns;
- completion length and invalid-answer rate;
- examples of successful and failed attacks;
- whether attack behavior is stable across random seeds.

Do not proceed to expensive activation collection until the attack has a meaningful
effect. If R0 cannot produce a reliable gap, revise the task/prompt/model choice and
document the failed attempt rather than treating an ineffective prompt as an attack.

Exit criteria: the primary attack condition has a prespecified minimum effect size
and passes a paired behavioral sanity check.

### Phase 4 — Probe baseline and representation audit (Weeks 4–6)

Objectives:

- establish the simplest useful white-box baseline;
- measure layer and token-position dependence;
- expose implementation errors early.

Run:

- answer-token residual-stream activations;
- teacher-forced and self-generated collection;
- layer sweep across the model;
- mean, last-token, and carefully defined pooling variants;
- linear probes with regularization selected on validation data;
- at least three probe-training seeds for the main setting.

Compare against:

- chance and majority baselines;
- a task/correctness-only baseline;
- a TF-IDF transcript classifier;
- a black-box monitor with fixed prompt and output parsing.

Critical implementation audit:

- check token spans visually or with decoded-token fixtures;
- verify no prompt tokens enter the main feature matrix;
- save normalization statistics and apply training statistics at evaluation;
- confirm the test set is not used during layer/regularization selection;
- inspect probe scores separately for honest-correct, honest-incorrect,
  attack-correct, and attack-incorrect examples.

Exit criteria: the baseline probe is numerically trustworthy, its operating point is
defined on validation data, and its advantage over trivial baselines is known.

### Phase 5 — Confound and validity controls (Weeks 6–7)

This is a publication-critical phase. Controls should be completed before adaptive
attacks are interpreted.

Required controls:

1. **Prompt leakage.** Train probes on prompt-token activations and answer-token
   activations separately, using genuinely separate honest and attack dictionaries.
   Include prompts that mention sandbagging but do not cause an accuracy drop.
2. **Surface text.** Compare activation probes with TF-IDF/logistic and, if possible,
   a frozen text encoder. Match train/test examples and report paired differences.
3. **Prefill mismatch.** Evaluate probes trained and tested within each collection
   mode and cross-mode. Treat a teacher-forced-only result as limited evidence.
4. **Template overfit.** Split by prompt template, not only by example. Hold out
   entire phrasings and report seen-to-unseen degradation.
5. **Failed attack filtering.** Report all prompts and behaviorally successful
   attacks, with denominators. Never silently relabel the condition as intent.
6. **Correctness leakage.** Test whether the probe simply detects answer difficulty,
   wrongness, length, or malformed formatting. Match or regress out these variables.
7. **Task leakage.** Train on some task categories and test on others when possible.
8. **Duplicate and near-duplicate leakage.** Check question and template similarity
   across splits.

Important repository follow-up: replace placeholder or heuristic control outputs with
actual measurements. A control that returns a synthetic score is useful for a unit
test but must never appear as empirical evidence.

Exit criteria: every high-level positive result has an explicit alternative
explanation and a corresponding control result.

### Phase 6 — Red-team ladder (Weeks 8–10)

Objectives:

- move from an unadaptive attack to attacks with increasing monitor knowledge;
- separate “the probe can be evaded” from “a realistic attacker can evade it.”

#### R0: prompted sandbagging

No probe knowledge. This establishes the raw signal and provides the baseline attack.

#### R1: naturalness pressure

Prompt the model to avoid obvious refusal, hedging, repetitive language, or formatting
artifacts. Measure whether black-box suspicion falls and whether the activation signal
changes.

#### R2: known-probe evasion

Implement a real model-level attack where possible: differentiable steering,
activation intervention, soft prompt optimization, or a small LoRA trained only on
allowed data. The current synthetic activation perturbation should remain as a
diagnostic lower-level baseline, but should be labeled “representation-space
evasion,” not “model attack.”

For each budget/strength, record:

- training examples and optimization steps;
- wall-clock time and accelerator hours;
- probe score reduction;
- attack success and retained capability;
- completion statistics;
- black-box and text-monitor suspicion;
- distance or magnitude of the intervention.

#### R3: transfer and adaptive evaluation

Evaluate against probes not used for optimization: different layer, training seed,
training subset, prompt family, and possibly model checkpoint. Add an ensemble-held-
out condition where the attacker knows the family but not the exact probe weights.

Avoid allowing test feedback through early stopping, prompt selection, intervention
strength selection, or manual cherry-picking.

Exit criteria: each attack level has a clear knowledge budget, optimization budget,
and held-out evaluation target.

### Phase 7 — Obfuscation-tax curves (Weeks 10–11)

Construct curves over prespecified evasion strengths or optimization budgets. Each
point should include uncertainty intervals and a fixed definition of the operating
point.

Primary plot family:

- x-axis: evasion budget/strength;
- y-axis: probe TPR at fixed FPR, AUROC, and AUPRC;
- companion panels: attack success, retained capability, black-box suspicion,
  completion validity, and resource cost.

The key interpretation is joint movement. A falling probe AUROC alone is evasion; a
falling AUROC accompanied by substantial capability loss or increased alternative-
monitor suspicion is evidence of a tax.

Analysis requirements:

- bootstrap at the example or paired-example level;
- report per-task and aggregate metrics;
- show raw points, not only smoothed lines;
- state how missing/invalid generations are handled;
- include negative and failed runs.

### Phase 8 — Subspace exhaustion and monitor diversity (Weeks 11–12)

Test whether repeated probe-and-evasion rounds exhaust one direction or reveal a
broader set of evasive strategies.

Round protocol:

1. Train probe P1 on an allowed training split.
2. Generate or optimize an attack against P1.
3. Train P2 on newly collected evaded examples, without test access.
4. Repeat for a prespecified number of rounds.
5. Evaluate every round against old and held-out probes.

Measure:

- probe angles and cosine similarities;
- effective rank and singular-value spectrum of the probe span;
- residual detectability after projecting out prior directions;
- attack utility degradation by round;
- transfer to unseen layers/templates/seeds;
- whether a diverse ensemble is materially stronger than one probe.

Be careful with interpretation: a high effective rank does not by itself prove many
semantically distinct concepts, and probe-angle results are sensitive to feature
normalization and layer choice.

### Phase 9 — Control-protocol evaluation (Weeks 12–13)

Move from classifier metrics to a decision problem. Under a fixed audit budget,
compare protocols such as:

- no monitor;
- black-box monitor only;
- activation probe only;
- text baseline only;
- fixed weighted ensemble;
- validation-trained ensemble;
- diverse-probe ensemble if supported by earlier results.

For each protocol, report:

- attack escape rate;
- honest rejection or disruption rate;
- usefulness/throughput;
- audit fraction and latency;
- false-positive rate on honest behavior;
- performance across R0–R3;
- uncertainty intervals.

The Pareto plot should use a clearly named safety metric and a clearly named
usefulness metric. Do not label an arbitrary monitor score “safety” without defining
the event it predicts.

### Phase 10 — Robustness, replication, and scope expansion (Weeks 13–14)

Use the remaining compute on the highest-value uncertainty, not an unconstrained
hyperparameter search.

Priority order:

1. replicate the primary result with new seeds;
2. test a second model size or family;
3. test the second dataset/task family;
4. test held-out prompt and layer transfer;
5. run a small human or expert audit of monitor judgments if black-box scores are
   central to the conclusion.

If resources are tight, prefer one clean replication and one transfer test over many
   extra layers on the same data.

### Phase 11 — Writing and release (Weeks 14–16)

Produce the paper and public post from the same result tables.

Paper structure:

1. Abstract: question, setting, main empirical finding, and scope.
2. Introduction: why probe evasion matters for white-box monitoring.
3. Threat model and definitions of attack utility and tax.
4. Experimental setup and leakage-safe protocol.
5. Behavioral attack validation.
6. Probe and monitor baselines.
7. Adaptive attacks and tax curves.
8. Controls, transfer, and subspace results.
9. Control-protocol/Pareto evaluation.
10. Limitations, negative results, and implications.

LessWrong/Alignment Forum version:

- lead with the motivating question and one intuitive figure;
- explain activation probes without assuming mechanistic-interpretability jargon;
- show a successful evasion example and a failed/expensive evasion example;
- include the strongest negative result prominently;
- explain what the experiment does not establish;
- link to code, configs, raw aggregate artifacts, and a reproducibility note.

Before release:

- rerun the final tables from clean artifacts;
- verify figure numbers against CSVs;
- check all test-set access logs and manifests;
- release prompt templates and licenses where permitted;
- remove API keys and private data;
- add a model/data card and an ethics/safety note;
- ask at least one person not involved in implementation to audit the main claim.

## 5. Statistical analysis plan

Use paired analyses wherever honest and attack outputs correspond to the same
question. Aggregate metrics should not hide task-level heterogeneity.

Minimum reporting:

- point estimate and 95% bootstrap interval;
- number of examples and number of successful attacks;
- per-seed mean and dispersion;
- per-task/category breakdown;
- operating-point metrics at a fixed validation-selected FPR;
- multiple-comparison awareness for exploratory layer/task sweeps.

For the main tax claim, define a comparison such as:

> At a fixed probe false-positive rate, the adaptive attacker must either lose at
> least X percentage points of attack success, increase black-box suspicion by Y,
> or spend Z units of optimization resource to reduce probe TPR below the target.

The values X, Y, and Z must be chosen as practical thresholds before confirmatory
evaluation, or the result must be described descriptively rather than as a threshold
test.

## 6. Engineering milestones and repository work

### Must-have engineering

- one command per pipeline stage;
- immutable, hash-addressed or manifest-tracked artifacts;
- deterministic seeds where generation is deterministic;
- explicit cache invalidation;
- complete schema validation;
- CI tests for parsers, splits, token spans, metrics, and artifact alignment;
- plotting scripts that regenerate every paper figure;
- a final-results configuration separate from exploratory configs.

### High-priority fixes in the current scaffold

- replace the placeholder prompt-leakage score with real separate prompt-token
  features for honest and attack conditions;
- ensure probe training and evaluation use identical saved normalization statistics;
- fix any split/config mismatch between dataset declarations and actual loaded data;
- add paired attack-success labels to the artifact schema;
- make R2 distinguish synthetic activation perturbation from model-level optimization;
- implement real self-generated activation collection before relying on that control;
- add uncertainty and operating-point metrics to the tax-curve output;
- add run manifests and artifact versioning;
- add tests for missing/duplicate activations and honest/attack alignment.

### Nice-to-have engineering

- experiment tracker or lightweight local SQLite/JSON index;
- parallel generation and activation collection;
- dashboard for filtering runs by model, layer, prompt, seed, and attack level;
- human-review queue for monitor disagreements;
- optional activation steering and LoRA backends behind one attacker interface.

## 7. Compute and resource strategy

Use a staged budget:

- cheap synthetic/CI tests for all code changes;
- small MMLU development slices for prompt and implementation debugging;
- medium runs for baseline and controls;
- expensive confirmatory runs only after the protocol is locked;
- replication budget reserved from the start.

Track local GPU/MPS hours, peak memory, generation count, activation storage, and API
calls. Keep the black-box monitor deterministic where possible and cache every score.
If an API monitor is used, record model name, date, prompt version, temperature,
token limit, and cost. A local monitor can be a useful robustness check, but should
not silently replace the stronger planned monitor in the main comparison.

## 8. Decision gates and fallback paths

### If sandbagging is unreliable

Try task selection, prompt revisions, or a model with stronger instruction following.
If no reliable attack can be produced, pivot to a measurement study of monitor
signals under prompted underperformance and state that strategic attack behavior was
not established.

### If activation probes perform at chance

Check token spans, labels, alignment, normalization, layer hooks, and behavioral
effect before changing the hypothesis. A chance result after valid checks is a useful
negative result.

### If R2 model-level optimization is too expensive

Run representation-space evasion as a clearly labeled lower bound, then use a small
LoRA or steering-vector attacker on a reduced training slice. Do not claim adaptive
model evasion from vector perturbation alone.

### If the black-box monitor is noisy

Cache repeated judgments, use a fixed rubric, report inter-run variance, and make the
activation/text results primary if the black-box signal cannot be made reliable.

### If compute is constrained

Prioritize: one model, one dataset, real controls, R0–R2, held-out transfer, three
seeds, and a complete writeup. A smaller clean study is preferable to a broad study
with leakage and unverified controls.

## 9. Expected result patterns and interpretation

The final discussion should explicitly cover at least these patterns:

1. **Cheap, transferable evasion:** probe AUROC falls, attack utility remains high,
   alternative monitors do not worsen, and transfer is good. This is evidence that
   the probe has low value against this attacker.
2. **Narrow evasion:** the known probe is evaded, but held-out probes or layers still
   detect the attack. This supports monitor diversity, not probe robustness in
   isolation.
3. **True-looking tax:** evasion reduces probe signal but also reduces attack success,
   increases suspicion, or requires substantial resources. Quantify which cost is
   dominant.
4. **Confounded baseline:** controls collapse performance. The main conclusion should
   become a warning about leakage or measurement validity.
5. **No behavioral attack:** sandbagging prompts do not produce a reliable effect.
   Report this directly and avoid treating condition classification as deception
   detection.

## 10. Final checklist for a workshop-quality result

- Is the threat model explicit about attacker knowledge and resources?
- Is there a real behavioral attack before monitoring is evaluated?
- Are train, validation, test, and prompt-template boundaries respected?
- Are all primary choices fixed before test evaluation?
- Are adaptive attacks model-level attacks, or clearly labeled synthetic proxies?
- Are successful and failed attacks both reported?
- Are probe, text, black-box, and ensemble monitors compared fairly?
- Are teacher-forced and self-generated modes distinguished?
- Are uncertainty, seeds, task breakdowns, and operating points reported?
- Can every figure be regenerated from versioned artifacts?
- Is the strongest negative result visible?
- Are model-scale and task limitations stated plainly?
- Does the public post teach the reader what was learned, including what failed?

The project is complete when the answer is not merely “we trained a probe,” but a
well-supported statement about when probe evasion is cheap, when it carries a tax,
how much that result depends on the measurement setup, and what a monitor designer
should do next.
