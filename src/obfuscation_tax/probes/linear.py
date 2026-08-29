from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression


class LinearProbe:
    def __init__(self, C: float = 1.0, penalty: str = "l2", max_iter: int = 1000, class_weight: str | None = "balanced"):
        self.C = C
        self.penalty = penalty
        self.max_iter = max_iter
        self.class_weight = class_weight
        self.model = LogisticRegression(
            C=C, penalty=penalty, max_iter=max_iter, class_weight=class_weight, solver="lbfgs"
        )
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LinearProbe":
        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)[:, 1]

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(X)

    @property
    def coef(self) -> np.ndarray:
        return self.model.coef_[0]

    @property
    def intercept(self) -> float:
        return float(self.model.intercept_[0])

    def angle_with(self, other: "LinearProbe") -> float:
        """Cosine angle between probe weight vectors in degrees."""
        a = self.coef
        b = other.coef
        cos = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))
        cos = float(np.clip(cos, -1, 1))
        return float(np.degrees(np.arccos(cos)))
