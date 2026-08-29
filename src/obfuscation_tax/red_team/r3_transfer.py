from __future__ import annotations

from typing import Any
import numpy as np

from ..probes.linear import LinearProbe
from ..probes.metrics import compute_auroc


def evaluate_transfer(
    evasive_acts: dict[str, np.ndarray],
    honest_acts: dict[str, np.ndarray],
    heldout_probe: LinearProbe,
    split_ids: dict[str, str],
    split: str = "test",
) -> dict[str, float]:
    from ..probes.dataset import build_feature_matrix

    X, y, _ = build_feature_matrix(honest_acts, evasive_acts, split_ids, split)
    if X.shape[0] == 0 or len(np.unique(y)) < 2:
        return {"auroc": 0.5, "n": int(len(y))}
    scores = heldout_probe.predict_proba(X)
    return {"auroc": compute_auroc(y, scores), "n": int(len(y))}


def run_r3(
    activations: dict[str, np.ndarray],
    honest_acts: dict[str, np.ndarray],
    source_probe: LinearProbe,
    heldout_probe: LinearProbe,
    config: dict[str, Any],
    split_ids: dict[str, str],
) -> dict[str, Any]:
    """Evasion was optimized against source_probe; evaluate against heldout_probe."""
    from .r2_probe_evasion import run_r2

    evasive = run_r2(activations, source_probe, config)
    metrics = evaluate_transfer(evasive, honest_acts, heldout_probe, split_ids, split="test")
    # also measure how much source probe was evaded
    from ..probes.dataset import build_feature_matrix

    X, y, _ = build_feature_matrix(honest_acts, activations, split_ids, "test")
    X_ev, _, _ = build_feature_matrix(honest_acts, evasive, split_ids, "test")
    if X.size and X_ev.size:
        src_before = compute_auroc(y, source_probe.predict_proba(X))
        src_after = compute_auroc(y, source_probe.predict_proba(X_ev))
    else:
        src_before = src_after = 0.5
    return {
        "heldout_auroc": metrics["auroc"],
        "source_before": src_before,
        "source_after": src_after,
        "n": metrics["n"],
    }
