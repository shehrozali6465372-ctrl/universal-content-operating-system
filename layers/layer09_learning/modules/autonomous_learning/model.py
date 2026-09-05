"""Real supervised model with persisted artifacts and honest evaluation."""
from __future__ import annotations

from hashlib import sha256
import math
from pathlib import Path
from typing import Any, Sequence


class OnlineRegressor:
    """Real estimator trained only from measured outcomes.

    There is deliberately no synthetic fallback. A model artifact is written
    only after a real holdout evaluation succeeds.
    """

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
        self.mae: float | None = None

    def fit(self, X: Sequence[Sequence[float]], y: Sequence[float]) -> dict[str, Any]:
        if len(X) != len(y) or len(X) < 20:
            raise ValueError("training requires matching X/y and at least 20 real observations")
        if not all(math.isfinite(float(v)) for row in X for v in row):
            raise ValueError("non-finite feature detected")
        if not all(math.isfinite(float(v)) for v in y):
            raise ValueError("non-finite target detected")
        X_train, X_test, y_train, y_test = self._split(
            list(X), list(y), test_size=0.2, random_state=42
        )
        estimator = self._Estimator(random_state=42)
        estimator.fit(X_train, y_train)
        mae = float(self._mae(y_test, estimator.predict(X_test)))
        self._model = estimator
        self.sample_count = len(X)
        self.mae = mae
        fingerprint = sha256((repr(estimator.get_params()) + repr(X_train) + repr(y_train)).encode()).hexdigest()[:20]
        self.version = "ml-" + fingerprint
        return {"metric_name": "mae_holdout", "metric_value": mae}

    def predict(self, X: Sequence[Sequence[float]]) -> list[float]:
        if self._model is None:
            raise RuntimeError("model has not been trained")
        return [float(v) for v in self._model.predict(X)]

    def save(self, path: str | Path) -> None:
        if self._model is None:
            raise RuntimeError("cannot persist an untrained model")
        try:
            import joblib
        except ImportError as exc:
            raise RuntimeError("joblib is required for real model persistence") from exc
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._model, target)

    def load(self, path: str | Path, *, version: str, sample_count: int, mae: float) -> None:
        try:
            import joblib
        except ImportError as exc:
            raise RuntimeError("joblib is required for real model persistence") from exc
        target = Path(path)
        if not target.exists():
            raise FileNotFoundError(target)
        self._model = joblib.load(target)
        self.version = version
        self.sample_count = int(sample_count)
        self.mae = float(mae)
