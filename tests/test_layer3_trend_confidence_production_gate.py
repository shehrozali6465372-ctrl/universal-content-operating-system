import os

import pytest

from layers.layer03_intelligence.modules.trend_intelligence.trend_confidence import TrendConfidence


def test_production_confidence_rejects_missing_observed_inputs(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(ValueError, match="requires observed inputs"):
        TrendConfidence().calculate("ai", {"data_points": 3, "source_count": 1})


def test_production_confidence_accepts_complete_observed_inputs(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    result = TrendConfidence().calculate(
        "ai",
        {
            "data_points": 8,
            "source_count": 2,
            "hours_since_latest": 6,
            "score_variance": 0.1,
        },
    )
    assert result.overall_confidence > 0
