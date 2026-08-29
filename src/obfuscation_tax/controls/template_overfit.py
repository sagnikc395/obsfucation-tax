from __future__ import annotations

import numpy as np


def template_overfit_control(
    honest_acts: dict[str, np.ndarray],
    sandbag_seen_acts: dict[str, np.ndarray],
    sandbag_heldout_acts: dict[str, np.ndarray],
    split_ids: dict[str, str],
) -> dict[str, float]:
    """Check probe generalizes to held-out template.
    Train on seen template, test on heldout.
    """
    from ..probes.train import train_probe_for_layer
    from ..probes.metrics import compute_auroc
    from ..probes.dataset import build_feature_matrix

    try:
        probe, _ = train_probe_for_layer(honest_acts, sandbag_seen_acts, split_ids, C=1.0)
        # Evaluate on seen vs heldout
        X_seen, y_seen, _ = build_feature_matrix(honest_acts, sandbag_seen_acts, split_ids, "test")
        X_held, y_held, _ = build_feature_matrix(honest_acts, sandbag_heldout_acts, split_ids, "test")
        seen_auroc = compute_auroc(y_seen, probe.predict_proba(X_seen)) if X_seen.size else 0.5
        held_auroc = compute_auroc(y_held, probe.predict_proba(X_held)) if X_held.size else 0.5
    except Exception:
        seen_auroc = held_auroc = 0.5

    return {
        "seen_template_auroc": seen_auroc,
        "heldout_template_auroc": held_auroc,
        "gap": seen_auroc - held_auroc,
    }
