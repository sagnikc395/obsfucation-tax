from __future__ import annotations

import numpy as np
from pathlib import Path

from ..data.schemas import GenerationRecord


def filter_successful_attacks(
    honest_records: list[GenerationRecord],
    sandbag_records: list[GenerationRecord],
) -> tuple[list[GenerationRecord], list[GenerationRecord]]:
    """Keep only examples where honest was correct and sandbag was incorrect (attack_succeeded)."""
    honest_by_id = {r.example_id: r for r in honest_records}
    sandbag_by_id = {r.example_id: r for r in sandbag_records}
    honest_kept = []
    sandbag_kept = []
    for eid, h in honest_by_id.items():
        s = sandbag_by_id.get(eid)
        if s is None:
            continue
        # attack succeeded if honest correct and sandbag incorrect
        honest_correct = bool(h.correct)
        sandbag_correct = bool(s.correct)
        attack_succeeded = honest_correct and not sandbag_correct
        if attack_succeeded:
            honest_kept.append(h)
            sandbag_kept.append(s)
    return honest_kept, sandbag_kept


def build_feature_matrix(
    honest_acts: dict[str, np.ndarray],
    sandbag_acts: dict[str, np.ndarray],
    split_ids: dict[str, str] | None = None,
    filter_split: str | None = None,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Build X,y from activation dicts. Returns X, y, ids.
    honest=0, sandbag=1. If split_ids provided, filter to that split.
    """
    X_list = []
    y_list = []
    ids = []

    def _add(acts: dict[str, np.ndarray], label: int):
        for eid, vec in acts.items():
            if split_ids is not None and filter_split is not None:
                if split_ids.get(eid) != filter_split:
                    continue
            X_list.append(np.asarray(vec).reshape(-1))
            y_list.append(label)
            ids.append(eid)

    _add(honest_acts, 0)
    _add(sandbag_acts, 1)

    if not X_list:
        return np.zeros((0, 0)), np.zeros((0,)), []

    X = np.stack(X_list, axis=0)
    y = np.array(y_list, dtype=int)
    return X, y, ids


def normalize_features(
    X_train: np.ndarray, X_val: np.ndarray | None = None, X_test: np.ndarray | None = None
) -> tuple[np.ndarray, ...]:
    mean = X_train.mean(axis=0, keepdims=True)
    std = X_train.std(axis=0, keepdims=True) + 1e-8
    Xt = (X_train - mean) / std
    out = [Xt]
    for X in [X_val, X_test]:
        if X is not None and X.size > 0:
            out.append((X - mean) / std)
        elif X is not None:
            out.append(X)
    return tuple(out)
