from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_auc_score, accuracy_score, average_precision_score


def compute_auroc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    if len(np.unique(y_true)) < 2:
        return 0.5
    return float(roc_auc_score(y_true, y_score))


def compute_accuracy(y_true: np.ndarray, y_score: np.ndarray, threshold: float = 0.5) -> float:
    y_pred = (y_score >= threshold).astype(int)
    return float(accuracy_score(y_true, y_pred))


def compute_auprc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    if len(np.unique(y_true)) < 2:
        return float(y_true.mean()) if len(y_true) else 0.5
    return float(average_precision_score(y_true, y_score))


def compute_ece(y_true: np.ndarray, y_score: np.ndarray, n_bins: int = 10) -> float:
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (y_score >= bins[i]) & (y_score < bins[i + 1])
        if i == n_bins - 1:
            mask = (y_score >= bins[i]) & (y_score <= bins[i + 1])
        if mask.sum() == 0:
            continue
        acc = y_true[mask].mean()
        conf = y_score[mask].mean()
        ece += abs(acc - conf) * mask.sum() / len(y_true)
    return float(ece)


def bootstrap_ci(
    y_true: np.ndarray,
    y_score: np.ndarray,
    metric_fn,
    n_bootstrap: int = 1000,
    seed: int = 42,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    rng = np.random.RandomState(seed)
    n = len(y_true)
    vals = []
    for _ in range(n_bootstrap):
        idx = rng.choice(n, n, replace=True)
        vals.append(metric_fn(y_true[idx], y_score[idx]))
    lo = float(np.percentile(vals, 100 * alpha / 2))
    hi = float(np.percentile(vals, 100 * (1 - alpha / 2)))
    mean = float(np.mean(vals))
    return mean, lo, hi
