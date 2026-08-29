from __future__ import annotations

import numpy as np
from ..probes.linear import LinearProbe


def probe_angles(probes: list[LinearProbe]) -> np.ndarray:
    n = len(probes)
    mat = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            mat[i, j] = probes[i].angle_with(probes[j])
    return mat


def effective_rank(probes: list[LinearProbe]) -> float:
    """Effective rank of probe span via singular values of stacked coefs."""
    if not probes:
        return 0.0
    M = np.stack([p.coef for p in probes], axis=0)  # [n_probes, dim]
    s = np.linalg.svd(M, compute_uv=False)
    # effective rank via entropy of normalized singular values
    s_norm = s / (s.sum() + 1e-12)
    entropy = -np.sum(s_norm * np.log(s_norm + 1e-12))
    return float(np.exp(entropy))


def degradation_over_rounds(aurocs: list[float]) -> dict[str, float]:
    if len(aurocs) < 2:
        return {"delta": 0.0, "slope": 0.0}
    delta = aurocs[-1] - aurocs[0]
    # linear slope
    x = np.arange(len(aurocs))
    slope = float(np.polyfit(x, aurocs, 1)[0])
    return {"delta": float(delta), "slope": slope}
