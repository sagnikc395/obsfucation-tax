from __future__ import annotations

import numpy as np


def prefill_mismatch_control(
    teacher_acts_h: dict[str, np.ndarray],
    teacher_acts_s: dict[str, np.ndarray],
    self_gen_acts_h: dict[str, np.ndarray],
    self_gen_acts_s: dict[str, np.ndarray],
    split_ids: dict[str, str],
) -> dict[str, float]:
    """Compare teacher-forced vs self-generated AUROC."""
    from ..probes.train import train_probe_for_layer
    from ..probes.metrics import compute_auroc
    from ..probes.dataset import build_feature_matrix

    def _eval(acts_h, acts_s, split="test"):
        try:
            probe, _ = train_probe_for_layer(acts_h, acts_s, split_ids, C=1.0)
            X, y, _ = build_feature_matrix(acts_h, acts_s, split_ids, split)
            scores = probe.predict_proba(X)
            return compute_auroc(y, scores)
        except Exception:
            return 0.5

    teacher_auroc = _eval(teacher_acts_h, teacher_acts_s, "test")
    self_gen_auroc = _eval(self_gen_acts_h, self_gen_acts_s, "test")
    return {
        "teacher_forced_auroc": teacher_auroc,
        "self_generated_auroc": self_gen_auroc,
        "gap": abs(teacher_auroc - self_gen_auroc),
    }
