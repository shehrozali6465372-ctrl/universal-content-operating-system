import json

from layers.layer23_website_manager.affiliate_manager.providers.hostinger_referral import (
    ingest_dashboard_rows,
    load_hostinger_referral,
    normalize_hostinger_referral,
)


def test_real_hostinger_referral_record_loads():
    record = load_hostinger_referral()
    assert record.program_id == "hostinger_referral"
    assert record.referral_code == "92OSHEHRO7G1"
    assert record.referral_url == "https://www.hostinger.com/pk?REFERRALCODE=92OSHEHRO7G1"
    assert record.status == "integration_ready"
    assert not record.has_live_metrics
    assert all(value is None for value in record.metrics.values())


def test_hostinger_referral_code_must_match_url():
    data = {
        "program_id": "hostinger_referral",
        "referral_code": "wrong",
        "referral_url": "https://www.hostinger.com/pk?REFERRALCODE=92OSHEHRO7G1",
        "status": "integration_ready",
        "metrics": {},
    }
    try:
        normalize_hostinger_referral(data)
    except ValueError as exc:
        assert "REFERRALCODE" in str(exc)
    else:
        raise AssertionError("mismatched referral code was accepted")


def test_dashboard_data_is_observed_only():
    result = ingest_dashboard_rows([
        {"status": "qualified", "purchase_date": "2026-09-20", "commission": 10.5, "currency": "USD"},
        {"status": "pending", "purchase_date": None, "commission": None},
    ])
    assert result["referrals"] == 2
    assert result["status_counts"]["qualified"] == 1
    assert result["status_counts"]["pending"] == 1
    assert result["commission_total"] == 10.5


def test_empty_dashboard_data_does_not_create_zero_revenue_claim():
    result = ingest_dashboard_rows([])
    assert result["referrals"] == 0
    assert result["commission_total"] is None
