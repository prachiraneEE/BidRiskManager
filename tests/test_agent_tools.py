from datetime import date, timedelta

import pytest

from app.agent.tools import (
    calculate_margin,
    check_deadline,
    get_bid_details,
    get_client_history,
)


class TestGetBidDetails:
    def test_returns_bid_data(self, client, sample_bid):
        from sqlalchemy.orm import Session

        from tests.conftest import TestSession

        db = TestSession()
        try:
            result = get_bid_details(db, sample_bid["id"])
            assert result["title"] == "Test Project"
            assert result["value"] == 50000
            assert result["estimated_cost"] == 35000
            assert result["client_id"] == sample_bid["client_id"]
            assert "deadline" in result
        finally:
            db.close()

    def test_bid_not_found(self, client):
        from tests.conftest import TestSession

        db = TestSession()
        try:
            with pytest.raises(ValueError, match="Bid 999 not found"):
                get_bid_details(db, 999)
        finally:
            db.close()


class TestGetClientHistory:
    def test_returns_client_data(self, client, sample_client):
        from tests.conftest import TestSession

        db = TestSession()
        try:
            result = get_client_history(db, sample_client["id"])
            assert result["name"] == "Test Corp"
            assert result["industry"] == "Technology"
            assert result["past_bids_won"] == 0
            assert result["past_bids_lost"] == 0
            assert result["win_rate"] == 0.0
        finally:
            db.close()

    def test_win_rate_calculation(self, client):
        resp = client.post(
            "/clients/",
            json={
                "name": "Active Corp",
                "industry": "Finance",
                "past_bids_won": 7,
                "past_bids_lost": 3,
            },
        )
        client_data = resp.json()

        from tests.conftest import TestSession

        db = TestSession()
        try:
            result = get_client_history(db, client_data["id"])
            assert result["win_rate"] == 70.0
        finally:
            db.close()

    def test_client_not_found(self, client):
        from tests.conftest import TestSession

        db = TestSession()
        try:
            with pytest.raises(ValueError, match="Client 999 not found"):
                get_client_history(db, 999)
        finally:
            db.close()


class TestCalculateMargin:
    def test_healthy_margin(self):
        result = calculate_margin(100_000, 70_000)
        assert result["margin_pct"] == 30.0
        assert result["is_low"] is False

    def test_low_margin(self):
        result = calculate_margin(100_000, 90_000)
        assert result["margin_pct"] == 10.0
        assert result["is_low"] is True

    def test_exact_threshold(self):
        result = calculate_margin(100, 85)
        assert result["margin_pct"] == 15.0
        assert result["is_low"] is False


class TestCheckDeadline:
    def test_far_deadline(self):
        future = (date.today() + timedelta(days=30)).isoformat()
        result = check_deadline(future)
        assert result["days_until"] == 30
        assert result["is_urgent"] is False

    def test_urgent_deadline(self):
        soon = (date.today() + timedelta(days=3)).isoformat()
        result = check_deadline(soon)
        assert result["days_until"] == 3
        assert result["is_urgent"] is True

    def test_past_deadline(self):
        past = (date.today() - timedelta(days=2)).isoformat()
        result = check_deadline(past)
        assert result["days_until"] == -2
        assert result["is_urgent"] is True
