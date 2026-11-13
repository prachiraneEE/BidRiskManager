from datetime import date

from app.schemas import RiskLevel, RiskReport


def compute_margin(value: float, estimated_cost: float) -> float:
    if value == 0:
        return 0.0
    return ((value - estimated_cost) / value) * 100


def compute_days_until_deadline(deadline: date) -> int:
    return (deadline - date.today()).days


def calculate_risk_score(
    margin_pct: float,
    days_until_deadline: int,
    past_bids_lost: int,
) -> dict:
    score = 0
    reasons: list[str] = []

    if margin_pct < 15:
        score += 40
        reasons.append(f"Profit margin is {margin_pct:.1f}%, below 15% threshold")

    if days_until_deadline < 7:
        score += 30
        reasons.append(
            f"Deadline is {days_until_deadline} days away, less than 7-day threshold"
        )

    if past_bids_lost >= 2:
        score += 30
        reasons.append(
            f"Client has lost {past_bids_lost} past bids (threshold: 2)"
        )

    score = min(score, 100)

    if score >= 70:
        level = RiskLevel.high
    elif score >= 40:
        level = RiskLevel.medium
    else:
        level = RiskLevel.low

    return RiskReport(score=score, level=level, reasons=reasons)
