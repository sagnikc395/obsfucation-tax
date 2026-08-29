from __future__ import annotations

from typing import Any
import numpy as np

from ..probes.linear import LinearProbe


def soft_prompt_evasion(
    activations: dict[str, np.ndarray],
    probe: LinearProbe,
    evasion_strength: float = 1.0,
    steps: int = 100,
    lr: float = 0.01,
) -> dict[str, np.ndarray]:
    """Simulate soft-prompt evasion by gradient descent against probe.
    This is a synthetic vector perturbation, not real token optimization.
    Each activation is perturbed to minimize probe score while staying close.
    """
    w = probe.coef  # [dim]
    b = probe.intercept
    # normalize w
    w_norm = w / (np.linalg.norm(w) + 1e-8)
    out = {}
    for eid, vec in activations.items():
        v = vec.copy().astype(float)
        for _ in range(steps):
            # probe logit = w·v + b, prob = sigmoid(logit)
            # gradient of prob w.r.t v is prob*(1-prob)*w
            logit = float(np.dot(w, v) + b)
            prob = 1 / (1 + np.exp(-logit))
            grad = prob * (1 - prob) * w
            # move opposite to probe direction + small regularization to original
            v -= lr * (evasion_strength * grad + 0.01 * (v - vec))
        out[eid] = v.astype(np.float32)
    return out


def lora_fallback_evasion(
    activations: dict[str, np.ndarray],
    probe: LinearProbe,
    evasion_strength: float = 1.0,
) -> dict[str, np.ndarray]:
    """Weaker evasion: simple projection away from probe direction."""
    w = probe.coef / (np.linalg.norm(probe.coef) + 1e-8)
    out = {}
    for eid, vec in activations.items():
        proj = float(np.dot(vec, w))
        # subtract projection scaled by evasion strength
        v = vec - evasion_strength * proj * w * 0.5
        out[eid] = v.astype(np.float32)
    return out


def run_r2(
    activations: dict[str, np.ndarray],
    probe: LinearProbe,
    config: dict[str, Any],
    method: str | None = None,
) -> dict[str, np.ndarray]:
    rt_cfg = config.get("red_team", {}).get("r2", {})
    method = method or rt_cfg.get("method", "soft_prompt")
    strength = rt_cfg.get("evasion_strength", config.get("red_team", {}).get("evasion_strength", 1.0))
    budget = rt_cfg.get("optimization_budget", 100)
    lr = rt_cfg.get("learning_rate", 0.01)

    if method == "lora_fallback" or method == "lora":
        return lora_fallback_evasion(activations, probe, evasion_strength=strength)
    # default soft prompt
    return soft_prompt_evasion(activations, probe, evasion_strength=strength, steps=budget, lr=lr)
