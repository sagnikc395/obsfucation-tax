from __future__ import annotations

from pathlib import Path
from typing import Any
import pickle

import numpy as np

from .linear import LinearProbe
from .dataset import build_feature_matrix, normalize_features
from .metrics import compute_auroc
from ..activations.cache import load_activations
from ..data.splits import load_splits


def train_probe_for_layer(
    honest_acts: dict[str, np.ndarray],
    sandbag_acts: dict[str, np.ndarray],
    split_ids: dict[str, str],
    C: float = 1.0,
    normalize: bool = True,
) -> tuple[LinearProbe, dict[str, Any]]:
    # build train
    X_train, y_train, _ = build_feature_matrix(honest_acts, sandbag_acts, split_ids, "train")
    X_val, y_val, _ = build_feature_matrix(honest_acts, sandbag_acts, split_ids, "validation")

    if X_train.shape[0] == 0:
        raise ValueError("No training data for probe")

    if normalize:
        if X_val.size:
            X_train, X_val = normalize_features(X_train, X_val)  # type: ignore
        else:
            X_train = normalize_features(X_train)[0]

    probe = LinearProbe(C=C)
    probe.fit(X_train, y_train)

    info: dict[str, Any] = {"n_train": int(len(y_train)), "n_val": int(len(y_val)) if y_val.size else 0}
    if y_val.size and len(np.unique(y_val)) >= 2:
        scores = probe.predict_proba(X_val)
        info["val_auroc"] = compute_auroc(y_val, scores)
    return probe, info


def save_probe(probe: LinearProbe, path: str | Path, meta: dict[str, Any] | None = None) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as f:
        pickle.dump({"probe": probe, "meta": meta or {}}, f)


def load_probe(path: str | Path) -> tuple[LinearProbe, dict[str, Any]]:
    with open(path, "rb") as f:
        data = pickle.load(f)
    return data["probe"], data.get("meta", {})


def select_best_layer(layer_to_auroc: dict[int, float]) -> int:
    if not layer_to_auroc:
        raise ValueError("No layer scores")
    return max(layer_to_auroc, key=lambda k: layer_to_auroc[k])
