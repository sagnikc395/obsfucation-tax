from __future__ import annotations

import numpy as np

from .linear import LinearProbe
from .dataset import build_feature_matrix, normalize_features
from .metrics import compute_auroc, compute_accuracy, compute_auprc, compute_ece


def evaluate_probe(
    probe: LinearProbe,
    honest_acts: dict[str, np.ndarray],
    sandbag_acts: dict[str, np.ndarray],
    split_ids: dict[str, str],
    split: str,
    normalize: bool = True,
    train_mean_std: tuple[np.ndarray, np.ndarray] | None = None,
) -> dict[str, float]:
    X, y, _ = build_feature_matrix(honest_acts, sandbag_acts, split_ids, split)
    if X.shape[0] == 0:
        return {"auroc": 0.5, "accuracy": 0.5, "auprc": 0.5, "ece": 0.0, "n": 0}
    # Note: for simplicity, caller should have normalized consistently; we redo with train stats if provided
    if train_mean_std is not None:
        mean, std = train_mean_std
        X = (X - mean) / std
    scores = probe.predict_proba(X)
    return {
        "auroc": compute_auroc(y, scores),
        "accuracy": compute_accuracy(y, scores),
        "auprc": compute_auprc(y, scores),
        "ece": compute_ece(y, scores),
        "n": int(len(y)),
    }
