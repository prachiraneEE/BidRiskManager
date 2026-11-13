from datetime import date

from sqlalchemy.orm import Session

from app.models import Bid, Client
from app.services.risk_scorer import compute_days_until_deadline, compute_margin


def get_bid_details(db: Session, bid_id: int) -> dict:
    bid = db.get(Bid, bid_id)
    if not bid:
        raise ValueError(f"Bid {bid_id} not found")
    return {
        "id": bid.id,
        "client_id": bid.client_id,
        "title": bid.title,
        "value": bid.value,
        "estimated_cost": bid.estimated_cost,
        "deadline": bid.deadline.isoformat(),
        "status": bid.status,
        "notes": bid.notes,
    }


def get_client_history(db: Session, client_id: int) -> dict:
    client = db.get(Client, client_id)
    if not client:
        raise ValueError(f"Client {client_id} not found")
    total = client.past_bids_won + client.past_bids_lost
    win_rate = (client.past_bids_won / total * 100) if total > 0 else 0.0
    return {
        "id": client.id,
        "name": client.name,
        "industry": client.industry,
        "past_bids_won": client.past_bids_won,
        "past_bids_lost": client.past_bids_lost,
        "win_rate": round(win_rate, 1),
    }


def calculate_margin(value: float, estimated_cost: float) -> dict:
    margin_pct = compute_margin(value, estimated_cost)
    return {
        "margin_pct": round(margin_pct, 1),
        "is_low": margin_pct < 15,
    }


def check_deadline(deadline_str: str) -> dict:
    deadline = date.fromisoformat(deadline_str)
    days = compute_days_until_deadline(deadline)
    return {
        "days_until": days,
        "is_urgent": days < 7,
    }
