from __future__ import annotations

import numpy as np

from ..data.schemas import GenerationRecord
from ..probes.metrics import compute_auroc


def failed_attack_filtering_control(
    honest_records: list[GenerationRecord],
    sandbag_records: list[GenerationRecord],
    honest_acts: dict[str, np.ndarray],
    sandbag_acts: dict[str, np.ndarray],
    split_ids: dict[str, str],
) -> dict[str, float]:
    """Compare AUROC on all sandbag prompts vs successful attacks only.
    If probe is detecting condition label rather than successful attack, gap will be large.
    """
    from ..probes.train import train_probe_for_layer
    from ..probes.dataset import build_feature_matrix, filter_successful_attacks

    def _auroc(acts_h, acts_s):
        try:
            probe, _ = train_probe_for_layer(acts_h, acts_s, split_ids, C=1.0)
            X, y, _ = build_feature_matrix(acts_h, acts_s, split_ids, "test")
            if X.size == 0 or len(np.unique(y)) < 2:
                return 0.5
            return compute_auroc(y, probe.predict_proba(X))
        except Exception:
            return 0.5

    all_auroc = _auroc(honest_acts, sandbag_acts)

    # filter to successful attacks only
    h_keep, s_keep = filter_successful_attacks(honest_records, sandbag_records)
    keep_ids = {r.example_id for r in h_keep} | {r.example_id for r in s_keep}
    honest_filt = {k: v for k, v in honest_acts.items() if k in keep_ids}
    sandbag_filt = {k: v for k, v in sandbag_acts.items() if k in keep_ids}

    success_auroc = _auroc(honest_filt, sandbag_filt)

    return {
        "all_prompts_auroc": all_auroc,
        "successful_attacks_auroc": success_auroc,
        "gap": all_auroc - success_auroc,
    }
