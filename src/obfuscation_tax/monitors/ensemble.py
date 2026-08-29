from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression


def zscore_normalize(scores: np.ndarray) -> np.ndarray:
    return (scores - scores.mean()) / (scores.std() + 1e-8)


def minmax_normalize(scores: np.ndarray) -> np.ndarray:
    lo, hi = scores.min(), scores.max()
    if hi - lo < 1e-8:
        return np.zeros_like(scores)
    return (scores - lo) / (hi - lo)


def ensemble_scores(
    black_box: np.ndarray,
    probe: np.ndarray,
    weights: list[float] | None = None,
    normalize: str = "zscore",
) -> np.ndarray:
    if normalize == "zscore":
        bb = zscore_normalize(black_box)
        pr = zscore_normalize(probe)
    elif normalize == "minmax":
        bb = minmax_normalize(black_box)
        pr = minmax_normalize(probe)
    else:
        bb, pr = black_box, probe
    w = weights or [0.5, 0.5]
    return w[0] * bb + w[1] * pr


def train_ensemble(
    black_box_train: np.ndarray,
    probe_train: np.ndarray,
    y_train: np.ndarray,
) -> LogisticRegression:
    X = np.stack([black_box_train, probe_train], axis=1)
    clf = LogisticRegression(C=1.0, max_iter=1000)
    clf.fit(X, y_train)
    return clf
