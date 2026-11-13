import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agent.risk_agent import run_risk_assessment
from app.config import settings
from app.database import get_db
from app.models import Assessment, Bid, Client
from app.schemas import AssessmentResponse, RiskSummaryItem, RiskSummaryResponse
from app.services.risk_scorer import (
    calculate_risk_score,
    compute_days_until_deadline,
    compute_margin,
)

router = APIRouter(prefix="/bids", tags=["Risk Assessment"])

summary_router = APIRouter(prefix="/risks", tags=["Risk Dashboard"])


@router.post("/{bid_id}/assess", response_model=AssessmentResponse, status_code=201)
def assess_bid(bid_id: int, db: Session = Depends(get_db)):
    if not settings.openrouter_api_key:
        raise HTTPException(
            status_code=503,
            detail="LLM not configured. Set OPENROUTER_API_KEY in .env",
        )

    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail=f"Bid {bid_id} not found")

    report = run_risk_assessment(bid_id, db)

    assessment = Assessment(
        bid_id=bid_id,
        score=report.score,
        level=report.level.value,
        reasons=json.dumps(report.reasons),
        recommendation=report.recommendation,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    assessment.reasons = json.loads(assessment.reasons)
    return assessment


@router.get("/{bid_id}/assessments", response_model=list[AssessmentResponse])
def list_assessments(bid_id: int, db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail=f"Bid {bid_id} not found")

    assessments = (
        db.query(Assessment)
        .filter(Assessment.bid_id == bid_id)
        .order_by(Assessment.created_at.desc(), Assessment.id.desc())
        .all()
    )

    for a in assessments:
        a.reasons = json.loads(a.reasons)

    return assessments


@summary_router.get("/summary", response_model=RiskSummaryResponse)
def risk_summary(db: Session = Depends(get_db)):
    open_bids = (
        db.query(Bid)
        .filter(Bid.status.in_(["draft", "submitted"]))
        .all()
    )

    scored: list[RiskSummaryItem] = []
    for bid in open_bids:
        client = db.get(Client, bid.client_id)
        margin_pct = compute_margin(bid.value, bid.estimated_cost)
        days = compute_days_until_deadline(bid.deadline)
        risk = calculate_risk_score(margin_pct, days, client.past_bids_lost)
        scored.append(
            RiskSummaryItem(
                bid_id=bid.id,
                bid_title=bid.title,
                client_name=client.name,
                score=risk.score,
                level=risk.level,
                reasons=risk.reasons,
            )
        )

    scored.sort(key=lambda x: x.score, reverse=True)
    return RiskSummaryResponse(top_risks=scored[:5], total_open_bids=len(open_bids))
