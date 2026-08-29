from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from ..data.schemas import GenerationRecord
from ..probes.metrics import compute_auroc


def train_tfidf_baseline(
    records: list[GenerationRecord],
    split_ids: dict[str, str],
    train_split: str = "train",
) -> Pipeline:
    texts = []
    labels = []
    for rec in records:
        if split_ids.get(rec.example_id) != train_split:
            continue
        texts.append(rec.completion)
        # honest=0, sandbag=1
        labels.append(0 if rec.condition == "honest" else 1)
    if not texts:
        raise ValueError("No training texts for TF-IDF baseline")
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ("clf", LogisticRegression(C=1.0, max_iter=1000, class_weight="balanced")),
    ])
    pipe.fit(texts, np.array(labels))
    return pipe


def evaluate_tfidf(
    pipe: Pipeline,
    records: list[GenerationRecord],
    split_ids: dict[str, str],
    split: str,
) -> dict[str, float]:
    texts = []
    y_true = []
    for rec in records:
        if split_ids.get(rec.example_id) != split:
            continue
        texts.append(rec.completion)
        y_true.append(0 if rec.condition == "honest" else 1)
    if not texts:
        return {"auroc": 0.5, "n": 0}
    y_true = np.array(y_true)
    y_score = pipe.predict_proba(texts)[:, 1]
    return {"auroc": compute_auroc(y_true, y_score), "n": int(len(y_true))}
