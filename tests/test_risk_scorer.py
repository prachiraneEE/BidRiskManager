from datetime import date, timedelta

from app.services.risk_scorer import (
    calculate_risk_score,
    compute_days_until_deadline,
    compute_margin,
)


class TestComputeMargin:
    def test_normal_margin(self):
        assert compute_margin(100_000, 80_000) == 20.0

    def test_exact_threshold(self):
        assert compute_margin(100, 85) == 15.0

    def test_zero_margin(self):
        assert compute_margin(100, 100) == 0.0

    def test_negative_margin(self):
        assert compute_margin(100, 120) == -20.0

    def test_zero_value(self):
        assert compute_margin(0, 100) == 0.0


class TestComputeDaysUntilDeadline:
    def test_future_deadline(self):
        future = date.today() + timedelta(days=10)
        assert compute_days_until_deadline(future) == 10

    def test_today_deadline(self):
        assert compute_days_until_deadline(date.today()) == 0

    def test_past_deadline(self):
        past = date.today() - timedelta(days=3)
        assert compute_days_until_deadline(past) == -3


class TestCalculateRiskScore:
    def test_low_risk(self):
        result = calculate_risk_score(
            margin_pct=30.0, days_until_deadline=30, past_bids_lost=0
        )
        assert result.score == 0
        assert result.level == "low"
        assert result.reasons == []

    def test_medium_risk_low_margin(self):
        result = calculate_risk_score(
            margin_pct=10.0, days_until_deadline=30, past_bids_lost=0
        )
        assert result.score == 40
        assert result.level == "medium"
        assert len(result.reasons) == 1

    def test_medium_risk_tight_deadline(self):
        result = calculate_risk_score(
            margin_pct=20.0, days_until_deadline=5, past_bids_lost=0
        )
        assert result.score == 30
        assert result.level == "low"

    def test_medium_risk_losing_client(self):
        result = calculate_risk_score(
            margin_pct=20.0, days_until_deadline=30, past_bids_lost=3
        )
        assert result.score == 30
        assert result.level == "low"

    def test_high_risk_all_signals(self):
        result = calculate_risk_score(
            margin_pct=5.0, days_until_deadline=3, past_bids_lost=4
        )
        assert result.score == 100
        assert result.level == "high"
        assert len(result.reasons) == 3

    def test_two_signals_margin_and_deadline(self):
        result = calculate_risk_score(
            margin_pct=10.0, days_until_deadline=3, past_bids_lost=0
        )
        assert result.score == 70
        assert result.level == "high"
        assert len(result.reasons) == 2

    def test_exact_thresholds_safe(self):
        result = calculate_risk_score(
            margin_pct=15.0, days_until_deadline=7, past_bids_lost=1
        )
        assert result.score == 0
        assert result.level == "low"

    def test_exact_thresholds_risky(self):
        result = calculate_risk_score(
            margin_pct=14.9, days_until_deadline=6, past_bids_lost=2
        )
        assert result.score == 100
        assert result.level == "high"

    def test_reasons_contain_values(self):
        result = calculate_risk_score(
            margin_pct=10.0, days_until_deadline=30, past_bids_lost=0
        )
        assert "10.0%" in result.reasons[0]
