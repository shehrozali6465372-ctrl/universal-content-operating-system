import pytest

from layers.layer03_intelligence.modules.trend_intelligence.trend_manager import TrendManager


def test_production_trend_manager_rejects_missing_observed_data(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(ValueError, match="requires observed source data"):
        TrendManager().analyze_topic("ai automation", {})


def test_production_trend_manager_rejects_synthetic_confidence_inputs(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    data = {
        "scores": [{"source": "serpapi", "score": 80}],
        "momentum_data": [60, 70, 80],
    }
    with pytest.raises(ValueError, match="requires observed hours_since_latest and score_variance"):
        TrendManager().analyze_topic("ai automation", data)


def test_production_trend_manager_accepts_observed_confidence_inputs(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    data = {
        "scores": [
            {"source": "serpapi", "score": 60},
            {"source": "serpapi", "score": 70},
            {"source": "serpapi", "score": 80},
        ],
        "momentum_data": [60, 70, 80],
        "hours_since_latest": 2,
        "score_variance": 0.04,
    }
    result = TrendManager().analyze_topic("ai automation", data)
    assert result.confidence is not None
    assert result.confidence.recency_confidence > 0.9
    assert result.confidence.consistency_confidence == 0.96
