from layers.layer03_intelligence.modules.intelligence_orchestrator.intel_orchestrator import IntelligenceOrchestrator


def test_production_intelligence_does_not_invent_trend_history(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    result = IntelligenceOrchestrator().analyze("ai automation")
    assert result.trend_prediction is None
    assert result.momentum is None
    assert result.lifecycle is None
    assert result.metadata["trend_observed"] is False
    assert result.metadata["production"] is True


def test_observed_trend_history_is_used_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    result = IntelligenceOrchestrator().analyze("ai automation", trend_history=[20.0, 30.0, 45.0])
    assert result.trend_prediction is not None
    assert result.momentum is not None
    assert result.lifecycle is not None
    assert result.metadata["trend_observed"] is True
