"""obftax — the shared half of the obfuscation-tax experiment.

What a model can be asked to give up to evade an activation probe is measured in the
notebooks, one per experiment, because each one needs a GPU and hours of generation.
Everything those notebooks have in common lives here: the datasets, the scoring sandbox,
model loading, prompt construction, the hooks, the probe and its split, and the
statistics. No module here generates anything on import.

    from obftax import config, tasks, scoring, model, hooks, probes, analysis, storage

The names used in more than one notebook are also re-exported at the top level, so
`obftax.score(...)` and `obftax.fit_probe(...)` work without naming the module.
"""

from . import analysis, config, hooks, model, probes, scoring, storage, tasks
from .analysis import (
    attack_stats,
    auroc,
    decision_overlap,
    fresh_probe_auroc,
    random_cos_baseline,
)
from .config import (
    LAYERS,
    MAIN_LAYER,
    MAIN_POOL,
    MIN_ATTACKS,
    MIN_AUROC,
    MODEL,
    POOLINGS,
    PROMPTS,
    RESULTS,
    SEED,
    TAG,
    TRACK_CFG,
)
from .hooks import Capture, Patch, Project, Steer, attach
from .model import (
    answer_start,
    build_chat_prompt,
    build_prompt,
    decoder_layers,
    device,
    generate,
    generate_and_pool,
    check_thinking,
    load_model,
    pool_one,
    split_generation,
    text_config,
)
from .probes import (
    build_xy,
    fit_and_score,
    fit_from_saved,
    fit_probe,
    probe_direction,
    problem_split,
    score_subset,
)
from .scoring import (
    check_harness,
    clean_literal,
    extract_code,
    parses_as_literal,
    run_program,
    score,
    score_literal,
)
from .storage import base_path, load_pre, save_summary, zip_results
from .tasks import LOADERS, load_track

__all__ = [
    "analysis", "config", "hooks", "model", "probes", "scoring", "storage", "tasks",
    "LAYERS", "MAIN_LAYER", "MAIN_POOL", "MIN_ATTACKS", "MIN_AUROC", "MODEL",
    "POOLINGS", "PROMPTS", "RESULTS", "SEED", "TAG", "TRACK_CFG",
    "LOADERS", "load_track",
    "check_harness", "clean_literal", "extract_code", "parses_as_literal",
    "run_program", "score", "score_literal",
    "answer_start", "build_chat_prompt", "build_prompt", "check_thinking",
    "decoder_layers", "device", "generate", "generate_and_pool", "load_model", "pool_one",
    "split_generation", "text_config",
    "Capture", "Patch", "Project", "Steer", "attach",
    "build_xy", "fit_and_score", "fit_from_saved", "fit_probe", "probe_direction",
    "problem_split", "score_subset",
    "attack_stats", "auroc", "decision_overlap", "fresh_probe_auroc",
    "random_cos_baseline",
    "base_path", "load_pre", "save_summary", "zip_results",
]
