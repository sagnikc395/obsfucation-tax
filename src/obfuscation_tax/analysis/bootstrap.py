from __future__ import annotations

import numpy as np
from ..probes.metrics import bootstrap_ci


def ci_for_metric(y_true: np.ndarray, y_score: np.ndarray, metric_fn, n_bootstrap: int = 1000, seed: int = 42):
    return bootstrap_ci(y_true, y_score, metric_fn, n_bootstrap=n_bootstrap, seed=seed)
