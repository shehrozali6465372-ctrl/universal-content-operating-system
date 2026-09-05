"""Real supervised regression model used by Layer 9.

scikit-learn is intentionally imported lazily so the core package remains
importable when the ML dependency has not yet been installed. Training then
fails explicitly instead of silently falling back to a fake model.
"""
from __future__ import annotations

from hashlib import sha256
import math
from typing import Any, Sequence


class OnlineRegressor:
    """A persisted-in-memory real estimator trained on measured rewards."""

    def __init__(self) -> None:
        try:
            from sklearn.ensemble import HistGradientBoostingRegressor
            from sklearn.metrics import mean_absolute_error
            from sklearn.model_selection import train_test_split
        except ImportError as exc:
            raise RuntimeError(
                "scikit-learn is required for real Layer 9 training; no fallback/mock model exists"
            ) from exc
        self._Estimator = HistGradientBoostingRegressor
        self._mae = mean_absolute_error
        self._split = train_test_split
        self._model = None
        self.sample_count = 0
        self.version = "untrained"
        self.confidence: float | None = None

    def fit(self, X: Sequence[Sequence[float]], y: Sequence[float]) -> dict[str, Any]:
        if len(X) != len(y) or len(X) < 4:
            raise ValueError("training requires matching X/y and at least four real observations")
        if not all(math.isfinite(float(v)) for row in X for v in row):
            raise ValueError("non-finite feature detected")
        if not all(math.isfinite(float(v)) for v in y):
            raise ValueError("non-finite target detected")
        X_train, X_test, y_train, y_test = self._split(
            list(X), list(y), test_size=0.2, random_state=42
        )
        estimator = self._Estimator(random_state=42)
        estimator.fit(X_train, y_train)
        pred = estimator.predict(X_test)
        mae = float(self._mae(y_test, pred))
        self._model = estimator
        self.sample_count = len(X)
        self.version = "ml-" + sha256(
            (str(self.sample_count) + repr(estimator.get_params()) + str(mae)).encode()
        ).hexdigest()[:20]
        self.confidence = 1.0 / (1.0 + mae)
        return {"metric_name": "mae_holdout", "metric_value": mae}

    def predict(self, X: Sequence[Sequence[float]]) -> list[float]:
        if self._model is None:
            raise RuntimeError("model has not been trained")
        return [float(v) for v in self._model.predict(X)]
