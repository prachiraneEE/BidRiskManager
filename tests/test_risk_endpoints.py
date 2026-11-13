import json
from datetime import date, timedelta
from unittest.mock import patch

from app.database import Base
from app.models import Assessment
from tests.conftest import TestSession


class TestAssessBid:
    def test_returns_risk_report(self, client, sample_bid, mock_llm):
        response = client.post(f"/bids/{sample_bid['id']}/assess")
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["bid_id"] == sample_bid["id"]
        assert 0 <= data["score"] <= 100
        assert data["level"] in ["low", "medium", "high"]
        assert isinstance(data["reasons"], list)
        assert data["recommendation"] == mock_llm.invoke.return_value.content
        assert "created_at" in data

    def test_bid_not_found(self, client, mock_llm):
        response = client.post("/bids/999/assess")
        assert response.status_code == 404

    def test_no_api_key_returns_503(self, client, sample_bid):
        with patch("app.routers.risk.settings") as mock_settings:
            mock_settings.openrouter_api_key = ""
            response = client.post(f"/bids/{sample_bid['id']}/assess")
        assert response.status_code == 503
        assert "LLM not configured" in response.json()["detail"]

    def test_saves_to_history(self, client, sample_bid, mock_llm):
        client.post(f"/bids/{sample_bid['id']}/assess")

        response = client.get(f"/bids/{sample_bid['id']}/assessments")
        data = response.json()
        assert len(data) == 1
        assert data[0]["bid_id"] == sample_bid["id"]
        assert data[0]["recommendation"] == mock_llm.invoke.return_value.content

    def test_high_risk_bid_scores_high(self, client, high_risk_bid, mock_llm):
        response = client.post(f"/bids/{high_risk_bid['id']}/assess")
        data = response.json()
        assert data["score"] >= 70
        assert data["level"] == "high"


class TestListAssessments:
    def test_returns_empty_list(self, client, sample_bid):
        response = client.get(f"/bids/{sample_bid['id']}/assessments")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_saved_assessments(self, client, sample_bid):
        db = TestSession()
        try:
            assessment = Assessment(
                bid_id=sample_bid["id"],
                score=70,
                level="high",
                reasons=json.dumps(["Low margin", "Tight deadline"]),
                recommendation="Proceed with caution.",
            )
            db.add(assessment)
            db.commit()
        finally:
            db.close()

        response = client.get(f"/bids/{sample_bid['id']}/assessments")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["score"] == 70
        assert data[0]["level"] == "high"
        assert data[0]["reasons"] == ["Low margin", "Tight deadline"]
        assert data[0]["recommendation"] == "Proceed with caution."
        assert "created_at" in data[0]

    def test_ordered_by_most_recent(self, client, sample_bid):
        db = TestSession()
        try:
            for score in [30, 70, 50]:
                a = Assessment(
                    bid_id=sample_bid["id"],
                    score=score,
                    level="medium",
                    reasons=json.dumps([]),
                    recommendation="Test",
                )
                db.add(a)
                db.commit()
        finally:
            db.close()

        response = client.get(f"/bids/{sample_bid['id']}/assessments")
        data = response.json()
        assert len(data) == 3
        assert data[0]["score"] == 50
        assert data[2]["score"] == 30

    def test_bid_not_found(self, client):
        response = client.get("/bids/999/assessments")
        assert response.status_code == 404


class TestRiskSummary:
    def _create_bid(self, client, client_id, title, value, cost, deadline, status="draft"):
        resp = client.post(
            "/bids/",
            json={
                "client_id": client_id,
                "title": title,
                "value": value,
                "estimated_cost": cost,
                "deadline": deadline,
                "status": status,
            },
        )
        return resp.json()

    def test_returns_top_risks(self, client, sample_client):
        far_deadline = (date.today() + timedelta(days=30)).isoformat()
        close_deadline = (date.today() + timedelta(days=3)).isoformat()

        self._create_bid(client, sample_client["id"], "Safe Bid", 100000, 70000, far_deadline)
        self._create_bid(client, sample_client["id"], "Risky Bid", 10000, 9000, close_deadline)

        response = client.get("/risks/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_open_bids"] == 2
        assert len(data["top_risks"]) == 2
        assert data["top_risks"][0]["bid_title"] == "Risky Bid"
        assert data["top_risks"][0]["score"] > data["top_risks"][1]["score"]

    def test_excludes_won_and_lost_bids(self, client, sample_client):
        deadline = (date.today() + timedelta(days=30)).isoformat()

        self._create_bid(client, sample_client["id"], "Open Bid", 10000, 9000, deadline, "draft")
        self._create_bid(client, sample_client["id"], "Won Bid", 10000, 9000, deadline, "won")
        self._create_bid(client, sample_client["id"], "Lost Bid", 10000, 9000, deadline, "lost")

        response = client.get("/risks/summary")
        data = response.json()
        assert data["total_open_bids"] == 1
        assert data["top_risks"][0]["bid_title"] == "Open Bid"

    def test_limits_to_five(self, client, sample_client):
        deadline = (date.today() + timedelta(days=30)).isoformat()
        for i in range(7):
            self._create_bid(client, sample_client["id"], f"Bid {i}", 10000, 9000, deadline)

        response = client.get("/risks/summary")
        data = response.json()
        assert data["total_open_bids"] == 7
        assert len(data["top_risks"]) == 5

    def test_empty_when_no_open_bids(self, client):
        response = client.get("/risks/summary")
        data = response.json()
        assert data["total_open_bids"] == 0
        assert data["top_risks"] == []
