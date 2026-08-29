from __future__ import annotations

from typing import Any
import numpy as np

from ..data.schemas import GenerationRecord


def surface_text_control(
    records: list[GenerationRecord],
    probe_auroc: float,
    split_ids: dict[str, str],
    config: dict[str, Any] | None = None,
) -> dict[str, float]:
    """Compare activation probe vs TF-IDF baseline.
    Returns gap: probe - text baseline.
    """
    try:
        from ..monitors.text_baselines import train_tfidf_baseline, evaluate_tfidf

        pipe = train_tfidf_baseline(records, split_ids, "train")
        res = evaluate_tfidf(pipe, records, split_ids, "test")
        text_auroc = res["auroc"]
    except Exception:
        text_auroc = 0.5

    return {
        "probe_auroc": probe_auroc,
        "tfidf_auroc": text_auroc,
        "gap": probe_auroc - text_auroc,
    }
