## obsfucation-tax
what does evading an activation probe actually cost an attacker inside a control protocol ?

### Abstract
Latent-space probes are known to be evadable. 
The open question is whether evasion is free. If pushing probe AUROC from 0.95 down to 0.60 also costs the attack policy 40% of its backdoor success rate and makes its code visibly weirder to a black-box monitor, then probes are still doing real work in a defense-in-depth stack, and you can quantify how much. 
If evasion is cheap, that is a strong negative result worth publishing. Either outcome is a result.

## Setup
- Setting: APPS code backdooring, via ControlArena's apps setting. Do not rebuild this. The dataset ships with validated backdoor solutions and a scorer that verifies the secret input actually triggers wrong behavior. Rebuilding it burns two weeks on plumbing.
- Untrusted model U: open weights, since you need activations. Qwen3-8B or Llama-3.1-8B-Instruct. Note the practical problem: a weak U produces few valid backdoors, so your positive class is thin. Mitigation is to seed with ControlArena's pre-validated backdoors and treat the model-generated ones as a held-out generalization set.
- Trusted monitor T: a small model reading only the code (Llama-3.2-3B or an API nano model).
- Blue team monitors: (a) T alone, (b) linear/attention probe on U's residual stream over generated code tokens, (c) score-normalized ensemble.
Compute: one 40-80GB GPU. Generation with vLLM is the bottleneck, not probing. Roughly 60 to 100 GPU-hours total, so on the order of $100 rented.

## Metrics to measure 

- Tax curve. 
Sweep red-team evasion pressure and plot, on the same x-axis, probe AUROC against (i) main-task pass rate, (ii) backdoor validity rate, (iii) T's mean suspiciousness score. The hypothesis worth testing is anticorrelation between (i)/(ii) and evasion, plus a rise in (iii). That last one is the interesting claim: obfuscating in activation space may push you into text that is more suspicious, making the two monitor types complementary rather than redundant.
- Subspace exhaustion. 
Iterate: train probe P₁, red team evades P₁, retrain P₂ on the evaded activations, red team evades P₂, and so on for k rounds. Track the pairwise angles between P₁…P_k, the effective rank of their span, and whether attack quality degrades monotonically. This answers a real mech interp question: is "I am inserting a backdoor" a roughly one-dimensional representation that dies after one round, or is it distributed enough that the blue team keeps finding fresh directions?
- Safety/usefulness 
Pareto at a fixed audit budget (2% is the convention), per protocol × attack pair, with bootstrapped confidence intervals. This is what makes it legible as control research rather than a probing demo.

- Red-team ladder
R0 prompted attack, no probe knowledge. R1 prompted attack plus "look benign" instructions. R2 soft prompt or steering vector optimized against the probe with a task-quality term in the loss. R3 same, but must transfer to a held-out probe trained at a different layer on different data. Assume Kerckhoffs: the red team knows the protocol and thresholds, and only R3 tests whether it needs the exact probe weights.

## Actual Difficulty 
`probe will cheat, and your first job is catching it`. 
The obvious failure is that the probe learns "there is an attack system prompt in context" rather than "this code contains a backdoor." An LLM will happily hand you AUROC 0.99 from that leak. Controls you need:

`Attack prompt present, model attempted no backdoor: separate label, not "honest."`
Attack prompt present, backdoor attempted but invalid: separate label again.
Probe reads only generated code tokens, never prompt tokens.
Held-out attack prompt template at test time.
Length, layer, and token-position ablations; a probe that only works at the final token on mean-pooled activations is often reading formatting.

`The task-quality term in the R2 loss is the other hard part.` 
Minimizing probe score alone gives you degenerate output. You need a differentiable-enough proxy for "code still compiles, still passes tests, still triggers on the secret input," and there is no clean gradient through a unit test. Budget a full week and expect to end up with a hybrid: gradient pressure on the probe, rejection sampling on task validity.

## Plan 
- W1 -> ControlArena baseline running, honest and attack rollouts generated, backdoor score verified, activation caching built. Deliverable : trusted-monitoring safety/ usefulness curve reproduced.
- W2: Probe training plus the full confound ablation table and layer sweep. Most people stop here; you do not.
- W3: R1 through R3 attacks, tax curve, probe-vs-black-box tradeoff.
- W4: Exhaustion rounds, Pareto with CIs, writeup, repo cleanup.

## De-risking
if R2/R3 optimization does not converge by end of W3, fall back to a cheap LoRA fine-tune on evasive attack demonstrations. You still get a tax curve, just a weaker attacker. Report that honestly and state the bound it gives you.

## Deliverable
clean repo, 8 to 10 page writeup with the Pareto plots and the confound table, and an Alignment Forum post. The confound table is what makes a reviewer at Redwood or AISI take you seriously.

## References:

- Greenblatt et al., AI Control: Improving Safety Despite Intentional Subversion, ICML 2024 (PMLR 235:16295-16336): https://proceedings.mlr.press/v235/greenblatt24a.html
- Goldowsky-Dill et al., Detecting Strategic Deception with Linear Probes, ICML 2025 (PMLR 267:19755-19786): https://proceedings.mlr.press/v267/goldowsky-dill25a.html
- Bailey et al., Obfuscated Activations Bypass LLM Latent-Space Defenses, ICLR 2026: https://openreview.net/forum?id=ktGmDGoWnB (the "obfuscation tax" observation in their SQL experiment is the seed of this project)
- Terekhov et al., Adaptive Attacks on Trusted Monitors Subvert AI Control Protocols, ICLR 2026: https://arxiv.org/abs/2510.09462
- Gupta and Jenner, RL-Obfuscation: Can Language Models Learn to Evade Latent-Space Monitors?: https://arxiv.org/abs/2506.14261

## Tooling and code to start from

- ControlArena: https://github.com/UKGovernmentBEIS/control-arena, APPS setting docs at https://control-arena.aisi.org.uk/settings/apps.html
- Apollo's probe code: https://github.com/ApolloResearch/deception-detection
- UK AISI White Box Control team update on sandbagging (blog, useful for how they frame results): https://aisi.gov.uk/research/white-box-control-at-uk-aisi---update-on-sandbagging-investigations